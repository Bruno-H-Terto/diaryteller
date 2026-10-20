# Diálogo que altera o diário

O usuário conversa (por texto ou voz) e o aplicativo cria perfis, identifica
perfis existentes, registra acontecimentos, vincula participantes e corrige datas
sem sair da conversa. O servidor **não** escreve conteúdo de diário: ele propõe
`DiaryAction` e o aparelho valida, grava e mostra o que mudou.

## Fluxo

1. O app envia a fala (ou o texto) com o contexto escolhido e um `diary`
   (snapshot local): entidades, acontecimentos e a data de hoje.
2. O pod `conversation` responde em streaming: texto visível e, no evento
   `result`, `actions` validados.
3. O app mostra as ações em um cartão de revisão. Nada é escrito antes de
   **Confirmar alterações**; **Descartar** não cria registro, perfil ou evento.
4. Após confirmação, `RoomDiaryMutator` aplica as ações e mostra chips
   ("Novo cadastro · Carlos", "Acontecimento · Almoço com Ana").
5. Em modo voz, a resposta é lida pelo `TextToSpeech` do aparelho e a escuta
   recomeça — turnos sem toque.

## Ações

| Ação | Campos | Efeito local |
|---|---|---|
| `create_entity` | `ref`, `entity_kind`, `name`, `relation` | cria cadastro e, se houver, a relação com "você" |
| `create_event` | `ref`, `title`, `summary`, `event_date`, `precision`, `participants`, `source_ids` | cria acontecimento e vincula participantes e relatos |
| `link_entity` | `entity`, `source_id` ou `event` | vincula menção a um registro ou acontecimento |
| `set_event_date` | `event`, `event_date`, `precision` | corrige quando algo aconteceu |

`precision` segue o modelo local (`day`, `month`, `year`, `unknown`). Sem data, a
precisão é obrigatoriamente `unknown`: nunca se inventa mês ou dia.

## Confiança e revisão

Cada ação carrega `certainty`:

- `explicit` → `CONFIRMED`: o usuário afirmou o fato.
- `inferred` → `SUGGESTED`: interpretação; aparece na fila **Para revisar** e não
  entra nas contagens confirmadas.

`origin` do vínculo é `AI` e o estado de revisão segue a mesma regra.

## Referências e evidência

Uma ação só pode apontar para:

- ids de entidades e acontecimentos enviados no `diary`; ou
- refs `new:N` declaradas na **mesma** resposta.

`source_ids` só aceita registros do contexto da requisição. A validação acontece
duas vezes: no pod (`kept_actions`) e no app (`DiaryActionParser`). No pod, uma
ação inválida é descartada sozinha — a resposta continua legível; no app, campos
ausentes ou tipos desconhecidos fazem a ação ser ignorada em vez de gravada.

## Limites

- Até 6 ações por resposta; até 10 participantes e 20 fontes por acontecimento.
- Snapshot: 60 entidades, 40 acontecimentos, rascunho até 4.000 caracteres.
- O snapshot é usado em uma requisição e não é retido pelo servidor.
- O servidor não recebe áudio: a transcrição e a síntese são do aparelho.

## Como validar

```bash
make test-env                 # pilha, banco, emulador e app
poetry run python -m ops.studio   # painel: aba Pessoas e Diário mostram o resultado
make simulate                 # frase pronta para o primeiro ensaio
make simulate TEXT="Ontem almocei com Carlos no centro"
make simulate AUDIO=/caminho/para/fala.wav
```

No painel, a aba **Pessoas** lista o cadastro criado pela conversa e a aba
**Diário** mostra o acontecimento com a data e a presença de áudio. O comando
`curl -s http://127.0.0.1:5557/state` devolve o estado local completo.
