# Módulo connections

**Responsabilidade:** mostrar as relações do diário em duas visões sobre o mesmo
conjunto de dados — mapa e linha do tempo.

- `domain/Connections.kt`: nós, eventos, revisão sugerida e `groupTimeline`.
- `domain/NodeGeometry.kt`: faixas de tamanho, raio do anel e posições.
- `application/ConnectionsRepository.kt`: contrato de leitura e revisão.
- `adapters/RoomConnectionsRepository.kt`: consultas agregadas em Room.
- `presentation/ConnectionsViewModel.kt`: período, filtros, seleção e expansão.
- `presentation/ConnectionsScreen.kt` + `ConnectionsHeader.kt`: cabeçalho,
  período, abas e barra de revisão.
- `presentation/ConnectionMap.kt` + `MapNodes.kt`: mapa com pan, zoom, deriva
  vertical e agrupamento.
- `presentation/TimelineView.kt` + `EventCard.kt`: meses, dias recolhíveis e
  cartões de acontecimento.
- `presentation/NodeDetailSheet.kt`, `GroupSheet.kt`, `ReviewSheet.kt`,
  `FilterSheet.kt`, `EventDetailScreen.kt`, `EventViewModel.kt`.

## Invariantes

- Período e filtros são os mesmos nas duas abas; trocar de visão não os perde.
- O centro tem tamanho fixo e é sempre o maior; nós periféricos crescem em
  faixas (46 → 68 dp) e nunca alcançam o centro.
- Contagem exata aparece no painel do nó, separada do total do diário.
- Sugestões ficam em "Para revisar" até confirmação explícita.
- Data do acontecimento usa a precisão informada: ano, mês, dia ou sem data.
- Expansão dos dias e posição da lista sobrevivem ao abrir um detalhe.

## Movimento

- Deriva vertical de 3 dp, ciclo lento, apenas nos nós visíveis.
- Nenhum quadro é produzido com "reduzir movimento" ativo, durante gestos ou com
  um painel aberto.
- Transições usam o orçamento de `core/ui/Motion.kt` (200 ms).
