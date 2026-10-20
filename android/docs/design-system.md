# Identidade visual

A identidade segue o arquivo "Diaryteller · UX e Navegação". Cores, tipografia,
formas e orçamento de movimento ficam em `core/ui` e são a única fonte para as
telas.

## Cores

| Papel | Claro | Escuro |
| --- | --- | --- |
| Primária (índigo) | `#51438F` | `#CBBFF5` |
| Destaque suave (lavanda) | `#EAE5F6` | `#3A2E73` |
| Acento (terracota) | `#B86443` | `#E9AE93` |
| Fundo (papel) | `#F7F4F0` | `#16141C` |
| Superfície | `#FFFDF9` | `#1F1D28` |
| Texto | `#2B2938` | `#EAE6F0` |
| Texto secundário | `#686477` | `#BDB8CB` |
| Linha divisória | `#E4DFEA` | `#3D3749` |

O fundo é uniforme (sem gradientes); cartões usam `surfaceContainerLowest`.
Terracota marca datas e estados de captura.

## Tipografia

Nunito nos títulos (400/600/700/800 variável) e Nunito Sans na leitura, ambas
embarcadas em `res/font` com licença em `assets/licenses/`:

- Títulos: `displaySmall` (36/42), `headlineLarge` (30/38), `headlineMedium`
  (26/34), semibold/bold e tracking negativo.
- Corpo: `bodyLarge` (16/26) para leitura, `bodyMedium` (15/24) em listas.
- Rótulos: `labelSmall` em caixa alta para datas, seções e contagens.

## Componentes

- `PillButton` (ação principal/tonal), `ChoicePill` (filtros), `CircleAction`
  (captura), `SegmentTabs` (Mapa/Linha do tempo), `SettingRow` e `TonalIcon`.
- Cartões com cantos 18–24 dp; pílulas em `CircleShape`.
- `EntityAvatar` desenha retratos cartoon em Compose (pessoa, animal, lugar,
  data) com modelo e cores por entidade.
- Barra inferior com quatro destinos (Diário, Conexões, Conversas, Ajustes) e
  indicador lavanda; some quando o teclado está aberto.

## Movimento

`Motion.kt` define `TAP_MS = 120`, `DISSOLVE_MS = 200`, `PANEL_MS = 240` e uma
curva única. `LocalReduceMotion` lê a escala de animação do sistema: com
"reduzir movimento" ativo, o mapa não executa a deriva vertical e nenhum quadro é
produzido fora da tela.
