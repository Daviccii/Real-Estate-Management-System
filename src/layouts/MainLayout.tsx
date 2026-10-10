import React, { useState } from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import LanguageToggle from '../components/LanguageToggle'
import { useAuth } from '../hooks/useAuth'
import { useTranslation } from '../i18n/LanguageContext'

const getSidebarItems = (role?: string): [string, string][] => {
  const r = (role || '').toLowerCase()
  switch (r) {
    case 'admin':
      return [
        ['/admin/dashboard', 'navitem.dashboard'],
        ['/admin/properties', 'navitem.properties'],
        ['/admin/buildings', 'navitem.buildings'],
        ['/admin/units', 'navitem.units'],
        ['/admin/leases', 'navitem.leases'],
        ['/admin/payments', 'navitem.payments'],
        ['/admin/maintenance', 'navitem.maintenance'],
        ['/admin/users', 'navitem.users'],
        ['/admin/verifications', 'navitem.verifications'],
        ['/admin/audit-logs', 'navitem.auditTrail'],
        ['/admin/settings', 'navitem.settings'],
      ]
    case 'manager':
      return [
        ['/manager/dashboard', 'navitem.dashboard'],
        ['/manager/properties', 'navitem.properties'],
        ['/manager/units', 'navitem.units'],
        ['/manager/tenants', 'navitem.tenants'],
        ['/manager/leases', 'navitem.leases'],
        ['/manager/payments', 'navitem.payments'],
        ['/manager/maintenance', 'navitem.maintenance'],
        ['/manager/reports', 'navitem.reports'],
        ['/manager/settings', 'navitem.settings'],
      ]
    case 'owner':
    case 'landlord':
      return [
        ['/owner/dashboard', 'navitem.dashboard'],
        ['/owner/properties', 'navitem.properties'],
        ['/owner/units', 'navitem.units'],
        ['/owner/tenants', 'navitem.tenants'],
        ['/owner/leases', 'navitem.leases'],
        ['/owner/financials', 'navitem.financials'],
        ['/owner/maintenance', 'navitem.maintenance'],
        ['/owner/settings', 'navitem.settings'],
      ]
    case 'agent':
    case 'realtor':
      return [
        ['/agent/dashboard', 'navitem.dashboard'],
        ['/agent/leads', 'navitem.leads'],
        ['/agent/listings', 'navitem.listings'],
        ['/agent/viewings', 'navitem.viewings'],
        ['/agent/applications', 'navitem.applications'],
        ['/agent/commissions', 'navitem.commissions'],
        ['/agent/profile', 'navitem.profile'],
      ]
    case 'service_provider':
    case 'contractor':
    case 'vendor':
      return [
        ['/provider/dashboard', 'navitem.dashboard'],
        ['/provider/work-orders', 'navitem.workOrders'],
        ['/provider/quotes', 'navitem.quotes'],
        ['/provider/profile', 'navitem.profile'],
      ]
    case 'tenant':
    case 'user':
    default:
      return [
        ['/tenant/dashboard', 'navitem.dashboard'],
        ['/tenant/tenancy', 'navitem.myTenancy'],
        ['/tenant/applications', 'navitem.applications'],
        ['/tenant/payments', 'navitem.payments'],
        ['/tenant/maintenance', 'navitem.maintenance'],
        ['/tenant/messages', 'navitem.messages'],
        ['/tenant/documents', 'navitem.documents'],
        ['/tenant/profile', 'navitem.profile'],
      ]
  }
}

const Sidebar: React.FC = () => {
  const { t } = useTranslation()
  const { user } = useAuth()
  const items = getSidebarItems(user?.role)
  const [collapsed, setCollapsed] = useState(false)
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="brand">PropNoxa</div>
        <button className="button muted" onClick={() => setCollapsed(c => !c)} aria-pressed={collapsed}>{collapsed ? '▶' : '◀'}</button>
      </div>
      <nav className="nav" aria-label={t('layout.aria.mainNav')}>
        {items.map(([path, labelKey]) => (
          <Link key={path} to={String(path)}>{t(labelKey)}</Link>
        ))}
      </nav>
    </aside>
  )
}

const Header: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  return (
    <header className="header" role="banner">
      <div style={{display:'flex',gap:12,alignItems:'center'}}>
        <div>
          <div style={{fontSize:14,fontWeight:700}}>{t('layout.greeting.morning')} {user?.full_name ?? user?.email ?? t('layout.fallback.user')}</div>
          <div style={{fontSize:12,color:'var(--muted)'}}>{t('layout.subtitle.main')}</div>
        </div>
      </div>
      <div style={{display:'flex',gap:12,alignItems:'center'}}>
        <ThemeToggle />
        <LanguageToggle />
        <input aria-label={t('layout.searchAria')} className="input" placeholder={t('layout.searchPlaceholder')} style={{width:260}} />
        <button className="button muted" aria-label={t('layout.aria.notifications')}>🔔</button>
        <button className="button muted" aria-label={t('layout.aria.help')}>?</button>
        <div style={{textAlign:'right'}}>
          <div style={{fontWeight:700}}>{user?.full_name ?? user?.email ?? t('layout.fallback.user')}</div>
          <div style={{fontSize:12,color:'var(--muted)'}}>{user?.role ?? t('layout.fallback.user')}</div>
        </div>
        <button onClick={async () => { await logout(); navigate('/login') }} className="button" style={{marginLeft:12}}>{t('common.logout')}</button>
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
