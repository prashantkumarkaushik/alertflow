import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getIncidents } from '../api/incidents'
import { useAuth } from '../context/useAuth'
import { StatusBadge, PriorityBadge, SLABadge } from '../components/StatusBadge'

export default function Incidents() {
  const [incidents, setIncidents] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const fetchIncidents = async () => {
    setLoading(true)
    try {
      const params = {}
      if (statusFilter) params.status = statusFilter
      const res = await getIncidents(params)
      setIncidents(res.data.items)
      setTotal(res.data.total)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIncidents()
  }, [statusFilter])

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* Navbar */}
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center
                      justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-white">AlertFlow</h1>
          <span className="text-gray-600">|</span>
          <span className="text-gray-400 text-sm">{user?.email} {user?.team}</span>
        </div>
        <button
          onClick={logout}
          className="text-gray-400 hover:text-white text-sm transition-colors"
        >
          Sign out
        </button>
      </nav>

      {/* Main */}
      <div className="max-w-6xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Incidents</h2>
            <p className="text-gray-400 text-sm mt-1">{total} total</p>
          </div>

          {/* Filter */}
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white rounded-lg
                       px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="">All statuses</option>
            <option value="triggered">Triggered</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        {/* Table */}
        {loading ? (
          <div className="text-gray-400 text-center py-20">Loading...</div>
        ) : incidents.length === 0 ? (
          <div className="text-gray-500 text-center py-20">
            No incidents found
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800 text-left">
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase">ID</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase">Title</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase">Priority</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase">Status</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase">SLA</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase">Created</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((inc, i) => (
                  <tr
                    key={inc.id}
                    onClick={() => navigate(`/incidents/${inc.id}`)}
                    className={`border-b border-gray-800/50 hover:bg-gray-800/50
                                cursor-pointer transition-colors
                                ${i === incidents.length - 1 ? 'border-0' : ''}`}
                  >
                    <td className="px-6 py-4 text-gray-400 text-sm">#{inc.id}</td>
                    <td className="px-6 py-4">
                      <span className="text-white font-medium">{inc.title}</span>
                    </td>
                    <td className="px-6 py-4">
                      <PriorityBadge priority={inc.priority} />
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={inc.status} />
                    </td>
                    <td className="px-6 py-4">
                      <SLABadge
                        breached={inc.sla_breached}
                        deadline={inc.sla_deadline}
                        status={inc.status}
                      />
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm">
                      {new Date(inc.created_at).toLocaleString()}
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
