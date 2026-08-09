import React from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'

const Sidebar: React.FC = () => {
  const items = [
    ['/', 'Dashboard'],
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
  return (
    <aside className="sidebar">
      <div className="brand">RealEstate OS</div>
      <nav className="nav">
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
    <header className="header">
      <div style={{display:'flex',gap:12,alignItems:'center'}}>
        <button className="button" onClick={() => navigate('/properties')}>Add Property</button>
      </div>
      <div style={{display:'flex',gap:12,alignItems:'center'}}>
        <div style={{textAlign:'right'}}>
          <div style={{fontWeight:700}}>{user?.full_name ?? user?.email ?? 'User'}</div>
          <div style={{fontSize:12,color:'var(--muted)'}}>{user?.role ?? 'Member'}</div>
        </div>
        <button onClick={() => { logout(); navigate('/login') }} style={{marginLeft:12}}>Logout</button>
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
