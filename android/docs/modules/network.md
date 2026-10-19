# Módulo network

**Responsabilidade:** falar com o backend e renovar sessão.

- `Dtos.kt`: corpos OIDC, refresh e `/v1/me`.
- `AuthApi.kt`: contrato Retrofit.
- `ApiClient.kt`: OkHttp com `Authorization` e `X-Session-Source`, sem credencial
  em chamadas de autenticação.
- `SessionRefresher.kt`: refresh single-flight com mutex.

**Falhas:** 401 sem refresh → sessão limpa; 5xx/429 → erro recuperável; refresh
concorrente usa o mesmo resultado.
