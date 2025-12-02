import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
} from '@mui/material'
import {
  MonitorHeart as MonitorIcon,
  LocalHospital as HospitalIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material'
import api from '../services/api'

interface MonitoringParameter {
  name: string
  value: number | null
  unit: string
  normal_range: {
    min: number
    max: number
    unit: string
  }
  status: 'normal' | 'abnormal' | 'critical' | 'missing'
  last_updated: string | null
  trend: string | null
}

interface PatientMonitoring {
  patient_id: string
  patient_name: string | null
  age: number | null
  gender: string | null
  has_cancer: boolean
  monitoring_date: string
  vital_signs: MonitoringParameter[]
  lab_results: MonitoringParameter[]
  clinical_parameters: MonitoringParameter[]
  imaging_results: MonitoringParameter[]
  overall_status: 'stable' | 'monitoring_required' | 'intervention_needed' | 'critical'
  alerts: string[]
}

export default function PatientMonitoring() {
  const [selectedPatient, setSelectedPatient] = useState<string>('')
  const [patients, setPatients] = useState<Array<{patient_id: string, name: string | null}>>([])
  const [monitoring, setMonitoring] = useState<PatientMonitoring | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tabValue, setTabValue] = useState(0)

  useEffect(() => {
    loadPatients()
  }, [])

  useEffect(() => {
    if (selectedPatient) {
      loadMonitoring(selectedPatient)
    }
  }, [selectedPatient])

  const loadPatients = async () => {
    try {
      const response = await api.get('/patients?limit=100')
      setPatients(response.data)
      if (response.data.length > 0 && !selectedPatient) {
        setSelectedPatient(response.data[0].patient_id)
      }
    } catch (err: any) {
      setError('Failed to load patients')
    }
  }

  const loadMonitoring = async (patientId: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(`/monitoring/patients/${patientId}/monitoring`)
      setMonitoring(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load monitoring data')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'success'
      case 'abnormal':
        return 'warning'
      case 'critical':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'normal':
        return <CheckCircleIcon color="success" />
      case 'abnormal':
        return <WarningIcon color="warning" />
      case 'critical':
        return <ErrorIcon color="error" />
      default:
        return null
    }
  }

  const renderParameterTable = (parameters: MonitoringParameter[], title: string) => {
    if (parameters.length === 0) {
      return (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>{title}</Typography>
            <Typography color="text.secondary">No data available</Typography>
          </CardContent>
        </Card>
      )
    }

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>{title}</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Parameter</strong></TableCell>
                  <TableCell><strong>Value</strong></TableCell>
                  <TableCell><strong>Normal Range</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Last Updated</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {parameters.map((param, index) => (
                  <TableRow key={index}>
                    <TableCell>{param.name}</TableCell>
                    <TableCell>
                      {param.value !== null ? (
                        <Typography variant="body1" fontWeight="bold">
                          {param.value.toFixed(2)} {param.unit}
                        </Typography>
                      ) : (
                        <Typography color="text.secondary">N/A</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {param.normal_range.min !== undefined && param.normal_range.max !== undefined ? (
                        <Typography variant="body2" color="text.secondary">
                          {param.normal_range.min} - {param.normal_range.max} {param.normal_range.unit}
                        </Typography>
                      ) : param.normal_range.min !== undefined ? (
                        <Typography variant="body2" color="text.secondary">
                          &gt; {param.normal_range.min} {param.normal_range.unit}
                        </Typography>
                      ) : param.normal_range.max !== undefined ? (
                        <Typography variant="body2" color="text.secondary">
                          &lt; {param.normal_range.max} {param.normal_range.unit}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          {param.normal_range.note || 'See reference'}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(param.status)}
                        label={param.status.toUpperCase()}
                        color={getStatusColor(param.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {param.last_updated ? (
                        <Typography variant="body2">
                          {new Date(param.last_updated).toLocaleDateString()}
                        </Typography>
                      ) : (
                        <Typography color="text.secondary">N/A</Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    )
  }

  if (loading && !monitoring) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box p={3}>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          <MonitorIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Patient Monitoring Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor vital signs, lab results, clinical parameters, and imaging data with normal ranges
        </Typography>
      </Box>

      {/* Patient Selection */}
      <Box mb={3}>
        <FormControl fullWidth sx={{ maxWidth: 400 }}>
          <InputLabel>Select Patient</InputLabel>
          <Select
            value={selectedPatient}
            onChange={(e) => setSelectedPatient(e.target.value)}
            label="Select Patient"
          >
            {patients.map((patient) => (
              <MenuItem key={patient.patient_id} value={patient.patient_id}>
                {patient.patient_id} - {patient.name || 'Unknown'}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {monitoring && (
        <>
          {/* Overall Status */}
          <Box mb={3}>
            <Card>
              <CardContent>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Patient: {monitoring.patient_name || monitoring.patient_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Age: {monitoring.age || 'N/A'} | Gender: {monitoring.gender || 'N/A'} | 
                      Cancer Status: {monitoring.has_cancer ? 'Yes' : 'No'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Box display="flex" justifyContent="flex-end" alignItems="center" gap={2}>
                      <Typography variant="body1">
                        Overall Status:
                      </Typography>
                      <Chip
                        icon={getStatusIcon(monitoring.overall_status)}
                        label={monitoring.overall_status.replace('_', ' ').toUpperCase()}
                        color={getStatusColor(monitoring.overall_status) as any}
                        size="medium"
                      />
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Box>

          {/* Alerts */}
          {monitoring.alerts.length > 0 && (
            <Box mb={3}>
              <Alert severity={monitoring.overall_status === 'critical' ? 'error' : 'warning'}>
                <Typography variant="h6" gutterBottom>Alerts</Typography>
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {monitoring.alerts.map((alert, index) => (
                    <li key={index}>{alert}</li>
                  ))}
                </ul>
              </Alert>
            </Box>
          )}

          {/* Tabs for different parameter categories */}
          <Box mb={3}>
            <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
              <Tab label="Vital Signs" />
              <Tab label="Lab Results" />
              <Tab label="Clinical Parameters" />
              <Tab label="Imaging Results" />
            </Tabs>
          </Box>

          {/* Tab Content */}
          <Box>
            {tabValue === 0 && renderParameterTable(monitoring.vital_signs, 'Vital Signs')}
            {tabValue === 1 && renderParameterTable(monitoring.lab_results, 'Laboratory Results')}
            {tabValue === 2 && renderParameterTable(monitoring.clinical_parameters, 'Clinical Parameters')}
            {tabValue === 3 && renderParameterTable(monitoring.imaging_results, 'Imaging Results')}
          </Box>
        </>
      )}

      {!monitoring && !loading && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <MonitorIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No monitoring data available
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Select a patient to view monitoring data
          </Typography>
        </Paper>
      )}
    </Box>
  )
}

