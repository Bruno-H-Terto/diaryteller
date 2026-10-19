# Operação, retenção e backups

## Serviços e saúde

| Serviço | Liveness | Readiness |
|---|---|---|
| identity | `/health/live` | PostgreSQL (`SELECT 1`) |
| conversation | `/health/live` | identity `/health/ready` |
| speech | `/health/live` | identity `/health/ready` |
| memory_mcp | `/health/live` | sem persistência essencial |
| notifications | processo do worker | banco no primeiro ciclo |

Mongo indisponível não derruba readiness: apenas logs são afetados. PostgreSQL
indisponível impede autorização (fail closed). `/metrics` exige
`X-Metrics-Token`; sem token configurado retorna 404.

## Logs

JSON por linha com allowlist: timestamp, nível, serviço, versão, ambiente,
request_id, operation_id, evento, status, duração, código de erro e contagem de
descartes. Proibido logar corpo, headers, prompt, áudio, transcrição, tokens ou
corpo de exceção do provedor. Mongo tem TTL de 7 dias. Buffer limitado; descartes
são contados, nunca bloqueiam streams.

Eventos críticos de segurança também vão para `security_events` no PostgreSQL.
O outbox é a fonte de entrega de alertas.

## Retenção

`diary-maintenance retention` (idempotente, advisory lock):

- recibos de operação: 24 h após conclusão;
- reservas concluídas: 24 h; reservas abandonadas: 24 h de validade + liberação;
- notificações: 30 dias;
- eventos de segurança: 30 dias;
- sessões revogadas: 30 dias (refresh cascade);
- tokens de email: 7 dias/expurgo de usados;
- outbox entregue/falho: 7 dias;
- contas com exclusão vencida: anonimização e remoção de sessões/dispositivos/push.

Backups não contêm diário, transcrição ou resposta de IA.

## Backups

`backup-postgres` usa `pg_dump --format=custom`; `backup-mongo` usa `mongodump`.
Ambos cifram com AES-256-GCM em streaming, gravam checksum SHA-256 com permissão
0600 e rotacionam por `BACKUP_RETENTION_DAYS` (7). O destino em produção deve ser
durável e fora do host, com chave separada em secret manager.

`restore-check` decifra o backup, valida checksum, lista o arquivo com
`pg_restore` e, se `RESTORE_TARGET_DATABASE_URL` estiver definido, restaura em
banco isolado. Para Mongo, o MVP valida checksum/decifra; restauração real deve
ser feita em ambiente isolado com `mongorestore`. Após restauração, reaplique
expurgos e exclusões pendentes.

Agendamento: um único `maintenance schedule` ou cron/systemd chamando comandos
(`ops/backup-schedule.example`). Nunca um scheduler por réplica HTTP. Locks
`pg_try_advisory_lock` impedem duplicidade.

## Scheduler

O loop padrão roda retenção, reconciliação, backup Postgres e Mongo a cada
`SCHEDULER_INTERVAL_SECONDS` e `restore-check` a cada 7 ciclos. Pode ser
substituído por scheduler externo usando o mesmo CLI.

## Shutdown

Serviços param de aceitar novas operações, drenam até o limite do orquestrador,
cancelam streams restantes, finalizam recursos best-effort e fecham pools. O
lease de operação recupera processos mortos como `interrupted`.

## Runbook rápido

1. readiness 503: verificar PostgreSQL e identity; não ignorar.
2. Mongo fora: processamento continua; monitorar `dropped` e corrigir.
3. quota/abuso: reduzir limite do plano ou bloquear conta (estado `suspended`).
4. sessão suspeita: usuário revoga dispositivo; streams encerram em ≤15 s.
5. provedor de IA instável: 502/504, sem fallback automático; comunicar.
6. restauração: executar `restore-check`; reaplicar retenção/exclusões.
