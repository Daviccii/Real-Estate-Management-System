import React, { useEffect, useState } from 'react'

import { propertyService } from '../services/property'
import { useToast } from '../components/ToastProvider'
import type { PropertyTour } from '../types'

const PROVIDER_LABELS: Record<string, string> = {
  matterport: 'Matterport 3D',
  kuula: 'Kuula 360°',
  roundme: 'RoundMe 360°',
  sketchfab: 'Sketchfab 3D',
  youtube: 'YouTube 360° Video',
  link: 'External link',
}

const HTTPS_URL = /^https:\/\/\S+$/i

interface TourEditorProps {
  propertyId: number
}

export default function TourEditor({ propertyId }: TourEditorProps) {
  const { addToast } = useToast()
  const [tours, setTours] = useState<PropertyTour[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [thumbnail, setThumbnail] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    propertyService
      .listTours(propertyId)
      .then((rows) => {
        if (!cancelled) setTours(rows || [])
      })
      .catch((err: any) => {
        if (!cancelled) addToast({ message: err?.message || 'Could not load tours', type: 'error' })
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propertyId])

  const handleAdd = async (event: React.FormEvent) => {
    event.preventDefault()
    const cleanUrl = url.trim()
    if (!HTTPS_URL.test(cleanUrl)) {
      addToast({ message: 'Tour link must start with https://', type: 'error' })
      return
    }
    setSaving(true)
    try {
      const created = await propertyService.addTour(propertyId, {
        url: cleanUrl,
        title: title.trim() || undefined,
        thumbnail_url: thumbnail.trim() || undefined,
      })
      if (created) {
        setTours((prev) => [...prev, created])
        setUrl('')
        setTitle('')
        setThumbnail('')
        addToast({
          message: created.embed_url
            ? 'Embeddable 360° tour added'
            : 'Tour link added — it will open on the external site',
          type: 'success',
        })
      }
    } catch (err: any) {
      addToast({ message: err?.message || 'Could not add tour', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (tour: PropertyTour) => {
    if (confirmingId !== tour.id) {
      setConfirmingId(tour.id)
      return
    }
    try {
      await propertyService.removeTour(propertyId, tour.id)
      setTours((prev) => prev.filter((item) => item.id !== tour.id))
      addToast({ message: 'Tour removed', type: 'success' })
    } catch (err: any) {
      addToast({ message: err?.message || 'Could not remove tour', type: 'error' })
    } finally {
      setConfirmingId(null)
    }
  }

  return (
    <div className="card tour-editor">
      <div className="tour-editor-head">
        <h3>360° / Virtual Tours</h3>
        <p>
          Paste a share link from Matterport, Kuula, RoundMe, Sketchfab or YouTube. Recognised links
          play embedded on the listing page; other https links are shown as an external tour button.
        </p>
      </div>

      {loading && tours.length === 0 ? (
        <div className="empty">Loading tours…</div>
      ) : tours.length === 0 ? (
        <div className="empty">No tours yet. Add your first 360° experience below.</div>
      ) : (
        <ul className="tour-editor-list">
          {tours.map((tour) => (
            <li key={tour.id} className="tour-editor-row">
              <div className="tour-editor-row-main">
                <strong>{tour.title || 'Untitled tour'}</strong>
                <span className={`tour-badge${tour.embed_url ? ' is-embeddable' : ''}`}>
                  {PROVIDER_LABELS[tour.provider] || 'Virtual tour'}
                  {tour.embed_url ? ' · embedded' : ' · external'}
                </span>
                <a href={tour.url} target="_blank" rel="noreferrer noopener" className="tour-editor-url">
                  {tour.url}
                </a>
              </div>
              <button
                type="button"
                className={`button small ${confirmingId === tour.id ? 'danger' : 'muted'}`}
                onClick={() => handleDelete(tour)}
                onBlur={() => setConfirmingId((current) => (current === tour.id ? null : current))}
              >
                {confirmingId === tour.id ? 'Confirm delete?' : 'Delete'}
              </button>
            </li>
          ))}
        </ul>
      )}

      <form className="tour-editor-form" onSubmit={handleAdd}>
        <div className="form-group">
          <label htmlFor="tour-url">Tour share link (https) *</label>
          <input
            id="tour-url"
            type="url"
            required
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://my.matterport.com/show/?m=…"
          />
        </div>
        <div className="tour-editor-form-grid">
          <div className="form-group">
            <label htmlFor="tour-title">Title (optional)</label>
            <input
              id="tour-title"
              type="text"
              value={title}
              maxLength={255}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Living room 360°"
            />
          </div>
          <div className="form-group">
            <label htmlFor="tour-thumbnail">Thumbnail URL (optional)</label>
            <input
              id="tour-thumbnail"
              type="url"
              value={thumbnail}
              onChange={(event) => setThumbnail(event.target.value)}
              placeholder="https://…/preview.jpg"
            />
          </div>
        </div>
        <button type="submit" className="button" disabled={saving}>
          {saving ? 'Adding…' : 'Add tour'}
        </button>
      </form>
    </div>
  )
}
