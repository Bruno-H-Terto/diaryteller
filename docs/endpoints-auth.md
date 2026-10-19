# Endpoints de identidade

Prefixo `/v1`. JSON UTF-8; datas ISO 8601 com timezone. Endpoints autenticados
exigem `Authorization: Bearer <jwt>` e `X-Session-Source: <jwe>`.

## Cadastro e login

| Método | Rota | Corpo | Sucesso |
|---|---|---|---|
| POST | `/auth/register` | email, senha, locale, timezone | 201 `{"status":"verification_queued"}` |
| POST | `/auth/verify-email` | token | 204 |
| POST | `/auth/verify-email/resend` | email | 202 |
| POST | `/auth/login` | email, senha, device_id, label, platform | 200 tokens |
| POST | `/auth/refresh` | refresh_token, device_id + header source | 200 tokens |
| POST | `/auth/logout` | — (autenticado) | 204 |
| POST | `/auth/password-reset/request` | email | 202 |
| POST | `/auth/password-reset/confirm` | token, new_password | 204 |

`register` e `resend` não revelam se um email existe. Login exige email
verificado (`403 email_not_verified`). A senha usa Argon2id; tentativas são
limitadas por janela compartilhada.

### Resposta de login/refresh

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<opaco>",
  "source": "<jwe>",
  "session_id": "UUID",
  "token_type": "Bearer",
  "expires_in": 600,
  "source_expires_in": 900
}
```

Guardar os tokens no Keychain/Keystore do aparelho. No Android, não usar
SharedPreferences sem proteção; no iOS, usar Keychain com acessibilidade
adequada. O servidor nunca devolve tokens em logs.

Refresh é rotativo e serializado: cada refresh consome a credencial e emite uma
substituta. Reutilizar uma credencial consumida revoga a família e a sessão. Se a
resposta se perder, o cliente deve autenticar novamente; isso não é mascarado com
reutilização ilimitada.

## Perfil e estado

| Método | Rota | Resultado |
|---|---|---|
| GET | `/me` | perfil, status, email verificado |
| PATCH | `/me` | display_name, locale, timezone editáveis |
| GET | `/me/entitlements` | plano, permissões, quotas e restante |
| GET | `/me/usage` | consumo/limite do dia UTC |
| DELETE | `/me` | 202; exige autenticação recente e revoga sessões |

Plano, preço e `is_premium` enviados pelo cliente são rejeitados (`422`). O
`device_id` é um UUID aleatório gerado pelo aparelho; não é identidade nem prova
de posse.

## Sessões, push e notificações

| Método | Rota | Comportamento |
|---|---|---|
| GET | `/me/sessions` | sessões do próprio usuário, marca `is_current` |
| DELETE | `/me/sessions/{id}` | revoga sessão própria; 204 |
| POST | `/me/sessions/revoke-others` | preserva a atual; 204 |
| PUT | `/me/devices/{id}/push-token` | token de push; dispositivo deve ser do usuário |
| DELETE | `/me/devices/{id}/push-token` | remove inscrição; 204 |
| GET | `/me/notifications?limit&before` | paginação por cursor |
| POST | `/me/notifications/{id}/read` | marca própria; 204 |

## Erros

Envelope uniforme:

```json
{
  "type": "https://diary.local/errors/session_revoked",
  "title": "Session is not active",
  "status": 401,
  "code": "session_revoked",
  "request_id": "UUID",
  "retryable": false,
  "details": {}
}
```

Códigos relevantes: `auth_invalid`, `session_revoked`, `session_source_invalid`,
`email_not_verified`, `account_disabled`, `rate_limited`, `validation_error`,
`not_found`, `subscription_required`, `quota_exceeded`, `provider_unavailable`,
`provider_timeout`, `media_invalid`, `media_too_large`, `idempotency_conflict`.

Recursos de outro usuário retornam `404`. `429` inclui `retry_after_seconds` em
`details`.
