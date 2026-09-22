import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const ProviderSidebar: React.FC = () => {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/provider/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/provider/work-orders', label: 'Field Work Orders', icon: '🔧' },
    { path: '/provider/quotes', label: 'Quote Bids', icon: '📝' },
    { path: '/provider/profile', label: 'Trade Profile & NCA', icon: '🛡️' }
  ]

  return (
    <aside className={`sidebar provider-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>Contractor</span>
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

      <nav className="nav" aria-label="Provider navigation">
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

const ProviderHeader: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <header className="header provider-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            Good day, {user?.full_name || user?.email || 'Service Provider'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>Field Service & Repair Marketplace</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <span
          style={{
            background: '#d97706',
            color: 'white',
            padding: '4px 12px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 600
          }}
        >
          CONTRACTOR
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

export const ProviderLayout: React.FC = () => {
  return (
    <div className="app-shell provider-shell">
      <ProviderSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <ProviderHeader />
        <main className="content provider-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default ProviderLayout
