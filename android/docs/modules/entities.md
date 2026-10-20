# Módulo entities

**Responsabilidade:** manter o cadastro local das pessoas, animais, lugares e
datas que aparecem nos relatos.

- `domain/Entities.kt`: `DiaryEntity`, `EntityProfile`, `EntityRelation`.
- `application/EntitiesRepository.kt`: listagem, perfil e edição.
- `adapters/RoomEntitiesRepository.kt` + `EntityMapping.kt`.
- `presentation/EntityListScreen.kt`: cadastros agrupados por tipo e criação.
- `presentation/EntityDetailScreen.kt`: identidade, contagem do período e total,
  acontecimentos, relatos de origem e correção da relação.
- `presentation/AvatarEditorScreen.kt` + `AvatarCatalog.kt`: modelo, cor de fundo
  e, para pessoas, pele, cabelo e roupa.
- `core/ui/EntityAvatar.kt`: desenho do avatar em Compose (sem assets de
  terceiros).

## Invariantes

- O identificador é estável: trocar nome ou aparência mantém menções, vínculos e
  acontecimentos.
- Pessoas com o mesmo nome são entidades distintas até confirmação explícita.
- Aparência nunca é inferida do texto; o usuário escolhe modelo e cores.
- O mesmo avatar é usado no mapa, na linha do tempo, no painel do nó e no
  cadastro, porque todos leem o mesmo registro.
