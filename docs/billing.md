# Cobrança e entitlements

## Provedor escolhido

**Google Play** (Android Publisher API + Real-time Developer Notifications via
Pub/Sub). Apple App Store não é implementado no MVP. A escolha é reversível por
adaptador; o domínio não conhece a loja.

## Verificação

`POST /v1/billing/purchases/verify` recebe `product_id` e `purchase_token`.
O servidor:

1. consulta `purchases/subscriptionsv2/tokens/{token}` com credencial de serviço;
2. exige `externalAccountIdentifiers.obfuscatedExternalAccountId` igual ao HMAC
   do usuário (vínculo feito pelo app na compra);
3. mapeia `product_id` para plano configurado;
4. grava transação única por provedor, digest do token e token cifrado para
   reconciliação;
5. atualiza o entitlement.

Nunca aceite `is_premium`, preço, validade ou produto arbitrário do cliente.
Token de compra já vinculado a outro usuário é rejeitado.

## Webhooks

`POST /v1/billing/webhooks/google_play` valida OIDC do Pub/Sub (audiência e
service account), decodifica o RTDN e deduplica por `messageId`. Tipos: compra,
renovação, cancelamento, graça, retenção, revogação e expiração. Eventos fora de
ordem não estendem acesso indevidamente; renegociações positivas agendam
reconciliação.

Cancelamento mantém acesso até `current_period_end`. Refund/expiração encerram
imediatamente. O estado do provedor é a autoridade.

## Reconciliação

O job `diary-maintenance reconcile-billing` consulta assinaturas próximas do fim,
decifra o token, revalida no provedor e atualiza status/validade. Execução é
idempotente e protegida por advisory lock.

## Ambiente local

`BILLING_PROVIDER=fake` só é aceito fora de produção. Tokens sintéticos têm o
formato `<produto>:<nonce>` e webhooks usam `X-Fake-Signature` HMAC. O adaptador
fake é rejeitado em `APP_ENV=production`.

## Retenção financeira

Transações, recibos e estado de assinatura seguem política financeira própria e
não entram no expurgo de 24 h. A retenção de dados fiscais deve ser definida pelo
negócio/jurídico; os defaults deste MVP não são conclusão legal.
