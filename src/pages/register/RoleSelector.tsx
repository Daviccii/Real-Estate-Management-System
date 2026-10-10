import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from '../../i18n/LanguageContext'

interface RoleOption {
  id: string
  titleKey: string
  badgeKey: string
  descriptionKey: string
  path: string
  icon: string
  highlightKeys: string[]
  color: string
}

const ROLES: RoleOption[] = [
  {
    id: 'tenant',
    titleKey: 'register.tenant.title',
    badgeKey: 'register.tenant.badge',
    descriptionKey: 'register.tenant.description',
    path: '/register/tenant',
    icon: '🏠',
    highlightKeys: ['register.tenant.h1', 'register.tenant.h2', 'register.tenant.h3'],
    color: '#2563eb'
  },
  {
    id: 'owner',
    titleKey: 'register.owner.title',
    badgeKey: 'register.owner.badge',
    descriptionKey: 'register.owner.description',
    path: '/register/owner',
    icon: '🏢',
    highlightKeys: ['register.owner.h1', 'register.owner.h2', 'register.owner.h3'],
    color: '#059669'
  },
  {
    id: 'agent',
    titleKey: 'register.agent.title',
    badgeKey: 'register.agent.badge',
    descriptionKey: 'register.agent.description',
    path: '/register/agent',
    icon: '🤝',
    highlightKeys: ['register.agent.h1', 'register.agent.h2', 'register.agent.h3'],
    color: '#7c3aed'
  },
  {
    id: 'provider',
    titleKey: 'register.provider.title',
    badgeKey: 'register.provider.badge',
    descriptionKey: 'register.provider.description',
    path: '/register/provider',
    icon: '🔧',
    highlightKeys: ['register.provider.h1', 'register.provider.h2', 'register.provider.h3'],
    color: '#d97706'
  }
]

export const RoleSelector: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', padding: '40px 20px' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <Link to="/" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{
              background: 'linear-gradient(135deg, var(--accent), var(--accent-2))',
              color: '#fff',
              padding: '6px 12px',
              borderRadius: '8px',
              fontWeight: 800,
              fontSize: '16px'
            }}>
              PropNoxa
            </span>
          </Link>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent)', margin: '8px 0' }}>
            {t('register.title')}
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '1.05rem', maxWidth: '600px', margin: '0 auto' }}>
            {t('register.subtitle')}
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '24px',
          marginBottom: '40px'
        }}>
          {ROLES.map((role) => (
            <div
              key={role.id}
              onClick={() => navigate(role.path)}
              style={{
                background: 'var(--surface)',
                borderRadius: '16px',
                padding: '28px',
                boxShadow: 'var(--card-shadow)',
                border: '2px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)'
                e.currentTarget.style.borderColor = role.color
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'none'
                e.currentTarget.style.borderColor = 'transparent'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <span style={{ fontSize: '2.4rem' }}>{role.icon}</span>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '4px 10px',
                    borderRadius: '20px',
                    background: `${role.color}15`,
                    color: role.color
                  }}>
                    {t(role.badgeKey)}
                  </span>
                </div>

                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '8px' }}>
                  {t(role.titleKey)}
                </h2>
                <p style={{ color: 'var(--muted)', fontSize: '0.9rem', lineHeight: 1.5, marginBottom: '20px' }}>
                  {t(role.descriptionKey)}
                </p>

                <div style={{ borderTop: '1px solid var(--line)', paddingTop: '16px', marginBottom: '20px' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {t('register.included')}
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {role.highlightKeys.map((highlightKey) => (
                      <li key={highlightKey} style={{ fontSize: '0.85rem', color: '#334155' }}>
                        {t(highlightKey)}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(role.path)
                }}
                style={{
                  width: '100%',
                  background: role.color,
                  color: '#fff',
                  border: 'none',
                  borderRadius: '10px',
                  padding: '12px',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  cursor: 'pointer',
                  transition: 'opacity 0.2s ease'
                }}
              >
                {t('register.asRole', { role: t(role.titleKey).split('/')[0].trim() })} &rarr;
              </button>
            </div>
          ))}
        </div>

        <div style={{ textAlign: 'center', color: 'var(--muted)', fontSize: '0.95rem' }}>
          {t('register.haveAccount')}{' '}
          <Link to="/login" style={{ color: 'var(--accent-2)', fontWeight: 700, textDecoration: 'none' }}>
            {t('register.signInHere')}
          </Link>
        </div>
      </div>
    </div>
  )
}

export default RoleSelector
