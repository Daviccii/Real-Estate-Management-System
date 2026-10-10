import { useCallback, useEffect, useRef, useState } from 'react'

// Minimal local typings for the (still vendor-prefixed) Web Speech API —
// lib.dom does not guarantee these across TypeScript versions.

interface SpeechAlternativeLike {
  transcript: string
}

interface SpeechResultLike {
  isFinal: boolean
  length: number
  [index: number]: SpeechAlternativeLike
}

interface SpeechResultListLike {
  length: number
  [index: number]: SpeechResultLike
}

interface SpeechResultEventLike {
  resultIndex: number
  results: SpeechResultListLike
}

interface SpeechErrorEventLike {
  error: string
}

interface SpeechRecognitionLike {
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  onresult: ((event: SpeechResultEventLike) => void) | null
  onerror: ((event: SpeechErrorEventLike) => void) | null
  onend: (() => void) | null
  onstart: (() => void) | null
  start: () => void
  stop: () => void
  abort: () => void
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike

const ERROR_MESSAGES: Record<string, string> = {
  'not-allowed': 'Microphone access was blocked. Allow microphone permission and try again.',
  'service-not-allowed': 'Voice input is not available in this browser.',
  'no-speech': "Didn't catch that — please try again.",
  'audio-capture': 'No microphone was found on this device.',
  network: 'Voice recognition needs a network connection.',
}

export const voiceErrorMessage = (code: string): string =>
  ERROR_MESSAGES[code] ?? 'Voice input failed — please try again.'

export function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === 'undefined') return null
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

export interface UseVoiceSearchOptions {
  /** Called once per recognised final phrase. */
  onResult?: (transcript: string) => void
  lang?: string
}

export interface UseVoiceSearchApi {
  supported: boolean
  listening: boolean
  interimTranscript: string
  error: string | null
  start: () => void
  stop: () => void
  toggle: () => void
  reset: () => void
}

export function useVoiceSearch(options: UseVoiceSearchOptions = {}): UseVoiceSearchApi {
  const { onResult, lang } = options
  const onResultRef = useRef(onResult)
  onResultRef.current = onResult

  const [supported] = useState(() => getSpeechRecognitionCtor() !== null)
  const [listening, setListening] = useState(false)
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
  }, [])

  const reset = useCallback(() => {
    setInterimTranscript('')
    setError(null)
  }, [])

  const start = useCallback(() => {
    const Recognition = getSpeechRecognitionCtor()
    if (!Recognition) return

    try {
      recognitionRef.current?.abort()
    } catch {
      /* aborted instances can throw when already stopped */
    }

    const recognition = new Recognition()
    recognition.lang = lang ?? ((typeof navigator !== 'undefined' && navigator.language) || 'en-KE')
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setError(null)
      setListening(true)
    }

    recognition.onresult = (event) => {
      let finalText = ''
      let interimText = ''
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i]
        if (result.isFinal) finalText += result[0].transcript
        else interimText += result[0].transcript
      }
      if (interimText) setInterimTranscript(interimText)
      if (finalText) {
        setInterimTranscript('')
        onResultRef.current?.(finalText.trim())
      }
    }

    recognition.onerror = (event) => {
      if (event.error !== 'aborted') setError(voiceErrorMessage(event.error))
      setListening(false)
    }

    recognition.onend = () => {
      setListening(false)
      setInterimTranscript('')
    }

    recognitionRef.current = recognition
    try {
      recognition.start()
    } catch {
      setError('Voice input failed — please try again.')
    }
  }, [lang])

  const toggle = useCallback(() => {
    if (listening) stop()
    else start()
  }, [listening, start, stop])

  useEffect(
    () => () => {
      try {
        recognitionRef.current?.abort()
      } catch {
        /* ignore teardown errors */
      }
    },
    [],
  )

  return { supported, listening, interimTranscript, error, start, stop, toggle, reset }
}
