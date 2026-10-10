// Shared test double for the Web Speech API surface used by useVoiceSearch.
// Plain functions (not vi.fn) so vitest's afterEach restoreAllMocks cannot
// strip the behaviour between tests.

export class FakeRecognition {
  static instances: FakeRecognition[] = []

  lang = ''
  continuous = false
  interimResults = false
  maxAlternatives = 1
  started = 0
  stopped = 0
  aborted = 0
  onstart: (() => void) | null = null
  onend: (() => void) | null = null
  onerror: ((event: { error: string }) => void) | null = null
  onresult: ((event: unknown) => void) | null = null

  constructor() {
    FakeRecognition.instances.push(this)
  }

  start() {
    this.started += 1
    this.onstart?.()
  }

  stop() {
    this.stopped += 1
    this.onend?.()
  }

  abort() {
    this.aborted += 1
  }
}

export const installFakeSpeechRecognition = () => {
  ;(window as unknown as { SpeechRecognition?: unknown }).SpeechRecognition = FakeRecognition
}

export const removeFakeSpeechRecognition = () => {
  delete (window as unknown as { SpeechRecognition?: unknown }).SpeechRecognition
  delete (window as unknown as { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition
}

export const finalSpeechResult = (transcript: string) => ({
  resultIndex: 0,
  results: [Object.assign([{ transcript }], { isFinal: true, length: 1 })],
})

export const interimSpeechResult = (transcript: string) => ({
  resultIndex: 0,
  results: [Object.assign([{ transcript }], { isFinal: false, length: 1 })],
})
