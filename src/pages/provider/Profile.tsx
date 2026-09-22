import React, { useEffect, useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { submitVerification } from '../../services/verification'
import { updateMyProviderProfile } from '../../services/serviceMarketplace'

const TRADE_CATEGORIES = [
  'Plumbing',
  'Electrical',
  'HVAC & Air Conditioning',
  'Carpentry & Woodwork',
  'Painting & Finishes',
  'Masonry & Structural',
  'Roofing & Waterproofing',
  'Deep Cleaning & Fumigation',
  'Security & Access Control',
  'Appliance Repair',
  'General Maintenance'
]

export const ProviderProfile: React.FC = () => {
  const { user } = useAuth()
  const [companyName, setCompanyName] = useState('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [serviceAreas, setServiceAreas] = useState<string>('Nairobi, Westlands, Kilimani, Karen')
  const [hourlyRate, setHourlyRate] = useState<string>('2500')
  const [licenseNumber, setLicenseNumber] = useState('')
  const [docUrl, setDocUrl] = useState('')
  const [isAvailable, setIsAvailable] = useState(true)

  const [savingProfile, setSavingProfile] = useState(false)
  const [submittingVerification, setSubmittingVerification] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [verifyMsg, setVerifyMsg] = useState<string | null>(null)

  useEffect(() => {
    if (user?.full_name) {
      setCompanyName(user.full_name + ' Services')
    }
  }, [user])

  const toggleCategory = (cat: string) => {
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    )
  }

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingProfile(true)
    setSuccessMsg(null)
    try {
      const areas = serviceAreas.split(',').map((s) => s.trim()).filter(Boolean)
      await updateMyProviderProfile({
        company_name: companyName || user?.full_name || 'Contractor',
        categories: selectedCategories.length > 0 ? selectedCategories : ['General Maintenance'],
        service_areas: areas,
        hourly_rate: hourlyRate,
        license_number: licenseNumber || undefined,
        is_available: isAvailable
      })
      setSuccessMsg('Service provider profile updated successfully!')
    } catch (err: any) {
      alert(err.message || 'Failed to update profile')
    } finally {
      setSavingProfile(false)
    }
  }

  const handleSubmitVerification = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!docUrl.trim()) return
    setSubmittingVerification(true)
    setVerifyMsg(null)
    try {
      await submitVerification({
        verification_type: 'contractor_license',
        business_name: companyName || undefined,
        license_number: licenseNumber || undefined,
        document_url: docUrl
      })
      setVerifyMsg('Contractor trade license submitted for platform verification!')
      setDocUrl('')
    } catch (err: any) {
      alert(err.message || 'Failed to submit contractor license')
    } finally {
      setSubmittingVerification(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Contractor Profile & Trade Accreditation</h1>
        <p className="text-slate-500 text-sm mt-1">
          Configure your service catalog, operational rates, coverage zones, and submit credentials for the Verified Contractor badge.
        </p>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm">
          {successMsg}
        </div>
      )}

      {verifyMsg && (
        <div className="p-4 bg-blue-50 border border-blue-200 text-blue-800 rounded-xl text-sm">
          {verifyMsg}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Service Profile & Trade Skills */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-5">
          <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">
            Business Details & Trade Categories
          </h2>

          <form onSubmit={handleSaveProfile} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Company / Trading Name *</label>
              <input
                type="text"
                required
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Apex Electrical & Plumbing Solutions"
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Trade Skills & Specialties</label>
              <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto p-2 bg-slate-50 rounded-xl border border-slate-200">
                {TRADE_CATEGORIES.map((cat) => {
                  const isSelected = selectedCategories.includes(cat)
                  return (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => toggleCategory(cat)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                        isSelected
                          ? 'bg-amber-600 text-white shadow-sm'
                          : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {cat} {isSelected ? '✓' : '+'}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Base Hourly Rate (KSh)</label>
                <input
                  type="number"
                  value={hourlyRate}
                  onChange={(e) => setHourlyRate(e.target.value)}
                  placeholder="2500"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Trade License / Reg No.</label>
                <input
                  type="text"
                  value={licenseNumber}
                  onChange={(e) => setLicenseNumber(e.target.value)}
                  placeholder="NCA / EPRA Reg"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Service Areas (Comma Separated)</label>
              <input
                type="text"
                value={serviceAreas}
                onChange={(e) => setServiceAreas(e.target.value)}
                placeholder="e.g. Westlands, Kilimani, Karen, Upperhill"
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div className="flex items-center gap-3 pt-1">
              <input
                type="checkbox"
                id="isAvailable"
                checked={isAvailable}
                onChange={(e) => setIsAvailable(e.target.checked)}
                className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
              />
              <label htmlFor="isAvailable" className="text-xs font-medium text-slate-700">
                Currently Available for Emergency & Scheduled Dispatches
              </label>
            </div>

            <button
              type="submit"
              disabled={savingProfile}
              className="w-full py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow transition"
            >
              {savingProfile ? 'Saving Profile...' : 'Save Contractor Profile'}
            </button>
          </form>
        </div>

        {/* Verification & Badges */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
            <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">
              Trust & Accreditation Status
            </h2>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-xs text-slate-400 block">Primary Representative</span>
                <span className="font-semibold text-slate-800">{user?.full_name || 'Service Partner'}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Registered Email</span>
                <span className="font-semibold text-slate-800">{user?.email}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Marketplace Badge</span>
                <span
                  className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold uppercase mt-1 ${
                    user?.is_verified ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  {user?.is_verified ? '✓ Verified Service Contractor' : 'Verification Under Review'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm space-y-4">
            <h2 className="font-bold text-base text-slate-800 border-b border-slate-100 pb-3">
              Upload NCA / Trade Certificate
            </h2>
            <form onSubmit={handleSubmitVerification} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  License / Registration Document URL *
                </label>
                <input
                  type="url"
                  required
                  value={docUrl}
                  onChange={(e) => setDocUrl(e.target.value)}
                  placeholder="https://storage.propnoxa.com/contractors/nca-cert.pdf"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <button
                type="submit"
                disabled={submittingVerification}
                className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow transition"
              >
                {submittingVerification ? 'Submitting...' : 'Submit Credentials for Verification'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProviderProfile
