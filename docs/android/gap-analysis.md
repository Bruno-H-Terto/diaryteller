# Gap analysis — backend atual × contrato Android

Auditoria feita em 2026-10-19 contra o código deste repositório e o pacote
`call-me-ai-backend-android-refatoracao.zip`. Baseline gerado por
`poetry run python scripts/export_openapi.py --baseline`; hashes em
`contracts/openapi/baseline/MANIFEST.json`. OpenAPI dos serviços: 3.1.

## Evidência atual

| Área | Rotas/tabelas/testes existentes | Situação |
|---|---|---|
| Conta/sessão | `/v1/auth/*`, `/v1/me`, `sessions`, `refresh_credentials`, `devices` | completo, sem OIDC |
| Autorização/quota | `usage_buckets`, `usage_reservations`, `/internal/authorize`, `/internal/operations/*` | AI/fala/memória; sem upload |
| Conversa | `POST /v1/ai/responses` com `context` inline e SSE | sem `context_id`; sem resultado recuperável |
| Fala | `POST /v1/speech/transcriptions` síncrono, `/voices`, `/syntheses` | sem job assíncrono |
| MCP | `memory_mcp` com 5 ferramentas e JWE por operação | contexto inline apenas |
| Operações | recibos, idempotência, lease, cancelamento | reutilizável |
| Notificações | outbox + worker + email/push | reutilizável para exclusão |
| Manutenção | retenção, reconciliação, backups PG/Mongo | sem storage/objetos |
| Observabilidade | allowlist, sink Mongo, métricas, `request_id` | reutilizável |

## Requisitos do pacote Android × delta

| Requisito | Evidência atual | Delta necessário |
|---|---|---|
| OIDC/PKCE | só email/senha | `federated_identities`, `oidc_transactions`, adapter genérico, endpoints `/v1/auth/oidc/*` |
| Contas vinculadas por `(issuer, subject)` | `users.email` único | proibir união por email; vínculo exige reautenticação |
| Contexto autorizado | contexto inline em memória | serviço `exchange`, contexto imutável cifrado, `context_id` |
| Retenção escolhida | sem escolha | `delete_after_processing`/`keep_until_deleted`; `PATCH` com `If-Match` |
| Upload direto | áudio passa pelo speech | URLs assinadas, SINGLE/MULTIPART, staging privado |
| Retomada | inexistente | partes, renovação, `complete` idempotente, cancelamento |
| Validação de mídia | magic bytes/duração no speech | worker no exchange com SHA256 real, promoção de chave |
| Transcrição assíncrona | síncrona | `transcription_jobs`, worker lease/fencing, retry sem reupload |
| Resultado recuperável | não armazenado | resultado imutável com TTL 24 h, `GET`, `ack` |
| Proveniência local | `ContextRecord.id` | `local_record_id`, `local_version_id`, `content_sha256` |
| Datas | `recorded_at`/`event_at` | `event_date`, `event_description`, `event_precision` |
| Feed operacional | inexistente | `changes` por owner, cursor HMAC, tombstones |
| Cursor expirado | inexistente | `410` + snapshot consistente de manifests |
| Exclusão | `DELETE /me` revoga sessão | purge durável em exchange/speech/storage, tombstone |
| Quotas de tier | AI/fala/memória | upload por dia, bytes, arquivo, capacidade, concorrência |
| Plano free | existe `free` | limites de upload obrigatórios; `paid_test` só dev/test |
| Anúncios | inexistente | `GET /v1/monetization/ad-policy`; reward desligada |
| Compatibilidade | rotas atuais | aditivo; nenhuma rota/evento SSE removido |

## Mapa de serviços

| Serviço | Alteração |
|---|---|
| `identity` | OIDC, quotas de upload, política de anúncios; mantém sessão/JWT/source/refresh |
| `exchange` (novo) | contextos, uploads, mídia validada, resultados, feed, snapshots, deleções |
| `speech` | jobs assíncronos e worker; rota síncrona preservada |
| `conversation` | `context_id` XOR inline; resultado no exchange; SSE preservado |
| `memory_mcp` | sem mudança estrutural; recebe apenas refs da operação |
| `notifications` | outbox de exclusão de conta e alertas existentes |
| `maintenance` | purge/abort/reconcile/delete-account; backups sem payload |
| `edge` | sem `/mcp`, `/internal`, `/metrics`; remove headers internos |

## Não implementado neste escopo

- App Android, UI de anúncios, SDK de anúncios e recompensa.
- Sync de diário, numeração de versões no servidor, CRUD, backup de conteúdo.
- MCP público para terceiros, análise multimodal, clonagem de voz.
- Provedor OIDC de produção, provedor de anúncios e preços comerciais.

## Decisões registradas

- OIDC genérico + Dex local; Google/nativo exige provider definido antes de
  habilitar (sem fingir PKCE onde não se aplica).
- Object storage S3-compatible + MinIO local; payload cifrado no storage,
  metadados no PostgreSQL.
- Fixtures de quota e retenção da especificação; valores são engenharia, não
  preço ou obrigação jurídica.
- Flags `CONTEXT_EXCHANGE_ENABLED`, `ASYNC_TRANSCRIPTION_ENABLED`, `ADS_ENABLED`,
  `REWARDED_ADS_ENABLED` desligadas em produção até os gates.
