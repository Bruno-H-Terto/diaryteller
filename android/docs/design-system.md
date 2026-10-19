# Identidade visual

A identidade segue o arquivo de referência "Call Me — Aplicativo Android · UX e
Navegação". Cores, tipografia e formas ficam em `core/ui` e são a única fonte
para as telas.

## Cores

| Papel | Claro | Escuro |
| --- | --- | --- |
| Primária (verde floresta) | `#24594D` | `#9CD3C2` |
| Superfície tonal | `#E5EDE6` | `#26302B` |
| Acento (terracota) | `#9C4934` | `#E5A48F` |
| Fundo (papel) | `#F7F5EF` | `#14120F` |
| Texto | `#242B29` | `#EFECE4` |
| Texto secundário | `#5D6863` | `#B6BAAE` |
| Linha divisória | `#DDE3DB` | `#3A3833` |

O terracota marca data, estado de gravação e origem da versão. O verde tonal
preenche cartões de contexto, chips selecionados e indicador da aba ativa.

## Tipografia

Poppins (SIL Open Font License 1.1, licença em
`app/src/main/assets/licenses/poppins-OFL.txt`), embarcada em `res/font`:

- Títulos: `displaySmall` (38/44), `headlineLarge` (32/40),
  `headlineMedium` (28/36), sempre semibold e com tracking negativo.
- Corpo: `bodyLarge` (16/26) para leitura, `bodyMedium` (15/24) para listas.
- Rótulos: `labelSmall` em caixa alta para datas e seções.

## Formas e componentes

- Cantos: cartões 16–24 dp, pílulas 24 dp, botões de ação em círculo.
- `PillButton` para ação principal e tonal; `ChoicePill` para filtros e contexto;
  `CircleAction` para captura; `SettingRow` para ajustes.
- Barra inferior com três abas (Diário, Conversas, Ajustes) e indicador em
  `primaryContainer`; some quando o teclado está aberto.
- Ícone do app: símbolo do diário em `#1C5F50` com canto terracota, fundo papel;
  ícone adaptativo, monocromático e splash usam o mesmo desenho.
