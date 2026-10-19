# Pendências do backend

Atualizado em 2026-10-19. Nenhuma alteração foi feita no backend.

## 1. Registros e versões (bloqueia etapa 3/4)

O app hoje mantém registros e versões apenas localmente. Para o fluxo completo
descrito na especificação falta:

- `POST /v1/records` com `Idempotency-Key` e `local_record_id`.
  - Entrada: `local_record_id`, `content`, `content_sha256`, `created_at`.
  - Saída: `record_id`, `version_id`, `version_number`, `sync_state`.
  - Autorização: sessão do dono; 401/403/409/413 documentados.
- `POST /v1/records/{id}/versions` com `base_version_id` e `If-Match`.
  - Saída: número atribuído pelo servidor e conflito `409` com a versão atual.
- `GET /v1/records?cursor=` incremental e `GET /v1/records/{id}/versions`.
- `DELETE /v1/records/{id}` propagando exclusão.

Tela bloqueada: sincronização da lista/editor. O adaptador
`UnavailableRecordsSync` mantém a fila local com estado pendente.

## 2. Upload direto (etapa 5)

Contrato já definido em `contracts/android-delta`, implementação pendente no
backend:

- `POST /v1/exchange/uploads`
- `POST /v1/exchange/uploads/{id}/urls`
- `GET /v1/exchange/uploads/{id}/parts`
- `POST /v1/exchange/uploads/{id}/complete`
- `DELETE /v1/exchange/uploads/{id}`
- `POST /v1/exchange/media/{id}/download-url`

## 3. Transcrição assíncrona (etapa 6)

- `POST /v1/speech/transcription-jobs`
- `GET /v1/speech/transcription-jobs/{id}`
- `POST /v1/speech/transcription-jobs/{id}/retry|cancel`

## 4. Conversa e timeline (etapas 7/8)

- `POST /v1/ai/responses` com `context_id` e streaming SSE.
- `GET /v1/exchange/results/{id}` e `POST .../ack`.
- `POST /v1/exchange/snapshots` e `GET /v1/exchange/changes`.

## 5. Configuração

- Provedor OIDC `dex` disponível no compose (`OIDC_ENABLED=true`).
- `BACKEND_BASE_URL` do app precisa apontar para o host correto.
- Push já existe (`PUT /v1/me/devices/{id}/push-token`), usado na etapa 9.

## Bloco para o time do backend

```text
Necessário para o app Android:
1. CRUD/sync de registros com versionamento autoritativo:
   POST /v1/records (Idempotency-Key, local_record_id)
   POST /v1/records/{id}/versions (If-Match, base_version_id)
   GET /v1/records?cursor= e GET /v1/records/{id}/versions
   DELETE /v1/records/{id}
2. Uploads diretos/multipart conforme contracts/android-delta.
3. Jobs assíncronos de transcrição com retry/cancel.
4. Conversa com context_id + resultados recuperáveis (GET/ack) e SSE.
5. Feed incremental e snapshots para sincronização.
Todos com erros {code,message,details,retryable} e limites por plano.
```
