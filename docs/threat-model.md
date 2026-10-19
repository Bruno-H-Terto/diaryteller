# Modelo de ameaças (MVP)

## Ativos

Conteúdo do diário em trânsito; credenciais; tokens de sessão/origem; estado de
assinatura e quota; recibos de operação; logs; chaves de assinatura, criptografia
e backup; tokens de push; base de contas.

## Fronteiras

Celular ↔ edge ↔ serviços; serviços ↔ identity (rede interna); conversation ↔
memory_mcp; serviços ↔ provedores (IA, loja, push, SMTP); jobs ↔ bancos/storage.

## Ameaças e mitigações

| Ameaça | Mitigação |
|---|---|
| Token de outro usuário | JWT RS256 com `kid`, `iss`, `aud`, `sid`; sessão no banco |
| Replay de origem em outra sessão | JWE autenticado com `sid`, `device_id`, `source_version`; comparação com banco |
| Refresh roubado/reutilizado | alta entropia, digest, rotação com lock, revogação da família |
| Cliente concede plano | plano e quota calculados no identity; body ignorado |
| Compra de outra conta | vínculo no provedor + transação única + verificação server-side |
| Corrida de quota | `UPDATE ... WHERE` atômico com lock e reserva |
| Webhook duplicado/fora de ordem | deduplicação por id de evento e estado monotônico |
| ID local inventado | validação contra conjunto enviado; sem leitura remota |
| Prompt injection no diário | conteúdo é dado; ferramentas sem rede/shell/arquivos; allowlist |
| Vazamento entre usuários | owner da sessão; credencial MCP vinculada à operação e contexto |
| Logs com conteúdo | allowlist, sem bodies/headers, TTL; Mongo indisponível não bloqueia |
| Força bruta/enumeração | Argon2id, respostas uniformes, throttle por identidade |
| Upload malicioso | limite de bytes, magic/duration check, subprocesso restrito |
| Processo morto deixa operação presa | lease/heartbeat, estados `interrupted`, cancelamento |
| Revogação durante stream | revalidação a cada 15 s e encerramento |
| Backup sem diário | dumps apenas administrativos, cifrados, checksum e restore test |
| Injeção de headers internos | edge remove `X-Internal-*`; rede interna; segredo por serviço |

## Riscos residuais

- Quem rouba JWT + token de origem pode reproduzi-los até expirar; não é prova
  criptográfica de posse do dispositivo.
- O provedor de IA processa conteúdo; retenção depende de contrato.
- Cancelamento é cooperativo: o provedor pode ter concluído antes da detecção.
- Não existe garantia de exatamente uma cobrança externa.
- Logs em Mongo e backups administrativos continuam sendo dados pessoais.
- Uma referência de fonte válida não garante correção semântica da IA.

## Fora de escopo

MCP público para terceiros, detecção de emergência e denúncia automática,
clonagem de voz, biometria, DRM, proteção contra dispositivo comprometido e
conformidade jurídica automatizada.
