# Módulo database

**Responsabilidade:** persistir registros, versões, entidades, acontecimentos e
fila de sincronização — tudo local, sob SQLCipher.

- `Entities.kt`: `records`, `record_versions`, `sync_queue`, `recordings`.
- `DiaryEntities.kt`: `record_metadata`, `diary_entities`, `record_entity_links`,
  `events`, `event_record_links`, `event_entity_links`, `relationships`.
- `RecordsDao.kt` / `EntitiesDao.kt` / `ConnectionsDao.kt`: consultas observáveis.
- `CallMeDatabase.kt`: Room versão 2.
- `DiaryMigration.kt`: `MIGRATION_1_2` adiciona as tabelas novas sem reescrever
  registros existentes; o áudio já gravado é ligado ao seu registro.
- `SampleDiary.kt`, `SampleEvents.kt`, `SampleAudio.kt`: conjunto sintético
  removível (prefixo `sample-`), usado nos testes manuais.

A passphrase é aleatória por instalação e cifrada pelo Keystore; nunca é
derivada de senha ou e-mail. `clearAll()` remove os dados da conta no logout.

## Regras de contagem

- Frequência = registros distintos (`COUNT(DISTINCT recordId)`) no período.
- Menções repetidas no mesmo texto não duplicam: a chave primária é
  (`recordId`, `entityId`).
- Versões vivem em `record_versions`; a ligação aponta para o registro, então
  editar não aumenta a contagem.
- Sugestões (`reviewState = 'SUGGESTED'`) nunca entram no mapa confirmado.

**Falhas:** chave perdida ou banco ilegível → recriar do zero (dados locais não
são recuperáveis). Não há backup em nuvem.
