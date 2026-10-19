# AGENTS.md

This repository is the backend of a local-first diary app. Diary content never
becomes durable server data. Read `docs/scope.md`, `docs/architecture.md` and
`docs/data-policy.md` before changing behavior.

## Invariants

- The phone is the source of truth for diary text, audio, transcripts, results,
  goals and reminders. Do not add CRUD endpoints for diary content, media
  buckets or server-side embeddings.
- Only `identity` writes identity and authorization tables.
- The server never trusts plan, permissions, owner or user id from the client.
- HTTP handlers validate transport, authenticate, call a use case and serialize.
  Domain code must not import FastAPI, SQLAlchemy, PyMongo, AI or MCP SDKs.
- Blocking work never runs on the event loop. Do not open SQL sessions during a
  stream, and never share an `AsyncSession` between concurrent tasks.
- Logs use the allowlist sanitizer. Never log bodies, prompts, transcripts,
  tokens, headers or provider exception bodies.
- External provider fallback requires an explicit privacy decision. There is no
  fallback in the MVP.

## Conventions

- Code, identifiers, comments and docstrings in English. Operational and
  integration documentation in Portuguese (`docs/`).
- Every Python module starts with a docstring describing responsibility,
  boundary and external effects. Public functions and classes document purpose,
  non-obvious parameters, return values, errors and side effects.
- Hand-written files have at most 200 physical lines, including tests,
  migrations, scripts and documentation pages. Generated lock/snapshot files are
  allowlisted by `scripts/check_line_limits.py`.
- Small functions and explicit bootstrap. `Protocol` only at replaceable
  boundaries. No generic `BaseService`, reflection injection or plugin systems.
- Timezone-aware UTC timestamps. Personal event dates keep their received
  offset and are never inferred from `recorded_at`.
- Commits in English, Conventional Commits, one logical stage at a time.

## Commands

```bash
make install      # Poetry workspace
make keys         # development keys/secrets (never commit keys/)
make up / down    # local stack
make migrate      # Alembic upgrade head
make seed         # plans, permissions, roles
make check        # ruff, black --check, pyright, line limits, tests
poetry run pytest -m "not integration and not e2e"
poetry run pytest -m integration
poetry run python scripts/check_line_limits.py
```

## When adding a service

1. Put transport schemas in `packages/contracts`, never ORM entities.
2. Define ports in `application/ports.py` and implement them in `adapters/`.
3. Wire dependencies explicitly in `bootstrap.py`.
4. Add health/readiness checks, settings validation, a README and tests.
5. Update `docs/` and `.env.example`.
6. Run `make check`; report tests that were not executed.
