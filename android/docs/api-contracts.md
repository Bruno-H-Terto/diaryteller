# Contratos com o backend

## Autenticação

`POST /v1/auth/oidc/transactions`

```json
{"provider":"dex","redirect_uri":"callmeai://oidc","device_id":"uuid",
 "code_challenge":"43 chars","code_challenge_method":"S256"}
```

Resposta: `transaction_id`, `authorization_url`, `state`, `expires_at`.

`POST /v1/auth/oidc/exchange`

```json
{"transaction_id":"uuid","code":"...","state":"...","code_verifier":"..."}
```

Resposta: `access_token`, `refresh_token`, `source`, `session_id`,
`expires_in`, `source_expires_in`.

`POST /v1/auth/refresh` (header `X-Session-Source`)

```json
{"refresh_token":"...","device_id":"uuid"}
```

`GET /v1/me` devolve `id` e `email`.

## Regras aplicadas no app

- `state` do callback precisa ser igual ao da transação.
- `code` e `state` ausentes, ou `error`, cancelam a entrada sem trocar tokens.
- Access token e source vão em `Authorization` e `X-Session-Source`.
- Renovação concorrente é serializada; falha de refresh limpa a sessão.
- Nenhuma URL assinada ou token é logado.

## Erros

O backend devolve `{code, message, details, retryable}`. O app mapeia para:

- `401` → tenta refresh uma vez; persistindo, volta para login.
- `403` → mostra motivo (`email_not_verified`, `account_disabled`).
- `429`/`5xx` → mensagem com ação de tentar novamente.

## Conversa

`POST /v1/ai/responses` (streaming SSE) com `Idempotency-Key`.

```json
{"client_message_id":"uuid","conversation_id":"uuid","mode":"conversation",
 "message":"...","context":{"coverage":"selected_records","records":[
   {"id":"local","recorded_at":"2026-10-19T10:00:00Z","text":"...","source_type":"diary_text"}]}}
```

Eventos consumidos: `started`, `text_delta` (`data.text`), `result`,
`completed`, `error` (`data.code`). O app nunca chama o provedor de IA.

## Voz

Sem contrato HTTP: áudio, transcrição e TTS são locais. O backend nunca recebe
áudio nem transcrição.

## Pendências

Endpoints de registros/versões, upload de anexos, conversa e timeline ainda não
existem. Ver [backend-requirements](backend-requirements.md).
