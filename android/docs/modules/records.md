# Módulo records e versions

**Responsabilidade:** criar registros, manter o original imutável e versionar
edições/restaurações.

- `domain/Records.kt`: `Record`, `RecordVersion` e regras de numeração.
- `application/RecordsRepository.kt`: contrato observável.
- `adapters/RoomRecordsRepository.kt`: grava rascunho, confirma, adiciona versão,
  restaura e enfileira sincronização.
- `presentation/DiaryScreen.kt` + `DiaryRows.kt`: registros agrupados por dia em
  um único cartão, com busca local, filtro de rascunhos e miniatura de capa.
- `presentation/EditorScreen.kt`: editor sem distrações (título + corpo, um toque
  para concluir). O texto é uma única string; a primeira linha é o título.
- `presentation/EditorMedia.kt` + `AudioPickerSheet.kt`: capa opcional e um áudio
  anexado, com a transcrição logo abaixo do player.
- `presentation/EditorEventDate.kt`: data do acontecimento, separada da data de
  registro e com precisão explícita.
- `presentation/VersionsScreen.kt`: histórico com restauração confirmada.

**Capas e áudio:** a capa é copiada para `files/covers` cifrada e serve apenas
como elemento visual — não comprova lugar ou acontecimento. O áudio anexado é uma
gravação local (`files/recordings`); a transcrição exibida é o próprio texto do
registro.

**Datas:** `record_metadata.diaryDate` é o dia a que o registro pertence;
`eventDate`/`eventDatePrecision` guardam a data narrada. Só o que o usuário
informou é gravado — ano sem mês, mês sem dia ou nenhuma data.

**Invariantes:**

- Versão 1 é o original e não é sobrescrita.
- Editar depois de confirmado cria versão nova.
- Restaurar copia o conteúdo para uma nova versão com origem `RESTORE`.
- Rascunho não confirmado aceita edição e não altera versões confirmadas.

**Falhas:** conteúdo vazio é aceito como rascunho; erro de banco mantém o texto
no campo e permite salvar de novo. Sincronização permanece pendente até o
backend expor o contrato.
