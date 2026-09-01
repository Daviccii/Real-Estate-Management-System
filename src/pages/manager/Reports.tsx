import React from 'react'

const ManagerReports: React.FC = () => {
  return (
    <div className="management-container">
      <div className="management-header">
        <h1>Reports</h1>
        <p>Generate and view property reports</p>
      </div>

      <div className="empty">
        <h2>Reports Feature</h2>
        <p>Generate comprehensive reports for your managed properties</p>
        <div style={{ marginTop: 24, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button className="button" disabled>Occupancy Report</button>
          <button className="button" disabled>Payment Summary</button>
          <button className="button" disabled>Maintenance Report</button>
          <button className="button" disabled>Financial Summary</button>
        </div>
      </div>
    </div>
  )
}

export default ManagerReports
