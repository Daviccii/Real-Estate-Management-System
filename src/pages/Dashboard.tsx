import React, { useEffect, useState } from 'react'
import StatCard from '../components/StatCard'
import QuickActions from '../components/QuickActions'
import { propertyService } from '../services/property'
import { useFavorites } from '../contexts/FavoriteContext'
import { Property } from '../types'

const DashboardPage: React.FC = () => {
  const [loading,setLoading]=useState(false)
  const [properties,setProperties]=useState<Property[] | null>(null)
  const [error,setError]=useState<string | null>(null)
  const { favorites } = useFavorites()

  useEffect(()=>{
    setLoading(true); setError(null)
    propertyService.list().then(res=>setProperties(res)).catch(e=>setError(String(e))).finally(()=>setLoading(false))
  },[])

  const totalProperties = properties?.length ?? 0
  const totalUnits = properties?.reduce((s,p)=>s + (p.units_count || 0),0) ?? 0
  const favoriteCount = favorites.length

  // Property breakdown by purpose
  const buyProperties = properties?.filter(p => p.purpose === 'buy').length ?? 0
  const rentProperties = properties?.filter(p => p.purpose === 'rent').length ?? 0
  const investProperties = properties?.filter(p => p.purpose === 'invest').length ?? 0

  return (
    <div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:14,marginBottom:14}}>
        <StatCard title="Total Properties" value={loading? '…': totalProperties} />
        <StatCard title="Total Units" value={loading? '…': totalUnits} />
        <StatCard title="For Sale" value={loading? '…': buyProperties} subtitle="Properties available for purchase" />
        <StatCard title="For Rent" value={loading? '…': rentProperties} subtitle="Properties available for rental" />
      </div>

      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:14,marginBottom:14}}>
        <StatCard title="Investment Properties" value={loading? '…': investProperties} subtitle="Investment opportunities" />
        <StatCard title="Your Favorites" value={favoriteCount} subtitle="Properties you've saved" />
        <StatCard title="Active Status" value={properties?.filter(p => p.status === 'active').length ?? 0} subtitle="Currently listed properties" />
        <StatCard title="Property Types" value={new Set(properties?.map(p => p.property_type)).size || 0} subtitle="Unique property categories" />
      </div>

      <div style={{display:'grid',gridTemplateColumns:'2fr 1fr',gap:14}}>
        <div className="card">
          <h3>Property Portfolio Overview</h3>
          {loading && <div className="empty">Loading property data…</div>}
          {!loading && error && <div style={{color:'var(--danger)'}}>Unable to load properties: {error}</div>}
          {!loading && !error && properties && properties.length===0 && <div className="empty">No properties yet. Add your first property to get started.</div>}
          {!loading && properties && properties.length>0 && (
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(250px,1fr))',gap:16}}>
              <div>
                <h4 style={{marginBottom:8}}>By Purpose</h4>
                <ul style={{listStyle:'none',padding:0,margin:0}}>
                  <li style={{padding:'4px 0',display:'flex',justifyContent:'space-between'}}>
                    <span>Buy</span>
                    <strong>{buyProperties}</strong>
                  </li>
                  <li style={{padding:'4px 0',display:'flex',justifyContent:'space-between'}}>
                    <span>Rent</span>
                    <strong>{rentProperties}</strong>
                  </li>
                  <li style={{padding:'4px 0',display:'flex',justifyContent:'space-between'}}>
                    <span>Invest</span>
                    <strong>{investProperties}</strong>
                  </li>
                </ul>
              </div>
              <div>
                <h4 style={{marginBottom:8}}>By Status</h4>
                <ul style={{listStyle:'none',padding:0,margin:0}}>
                  {Array.from(new Set(properties.map(p => p.status))).map(status => (
                    <li key={status} style={{padding:'4px 0',display:'flex',justifyContent:'space-between'}}>
                      <span style={{textTransform:'capitalize'}}>{status}</span>
                      <strong>{properties.filter(p => p.status === status).length}</strong>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
        <div style={{display:'grid',gap:14}}>
          <QuickActions />
          <div className="card">
            <h3>Recent Properties</h3>
            {loading && <div className="empty">Loading activity…</div>}
            {!loading && error && <div style={{color:'var(--danger)'}}>Unable to load properties: {error}</div>}
            {!loading && !error && properties && properties.length===0 && <div className="empty">No properties yet.</div>}
            {!loading && properties && properties.length>0 && (
              <ul style={{listStyle:'none',padding:0,margin:0}}>
                {properties.slice(0,6).map(p=> (
                  <li key={p.id} style={{padding:'8px 0',borderBottom:'1px solid #f1f5f9'}}>
                    <div style={{fontWeight:700}}>{p.name}</div>
                    <div style={{fontSize:12,color:'var(--muted)'}}>{p.city ?? '—'} — {p.units_count ?? '—'} units — {p.purpose || 'N/A'}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginTop:14}}>
        <div className="card"> <h4>Recent payments</h4><div className="empty">Payments API not available</div></div>
        <div className="card"> <h4>Maintenance activity</h4><div className="empty">Maintenance API not available</div></div>
      </div>
    </div>
  )
}

export default DashboardPage
