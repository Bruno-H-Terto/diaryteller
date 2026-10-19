# Arquitetura e fronteiras

## Visão

```text
celular ──HTTPS──> api/ (borda pública + identidade)
                        │  outbox transacional
                        ▼
                    Redpanda/Kafka ──> services/notifications (email, push)
                        │
                        └──> demais vizinhos (incremental)

api/ ──> PostgreSQL (conta, sessão, quota, operação, outbox)
services/{conversation,speech,exchange,memory_mcp} ──> suas próprias portas
services/notifications ──> PostgreSQL próprio (inbox) + SMTP/push
services/maintenance ──> PostgreSQL, Mongo, storage, backups
```

## Unidades

| Unidade | Fronteira | Persistência |
|---|---|---|
| `api` | Borda pública + conta, sessão, permissões, assinatura, quota, recibos, OIDC | PostgreSQL próprio, provedor de cobrança |
| `conversation` | Resposta incremental, política, propostas, cliente MCP | Sem conteúdo durável |
| `speech` | Áudio limitado, transcrição, catálogo, TTS | Sem mídia persistida |
| `memory_mcp` | Ferramentas sobre contexto enviado | Sem banco/cache de memória |
| `notifications` | Consumidor Kafka de e-mail e push | PostgreSQL próprio (inbox) |
| `maintenance` | Expurgo, reconciliação, backups | PostgreSQL, Mongo, storage |
| `edge` | Roteamento, limites, remoção de headers forjados | Nenhuma lógica de domínio |

## Direção das dependências

`HTTP/MCP → aplicação → domínio`. Adaptadores implementam portas declaradas pela
aplicação. O domínio não importa FastAPI, SQLAlchemy, PyMongo, SDK de IA ou SDK
MCP. Não há injeção por reflexão: `bootstrap.py` monta cada dependência.

## Pacotes compartilhados

- `packages/contracts`: schemas Pydantic de transporte, erros, eventos SSE e
  propostas. Não contém entidades ORM nem lógica de aplicação.
- `packages/observability`: allowlist de log, sink Mongo limitado e middleware de
  `request_id`. Extraído após duplicação real entre cinco serviços.
- `packages/messaging`: envelope de evento versionado, tópicos, codec estrito,
  produtor e consumidor Kafka com inbox idempotente e DLQ.

## Layout

- `api/`: única borda HTTP pública. Contém identidade, sessões, quotas, OIDC e
  políticas; publica eventos via outbox transacional.
- `services/<vizinho>/`: conversation, speech, exchange, memory_mcp,
  notifications e maintenance. Cada um tem `src`, `tests`, `Dockerfile`,
  `pyproject.toml` e, quando precisa, migrations próprias.
- `packages/`: contratos, observabilidade, segurança e mensageria.
- `ops/`: compose principal e arquivos incluídos por domínio
  (`compose.android.yaml`, `compose.messaging.yaml`), Dex e scripts de init.

## Mensageria

Todo evento usa `EventEnvelope` (`event_id`, `type`, `version`, `producer`,
`occurred_at`, `key`, `payload`, `request_id`). `key` é o dono do recurso, o que
mantém a ordem por conta. Conteúdo de diário nunca vai para o broker; quando um
canal precisa de destinatário, o payload leva ciphertext produzido pelo `api`.

Fluxo de entrega:

1. `api` grava o evento na tabela `outbox_events` na mesma transação do fato.
2. `outbox-relay` publica no tópico indicado e marca `published`.
3. O vizinho consome com `enable_auto_commit=False`, deduplica por
   `inbox_events (consumer, event_id)` e confirma o offset.
4. Falha após o orçamento de tentativas vai para `<tópico>.dlq`.

Tópicos atuais: `diary.identity.sessions.v1`, `diary.identity.emails.v1`,
`diary.identity.accounts.v1`, `diary.maintenance.lifecycle.v1`.

## Sessão e autorização

Sessão é um contexto ativo do usuário, não uma cópia de permissões. O `api`
valida o JWT e o token de origem (JWE com dispositivo e versão) localmente contra
o registro persistido. Durante a migração incremental, conversation, speech e
exchange ainda chamam `POST /internal/authorize`; o alvo é validação local com
revogação propagada por evento.

## Operações

O identity é dono dos recibos de operação, da idempotência e das reservas de
quota. Conversation e speech criam a operação antes de chamar o provedor,
finalizam com consumo conhecido e consultam `/internal/operations/{id}/control`
durante streams longos. O recibo nunca guarda a resposta da IA.

## Fluxo de IA paga

1. Celular envia registros selecionados em `context`.
2. Conversation autoriza (`conversation:use` + modo) e reserva orçamento.
3. Modelo decide usar ferramenta; o cliente MCP injeta contexto e credencial JWE
   de curta duração, nunca o modelo.
4. `memory_mcp` valida audiência, operação, prazo e IDs presentes.
5. Conversation valida referências e emite `result`; o celular persiste.
6. Consumo conhecido finaliza o recibo e ajusta a reserva.

## Decisões de implantação

- Serviços escaláveis separadamente; nenhum estado de sessão em memória.
- MCP em HTTP stateless dentro da rede interna. Não há afinidade obrigatória.
- Sem Kubernetes, Kafka, Celery ou Redis no MVP. Outbox usa PostgreSQL e
  `SKIP LOCKED`.
- Go só será considerado com profiling reproduzível e ADR aprovado.
