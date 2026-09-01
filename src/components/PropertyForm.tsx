import React, { useState } from 'react'
import { validateProperty } from '../utils/validation'
import { PROPERTY_TYPES, NON_RESIDENTIAL_TYPES } from '../data/propertySearchOptions'

type Props = {
  initial?: any
  onSubmit: (payload: any) => Promise<void>
  onCancel?: ()=>void
}

const PURPOSE_OPTIONS = [
  { label: 'Buy', value: 'buy' },
  { label: 'Rent', value: 'rent' },
  { label: 'Invest', value: 'invest' },
]

const STATUS_OPTIONS = ['active', 'inactive', 'pending', 'sold', 'rented']

const PropertyForm: React.FC<Props> = ({ initial = {}, onSubmit, onCancel }) => {
  const [name,setName]=useState(initial.name||'')
  const [purpose,setPurpose]=useState(initial.purpose||'')
  const [property_type,setType]=useState(initial.property_type||'')
  const [status,setStatus]=useState(initial.status||'active')
  const [city,setCity]=useState(initial.city||'')
  const [address,setAddress]=useState(initial.address||'')
  const [county,setCounty]=useState(initial.county||'')
  const [country,setCountry]=useState(initial.country||'Kenya')
  const [units_count,setUnits]=useState(initial.units_count ?? 1)
  const [price,setPrice]=useState(initial.price||'')
  const [price_label,setPriceLabel]=useState(initial.price_label||'')
  const [bedrooms,setBedrooms]=useState<string>(initial.bedrooms != null ? String(initial.bedrooms) : '')
  const [bathrooms,setBathrooms]=useState<string>(initial.bathrooms != null ? String(initial.bathrooms) : '')
  const [area,setArea]=useState(initial.area||'')
  const [image_url,setImageUrl]=useState(initial.image_url||'')
  const [description,setDescription]=useState(initial.description||'')
  const [deposit,setDeposit]=useState(initial.deposit||'')
  const [lease_term,setLeaseTerm]=useState(initial.lease_term||'')

  const [loading,setLoading]=useState(false)
  const [error,setError]=useState<string | null>(null)
  const [fieldErrors,setFieldErrors]=useState<Record<string,string>>({})

  const showBedBath = !NON_RESIDENTIAL_TYPES.includes(property_type)
  const showRentFields = purpose === 'rent'

  function clearFieldError(key: string) {
    setFieldErrors(s => { const n = {...s}; delete n[key]; return n })
  }

  const submit = async (e:React.FormEvent)=>{
    e.preventDefault()
    setLoading(true); setError(null)

    const payload: Record<string, any> = {
      name,
      purpose: purpose || undefined,
      property_type: property_type || undefined,
      status,
      city: city || undefined,
      address: address || undefined,
      county: county || undefined,
      country: country || undefined,
      units_count,
      price: price || undefined,
      price_label: price_label || undefined,
      bedrooms: showBedBath && bedrooms !== '' ? Number(bedrooms) : undefined,
      bathrooms: showBedBath && bathrooms !== '' ? Number(bathrooms) : undefined,
      area: area || undefined,
      image_url: image_url || undefined,
      description: description || undefined,
      deposit: showRentFields ? (deposit || undefined) : undefined,
      lease_term: showRentFields ? (lease_term || undefined) : undefined,
    }

    const errs = validateProperty(payload)
    // purpose is required by the backend schema (PropertyCreate) but
    // validateProperty() predates that field, so it's checked here too
    // rather than assuming the shared validator already covers it.
    if (!purpose) errs.purpose = 'Purpose is required'

    if(Object.keys(errs).length>0){ setFieldErrors(errs); setLoading(false); return }

    try{
      await onSubmit(payload)
    }catch(err:any){
      const msg = err?.message || String(err)
      setError(msg)
    }
    setLoading(false)
  }

  return (
    <form onSubmit={submit} className="card form">
      <label>Name</label>
      <input value={name} onChange={e=>{ setName(e.target.value); clearFieldError('name') }} required />
      {fieldErrors.name && <div style={{color:'var(--danger)'}}>{fieldErrors.name}</div>}

      <label>Purpose</label>
      <select value={purpose} onChange={e=>{ setPurpose(e.target.value); clearFieldError('purpose') }} required>
        <option value="">Select purpose…</option>
        {PURPOSE_OPTIONS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
      </select>
      {fieldErrors.purpose && <div style={{color:'var(--danger)'}}>{fieldErrors.purpose}</div>}

      <label>Type</label>
      <select value={property_type} onChange={e=>setType(e.target.value)}>
        <option value="">Select type…</option>
        {PROPERTY_TYPES.filter(t => t.value).map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
      </select>

      <label>Status</label>
      <select value={status} onChange={e=>setStatus(e.target.value)}>
        {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
      </select>

      <label>City</label>
      <input value={city} onChange={e=>setCity(e.target.value)} placeholder="e.g. Kilimani" />

      <label>Address</label>
      <input value={address} onChange={e=>setAddress(e.target.value)} placeholder="Street address" />

      <div style={{display:'flex',gap:12}}>
        <div style={{flex:1}}>
          <label>County</label>
          <input value={county} onChange={e=>setCounty(e.target.value)} style={{width:'100%'}} />
        </div>
        <div style={{flex:1}}>
          <label>Country</label>
          <input value={country} onChange={e=>setCountry(e.target.value)} style={{width:'100%'}} />
        </div>
      </div>

      <label>Units</label>
      <input type="number" value={units_count} onChange={e=>{ setUnits(Number(e.target.value)); clearFieldError('units_count') }} min={0} />
      {fieldErrors.units_count && <div style={{color:'var(--danger)'}}>{fieldErrors.units_count}</div>}

      <div style={{display:'flex',gap:12}}>
        <div style={{flex:1}}>
          <label>Price</label>
          <input value={price} onChange={e=>setPrice(e.target.value)} placeholder="e.g. 45000000" style={{width:'100%'}} />
        </div>
        <div style={{flex:1}}>
          <label>Price label</label>
          <input value={price_label} onChange={e=>setPriceLabel(e.target.value)} placeholder="e.g. From KES 45M" style={{width:'100%'}} />
        </div>
      </div>

      {showBedBath && (
        <div style={{display:'flex',gap:12}}>
          <div style={{flex:1}}>
            <label>Bedrooms</label>
            <input type="number" min={0} value={bedrooms} onChange={e=>setBedrooms(e.target.value)} style={{width:'100%'}} />
          </div>
          <div style={{flex:1}}>
            <label>Bathrooms</label>
            <input type="number" min={0} value={bathrooms} onChange={e=>setBathrooms(e.target.value)} style={{width:'100%'}} />
          </div>
        </div>
      )}

      <label>Area</label>
      <input value={area} onChange={e=>setArea(e.target.value)} placeholder="e.g. 180 sqm or 1 acre" />

      {showRentFields && (
        <div style={{display:'flex',gap:12}}>
          <div style={{flex:1}}>
            <label>Deposit</label>
            <input value={deposit} onChange={e=>setDeposit(e.target.value)} placeholder="e.g. KES 170,000" style={{width:'100%'}} />
          </div>
          <div style={{flex:1}}>
            <label>Lease term</label>
            <input value={lease_term} onChange={e=>setLeaseTerm(e.target.value)} placeholder="e.g. 12 months" style={{width:'100%'}} />
          </div>
        </div>
      )}

      <label>Image URL</label>
      <input value={image_url} onChange={e=>setImageUrl(e.target.value)} placeholder="https://…  (leave blank to auto-generate)" />

      <label>Description</label>
      <textarea value={description} onChange={e=>setDescription(e.target.value)} rows={4} style={{width:'100%',resize:'vertical'}} />

      {error && <div style={{color:'var(--danger)'}}>{error}</div>}

      <div style={{display:'flex',gap:8,marginTop:8}}>
        <button className="button" type="submit" disabled={loading}>{loading? 'Saving...':'Save'}</button>
        <button type="button" className="button muted" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

export default PropertyForm