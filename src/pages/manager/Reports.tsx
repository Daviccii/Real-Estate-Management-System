import React, { useCallback, useEffect, useState } from 'react'
import { managerService } from '../../services/manager'
import type { ManagerProperty } from '../../services/manager'
import { downloadReportCsv, getReport } from '../../services/reports'
import type { ReportEnvelope, ReportParams, ReportType } from '../../services/reports'

const REPORT_TABS: Array<{ type: ReportType; label: string; description: string }> = [
  { type: 'occupancy', label: 'Occupancy', description: 'Unit occupancy and active leases per property' },
  { type: 'payments', label: 'Payments', description: 'Monthly expected vs collected rent and arrears' },
  { type: 'maintenance', label: 'Maintenance', description: 'Requests, resolution time and cost per category' },
  { type: 'financial', label: 'Financial', description: 'Monthly income, expenses and net position' },
]

const formatValue = (key: string, value: number | string | null): string => {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'number') {
    if (key.endsWith('_rate')) return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
  }
  return String(value)
}

const ManagerReports: React.FC = () => {
  const [reportType, setReportType] = useState<ReportType>('occupancy')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [propertyId, setPropertyId] = useState<number | ''>('')
  const [properties, setProperties] = useState<ManagerProperty[]>([])
  const [report, setReport] = useState<ReportEnvelope | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)

  const buildParams = useCallback((): ReportParams => {
    const params: ReportParams = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = `${dateTo}T23:59:59`
    if (propertyId !== '') params.property_id = propertyId
    return params
  }, [dateFrom, dateTo, propertyId])

  const loadReport = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setReport(await getReport(reportType, buildParams()))
    } catch (err: any) {
      setError(err?.message || 'Failed to load report')
    } finally {
      setLoading(false)
    }
  }, [reportType, buildParams])

  useEffect(() => {
    loadReport()
  }, [loadReport])

  useEffect(() => {
    managerService.getProperties().then(setProperties).catch(() => setProperties([]))
  }, [])

  const handleDownload = async () => {
    setDownloading(true)
    setError(null)
    try {
      await downloadReportCsv(reportType, buildParams())
    } catch (err: any) {
      setError(err?.message || 'Failed to download report')
    } finally {
      setDownloading(false)
    }
  }

  const activeTab = REPORT_TABS.find((tab) => tab.type === reportType)!

  return (
    <div className="management-container">
      <div className="management-header">
        <span className="manager-eyebrow">Performance intelligence</span>
        <h1>Reports</h1>
        <p>{activeTab.description} — preview here and export the same rows as CSV</p>
      </div>

      <div className="controls-section" role="tablist" aria-label="Report type" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {REPORT_TABS.map((tab) => (
          <button
            key={tab.type}
            role="tab"
            aria-selected={tab.type === reportType}
            className={tab.type === reportType ? 'button small' : 'button small muted'}
            onClick={() => setReportType(tab.type)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="controls-section">
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '.75rem', fontWeight: 700 }}>From</span>
            <input
              type="date"
              className="input"
              aria-label="From date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '.75rem', fontWeight: 700 }}>To</span>
            <input
              type="date"
              className="input"
              aria-label="To date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: '.75rem', fontWeight: 700 }}>Property</span>
            <select
              className="input"
              aria-label="Property filter"
              value={propertyId}
              onChange={(e) => setPropertyId(e.target.value === '' ? '' : Number(e.target.value))}
            >
              <option value="">All properties</option>
              {properties.map((property) => (
                <option key={property.id} value={property.id}>{property.name}</option>
              ))}
            </select>
          </label>
          <button onClick={loadReport} className="button small" disabled={loading}>
            {loading ? 'Running…' : 'Run report'}
          </button>
          <button onClick={handleDownload} className="button small secondary" disabled={downloading || loading}>
            {downloading ? 'Preparing…' : 'Download CSV'}
          </button>
        </div>
        {reportType === 'occupancy' && (
          <p style={{ margin: '10px 2px 0', fontSize: '.78rem', color: 'var(--muted)' }}>
            Occupancy is a point-in-time snapshot, so date filters do not apply to it.
          </p>
        )}
      </div>

      {error && <div className="empty error">{error}</div>}

      {report && (
        <>
          <div className="stats-grid">
            {report.summary.map((item) => (
              <div className="stat-card" key={item.key}>
                <div className="stat-label">{item.label}</div>
                <div className="stat-value">{formatValue(item.key, item.value)}</div>
              </div>
            ))}
          </div>

          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  {report.columns.map((column) => (
                    <th key={column.key}>{column.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {report.rows.length === 0 ? (
                  <tr>
                    <td colSpan={report.columns.length} style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                      No data for the selected filters
                    </td>
                  </tr>
                ) : (
                  report.rows.map((row, index) => (
                    <tr key={`${row[report.columns[0].key] ?? index}`}>
                      {report.columns.map((column) => (
                        <td key={column.key}>{formatValue(column.key, row[column.key])}</td>
                      ))}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <p style={{ marginTop: 12, textAlign: 'center', fontSize: '.78rem', color: 'var(--muted)' }}>
            {report.rows.length} row{report.rows.length === 1 ? '' : 's'} · generated{' '}
            {new Date(report.generated_at).toLocaleString()}
          </p>
        </>
      )}

      {loading && !report && <div className="empty">Running report…</div>}
    </div>
  )
}

export default ManagerReports
