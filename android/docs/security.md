# Segurança

## Chaves e tokens

- Chave AES-256-GCM por alias no Android Keystore (`callme.session`,
  `callme.database`). Chaves não são exportáveis e não saem do dispositivo.
- Sessão (access, refresh e source) é serializada e cifrada antes de ir para o
  DataStore.
- A senha do SQLCipher é aleatória por instalação, cifrada com a chave do
  Keystore e guardada em arquivo privado.
- Reinstalação ou perda da chave torna os dados antigos ilegíveis: o app trata
  como sessão inválida e recomeça.

## Banco e arquivos

- Room sobre SQLCipher; nenhum conteúdo em texto claro no banco.
- Gravações ficam em `files/recordings` cifradas com AES-256-GCM (chave do
  Keystore). A reprodução descriptografa para um cache temporário apagado ao
  final.
- `allowBackup=false` e regras de extração excluem banco, arquivos e prefs.
- Anexos (imagens/arquivos) usarão armazenamento privado protegido (etapa 5).
- Reconhecimento de fala e TTS são executados pelo sistema no aparelho; não há
  fallback para serviços de nuvem.

## Limites do modelo

O conteúdo é protegido em repouso no dispositivo e em trânsito por TLS. **Não é
criptografia de ponta a ponta**: quando o usuário envia um contexto, o backend e
os provedores autorizados processam o conteúdo.

## Regras de desenvolvimento

- Não logar texto, áudio, prompts, tokens ou URLs assinadas.
- Não criar criptografia própria; usar Keystore, TLS e primitivas padrão.
- HTTP sem TLS apenas no build `debug` para o backend local.
- Nenhum segredo no repositório; o cliente OIDC é público e usa PKCE.
