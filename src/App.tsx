import React, { lazy, Suspense } from 'react'
import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import HomePage from './pages/Home'
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'
import DashboardPage from './pages/Dashboard'
import PropertiesPage from './pages/Properties'
import BuyPage from './pages/Buy'
import RentPage from './pages/Rent'
import InvestPage from './pages/Invest'
import PropertyDetailsPage from './pages/PropertyDetails'
import PropertyEditPage from './pages/PropertyEdit'
import PlaceholderPage from './pages/Placeholder'
import MainLayout from './layouts/MainLayout'
import AdminLayout from './layouts/AdminLayout'
import PublicLayout from './layouts/PublicLayout'
const Solutions = lazy(() => import('./pages/Solutions'))
const Features = lazy(() => import('./pages/Features'))
const About = lazy(() => import('./pages/About'))
const Contact = lazy(() => import('./pages/Contact'))
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { FavoriteProvider } from './contexts/FavoriteContext'
import ErrorBoundary from './components/ErrorBoundary'
import ToastProvider from './components/ToastProvider'
import type { UserRole } from './types'
// Admin pages
import AdminDashboard from './pages/admin/Dashboard'
import UsersManagement from './pages/admin/Users'
import PropertiesManagement from './pages/admin/Properties'
import InquiriesManagement from './pages/admin/Inquiries'
import AgentsManagement from './pages/admin/Agents'
import ManagersManagement from './pages/admin/Managers'
import TenantsManagement from './pages/admin/Tenants'
import AdminMarketInsights from './pages/admin/MarketInsights'
import AdminSettings from './pages/admin/Settings'
import UnitsManagement from './pages/admin/Units'
import LeasesManagement from './pages/admin/Leases'
import PaymentsManagement from './pages/admin/Payments'
import MaintenanceManagement from './pages/admin/Maintenance'

const RequireAuth: React.FC = () => {
  const { user, loading } = useAuth()
  if (loading) return <div className="empty">Checking authentication…</div>
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}

const RequireRole: React.FC<{ allowedRoles: UserRole[] }> = ({ allowedRoles }) => {
  const { user, loading, hasAnyRole, getDashboardPath } = useAuth()
  
  if (loading) return <div className="empty">Checking permissions…</div>
  if (!user) return <Navigate to="/login" replace />
  if (!hasAnyRole(allowedRoles)) {
    // Redirect to appropriate dashboard based on user's role
    return <Navigate to={getDashboardPath()} replace />
  }
  return <Outlet />
}

const RoleRedirect: React.FC = () => {
  const { user, loading, getDashboardPath } = useAuth()
  
  if (loading) return <div className="empty">Redirecting to your dashboard…</div>
  if (!user) return <Navigate to="/login" replace />
  
  return <Navigate to={getDashboardPath()} replace />
}

const App: React.FC = () => {
  return (
    <AuthProvider>
      <FavoriteProvider>
        <ErrorBoundary>
          <ToastProvider>
            <Routes>
              {/* Public — anyone can browse, no login required */}
              <Route element={<PublicLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/properties" element={<PropertiesPage />} />
                <Route path="/buy" element={<BuyPage />} />
                <Route path="/rent" element={<RentPage />} />
                <Route path="/invest" element={<InvestPage />} />
                <Route path="/properties/:id" element={<PropertyDetailsPage />} />
                <Route path="/solutions" element={<Suspense fallback={<div className="empty">Loading…</div>}><Solutions /></Suspense>} />
                <Route path="/features" element={<Suspense fallback={<div className="empty">Loading…</div>}><Features /></Suspense>} />
                <Route path="/about" element={<Suspense fallback={<div className="empty">Loading…</div>}><About /></Suspense>} />
                <Route path="/contact" element={<Suspense fallback={<div className="empty">Loading…</div>}><Contact /></Suspense>} />
              </Route>

              {/* Role-based redirect for authenticated users */}
              <Route element={<RequireAuth />}>
                <Route path="/dashboard" element={<RoleRedirect />} />
              </Route>

              {/* User Portal */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['user']} />}>
                  <Route path="/app" element={<MainLayout />}>
                    <Route index element={<DashboardPage />} />
                    <Route path="properties/:id/edit" element={<PropertyEditPage />} />
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
              </Route>

              {/* Admin Portal - Phase 2 implementation */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['admin']} />}>
                  <Route path="/admin" element={<AdminLayout />}>
                    <Route path="dashboard" element={<AdminDashboard />} />
                    <Route path="users" element={<UsersManagement />} />
                    <Route path="properties" element={<PropertiesManagement />} />
                    <Route path="units" element={<UnitsManagement />} />
                    <Route path="leases" element={<LeasesManagement />} />
                    <Route path="payments" element={<PaymentsManagement />} />
                    <Route path="maintenance" element={<MaintenanceManagement />} />
                    <Route path="inquiries" element={<InquiriesManagement />} />
                    <Route path="agents" element={<AgentsManagement />} />
                    <Route path="managers" element={<ManagersManagement />} />
                    <Route path="tenants" element={<TenantsManagement />} />
                    <Route path="market-insights" element={<AdminMarketInsights />} />
                    <Route path="settings" element={<AdminSettings />} />
                  </Route>
                </Route>
              </Route>

              {/* Manager Portal - Future implementation */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['manager']} />}>
                  <Route path="/manager" element={<MainLayout />}>
                    <Route path="dashboard" element={<PlaceholderPage title="Manager Dashboard" />} />
                    <Route path="properties" element={<PlaceholderPage title="Properties" />} />
                    <Route path="properties/new" element={<PlaceholderPage title="New Property" />} />
                    <Route path="tenants" element={<PlaceholderPage title="Tenants" />} />
                    <Route path="leases" element={<PlaceholderPage title="Leases" />} />
                    <Route path="inquiries" element={<PlaceholderPage title="Inquiries" />} />
                    <Route path="maintenance" element={<PlaceholderPage title="Maintenance" />} />
                    <Route path="payments" element={<PlaceholderPage title="Payments" />} />
                    <Route path="profile" element={<PlaceholderPage title="Profile" />} />
                  </Route>
                </Route>
              </Route>

              {/* Agent Portal - Future implementation */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['agent']} />}>
                  <Route path="/agent" element={<MainLayout />}>
                    <Route path="dashboard" element={<PlaceholderPage title="Agent Dashboard" />} />
                    <Route path="properties" element={<PlaceholderPage title="Properties" />} />
                    <Route path="properties/new" element={<PlaceholderPage title="New Property" />} />
                    <Route path="inquiries" element={<PlaceholderPage title="Inquiries" />} />
                    <Route path="leads" element={<PlaceholderPage title="Leads" />} />
                    <Route path="clients" element={<PlaceholderPage title="Clients" />} />
                    <Route path="appointments" element={<PlaceholderPage title="Appointments" />} />
                    <Route path="profile" element={<PlaceholderPage title="Profile" />} />
                  </Route>
                </Route>
              </Route>

              {/* Tenant Portal - Future implementation */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['tenant']} />}>
                  <Route path="/tenant" element={<MainLayout />}>
                    <Route path="dashboard" element={<PlaceholderPage title="Tenant Dashboard" />} />
                    <Route path="property" element={<PlaceholderPage title="My Property" />} />
                    <Route path="lease" element={<PlaceholderPage title="My Lease" />} />
                    <Route path="payments" element={<PlaceholderPage title="Payments" />} />
                    <Route path="maintenance" element={<PlaceholderPage title="Maintenance Requests" />} />
                    <Route path="messages" element={<PlaceholderPage title="Messages" />} />
                    <Route path="profile" element={<PlaceholderPage title="Profile" />} />
                  </Route>
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ToastProvider>
        </ErrorBoundary>
      </FavoriteProvider>
    </AuthProvider>
  )
}

export default App