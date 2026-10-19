# Escopo do MVP

## Objetivo

Fornecer o backend mínimo de um diário local-first: identidade por dispositivo,
permissões e assinatura verificadas no servidor, organização e interpretação de
contexto selecionado pelo celular, ferramentas MCP, notificações administrativas
e operação tolerante a falhas.

Gravação, transcrição e texto do diário acontecem somente no aparelho. O servidor
recebe apenas o contexto que o usuário escolhe enviar para uma operação de
organização/interpretação.

## Incluído

1. Cadastro, verificação de email, login, renovação rotativa, logout, listagem e
   revogação de sessões por dispositivo.
2. JWT curto + token de origem criptografado (`X-Session-Source`), validados
   contra a sessão persistida.
3. Permissões combinando conta ativa, sessão, papel, assinatura e quota.
4. Conversa por texto com SSE, resposta incremental, limite de perguntas e
   propostas estruturadas.
5. Contextos autorizados enviados pelo app para organização e interpretação
   (sem áudio, sem transcrição e sem TTS no servidor).
6. Servidor MCP interno com `search_memories`, `get_memory`, `organize_ideas`,
   `build_timeline` e `summarize_period`.
7. Alertas genéricos de novo acesso, leitura de notificações e push.
8. Logs sanitizados, outbox, retenção, reconciliação e backups administrativos.

## Excluído

- Landing page e qualquer sincronização de diário.
- Áudio, transcrição, TTS e texto do diário no servidor: esses fluxos são
  locais no aparelho.
- CRUD de registros, armazenamento de mídia, transcrições ou respostas.
- Índice semântico global, embeddings persistidos e leitura do histórico não
  enviado.
- Clonagem de voz, vídeo, fotos, identificação de falantes e chamadas em tempo
  real.
- Integrações públicas MCP, compartilhamento social e execução automática de
  metas/lembretes.
- Diagnóstico clínico, denúncia automática ou protocolos de emergência. O
  produto não substitui atendimento profissional.

## Fluxos que devem funcionar ponta a ponta

1. Cadastro → verificação → login → entitlements → alerta de sessão.
2. Texto → autorização → reserva → LLM → SSE → resultado validado.
3. Áudio → transcrição → confirmação local → conversa → TTS opcional.
4. Período selecionado → modo `timeline` → MCP → fontes → resultado local.
5. Compra → verificação no backend → entitlement → expiração/revogação.
6. Revogação de sessão → chamadas e streams bloqueados no prazo documentado.

## Definição de pronto

Um cliente HTTP completa os fluxos de texto, voz e memória paga com sessões
persistidas, permissões reais e provedores reais (ou adaptadores determinísticos
declarados como teste). Endpoints que retornam conteúdo fixo não atendem ao
critério.
