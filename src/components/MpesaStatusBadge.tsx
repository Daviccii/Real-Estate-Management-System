import React from 'react'
import { mpesaStatusLabel } from '../services/mpesa'

const badgeClass = (status: string): string => {
  if (status === 'succeeded') return 'bg-emerald-100 text-emerald-800'
  if (['pending', 'awaiting_callback'].includes(status)) return 'bg-amber-100 text-amber-800'
  if (['failed', 'cancelled', 'timed_out', 'expired'].includes(status)) return 'bg-red-100 text-red-800'
  return 'bg-slate-100 text-slate-600'
}

export const MpesaStatusBadge: React.FC<{ status: string }> = ({ status }) => (
  <span
    className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${badgeClass(status)}`}
  >
    {mpesaStatusLabel(status)}
  </span>
)

export default MpesaStatusBadge
