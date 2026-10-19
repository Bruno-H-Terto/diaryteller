# Streaming e idempotência

## Transporte

`POST /v1/ai/responses` devolve `text/event-stream`. Use um cliente HTTP nativo
que permita POST com headers; não dependa do `EventSource` de navegador. Cada
evento:

```text
event: text_delta
data: {"operation_id":"UUID","sequence":3,"text":"..."}
id: 3
```

`sequence` é crescente por operação. `operation_id` aparece em todo evento.
O `id` é o mesmo `sequence`; retomada por `Last-Event-ID` não é suportada.

## Eventos

| Evento | Conteúdo | Significado |
|---|---|---|
| `started` | mode | reserva confirmada |
| `text_delta` | text | texto provisório |
| `tool_status` | tool, phase (`started/completed/failed`) | progresso sem argumentos |
| `result` | resultado final validado | habilita propostas |
| `error` | code, message, retryable | falha após o início do stream |
| `completed` | state `succeeded` | encerra sucesso |

Comentários `: keep-alive` a cada 15 s não têm conteúdo pessoal. Proxy deve
desativar buffering (`X-Accel-Buffering: no`). Timeouts: conexão ao provedor,
primeiro token (20 s), operação total (90 s) e heartbeat (15 s).

## Queda de conexão

1. O celular mantém o texto parcial marcado como provisório.
2. Consulta `GET /v1/operations/{id}`.
3. Se necessário, regenera com **nova** `Idempotency-Key`; pode haver novo custo.
4. O servidor marca `interrupted` quando o lease vence ou o cliente desaparece.
   O provedor pode já ter concluído a inferência: a incerteza é registrada.

Cancelamento é cooperativo. `POST /operations/{id}/cancel` retorna `202`; o
stream verifica controle a cada 15 s. Revogação de sessão encerra streams no
mesmo prazo.

## Idempotência

A chave é associada a usuário + tipo de operação. O recibo guarda HMAC do
payload normalizado com chave dedicada e rotacionável; texto e hash simples de
frases curtas não são persistidos. Retenção inicial: 24 h.

- em execução → `409 operation_in_progress`
- concluída → `409 operation_completed`, `result_available=false`
- payload diferente → `409 idempotency_conflict`

Não há replay de resposta. Após timeout ambíguo, não repita o POST de inferência
sem decidir explicitamente por regenerar.

## Pseudocódigo mobile

```kotlin
val request = http.newCall(Request.Builder()
    .url("$base/v1/ai/responses")
    .header("Authorization", "Bearer $access")
    .header("X-Session-Source", source)
    .header("Idempotency-Key", clientMessageId.toString())
    .post(jsonBody)
    .build())

request.execute().use { response ->
    val reader = response.body!!.source()
    while (!reader.exhausted()) {
        val line = reader.readUtf8Line() ?: break
        when {
            line.startsWith("event: ") -> event = line.removePrefix("event: ")
            line.startsWith("data: ") -> handle(event, line.removePrefix("data: "))
            line.startsWith(":") -> Unit // heartbeat
        }
    }
}
```
