import React, { useEffect, useState } from 'react'

import BarChart from '../components/charts/BarChart'
import DonutChart from '../components/charts/DonutChart'
import LineChart from '../components/charts/LineChart'
import StatCard from '../components/StatCard'
import { useAuth } from '../contexts/AuthContext'
import { getAnalyticsDashboard } from '../services/analytics'
import type { AnalyticsEnvelope } from '../services/analytics'
import { formatCompact, monthLabel } from '../components/charts/chartUtils'

const RANGES = [
  { months: 3, label: '3M' },
  { months: 6, label: '6M' },
  { months: 12, label: '12M' },
]

const CHART_COLORS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
  'var(--chart-6)',
]

const FINANCIAL_SERIES = [
  { key: 'income', label: 'Income', color: 'var(--chart-2)' },
  { key: 'expenses', label: 'Expenses', color: 'var(--chart-4)' },
  { key: 'net', label: 'Net', color: 'var(--chart-1)' },
]

const PAYMENT_SEGMENTS = [
  { label: 'Collected', color: 'var(--chart-2)' },
  { label: 'Outstanding', color: 'var(--chart-3)' },
]

const MAINTENANCE_SEGMENTS = [
  { label: 'Requests', color: 'var(--chart-1)' },
  { label: 'Resolved', color: 'var(--chart-2)' },
]

const ROLE_HEADINGS: Record<string, { title: string; eyebrow: string }> = {
  admin: { title: 'Platform Analytics', eyebrow: 'Platform intelligence' },
  manager: { title: 'Operations Analytics', eyebrow: 'Performance intelligence' },
  owner: { title: 'Portfolio Analytics', eyebrow: 'Portfolio intelligence' },
  landlord: { title: 'Portfolio Analytics', eyebrow: 'Portfolio intelligence' },
}

const formatCount = (value: number): string => value.toLocaleString()

const formatMoney = (value: number): string => `KSh ${Math.round(value).toLocaleString()}`

const formatRate = (value: number): string => `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`

const humanize = (value: string): string => {
  const text = value.replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

const AnalyticsDashboard: React.FC = () => {
  const { user } = useAuth()
  const [months, setMonths] = useState(6)
  const [data, setData] = useState<AnalyticsEnvelope | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getAnalyticsDashboard(months)
      .then((response) => {
        if (!cancelled) setData(response)
      })
      .catch((err: any) => {
        if (!cancelled) setError(err?.message || 'Failed to load analytics')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [months])

  const role = (user?.role || '').toLowerCase()
  const heading = ROLE_HEADINGS[role] || { title: 'Analytics', eyebrow: 'Performance intelligence' }
  const eyebrowClass = ['admin', 'manager', 'owner', 'landlord'].includes(role) ? `${role}-eyebrow` : 'manager-eyebrow'

  const kpis = data?.kpis
  const cities = data?.distributions.properties_by_city || []
  const categories = data?.distributions.maintenance_by_category || []
  const cityMax = cities.reduce((max, row) => Math.max(max, row.count), 0)
  const categoryMax = categories.reduce((max, row) => Math.max(max, row.requests), 0)

  const unitSlices = Object.entries(data?.distributions.units_by_status || {}).map(([status, count], index) => ({
    label: humanize(status),
    value: count,
    color: CHART_COLORS[index % CHART_COLORS.length],
  }))

  return (
    <div className="management-container">
      <div className="management-header">
        <span className={eyebrowClass}>{heading.eyebrow}</span>
        <h1>{heading.title}</h1>
        <p>
          {data
            ? `Rolling ${data.months}-month view · ${monthLabel(data.period.start, true)} → ${monthLabel(data.period.end, true)}`
            : 'Role-scoped KPIs, trends and portfolio distributions'}
        </p>
      </div>

      <div className="controls-section" role="group" aria-label="Time range" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {RANGES.map((range) => (
          <button
            key={range.months}
            type="button"
            aria-pressed={range.months === months}
            aria-label={`${range.months} months`}
            className={range.months === months ? 'button small' : 'button small muted'}
            onClick={() => setMonths(range.months)}
          >
            {range.label}
          </button>
        ))}
      </div>

      {error && <div className="empty error">{error}</div>}
      {loading && !data && <div className="empty">Loading analytics…</div>}

      {data && kpis && (
        <>
          <div className="analytics-kpis">
            <StatCard title="Properties" icon="🏠" value={formatCount(kpis.properties)} subtitle="in scope" />
            <StatCard
              title="Total units"
              icon="🏢"
              value={formatCount(kpis.total_units)}
              subtitle={`${formatCount(kpis.occupied_units)} occupied · ${formatCount(kpis.vacant_units)} vacant`}
            />
            <StatCard
              title="Occupancy rate"
              icon="📊"
              value={formatRate(kpis.occupancy_rate)}
              subtitle="of all units occupied"
            />
            <StatCard
              title="Active leases"
              icon="📄"
              value={formatCount(kpis.active_leases)}
              subtitle={`${formatCount(kpis.leases_expiring_soon)} expiring within 30 days`}
            />
            <StatCard
              title="Open maintenance"
              icon="🔧"
              value={formatCount(kpis.open_maintenance)}
              subtitle="pending or in progress"
            />
            <StatCard
              title="Overdue payments"
              icon="⚠️"
              value={formatCount(kpis.overdue_payments)}
              subtitle="marked overdue"
            />
            <StatCard
              title="Collected in period"
              icon="💰"
              value={formatMoney(kpis.period_collected)}
              subtitle={`${formatRate(kpis.period_collection_rate)} of ${formatMoney(kpis.period_expected)} expected`}
            />
            <StatCard
              title="Net position"
              icon="📈"
              value={formatMoney(kpis.period_net)}
              subtitle={`${formatMoney(kpis.period_expenses)} maintenance expenses`}
            />
          </div>

          <div className="analytics-grid">
            <div className="card chart-card span-2">
              <div className="chart-card-header">
                <h2 className="chart-title">Financial trend</h2>
                <p className="chart-subtitle">Collected income vs resolved maintenance costs</p>
              </div>
              <LineChart
                ariaLabel="Monthly income, expenses and net position"
                data={data.series.financial}
                series={FINANCIAL_SERIES}
                formatValue={formatCompact}
              />
              <ul className="chart-legend">
                {FINANCIAL_SERIES.map((series) => (
                  <li key={series.key}>
                    <span className="chart-legend-dot" style={{ background: series.color }} aria-hidden="true" />
                    <span>{series.label}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="card chart-card">
              <div className="chart-card-header">
                <h2 className="chart-title">Rent collection</h2>
                <p className="chart-subtitle">Monthly expected split by collected and outstanding</p>
              </div>
              <BarChart
                ariaLabel="Monthly collected and outstanding rent"
                data={data.series.payments.map((point) => ({
                  label: monthLabel(point.month),
                  values: [point.collected, point.outstanding],
                }))}
                segments={PAYMENT_SEGMENTS}
              />
              <ul className="chart-legend">
                {PAYMENT_SEGMENTS.map((segment) => (
                  <li key={segment.label}>
                    <span className="chart-legend-dot" style={{ background: segment.color }} aria-hidden="true" />
                    <span>{segment.label}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="card chart-card">
              <div className="chart-card-header">
                <h2 className="chart-title">Portfolio mix</h2>
                <p className="chart-subtitle">Units by current status</p>
              </div>
              <DonutChart
                ariaLabel="Units by status"
                slices={unitSlices}
                centerValue={formatCount(kpis.total_units)}
                centerLabel="units"
              />
            </div>

            <div className="card chart-card">
              <div className="chart-card-header">
                <h2 className="chart-title">Maintenance inflow</h2>
                <p className="chart-subtitle">Requests opened vs resolved per month</p>
              </div>
              <BarChart
                ariaLabel="Monthly maintenance requests and resolutions"
                data={data.series.maintenance.map((point) => ({
                  label: monthLabel(point.month),
                  values: [point.requests, point.resolved],
                }))}
                segments={MAINTENANCE_SEGMENTS}
                stacked={false}
                formatValue={formatCount}
              />
              <ul className="chart-legend">
                {MAINTENANCE_SEGMENTS.map((segment) => (
                  <li key={segment.label}>
                    <span className="chart-legend-dot" style={{ background: segment.color }} aria-hidden="true" />
                    <span>{segment.label}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="card chart-card">
              <div className="chart-card-header">
                <h2 className="chart-title">Cities</h2>
                <p className="chart-subtitle">Properties per city in scope</p>
              </div>
              {cities.length === 0 ? (
                <div className="chart-empty">No properties in scope</div>
              ) : (
                <ul className="analytics-bars">
                  {cities.map((row) => (
                    <li key={row.city} className="analytics-bar-row" title={`${row.city}: ${row.count} properties`}>
                      <span className="analytics-bar-label">{row.city}</span>
                      <span className="analytics-bar-track">
                        <span
                          className="analytics-bar-fill"
                          style={{ width: `${cityMax > 0 ? Math.round((row.count / cityMax) * 100) : 0}%`, display: 'block' }}
                        />
                      </span>
                      <span className="analytics-bar-value">{formatCount(row.count)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card chart-card">
              <div className="chart-card-header">
                <h2 className="chart-title">Maintenance by category</h2>
                <p className="chart-subtitle">Opened in period · value shows resolved cost</p>
              </div>
              {categories.length === 0 ? (
                <div className="chart-empty">No maintenance in this period</div>
              ) : (
                <ul className="analytics-bars">
                  {categories.map((row) => (
                    <li
                      key={row.category}
                      className="analytics-bar-row"
                      title={`${row.category}: ${row.requests} requests · ${row.open} open`}
                    >
                      <span className="analytics-bar-label">{row.category}</span>
                      <span className="analytics-bar-track">
                        <span
                          className="analytics-bar-fill"
                          style={{
                            width: `${categoryMax > 0 ? Math.round((row.requests / categoryMax) * 100) : 0}%`,
                            display: 'block',
                            background: 'var(--chart-5)',
                          }}
                        />
                      </span>
                      <span className="analytics-bar-value">{formatMoney(row.cost)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card chart-card span-2">
              <div className="chart-card-header">
                <h2 className="chart-title">Top properties</h2>
                <p className="chart-subtitle">Ranked by rent collected in the selected window</p>
              </div>
              {data.top_properties.length === 0 ? (
                <div className="chart-empty">No properties in scope</div>
              ) : (
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Property</th>
                        <th>City</th>
                        <th>Units</th>
                        <th>Occupancy</th>
                        <th>Collected</th>
                        <th>Outstanding</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.top_properties.map((row) => (
                        <tr key={row.property_id}>
                          <td>{row.name}</td>
                          <td>{row.city}</td>
                          <td>{row.units}</td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <span className="mini-bar" style={{ flex: 1 }}>
                                <span className="mini-bar-fill" style={{ width: `${Math.min(100, row.occupancy_rate)}%`, display: 'block' }} />
                              </span>
                              <span>{formatRate(row.occupancy_rate)}</span>
                            </div>
                          </td>
                          <td>{formatMoney(row.collected)}</td>
                          <td>{formatMoney(row.outstanding)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          <p className="analytics-footer">Generated {new Date(data.generated_at).toLocaleString()}</p>
        </>
      )}
    </div>
  )
}

export default AnalyticsDashboard
