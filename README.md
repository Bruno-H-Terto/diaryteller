# Diary API

Backend for a local-first voice/text diary. The phone owns diary content,
recording and transcription; this backend authenticates devices, enforces plans
and quotas, and processes only the context the user selects for organization or
interpretation.

## Provedor de IA

A conversa usa um provedor compatível com OpenAI. Com `DEEPSEEK_API_KEY`
definido no `.env` (e `LLM_PROVIDER` vazio), o serviço `conversation` usa
`https://api.deepseek.com` com `deepseek-chat`. A chave fica apenas no servidor;
o app nunca a recebe.

## Pods

Cada diretório de topo é um pod: código, testes, Dockerfile, lock e migrations
próprios.

| Pod | Porta (compose) | Responsabilidade |
|---|---|---|
| `api` | 8001 | Borda pública, contas, sessões, quotas, OIDC, operações |
| `conversation` | 8010 | Respostas de IA em streaming, MCP, propostas |
| `exchange` | 8012 | Contextos autorizados, uploads, resultados, feed |
| `memory_mcp` | interno | Servidor MCP sobre registros selecionados |
| `notifications` | worker | Consumidor Kafka de e-mail e push |
| `maintenance` | CLI/job | Retenção, reconciliação e backups |

`shared/` contém contratos, segurança, observabilidade e mensageria usados no
build desses pods.

## Quick start

Requirements: Python 3.12–3.14, Poetry 2.x, Docker with Compose.

```bash
cp .env.example .env
make install
make keys          # development RS256 keys and local secret checks
make up            # postgres, mongo, mailpit, services
make migrate
make seed          # plans, permissions and roles
curl -s localhost:8001/health/ready
```

Run the full check suite with `make check`. Integration tests need the databases:

```bash
docker compose -f ops/compose.yaml --env-file .env up -d postgres mongo
TEST_DATABASE_URL=postgresql+asyncpg://diary:diary@localhost:55432/diary_test \
TEST_MONGO_URL='mongodb://diary:diary@localhost:57017/?authSource=admin' \
  poetry run pytest -m integration
```

## Local endpoints

- Identity: `http://localhost:8001/v1`
- Conversation: `http://localhost:8010/v1` (SSE on `POST /ai/responses`)
- Speech: `http://localhost:8011/v1`
- Mailpit UI: `http://localhost:8025`
- MCP is internal-only (`http://memory_mcp:8080/mcp` in compose).

Examples of every mobile flow are in [docs/mobile-contract.md](docs/mobile-contract.md).

## Documentation

Start at [docs/index.md](docs/index.md). Decisions and trade-offs are recorded
in [docs/adr/](docs/adr/). Contributions follow [AGENTS.md](AGENTS.md).

## Status and limitations

The external AI, store, push and email adapters are real HTTP/SMTP
implementations. Without provider credentials the affected smoke test is not
executed; deterministic test adapters are used only when `APP_ENV=test` or when
an explicit development flag enables them. The MVP does not store diary text,
audio, transcripts or AI results on the server.


## Aplicativo Android

O cliente móvel fica em [android/](android/README.md), com build e testes
próprios. Ele consome o contrato do backend e não faz parte dos pods.
