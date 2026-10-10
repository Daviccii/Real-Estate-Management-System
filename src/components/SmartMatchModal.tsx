import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { matchProperties } from '../services/property'
import { PropertyMatchResult, PropertyMatchCriteria } from '../types'
import VoiceSearchButton from './VoiceSearchButton'
import { parseVoiceQuery } from '../utils/voiceQueryParser'

interface SmartMatchModalProps {
  isOpen: boolean
  onClose: () => void
}

export const SmartMatchModal: React.FC<SmartMatchModalProps> = ({ isOpen, onClose }) => {
  const [step, setStep] = useState<'form' | 'results'>('form')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<PropertyMatchResult[]>([])

  // Form criteria
  const [purpose, setPurpose] = useState<string>('rent')
  const [maxBudget, setMaxBudget] = useState<string>('120000')
  const [preferredCity, setPreferredCity] = useState<string>('Nairobi')
  const [minBedrooms, setMinBedrooms] = useState<number>(2)
  const [propertyType, setPropertyType] = useState<string>('apartment')
  const [furnishing, setFurnishing] = useState<string>('any')
  const [requireParking, setRequireParking] = useState(true)
  const [requireSecurity, setRequireSecurity] = useState(true)
  const [requireBalcony, setRequireBalcony] = useState(false)

  // Voice assistant state
  const [voiceHeard, setVoiceHeard] = useState('')
  const [voiceChips, setVoiceChips] = useState<string[]>([])
  const [voiceError, setVoiceError] = useState<string | null>(null)
  const [voiceAmenities, setVoiceAmenities] = useState<string[]>([])

  if (!isOpen) return null

  const handleVoiceResult = (transcript: string) => {
    const parsed = parseVoiceQuery(transcript)
    setVoiceHeard(parsed.heard)
    setVoiceChips(parsed.understood)
    setVoiceError(null)

    const c = parsed.criteria
    if (c.purpose) setPurpose(c.purpose)
    if (c.max_budget != null) setMaxBudget(String(c.max_budget))
    if (c.preferred_city) setPreferredCity(c.preferred_city)
    if (c.min_bedrooms != null) setMinBedrooms(Math.min(4, Math.max(1, c.min_bedrooms)))
    if (c.property_type) setPropertyType(c.property_type)
    if (c.furnishing) setFurnishing(c.furnishing)
    if (c.require_parking) setRequireParking(true)
    if (c.require_security) setRequireSecurity(true)
    if (c.require_balcony) setRequireBalcony(true)
    if (c.amenities?.length) setVoiceAmenities(c.amenities)
  }

  const handleMatch = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const criteria: PropertyMatchCriteria = {
        purpose,
        max_budget: maxBudget ? Number(maxBudget) : undefined,
        preferred_city: preferredCity || undefined,
        min_bedrooms: minBedrooms,
        property_type: propertyType || undefined,
        furnishing: furnishing !== 'any' ? furnishing : undefined,
        require_parking: requireParking,
        require_security: requireSecurity,
        require_balcony: requireBalcony,
        amenities: voiceAmenities.length ? voiceAmenities : undefined
      }
      const data = await matchProperties(criteria)
      setResults(data)
      setStep('results')
    } catch (err: any) {
      alert(err.message || 'Failed to calculate smart matches')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-4xl w-full p-6 sm:p-8 shadow-2xl space-y-6 my-8">
        <div className="flex justify-between items-center border-b border-slate-100 pb-4">
          <div>
            <span className="inline-block px-3 py-1 bg-purple-50 text-purple-600 rounded-full text-xs font-bold uppercase tracking-wider mb-1">
              AI Intelligent Matchmaker
            </span>
            <h2 className="text-xl font-bold text-slate-800">
              {step === 'form' ? 'Find Your Perfect Property Match' : `Top Matched Properties (${results.length})`}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold flex items-center justify-center transition"
          >
            ✕
          </button>
        </div>

        {step === 'form' ? (
          <form onSubmit={handleMatch} className="space-y-5 text-sm">
            <p className="text-slate-500 text-xs">
              Answer a few lifestyle and budget questions. Our recommendation engine will rank all active ecosystem listings based on proximity, budget compatibility, and amenity matches.
            </p>

            <div className="bg-purple-50 border border-purple-100 rounded-2xl p-3 space-y-2">
              <div className="flex items-center gap-3">
                <VoiceSearchButton onResult={handleVoiceResult} onError={setVoiceError} label="Describe your ideal property by voice" />
                <p className="text-xs text-slate-600 flex-1">
                  {voiceHeard ? (
                    <>
                      <span className="font-semibold text-slate-700">Heard:</span> &ldquo;{voiceHeard}&rdquo; — review the details below, then calculate.
                    </>
                  ) : (
                    'Tap the mic and describe what you need — e.g. “two bedroom apartment in Kilimani under 80k with parking”.'
                  )}
                </p>
              </div>
              {voiceChips.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {voiceChips.map((chip) => (
                    <span
                      key={chip}
                      className="px-2 py-0.5 rounded-full bg-white border border-purple-200 text-[10px] font-semibold text-purple-700"
                    >
                      {chip}
                    </span>
                  ))}
                </div>
              )}
              {voiceError && (
                <p role="alert" className="text-xs text-red-600">
                  {voiceError}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="smart-match-purpose" className="block text-xs font-semibold text-slate-700 mb-1">Goal</label>
                <select
                  id="smart-match-purpose"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="rent">Rent a Home</option>
                  <option value="sale">Buy / Invest</option>
                </select>
              </div>

              <div>
                <label htmlFor="smart-match-budget" className="block text-xs font-semibold text-slate-700 mb-1">
                  Maximum Budget (KSh {purpose === 'rent' ? '/ mo' : ''})
                </label>
                <input
                  id="smart-match-budget"
                  type="number"
                  required
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value)}
                  placeholder="120000"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div>
                <label htmlFor="smart-match-city" className="block text-xs font-semibold text-slate-700 mb-1">Preferred City / Locality</label>
                <input
                  id="smart-match-city"
                  type="text"
                  value={preferredCity}
                  onChange={(e) => setPreferredCity(e.target.value)}
                  placeholder="e.g. Nairobi, Westlands, Kilimani"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div>
                <label htmlFor="smart-match-bedrooms" className="block text-xs font-semibold text-slate-700 mb-1">Minimum Bedrooms</label>
                <select
                  id="smart-match-bedrooms"
                  value={minBedrooms}
                  onChange={(e) => setMinBedrooms(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value={1}>1+ Bedroom / Studio</option>
                  <option value={2}>2+ Bedrooms</option>
                  <option value={3}>3+ Bedrooms</option>
                  <option value={4}>4+ Bedrooms</option>
                </select>
              </div>

              <div>
                <label htmlFor="smart-match-type" className="block text-xs font-semibold text-slate-700 mb-1">Property Type</label>
                <select
                  id="smart-match-type"
                  value={propertyType}
                  onChange={(e) => setPropertyType(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="apartment">Apartment</option>
                  <option value="house">Townhouse / Villa</option>
                  <option value="commercial">Commercial Space</option>
                </select>
              </div>

              <div>
                <label htmlFor="smart-match-furnishing" className="block text-xs font-semibold text-slate-700 mb-1">Furnishing Preference</label>
                <select
                  id="smart-match-furnishing"
                  value={furnishing}
                  onChange={(e) => setFurnishing(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="any">Any / Flexible</option>
                  <option value="furnished">Furnished</option>
                  <option value="unfurnished">Unfurnished</option>
                </select>
              </div>
            </div>

            {/* Lifestyle & Amenity Requirements */}
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Lifestyle & Amenities Priorities
              </label>
              <div className="flex flex-wrap gap-4 text-xs font-medium text-slate-700">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={requireParking}
                    onChange={(e) => setRequireParking(e.target.checked)}
                    className="rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span>Dedicated Vehicle Parking</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={requireSecurity}
                    onChange={(e) => setRequireSecurity(e.target.checked)}
                    className="rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span>24/7 Gated Security & CCTV</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={requireBalcony}
                    onChange={(e) => setRequireBalcony(e.target.checked)}
                    className="rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span>Private Balcony / Terrace View</span>
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold shadow-lg transition"
              >
                {loading ? 'Evaluating Listings...' : '⚡ Calculate Best Matches'}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <button
                onClick={() => setStep('form')}
                className="text-xs font-semibold text-purple-600 hover:text-purple-800 flex items-center gap-1"
              >
                &larr; Adjust Match Filters
              </button>
              <span className="text-xs text-slate-400">Ranked by smart algorithm</span>
            </div>

            {results.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-sm">
                No active properties matched these strict criteria. Try expanding your budget or adjusting bedroom requirements.
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                {results.map((res) => {
                  const p = res.property
                  const score = Math.round(res.match_score)
                  const topFactors = Object.entries(res.score_breakdown || {})
                    .filter(([, pts]) => pts > 0)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 4)
                  return (
                    <div
                      key={p.id}
                      className="bg-slate-50 rounded-2xl p-4 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-purple-300 transition"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-20 h-20 rounded-xl bg-slate-200 overflow-hidden flex-shrink-0 relative">
                          {p.image_url ? (
                            <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-xl">🏠</div>
                          )}
                        </div>

                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                                score >= 85
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : score >= 70
                                  ? 'bg-purple-100 text-purple-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {score}% Match
                            </span>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-slate-200 text-slate-700">
                              {res.match_label}
                            </span>
                            <span className="text-xs text-slate-400">• {p.bedrooms ?? 0} Beds • {p.bathrooms ?? 0} Baths</span>
                          </div>

                          <h4 className="font-bold text-sm text-slate-800">{p.name}</h4>
                          <p className="text-xs text-slate-500">{p.address}, {p.city}</p>

                          {topFactors.length > 0 && (
                            <div className="flex flex-wrap gap-1 pt-1">
                              {topFactors.map(([factor, pts]) => (
                                <span
                                  key={factor}
                                  className="px-2 py-0.5 rounded bg-purple-50 text-[10px] font-semibold text-purple-700 border border-purple-100"
                                >
                                  {factor} +{pts}
                                </span>
                              ))}
                            </div>
                          )}

                          <div className="flex flex-wrap gap-1 pt-1">
                            {res.match_reasons.map((reason, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded bg-white text-[10px] font-medium text-slate-600 border border-slate-200"
                              >
                                ✓ {reason}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 flex-shrink-0">
                        <div className="font-bold text-base text-slate-900">
                          KSh {Number(p.price).toLocaleString()}
                        </div>
                        <Link
                          to={`/properties/${p.id}`}
                          onClick={onClose}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
                        >
                          View Listing
                        </Link>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default SmartMatchModal
