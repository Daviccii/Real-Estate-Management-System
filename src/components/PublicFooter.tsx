import React from 'react'
import { Link } from 'react-router-dom'
import Logo from './Logo'
import { useTranslation } from '../i18n/LanguageContext'

const PublicFooter: React.FC = ()=>{
  const { t } = useTranslation()
  return (
    <footer className="public-footer">
      <div className="public-footer-inner">
        <div className="footer-brand-block">
          <div className="brand" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Logo variant="mark" size={28} />
            PropNoxa
          </div>
          <p className="muted">{t('footer.blurb')}</p>
        </div>

        <div className="footer-columns">
          <section>
          <h4>{t('footer.platform')}</h4>
          <ul>
            <li><Link to="/properties">{t('footer.properties')}</Link></li>
            <li><Link to="/buy">{t('nav.buy')}</Link></li>
            <li><Link to="/rent">{t('nav.rent')}</Link></li>
            <li><Link to="/invest">{t('nav.invest')}</Link></li>
            <li><Link to="/features">{t('nav.marketInsights')}</Link></li>
          </ul>
          </section>

          <section>
          <h4>{t('footer.company')}</h4>
          <ul>
            <li><Link to="/about">{t('footer.about')}</Link></li>
            <li><Link to="/contact">{t('footer.contact')}</Link></li>
          </ul>
          </section>

          <section>
          <h4>{t('footer.account')}</h4>
          <ul>
            <li><Link to="/login">{t('common.signIn')}</Link></li>
            <li><Link to="/register">{t('common.createAccount')}</Link></li>
          </ul>
          </section>

          <section>
            <h4>{t('footer.legal')}</h4>
            <ul>
              <li><Link to="/privacy">{t('footer.privacy')}</Link></li>
              <li><span className="footer-placeholder">{t('footer.terms')}</span></li>
            </ul>
          </section>
        </div>
      </div>
      <div className="footer-bottom">{t('footer.rights', { year: new Date().getFullYear() })}</div>
    </footer>
  )
}

export default PublicFooter