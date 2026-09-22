import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom'
import { propertyService } from '../services/property'
import { inquiryService } from '../services/inquiry'
import { requestViewing } from '../services/viewing'
import { submitApplication } from '../services/application'
import { Property } from '../types'
import ConfirmDialog from '../components/ConfirmDialog'
import { useToast } from '../components/ToastProvider'
import { useFavorites } from '../contexts/FavoriteContext'
import { useAuth } from '../contexts/AuthContext'
import { NON_RESIDENTIAL_TYPES } from '../data/propertySearchOptions'
import { resolvePropertyImage, placeholderPropertyImage } from '../utils/propertyImages'

function isResidentialType(propertyType?: string | null): boolean {
  if (!propertyType) return true
  return !NON_RESIDENTIAL_TYPES.includes(propertyType)
}

const PropertyDetailsPage: React.FC = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [item, setItem] = useState<Property | null>(null)
  const [loading, setLoading] = useState(false)
  const [img, setImg] = useState<string | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const [showInquiry, setShowInquiry] = useState(false)
  const [inquiryMessage, setInquiryMessage] = useState('')

  // Viewing Modal State
  const [showViewingModal, setShowViewingModal] = useState(false)
  const [viewingType, setViewingType] = useState('in_person')
  const [viewingDate, setViewingDate] = useState('')
  const [viewingTime, setViewingTime] = useState('10:00')
  const [viewingNotes, setViewingNotes] = useState('')
  const [bookingViewing, setBookingViewing] = useState(false)

  // Application Modal State
  const [showApplyModal, setShowApplyModal] = useState(false)
  const [moveInDate, setMoveInDate] = useState('')
  const [monthlyIncome, setMonthlyIncome] = useState('150000')
  const [employmentStatus, setEmploymentStatus] = useState('employed')
  const [employerName, setEmployerName] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [occupantsCount, setOccupantsCount] = useState<number>(2)
  const [hasPets, setHasPets] = useState('no')
  const [emergencyName, setEmergencyName] = useState('')
  const [emergencyPhone, setEmergencyPhone] = useState('')
  const [submittingApp, setSubmittingApp] = useState(false)

  const { addFavorite, removeFavorite, isFavorite } = useFavorites()
  const { user } = useAuth()
  const { addToast } = useToast()

  const getBackPath = () => {
    const params = new URLSearchParams(location.search)
    const from = params.get('from')
    if (from) return from
    if (item?.purpose === 'buy') return '/buy'
    if (item?.purpose === 'rent') return '/rent'
    if (item?.purpose === 'invest') return '/invest'
    return '/properties'
  }

  const getBackLabel = () => {
    const params = new URLSearchParams(location.search)
    const from = params.get('from')
    if (from === '/buy') return 'Back to Buy'
    if (from === '/rent') return 'Back to Rent'
    if (from === '/invest') return 'Back to Invest'
    if (item?.purpose === 'buy') return 'Back to Buy'
    if (item?.purpose === 'rent') return 'Back to Rent'
    if (item?.purpose === 'invest') return 'Back to Investment'
    return 'Back to Properties'
  }

  useEffect(() => {
    if (!id) return
    setLoading(true)
    propertyService
      .getPublic(Number(id))
      .then((r) => setItem(r))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!item) return
    let cancelled = false
    setImg(placeholderPropertyImage(item))
    resolvePropertyImage(item).then((url) => {
      if (!cancelled) setImg(url)
    })
    return () => {
      cancelled = true
    }
  }, [item?.id, item?.image_url, item?.property_type, item?.purpose])

  const handleDelete = async () => {
    if (!id) return
    try {
      const ok = await propertyService.delete(Number(id))
      if (ok) {
        addToast({ message: 'Property deleted', type: 'success' })
        setShowConfirm(false)
        navigate(getBackPath())
      } else {
        addToast({ message: 'Failed to delete property', type: 'error' })
      }
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to delete property', type: 'error' })
    }
  }

  const handleInquiry = async () => {
    if (!inquiryMessage.trim()) {
      addToast({ message: 'Please enter a message', type: 'error' })
      return
    }
    if (!id) {
      addToast({ message: 'Property ID not found', type: 'error' })
      return
    }

    try {
      await inquiryService.create({
        property_id: Number(id),
        message: inquiryMessage,
        status: 'pending'
      })
      addToast({ message: 'Inquiry submitted successfully', type: 'success' })
      setInquiryMessage('')
      setShowInquiry(false)
    } catch (error) {
      addToast({ message: 'Failed to submit inquiry', type: 'error' })
    }
  }

  const handleBookViewing = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id) return
    if (!viewingDate) {
      addToast({ message: 'Please select a viewing date', type: 'error' })
      return
    }
    setBookingViewing(true)
    try {
      const scheduledTime = `${viewingDate}T${viewingTime}:00`
      await requestViewing({
        property_id: Number(id),
        viewing_type: viewingType,
        scheduled_time: scheduledTime,
        notes: viewingNotes
      })
      addToast({ message: 'Viewing tour requested! The host will confirm your slot.', type: 'success' })
      setShowViewingModal(false)
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to request viewing', type: 'error' })
    } finally {
      setBookingViewing(false)
    }
  }

  const handleApplyTenancy = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id) return
    setSubmittingApp(true)
    try {
      await submitApplication({
        property_id: Number(id),
        desired_move_in_date: moveInDate || undefined,
        monthly_income: monthlyIncome || undefined,
        employment_status: employmentStatus || undefined,
        employer_name: employerName || undefined,
        job_title: jobTitle || undefined,
        occupants_count: occupantsCount,
        has_pets: hasPets,
        emergency_contact_name: emergencyName || undefined,
        emergency_contact_phone: emergencyPhone || undefined
      })
      addToast({ message: 'Tenancy application submitted for owner review!', type: 'success' })
      setShowApplyModal(false)
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to submit application', type: 'error' })
    } finally {
      setSubmittingApp(false)
    }
  }

  const toggleFavorite = async () => {
    if (!id) return
    try {
      if (isFavorite(Number(id))) {
        await removeFavorite(Number(id))
        addToast({ message: 'Removed from favorites', type: 'success' })
      } else {
        await addFavorite(Number(id))
        addToast({ message: 'Added to favorites', type: 'success' })
      }
    } catch (error) {
      addToast({ message: 'Failed to update favorites', type: 'error' })
    }
  }

  if (loading) {
    return (
      <div className="page">
        <button className="button muted" onClick={() => navigate(getBackPath())}>
          ← {getBackLabel()}
        </button>
        <div className="empty">Loading property details…</div>
      </div>
    )
  }

  if (!item) {
    return (
      <div className="page">
        <button className="button muted" onClick={() => navigate(getBackPath())}>
          ← {getBackLabel()}
        </button>
        <div className="empty">Property not found.</div>
      </div>
    )
  }

  const showBedBath = isResidentialType(item.property_type)

  return (
    <div className="page">
      <button className="button muted" onClick={() => navigate(getBackPath())} style={{ marginBottom: 16 }}>
        ← {getBackLabel()}
      </button>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(320px,1fr))', gap: 24 }}>
        {/* Left Column - Property Info */}
        <div style={{ gridColumn: 'span 2' }}>
          {/* Property Image & Badges */}
          <div
            className="card"
            style={{
              marginBottom: 16,
              aspectRatio: '16/9',
              background: 'var(--bg-secondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 16,
              overflow: 'hidden',
              position: 'relative'
            }}
          >
            <img
              src={img ?? placeholderPropertyImage(item)}
              alt={item.name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
            <div style={{ position: 'absolute', top: 16, left: 16, display: 'flex', gap: 8 }}>
              <span
                style={{
                  background: 'rgba(15, 23, 42, 0.85)',
                  color: 'white',
                  padding: '4px 12px',
                  borderRadius: 20,
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  backdropFilter: 'blur(8px)'
                }}
              >
                {item.purpose || 'For Rent'}
              </span>
              <span
                style={{
                  background: 'rgba(16, 185, 129, 0.9)',
                  color: 'white',
                  padding: '4px 12px',
                  borderRadius: 20,
                  fontSize: 12,
                  fontWeight: 700,
                  backdropFilter: 'blur(8px)'
                }}
              >
                ✓ Verified Property
              </span>
            </div>
          </div>

          {/* Basic Information */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 16 }}>
              <div>
                <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>{item.name}</h1>
                <p style={{ color: 'var(--text-secondary)', margin: '4px 0 0' }}>
                  {item.address ? `${item.address}, ` : ''}{item.city}, {item.country}
                </p>
              </div>
              {user && (
                <button className="button muted" onClick={toggleFavorite} style={{ padding: '8px 12px' }}>
                  {isFavorite(Number(id)) ? '❤️ Saved' : '🤍 Save'}
                </button>
              )}
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit,minmax(120px,1fr))',
                gap: 12,
                marginBottom: 16,
                background: 'var(--bg-secondary)',
                padding: 16,
                borderRadius: 12
              }}
            >
              <div>
                <div style={{ fontSize: '0.8em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Type</div>
                <div style={{ fontWeight: 700, textTransform: 'capitalize' }}>{item.property_type || 'Apartment'}</div>
              </div>
              {showBedBath && item.bedrooms !== null && (
                <div>
                  <div style={{ fontSize: '0.8em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Bedrooms</div>
                  <div style={{ fontWeight: 700 }}>{item.bedrooms} Beds</div>
                </div>
              )}
              {showBedBath && item.bathrooms !== null && (
                <div>
                  <div style={{ fontSize: '0.8em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Bathrooms</div>
                  <div style={{ fontWeight: 700 }}>{item.bathrooms} Baths</div>
                </div>
              )}
              {item.area && (
                <div>
                  <div style={{ fontSize: '0.8em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Floor Area</div>
                  <div style={{ fontWeight: 700 }}>{item.area}</div>
                </div>
              )}
              <div>
                <div style={{ fontSize: '0.8em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Availability</div>
                <div style={{ fontWeight: 700, color: 'var(--primary)', textTransform: 'capitalize' }}>{item.status}</div>
              </div>
            </div>

            {item.description && (
              <div style={{ marginTop: 16 }}>
                <h3 style={{ marginBottom: 8, fontSize: 16 }}>Description & Highlights</h3>
                <p style={{ lineHeight: 1.7, color: 'var(--text-secondary)' }}>{item.description}</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Action Hub */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Price & Primary CTA Card */}
          <div className="card" style={{ border: '2px solid var(--primary)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              {item.purpose === 'rent' ? 'Monthly Rental' : 'Guide Price'}
            </div>
            <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--primary)', margin: '4px 0 16px' }}>
              {item.price_label || (item.price ? `KSh ${Number(item.price).toLocaleString()}` : 'Price on Inquiry')}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                className="button"
                onClick={() => {
                  if (!user) {
                    navigate('/login')
                    return
                  }
                  setShowViewingModal(true)
                }}
                style={{ width: '100%', fontWeight: 700, padding: 12 }}
              >
                📅 Schedule Viewing Tour
              </button>

              {item.purpose === 'rent' && (
                <button
                  className="button"
                  onClick={() => {
                    if (!user) {
                      navigate('/login')
                      return
                    }
                    setShowApplyModal(true)
                  }}
                  style={{
                    width: '100%',
                    fontWeight: 700,
                    padding: 12,
                    background: '#059669',
                    borderColor: '#059669'
                  }}
                >
                  📝 Apply for Tenancy
                </button>
              )}

              {!showInquiry ? (
                <button
                  className="button muted"
                  onClick={() => {
                    if (!user) {
                      navigate('/login')
                      return
                    }
                    setShowInquiry(true)
                  }}
                  style={{ width: '100%' }}
                >
                  💬 Send Host Inquiry
                </button>
              ) : (
                <div style={{ marginTop: 8 }}>
                  <textarea
                    className="input"
                    placeholder="Ask about move-in dates, terms, or utility arrangements..."
                    value={inquiryMessage}
                    onChange={(e) => setInquiryMessage(e.target.value)}
                    rows={3}
                    style={{ width: '100%', marginBottom: 8, resize: 'vertical' }}
                  />
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="button" onClick={handleInquiry} style={{ flex: 1 }}>
                      Submit
                    </button>
                    <button className="button muted" onClick={() => setShowInquiry(false)}>
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Owner/Admin Management Controls */}
          {user && (user.id === item.owner_id || user.role === 'admin') && (
            <div className="card">
              <h3 style={{ fontSize: 15, marginBottom: 12 }}>Property Management</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button className="button" onClick={() => navigate(`/app/properties/${id}/edit`)}>
                  Edit Listing Details
                </button>
                <button className="button danger" onClick={() => setShowConfirm(true)}>
                  Delete Listing
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Book Viewing Modal */}
      {showViewingModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-bold text-lg text-slate-800">Schedule Viewing Tour</h3>
              <button onClick={() => setShowViewingModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleBookViewing} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tour Format</label>
                <select
                  value={viewingType}
                  onChange={(e) => setViewingType(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="in_person">In-Person Guided Tour</option>
                  <option value="virtual">Virtual Live Video Walkthrough</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Preferred Date *</label>
                  <input
                    type="date"
                    required
                    value={viewingDate}
                    onChange={(e) => setViewingDate(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Time Slot *</label>
                  <input
                    type="time"
                    required
                    value={viewingTime}
                    onChange={(e) => setViewingTime(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Special Instructions / Questions</label>
                <textarea
                  rows={2}
                  value={viewingNotes}
                  onChange={(e) => setViewingNotes(e.target.value)}
                  placeholder="e.g. Arriving with vehicle, would like to inspect parking bay."
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowViewingModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={bookingViewing}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow transition"
                >
                  {bookingViewing ? 'Booking...' : 'Confirm Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Tenancy Application Modal */}
      {showApplyModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-4 my-8">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-bold text-lg text-slate-800">Apply for Tenancy: {item.name}</h3>
              <button onClick={() => setShowApplyModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleApplyTenancy} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Desired Move-in Date *</label>
                  <input
                    type="date"
                    required
                    value={moveInDate}
                    onChange={(e) => setMoveInDate(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Net Monthly Income (KSh)</label>
                  <input
                    type="number"
                    value={monthlyIncome}
                    onChange={(e) => setMonthlyIncome(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Employment Status</label>
                  <select
                    value={employmentStatus}
                    onChange={(e) => setEmploymentStatus(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="employed">Employed (Full-time)</option>
                    <option value="self_employed">Self-Employed / Business</option>
                    <option value="contract">Contractor</option>
                    <option value="student">Student</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Employer / Org Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Safaricom PLC"
                    value={employerName}
                    onChange={(e) => setEmployerName(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Job Title</label>
                  <input
                    type="text"
                    placeholder="e.g. Engineer"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Total Occupants</label>
                  <input
                    type="number"
                    value={occupantsCount}
                    onChange={(e) => setOccupantsCount(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Pets?</label>
                  <select
                    value={hasPets}
                    onChange={(e) => setHasPets(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="no">No</option>
                    <option value="yes">Yes</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Emergency Contact Name</label>
                  <input
                    type="text"
                    value={emergencyName}
                    onChange={(e) => setEmergencyName(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Emergency Phone</label>
                  <input
                    type="text"
                    value={emergencyPhone}
                    onChange={(e) => setEmergencyPhone(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowApplyModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingApp}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow transition"
                >
                  {submittingApp ? 'Submitting...' : 'Submit Application'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={showConfirm}
        title="Delete Property"
        description="This will permanently delete the property. This action cannot be undone."
        onConfirm={handleDelete}
        onCancel={() => setShowConfirm(false)}
      />
    </div>
  )
}

export default PropertyDetailsPage