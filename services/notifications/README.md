# notifications

Serviço do backend do diário local-first. Responsabilidade, configuração e
comandos estão documentados em [docs/architecture.md](../../docs/architecture.md)
e nos contratos públicos em [docs/index.md](../../docs/index.md).

## Executar localmente

```bash
poetry install
poetry run uvicorn notifications.main:app --port 8000
```

## Testes

```bash
poetry run pytest
```
