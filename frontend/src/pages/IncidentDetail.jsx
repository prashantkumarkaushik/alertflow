import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getIncident, updateStatus } from '../api/incidents'
import { StatusBadge, PriorityBadge, SLABadge } from '../components/StatusBadge'

const ACTION_COLORS = {
  'incident.created': 'bg-blue-500',
  'incident.acknowledged': 'bg-yellow-500',
  'incident.resolved': 'bg-green-500',
  'incident.triggered': 'bg-red-500',
  'sla.breached': 'bg-red-600',
  'incident.escalated': 'bg-orange-500',
  'alert.added_to_incident': 'bg-purple-500',
}

export default function IncidentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [incident, setIncident] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchIncident = async () => {
    try {
      const res = await getIncident(id)
      setIncident(res.data)
    } catch (err) {
      setError('Incident not found')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchIncident() }, [id])

  const handleTransition = async (newStatus) => {
    setActionLoading(true)
    setError('')
    try {
      await updateStatus(id, newStatus)
      await fetchIncident()
    } catch (err) {
      setError(err.response?.data?.detail || 'Transition failed')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-gray-400">Loading...</div>
    </div>
  )

  if (error && !incident) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-red-400">{error}</div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* Navbar */}
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate('/incidents')}
          className="text-gray-400 hover:text-white transition-colors text-sm"
        >
          ← Incidents
        </button>
        <span className="text-gray-600">|</span>
        <span className="text-gray-300 font-medium">#{incident.id}</span>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">

        {/* Incident header */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold mb-3">{incident.title}</h2>
              <div className="flex items-center gap-3 flex-wrap">
                <StatusBadge status={incident.status} />
                <PriorityBadge priority={incident.priority} />
                <SLABadge
                  breached={incident.sla_breached}
                  deadline={incident.sla_deadline}
                  status={incident.status}
                />
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 shrink-0">
              {incident.status === 'triggered' && (
                <button
                  onClick={() => handleTransition('acknowledged')}
                  disabled={actionLoading}
                  className="bg-yellow-600 hover:bg-yellow-500 disabled:opacity-50
                             text-white px-4 py-2 rounded-lg text-sm font-medium
                             transition-colors"
                >
                  Acknowledge
                </button>
              )}
              {incident.status !== 'resolved' && (
                <button
                  onClick={() => handleTransition('resolved')}
                  disabled={actionLoading}
                  className="bg-green-600 hover:bg-green-500 disabled:opacity-50
                             text-white px-4 py-2 rounded-lg text-sm font-medium
                             transition-colors"
                >
                  Resolve
                </button>
              )}
              {incident.status === 'resolved' && (
                <button
                  onClick={() => handleTransition('triggered')}
                  disabled={actionLoading}
                  className="bg-red-600 hover:bg-red-500 disabled:opacity-50
                             text-white px-4 py-2 rounded-lg text-sm font-medium
                             transition-colors"
                >
                  Re-open
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="mt-4 bg-red-900/30 border border-red-800 text-red-400
                            rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          {/* Meta */}
          <div className="mt-4 pt-4 border-t border-gray-800 grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-gray-500 mb-1">Created</p>
              <p className="text-sm text-gray-300">
                {new Date(incident.created_at).toLocaleString()}
              </p>
            </div>
            {incident.acknowledged_at && (
              <div>
                <p className="text-xs text-gray-500 mb-1">Acknowledged</p>
                <p className="text-sm text-gray-300">
                  {new Date(incident.acknowledged_at).toLocaleString()}
                </p>
              </div>
            )}
            {incident.resolved_at && (
              <div>
                <p className="text-xs text-gray-500 mb-1">Resolved</p>
                <p className="text-sm text-gray-300">
                  {new Date(incident.resolved_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Alerts */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="font-semibold mb-4 text-gray-200">
            Alerts ({incident.alerts?.length || 0})
          </h3>
          {incident.alerts?.length === 0 ? (
            <p className="text-gray-500 text-sm">No alerts</p>
          ) : (
            <div className="space-y-3">
              {incident.alerts?.map(alert => (
                <div
                  key={alert.id}
                  className="bg-gray-800/50 border border-gray-700/50
                             rounded-lg px-4 py-3"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-white font-medium text-sm">
                        {alert.name}
                      </span>
                      <span className="text-gray-500 text-sm ml-2">
                        via {alert.source}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </div>
                  {alert.message && (
                    <p className="text-gray-400 text-sm mt-1">{alert.message}</p>
                  )}
                  {Object.keys(alert.labels || {}).length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {Object.entries(alert.labels).map(([k, v]) => (
                        <span
                          key={k}
                          className="bg-gray-700 text-gray-300 text-xs
                                     px-2 py-0.5 rounded"
                        >
                          {k}={v}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Audit Timeline */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="font-semibold mb-4 text-gray-200">Audit Timeline</h3>
          <div className="space-y-4">
            {incident.audit_logs?.map((log, i) => (
              <div key={log.id} className="flex gap-4">
                {/* Timeline dot + line */}
                <div className="flex flex-col items-center">
                  <div className={`w-3 h-3 rounded-full mt-1 shrink-0
                                  ${ACTION_COLORS[log.action] || 'bg-gray-500'}`}
                  />
                  {i < incident.audit_logs.length - 1 && (
                    <div className="w-px flex-1 bg-gray-800 mt-1" />
                  )}
                </div>
                {/* Content */}
                <div className="pb-4 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-200">
                      {log.action}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(log.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    by {log.actor}
                  </p>
                  {Object.keys(log.payload || {}).length > 0 && (
                    <div className="mt-2 bg-gray-800/50 rounded px-3 py-2">
                      {Object.entries(log.payload).map(([k, v]) => (
                        v && <p key={k} className="text-xs text-gray-400">
                          <span className="text-gray-500">{k}:</span> {String(v)}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
