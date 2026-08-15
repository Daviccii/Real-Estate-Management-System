import React, { useState } from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'

const Sidebar: React.FC = () => {
  const items = [
    ['/', 'Overview'],
    ['/properties', 'Properties'],
    ['/units', 'Units'],
    ['/tenants', 'Tenants'],
    ['/leases', 'Leases'],
    ['/payments', 'Payments'],
    ['/maintenance', 'Maintenance'],
    ['/documents', 'Documents'],
    ['/reports', 'Reports'],
    ['/ai', 'AI Assistant'],
    ['/settings', 'Settings'],
  ]
  const [collapsed,setCollapsed] = useState(false)
  return (
    <aside className={`sidebar ${collapsed? 'collapsed':''}`} aria-hidden={collapsed}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <div className="brand">PropNoxa</div>
        <button className="button muted" onClick={()=>setCollapsed(c=>!c)} aria-pressed={collapsed}>{collapsed? '▶':'◀'}</button>
      </div>
      <nav className="nav" aria-label="Main navigation">
        {items.map(([path, label]) => (
          <Link key={path} to={String(path)}>{label}</Link>
        ))}
      </nav>
    </aside>
  )
}

import { useAuth } from '../hooks/useAuth'

const Header: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  return (
    <header className="header" role="banner">
      <div style={{display:'flex',gap:12,alignItems:'center'}}>
        <div>
          <div style={{fontSize:14,fontWeight:700}}>Good morning, {user?.full_name ?? user?.email ?? 'User'}</div>
          <div style={{fontSize:12,color:'var(--muted)'}}>Here's what's happening across your portfolio today.</div>
        </div>
      </div>
      <div style={{display:'flex',gap:12,alignItems:'center'}}>
        <input aria-label="Search" className="input" placeholder="Search properties, tenants, units..." style={{width:260}} />
        <button className="button muted" aria-label="Notifications">🔔</button>
        <button className="button muted" aria-label="Help">?</button>
        <div style={{textAlign:'right'}}>
          <div style={{fontWeight:700}}>{user?.full_name ?? user?.email ?? 'User'}</div>
          <div style={{fontSize:12,color:'var(--muted)'}}>{user?.role ?? 'Member'}</div>
        </div>
        <button onClick={async () => { await logout(); navigate('/login') }} className="button" style={{marginLeft:12}}>Logout</button>
      </div>
    </header>
  )
}

const MainLayout: React.FC = () => {
  return (
    <div className="app-shell">
      <Sidebar />
      <div style={{flex:1}}>
        <Header />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default MainLayout
