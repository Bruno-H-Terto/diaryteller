# Testes e validação

## Automatizado

```bash
./gradlew :app:assembleDebug
./gradlew :app:testDebugUnitTest
./gradlew :app:lintDebug
./gradlew :app:check
./gradlew :app:connectedDebugAndroidTest   # exige emulador
python3 scripts/check_line_limits.py
```

Resultados (2026-10-19):

- `assembleDebug`, `lintDebug` e `check`: sucesso.
- `testDebugUnitTest`: **19 testes** — PKCE, versionamento, Room, sessão cifrada,
  captura (ditar/gravar) e parser SSE.
- `connectedDebugAndroidTest`: **3 testes** no AVD `callme_api36` (API 36) —
  Room+SQLCipher, áudio cifrado em repouso com reprodução e exclusão.
- Limite de 200 linhas: aprovado.

## Validação manual no emulador (backend real)

Fluxo executado com o stack completo (Postgres, Kafka/Redpanda, Dex, identity,
conversation, exchange) e DeepSeek real:

| Passo | Resultado |
|---|---|
| Login OIDC/PKCE no navegador do sistema | sessão criada e persistida |
| Registro de texto criado e editado | lista atualizada, versões gravadas |
| Versões | v1 Original → v2 USER → v3 RESTORE |
| Gravação de áudio | 19 s / 241 KiB, arquivo `.enc`, reprodução sem crash, descarte apagou |
| Ditado | reconhecedor on-device iniciou; aparelho sem pacote pt-BR → mensagem acionável, sem upload |
| Conversa com DeepSeek | resposta em streaming no app, citando apenas o registro selecionado |

## Conexões e cadastros (validação manual)

| Fluxo | Resultado |
|---|---|
| Diário agrupado | 5 registros do mesmo dia em um cartão, capa e ícone de áudio |
| Áudio | player na abertura do registro com a transcrição logo abaixo |
| Data do acontecimento | ano 2019 gravado e exibido como "2019", sem mês/dia inventados |
| Mapa | centro fixo maior, periféricos em faixas, rótulos fora do anel |
| Nó | painel com contagem do período, total do diário e acontecimentos |
| Agrupamento | "+N conexões" lista as conexões restantes |
| Revisão | sugestões confirmadas/descartadas saem de "Para revisar" |
| Linha do tempo | mês, dia recolhível, cartão com participantes, fonte e precisão |
| Precisão | "2019 · ano informado" e "Sem data definida" em seção própria |
| Cadastros | duas "Marina" distintas; avatar alterado reflete em lista e mapa |
| Período/filtros | trocar de aba e filtrar por Pessoa mantém período e contagens |
| Estado | abrir um detalhe e voltar preserva rolagem e dia expandido |
| Movimento | com escala de animação 0, duas capturas ficam idênticas (sem deriva) |
| Remoção | "Remover dados de exemplo" apaga somente itens `sample-` |

## Achados corrigidos nesta validação

1. `RECORD_AUDIO` ausente no manifesto: ditado falhava com erro opaco.
2. `LANGUAGE_PACK_ERROR` era mapeado para `CLIENT_ERROR`: agora explica o pacote offline.
3. Seed deixava permissões/quotas de fala antigas no banco e quebrava o `/internal/authorize`.
4. Retrofit da conversa sem converter kotlinx: crash ao abrir a aba.
5. `401` derrubava o app: agora há refresh único e erro tratado.
6. Token de origem expirava em 15 min e impedia refresh após ociosidade: TTL de 30 dias.

## Testes automatizados adicionados

- `NodeGeometryTest`: faixas de tamanho, centro sempre maior, anel sem repetição.
- `EventDateTest`: ano/mês/dia não inventam partes ausentes.
- `TimelineGroupingTest`: ordem de meses/dias e balde sem data.
- `ConnectionsCountingTest`: menções repetidas, versões, sugestões, período e
  homônimos contam como esperado.

## Ainda não executado

- Teste auditivo real de reprodução (emulador sem microfone/alto-falante útil).
- Ditado com pacote pt-BR instalado (depende de download no aparelho).
- Upload de anexos: endpoint pendente no backend.
- Calendário com miniaturas de capa (tela ainda não existe).
- Extração automática de entidades a partir do texto: os vínculos são criados
  manualmente ou pelo conjunto de exemplo.
