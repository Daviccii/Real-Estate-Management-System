import React from 'react'
import { Link } from 'react-router-dom'
import { Property } from '../types'

interface PropertyComparisonModalProps {
  isOpen: boolean
  onClose: () => void
  properties: Property[]
  onRemoveProperty?: (propertyId: number) => void
}

export const PropertyComparisonModal: React.FC<PropertyComparisonModalProps> = ({
  isOpen,
  onClose,
  properties,
  onRemoveProperty
}) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-5xl w-full p-6 sm:p-8 shadow-2xl space-y-6 my-8">
        <div className="flex justify-between items-center border-b border-slate-100 pb-4">
          <div>
            <span className="inline-block px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-xs font-bold uppercase tracking-wider mb-1">
              Side-by-Side Analysis
            </span>
            <h2 className="text-xl font-bold text-slate-800">Compare Properties ({properties.length})</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold flex items-center justify-center transition"
          >
            ✕
          </button>
        </div>

        {properties.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            No properties selected for comparison. Add up to 4 listings to evaluate them side-by-side.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 overflow-x-auto pb-2">
            {properties.map((p) => {
              const amenitiesList = Array.isArray(p.amenities)
                ? p.amenities
                : typeof p.amenities === 'string'
                ? (p.amenities as string).split(',').map((a) => a.trim()).filter(Boolean)
                : []

              return (
                <div
                  key={p.id}
                  className="bg-slate-50 rounded-2xl p-4 border border-slate-200 flex flex-col justify-between space-y-4 relative"
                >
                  {onRemoveProperty && (
                    <button
                      onClick={() => onRemoveProperty(p.id)}
                      className="absolute top-2 right-2 w-6 h-6 rounded-full bg-white/80 hover:bg-rose-100 hover:text-rose-600 text-slate-400 text-xs font-bold flex items-center justify-center shadow-sm"
                      title="Remove from comparison"
                    >
                      ✕
                    </button>
                  )}

                  <div className="space-y-3">
                    <div className="h-32 rounded-xl bg-slate-200 overflow-hidden relative">
                      {p.image_url ? (
                        <img src={p.image_url} alt={p.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-400 text-2xl">
                          🏠
                        </div>
                      )}
                      <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-slate-900/80 text-white backdrop-blur">
                        {p.purpose || 'For Rent'}
                      </div>
                    </div>

                    <div>
                      <h3 className="font-bold text-sm text-slate-800 line-clamp-1">{p.title}</h3>
                      <p className="text-xs text-slate-500 line-clamp-1">{p.address}, {p.city}</p>
                    </div>

                    <div className="font-bold text-base text-blue-600">
                      KSh {Number(p.price).toLocaleString()}
                      <span className="text-[10px] text-slate-400 font-normal">
                        {p.purpose === 'rent' ? ' / mo' : ''}
                      </span>
                    </div>

                    {/* Specs Matrix */}
                    <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 bg-white p-2.5 rounded-xl border border-slate-100">
                      <div>
                        <span className="text-slate-400 block text-[10px]">Bedrooms</span>
                        <span className="font-bold text-slate-800">{p.bedrooms ?? '—'} Beds</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Bathrooms</span>
                        <span className="font-bold text-slate-800">{p.bathrooms ?? '—'} Baths</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Floor Area</span>
                        <span className="font-bold text-slate-800">{p.area_sqft ? `${p.area_sqft} sqft` : '—'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Type</span>
                        <span className="font-bold text-slate-800 capitalize">{p.property_type || 'Apartment'}</span>
                      </div>
                    </div>

                    {/* Amenities list */}
                    <div>
                      <span className="text-[10px] font-bold uppercase text-slate-400 block mb-1">Key Amenities</span>
                      {amenitiesList.length === 0 ? (
                        <span className="text-xs text-slate-400">Standard amenities</span>
                      ) : (
                        <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
                          {amenitiesList.slice(0, 5).map((a, i) => (
                            <span
                              key={i}
                              className="px-1.5 py-0.5 rounded bg-white text-[10px] font-medium text-slate-600 border border-slate-200"
                            >
                              ✓ {a}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <Link
                    to={`/properties/${p.id}`}
                    onClick={onClose}
                    className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold text-center transition shadow-sm block"
                  >
                    View Listing Details
                  </Link>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default PropertyComparisonModal
