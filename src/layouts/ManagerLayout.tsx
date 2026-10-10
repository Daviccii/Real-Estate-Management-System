import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import LanguageToggle from '../components/LanguageToggle'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from '../i18n/LanguageContext'

const ManagerSidebar: React.FC = () => {
  const { t } = useTranslation()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/manager', labelKey: 'navitem.dashboard', icon: '📊' },
    { path: '/manager/analytics', labelKey: 'navitem.analytics', icon: '📉' },
    { path: '/manager/properties', labelKey: 'navitem.properties', icon: '🏠' },
    { path: '/manager/tenants', labelKey: 'navitem.tenants', icon: '👥' },
    { path: '/manager/leases', labelKey: 'navitem.leases', icon: '📄' },
    { path: '/manager/payments', labelKey: 'navitem.payments', icon: '💰' },
    { path: '/manager/maintenance', labelKey: 'navitem.maintenance', icon: '🔧' },
    { path: '/manager/marketplace', labelKey: 'navitem.marketplace', icon: '🛠️' },
    { path: '/manager/inquiries', labelKey: 'navitem.inquiries', icon: '💬' },
    { path: '/manager/units', labelKey: 'navitem.units', icon: '🏢' },
    { path: '/manager/reports', labelKey: 'navitem.reports', icon: '📈' },
    { path: '/manager/settings', labelKey: 'navitem.settings', icon: '⚙️' },
  ]

  return (
    <aside className={`sidebar manager-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>{t('layout.role.manager')}</span>
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
      
      <div className="manager-workspace-label">{t('layout.workspace.manager')}</div>
      <nav className="nav" aria-label={t('layout.aria.managerNav')}>
        {menuItems.map((item) => (
          <Link 
            key={item.path} 
            to={item.path}
            className={location.pathname === item.path || location.pathname.startsWith(item.path + '/') ? 'active' : ''}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <span style={{ fontSize: 16 }}>{item.icon}</span>
            {!collapsed && <span>{t(item.labelKey)}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  )
}

const ManagerHeader: React.FC = () => {
  const { t } = useTranslation()
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
            {t('layout.greeting.morning')} {user?.full_name || user?.email || t('layout.fallback.manager')}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            {t('layout.subtitle.manager')}
          </div>
        </div>
      </div>
      
      <div className="manager-header-meta" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <ThemeToggle />
        <LanguageToggle />
        <div className="manager-sync-status"><span /> {t('layout.sync.manager')}</div>
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
            {user?.full_name || user?.email || t('layout.fallback.manager')}
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
          {t('common.logout')}
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
