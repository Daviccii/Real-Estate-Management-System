import React from 'react'

const DashboardPage: React.FC = () => {
  return (
    <div>
      <div style={{display:'flex',gap:14,marginBottom:14}} className="stats">
        <div className="card"> <div style={{fontSize:12,color:'var(--muted)'}}>Total Properties</div><div style={{fontSize:22,fontWeight:700}}>—</div></div>
        <div className="card"> <div style={{fontSize:12,color:'var(--muted)'}}>Total Units</div><div style={{fontSize:22,fontWeight:700}}>—</div></div>
        <div className="card"> <div style={{fontSize:12,color:'var(--muted)'}}>Occupied Units</div><div style={{fontSize:22,fontWeight:700}}>—</div></div>
        <div className="card"> <div style={{fontSize:12,color:'var(--muted)'}}>Vacant Units</div><div style={{fontSize:22,fontWeight:700}}>—</div></div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'2fr 1fr',gap:14}}>
        <div className="card">
          <h3>Property performance</h3>
          <div style={{height:220}} className="empty">Charts will be available here</div>
        </div>
        <div className="card">
          <h3>Recent activity</h3>
          <div className="empty">No recent activity</div>
        </div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginTop:14}}>
        <div className="card"> <h4>Recent payments</h4><div className="empty">No data</div></div>
        <div className="card"> <h4>Maintenance activity</h4><div className="empty">No data</div></div>
      </div>
    </div>
  )
}

export default DashboardPage
