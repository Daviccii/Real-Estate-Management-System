import React from 'react'

const items = [
  {title: 'Property Owners', body: 'Get a complete view of your portfolio, income, occupancy and property performance.'},
  {title: 'Property Managers', body: 'Manage properties, tenants, leases, maintenance and payments from one platform.'},
  {title: 'Real Estate Agencies', body: 'Centralize your property portfolio and streamline day-to-day operations.'},
  {title: 'Finance Teams', body: 'Track rent collection, outstanding balances, revenue and financial performance.'},
  {title: 'Maintenance Teams', body: 'Organize maintenance requests, assignments, progress and completion.'},
  {title: 'Tenants', body: 'Give tenants a simple way to access their property information, payments and requests.'},
]

export default function Solutions(){
  return (
    <div className="page">
      <h1>Solutions built for every part of your property operation.</h1>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',gap:16,marginTop:16}}>
        {items.map(i=> (
          <div className="card" key={i.title}>
            <h3>{i.title}</h3>
            <p style={{color:'var(--muted)'}}>{i.body}</p>
            <div style={{marginTop:10}}><button className="button muted">Learn more</button></div>
          </div>
        ))}
      </div>
    </div>
  )
}
