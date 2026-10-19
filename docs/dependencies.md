# Dependências e versões

Verificado em **2026-10-19** contra PyPI e documentação oficial. O `poetry.lock`
é a fonte das versões transitivas. Python de referência: **3.13.3** (suportado:
3.12–3.14).

## Principais

| Pacote | Versão | Uso | Documentação |
|---|---|---|---|
| fastapi | 0.146.0 | HTTP/SSE | https://fastapi.tiangolo.com/ |
| pydantic | 2.14.1 | contratos | https://docs.pydantic.dev/ |
| sqlalchemy | 2.1.5 | ORM async | https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html |
| asyncpg | 0.32.0 | driver PostgreSQL | https://magicstack.github.io/asyncpg/ |
| alembic | 1.20.0 | migrations | https://alembic.sqlalchemy.org/ |
| pymongo | 4.19.0 | logs async (`AsyncMongoClient`) | https://www.mongodb.com/docs/languages/python/pymongo-driver/current/ |
| mcp | 2.3.0 | servidor/cliente MCP, Streamable HTTP | https://py.sdk.modelcontextprotocol.io/ |
| openai | 3.35.1 | LLM, transcrição, TTS | https://platform.openai.com/docs/api-reference |
| pyjwt | 2.15.1 | JWT RS256 | https://pyjwt.readthedocs.io/ |
| joserfc | 1.7.7 | JWE A256GCM | https://jose.authlib.org/ |
| argon2-cffi | 25.1.0 | Argon2id | https://argon2-cffi.readthedocs.io/ |
| cryptography | 50.0.2 | AES-GCM de segredos/backups | https://cryptography.io/ |
| google-auth | 2.62.0 | Google Play e FCM | https://googleapis.dev/python/google-auth/latest/ |
| httpx | 0.28.1 | clientes internos/provedores | https://www.python-httpx.org/ |
| requests | 2.32.5 | transporte OAuth do Google | https://requests.readthedocs.io/ |
| aiosmtplib | 5.1.3 | SMTP assíncrono | https://aiosmtplib.readthedocs.io/ |

## Desenvolvimento

`poetry` 2.5.1, `pytest` 9.1.1, `pytest-asyncio` 1.4.0, `ruff` 0.17.1,
`black` 26.10.1, `pyright` 1.1.414, `memray` 1.20.0.

## Instalação reproduzível

```bash
pipx install poetry==2.5.1 --python python3.13
poetry env use python3.13
poetry install --with dev          # workspace de desenvolvimento
poetry run alembic -c services/identity/alembic.ini upgrade head
```

Cada serviço possui `pyproject.toml` próprio e lock independente para imagem de
container. O projeto raiz inclui todos os pacotes apenas para desenvolvimento e
CI; não é a unidade de deploy.

## Escolhas externas

- **LLM/voz:** OpenAI (`gpt-4.1-mini`, `gpt-4o-mini-transcribe`,
  `gpt-4o-mini-tts`). O adaptador aceita `OPENAI_BASE_URL` compatível.
- **Loja:** Google Play (Android Publisher API + RTDN via Pub/Sub).
- **Push:** Firebase Cloud Messaging HTTP v1.
- **Email:** SMTP (Mailpit local).
- **MCP:** SDK Python 2.3.0, protocolo negociado pelo SDK (2026-07-28), transporte
  Streamable HTTP sem estado.

## Regras

- Não usar API lembrada de memória sem verificar na versão fixada.
- Não usar Motor em código novo.
- Não há fallback automático entre provedores.
- A tabela de preços de IA é versionada em `services/identity/src/identity/domain/pricing.py`;
  valores são estimativas e não substituem a fatura do provedor.
