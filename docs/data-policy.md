# Política de dados e retenção

## Princípio

O celular é a fonte de verdade do diário. Gravação, transcrição, síntese de voz
e texto vivem apenas no aparelho; nenhum desses bytes é enviado ao backend. O
servidor recebe somente o contexto textual que o usuário seleciona para uma
operação de organização/interpretação, e não o persiste.

## Dados permitidos

| Categoria | Exemplos | Restrições |
|---|---|---|
| Conta | id, email, hash de senha, estado, locale, timezone | minimização e exclusão |
| Sessão | id, usuário, dispositivo aleatório, validade, revogação | digests apenas |
| Acesso | papéis, permissões, plano, validade, quotas | banco é a autoridade |
| Operação | id, tipo, estado, tempos, tokens/bytes, custo estimado | sem prompt/resposta |
| Segurança | evento, horário, referência administrativa | sem localização, IP curto |
| Push | token protegido, estado de entrega | dado operacional sensível |
| Logs | evento, serviço, latência, erro sanitizado, request_id | allowlist e TTL |

Metadados administrativos também podem ser dados pessoais. Não há promessa de
“nenhum dado pessoal no servidor” nem conformidade jurídica automática.

## Processamento temporário

- Corpo limitado e lido em memória durante a requisição; conexões do banco não
  ficam abertas durante streams.
- Nenhum upload de áudio: gravação e transcrição são locais. O contexto textual
  enviado é limitado por tamanho e validado pelo contrato de contexto.
- `Cache-Control: no-store` em respostas com conteúdo; proxies/APM sem captura
  de corpo; sem logs de request/response.
- Python não oferece apagamento criptograficamente garantido da RAM. Riscos de
  swap e crash dump pertencem ao ambiente de hospedagem.
- TLS obrigatório nas conexões externas; credenciais apenas por variáveis
  injetadas/secret manager.

## Provedores externos

O provedor de IA recebe conteúdo durante a operação. Isso não equivale a
processamento somente no celular. A retenção e o treinamento do provedor devem
ser contratualmente verificados antes de produção. Não há fallback automático
para outro provedor no MVP.

## Retenção inicial (defaults de engenharia)

| Dado | Prazo | Mecanismo |
|---|---|---|
| Logs operacionais | 7 dias | TTL no Mongo |
| Recibos de operação | 24 horas | expurgo agendado |
| Notificações administrativas | 30 dias | expurgo agendado |
| Eventos de segurança e sessões revogadas | 30 dias | expurgo agendado |
| Backups administrativos | 7 dias | rotação criptografada |
| Reservas abandonadas | expiração + reconciliação | job |

Esses prazos são configuráveis e não são conclusões jurídicas. Dados
financeiros seguem política própria documentada em [billing.md](billing.md).

## Exclusão de conta

`DELETE /me` exige reautenticação recente, revoga todas as sessões
imediatamente e marca a conta para remoção. Expurgos são idempotentes. Após
restauração de backup, o expurgo é reaplicado; nenhum backup contém diário,
transcrição ou resultado de IA.

## Logs

Campos permitidos: `timestamp`, `level`, `service`, `version`, `environment`,
`request_id`, `operation_id`, `event`, `status`, `duration_ms`, `error_code`,
`dropped_logs`. Nunca serializar modelo Pydantic completo, request, response,
headers, prompts, áudio, transcrição ou corpo de exceção do provedor.
