import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const AgentSidebar: React.FC = () => {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/agent/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/agent/leads', label: 'Leads Pipeline', icon: '🎯' },
    { path: '/agent/listings', label: 'Assigned Listings', icon: '🏠' },
    { path: '/agent/viewings', label: 'Viewing Tours', icon: '📅' },
    { path: '/agent/applications', label: 'Rental Apps', icon: '📝' },
    { path: '/agent/commissions', label: 'Commissions', icon: '💵' },
    { path: '/agent/profile', label: 'EARB Accreditation', icon: '🛡️' }
  ]

  return (
    <aside className={`sidebar agent-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>Agent</span>
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

      <nav className="nav" aria-label="Agent navigation">
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

const AgentHeader: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <header className="header agent-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            Hello, {user?.full_name || user?.email || 'Licensed Agent'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>Agency Deal Pipeline & Client CRM</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <span
          style={{
            background: '#2563eb',
            color: 'white',
            padding: '4px 12px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 600
          }}
        >
          AGENT
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

export const AgentLayout: React.FC = () => {
  return (
    <div className="app-shell agent-shell">
      <AgentSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <AgentHeader />
        <main className="content agent-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AgentLayout
