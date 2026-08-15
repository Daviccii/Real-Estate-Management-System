import React, { useEffect, useState } from 'react'
import StatCard from '../../components/StatCard'
import { adminService } from '../../services/admin'
import type { MarketInsights } from '../../services/admin'

const AdminMarketInsights: React.FC = () => {
  const [insights, setInsights] = useState<MarketInsights | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadInsights()
  }, [])

  const loadInsights = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await adminService.getMarketInsights()
      setInsights(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load market insights')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <h1>Market Insights</h1>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
          {[...Array(5)].map((_, i) => (
            <StatCard key={i} title="Loading..." value="..." loading />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>Market Insights</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load market insights: {error}
          <button className="button" onClick={loadInsights} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
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

  return (
    <div className="page">
      <h1>Market Insights</h1>
      
      {/* Overview Stats */}
      <div style={{ marginBottom: 24 }}>
        <StatCard title="Total Properties" value={insights.total_properties} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
        {/* Properties by Purpose */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Properties by Purpose</h3>
          {Object.keys(insights.by_purpose).length === 0 ? (
            <div className="empty">No data available</div>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {Object.entries(insights.by_purpose).map(([purpose, count]) => (
                <li key={purpose} style={{ 
                  padding: '8px 0', 
                  borderBottom: '1px solid #f1f5f9',
                  display: 'flex',
                  justifyContent: 'space-between'
                }}>
                  <span style={{ textTransform: 'capitalize' }}>{purpose}</span>
                  <strong>{count}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Properties by Type */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Properties by Type</h3>
          {Object.keys(insights.by_type).length === 0 ? (
            <div className="empty">No data available</div>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {Object.entries(insights.by_type).map(([type, count]) => (
                <li key={type} style={{ 
                  padding: '8px 0', 
                  borderBottom: '1px solid #f1f5f9',
                  display: 'flex',
                  justifyContent: 'space-between'
                }}>
                  <span style={{ textTransform: 'capitalize' }}>{type}</span>
                  <strong>{count}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Properties by Status */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Properties by Status</h3>
          {Object.keys(insights.by_status).length === 0 ? (
            <div className="empty">No data available</div>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {Object.entries(insights.by_status).map(([status, count]) => (
                <li key={status} style={{ 
                  padding: '8px 0', 
                  borderBottom: '1px solid #f1f5f9',
                  display: 'flex',
                  justifyContent: 'space-between'
                }}>
                  <span style={{ textTransform: 'capitalize' }}>{status}</span>
                  <strong>{count}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Top Locations */}
      <div className="card" style={{ marginTop: 24 }}>
        <h3 style={{ marginBottom: 12 }}>Top Locations</h3>
        {insights.top_locations.length === 0 ? (
          <div className="empty">No location data available</div>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {insights.top_locations.map((location, index) => (
              <li key={location.city} style={{ 
                padding: '8px 0', 
                borderBottom: '1px solid #f1f5f9',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ 
                    background: 'var(--primary)', 
                    color: 'white', 
                    width: 24, 
                    height: 24, 
                    borderRadius: '50%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    fontSize: 12,
                    fontWeight: 600
                  }}>
                    {index + 1}
                  </span>
                  <span>{location.city}</span>
                </div>
                <strong>{location.count} properties</strong>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default AdminMarketInsights