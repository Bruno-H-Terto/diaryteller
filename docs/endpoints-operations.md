# Operações, assinatura e consumo

## Operações

`GET /v1/operations/{id}` retorna apenas metadados e nunca o conteúdo de uma
resposta antiga:

```json
{
  "id": "UUID",
  "type": "ai_response",
  "state": "succeeded",
  "created_at": "...",
  "started_at": "...",
  "finished_at": "...",
  "updated_at": "...",
  "error_code": null,
  "result_available": false
}
```

`POST /v1/operations/{id}/cancel` retorna `202` e o estado atual. O stream
observa `cancel_requested` e encerra; se o provedor já concluiu, a operação pode
terminar antes da detecção. A chamada externa pode ter sido cobrada.

## Assinatura

| Método | Rota | Comportamento |
|---|---|---|
| POST | `/v1/billing/purchases/verify` | valida no provedor e atualiza entitlement |
| POST | `/v1/billing/webhooks/{provider}` | autenticado pelo provedor; sem auth de usuário |
| GET | `/v1/me/usage` | quotas e restante do próprio usuário |
| GET | `/v1/me/entitlements` | plano, permissões e validade |

O plano nunca vem do corpo. A compra é vinculada à conta no provedor; token
reutilizado por outro usuário é rejeitado. Webhooks são deduplicados por evento e
estado não retrocede. Expiração/refund bloqueiam a próxima autorização.

## Quotas

Reserva atômica antes do provedor:

1. `POST /internal/operations/reserve` cria recibo idempotente e aplica
   `UPDATE ... WHERE used + amount <= limit`.
2. O provedor é chamado.
3. `finish` substitui a estimativa pelo consumo conhecido; consumo desconhecido
   permanece reservado e marcado implicitamente como incerto.

Limites por plano (defaults em `identity/seed.py`):

| Plano | AI tokens/dia | Fala s/dia | Chamadas de memória/dia |
|---|---|---|---|
| free | 20.000 | 300 | 0 |
| plus | 200.000 | 1.800 | 100 |
| pro | 1.000.000 | 3.600 | 500 |

Reservas abandonadas expiram em 24 h e são reconciliadas pelo job de retenção.
Corrida de quota não ultrapassa o limite. Limites globais e por usuário podem ser
reduzidos por configuração/deploy.

## Erros

`404 operation_not_found` para operação de outro usuário ou inexistente.
`409 operation_in_progress`, `409 operation_completed`, `409 idempotency_conflict`,
`429 quota_exceeded`, `403 subscription_required`, `502 provider_unavailable`,
`504 provider_timeout`.
