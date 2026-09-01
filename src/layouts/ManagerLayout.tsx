import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const ManagerSidebar: React.FC = () => {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/manager', label: 'Dashboard', icon: '📊' },
    { path: '/manager/properties', label: 'Properties', icon: '🏠' },
    { path: '/manager/tenants', label: 'Tenants', icon: '👥' },
    { path: '/manager/leases', label: 'Leases', icon: '📄' },
    { path: '/manager/payments', label: 'Payments', icon: '💰' },
    { path: '/manager/maintenance', label: 'Maintenance', icon: '🔧' },
    { path: '/manager/inquiries', label: 'Inquiries', icon: '💬' },
    { path: '/manager/units', label: 'Units', icon: '🏢' },
    { path: '/manager/reports', label: 'Reports', icon: '📈' },
    { path: '/manager/settings', label: 'Settings', icon: '⚙️' },
  ]

  return (
    <aside className={`sidebar manager-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>Manager</span>
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
      
      <nav className="nav" aria-label="Manager navigation">
        {menuItems.map((item) => (
          <Link 
            key={item.path} 
            to={item.path}
            className={location.pathname === item.path || location.pathname.startsWith(item.path + '/') ? 'active' : ''}
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

const ManagerHeader: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="header manager-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            Good morning, {user?.full_name || user?.email || 'Manager'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            Property Management
          </div>
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div className="manager-badge" style={{ 
          background: 'var(--primary)', 
          color: 'white', 
          padding: '4px 12px', 
          borderRadius: 12, 
          fontSize: 12, 
          fontWeight: 600 
        }}>
          MANAGER
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: 700, fontSize: 14 }}>
            {user?.full_name || user?.email || 'Manager'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            {user?.role || 'manager'}
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

const ManagerLayout: React.FC = () => {
  return (
    <div className="app-shell manager-shell">
      <ManagerSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <ManagerHeader />
        <main className="content manager-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default ManagerLayout
