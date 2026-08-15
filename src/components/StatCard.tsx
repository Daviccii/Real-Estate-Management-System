import React from 'react'

type Props = {
  title: string
  value: string | number
  subtitle?: string
  trend?: { value: string, positive?: boolean }
  loading?: boolean
}

const StatCard: React.FC<Props> = ({ title, value, subtitle, trend, loading }) => {
  return (
    <div className="card stat-card" role="region" aria-label={title} style={{display:'flex',flexDirection:'column',gap:8}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <div style={{fontSize:12,color:'var(--muted)'}}>{title}</div>
        {trend && <div style={{color: trend.positive? 'var(--success)': 'var(--danger)', fontWeight:700}}>{trend.value}</div>}
      </div>
      <div style={{fontSize:24,fontWeight:700}}>
        {loading ? <span className="skeleton" style={{width:80,height:28,display:'inline-block',borderRadius:6}} /> : value}
      </div>
      {subtitle && <div style={{fontSize:12,color:'var(--muted)'}}>{subtitle}</div>}
    </div>
  )
}

export default StatCard
