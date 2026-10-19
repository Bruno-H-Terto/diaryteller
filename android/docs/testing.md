# Testes e validação

## Automatizado

```bash
./gradlew :app:assembleDebug
./gradlew :app:testDebugUnitTest
./gradlew :app:lintDebug
./gradlew :app:check
./gradlew :app:connectedDebugAndroidTest   # exige emulador
python3 scripts/check_line_limits.py
```

Resultados (2026-10-19):

- `assembleDebug`, `lintDebug` e `check`: sucesso.
- `testDebugUnitTest`: **19 testes** — PKCE, versionamento, Room, sessão cifrada,
  captura (ditar/gravar) e parser SSE.
- `connectedDebugAndroidTest`: **3 testes** no AVD `callme_api36` (API 36) —
  Room+SQLCipher, áudio cifrado em repouso com reprodução e exclusão.
- Limite de 200 linhas: aprovado.

## Validação manual no emulador (backend real)

Fluxo executado com o stack completo (Postgres, Kafka/Redpanda, Dex, identity,
conversation, exchange) e DeepSeek real:

| Passo | Resultado |
|---|---|
| Login OIDC/PKCE no navegador do sistema | sessão criada e persistida |
| Registro de texto criado e editado | lista atualizada, versões gravadas |
| Versões | v1 Original → v2 USER → v3 RESTORE |
| Gravação de áudio | 19 s / 241 KiB, arquivo `.enc`, reprodução sem crash, descarte apagou |
| Ditado | reconhecedor on-device iniciou; aparelho sem pacote pt-BR → mensagem acionável, sem upload |
| Conversa com DeepSeek | resposta em streaming no app, citando apenas o registro selecionado |

## Achados corrigidos nesta validação

1. `RECORD_AUDIO` ausente no manifesto: ditado falhava com erro opaco.
2. `LANGUAGE_PACK_ERROR` era mapeado para `CLIENT_ERROR`: agora explica o pacote offline.
3. Seed deixava permissões/quotas de fala antigas no banco e quebrava o `/internal/authorize`.
4. Retrofit da conversa sem converter kotlinx: crash ao abrir a aba.
5. `401` derrubava o app: agora há refresh único e erro tratado.
6. Token de origem expirava em 15 min e impedia refresh após ociosidade: TTL de 30 dias.

## Ainda não executado

- Teste auditivo real de reprodução (emulador sem microfone/alto-falante útil).
- Ditado com pacote pt-BR instalado (depende de download no aparelho).
- Upload de anexos: endpoint pendente no backend.
