# Módulo database

**Responsabilidade:** persistir registros, versões e fila de sincronização.

- `Entities.kt`: `records`, `record_versions`, `sync_queue`.
- `RecordsDao.kt`: consultas observáveis e transações.
- `CallMeDatabase.kt`: banco Room versão 1.
- `DatabaseFactory.kt`: abre Room com SQLCipher.

A passphrase é aleatória por instalação e cifrada pelo Keystore; nunca é
derivada de senha ou e-mail. `clearAll()` remove os dados da conta no logout.

**Falhas:** chave perdida ou banco ilegível → recriar do zero (dados locais não
são recuperáveis). Não há backup em nuvem.
