# maintenance

Jobs de retenção, reconciliação de assinatura e backups administrativos
criptografados. Não processa nem armazena conteúdo do diário.

```bash
poetry install
poetry run diary-maintenance retention
poetry run diary-maintenance backup-postgres
poetry run diary-maintenance schedule
```

Requer `pg_dump`, `pg_restore`, `mongodump` e `mongorestore` no PATH.
