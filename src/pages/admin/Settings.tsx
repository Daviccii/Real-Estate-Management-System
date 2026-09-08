import React, { useEffect, useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { adminService } from '../../services/admin'
import type { PlatformSettings } from '../../services/admin'
import { useToast } from '../../components/ToastProvider'

const AdminSettings: React.FC = () => {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [settings, setSettings] = useState<PlatformSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => { loadSettings() }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const data = await adminService.getSettings()
      setSettings(data)
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to load settings', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const patch = async (change: Partial<PlatformSettings>) => {
    if (!settings) return
    setSaving(true)
    // optimistic update
    setSettings({ ...settings, ...change })
    try {
      const updated = await adminService.updateSettings(change)
      setSettings(updated)
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to save setting', type: 'error' })
      loadSettings() // revert to server truth on failure
    } finally {
      setSaving(false)
    }
  }

  if (loading || !settings) {
    return (
      <div className="page">
        <h1>Admin Settings</h1>
        <div className="empty">Loading settings…</div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>Admin Settings</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Account Settings</h3>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>Email</label>
            <div style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 4 }}>{user?.email || 'N/A'}</div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>Name</label>
            <div style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 4 }}>{user?.full_name || 'N/A'}</div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>Role</label>
            <div style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 4 }}>{user?.role || 'N/A'}</div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Platform Settings</h3>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.enable_user_registration}
                disabled={saving}
                onChange={e => patch({ enable_user_registration: e.target.checked })}
              />
              <span>Enable user registration</span>
            </label>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.require_email_verification}
                disabled={saving}
                onChange={e => patch({ require_email_verification: e.target.checked })}
              />
              <span>Require email verification</span>
            </label>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.enable_property_moderation}
                disabled={saving}
                onChange={e => patch({ enable_property_moderation: e.target.checked })}
              />
              <span>Enable property moderation</span>
            </label>
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Security Settings</h3>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>Session Timeout</label>
            <select
              className="input"
              style={{ width: '100%' }}
              disabled={saving}
              value={settings.session_timeout_minutes}
              onChange={e => patch({ session_timeout_minutes: Number(e.target.value) })}
            >
              <option value={30}>30 minutes</option>
              <option value={60}>60 minutes</option>
              <option value={120}>120 minutes</option>
            </select>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>Minimum Password Length</label>
            <select
              className="input"
              style={{ width: '100%' }}
              disabled={saving}
              value={settings.password_min_length}
              onChange={e => patch({ password_min_length: Number(e.target.value) })}
            >
              <option value={6}>6 characters</option>
              <option value={8}>8 characters</option>
              <option value={12}>12 characters</option>
            </select>
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Notification Settings</h3>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.notify_new_users}
                disabled={saving}
                onChange={e => patch({ notify_new_users: e.target.checked })}
              />
              <span>Email notifications for new users</span>
            </label>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.notify_new_inquiries}
                disabled={saving}
                onChange={e => patch({ notify_new_inquiries: e.target.checked })}
              />
              <span>Email notifications for new inquiries</span>
            </label>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.notify_property_updates}
                disabled={saving}
                onChange={e => patch({ notify_property_updates: e.target.checked })}
              />
              <span>Email notifications for property updates</span>
            </label>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 24 }}>
        <h3 style={{ marginBottom: 12 }}>Platform Information</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 8, fontSize: 14 }}>
          <span style={{ color: 'var(--muted)' }}>Version:</span>
          <span>1.0.0</span>
          <span style={{ color: 'var(--muted)' }}>Environment:</span>
          <span>Development</span>
          <span style={{ color: 'var(--muted)' }}>Last updated:</span>
          <span>{settings.updated_at ? new Date(settings.updated_at).toLocaleString() : 'Never'}</span>
        </div>
      </div>
    </div>
  )
}

export default AdminSettings