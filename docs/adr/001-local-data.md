# ADR 001 — O celular é a fonte de verdade do diário

- **Status:** aceito
- **Data:** 2026-10-19

## Contexto

O produto é um diário pessoal sensível. Sincronizar texto, áudio, transcrições e
resultados criaria um acervo remoto com alto risco e custo, além de exigir busca
global e políticas de retenção complexas.

## Decisão

O celular guarda todo o conteúdo do diário e o índice de busca local. O backend
recebe registros apenas como contexto de uma operação, processa em memória e
devolve o resultado. Não há CRUD de diário, buckets de mídia, embeddings
persistidos nem cache de conteúdo.

O servidor conserva somente dados administrativos: conta, sessão, permissões,
assinatura, quotas, recibos de operação, outbox, auditoria e logs sanitizados.
IDs de registros são gerados no cliente e têm significado apenas dentro da
operação.

## Consequências

- Busca sobre histórico não enviado é impossível; o contrato devolve necessidade
  de ampliar contexto e o celular seleciona mais registros.
- Não é possível repetir uma resposta sem novo conteúdo e nova chave.
- O backend pode ser menor, mas deve limitar contexto, áudio e concorrência.
- Backup remoto nunca contém diário.
- Metadados administrativos continuam sujeitos a minimização e exclusão.
