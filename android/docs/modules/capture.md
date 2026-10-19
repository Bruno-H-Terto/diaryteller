# Módulo capture (voz local)

**Responsabilidade:** ditar, gravar e ouvir áudio sem sair do aparelho.

- `domain/Capture.kt`: modos, disponibilidade e falhas de ditado.
- `application/CapturePorts.kt`: contratos `DictationEngine`, `AudioRecorder`,
  `RecordingStore`.
- `adapters/SpeechRecognizerDictation.kt`: reconhecedor **on-device**
  (`createOnDeviceSpeechRecognizer` + `EXTRA_PREFER_OFFLINE`). Sem modelo
  offline, retorna `MISSING_MODEL`/`UNSUPPORTED_DEVICE`.
- `adapters/MediaRecorderAudioRecorder.kt`: grava AAC/MP4 em cache privado.
- `adapters/EncryptedRecordingStore.kt`: cifra com AES-256-GCM, apaga o
  temporário, guarda metadados no Room e descriptografa para reprodução.
- `presentation/CaptureScreen.kt` + `CaptureViewModel.kt`: permissão de
  microfone, ditado com transcrição revisável, gravação e lista local.

**Fluxo de ditado:** microfone → eventos parciais → resultado final → revisão →
`createRecord` (versão 1 confirmada, original imutável).

**Fluxo de gravação:** microfone → parada → arquivo cifrado + metadados →
reprodução sob demanda → descarte apaga o arquivo.

**Falhas esperadas:** permissão negada, sem modelo offline, sem correspondência,
tempo esgotado, aparelho não suportado. Nenhuma delas envia áudio para fora.

**Limite conhecido:** transcrever um arquivo já gravado exigiria modelo ASR
embarcado. O ditado cobre a transcrição; a gravação serve para audição.
