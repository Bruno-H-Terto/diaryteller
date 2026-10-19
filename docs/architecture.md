# Arquitetura e fronteiras

## Visão

```text
celular ──HTTPS──> edge ──> services/{identity,conversation,speech}
                                  │            │
                                  │            └── MCP (HTTP interno) ──> memory_mcp
                                  └── /internal/* ───────────────────────> identity
identity ──> PostgreSQL (identidade, autorização, operações, outbox)
conversation/speech/memory_mcp ──> Mongo (logs sanitizados)
notifications (worker) ──> PostgreSQL outbox, SMTP, push
maintenance (job) ──> PostgreSQL, Mongo, destino de backup
```

## Unidades

| Unidade | Fronteira | Persistência |
|---|---|---|
| `identity` | Conta, sessão, permissões, assinatura, quota, recibos | PostgreSQL, provedor de cobrança |
| `conversation` | Resposta incremental, política, propostas, cliente MCP | Sem conteúdo durável |
| `speech` | Áudio limitado, transcrição, catálogo, TTS | Sem mídia persistida |
| `memory_mcp` | Ferramentas sobre contexto enviado | Sem banco/cache de memória |
| `notifications` | Outbox, email, push, alertas | PostgreSQL (ledger próprio) |
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

## Sessão e autorização

Sessão é um contexto ativo do usuário, não uma cópia de permissões. Todo serviço
de IA chama `POST /internal/authorize` no identity com o JWT e o token de origem.
O JWT identifica a sessão; o token de origem (JWE) vincula dispositivo e versão.
Ambos precisam corresponder ao registro persistido.

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
