# Módulo auth

**Responsabilidade:** entrar com OIDC, manter a sessão cifrada, renovar tokens e
sair.

- `domain/AuthModels.kt`: estados e falhas.
- `application/AuthRepository.kt`: contrato usado pela UI.
- `adapters/OidcAuthRepository.kt`: Authorization Code + PKCE via navegador do
  sistema, troca no backend e persistência da sessão.
- `presentation/AuthViewModel.kt` e `AuthScreen.kt`: botão, abertura do navegador
  e mensagens de erro.

**Fluxo:** iniciar → abrir navegador → callback `callmeai://oidc` → validar
`state` → trocar código → gravar sessão → `SignedIn`.

**Falhas esperadas:** provedor indisponível, callback inválido, cancelamento,
rede. Em todas a UI mostra ação de tentar novamente.

**Dependências:** `AuthApi`, `SessionStore`, `DeviceIdStore`, Custom Tabs.
