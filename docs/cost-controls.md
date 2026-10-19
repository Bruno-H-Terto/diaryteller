# Controle de custos

## Reserva antes do provedor

Toda operação paga cria um recibo idempotente e reserva quota atomicamente no
identity. A reserva usa `UPDATE ... WHERE used + amount <= limit`, impedindo
corridas. A finalização substitui a estimativa pelo consumo conhecido. Consumo
externo incerto permanece reservado; não se afirma que o cancelamento evitou
cobrança.

## Limites

- Janela diária UTC por plano (AI tokens, segundos de fala, chamadas de memória).
- Estimativa por operação: AI `1200 + (mensagem+contexto)/3`, limitada a 8.000;
  transcrição pela duração validada; TTS por `caracteres/15`.
- Contexto 256 KiB, 50 registros, 8.000 caracteres por mensagem; áudio 10 MiB/120 s;
  TTS 4.000 caracteres; 4 ferramentas MCP por operação.
- Concorrência por usuário e por fornecedor configurável no deploy.
- Orçamento global: reduzir limites de plano e/ou bloquear contas; não há
  contador global embutido no MVP (extensão documentada).

## Preços

Custo é estimativa, com versão da tabela de preços e moeda. Não fixar preços de
IA desatualizados no código: a tabela fica em configuração/deploy e é usada no
recibo (`reserved_amount`, `actual_amount`). A fatura do provedor é a autoridade.

## Abuso

- Login limitado por janela; senha Argon2id.
- Quota por usuário e plano; respostas 429 com `Retry-After`/detalhes.
- Áudio validado por bytes e duração; `ffprobe` em subprocesso com CPU/memória.
- Streams cancelados liberam recursos locais; o provedor pode já ter cobrado.
- Sem fallback automático para outro provedor.
