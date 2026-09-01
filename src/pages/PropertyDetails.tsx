import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom'
import { propertyService } from '../services/property'
import { inquiryService } from '../services/inquiry'
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
  const [item,setItem]=useState<Property | null>(null)
  const [loading,setLoading]=useState(false)
  const [img,setImg]=useState<string | null>(null)
  const [showConfirm,setShowConfirm]=useState(false)
  const [showInquiry,setShowInquiry]=useState(false)
  const [inquiryMessage,setInquiryMessage]=useState('')
  const { addFavorite, removeFavorite, isFavorite } = useFavorites()
  const { user } = useAuth()
  const { addToast } = useToast()

  // Determine where to go back based on referrer or purpose
  const getBackPath = () => {
    const params = new URLSearchParams(location.search)
    const from = params.get('from')
    if (from) return from
    
    // Check if property has a purpose and suggest appropriate back path
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

  // FIX: previously called propertyService.get(), which hits the
  // authenticated GET /properties/{id} route. That route explicitly rejects
  // anyone who isn't the property's owner or an admin (403 "Not authorized to
  // view this property") — so any buyer clicking "View Details" on a listing
  // that wasn't theirs got an error instead of the page. getPublic() calls
  // the new open /properties/public/{id} route instead. The owner/admin-only
  // management actions below still gate correctly since they separately check
  // user.id === item.owner_id.
  useEffect(()=>{
    if(!id) return
    setLoading(true)
    propertyService.getPublic(Number(id)).then(r=>setItem(r)).catch(()=>{}).finally(()=>setLoading(false))
  },[id])

  // Resolve a real photo (Pexels, when configured) the same way PropertyCard
  // does, instead of the old dead Unsplash Source call duplicated here.
  useEffect(()=>{
    if(!item) return
    let cancelled = false
    setImg(placeholderPropertyImage(item))
    resolvePropertyImage(item).then((url) => { if (!cancelled) setImg(url) })
    return () => { cancelled = true }
  },[item?.id, item?.image_url, item?.property_type, item?.purpose])

  const handleDelete = async ()=>{
    if(!id) return
    try{
      const ok = await propertyService.delete(Number(id))
      if(ok){
        addToast({ message: 'Property deleted', type: 'success' })
        setShowConfirm(false)
        navigate(getBackPath())
      } else {
        addToast({ message: 'Failed to delete property', type: 'error' })
      }
    }catch(err:any){
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

  const renderPriceInfo = () => {
    if (item.purpose === 'rent') {
      return (
        <div className="card" style={{marginBottom:16}}>
          <h3>Rental Information</h3>
          <p><strong>Monthly Rent:</strong> {item.price_label || item.price || 'Not specified'}</p>
        </div>
      )
    }
    
    if (item.purpose === 'invest') {
      return (
        <div className="card" style={{marginBottom:16}}>
          <h3>Investment Information</h3>
          <p><strong>Purchase Price:</strong> {item.price_label || item.price || 'Not specified'}</p>
          <p style={{color:'var(--text-secondary)',fontSize:'0.9em'}}>
            Note: Detailed investment metrics (ROI, rental yield) are not currently available in our database.
          </p>
        </div>
      )
    }
    
    return (
      <div className="card" style={{marginBottom:16}}>
        <h3>Purchase Information</h3>
        <p><strong>Price:</strong> {item.price_label || item.price || 'Not specified'}</p>
      </div>
    )
  }

  return (
    <div className="page">
      <button className="button muted" onClick={() => navigate(getBackPath())} style={{marginBottom:16}}>
        ← {getBackLabel()}
      </button>

      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(300px,1fr))',gap:24}}>
        {/* Left Column - Property Info */}
        <div>
          {/* Property Image */}
          <div className="card" style={{marginBottom:16,aspectRatio:'16/9',background:'var(--bg-secondary)',display:'flex',alignItems:'center',justifyContent:'center',borderRadius:8,overflow:'hidden'}}>
            <img 
              src={img ?? placeholderPropertyImage(item)} 
              alt={item.name} 
              style={{width:'100%',height:'100%',objectFit:'cover'}} 
            />
          </div>

          {/* Basic Information */}
          <div className="card" style={{marginBottom:16}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'start',marginBottom:16}}>
              <div>
                <h1 style={{margin:0}}>{item.name}</h1>
                <p style={{color:'var(--text-secondary)',margin:0}}>
                  {item.city}, {item.country}
                </p>
              </div>
              {user && (
                <button 
                  className="button muted" 
                  onClick={toggleFavorite}
                  style={{padding:'8px 12px'}}
                >
                  {isFavorite(Number(id)) ? '❤️' : '🤍'}
                </button>
              )}
            </div>

            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(120px,1fr))',gap:12,marginBottom:16}}>
              <div>
                <div style={{fontSize:'0.85em',color:'var(--text-secondary)'}}>Type</div>
                <div style={{fontWeight:600}}>{item.property_type || 'Not specified'}</div>
              </div>
              {showBedBath && item.bedrooms !== null && (
                <div>
                  <div style={{fontSize:'0.85em',color:'var(--text-secondary)'}}>Bedrooms</div>
                  <div style={{fontWeight:600}}>{item.bedrooms}</div>
                </div>
              )}
              {showBedBath && item.bathrooms !== null && (
                <div>
                  <div style={{fontSize:'0.85em',color:'var(--text-secondary)'}}>Bathrooms</div>
                  <div style={{fontWeight:600}}>{item.bathrooms}</div>
                </div>
              )}
              {item.area && (
                <div>
                  <div style={{fontSize:'0.85em',color:'var(--text-secondary)'}}>Area</div>
                  <div style={{fontWeight:600}}>{item.area}</div>
                </div>
              )}
              <div>
                <div style={{fontSize:'0.85em',color:'var(--text-secondary)'}}>Status</div>
                <div style={{fontWeight:600,textTransform:'capitalize'}}>{item.status}</div>
              </div>
              <div>
                <div style={{fontSize:'0.85em',color:'var(--text-secondary)'}}>Purpose</div>
                <div style={{fontWeight:600,textTransform:'capitalize'}}>{item.purpose || 'Not specified'}</div>
              </div>
            </div>

            {item.address && (
              <div style={{marginBottom:16}}>
                <strong>Address:</strong> {item.address}
              </div>
            )}

            {item.description && (
              <div>
                <h3 style={{marginBottom:8}}>Description</h3>
                <p style={{lineHeight:1.6}}>{item.description}</p>
              </div>
            )}
          </div>

          {/* Purpose-specific Information */}
          {renderPriceInfo()}

          {/* Inquiry Form */}
          <div className="card">
            <h3>Inquire About This Property</h3>
            {!user ? (
              <div style={{color:'var(--text-secondary)'}}>
                <p>Please <Link to="/login" style={{color:'var(--primary)'}}>sign in</Link> to send an inquiry about this property.</p>
              </div>
            ) : !showInquiry ? (
              <button className="button" onClick={() => setShowInquiry(true)}>
                Send Inquiry
              </button>
            ) : (
              <div>
                <textarea
                  className="input"
                  placeholder="Enter your message..."
                  value={inquiryMessage}
                  onChange={(e) => setInquiryMessage(e.target.value)}
                  rows={4}
                  style={{width:'100%',marginBottom:12,resize:'vertical'}}
                />
                <div style={{display:'flex',gap:8}}>
                  <button className="button" onClick={handleInquiry}>
                    Send Inquiry
                  </button>
                  <button className="button muted" onClick={() => setShowInquiry(false)}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Management Actions */}
        {user && (user.id === item.owner_id || user.role === 'admin') && (
          <div>
            <div className="card">
              <h3>Property Management</h3>
              <div style={{display:'flex',flexDirection:'column',gap:8}}>
                <button className="button" onClick={()=>navigate(`/app/properties/${id}/edit`)}>
                  Edit Property
                </button>
                <button className="button danger" onClick={()=>setShowConfirm(true)}>
                  Delete Property
                </button>
              </div>
            </div>

          </div>
        )}

        <div>
          <div className="card" style={{marginTop:16}}>
            <h3>Property Details</h3>
            <div style={{display:'grid',gridTemplateColumns:'auto 1fr',gap:8,fontSize:'0.9em'}}>
              <span style={{color:'var(--text-secondary)'}}>ID:</span>
              <span>{item.id}</span>
              
              <span style={{color:'var(--text-secondary)'}}>Units:</span>
              <span>{item.units_count ?? 'Not specified'}</span>
              
              <span style={{color:'var(--text-secondary)'}}>County:</span>
              <span>{item.county || 'Not specified'}</span>
            </div>
          </div>
        </div>
      </div>

      <ConfirmDialog 
        open={showConfirm} 
        title="Delete Property" 
        description="This will permanently delete the property. This action cannot be undone." 
        onConfirm={handleDelete} 
        onCancel={()=>setShowConfirm(false)} 
      />
    </div>
  )
}

export default PropertyDetailsPage