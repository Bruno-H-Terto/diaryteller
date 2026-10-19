# Módulo navigation

**Responsabilidade:** alternar entre autenticação e as quatro abas.

- `Destinations.kt`: rotas.
- `AppNavigation.kt`: `NavHost` + `NavigationBar`.
- `AppRoot.kt`: porta de entrada; observa `AuthState` e trata o redirect OIDC.

Abas: Registros, Conversa, Linha do tempo, Conta. Editor e versões são rotas
empilhadas sem barra inferior. Conversa e timeline exibem estado pendente até as
etapas 7 e 8.
