import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const OwnerSidebar: React.FC = () => {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/owner/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/owner/properties', label: 'Portfolio Properties', icon: '🏠' },
    { path: '/owner/units', label: 'Unit Directory', icon: '🏢' },
    { path: '/owner/tenants', label: 'Active Tenants', icon: '👥' },
    { path: '/owner/leases', label: 'Lease Agreements', icon: '📄' },
    { path: '/owner/financials', label: 'Financial Yield & P&L', icon: '💰' },
    { path: '/owner/applications', label: 'Tenant Screening', icon: '📝' },
    { path: '/owner/maintenance', label: 'Repair Approvals', icon: '🔧' },
    { path: '/owner/settings', label: 'Ownership & Deeds', icon: '⚙️' }
  ]

  return (
    <aside className={`sidebar owner-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>Owner</span>
        </div>
        <button
          className="button muted"
          onClick={() => setCollapsed((c) => !c)}
          aria-pressed={collapsed}
          style={{ padding: '4px 8px', fontSize: 12 }}
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>

      <nav className="nav" aria-label="Owner navigation">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={location.pathname === item.path ? 'active' : ''}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <span style={{ fontSize: 16 }}>{item.icon}</span>
            {!collapsed && <span>{item.label}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  )
}

const OwnerHeader: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <header className="header owner-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            Good day, {user?.full_name || user?.email || 'Property Owner'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>Asset Portfolio & Landlord Management</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <span
          style={{
            background: '#4f46e5',
            color: 'white',
            padding: '4px 12px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 600
          }}
        >
          OWNER
        </span>

        <button
          onClick={async () => {
            await logout()
            navigate('/login')
          }}
          className="button"
          style={{ marginLeft: 12 }}
        >
          Logout
        </button>
      </div>
    </header>
  )
}

export const OwnerLayout: React.FC = () => {
  return (
    <div className="app-shell owner-shell">
      <OwnerSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <OwnerHeader />
        <main className="content owner-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default OwnerLayout
