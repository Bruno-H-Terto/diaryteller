# Call Me AI — Android

Aplicativo local-first para registrar texto e áudio, consultar versões e
conversar com a IA sobre registros selecionados.

## Estado atual

Entrega incremental conforme `docs/`:

| Etapa | Estado |
|---|---|
| 1. Ambiente e estrutura | concluída |
| 2. Persistência protegida e autenticação | concluída |
| 3. Registros de texto e sincronização | parcial (local; endpoint de sync pendente no backend) |
| 4. Histórico de versões | concluída (local) |
| 6. Gravação e transcrição local | concluída (ditado on-device e gravação cifrada) |
| 5. Upload de anexos | pendente (contrato pronto no backend, implementação não) |
| 7. Conversa com IA | concluída (streaming com contexto selecionado, DeepSeek no servidor) |
| 8. Identidade visual | concluída (tema, ícone, splash; ver docs/design-system.md) |
| 9. Release | pendente |

O que é real: autenticação OIDC por Authorization Code + PKCE no navegador do
sistema, sessão cifrada com Android Keystore, Room sobre SQLCipher, criação e
versionamento local de registros, ditado transcrito no aparelho e gravação de
áudio cifrada localmente com TTS local para leitura.

O que é simulado/pendente: sincronização de registros (não há endpoint no
backend) e upload de anexos. Ver
[backend-requirements](docs/backend-requirements.md) e
[testing](docs/testing.md).

## Voz: somente no aparelho

- Transcrição usa `SpeechRecognizer` criado com `createOnDeviceSpeechRecognizer`
  e `EXTRA_PREFER_OFFLINE`. Não há fallback para mecanismo em nuvem.
- Sem pacote de idioma offline, o app informa a limitação e não envia áudio.
- Gravação vai para arquivo cifrado AES-256-GCM com chave do Keystore.
- Leitura de texto usa o `TextToSpeech` do Android.
- Nenhum áudio, transcrição ou texto é enviado ao backend; apenas o contexto
  selecionado para organização/interpretação.

## Requisitos

- JDK 17
- Android SDK 35 (`ANDROID_HOME`)
- Emulador ou dispositivo com API 26+

## Build e testes

```bash
export ANDROID_HOME=$HOME/Android/Sdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
./gradlew :app:assembleDebug
./gradlew :app:testDebugUnitTest
./gradlew :app:lintDebug
./gradlew checkLineLimits
```

APK: `app/build/outputs/apk/debug/app-debug.apk`.

## Backend

- Desenvolvimento: `http://10.0.2.2:8001/` (emulador) via `BACKEND_BASE_URL`.
- OIDC: provedor `dex` do compose do backend e redirect `callmeai://oidc`.
- No emulador, use `adb reverse tcp:8001 tcp:8001` e ajuste a URL se necessário.
- Nenhum segredo de cliente é embarcado.

## Estrutura

```text
app/src/main/java/com/callme/ai/
  bootstrap/     # Application e composição manual
  navigation/    # rotas e scaffold principal
  core/          # segurança, rede, banco, tema
  features/      # auth, records, settings (domain/application/adapters/presentation)
docs/            # arquitetura, segurança, contratos, testes, release, módulos
scripts/         # verificação do limite de 200 linhas
```
