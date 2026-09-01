import React, { useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerUnit } from '../../services/manager'

const ManagerUnits: React.FC = () => {
  const [units, setUnits] = useState<ManagerUnit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadUnits()
  }, [])

  const loadUnits = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await managerService.getUnits()
      setUnits(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load units')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="empty">Loading units…</div>
  if (error) return <div className="empty error">{error}</div>

  return (
    <div className="management-container">
      <div className="management-header">
        <h1>Units</h1>
        <p>Manage all units in your properties</p>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Unit Number</th>
              <th>Property ID</th>
              <th>Type</th>
              <th>Bedrooms</th>
              <th>Bathrooms</th>
              <th>Rent</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {units.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  No units found
                </td>
              </tr>
            ) : (
              units.map((unit) => (
                <tr key={unit.id}>
                  <td><strong>{unit.unit_number}</strong></td>
                  <td>{unit.property_id}</td>
                  <td>{unit.unit_type || '—'}</td>
                  <td>{unit.bedrooms || '—'}</td>
                  <td>{unit.bathrooms || '—'}</td>
                  <td>${unit.rent.toFixed(2)}</td>
                  <td>
                    <span className={`badge status-${unit.status}`}>
                      {unit.status || 'Available'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button onClick={loadUnits} className="button" disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh Units'}
        </button>
      </div>
    </div>
  )
}

export default ManagerUnits
