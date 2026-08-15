import React, { useState } from 'react'
import { validateProperty } from '../utils/validation'

type Props = {
  initial?: any
  onSubmit: (payload: any) => Promise<void>
  onCancel?: ()=>void
}

const PropertyForm: React.FC<Props> = ({ initial = {}, onSubmit, onCancel }) => {
  const [name,setName]=useState(initial.name||'')
  const [property_type,setType]=useState(initial.property_type||'')
  const [city,setCity]=useState(initial.city||'')
  const [units_count,setUnits]=useState(initial.units_count||1)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState<string | null>(null)
  const [fieldErrors,setFieldErrors]=useState<Record<string,string>>({})

  const submit = async (e:React.FormEvent)=>{
    e.preventDefault()
    setLoading(true); setError(null)
    const payload = { name, property_type, city, units_count }
    const errs = validateProperty(payload)
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
      <input value={name} onChange={e=>{ setName(e.target.value); setFieldErrors(s=>{ const n={...s}; delete n.name; return n }) }} required />
      {fieldErrors.name && <div style={{color:'var(--danger)'}}>{fieldErrors.name}</div>}

      <label>Type</label>
      <input value={property_type} onChange={e=>setType(e.target.value)} />

      <label>City</label>
      <input value={city} onChange={e=>setCity(e.target.value)} />

      <label>Units</label>
      <input type="number" value={units_count} onChange={e=>{ setUnits(Number(e.target.value)); setFieldErrors(s=>{ const n={...s}; delete n.units_count; return n }) }} min={0} />
      {fieldErrors.units_count && <div style={{color:'var(--danger)'}}>{fieldErrors.units_count}</div>}

      {error && <div style={{color:'var(--danger)'}}>{error}</div>}

      <div style={{display:'flex',gap:8,marginTop:8}}>
        <button className="button" type="submit" disabled={loading}>{loading? 'Saving...':'Save'}</button>
        <button type="button" className="button muted" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

export default PropertyForm
