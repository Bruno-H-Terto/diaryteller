# Contrato mobile e exemplos

Exemplos usam variáveis de ambiente. Substitua por dados sintéticos. Tokens
devem ficar no Keychain/Keystore, nunca em logs, analytics ou backups do app.

```bash
export BASE=http://localhost:8001
export CONV=http://localhost:8010
export SPEECH=http://localhost:8011
```

## Cadastro, verificação e login

```bash
curl -s -X POST "$BASE/v1/auth/register" -H 'content-type: application/json' -d '{
  "email": "sintetico@example.test",
  "password": "correct horse battery",
  "locale": "pt-BR",
  "timezone": "America/Sao_Paulo"
}'

# O token chega no email (Mailpit em http://localhost:8025 no ambiente local).
curl -s -X POST "$BASE/v1/auth/verify-email" -H 'content-type: application/json' \
  -d '{"token":"TOKEN_RECEBIDO"}'

curl -s -X POST "$BASE/v1/auth/login" -H 'content-type: application/json' -d '{
  "email": "sintetico@example.test",
  "password": "correct horse battery",
  "device_id": "11111111-1111-4111-8111-111111111111",
  "device_label": "Telefone de teste",
  "platform": "android"
}' > tokens.json
```

O aparelho deve gerar o `device_id` aleatório uma vez e reutilizá-lo. Serializar
refresh: uma chamada por vez. Guarde `access_token`, `refresh_token`, `source`,
`session_id`.

## Headers autenticados

```bash
ACCESS=$(jq -r .access_token tokens.json)
SOURCE=$(jq -r .source tokens.json)
AUTH=(-H "Authorization: Bearer $ACCESS" -H "X-Session-Source: $SOURCE")
```

## Perfil e direitos

```bash
curl -s "$BASE/v1/me" "${AUTH[@]}"
curl -s "$BASE/v1/me/entitlements" "${AUTH[@]}"
curl -s "$BASE/v1/me/sessions" "${AUTH[@]}"
```

## Conversa

```bash
curl -N -X POST "$CONV/v1/ai/responses" "${AUTH[@]}" \
  -H 'content-type: application/json' \
  -H 'Idempotency-Key: 6f6d2d62-8d27-4a5b-a2d9-5d6f6f6f6f61' -d '{
  "client_message_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "conversation_id": "local-conversation-1",
  "mode": "conversation",
  "message": "Hoje briguei com minha mãe.",
  "locale": "pt-BR",
  "timezone": "America/Sao_Paulo",
  "context": {"coverage": "selected_records", "records": []}
}'
```

Leia o corpo incremental como provisório. Persistir apenas o evento `result`.
Propostas (`goal`, `reminder`, `local_summary`) exigem confirmação e são
salvas/agendadas pelo app; o backend não executa nada.

## Memória paga (timeline)

```bash
curl -N -X POST "$CONV/v1/ai/responses" "${AUTH[@]}" \
  -H 'content-type: application/json' -H 'Idempotency-Key: timeline-0001' -d '{
  "client_message_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "conversation_id": "local-conversation-1",
  "mode": "timeline",
  "message": "Organize minha semana.",
  "locale": "pt-BR",
  "timezone": "America/Sao_Paulo",
  "context": {"coverage": "selected_records", "records": [{
    "id": "local-record-1",
    "recorded_at": "2026-10-18T20:00:00-03:00",
    "event_at": "2026-10-17T10:00:00-03:00",
    "text": "Conversa difícil com minha mãe.",
    "source_type": "diary_text"
  }]}
}'
```

## Voz

```bash
curl -s -X POST "$SPEECH/v1/speech/transcriptions" "${AUTH[@]}" \
  -H 'content-type: audio/wav' -H 'X-Audio-Format: wav' \
  -H 'X-Audio-Language: pt' -H 'Idempotency-Key: speech-0001' \
  --data-binary @audio-sintetico.wav

curl -s "$SPEECH/v1/speech/voices" "${AUTH[@]}"

curl -s -X POST "$SPEECH/v1/speech/syntheses" "${AUTH[@]}" \
  -H 'content-type: application/json' -H 'Idempotency-Key: tts-0001' \
  -d '{"text":"Resposta curta.","voice_id":"alloy","format":"mp3"}' \
  --output resposta.mp3
```

Cada etapa tem operação própria. Sem rede, o app mantém fila local; a API
remota não funciona offline.

## Refresh e revogação

```bash
curl -s -X POST "$BASE/v1/auth/refresh" -H "X-Session-Source: $SOURCE" \
  -H 'content-type: application/json' \
  -d "{\"refresh_token\":\"$(jq -r .refresh_token tokens.json)\",\"device_id\":\"11111111-1111-4111-8111-111111111111\"}"

curl -s -X POST "$BASE/v1/me/sessions/revoke-others" "${AUTH[@]}"
```

## Tratamento de erros

- `401 session_revoked`/`session_source_invalid`: apagar tokens locais e autenticar.
- `403 email_not_verified`: pedir reenvio e verificar.
- `403 subscription_required`: mostrar plano e loja.
- `429 quota_exceeded`/`rate_limited`: respeitar `details.retry_after_seconds`.
- `409 operation_in_progress`: consultar `GET /v1/operations/{id}`.
- `409 operation_completed`: não repetir IA; `result_available=false`.
- `502/504`: preservar texto parcial, consultar operação e decidir nova chave.
- `413/415 media_*`: reduzir áudio ou usar formato suportado.
