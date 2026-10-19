# Desenvolvimento local

## Versões verificadas

- JDK 17 (`/usr/lib/jvm/java-17-openjdk-amd64`)
- Android SDK 35, build-tools 35.0.1/36.0.0
- Gradle 8.14.3 (wrapper)
- AGP 8.11.1, Kotlin 2.1.21, Compose BOM 2025.05.01

## Backend

O backend local sobe com `make up` no repositório raiz. O app usa
`BACKEND_BASE_URL` (debug: `http://10.0.2.2:8001/`).

Para dispositivo físico, troque `BACKEND_BASE_URL` em
`app/build.gradle.kts` pelo IP da máquina e mantenha HTTPS fora do build de
desenvolvimento.

OIDC: provedor `dex` (`http://localhost:5556/dex`) e redirect
`callmeai://oidc`. No emulador, `adb reverse tcp:5556 tcp:5556` faz o emissor
responder em `localhost`.

## Emulador

```bash
$ANDROID_HOME/emulator/emulator -list-avds
$ANDROID_HOME/emulator/emulator -avd Medium_Phone_API_36 -no-snapshot -gpu swiftshader_indirect
adb wait-for-device
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## Build

```bash
export ANDROID_HOME=$HOME/Android/Sdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
./gradlew :app:assembleDebug
```

## Problemas comuns

- `Toolchain ... does not provide JAVA_COMPILER`: `JAVA_HOME` aponta para um JRE;
  use o JDK 17.
- `Cleartext HTTP not permitted`: só o build `debug` permite HTTP local.
- OIDC retorna 404: confirme `OIDC_ENABLED` e o provedor no backend.
