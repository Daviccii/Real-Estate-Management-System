import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { useInstallPrompt } from './useInstallPrompt'

type PromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const makePromptEvent = (outcome: 'accepted' | 'dismissed' = 'accepted') => {
  let promptCalls = 0
  const event = new Event('beforeinstallprompt', { cancelable: true }) as PromptEvent
  Object.assign(event, {
    prompt: () => {
      promptCalls += 1
      return Promise.resolve()
    },
    userChoice: Promise.resolve({ outcome }),
  })
  return { event, promptCalls: () => promptCalls }
}

const originalUserAgent = window.navigator.userAgent

const setUserAgent = (userAgent: string) => {
  Object.defineProperty(window.navigator, 'userAgent', { configurable: true, value: userAgent })
}

const setStandalone = () => {
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: (query: string) => ({ matches: true, media: query }),
  })
}

afterEach(() => {
  setUserAgent(originalUserAgent)
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: (query: string) => ({ matches: false, media: query }),
  })
})

describe('useInstallPrompt', () => {
  it('starts hidden in a browser that has not offered an install', async () => {
    const { result } = renderHook(() => useInstallPrompt())

    expect(result.current.canInstall).toBe(false)
    expect(result.current.showIosHint).toBe(false)
    expect(result.current.isStandalone).toBe(false)
    await expect(result.current.promptInstall()).resolves.toBe('unavailable')
  })

  it('captures beforeinstallprompt and suppresses the browser mini-infobar', () => {
    const { event } = makePromptEvent()
    const { result } = renderHook(() => useInstallPrompt())

    act(() => {
      window.dispatchEvent(event)
    })

    expect(event.defaultPrevented).toBe(true)
    expect(result.current.canInstall).toBe(true)
  })

  it('prompts on request, resolves with the user choice, and clears the deferred prompt', async () => {
    const { event, promptCalls } = makePromptEvent('accepted')
    const { result } = renderHook(() => useInstallPrompt())
    act(() => {
      window.dispatchEvent(event)
    })

    let outcome: string | undefined
    await act(async () => {
      outcome = await result.current.promptInstall()
    })

    expect(promptCalls()).toBe(1)
    expect(outcome).toBe('accepted')
    expect(result.current.canInstall).toBe(false)
    await expect(result.current.promptInstall()).resolves.toBe('unavailable')
  })

  it('clears the deferred prompt once the app is installed', () => {
    const { event } = makePromptEvent()
    const { result } = renderHook(() => useInstallPrompt())
    act(() => {
      window.dispatchEvent(event)
    })
    expect(result.current.canInstall).toBe(true)

    act(() => {
      window.dispatchEvent(new Event('appinstalled'))
    })
    expect(result.current.canInstall).toBe(false)
  })

  it('shows the manual hint on iOS because Safari never fires beforeinstallprompt', () => {
    setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15')
    const { result } = renderHook(() => useInstallPrompt())

    expect(result.current.showIosHint).toBe(true)
    expect(result.current.canInstall).toBe(false)
  })

  it('hides the iOS hint when already running standalone', () => {
    setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15')
    setStandalone()
    const { result } = renderHook(() => useInstallPrompt())

    expect(result.current.isStandalone).toBe(true)
    expect(result.current.showIosHint).toBe(false)
  })
})
