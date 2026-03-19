import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

const PRIORITIES = ['P1', 'P2', 'P3', 'P4']
const PRIORITY_COLORS = {
  P1: 'text-red-400', P2: 'text-orange-400',
  P3: 'text-yellow-400', P4: 'text-gray-400'
}

export default function SLAPolicies() {
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    name: '', priority: 'P1', response_minutes: 15, resolution_minutes: 60
  })
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const fetchPolicies = async () => {
    try {
      const res = await client.get('/sla-policies')
      setPolicies(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPolicies() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await client.post('/sla-policies', form)
      setShowForm(false)
      setForm({ name: '', priority: 'P1', response_minutes: 15, resolution_minutes: 60 })
      await fetchPolicies()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create policy')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this SLA policy?')) return
    try {
      await client.delete(`/sla-policies/${id}`)
      await fetchPolicies()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate('/incidents')}
          className="text-gray-400 hover:text-white text-sm transition-colors"
        >
          ← Incidents
        </button>
        <span className="text-gray-600">|</span>
        <span className="font-medium">SLA Policies</span>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">SLA Policies</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2
                       rounded-lg text-sm font-medium transition-colors"
          >
            {showForm ? 'Cancel' : '+ New Policy'}
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
            <h3 className="font-semibold mb-4">New SLA Policy</h3>
            {error && (
              <div className="bg-red-900/30 border border-red-800 text-red-400
                              rounded-lg px-4 py-3 mb-4 text-sm">{error}</div>
            )}
            <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Name</label>
                <input
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="Critical SLA"
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg
                             px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Priority</label>
                <select
                  value={form.priority}
                  onChange={e => setForm({ ...form, priority: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg
                             px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  {PRIORITIES.map(p => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Response (minutes)
                </label>
                <input
                  type="number"
                  value={form.response_minutes}
                  onChange={e => setForm({ ...form, response_minutes: +e.target.value })}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg
                             px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Resolution (minutes)
                </label>
                <input
                  type="number"
                  value={form.resolution_minutes}
                  onChange={e => setForm({ ...form, resolution_minutes: +e.target.value })}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg
                             px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="col-span-2">
                <button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2
                             rounded-lg text-sm font-medium transition-colors"
                >
                  Create Policy
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Policies list */}
        {loading ? (
          <div className="text-gray-400 text-center py-20">Loading...</div>
        ) : policies.length === 0 ? (
          <div className="text-gray-500 text-center py-20">
            No SLA policies yet. Create one to track deadlines.
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase text-left">Name</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase text-left">Priority</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase text-left">Response</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase text-left">Resolution</th>
                  <th className="px-6 py-4 text-xs text-gray-400 font-medium uppercase text-left"></th>
                </tr>
              </thead>
              <tbody>
                {policies.map((policy, i) => (
                  <tr
                    key={policy.id}
                    className={`border-b border-gray-800/50
                                ${i === policies.length - 1 ? 'border-0' : ''}`}
                  >
                    <td className="px-6 py-4 text-white">{policy.name}</td>
                    <td className="px-6 py-4">
                      <span className={`font-bold ${PRIORITY_COLORS[policy.priority]}`}>
                        {policy.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-300">{policy.response_minutes}m</td>
                    <td className="px-6 py-4 text-gray-300">{policy.resolution_minutes}m</td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleDelete(policy.id)}
                        className="text-red-400 hover:text-red-300 text-sm transition-colors"
                      >
                        Delete
                      </button>
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
