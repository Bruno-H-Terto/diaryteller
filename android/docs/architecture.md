# Arquitetura

## Camadas

Cada funcionalidade se divide em quatro pastas:

```text
features/<feature>/
  domain/        # modelos e regras puras (sem Android)
  application/   # contratos de repositório e casos de uso
  adapters/      # implementações Room, HTTP, navegador, Keystore
  presentation/  # ViewModel e Compose
```

`domain` não importa Compose, Room, Retrofit ou navegação. `presentation`
depende de `application`, nunca de `adapters`. `bootstrap/AppContainer.kt` monta
as implementações e injeta nos ViewModels por construtor.

## Injeção

Composição manual, sem framework:

- `CallMeApplication` cria `AppContainer`.
- `AppContainer` cria sessão, API, banco e repositórios.
- `AppRoot` cria o `AuthViewModel`; as telas criam os demais ViewModels com
  factories explícitas.

## Fluxo de dados

```text
Compose → ViewModel → application (contrato) → adapter (Room/HTTP) → dados
```

A UI observa `StateFlow` do ViewModel; o ViewModel observa o banco. Escritas
acontecem no banco local primeiro e a sincronização (quando existir) atualiza o
mesmo estado.

## Sessão

1. App pede transação OIDC ao backend.
2. Abre o navegador do sistema com PKCE.
3. Recebe `callmeai://oidc` com `code`/`state`.
4. Backend troca o código e devolve tokens.
5. Sessão é cifrada com chave do Keystore e gravada em DataStore.

Renovação é centralizada em `SessionRefresher` (mutex, single-flight).

## Módulos Gradle

Um único módulo `:app`. A separação por features já permite extrair módulos se
houver ganho concreto (build paralelo ou reuso); hoje não há.
