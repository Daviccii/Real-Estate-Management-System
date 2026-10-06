import React, { useState } from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const getSidebarItems = (role?: string): [string, string][] => {
  const r = (role || '').toLowerCase()
  switch (r) {
    case 'admin':
      return [
        ['/admin/dashboard', 'Dashboard'],
        ['/admin/properties', 'Properties'],
        ['/admin/buildings', 'Buildings'],
        ['/admin/units', 'Units'],
        ['/admin/leases', 'Leases'],
        ['/admin/payments', 'Payments'],
        ['/admin/maintenance', 'Maintenance'],
        ['/admin/users', 'Users'],
        ['/admin/verifications', 'Verifications'],
        ['/admin/audit-logs', 'Audit Trail'],
        ['/admin/settings', 'Settings'],
      ]
    case 'manager':
      return [
        ['/manager/dashboard', 'Dashboard'],
        ['/manager/properties', 'Properties'],
        ['/manager/units', 'Units'],
        ['/manager/tenants', 'Tenants'],
        ['/manager/leases', 'Leases'],
        ['/manager/payments', 'Payments'],
        ['/manager/maintenance', 'Maintenance'],
        ['/manager/reports', 'Reports'],
        ['/manager/settings', 'Settings'],
      ]
    case 'owner':
    case 'landlord':
      return [
        ['/owner/dashboard', 'Dashboard'],
        ['/owner/properties', 'Properties'],
        ['/owner/units', 'Units'],
        ['/owner/tenants', 'Tenants'],
        ['/owner/leases', 'Leases'],
        ['/owner/financials', 'Financials'],
        ['/owner/maintenance', 'Maintenance'],
        ['/owner/settings', 'Settings'],
      ]
    case 'agent':
    case 'realtor':
      return [
        ['/agent/dashboard', 'Dashboard'],
        ['/agent/leads', 'Leads'],
        ['/agent/listings', 'Listings'],
        ['/agent/viewings', 'Viewings'],
        ['/agent/applications', 'Applications'],
        ['/agent/commissions', 'Commissions'],
        ['/agent/profile', 'Profile'],
      ]
    case 'service_provider':
    case 'contractor':
    case 'vendor':
      return [
        ['/provider/dashboard', 'Dashboard'],
        ['/provider/work-orders', 'Work Orders'],
        ['/provider/quotes', 'Quotes'],
        ['/provider/profile', 'Profile'],
      ]
    case 'tenant':
    case 'user':
    default:
      return [
        ['/tenant/dashboard', 'Dashboard'],
        ['/tenant/tenancy', 'My Tenancy'],
        ['/tenant/applications', 'Applications'],
        ['/tenant/payments', 'Payments'],
        ['/tenant/maintenance', 'Maintenance'],
        ['/tenant/messages', 'Messages'],
        ['/tenant/documents', 'Documents'],
        ['/tenant/profile', 'Profile'],
      ]
  }
}

const Sidebar: React.FC = () => {
  const { user } = useAuth()
  const items = getSidebarItems(user?.role)
  const [collapsed, setCollapsed] = useState(false)
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="brand">PropNoxa</div>
        <button className="button muted" onClick={() => setCollapsed(c => !c)} aria-pressed={collapsed}>{collapsed ? '▶' : '◀'}</button>
      </div>
      <nav className="nav" aria-label="Main navigation">
        {items.map(([path, label]) => (
          <Link key={path} to={String(path)}>{label}</Link>
        ))}
      </nav>
    </aside>
  )
}

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
