import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { CircularProgress, Box } from '@mui/material'
import Layout from './components/Layout'
import ErrorBoundary from './components/ErrorBoundary'

// Code splitting: lazy load route components to reduce initial bundle
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Patients = lazy(() => import('./pages/Patients'))
const PatientData = lazy(() => import('./pages/PatientData'))
const MLModels = lazy(() => import('./pages/MLModels'))
const CDS = lazy(() => import('./pages/CDS'))
const MRIDashboard = lazy(() => import('./pages/MRIDashboard'))
const PatientMonitoring = lazy(() => import('./pages/PatientMonitoring'))
const SurgicalGuidance = lazy(() => import('./pages/SurgicalGuidance'))
const TreatmentResponse = lazy(() => import('./pages/TreatmentResponse'))
const Training = lazy(() => import('./pages/Training'))
const Compliance = lazy(() => import('./pages/Compliance'))
const ClinicalWorkflow = lazy(() => import('./pages/ClinicalWorkflow'))
const Settings = lazy(() => import('./pages/Settings'))

function RouteFallback() {
  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight={280} p={3}>
      <CircularProgress />
    </Box>
  )
}

function App() {
  return (
    <Layout>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<Navigate to="/workflow" replace />} />
          <Route path="/login" element={<Navigate to="/workflow" replace />} />
          <Route path="/workflow" element={<ClinicalWorkflow />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/patient-data" element={<PatientData />} />
          <Route path="/data-generation" element={<Navigate to="/patient-data" replace />} />
          <Route path="/data-collection" element={<Navigate to="/patient-data" replace />} />
          <Route path="/ml-models" element={<MLModels />} />
          <Route path="/cds" element={
            <ErrorBoundary>
              <CDS />
            </ErrorBoundary>
          } />
          <Route path="/mri" element={<MRIDashboard />} />
          <Route path="/monitoring" element={<PatientMonitoring />} />
          <Route path="/surgical-guidance" element={<SurgicalGuidance />} />
          <Route path="/treatment-response" element={<TreatmentResponse />} />
          <Route path="/training" element={<Training />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </Layout>
  )
}

export default App

