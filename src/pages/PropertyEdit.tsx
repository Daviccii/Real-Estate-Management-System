import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { propertyService } from '../services/property'
import { useToast } from '../components/ToastProvider'
import PropertyForm from '../components/PropertyForm'
import { Property } from '../types'

const PropertyEditPage: React.FC = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [item,setItem]=useState<Property | null>(null)
  const [loading,setLoading]=useState(false)
  const { addToast } = useToast()

  useEffect(()=>{
    if(!id) return
    setLoading(true)
    propertyService.get(Number(id)).then(r=>setItem(r)).catch(()=>{}).finally(()=>setLoading(false))
  },[id])

  const handleUpdate = async (payload:any)=>{
    if(!id) return
    setLoading(true)
    try{
      const updated = await propertyService.update(Number(id), payload)
      if(updated){
        addToast({ message: 'Property updated', type: 'success' })
        navigate(`/properties/${id}`)
      } else {
        addToast({ message: 'Update failed', type: 'error' })
      }
    }catch(err:any){
      addToast({ message: err?.message || 'Update failed', type: 'error' })
    }finally{ setLoading(false) }
  }

  if(!id) return <div className="empty">Invalid property id</div>

  return (
    <div>
      <h2>Edit Property</h2>
      <div className="card">
        {item ? (
          <PropertyForm initial={item} onSubmit={handleUpdate} onCancel={()=>navigate(`/properties/${id}`)} />
        ) : (
          <div className="empty">Loading property…</div>
        )}
      </div>
    </div>
  )
}

export default PropertyEditPage
