import React, { useEffect, useRef } from 'react'
import { useVoiceSearch } from '../hooks/useVoiceSearch'

export interface VoiceSearchButtonProps {
  /** Receives the final recognised phrase. */
  onResult: (transcript: string) => void
  /** Surfaces unsupported/permission/mic errors to the parent. */
  onError?: (message: string) => void
  /** Accessible name, e.g. "Search by voice". */
  label?: string
  className?: string
  lang?: string
}

export const VoiceSearchButton: React.FC<VoiceSearchButtonProps> = ({
  onResult,
  onError,
  label = 'Search by voice',
  className,
  lang,
}) => {
  const { supported, listening, error, toggle } = useVoiceSearch({ onResult, lang })
  const lastErrorRef = useRef<string | null>(null)

  useEffect(() => {
    if (error && error !== lastErrorRef.current) {
      lastErrorRef.current = error
      onError?.(error)
    }
    if (!error) lastErrorRef.current = null
  }, [error, onError])

  if (!supported) return null

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={listening}
      aria-label={listening ? 'Stop voice input' : label}
      title={listening ? 'Listening… tap to stop' : label}
      data-listening={listening ? 'true' : undefined}
      className={`pn-voice-button${listening ? ' pn-voice-button--listening' : ''}${className ? ` ${className}` : ''}`}
    >
      <span aria-hidden="true">{listening ? '🎙️' : '🎤'}</span>
    </button>
  )
}

export default VoiceSearchButton
