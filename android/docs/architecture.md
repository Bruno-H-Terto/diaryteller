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

## Módulos de produto

- `features/records`: diário agrupado por dia, editor, versões, capa e áudio.
- `features/entities`: cadastro local e avatares desenhados em Compose.
- `features/connections`: mapa e linha do tempo sobre os mesmos dados.
- `core/media`: arquivos cifrados (capas, gravações) e reprodução.
- `core/database`: Room versão 2 com migração não destrutiva.

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

## Voz local

`features/capture` trata áudio sem servidor:

- `SpeechRecognizerDictation` cria o reconhecedor **on-device**; se o aparelho
  não tem modelo, retorna `MISSING_MODEL`/`UNSUPPORTED_DEVICE` e a UI explica.
- `MediaRecorderAudioRecorder` grava AAC/MP4 em cache privado.
- `EncryptedRecordingStore` cifra o arquivo (AES-256-GCM via `EncryptedFile`),
  guarda metadados no Room e apaga o temporário.
- `LocalSpeaker` usa `TextToSpeech` para ler texto no aparelho.

Nenhum adaptador desta feature fala HTTP. O backend só recebe o texto que o
usuário escolhe enviar em uma operação de organização/interpretação.

## Módulos Gradle

Um único módulo `:app`. A separação por features já permite extrair módulos se
houver ganho concreto (build paralelo ou reuso); hoje não há.
