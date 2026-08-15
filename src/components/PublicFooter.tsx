import React from 'react'
import { Link } from 'react-router-dom'
import Logo from './Logo'

const PublicFooter: React.FC = ()=>{
  return (
    <footer className="public-footer">
      <div className="public-footer-inner">
        <div className="footer-brand-block">
          <div className="brand" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Logo variant="mark" size={28} />
            PropNoxa
          </div>
          <p className="muted">Discover, compare and manage real estate with intelligence built for modern property journeys.</p>
        </div>

        <div className="footer-columns">
          <section>
          <h4>Platform</h4>
          <ul>
            <li><Link to="/properties">Properties</Link></li>
            <li><Link to="/buy">Buy</Link></li>
            <li><Link to="/rent">Rent</Link></li>
            <li><Link to="/invest">Invest</Link></li>
            <li><Link to="/features">Market Insights</Link></li>
          </ul>
          </section>

          <section>
          <h4>Company</h4>
          <ul>
            <li><Link to="/about">About</Link></li>
            <li><Link to="/contact">Contact</Link></li>
          </ul>
          </section>

          <section>
          <h4>Account</h4>
          <ul>
            <li><Link to="/login">Sign In</Link></li>
            <li><Link to="/register">Create Account</Link></li>
          </ul>
          </section>

          <section>
            <h4>Legal</h4>
            <ul>
              <li><span className="footer-placeholder">Privacy (coming soon)</span></li>
              <li><span className="footer-placeholder">Terms (coming soon)</span></li>
            </ul>
          </section>
        </div>
      </div>
      <div className="footer-bottom">© {new Date().getFullYear()} PropNoxa. All rights reserved.</div>
    </footer>
  )
}

export default PublicFooter