# Testes e critérios de qualidade

## Comandos

```bash
make install
cp .env.example .env
make keys
docker compose -f ops/compose.yaml up -d postgres mongo mailpit
make migrate
make seed
make check
```

`make check` executa Ruff, Black `--check`, Pyright, verificador de 200 linhas e
pytest. Testes de integração usam PostgreSQL real:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://diary:diary@localhost:55432/diary_test \
TEST_MONGO_URL='mongodb://diary:diary@localhost:57017/?authSource=admin' \
  poetry run pytest -m integration
```

## Cobertura por área

- Contratos: contexto, timezone, IDs duplicados, propostas com confirmação,
  limite de perguntas, SSE com `sequence`/`operation_id`.
- Segurança: JWE adulterado/chave errada, JWT RS256 adulterado, source de outra
  sessão, senha Argon2id, canário de conteúdo descartado do log.
- Identidade (PostgreSQL real): cadastro/login, verificação obrigatória, refresh
  rotativo, reutilização revoga sessão, source incompatível, quota concorrente,
  idempotência, isolamento entre usuários, compra/refund, exclusão de conta.
- Conversa: validação de fontes inventadas, filtro de marcador, timeline via MCP
  fake, finalização de consumo, cancelamento e deadline de primeiro token.
- MCP: descoberta das cinco ferramentas, busca lexical, ID fora do contexto,
  permissão errada, timeline com eventos sem data.
- Áudio: magic bytes, duração WAV, limite de bytes/segundos, formato declarado
  incompatível.
- Observabilidade: allowlist remove prompt/headers/canário.

## Não executado automaticamente

- Smoke real de OpenAI, Google Play, FCM e SMTP externo: exige credenciais fora
  do CI. Adaptadores reais estão implementados; o smoke deve ser opt-in com dados
  sintéticos e limite de custo.
- Carga de 100/500 streams e Memray: ver [performance](performance.md).
- Teste de restauração Mongo completa: requer ambiente isolado.

## Resultado executado

Em 2026-10-19, com PostgreSQL e MongoDB reais em containers:

- `pytest -q` (unit + integração): **47 passaram**;
- `ruff check`, `black --check`, `pyright` e verificador de 200 linhas: passaram;
- Compose completo subiu; cadastro → email (Mailpit) → verificação → login →
  conversa SSE → compra fake → timeline via MCP funcionaram;
- retenção, backup PostgreSQL/Mongo cifrado e `restore-check` (pg_restore list +
  mongorestore `--dryRun`) foram executados;
- 100 e 500 streams sintéticos e Memray: ver [performance](performance.md).

Nunca declarar integração de produção validada apenas por fake. Smoke real de
OpenAI/Google Play/FCM não foi executado por ausência de credenciais.

## Dados de teste

Somente dados sintéticos. Testes usam banco `diary_test`, criado e destruído por
fixture; nenhum teste aponta para o banco de desenvolvimento/produção. Chaves de
teste são geradas em diretório temporário.
