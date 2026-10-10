import React from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen } from '@testing-library/react'

import VoiceSearchButton from './VoiceSearchButton'
import {
  FakeRecognition,
  finalSpeechResult,
  installFakeSpeechRecognition,
  interimSpeechResult,
  removeFakeSpeechRecognition,
} from '../test/speechRecognitionFake'

describe('VoiceSearchButton', () => {
  beforeEach(() => {
    FakeRecognition.instances = []
    installFakeSpeechRecognition()
  })

  afterEach(() => {
    removeFakeSpeechRecognition()
  })

  it('renders nothing when the Web Speech API is unavailable', () => {
    removeFakeSpeechRecognition()
    const { container } = render(<VoiceSearchButton onResult={vi.fn()} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('starts listening on click and reflects state on the button', () => {
    render(<VoiceSearchButton onResult={vi.fn()} />)

    const button = screen.getByRole('button', { name: /search by voice/i })
    expect(button).toHaveAttribute('aria-pressed', 'false')

    fireEvent.click(button)

    expect(FakeRecognition.instances).toHaveLength(1)
    expect(FakeRecognition.instances[0].started).toBe(1)
    expect(FakeRecognition.instances[0].lang).toBeTruthy()
    expect(screen.getByRole('button', { name: /stop voice input/i })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('fires onResult with the final transcript and clears listening on end', () => {
    const onResult = vi.fn()
    render(<VoiceSearchButton onResult={onResult} />)

    fireEvent.click(screen.getByRole('button', { name: /search by voice/i }))
    const recognition = FakeRecognition.instances[0]

    act(() => {
      recognition.onresult?.(finalSpeechResult('two bedroom apartment in Kilimani'))
    })
    act(() => {
      recognition.onend?.()
    })

    expect(onResult).toHaveBeenCalledTimes(1)
    expect(onResult).toHaveBeenCalledWith('two bedroom apartment in Kilimani')
    expect(screen.getByRole('button', { name: /search by voice/i })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
  })

  it('ignores interim (non-final) results', () => {
    const onResult = vi.fn()
    render(<VoiceSearchButton onResult={onResult} />)

    fireEvent.click(screen.getByRole('button', { name: /search by voice/i }))
    act(() => {
      FakeRecognition.instances[0].onresult?.(interimSpeechResult('two bed'))
    })

    expect(onResult).not.toHaveBeenCalled()
  })

  it('maps permission errors to a readable message', () => {
    const onError = vi.fn()
    render(<VoiceSearchButton onResult={vi.fn()} onError={onError} />)

    fireEvent.click(screen.getByRole('button', { name: /search by voice/i }))
    act(() => {
      FakeRecognition.instances[0].onerror?.({ error: 'not-allowed' })
    })

    expect(onError).toHaveBeenCalledWith(
      'Microphone access was blocked. Allow microphone permission and try again.',
    )
  })

  it('aborts the active recognition session on unmount', () => {
    const { unmount } = render(<VoiceSearchButton onResult={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: /search by voice/i }))
    const recognition = FakeRecognition.instances[0]

    unmount()

    expect(recognition.aborted).toBe(1)
  })
})
