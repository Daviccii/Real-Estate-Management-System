import React, { useEffect, useState } from 'react'
import { Property } from '../types'
import { propertyService } from '../services/property'
import { Link } from 'react-router-dom'

const PropertiesPage: React.FC = () => {
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState<string | null>(null)
  const [items,setItems]=useState<Property[] | null>(null)

  useEffect(()=>{
    setLoading(true); setError(null)
    propertyService.list().then(res=>setItems(res)).catch(e=>setError(String(e))).finally(()=>setLoading(false))
  },[])

  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
        <h2>Properties</h2>
        <div style={{display:'flex',gap:8}}>
          <input className="input" placeholder="Search properties" />
          <button className="button">Add Property</button>
        </div>
      </div>

      <div className="card">
        {loading && <div className="empty">Loading properties…</div>}
        {error && <div style={{color:'var(--danger)'}}>{error}</div>}
        {!loading && !error && items && items.length===0 && <div className="empty">No properties yet</div>}
        {!loading && !error && items && items.length>0 && (
          <table style={{width:'100%'}} className="table">
            <thead><tr><th>Name</th><th>Type</th><th>City</th><th>Units</th><th>Status</th></tr></thead>
            <tbody>
              {items.map(p=> (
                <tr key={p.id}>
                  <td><Link to={`/properties/${p.id}`}>{p.name}</Link></td>
                  <td>{p.property_type}</td>
                  <td>{p.city}</td>
                  <td>{p.units_count ?? '-'}</td>
                  <td>{p.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default PropertiesPage
