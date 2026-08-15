import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import Logo from './Logo'

const LINKS = [
  { label: 'Home', to: '/' },
  { label: 'Buy', to: '/buy' },
  { label: 'Rent', to: '/rent' },
  { label: 'Invest', to: '/invest' },
  { label: 'Explore', to: '/properties' },
  { label: 'Market Insights', to: '/features' },
] as const

const PublicNavbar: React.FC = ()=>{
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()

  useEffect(() => {
    function onScroll(){ setScrolled(window.scrollY > 8) }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function isActive(link: typeof LINKS[number]) {
    return location.pathname === link.to
  }

  return (
    <header className={`public-nav ${scrolled? 'scrolled':''}`} role="banner">
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
          <Link to="/login" className="nav-cta-ghost">Sign In</Link>
          <Link to="/register" className="nav-cta">Create Account</Link>
          <button className="nav-toggle" aria-label="Menu" aria-controls="primary-navigation" aria-expanded={open} onClick={() => setOpen(o => !o)}>
            <span /> <span /> <span />
          </button>
        </div>
      </div>
    </header>
  )
}

export default PublicNavbar