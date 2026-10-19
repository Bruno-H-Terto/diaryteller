# Endpoints de IA e voz

## Conversa (`POST /v1/ai/responses`)

Headers obrigatórios: `Authorization`, `X-Session-Source`, `Idempotency-Key`
(8–128 caracteres) e `Content-Type: application/json`.

Corpo conforme [contrato mobile](mobile-contract.md#conversa). Limites iniciais:
JSON 256 KiB, mensagem 8.000 caracteres, 50 registros, 50.000 caracteres de
contexto, AI estimate até 16.000 tokens por requisição. O menor limite vence.

Modos: `conversation`, `recall`, `organize`, `timeline`, `summarize`. O modo orienta
a intenção; permissões são verificadas no identity:

| Modo | Permissões |
|---|---|
| conversation | `conversation:use` |
| recall | `conversation:use` + `memory:search` |
| organize | `conversation:use` + `memory:organize` |
| timeline | `conversation:use` + `memory:timeline` |
| summarize | `conversation:use` + `memory:summarize` |

Sem permissão: `403 subscription_required` com `details.required_permission`.
Quota insuficiente: `429 quota_exceeded` com `details.operation_id`, `metric`,
`limit`, `remaining`.

A resposta é `text/event-stream`; ver [streaming](streaming-contract.md).
`Cache-Control: no-store`. O corpo incremental é provisório; somente o evento
`result` habilita propostas.

### Idempotência

- Nova chave: reserva e inicia.
- Mesma chave em execução: `409 operation_in_progress` com `operation_id`.
- Mesma chave já concluída: `409 operation_completed`, `result_available=false`.
  A resposta antiga não é rearmazenada nem reproduzida.
- Mesma chave com payload diferente: `409 idempotency_conflict`.

## Operações

| Método | Rota | Sucesso |
|---|---|---|
| GET | `/v1/operations/{id}` | 200 metadados; nunca a resposta antiga |
| POST | `/v1/operations/{id}/cancel` | 202 estado atual; cancelamento cooperativo |

Estados: `accepted`, `running`, `succeeded`, `failed`, `cancel_requested`,
`cancelled`, `interrupted`.

## Voz no aparelho

Transcrição, síntese e gravação são locais e não têm endpoint. O app usa
`SpeechRecognizer` em modo on-device e o `TextToSpeech` do Android; nenhum áudio
ou transcrição é enviado ao backend nem persistido no servidor.

A única operação de IA no servidor é organização/interpretação do contexto
textual explicitamente selecionado.

## Operações

Cada conversa tem operação, erro e consumo independentes. Não há endpoint de
upload de áudio nem de job de transcrição.
