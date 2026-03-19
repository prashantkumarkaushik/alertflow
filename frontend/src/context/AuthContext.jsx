import react from 'react'
import { getMe } from '../api/auth'

export const AuthContext = react.createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = react.useState(null)
  const [loading, setLoading] = react.useState(true)

  react.useEffect(() => {
    // On app load, check if we have a valid token
    const token = localStorage.getItem('token')
    if (token) {
      getMe()
        .then(res => setUser(res.data))
        .catch(() => localStorage.removeItem('token'))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const loginUser = (token, userData) => {
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ user, loginUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

