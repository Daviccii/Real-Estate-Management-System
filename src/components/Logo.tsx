import React from 'react'

type LogoProps = {
  /** Badge + full wordmark, or just the badge (e.g. for tight mobile headers). */
  variant?: 'full' | 'mark'
  size?: number
  className?: string
}

/**
 * PropNoxa brand mark: solid indigo monogram badge with an amber baseline
 * accent, paired with a two-tone wordmark ("Prop" in ink, "Noxa" in brand
 * blue). Self-contained SVG + inline styles so it renders consistently
 * regardless of which stylesheet is loaded around it (navbar, footer,
 * favicon export, etc).
 */
const Logo: React.FC<LogoProps> = ({ variant = 'full', size = 36, className }) => {
  const badge = (
    <svg
      width={size}
      height={size}
      viewBox="0 0 72 72"
      role="img"
      aria-label="PropNoxa"
      className="pn-logo-badge"
    >
      <rect width="72" height="72" rx="18" fill="#1D3FD6" />
      <text
        x="36"
        y="46"
        textAnchor="middle"
        fontFamily="inherit"
        fontSize="30"
        fontWeight={800}
        fill="#ffffff"
      >
        PN
      </text>
      <rect x="0" y="64" width="72" height="8" fill="#F5A623" />
    </svg>
  )

  if (variant === 'mark') return <span className={className}>{badge}</span>

  return (
    <span className={className} style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      {badge}
      <span style={{ fontWeight: 800, fontSize: size * 0.52, letterSpacing: '-0.02em', lineHeight: 1 }}>
        <span style={{ color: '#0B1220' }}>Prop</span>
        <span style={{ color: '#1D3FD6' }}>Noxa</span>
      </span>
    </span>
  )
}

export default Logo