# notifications

Serviço do backend do diário local-first. Responsabilidade, configuração e
comandos estão documentados em [docs/architecture.md](../../docs/architecture.md)
e nos contratos públicos em [docs/index.md](../../docs/index.md).

## Executar localmente

```bash
poetry install
poetry run python -m notifications.jobs.worker
```

## Testes

```bash
poetry run pytest
```
