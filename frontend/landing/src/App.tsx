import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Landing from './Landing'
import FarmerApp from './farmer/FarmerApp'
import Home from './farmer/screens/Home'
import { Spinner } from './ui/kit'

// Farmers load only their own screens on slow rural networks; the expert
// console and the Leaflet-heavy officials' dashboard are separate chunks.
const Scan = lazy(() => import('./farmer/screens/Scan'))
const Result = lazy(() => import('./farmer/screens/Result'))
const Spray = lazy(() => import('./farmer/screens/Spray'))
const Alerts = lazy(() => import('./farmer/screens/Alerts'))
const History = lazy(() => import('./farmer/screens/History'))
const ProblemDetail = lazy(() => import('./farmer/screens/History').then((m) => ({ default: m.ProblemDetail })))
const ExpertConsole = lazy(() => import('./expert/ExpertConsole'))
const OfficerDashboard = lazy(() => import('./officer/OfficerDashboard'))

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<Spinner />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<FarmerApp />}>
            <Route index element={<Home />} />
            <Route path="scan" element={<Scan />} />
            <Route path="result" element={<Result />} />
            <Route path="spray" element={<Spray />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="history" element={<History />} />
            <Route path="history/:id" element={<ProblemDetail />} />
          </Route>
          <Route path="/expert" element={<ExpertConsole />} />
          <Route path="/officer" element={<OfficerDashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
