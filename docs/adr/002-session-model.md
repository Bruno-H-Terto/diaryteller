# ADR 002 — Sessão ativa, JWT curto e token de origem

- **Status:** aceito
- **Data:** 2026-10-19

## Contexto

A sessão precisa ser revogável por dispositivo sem copiar permissões para um
token de longa duração. Um JWT sozinho não prova vínculo com o aparelho.

## Decisão

- `Session` é um registro pertencente ao usuário, com `device_id`,
  `source_version`, validade e revogação. Não há herança `Session(User)`.
- Access token JWT RS256, 10 minutos, com `iss`, `aud`, `sub`, `sid`, `jti`, `iat`,
  `exp`, `kid` e algoritmo restrito na verificação.
- Token de origem separado em JWE A256GCM, chave distinta, header
  `X-Session-Source`, contendo `sid`, `device_id`, `source_version`, propósito,
  emissão e validade.
- Refresh opaco de alta entropia, digest no banco, rotação transacional com lock.
  Reutilização revoga a família e a sessão e gera evento.
- Serviços de IA validam tokens e sessão no identity em cada operação sensível;
  durante stream, revalidam no máximo a cada 15 segundos.

## Consequências

- Chaves privadas não saem do identity; demais serviços precisam apenas das
  chaves públicas e da chave do JWE (ou consultam o identity).
- Roubo simultâneo de JWT e origem permite replay até expirar. Isso não é prova
  criptográfica de posse do aparelho e está documentado.
- O cliente deve serializar refresh; uma resposta perdida pode exigir novo login.
- Revogação é aplicada em chamadas novas imediatamente e em streams em até 15 s.
