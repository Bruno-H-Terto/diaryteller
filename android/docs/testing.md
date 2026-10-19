# Testes e validação

## Executado neste ambiente

```bash
./gradlew :app:assembleDebug
./gradlew :app:testDebugUnitTest
python3 scripts/check_line_limits.py
```

Resultados:

- `assembleDebug`: sucesso; APK em `app/build/outputs/apk/debug/`.
- `testDebugUnitTest`: 16 testes aprovados.
  - PKCE: tamanho, alfabeto, S256 e unicidade.
  - Versionamento: numeração, restauração como nova versão.
  - Room: original imutável, nova versão, rascunho não altera versão confirmada,
    limpeza no logout.
  - Sessão: round-trip, limpeza e ciphertext ilegível → signed out.
  - Captura: parada entrega arquivo e duração ao armazenamento, disponibilidade de
    ditado é respeitada, descarte não grava, exclusão é local.
- Limite de 200 linhas: aprovado.
- `lintDebug`: aprovado.
- `connectedDebugAndroidTest`: 3 testes aprovados no AVD `callme_api36`
  (API 36): Room com SQLCipher confirma versão; gravação é cifrada em repouso,
  reproduz o conteúdo original e a exclusão remove o arquivo.
- Instalação e abertura do APK no emulador: sucesso; processo ativo e tela de
  autenticação renderizada.

## Ainda não executado

- Testes de upload de anexos e conversa: dependem dos endpoints pendentes.
- Ditado on-device real: depende de modelo de fala offline instalado no aparelho;
  a ausência é tratada e testada por estado, sem fallback de nuvem.
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
