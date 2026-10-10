import { useEffect, useState } from 'react'

import type { PropertyTour } from '../types'

const PROVIDER_LABELS: Record<string, string> = {
  matterport: 'Matterport 3D',
  kuula: 'Kuula 360°',
  roundme: 'RoundMe 360°',
  sketchfab: 'Sketchfab 3D',
  youtube: 'YouTube 360° Video',
  link: 'External tour',
}

interface VirtualTourViewerProps {
  tours: PropertyTour[]
  isOpen: boolean
  onClose: () => void
  initialIndex?: number
}

export default function VirtualTourViewer({ tours, isOpen, onClose, initialIndex = 0 }: VirtualTourViewerProps) {
  const [activeIndex, setActiveIndex] = useState(initialIndex)

  useEffect(() => {
    if (isOpen) {
      setActiveIndex(Math.min(Math.max(initialIndex, 0), Math.max(tours.length - 1, 0)))
    }
  }, [isOpen, initialIndex, tours.length])

  useEffect(() => {
    if (!isOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [isOpen, onClose])

  if (!isOpen || tours.length === 0) return null

  const active = tours[Math.min(activeIndex, tours.length - 1)] ?? tours[0]
  // Defence in depth: the backend only ever emits rebuilt https embed URLs,
  // but the client refuses anything else outright.
  const embedUrl = active.embed_url && active.embed_url.startsWith('https://') ? active.embed_url : null
  const providerLabel = PROVIDER_LABELS[active.provider] || 'Virtual tour'

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Virtual tour viewer"
      onClick={onClose}
    >
      <div className="tour-modal" onClick={(event) => event.stopPropagation()}>
        <div className="tour-modal-head">
          <div>
            <span className="tour-modal-eyebrow">{providerLabel}</span>
            <h3>{active.title || 'Property virtual tour'}</h3>
          </div>
          <button type="button" className="close-button" aria-label="Close tour viewer" onClick={onClose}>
            ✕
          </button>
        </div>

        {embedUrl ? (
          <div className="tour-frame-wrap">
            <iframe
              key={active.id}
              src={embedUrl}
              title={active.title || 'Property virtual tour'}
              className="tour-frame"
              sandbox="allow-scripts allow-same-origin allow-presentation allow-popups allow-fullscreen"
              allow="fullscreen; xr-spatial-tracking; gyroscope; accelerometer"
              allowFullScreen
              loading="lazy"
            />
          </div>
        ) : (
          <div className="tour-link-fallback">
            {active.thumbnail_url ? (
              <img src={active.thumbnail_url} alt="" className="tour-fallback-image" />
            ) : (
              <div className="tour-fallback-image tour-fallback-placeholder">360°</div>
            )}
            <p>This tour is hosted on an external site and opens in a new tab.</p>
            <a className="button" href={active.url} target="_blank" rel="noreferrer noopener">
              Open tour in new tab
            </a>
          </div>
        )}

        <div className="tour-modal-foot">
          {tours.length > 1 && (
            <div className="tour-switcher" role="tablist" aria-label="Available tours">
              {tours.map((tour, index) => (
                <button
                  key={tour.id}
                  type="button"
                  role="tab"
                  aria-selected={index === activeIndex}
                  className={`tour-chip${index === activeIndex ? ' is-active' : ''}`}
                  onClick={() => setActiveIndex(index)}
                >
                  {tour.title || `Tour ${index + 1}`}
                </button>
              ))}
            </div>
          )}
          <a className="button muted small" href={active.url} target="_blank" rel="noreferrer noopener">
            Open in new tab ↗
          </a>
        </div>
      </div>
    </div>
  )
}
