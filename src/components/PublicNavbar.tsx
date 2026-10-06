import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Logo from './Logo'
import { useAuth } from '../contexts/AuthContext'

const LINKS = [
  { label: 'Home', to: '/' },
  { label: 'Buy', to: '/buy' },
  { label: 'Rent', to: '/rent' },
  { label: 'Invest', to: '/invest' },
  { label: 'Explore', to: '/properties' },
  { label: 'Market Insights', to: '/features' },
] as const

const getPortalLabel = (role?: string) => {
  const r = (role || '').toLowerCase()
  switch (r) {
    case 'admin':
      return 'Admin Portal'
    case 'manager':
      return 'Manager Portal'
    case 'owner':
    case 'landlord':
      return 'Owner Portal'
    case 'agent':
    case 'realtor':
      return 'Agent Portal'
    case 'service_provider':
    case 'contractor':
    case 'vendor':
      return 'Contractor Portal'
    case 'tenant':
    case 'resident':
      return 'Tenant Portal'
    default:
      return 'My Dashboard'
  }
}

const PublicNavbar: React.FC = () => {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, getDashboardPath } = useAuth()

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
        <Link to="/" className="brand" aria-label="PropNoxa home">
          <Logo size={36} />
        </Link>

        <nav id="primary-navigation" className={`nav-links ${open ? 'open' : ''}`} aria-label="Primary" aria-expanded={open}>
          {LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={isActive(link) ? 'nav-link active' : 'nav-link'}
              aria-current={isActive(link) ? 'page' : undefined}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="nav-cta-group">
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Link to={getDashboardPath()} className="nav-cta" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span>{getPortalLabel(user.role)}</span>
                <span>→</span>
              </Link>
              <button onClick={handleLogout} className="nav-cta-ghost" style={{ padding: '6px 14px', fontSize: 13 }}>
                Sign Out
              </button>
            </div>
          ) : (
            <>
              <Link to="/login" className="nav-cta-ghost">Sign In</Link>
              <Link to="/register" className="nav-cta">Create Account</Link>
            </>
          )}
          <button className="nav-toggle" aria-label="Menu" aria-controls="primary-navigation" aria-expanded={open} onClick={() => setOpen(o => !o)}>
            <span /> <span /> <span />
          </button>
        </div>
      </div>
    </header>
  )
}

export default PublicNavbar