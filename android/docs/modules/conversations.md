# Módulo conversations

**Responsabilidade:** conversar com a IA usando registros escolhidos pelo usuário.

- `domain/Chat.kt`: mensagens, registros selecionáveis e eventos do stream.
- `application/ConversationRepository.kt`: contrato `ask(message, recordIds)`.
- `adapters/HttpConversationRepository.kt`: monta `POST /v1/ai/responses` com
  `context.coverage=selected_records`, consome SSE (`started`, `text_delta`,
  `result`, `completed`, `error`) e nunca fala com o provedor de IA.
- `presentation/ConversationViewModel.kt` + `ConversationScreen.kt`: chips de
  contexto, histórico em memória, streaming, cancelar e erro acionável.

**Privacidade:** só vai ao servidor o que o usuário marcar. Nenhum histórico
completo é reenviado; cada pergunta leva apenas os registros selecionados.

**Falhas:** `session_expired` (401) volta para login; `http_5xx`/rede mostram
mensagem e mantêm a pergunta na tela.

**Provedor:** a chave fica no backend (`DEEPSEEK_API_KEY`); o app não conhece
nem armazena credencial de IA.
