import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const TenantSidebar: React.FC = () => {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/tenant/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/tenant/tenancy', label: 'My Tenancy', icon: '🔑' },
    { path: '/tenant/applications', label: 'Applications', icon: '📝' },
    { path: '/tenant/payments', label: 'Rent Payments', icon: '💳' },
    { path: '/tenant/maintenance', label: 'Maintenance', icon: '🔧' },
    { path: '/tenant/messages', label: 'Messages', icon: '💬' },
    { path: '/tenant/documents', label: 'Documents Vault', icon: '📁' },
    { path: '/tenant/profile', label: 'ID Verification', icon: '🛡️' }
  ]

  return (
    <aside className={`sidebar tenant-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>Tenant</span>
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

      <nav className="nav" aria-label="Tenant navigation">
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

const TenantHeader: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <header className="header tenant-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            Welcome back, {user?.full_name || user?.email || 'Tenant'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>Tenant Portal & Resident Services</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <span
          style={{
            background: '#059669',
            color: 'white',
            padding: '4px 12px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 600
          }}
        >
          TENANT
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

export const TenantLayout: React.FC = () => {
  return (
    <div className="app-shell tenant-shell">
      <TenantSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <TenantHeader />
        <main className="content tenant-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default TenantLayout
