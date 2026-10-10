import React from 'react'
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import MfaPanel from './MfaPanel'
import ToastProvider from './ToastProvider'
import { mfaService } from '../services/mfa'

vi.mock('../services/mfa', () => ({
  mfaService: {
    status: vi.fn(),
    setup: vi.fn(),
    enable: vi.fn(),
    disable: vi.fn(),
    regenerateRecoveryCodes: vi.fn(),
    sendSms: vi.fn(),
    verify: vi.fn(),
  },
  isMfaChallenge: vi.fn(() => false),
}))

const disabled = { mfa_enabled: false, has_secret: false, sms_available: false, recovery_codes_remaining: 0, mandatory_for_admin: false }
const enabled = { mfa_enabled: true, has_secret: true, sms_available: true, recovery_codes_remaining: 10, mandatory_for_admin: true }

const renderPanel = () =>
  render(
    <ToastProvider>
      <MfaPanel />
    </ToastProvider>,
  )

describe('MfaPanel', () => {
  it('offers enrolment when MFA is off', async () => {
    vi.mocked(mfaService.status).mockResolvedValue(disabled)
    renderPanel()

    expect(await screen.findByText('Disabled')).toBeInTheDocument()
    expect(screen.queryByText('Required for your role')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /set up authenticator app/i })).toBeInTheDocument()
  })

  it('warns admins when MFA is mandatory for their role', async () => {
    vi.mocked(mfaService.status).mockResolvedValue({ ...disabled, mandatory_for_admin: true })
    renderPanel()

    expect(await screen.findByText('Required for your role')).toBeInTheDocument()
  })

  it('walks the enrolment flow and reveals recovery codes once', async () => {
    vi.mocked(mfaService.status)
      .mockResolvedValueOnce(disabled)
      .mockResolvedValueOnce(enabled)
    vi.mocked(mfaService.setup).mockResolvedValue({
      secret: 'JBSWY3DPEHPK3PXP',
      provisioning_uri: 'otpauth://totp/PropNoxa:a@b.com?secret=JBSWY3DPEHPK3PXP',
      issuer: 'PropNoxa',
      account: 'a@b.com',
      message: '',
    })
    vi.mocked(mfaService.enable).mockResolvedValue({
      message: 'MFA enabled',
      recovery_codes: ['crate-aaaa-bbbb', 'crate-cccc-dddd'],
      warning: '',
    })

    renderPanel()
    fireEvent.click(await screen.findByRole('button', { name: /set up authenticator app/i }))

    expect((await screen.findAllByText(/JBSWY3DPEHPK3PXP/)).length).toBeGreaterThan(0)
    fireEvent.change(screen.getByLabelText(/verification code/i), { target: { value: '123456' } })
    fireEvent.click(screen.getByRole('button', { name: /enable mfa/i }))

    expect(mfaService.enable).toHaveBeenCalledWith('123456')
    const codes = await screen.findByText(/crate-aaaa-bbbb/)
    expect(codes.textContent).toContain('crate-cccc-dddd')
    await waitFor(() => expect(screen.getByText('Enabled')).toBeInTheDocument())
  })

  it('reports remaining codes and SMS availability when enabled', async () => {
    vi.mocked(mfaService.status).mockResolvedValue(enabled)
    renderPanel()

    expect(await screen.findByText('Enabled')).toBeInTheDocument()
    expect(screen.getByText(/Recovery codes remaining: 10/)).toBeInTheDocument()
    expect(screen.getByText(/SMS backup: available/)).toBeInTheDocument()
  })

  it('keeps destructive actions disabled until a code is entered', async () => {
    vi.mocked(mfaService.status)
      .mockResolvedValueOnce(enabled)
      .mockResolvedValueOnce(disabled)
    vi.mocked(mfaService.disable).mockResolvedValue({ message: 'MFA disabled' })
    renderPanel()

    const disableButton = await screen.findByRole('button', { name: /disable mfa/i })
    expect(disableButton).toBeDisabled()

    fireEvent.change(screen.getByLabelText(/authenticator code/i), { target: { value: ' 246810 ' } })
    expect(disableButton).toBeEnabled()
    fireEvent.click(disableButton)

    expect(mfaService.disable).toHaveBeenCalledWith('246810')
    await waitFor(() => expect(screen.getByText('Disabled')).toBeInTheDocument())
  })

  it('surfaces the server message when a code is rejected', async () => {
    vi.mocked(mfaService.status).mockResolvedValue(enabled)
    vi.mocked(mfaService.regenerateRecoveryCodes).mockRejectedValue(new Error('Invalid authenticator code'))
    renderPanel()

    fireEvent.change(await screen.findByLabelText(/authenticator code/i), { target: { value: '000000' } })
    fireEvent.click(screen.getByRole('button', { name: /regenerate recovery codes/i }))

    expect(await screen.findByText('Invalid authenticator code')).toBeInTheDocument()
    expect(screen.queryByText(/Save these recovery codes now/)).not.toBeInTheDocument()
  })

  it('surfaces a status load failure instead of hanging', async () => {
    vi.mocked(mfaService.status).mockRejectedValue(new Error('The backend service cannot be reached.'))
    renderPanel()

    expect(await screen.findByText('The backend service cannot be reached.')).toBeInTheDocument()
    expect(screen.queryByText('Loading security settings…')).not.toBeInTheDocument()
  })
})
