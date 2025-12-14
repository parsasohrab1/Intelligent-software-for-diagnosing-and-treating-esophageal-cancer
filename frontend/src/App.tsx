import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import ErrorBoundary from './components/ErrorBoundary'
import Dashboard from './pages/Dashboard'
import Patients from './pages/Patients'
import PatientData from './pages/PatientData'
import MLModels from './pages/MLModels'
import CDS from './pages/CDS'
import MRIDashboard from './pages/MRIDashboard'
import PatientMonitoring from './pages/PatientMonitoring'
import Settings from './pages/Settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
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
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}

export default App

