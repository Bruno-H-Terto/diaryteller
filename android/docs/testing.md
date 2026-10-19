# Testes e validação

## Executado neste ambiente

```bash
./gradlew :app:assembleDebug
./gradlew :app:testDebugUnitTest
python3 scripts/check_line_limits.py
```

Resultados:

- `assembleDebug`: sucesso; APK em `app/build/outputs/apk/debug/`.
- `testDebugUnitTest`: 12 testes aprovados.
  - PKCE: tamanho, alfabeto, S256 e unicidade.
  - Versionamento: numeração, restauração como nova versão.
  - Room: original imutável, nova versão, rascunho não altera versão confirmada,
    limpeza no logout.
  - Sessão: round-trip, limpeza e ciphertext ilegível → signed out.
- Limite de 200 linhas: aprovado.
- `lintDebug`: aprovado.
- `connectedDebugAndroidTest`: 1 teste aprovado no AVD `callme_api36`
  (API 36) — abre Room com SQLCipher e confirma uma versão.
- Instalação e abertura do APK no emulador: sucesso; processo ativo e tela de
  autenticação renderizada.

## Ainda não executado

- Testes de upload/transcrição/conversa: dependem dos endpoints pendentes.
- Teste manual do fluxo OIDC completo: depende do Dex e do backend em execução.

## Emulador

AVD criado para este projeto (não reutiliza dados de outros):

```bash
avdmanager create avd -n callme_api36 \
  -k "system-images;android-36;google_apis_playstore;x86_64"
$ANDROID_HOME/emulator/emulator -avd callme_api36 -no-window -no-snapshot &
adb wait-for-device
./gradlew :app:connectedDebugAndroidTest
```

## Estratégia

- Regras puras (PKCE, versionamento) em testes JVM rápidos.
- Persistência em Room com Robolectric.
- Adaptadores HTTP com servidor local (MockWebServer) nas próximas etapas.
- Fluxos essenciais no emulador com dados de teste.
