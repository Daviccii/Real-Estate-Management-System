import React from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import ManagerMaintenance from './Maintenance'
import { managerService } from '../../services/manager'
import {
  acceptQuote,
  getQuotesForRequest,
  getWorkOrders,
  submitWorkOrderReview,
} from '../../services/serviceMarketplace'
import type { MaintenanceQuote, MaintenanceWorkOrder } from '../../types'

const { addToast } = vi.hoisted(() => ({ addToast: vi.fn() }))

vi.mock('../../components/ToastProvider', () => ({
  useToast: () => ({ addToast, removeToast: vi.fn() }),
}))

vi.mock('../../services/manager', () => ({
  managerService: {
    getMaintenance: vi.fn(),
    updateMaintenanceStatus: vi.fn(),
  },
}))

vi.mock('../../services/serviceMarketplace', () => ({
  acceptQuote: vi.fn(),
  getQuotesForRequest: vi.fn(),
  getWorkOrders: vi.fn(),
  submitWorkOrderReview: vi.fn(),
}))

const ticket = {
  id: 11,
  title: 'Burst pipe in kitchen',
  description: 'Water spraying under the sink.',
  priority: 'high',
  status: 'open',
  property_id: 3,
  created_at: '2026-10-01T09:00:00',
}

const pendingQuote: MaintenanceQuote = {
  id: 21,
  request_id: 11,
  provider_id: 5,
  quoted_amount: '15000',
  estimated_hours: 4,
  scope_description: 'Replace pipe segment and seal joint',
  status: 'pending',
  created_at: '2026-10-02T10:00:00',
  provider_name: 'Njoroge Plumbing',
}

const assignedOrder: MaintenanceWorkOrder = {
  id: 31,
  request_id: 11,
  maintenance_id: 11,
  property_id: 3,
  provider_id: 5,
  assigned_by_id: 2,
  status: 'assigned',
  scheduled_date: null,
  approved_budget: '15000',
  notes: null,
  completion_notes: null,
  created_at: '2026-10-02T11:00:00',
  updated_at: '2026-10-02T11:00:00',
  property_name: 'Alpha Court',
  provider_company: 'Njoroge Plumbing',
  request_title: 'Burst pipe in kitchen',
  has_review: false,
  review_score: null,
  can_review: false,
}

const completedOrder: MaintenanceWorkOrder = {
  ...assignedOrder,
  id: 32,
  status: 'completed',
  can_review: true,
}

describe('ManagerMaintenance', () => {
  beforeEach(() => {
    vi.mocked(managerService.getMaintenance).mockResolvedValue([ticket] as any)
    vi.mocked(managerService.updateMaintenanceStatus).mockResolvedValue({} as any)
    vi.mocked(getQuotesForRequest).mockResolvedValue([pendingQuote])
    vi.mocked(getWorkOrders).mockResolvedValue([assignedOrder, completedOrder])
    vi.mocked(acceptQuote).mockResolvedValue({ ...assignedOrder } as any)
    vi.mocked(submitWorkOrderReview).mockResolvedValue({} as any)
  })

  it('renders the maintenance queue', async () => {
    render(<ManagerMaintenance />)

    expect(await screen.findByText('Burst pipe in kitchen')).toBeInTheDocument()
    expect(managerService.getMaintenance).toHaveBeenCalledWith({})
    expect(screen.getByRole('button', { name: 'Quotes & Work Orders' })).toBeInTheDocument()
  })

  it('shows quotes and work orders for a ticket', async () => {
    render(<ManagerMaintenance />)
    await screen.findByText('Burst pipe in kitchen')

    fireEvent.click(screen.getByRole('button', { name: 'Quotes & Work Orders' }))

    expect(
      await screen.findByRole('heading', { name: 'Quotes & Work Orders' }),
    ).toBeInTheDocument()
    await waitFor(() => expect(getQuotesForRequest).toHaveBeenCalledWith(11))
    expect(getWorkOrders).toHaveBeenCalledWith(undefined, 11)

    expect(await screen.findByText('KSh 15000')).toBeInTheDocument()
    expect(screen.getByText('Replace pipe segment and seal joint')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Accept & Dispatch' })).toBeInTheDocument()
    expect(screen.getByText('Awaiting execution')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rate Provider' })).toBeInTheDocument()
    expect(screen.getAllByText('Not rated')).toHaveLength(2)
  })

  it('accepts a pending quote, dispatches a work order and reloads the panel', async () => {
    render(<ManagerMaintenance />)
    await screen.findByText('Burst pipe in kitchen')
    fireEvent.click(screen.getByRole('button', { name: 'Quotes & Work Orders' }))
    await screen.findByText('KSh 15000')

    fireEvent.click(screen.getByRole('button', { name: 'Accept & Dispatch' }))

    await waitFor(() => expect(acceptQuote).toHaveBeenCalledWith(21))
    await waitFor(() => expect(getQuotesForRequest).toHaveBeenCalledTimes(2))
    expect(addToast).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'success',
        message: expect.stringContaining('accepted'),
      }),
    )
    await waitFor(() => expect(managerService.getMaintenance).toHaveBeenCalledTimes(2))
  })

  it('submits a provider review for a completed work order', async () => {
    render(<ManagerMaintenance />)
    await screen.findByText('Burst pipe in kitchen')
    fireEvent.click(screen.getByRole('button', { name: 'Quotes & Work Orders' }))
    await screen.findByText('KSh 15000')

    fireEvent.click(screen.getByRole('button', { name: 'Rate Provider' }))
    expect(
      await screen.findByRole('heading', { name: /Rate Njoroge Plumbing/ }),
    ).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Score'), { target: { value: '4' } })
    fireEvent.change(screen.getByLabelText('Comment (optional)'), {
      target: { value: 'Neat work' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Submit Review' }))

    await waitFor(() => expect(submitWorkOrderReview).toHaveBeenCalledWith(32, 4, 'Neat work'))
    expect(addToast).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'success',
        message: expect.stringContaining('review'),
      }),
    )
    await waitFor(() => expect(getQuotesForRequest).toHaveBeenCalledTimes(2))
  })

  it('still updates ticket status from the queue', async () => {
    render(<ManagerMaintenance />)
    await screen.findByText('Burst pipe in kitchen')

    fireEvent.click(screen.getByRole('button', { name: 'Update Status' }))
    await screen.findByRole('heading', { name: 'Update Maintenance Status' })

    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[selects.length - 1], { target: { value: 'resolved' } })
    const statusButtons = screen.getAllByRole('button', { name: 'Update Status' })
    fireEvent.click(statusButtons[statusButtons.length - 1])

    await waitFor(() =>
      expect(managerService.updateMaintenanceStatus).toHaveBeenCalledWith(11, 'resolved'),
    )
    expect(addToast).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'success' }),
    )
    await waitFor(() => expect(managerService.getMaintenance).toHaveBeenCalledTimes(2))
  })
})
