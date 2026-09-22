import React, { lazy, Suspense } from 'react'
import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import HomePage from './pages/Home'
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'
import TenantRegister from './pages/register/TenantRegister'
import OwnerRegister from './pages/register/OwnerRegister'
import AgentRegister from './pages/register/AgentRegister'
import ProviderRegister from './pages/register/ProviderRegister'
import DashboardPage from './pages/Dashboard'
import PropertiesPage from './pages/Properties'
import BuyPage from './pages/Buy'
import RentPage from './pages/Rent'
import InvestPage from './pages/Invest'
import PropertyDetailsPage from './pages/PropertyDetails'
import PropertyEditPage from './pages/PropertyEdit'
import MainLayout from './layouts/MainLayout'
import AdminLayout from './layouts/AdminLayout'
import ManagerLayout from './layouts/ManagerLayout'
import PublicLayout from './layouts/PublicLayout'
import TenantLayout from './layouts/TenantLayout'
import OwnerLayout from './layouts/OwnerLayout'
import AgentLayout from './layouts/AgentLayout'
import ProviderLayout from './layouts/ProviderLayout'

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
import AdminBuildings from './pages/admin/Buildings'
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
import AdminVerifications from './pages/admin/Verifications'
import AdminAuditLogs from './pages/admin/AuditLogs'

// Manager pages
import ManagerDashboard from './pages/manager/Dashboard'
import ManagerProperties from './pages/manager/Properties'
import ManagerTenants from './pages/manager/Tenants'
import ManagerLeases from './pages/manager/Leases'
import ManagerPayments from './pages/manager/Payments'
import ManagerMaintenance from './pages/manager/Maintenance'
import ManagerUnits from './pages/manager/Units'
import ManagerInquiries from './pages/manager/Inquiries'
import ManagerReports from './pages/manager/Reports'
import ManagerSettings from './pages/manager/Settings'

// Tenant pages
import TenantDashboard from './pages/tenant/Dashboard'
import TenantMyTenancy from './pages/tenant/MyTenancy'
import TenantApplications from './pages/tenant/Applications'
import TenantPayments from './pages/tenant/Payments'
import TenantMaintenance from './pages/tenant/Maintenance'
import TenantMessages from './pages/tenant/Messages'
import TenantDocuments from './pages/tenant/Documents'
import TenantProfile from './pages/tenant/Profile'

// Owner pages
import OwnerDashboard from './pages/owner/Dashboard'
import OwnerProperties from './pages/owner/Properties'
import OwnerUnits from './pages/owner/Units'
import OwnerTenants from './pages/owner/Tenants'
import OwnerLeases from './pages/owner/Leases'
import OwnerFinancials from './pages/owner/Financials'
import OwnerApplications from './pages/owner/Applications'
import OwnerMaintenance from './pages/owner/Maintenance'
import OwnerSettings from './pages/owner/Settings'

// Agent pages
import AgentDashboard from './pages/agent/Dashboard'
import AgentLeadsPipeline from './pages/agent/LeadsPipeline'
import AgentListings from './pages/agent/Listings'
import AgentViewings from './pages/agent/Viewings'
import AgentApplications from './pages/agent/Applications'
import AgentCommissions from './pages/agent/Commissions'
import AgentProfile from './pages/agent/Profile'

// Service Provider pages
import ProviderDashboard from './pages/provider/Dashboard'
import ProviderWorkOrders from './pages/provider/WorkOrders'
import ProviderQuotes from './pages/provider/Quotes'
import ProviderProfile from './pages/provider/Profile'

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
              {/* Public browsing routes */}
              <Route element={<PublicLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/register/tenant" element={<TenantRegister />} />
                <Route path="/register/owner" element={<OwnerRegister />} />
                <Route path="/register/agent" element={<AgentRegister />} />
                <Route path="/register/provider" element={<ProviderRegister />} />
                <Route path="/properties" element={<PropertiesPage />} />
                <Route path="/buy" element={<BuyPage />} />
                <Route path="/rent" element={<RentPage />} />
                <Route path="/invest" element={<InvestPage />} />
                <Route path="/properties/:id" element={<PropertyDetailsPage />} />
                <Route
                  path="/solutions"
                  element={
                    <Suspense fallback={<div className="empty">Loading…</div>}>
                      <Solutions />
                    </Suspense>
                  }
                />
                <Route
                  path="/features"
                  element={
                    <Suspense fallback={<div className="empty">Loading…</div>}>
                      <Features />
                    </Suspense>
                  }
                />
                <Route
                  path="/about"
                  element={
                    <Suspense fallback={<div className="empty">Loading…</div>}>
                      <About />
                    </Suspense>
                  }
                />
                <Route
                  path="/contact"
                  element={
                    <Suspense fallback={<div className="empty">Loading…</div>}>
                      <Contact />
                    </Suspense>
                  }
                />
              </Route>

              {/* Dynamic role dashboard redirection */}
              <Route element={<RequireAuth />}>
                <Route path="/dashboard" element={<RoleRedirect />} />
              </Route>

              {/* Tenant Portal */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['tenant', 'user']} />}>
                  <Route path="/tenant" element={<TenantLayout />}>
                    <Route index element={<TenantDashboard />} />
                    <Route path="dashboard" element={<TenantDashboard />} />
                    <Route path="tenancy" element={<TenantMyTenancy />} />
                    <Route path="applications" element={<TenantApplications />} />
                    <Route path="payments" element={<TenantPayments />} />
                    <Route path="maintenance" element={<TenantMaintenance />} />
                    <Route path="messages" element={<TenantMessages />} />
                    <Route path="documents" element={<TenantDocuments />} />
                    <Route path="profile" element={<TenantProfile />} />
                  </Route>
                </Route>
              </Route>

              {/* Property Owner Portal */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['owner', 'landlord']} />}>
                  <Route path="/owner" element={<OwnerLayout />}>
                    <Route index element={<OwnerDashboard />} />
                    <Route path="dashboard" element={<OwnerDashboard />} />
                    <Route path="properties" element={<OwnerProperties />} />
                    <Route path="units" element={<OwnerUnits />} />
                    <Route path="tenants" element={<OwnerTenants />} />
                    <Route path="leases" element={<OwnerLeases />} />
                    <Route path="financials" element={<OwnerFinancials />} />
                    <Route path="applications" element={<OwnerApplications />} />
                    <Route path="maintenance" element={<OwnerMaintenance />} />
                    <Route path="settings" element={<OwnerSettings />} />
                  </Route>
                </Route>
              </Route>

              {/* Real Estate Agent Workspace */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['agent', 'realtor']} />}>
                  <Route path="/agent" element={<AgentLayout />}>
                    <Route index element={<AgentDashboard />} />
                    <Route path="dashboard" element={<AgentDashboard />} />
                    <Route path="leads" element={<AgentLeadsPipeline />} />
                    <Route path="listings" element={<AgentListings />} />
                    <Route path="viewings" element={<AgentViewings />} />
                    <Route path="applications" element={<AgentApplications />} />
                    <Route path="commissions" element={<AgentCommissions />} />
                    <Route path="profile" element={<AgentProfile />} />
                  </Route>
                </Route>
              </Route>

              {/* Service Provider / Contractor Portal */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['service_provider', 'contractor', 'vendor']} />}>
                  <Route path="/provider" element={<ProviderLayout />}>
                    <Route index element={<ProviderDashboard />} />
                    <Route path="dashboard" element={<ProviderDashboard />} />
                    <Route path="work-orders" element={<ProviderWorkOrders />} />
                    <Route path="quotes" element={<ProviderQuotes />} />
                    <Route path="profile" element={<ProviderProfile />} />
                  </Route>
                </Route>
              </Route>

              {/* Property Manager Portal */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['manager']} />}>
                  <Route path="/manager" element={<ManagerLayout />}>
                    <Route index element={<ManagerDashboard />} />
                    <Route path="dashboard" element={<ManagerDashboard />} />
                    <Route path="properties" element={<ManagerProperties />} />
                    <Route path="tenants" element={<ManagerTenants />} />
                    <Route path="leases" element={<ManagerLeases />} />
                    <Route path="payments" element={<ManagerPayments />} />
                    <Route path="maintenance" element={<ManagerMaintenance />} />
                    <Route path="units" element={<ManagerUnits />} />
                    <Route path="inquiries" element={<ManagerInquiries />} />
                    <Route path="reports" element={<ManagerReports />} />
                    <Route path="settings" element={<ManagerSettings />} />
                  </Route>
                </Route>
              </Route>

              {/* Platform Administrator Portal */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['admin']} />}>
                  <Route path="/admin" element={<AdminLayout />}>
                    <Route index element={<AdminDashboard />} />
                    <Route path="dashboard" element={<AdminDashboard />} />
                    <Route path="users" element={<UsersManagement />} />
                    <Route path="properties" element={<PropertiesManagement />} />
                    <Route path="buildings" element={<AdminBuildings />} />
                    <Route path="units" element={<UnitsManagement />} />
                    <Route path="leases" element={<LeasesManagement />} />
                    <Route path="payments" element={<PaymentsManagement />} />
                    <Route path="maintenance" element={<MaintenanceManagement />} />
                    <Route path="verifications" element={<AdminVerifications />} />
                    <Route path="audit-logs" element={<AdminAuditLogs />} />
                    <Route path="inquiries" element={<InquiriesManagement />} />
                    <Route path="agents" element={<AgentsManagement />} />
                    <Route path="managers" element={<ManagersManagement />} />
                    <Route path="tenants" element={<TenantsManagement />} />
                    <Route path="market-insights" element={<AdminMarketInsights />} />
                    <Route path="settings" element={<AdminSettings />} />
                  </Route>
                </Route>
              </Route>

              {/* Generic App Shell / Legacy User routes */}
              <Route element={<RequireAuth />}>
                <Route element={<RequireRole allowedRoles={['user', 'admin']} />}>
                  <Route path="/app" element={<MainLayout />}>
                    <Route index element={<DashboardPage />} />
                    <Route path="properties/:id/edit" element={<PropertyEditPage />} />
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