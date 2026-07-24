import { Routes, Route, Navigate, useLocation, Link } from 'react-router-dom'
import useAuth from './hooks/useAuth'
import Spinner from './components/common/Spinner'

import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Onboarding from './pages/Onboarding'
import FieldExplorer from './pages/FieldExplorer'
import SpecializationDetail from './pages/SpecializationDetail'
import Profile from './pages/Profile'
import Roadmap from './pages/Roadmap'
import TaskWorkspace from './pages/TaskWorkspace'
import CertificateVerify from './pages/CertificateVerify'

/**
 * Wraps any route that requires a signed-in user.
 * - While the initial /auth/me bootstrap is in flight, shows a spinner
 *   instead of redirecting — otherwise a page refresh on a protected route
 *   would always bounce to /login for a split second, even with a valid token.
 * - Preserves the attempted location in router state so Login can send the
 *   user back to where they were headed after a successful sign-in.
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}

function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-md text-center px-margin">
      <p className="font-heading-xl text-heading-xl">404</p>
      <p className="font-body-md text-body-md text-mute">This page doesn't exist.</p>
      <Link to="/" className="btn-primary">
        Back home
      </Link>
    </div>
  )
}

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/fields" element={<FieldExplorer />} />
      <Route path="/specializations/:id" element={<SpecializationDetail />} />
      <Route path="/certificates/verify/:code" element={<CertificateVerify />} />

      {/* Protected routes */}
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />
      <Route
        path="/roadmap/:spec_id"
        element={
          <ProtectedRoute>
            <Roadmap />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tasks/:task_id"
        element={
          <ProtectedRoute>
            <TaskWorkspace />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}