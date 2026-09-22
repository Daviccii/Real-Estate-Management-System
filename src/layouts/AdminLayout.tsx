import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const AdminSidebar: React.FC = () => {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/admin/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/admin/properties', label: 'Properties', icon: '🏠' },
    { path: '/admin/buildings', label: 'Buildings', icon: '🏙️' },
    { path: '/admin/units', label: 'Units', icon: '🏢' },
    { path: '/admin/leases', label: 'Leases', icon: '📄' },
    { path: '/admin/payments', label: 'Payments', icon: '💰' },
    { path: '/admin/maintenance', label: 'Maintenance', icon: '🔧' },
    { path: '/admin/verifications', label: 'Verifications', icon: '🛡️' },
    { path: '/admin/audit-logs', label: 'Audit Trail', icon: '📋' },
    { path: '/admin/users', label: 'Users', icon: '👥' },
    { path: '/admin/inquiries', label: 'Inquiries', icon: '💬' },
    { path: '/admin/agents', label: 'Agents', icon: '🤝' },
    { path: '/admin/managers', label: 'Managers', icon: '👔' },
    { path: '/admin/tenants', label: 'Tenants', icon: '🔑' },
    { path: '/admin/market-insights', label: 'Market Insights', icon: '📈' },
    { path: '/admin/settings', label: 'Settings', icon: '⚙️' },
  ]

  return (
    <aside className={`sidebar admin-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>Admin</span>
        </div>
        <button 
          className="button muted" 
          onClick={() => setCollapsed(c => !c)} 
          aria-pressed={collapsed}
          style={{ padding: '4px 8px', fontSize: 12 }}
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>
      
      <nav className="nav" aria-label="Admin navigation">
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

const AdminHeader: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="header admin-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            Good morning, {user?.full_name || user?.email || 'Admin'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            Platform Administration
          </div>
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div className="admin-badge" style={{ 
          background: 'var(--primary)', 
          color: 'white', 
          padding: '4px 12px', 
          borderRadius: 12, 
          fontSize: 12, 
          fontWeight: 600 
        }}>
          ADMIN
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: 700, fontSize: 14 }}>
            {user?.full_name || user?.email || 'Admin'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            {user?.role || 'admin'}
          </div>
        </div>
        
        <button 
          onClick={handleLogout} 
          className="button"
          style={{ marginLeft: 12 }}
        >
          Logout
        </button>
      </div>
    </header>
  )
}

const AdminLayout: React.FC = () => {
  return (
    <div className="app-shell admin-shell">
      <AdminSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <AdminHeader />
        <main className="content admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AdminLayout