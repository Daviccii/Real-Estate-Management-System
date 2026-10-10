import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'
import LanguageToggle from './LanguageToggle'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from '../i18n/LanguageContext'

const LINKS = [
  { labelKey: 'nav.home', to: '/' },
  { labelKey: 'nav.buy', to: '/buy' },
  { labelKey: 'nav.rent', to: '/rent' },
  { labelKey: 'nav.invest', to: '/invest' },
  { labelKey: 'nav.explore', to: '/properties' },
  { labelKey: 'nav.marketInsights', to: '/features' },
] as const

const getPortalLabelKey = (role?: string) => {
  const r = (role || '').toLowerCase()
  switch (r) {
    case 'admin':
      return 'nav.portal.admin'
    case 'manager':
      return 'nav.portal.manager'
    case 'owner':
    case 'landlord':
      return 'nav.portal.owner'
    case 'agent':
    case 'realtor':
      return 'nav.portal.agent'
    case 'service_provider':
    case 'contractor':
    case 'vendor':
      return 'nav.portal.contractor'
    case 'tenant':
    case 'resident':
      return 'nav.portal.tenant'
    default:
      return 'nav.portal.default'
  }
}

const PublicNavbar: React.FC = () => {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, getDashboardPath } = useAuth()
  const { t } = useTranslation()

  useEffect(() => {
    function onScroll() { setScrolled(window.scrollY > 8) }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function isActive(link: typeof LINKS[number]) {
    return location.pathname === link.to
  }

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <header className={`public-nav ${scrolled ? 'scrolled' : ''}`} role="banner">
      <div className="public-nav-inner">
        <Link to="/" className="brand" aria-label={t('nav.aria.home')}>
          <Logo size={36} />
        </Link>

        <nav id="primary-navigation" className={`nav-links ${open ? 'open' : ''}`} aria-label={t('nav.aria.primary')} aria-expanded={open}>
          {LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={isActive(link) ? 'nav-link active' : 'nav-link'}
              aria-current={isActive(link) ? 'page' : undefined}
              onClick={() => setOpen(false)}
            >
              {t(link.labelKey)}
            </Link>
          ))}
        </nav>

        <div className="nav-cta-group">
          <ThemeToggle />
          <LanguageToggle />
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Link to={getDashboardPath()} className="nav-cta" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span>{t(getPortalLabelKey(user.role))}</span>
                <span>→</span>
              </Link>
              <button onClick={handleLogout} className="nav-cta-ghost" style={{ padding: '6px 14px', fontSize: 13 }}>
                {t('common.signOut')}
              </button>
            </div>
          ) : (
            <>
              <Link to="/login" className="nav-cta-ghost">{t('common.signIn')}</Link>
              <Link to="/register" className="nav-cta">{t('common.createAccount')}</Link>
            </>
          )}
          <button className="nav-toggle" aria-label={t('nav.aria.menu')} aria-controls="primary-navigation" aria-expanded={open} onClick={() => setOpen(o => !o)}>
            <span /> <span /> <span />
          </button>
        </div>
      </div>
    </header>
  )
}

export default PublicNavbar