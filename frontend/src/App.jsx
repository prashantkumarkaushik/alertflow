import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from "./context/useAuth"
import Login from './pages/Login'
import Incidents from './pages/Incidents'
import IncidentDetail from './pages/IncidentDetail'
import Register from './pages/Register'

function ProtectedRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/incidents" replace /> : <Login />}
      />
      <Route path="/register" element={
        user ? <Navigate to="/incidents" replace /> : <Register />
      } />
      <Route path="/register" element={
        user ? <Navigate to="/incidents" replace /> : <Register />
      } />
      <Route path="/incidents" element={
        <ProtectedRoute><Incidents /></ProtectedRoute>
      } />
      <Route path="/incidents/:id" element={
        <ProtectedRoute><IncidentDetail /></ProtectedRoute>
      } />
      <Route path="*" element={<Navigate to="/incidents" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
