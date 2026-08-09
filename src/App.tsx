import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'
import DashboardPage from './pages/Dashboard'
import PropertiesPage from './pages/Properties'
import PropertyDetailsPage from './pages/PropertyDetails'
import PlaceholderPage from './pages/Placeholder'
import MainLayout from './layouts/MainLayout'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { Outlet, Navigate } from 'react-router-dom'

const RequireAuth: React.FC = () => {
  const { user, loading } = useAuth()
  if (loading) return <div className="empty">Checking authentication…</div>
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<RequireAuth />}>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="properties" element={<PropertiesPage />} />
            <Route path="properties/:id" element={<PropertyDetailsPage />} />
            <Route path="units" element={<PlaceholderPage title="Units" />} />
            <Route path="tenants" element={<PlaceholderPage title="Tenants" />} />
            <Route path="leases" element={<PlaceholderPage title="Leases" />} />
            <Route path="payments" element={<PlaceholderPage title="Payments" />} />
            <Route path="maintenance" element={<PlaceholderPage title="Maintenance" />} />
            <Route path="documents" element={<PlaceholderPage title="Documents" />} />
            <Route path="reports" element={<PlaceholderPage title="Reports" />} />
            <Route path="ai" element={<PlaceholderPage title="AI Assistant" />} />
            <Route path="settings" element={<PlaceholderPage title="Settings" />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
