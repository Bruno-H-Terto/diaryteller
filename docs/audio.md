# Áudio: fala para texto e texto para fala no aparelho

Comunicação por voz é a função central do app. Todo o caminho de áudio acontece
no aparelho: nenhum som, transcrição ou resposta falada cruza a rede.

## Reconhecimento (fala → texto)

O app embarca um modelo de fala **Vosk** em `android/app/src/main/assets/model-pt`
e o usa por dois caminhos:

| Caminho | Classe | Uso |
|---|---|---|
| microfone ao vivo | `VoskDictation` | conversa mão livre, ditado no editor |
| arquivo gravado | `VoskFileTranscriber` + `AudioFileDecoder` | transcrição de um relato por voz já gravado |

Por que um modelo embarcado e não o `SpeechRecognizer` do sistema: o
reconhecedor do Android depende de um pacote de idioma baixado pelo sistema. Sem
ele o app simplesmente não ouve — e a função central morre em aparelhos limpos ou
sem o pacote. O modelo no app elimina essa dependência e mantém a promessa de que
nada sai do celular.

O modelo **não é versionado** (31 MB, muda à parte do código):

```bash
make model    # baixa e descompacta em android/app/src/main/assets/model-pt
```

Sem ele, o app compila e informa "O modelo de fala não está neste build".

### Formatos

- Microfone: PCM 16 bits, 16 kHz, mono, `AudioSource.VOICE_RECOGNITION`.
- Arquivos: WAV 16 kHz mono é lido direto (`WavReader`); gravações AAC/MP4 são
  decodificadas com `MediaCodec` e reamostradas para 16 kHz (`AudioFileDecoder`).

### Limites do modelo embarcado

O modelo pequeno (`vosk-model-small-pt-0.3`) entende bem frases comuns e erra
nomes próprios: "Ana" pode virar "a". O diálogo compensa isso perguntando e
revisando, e o app não cria cadastro com nome de uma letra.

## Síntese (texto → fala)

`AndroidReplySpeaker` usa o `TextToSpeech` do aparelho no idioma escolhido no app.
Se a voz daquele idioma não estiver instalada, o app fica em silêncio em vez de
falhar. A resposta é lida ao final de cada turno e a escuta recomeça.

## Permissão

O microfone é pedido na primeira vez que a conversa entra em modo voz
(`rememberMicrophone`), com o mesmo tratamento já usado na tela de captura.

## Rehearsal no emulador

O emulador não tem microfone, então o painel do studio oferece rotas de ensaio
(somente builds `debug`):

```bash
# fala sintetizada ou arquivo empurrado para o app
adb push fala.wav /data/local/tmp/fala.wav
adb shell run-as com.callme.ai cp /data/local/tmp/fala.wav files/fala.wav
curl -X POST localhost:5557/voice/transcribe -d '{"path":"fala.wav"}'

# faz o botão do microfone reproduzir o arquivo pelo mesmo reconhecedor
curl -X POST localhost:5557/voice/replay -d '{"path":"fala.wav"}'

# anexa o arquivo a um registro como se tivesse sido gravado
curl -X POST localhost:5557/records/audio -d '{"recordId":"<id>","path":"fala.wav"}'
```

`ReplayDictation` emite os mesmos eventos parciais e finais do microfone, então o
laço `ConversationVoice` → backend → ações → chips é exercitado inteiro.

## Custos

O APK de debug cresce ~90 MB (modelo descompactado + `libvosk.so` para quatro
ABIs). Para publicação, avalie `abiFilters` apenas para `arm64-v8a` e a
distribuição do modelo por *asset pack*.
