import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertyService } from '../services/property'
import StatCard from '../components/StatCard'

interface MarketInsights {
  total_properties: number
  by_purpose: Record<string, number>
  by_type: Record<string, number>
  top_locations: Array<{ city: string; count: number }>
  by_status: Record<string, number>
}

export default function MarketInsights() {
  const [insights, setInsights] = useState<MarketInsights | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true)
        const data = await propertyService.marketInsights()
        setInsights(data)
      } catch (err: any) {
        setError(err.message || 'Failed to load market insights')
      } finally {
        setLoading(false)
      }
    }

    fetchInsights()
  }, [])

  if (loading) {
    return (
      <div className="page">
        <h1>Market Insights</h1>
        <div className="empty">Loading market insights…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Market Insights</h1>
        <div style={{color:'var(--danger)'}}>{error}</div>
      </div>
    )
  }

  if (!insights) {
    return (
      <div className="page">
        <h1>Market Insights</h1>
        <div className="empty">No market data available</div>
      </div>
    )
  }

  const formatNumber = (num: number) => num.toLocaleString()

  return (
    <div className="page">
      <h1>Market Insights</h1>
      <p style={{color:'var(--text-secondary)',marginBottom:24}}>
        Real-time market data derived from our property database
      </p>

      {/* Market Overview */}
      <section style={{marginBottom:32}}>
        <h2 style={{marginBottom:16}}>Market Overview</h2>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:16}}>
          <StatCard 
            title="Total Properties" 
            value={formatNumber(insights.total_properties)} 
            subtitle="All listed properties"
          />
          <StatCard 
            title="Properties for Sale" 
            value={formatNumber(insights.by_purpose.buy || 0)} 
            subtitle="Available for purchase"
          />
          <StatCard 
            title="Properties for Rent" 
            value={formatNumber(insights.by_purpose.rent || 0)} 
            subtitle="Available for rental"
          />
          <StatCard 
            title="Investment Properties" 
            value={formatNumber(insights.by_purpose.invest || 0)} 
            subtitle="Investment opportunities"
          />
        </div>
      </section>

      {/* Property Types */}
      <section style={{marginBottom:32}}>
        <h2 style={{marginBottom:16}}>Property Types</h2>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:16}}>
          {Object.entries(insights.by_type).map(([type, count]) => (
            <StatCard 
              key={type}
              title={type} 
              value={formatNumber(count)} 
              subtitle={`${((count / insights.total_properties) * 100).toFixed(1)}% of total`}
            />
          ))}
        </div>
      </section>

      {/* Popular Locations */}
      <section style={{marginBottom:32}}>
        <h2 style={{marginBottom:16}}>Popular Locations</h2>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:16}}>
          {insights.top_locations.map((location, index) => (
            <div key={location.city} className="card">
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                <h3 style={{margin:0}}>#{index + 1} {location.city}</h3>
                <span style={{fontSize:'1.5em',fontWeight:'bold',color:'var(--primary)'}}>
                  {location.count}
                </span>
              </div>
              <div style={{
                height:'8px',
                background:'var(--bg-secondary)',
                borderRadius:'4px',
                overflow:'hidden'
              }}>
                <div style={{
                  height:'100%',
                  width:`${(location.count / insights.total_properties) * 100}%`,
                  background:'var(--primary)',
                  borderRadius:'4px'
                }} />
              </div>
              <p style={{color:'var(--text-secondary)',margin:'8px 0 0 0',fontSize:'0.9em'}}>
                {((location.count / insights.total_properties) * 100).toFixed(1)}% of all properties
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Status Distribution */}
      <section style={{marginBottom:32}}>
        <h2 style={{marginBottom:16}}>Property Status</h2>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:16}}>
          {Object.entries(insights.by_status).map(([status, count]) => (
            <StatCard 
              key={status}
              title={status.charAt(0).toUpperCase() + status.slice(1)} 
              value={formatNumber(count)} 
              subtitle={`${((count / insights.total_properties) * 100).toFixed(1)}% of total`}
            />
          ))}
        </div>
      </section>

      {/* Investment Insights Note */}
      <section style={{padding:20,background:'var(--bg-secondary)',borderRadius:8,marginBottom:32}}>
        <h3 style={{marginTop:0}}>Investment Insights</h3>
        <p style={{marginBottom:12}}>
          Detailed investment metrics such as rental yield, ROI, and appreciation rates are not currently available in our database. 
          These metrics require historical transaction data and ongoing market analysis.
        </p>
        <p style={{margin:0,fontSize:'0.9em',color:'var(--text-secondary)'}}>
          <strong>Coming soon:</strong> Advanced investment analytics including rental yields, price trends, and market performance indicators.
        </p>
      </section>

      <div style={{marginTop:24}}>
        <h3>Explore Properties Based on Market Data</h3>
        <div style={{display:'flex',gap:12,marginTop:12}}>
          <Link to="/buy" className="nav-cta">Browse Properties for Sale</Link>
          <Link to="/rent" className="nav-cta-ghost">Browse Rentals</Link>
          <Link to="/invest" className="nav-cta-ghost">Investment Properties</Link>
        </div>
      </div>
    </div>
  )
}
