# Release

## Versão

- `versionCode` incremental em `app/build.gradle.kts`.
- `versionName` no formato `MAJOR.MINOR.PATCH`.
- `minSdk 26`, `targetSdk 35`.

## Assinatura

Nunca versionar keystore ou senhas. Configure por variável de ambiente:

```kotlin
signingConfigs {
    create("release") {
        storeFile = file(System.getenv("CALLME_KEYSTORE") ?: "missing.jks")
        storePassword = System.getenv("CALLME_STORE_PASSWORD")
        keyAlias = System.getenv("CALLME_KEY_ALIAS")
        keyPassword = System.getenv("CALLME_KEY_PASSWORD")
    }
}
```

## Pacote

```bash
./gradlew :app:bundleRelease
```

Artefato: `app/build/outputs/bundle/release/app-release.aab`.

## Checklist

- `./gradlew check` e `./gradlew :app:lintDebug` sem erros.
- Testes instrumentados executados no emulador/dispositivo.
- `BACKEND_BASE_URL` de produção com HTTPS.
- `allowBackup=false` e regras de extração conferidas.
- Política de privacidade e classificação de conteúdo na Play Console.
- Nenhum log com conteúdo, tokens ou URLs assinadas.
