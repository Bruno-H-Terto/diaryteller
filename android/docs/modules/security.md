# Módulo security

**Responsabilidade:** proteger credenciais e segredos locais.

- `Crypto.kt`: AES-256-GCM com chave do Android Keystore.
- `SessionStore.kt`: sessão cifrada em DataStore.
- `SecretFile.kt`: segredo aleatório para o SQLCipher.
- `Pkce.kt`: verifier/challenge S256.

Limites: protege repouso e trânsito TLS; não é ponta a ponta. Reinstalação
invalida chaves. Nenhum segredo é registrado em log.
