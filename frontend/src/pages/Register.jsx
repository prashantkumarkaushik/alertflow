import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import axios from 'axios'

export default function Register() {
  const [form, setForm] = useState({
    email: '', password: '', full_name: '', team_name: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await axios.post('/api/v1/auth/register', form)
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white">AlertFlow</h1>
          <p className="text-gray-400 mt-2">Incident Management Platform</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Create account</h2>

          {error && (
            <div className="bg-red-900/30 border border-red-800 text-red-400
                            rounded-lg px-4 py-3 mb-4 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {[
              { name: 'full_name', label: 'Full Name', type: 'text', placeholder: 'John Doe' },
              { name: 'email', label: 'Email', type: 'email', placeholder: 'you@company.com' },
              { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
              { name: 'team_name', label: 'Team Name', type: 'text', placeholder: 'Payments Team' },
            ].map(field => (
              <div key={field.name}>
                <label className="block text-sm text-gray-400 mb-1">
                  {field.label}
                </label>
                <input
                  type={field.type}
                  name={field.name}
                  value={form[field.name]}
                  onChange={handleChange}
                  placeholder={field.placeholder}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg
                             px-4 py-2.5 text-white placeholder-gray-500
                             focus:outline-none focus:border-blue-500"
                />
              </div>
            ))}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800
                         text-white font-medium py-2.5 rounded-lg transition-colors"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-400 hover:text-blue-300">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
