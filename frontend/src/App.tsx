import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Patients from './pages/Patients'
import DataGeneration from './pages/DataGeneration'
import DataCollection from './pages/DataCollection'
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
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/patients" element={<Patients />} />
        <Route path="/data-generation" element={<DataGeneration />} />
        <Route path="/data-collection" element={<DataCollection />} />
        <Route path="/ml-models" element={<MLModels />} />
        <Route path="/cds" element={<CDS />} />
        <Route path="/mri" element={<MRIDashboard />} />
        <Route path="/monitoring" element={<PatientMonitoring />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App

