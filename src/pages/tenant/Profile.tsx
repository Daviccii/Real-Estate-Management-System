import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { submitVerification } from '../../services/verification'
import MfaPanel from '../../components/MfaPanel'
import { getMyDeletionRequest, requestAccountDeletion, cancelAccountDeletion, exportMyData, type DeletionRequestInfo } from '../../services/privacy'
import { notificationService, type EmailPreference } from '../../services/notification'

export const TenantProfile: React.FC = () => {
  const { user } = useAuth()
  const [idType, setIdType] = useState('National ID')
  const [idNumber, setIdNumber] = useState('')
  const [docUrl, setDocUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)

  const [deletion, setDeletion] = useState<DeletionRequestInfo | null>(null)
  const [privacyBusy, setPrivacyBusy] = useState(false)
  const [privacyMsg, setPrivacyMsg] = useState<string | null>(null)
  const [emailPref, setEmailPref] = useState<EmailPreference | null>(null)

  useEffect(() => {
    let cancelled = false
    getMyDeletionRequest()
      .then((res) => { if (!cancelled) setDeletion(res.request) })
      .catch(() => {})
    notificationService.getEmailPreference()
      .then((pref) => { if (!cancelled) setEmailPref(pref) })
      .catch(() => { if (!cancelled) setEmailPref({ notifications_enabled: true }) })
    return () => { cancelled = true }
  }, [])

  const handleToggleEmailPref = async () => {
    if (!emailPref) return
    const next = !emailPref.notifications_enabled
    setEmailPref({ notifications_enabled: next })
    try {
      const saved = await notificationService.updateEmailPreference(next)
      setEmailPref(saved)
    } catch {
      setEmailPref({ notifications_enabled: !next })
    }
  }

  const handleExport = async () => {
    setPrivacyBusy(true); setPrivacyMsg(null)
    try {
      await exportMyData()
      setPrivacyMsg('Your data export has been downloaded.')
    } catch {
      setPrivacyMsg('Could not download your export. Please try again.')
    } finally {
      setPrivacyBusy(false)
    }
  }

  const handleRequestDeletion = async () => {
    if (!window.confirm('Request deletion of your account and personal data? You can cancel while the request is pending.')) return
    setPrivacyBusy(true); setPrivacyMsg(null)
    try {
      const res = await requestAccountDeletion('Requested by user from profile page')
      setDeletion(res.request)
      setPrivacyMsg('Your deletion request has been submitted for review.')
    } catch {
      setPrivacyMsg('Could not submit your deletion request.')
    } finally {
      setPrivacyBusy(false)
    }
  }

  const handleCancelDeletion = async () => {
    setPrivacyBusy(true); setPrivacyMsg(null)
    try {
      await cancelAccountDeletion()
      setDeletion((d) => (d ? { ...d, status: 'cancelled' } : d))
      setPrivacyMsg('Your deletion request has been cancelled.')
    } catch {
      setPrivacyMsg('Could not cancel the request.')
    } finally {
      setPrivacyBusy(false)
    }
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!docUrl.trim()) return
    setSubmitting(true)
    try {
      await submitVerification({
        verification_type: 'identity',
        id_type: idType,
        id_number: idNumber,
        document_url: docUrl,
      })
      setStatusMsg('Identity document submitted for verification! Our security desk will review it shortly.')
      setIdNumber('')
      setDocUrl('')
    } catch (err: any) {
      alert(err.message || 'Failed to submit verification')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <span className="tenant-eyebrow">Identity & access</span>
        <h1 className="text-2xl font-bold text-slate-800">My Profile & Security Verification</h1>
        <p className="text-slate-500 text-sm mt-1">Manage personal contact details and verified tenant trust badges.</p>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {statusMsg}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Account Info */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Account Information</h2>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs text-slate-400 block">Full Name</span>
              <span className="font-semibold text-slate-800">{user?.full_name || 'Resident'}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Email Address</span>
              <span className="font-semibold text-slate-800">{user?.email}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Platform Role</span>
              <span className="inline-block px-2.5 py-0.5 bg-teal-100 text-teal-800 rounded-full text-xs font-bold uppercase mt-1">
                {user?.role}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Verification Status</span>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold uppercase mt-1 ${
                user?.is_verified ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {user?.is_verified ? 'Verified Resident' : 'Unverified'}
              </span>
            </div>
          </div>
        </div>

        {/* Verification Document Upload */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Submit Identity for Verification</h2>
          <form onSubmit={handleVerify} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">ID Document Type</label>
              <select
                value={idType}
                onChange={(e) => setIdType(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="National ID">National ID Card</option>
                <option value="Passport">Passport</option>
                <option value="Alien Card / Work Permit">Alien Card / Work Permit</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">ID Number</label>
              <input
                type="text"
                placeholder="e.g. 12345678"
                value={idNumber}
                onChange={(e) => setIdNumber(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Document File URL / Link *</label>
              <input
                type="url"
                required
                placeholder="https://storage.propnoxa.com/docs/my-id.pdf"
                value={docUrl}
                onChange={(e) => setDocUrl(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">
                Securely encrypted and accessible exclusively to platform compliance officers.
              </span>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow transition"
            >
              {submitting ? 'Submitting...' : 'Submit Verification Request'}
            </button>
          </form>
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <MfaPanel />
      </div>

      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4" style={{ marginTop: 24 }}>
        <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Privacy &amp; Your Data</h2>
        {privacyMsg && (
          <div className="p-3 bg-slate-50 border border-slate-200 text-slate-700 rounded-xl text-sm">{privacyMsg}</div>
        )}
        {deletion?.status === 'pending' && (
          <p className="text-sm text-amber-700">
            A deletion request submitted{' '}
            {deletion.requested_at ? new Date(deletion.requested_at).toLocaleString() : ''} is pending review.
          </p>
        )}
        <p className="text-sm text-slate-500">
          Download everything we store about you, or request erasure of your account. See our{' '}
          <Link to="/privacy" className="text-teal-700 underline">privacy policy</Link> for what is retained and why.
        </p>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            onClick={handleExport}
            disabled={privacyBusy}
            className="py-2 px-4 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow transition disabled:opacity-50"
          >
            Download my data (JSON)
          </button>
          {deletion?.status === 'pending' ? (
            <button
              onClick={handleCancelDeletion}
              disabled={privacyBusy}
              className="py-2 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition disabled:opacity-50"
            >
              Cancel deletion request
            </button>
          ) : (
            <button
              onClick={handleRequestDeletion}
              disabled={privacyBusy}
              className="py-2 px-4 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-xl text-xs font-semibold transition disabled:opacity-50"
            >
              Request account deletion
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm" style={{ marginTop: 24 }}>
        <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">Email Notifications</h2>
        <div className="flex items-center justify-between gap-4 pt-4">
          <div className="text-sm">
            <p className="font-semibold text-slate-800">Product &amp; account notification emails</p>
            <p className="text-xs text-slate-400 mt-1">
              Payment, lease and maintenance updates by email. Security emails (password reset,
              verification) are always sent.
            </p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={emailPref?.notifications_enabled ?? true}
            disabled={!emailPref}
            onClick={handleToggleEmailPref}
            className={`relative shrink-0 h-6 w-11 rounded-full transition-colors ${
              emailPref?.notifications_enabled ? 'bg-teal-600' : 'bg-slate-300'
            } disabled:opacity-50`}
          >
            <span
              className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                emailPref?.notifications_enabled ? 'translate-x-5' : ''
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  )
}
export default TenantProfile
