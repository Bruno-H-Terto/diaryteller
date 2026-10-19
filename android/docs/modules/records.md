# Módulo records e versions

**Responsabilidade:** criar registros, manter o original imutável e versionar
edições/restaurações.

- `domain/Records.kt`: `Record`, `RecordVersion` e regras de numeração.
- `application/RecordsRepository.kt`: contrato observável.
- `adapters/RoomRecordsRepository.kt`: grava rascunho, confirma, adiciona versão,
  restaura e enfileira sincronização.
- `presentation`: lista, editor e histórico (`vN ▾`).

**Invariantes:**

- Versão 1 é o original e não é sobrescrita.
- Editar depois de confirmado cria versão nova.
- Restaurar copia o conteúdo para uma nova versão com origem `RESTORE`.
- Rascunho não confirmado aceita edição e não altera versões confirmadas.

**Falhas:** conteúdo vazio é aceito como rascunho; erro de banco mantém o texto
no campo e permite salvar de novo. Sincronização permanece pendente até o
backend expor o contrato.
