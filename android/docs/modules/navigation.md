# Módulo navigation

**Responsabilidade:** alternar entre autenticação e as três abas principais.

- `Destinations.kt`: rotas.
- `AppNavigation.kt`: `NavHost` + barra inferior.
- `SubScreen.kt`: telas secundárias com ação de voltar.
- `ViewModelFactory.kt`: fábrica explícita de ViewModel, sem DI.
- `AppRoot.kt`: porta de entrada; observa `AuthState` e trata o redirect OIDC.

Abas: Diário, Conversas e Ajustes. Editor, versões, captura de voz, privacidade e
conta são rotas empilhadas sem barra inferior. A barra some enquanto o teclado
está aberto para liberar espaço ao campo em foco.
