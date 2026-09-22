import React, { useEffect, useState } from 'react'
import { getAuditLogs } from '../../services/auditLog'
import { AuditLog } from '../../types'

export const AdminAuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [entityFilter, setEntityFilter] = useState('')
  const [actionFilter, setActionFilter] = useState('')
  const [limit, setLimit] = useState(50)

  const loadLogs = async () => {
    setLoading(true)
    try {
      const data = await getAuditLogs({
        entity_type: entityFilter || undefined,
        action: actionFilter || undefined,
        limit
      })
      setLogs(data)
    } catch (err: any) {
      console.error('Failed to load audit logs', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLogs()
  }, [entityFilter, actionFilter, limit])

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-slate-900 via-gray-900 to-zinc-900 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-block px-3 py-1 bg-slate-700/50 text-slate-300 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
              System Forensics & Governance
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Immutable System Audit Trail</h1>
            <p className="text-slate-400 text-sm mt-1">
              Traceable activity stream recording every security event, lease signing, application review, and verification approval.
            </p>
          </div>
          <button
            onClick={loadLogs}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-sm font-medium transition backdrop-blur flex items-center gap-2 self-start md:self-auto"
          >
            <span>🔄</span> Refresh Logs
          </button>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm flex flex-wrap items-center gap-4 text-xs font-medium text-slate-700">
        <div className="flex items-center gap-2">
          <label>Entity Type:</label>
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="px-3 py-1.5 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Entities</option>
            <option value="property">Property</option>
            <option value="application">Rental Application</option>
            <option value="lease">Lease Agreement</option>
            <option value="payment">Payment & Receipt</option>
            <option value="verification">Verification</option>
            <option value="building">Building / Complex</option>
            <option value="work_order">Maintenance Work Order</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label>Action Query:</label>
          <input
            type="text"
            placeholder="e.g. approve, create, review"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="px-3 py-1.5 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 w-48"
          />
        </div>

        <div className="flex items-center gap-2">
          <label>Records Limit:</label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-3 py-1.5 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="25">25 records</option>
            <option value="50">50 records</option>
            <option value="100">100 records</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-400 text-sm">Streaming audit trail records...</div>
        ) : logs.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">No audit records found matching current query.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Changes & Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 px-4 whitespace-nowrap text-slate-500 font-mono">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-full font-bold uppercase tracking-wider bg-slate-100 text-slate-800">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="font-semibold text-slate-700">
                        {log.entity_type} {log.entity_id ? `#${log.entity_id}` : ''}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="font-medium text-slate-800">{log.user_email || `User #${log.user_id || 'System'}`}</div>
                      {log.ip_address && <div className="text-[10px] text-slate-400 font-mono">IP: {log.ip_address}</div>}
                    </td>
                    <td className="py-3 px-4 text-slate-600 max-w-md break-words font-mono text-[11px]">
                      {log.details_json || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminAuditLogs
