# Módulo navigation

**Responsabilidade:** alternar entre autenticação e as três abas principais.

- `Destinations.kt`: rotas.
- `AppNavigation.kt`: `NavHost` + barra inferior.
- `SubScreen.kt`: telas secundárias com ação de voltar.
- `ViewModelFactory.kt`: fábrica explícita de ViewModel, sem DI.
- `AppRoot.kt`: porta de entrada; observa `AuthState` e trata o redirect OIDC.

Abas: Diário, Conexões, Conversas e Ajustes. Editor, versões, captura de voz,
cadastros de entidades, avatar, acontecimento, privacidade e conta são rotas
empilhadas sem barra inferior. A barra some enquanto o teclado está aberto.

`DetailRoutes.kt` registra conexões, cadastros e acontecimento; `SettingsRoutes.kt`
registra ajustes, privacidade, conta e dados de exemplo. O período escolhido em
Conexões viaja como argumento `mes` para o detalhe da entidade.
