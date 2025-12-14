import { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  Divider,
  Paper,
  Tabs,
  Tab,
} from '@mui/material'
import {
  LocalHospital as HospitalIcon,
  Science as ScienceIcon,
  Assessment as AssessmentIcon,
  Visibility as VisibilityIcon,
  Description as DescriptionIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import api from '../services/api'
import SHAPVisualization from '../components/SHAPVisualization'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area,
} from 'recharts'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`cds-tabpanel-${index}`}
      aria-labelledby={`cds-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

interface Patient {
  patient_id: string
  age: number
  gender: string
  has_cancer?: boolean
  cancer_type?: string
  bmi?: number
  [key: string]: any
}

interface CDSService {
  name: string
  id: string
  description: string
  endpoint: string
}

export default function CDS() {
  const [activeStep, setActiveStep] = useState(0)
  const [tabValue, setTabValue] = useState(0)
  
  // Data fetching states
  const [patients, setPatients] = useState<Patient[]>([])
  const [cdsServices, setCdsServices] = useState<CDSService[]>([])
  const [loadingPatients, setLoadingPatients] = useState(false)
  const [loadingServices, setLoadingServices] = useState(false)
  const [selectedPatientId, setSelectedPatientId] = useState<string>('')
  
  // Patient data for graphs (1-4 patients)
  const [graphPatients, setGraphPatients] = useState<Patient[]>([])
  const [loadingGraphPatients, setLoadingGraphPatients] = useState(false)
  
  // Component mount error state
  const [componentError, setComponentError] = useState<string | null>(null)
  
  const [patientData, setPatientData] = useState({
    age: 65,
    gender: 'Male',
    smoking: false,
    alcohol: false,
    gerd: false,
    bmi: 28,
    barretts_esophagus: false,
    family_history: false,
  })

  const [cancerData, setCancerData] = useState({
    t_stage: 'T2',
    n_stage: 'N0',
    m_stage: 'M0',
    pdl1_status: 'Unknown',
    histological_grade: 'G2',
    tumor_location: 'Middle',
    tumor_length_cm: 3.5,
  })

  const [riskResult, setRiskResult] = useState<any>(null)
  const [treatmentResult, setTreatmentResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPatients = useCallback(async () => {
    setLoadingPatients(true)
    try {
      console.log('CDS: Fetching patients from /patients/...')
      const response = await api.get('/patients/', {
        params: { limit: 50 }, // Reduced limit for better performance
        timeout: 60000, // 60 seconds timeout (increased for reliability)
      })
      console.log('CDS: Patients API response:', response.data)
      
      // Handle different response formats
      let patientsData: Patient[] = []
      if (response.data) {
        if (Array.isArray(response.data)) {
          patientsData = response.data
        } else if (response.data.patients && Array.isArray(response.data.patients)) {
          patientsData = response.data.patients
        } else if (response.data.data && Array.isArray(response.data.data)) {
          patientsData = response.data.data
        }
      }
      
      console.log('CDS: Extracted patients:', patientsData.length)
      setPatients(patientsData)
      setSelectedPatientId((prev) => {
        if (patientsData.length > 0 && !prev) {
          return patientsData[0].patient_id
        }
        return prev
      })
    } catch (error: any) {
      console.error('CDS: Error fetching patients:', error)
      console.error('CDS: Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
      
      // Handle 401 (Unauthorized) differently - show informative message
      if (error.response?.status === 401) {
        setError('Patient data requires authentication. You can still use CDS features by entering patient information manually below.')
      } else {
        setError('Failed to load patients. Please check backend connection.')
      }
      setPatients([])
    } finally {
      setLoadingPatients(false)
    }
  }, [])

  const fetchCDSServices = useCallback(async () => {
    setLoadingServices(true)
    try {
      console.log('CDS: Fetching services from /cds/services...')
      const response = await api.get('/cds/services', {
        timeout: 30000, // 30 seconds timeout (increased for reliability)
      })
      console.log('CDS: Services API response:', response.data)
      
      // Handle different response formats
      let services: CDSService[] = []
      if (response.data) {
        if (Array.isArray(response.data)) {
          services = response.data
        } else if (response.data.services && Array.isArray(response.data.services)) {
          services = response.data.services
        } else if (response.data.data && Array.isArray(response.data.data)) {
          services = response.data.data
        }
      }
      
      console.log('CDS: Extracted services:', services)
      setCdsServices(services)
      
      // If no services from API, use defaults
      if (services.length === 0) {
        console.warn('CDS: No services from API, using defaults')
        const defaultServices: CDSService[] = [
          {
            name: 'Risk Prediction',
            id: 'risk-prediction',
            description: 'Predict risk of esophageal cancer development',
            endpoint: '/cds/risk-prediction'
          },
          {
            name: 'Treatment Recommendation',
            id: 'treatment-recommendation',
            description: 'Recommend treatment based on patient characteristics',
            endpoint: '/cds/treatment-recommendation'
          },
          {
            name: 'Prognostic Scoring',
            id: 'prognostic-score',
            description: 'Calculate prognostic score for patient',
            endpoint: '/cds/prognostic-score'
          },
          {
            name: 'Nanosystem Design',
            id: 'nanosystem-design',
            description: 'Suggest personalized nanosystem design',
            endpoint: '/cds/nanosystem-design'
          },
          {
            name: 'Clinical Trial Matching',
            id: 'clinical-trial-match',
            description: 'Match patient to clinical trials',
            endpoint: '/cds/clinical-trial-match'
          },
          {
            name: 'Monitoring Alerts',
            id: 'monitoring-alerts',
            description: 'Check for monitoring alerts',
            endpoint: '/cds/monitoring-alerts'
          }
        ]
        setCdsServices(defaultServices)
      }
    } catch (error: any) {
      console.error('CDS: Error fetching CDS services:', error)
      console.error('CDS: Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
      
      // Set default services if API fails (offline mode)
      const defaultServices: CDSService[] = [
        {
          name: 'Risk Prediction',
          id: 'risk-prediction',
          description: 'Predict risk of esophageal cancer development',
          endpoint: '/cds/risk-prediction'
        },
        {
          name: 'Treatment Recommendation',
          id: 'treatment-recommendation',
          description: 'Recommend treatment based on patient characteristics',
          endpoint: '/cds/treatment-recommendation'
        },
        {
          name: 'Prognostic Scoring',
          id: 'prognostic-score',
          description: 'Calculate prognostic score for patient',
          endpoint: '/cds/prognostic-score'
        },
        {
          name: 'Nanosystem Design',
          id: 'nanosystem-design',
          description: 'Suggest personalized nanosystem design',
          endpoint: '/cds/nanosystem-design'
        },
        {
          name: 'Clinical Trial Matching',
          id: 'clinical-trial-match',
          description: 'Match patient to clinical trials',
          endpoint: '/cds/clinical-trial-match'
        },
        {
          name: 'Monitoring Alerts',
          id: 'monitoring-alerts',
          description: 'Check for monitoring alerts',
          endpoint: '/cds/monitoring-alerts'
        }
      ]
      setCdsServices(defaultServices)
    } finally {
      setLoadingServices(false)
    }
  }, [])

  const fetchGraphPatients = useCallback(async () => {
    setLoadingGraphPatients(true)
    try {
      const response = await api.get('/patients/', {
        params: { limit: 4 },
        timeout: 60000, // 60 seconds timeout
      })
      const patientsData = Array.isArray(response.data) ? response.data : []
      // Take first 1-4 patients
      setGraphPatients(patientsData.slice(0, 4))
    } catch (error: any) {
      console.error('Error fetching graph patients:', error)
      setGraphPatients([])
    } finally {
      setLoadingGraphPatients(false)
    }
  }, [])

  const loadPatientData = useCallback(async (patientId: string) => {
    try {
      const patient = patients.find((p) => p.patient_id === patientId)
      if (patient) {
        setPatientData((prev) => ({
          ...prev,
          age: patient.age || 65,
          gender: patient.gender || 'Male',
        }))
      }
    } catch (error) {
      console.error('Error loading patient data:', error)
    }
  }, [patients])

  // Fetch patients and CDS services on mount
  useEffect(() => {
    let isMounted = true
    
    const initialize = async () => {
      try {
        console.log('CDS: Initializing component...')
        if (isMounted) {
          // Use Promise.allSettled to ensure both calls complete even if one fails
          const results = await Promise.allSettled([
            fetchPatients().catch(err => {
              console.error('CDS: fetchPatients failed:', err)
              return null
            }),
            fetchCDSServices().catch(err => {
              console.error('CDS: fetchCDSServices failed:', err)
              return null
            })
          ])
          console.log('CDS: Initialization complete', results)
          
          // Check if both failed
          const allFailed = results.every(r => r.status === 'rejected')
          if (allFailed && isMounted) {
            console.warn('CDS: All initialization requests failed, but continuing anyway')
            // Don't set componentError - let it show default/fallback data
          }
        }
      } catch (error: any) {
        console.error('CDS: Error initializing component:', error)
        // Don't set componentError for initialization errors - let the component render with defaults
        // Only set error if it's a critical error that prevents rendering
      }
    }
    
    // Wrap in try-catch to prevent any unhandled errors
    try {
      initialize()
    } catch (error) {
      console.error('CDS: Fatal error during initialization:', error)
    }
    
    return () => {
      isMounted = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Load patient data when selected
  useEffect(() => {
    if (selectedPatientId) {
      loadPatientData(selectedPatientId)
    }
  }, [selectedPatientId, loadPatientData])

  // Debug: Log state changes
  useEffect(() => {
    console.log('CDS: State update -', {
      cdsServicesCount: cdsServices.length,
      patientsCount: patients.length,
      loadingServices,
      loadingPatients,
      selectedPatientId
    })
  }, [cdsServices, patients, loadingServices, loadingPatients, selectedPatientId])

  // Fetch 1-4 patients for graph display when Basic Patient Information step is active
  useEffect(() => {
    if (activeStep === 0) {
      fetchGraphPatients()
    }
  }, [activeStep, fetchGraphPatients])

  const steps = [
    {
      label: 'Basic Patient Information',
      description: 'Age, gender, and primary indicators',
    },
    {
      label: 'Risk Factors',
      description: 'Smoking, alcohol, GERD, and other factors',
    },
    {
      label: 'Tumor Information',
      description: 'Stage, grade, and tumor characteristics',
    },
    {
      label: 'Prediction and Recommendation',
      description: 'View results and recommendations',
    },
  ]

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1)
  }

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1)
  }

  const handleRiskPrediction = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post('/cds/risk-prediction', {
        patient_data: patientData,
        include_explanation: true,
      }, {
        timeout: 60000,
      })
      setRiskResult(response.data)
      setActiveStep(3)
    } catch (error: any) {
      console.error('Error predicting risk:', error)
      setError(error.response?.data?.detail || 'Failed to predict risk. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleTreatmentRecommendation = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post('/cds/treatment-recommendation', {
        patient_data: patientData,
        cancer_data: cancerData,
      }, {
        timeout: 60000,
      })
      setTreatmentResult(response.data)
    } catch (error: any) {
      console.error('Error getting recommendations:', error)
      setError(error.response?.data?.detail || 'Failed to get treatment recommendations. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ width: '100%', minHeight: '100vh', p: 3 }}>
      {/* Show error message if there's a critical error, but don't block rendering */}
      {componentError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setComponentError(null)}>
          <Typography variant="h6">Error Loading Clinical Decision Support</Typography>
          <Typography>{componentError}</Typography>
          <Button 
            onClick={() => {
              setComponentError(null)
              // Retry initialization instead of reloading
              fetchPatients()
              fetchCDSServices()
            }} 
            sx={{ mt: 1 }}
            size="small"
            variant="outlined"
          >
            Retry
          </Button>
        </Alert>
      )}
      
      <Typography variant="h4" gutterBottom>
        Clinical Decision Support
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        This system helps you receive risk assessments and treatment recommendations based on patient information
      </Typography>

      {/* Status Summary */}
      <Card sx={{ mb: 3, bgcolor: 'background.default' }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                CDS Services
              </Typography>
              <Typography variant="h6">
                {loadingServices ? 'Loading...' : `${cdsServices.length} available`}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Patients
              </Typography>
              <Typography variant="h6">
                {loadingPatients ? 'Loading...' : `${patients.length} available`}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Selected Patient
              </Typography>
              <Typography variant="h6">
                {selectedPatientId || 'None'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* CDS Services Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Available CDS Services {cdsServices.length > 0 && `(${cdsServices.length})`}
            </Typography>
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={fetchCDSServices}
              disabled={loadingServices}
            >
              Refresh
            </Button>
          </Box>
          {loadingServices ? (
            <Box display="flex" justifyContent="center" p={2}>
              <CircularProgress />
              <Typography variant="body2" sx={{ ml: 2 }}>
                Loading services...
              </Typography>
            </Box>
          ) : cdsServices.length > 0 ? (
            <Grid container spacing={2}>
              {cdsServices.map((service) => (
                <Grid item xs={12} sm={6} md={4} key={service.id}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        {service.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {service.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="warning">
              <Typography variant="body2">
                No CDS services available. Please check backend connection.
              </Typography>
              <Button 
                size="small" 
                onClick={fetchCDSServices} 
                sx={{ mt: 1 }}
                variant="outlined"
              >
                Retry
              </Button>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Patient Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Select Patient</Typography>
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={fetchPatients}
              disabled={loadingPatients}
            >
              Refresh
            </Button>
          </Box>
          {loadingPatients ? (
            <Box display="flex" justifyContent="center" p={2}>
              <CircularProgress />
              <Typography variant="body2" sx={{ ml: 2 }}>
                Loading patients...
              </Typography>
            </Box>
          ) : patients.length > 0 ? (
            <FormControl fullWidth>
              <InputLabel>Select Patient ({patients.length} available)</InputLabel>
              <Select
                value={selectedPatientId}
                onChange={(e) => setSelectedPatientId(e.target.value)}
              >
                {patients.map((patient) => (
                  <MenuItem key={patient.patient_id} value={patient.patient_id}>
                    {patient.patient_id} - {patient.gender}, Age {patient.age}
                    {patient.has_cancer && ` (${patient.cancer_type || 'Cancer'})`}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          ) : (
            <Alert severity="info">
              <Typography variant="body2">
                {error && error.includes('authentication') 
                  ? 'Patient data requires authentication. You can still use CDS features by entering patient information manually in the Clinical Workflow tab below.'
                  : 'No patients found. Go to Patient Data page to generate or import patient data, or enter patient information manually below.'}
              </Typography>
              {!error?.includes('authentication') && (
                <Button 
                  size="small" 
                  onClick={fetchPatients} 
                  sx={{ mt: 1 }}
                  variant="outlined"
                >
                  Retry
                </Button>
              )}
            </Alert>
          )}
        </CardContent>
      </Card>

      {error && !error.includes('authentication') && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {error && error.includes('authentication') && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <Typography variant="body2">
            {error}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            The CDS system can still provide risk predictions and treatment recommendations using manually entered patient data.
          </Typography>
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab icon={<AssessmentIcon />} label="Clinical Workflow" />
        <Tab icon={<VisibilityIcon />} label="Sandbox Mode" />
        <Tab icon={<DescriptionIcon />} label="Clinical Decision Report" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 3 }}>
          <Stepper activeStep={activeStep} orientation="vertical">
            <Step>
              <StepLabel>{steps[0].label}</StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {steps[0].description}
                </Typography>
                
                {/* Input Fields */}
                <Grid container spacing={2} sx={{ mb: 4 }}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Age"
                      type="number"
                      value={patientData.age}
                      onChange={(e) =>
                        setPatientData({ ...patientData, age: parseInt(e.target.value) || 0 })
                      }
                      inputProps={{ min: 0, max: 120 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>Gender</InputLabel>
                      <Select
                        value={patientData.gender}
                        onChange={(e) =>
                          setPatientData({ ...patientData, gender: e.target.value })
                        }
                      >
                        <MenuItem value="Male">Male</MenuItem>
                        <MenuItem value="Female">Female</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="BMI"
                      type="number"
                      value={patientData.bmi}
                      onChange={(e) =>
                        setPatientData({ ...patientData, bmi: parseFloat(e.target.value) || 0 })
                      }
                      inputProps={{ min: 10, max: 50, step: 0.1 }}
                    />
                  </Grid>
                </Grid>

                <Divider sx={{ my: 3 }} />

                {/* Patient Data Graphs */}
                <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
                  Patient Data Visualization (1-4 Patients)
                </Typography>
                
                {loadingGraphPatients ? (
                  <Box display="flex" justifyContent="center" sx={{ py: 4 }}>
                    <CircularProgress />
                  </Box>
                ) : graphPatients.length > 0 ? (
                  <Grid container spacing={3} sx={{ mb: 3 }}>
                    {/* Graph 1: Age Comparison */}
                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Age Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={graphPatients.map((p, idx) => ({
                              patient: `P${idx + 1}`,
                              age: p.age || 0,
                            }))}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="patient" />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="age" fill="#1976d2" />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Graph 2: Gender Distribution */}
                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Gender Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                              <Pie
                                data={(() => {
                                  const genderCount = graphPatients.reduce((acc, p) => {
                                    const gender = p.gender || 'Unknown'
                                    acc[gender] = (acc[gender] || 0) + 1
                                    return acc
                                  }, {} as Record<string, number>)
                                  return Object.entries(genderCount).map(([name, value]) => ({
                                    name,
                                    value,
                                  }))
                                })()}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                              >
                                {(() => {
                                  const genderCount = graphPatients.reduce((acc, p) => {
                                    const gender = p.gender || 'Unknown'
                                    acc[gender] = (acc[gender] || 0) + 1
                                    return acc
                                  }, {} as Record<string, number>)
                                  const colors = ['#1976d2', '#dc004e', '#9c27b0', '#ff9800']
                                  return Object.keys(genderCount).map((_, index) => (
                                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                  ))
                                })()}
                              </Pie>
                              <Tooltip />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Graph 3: BMI Comparison (if available) */}
                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            BMI Comparison
                          </Typography>
                          <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={graphPatients.map((p, idx) => ({
                              patient: `P${idx + 1}`,
                              bmi: (p as any).bmi || patientData.bmi || 0,
                            }))}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="patient" />
                              <YAxis domain={[0, 50]} />
                              <Tooltip />
                              <Bar dataKey="bmi" fill="#ff9800" />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Graph 4: Cancer Status */}
                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Cancer Status Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={250}>
                            <PieChart>
                              <Pie
                                data={(() => {
                                  const cancerCount = graphPatients.reduce((acc, p) => {
                                    const status = p.has_cancer ? 'Has Cancer' : 'No Cancer'
                                    acc[status] = (acc[status] || 0) + 1
                                    return acc
                                  }, {} as Record<string, number>)
                                  return Object.entries(cancerCount).map(([name, value]) => ({
                                    name,
                                    value,
                                  }))
                                })()}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                              >
                                {(() => {
                                  const cancerCount = graphPatients.reduce((acc, p) => {
                                    const status = p.has_cancer ? 'Has Cancer' : 'No Cancer'
                                    acc[status] = (acc[status] || 0) + 1
                                    return acc
                                  }, {} as Record<string, number>)
                                  return Object.keys(cancerCount).map((name, index) => (
                                    <Cell 
                                      key={`cell-${index}`} 
                                      fill={name === 'Has Cancer' ? '#dc004e' : '#4caf50'} 
                                    />
                                  ))
                                })()}
                              </Pie>
                              <Tooltip />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                ) : (
                  <Alert severity="info" sx={{ mb: 3 }}>
                    <Typography variant="body2">
                      No patient data available for visualization. 
                      {patients.length === 0 && error?.includes('authentication') 
                        ? ' Patient data requires authentication. You can still use the CDS features by entering patient information manually.'
                        : ' Generate or import patient data first, or enter patient information manually below.'}
                    </Typography>
                  </Alert>
                )}

                <Box sx={{ mt: 2 }}>
                  <Button variant="contained" onClick={handleNext}>
                    Next
                  </Button>
                </Box>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>{steps[1].label}</StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {steps[1].description}
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={4}>
                    <Button
                      fullWidth
                      variant={patientData.smoking ? 'contained' : 'outlined'}
                      color={patientData.smoking ? 'error' : 'primary'}
                      onClick={() =>
                        setPatientData({ ...patientData, smoking: !patientData.smoking })
                      }
                    >
                      Smoking: {patientData.smoking ? 'Yes' : 'No'}
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Button
                      fullWidth
                      variant={patientData.alcohol ? 'contained' : 'outlined'}
                      color={patientData.alcohol ? 'error' : 'primary'}
                      onClick={() =>
                        setPatientData({ ...patientData, alcohol: !patientData.alcohol })
                      }
                    >
                      Alcohol: {patientData.alcohol ? 'Yes' : 'No'}
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Button
                      fullWidth
                      variant={patientData.gerd ? 'contained' : 'outlined'}
                      color={patientData.gerd ? 'warning' : 'primary'}
                      onClick={() =>
                        setPatientData({ ...patientData, gerd: !patientData.gerd })
                      }
                    >
                      GERD: {patientData.gerd ? 'Yes' : 'No'}
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Button
                      fullWidth
                      variant={patientData.barretts_esophagus ? 'contained' : 'outlined'}
                      color={patientData.barretts_esophagus ? 'error' : 'primary'}
                      onClick={() =>
                        setPatientData({ ...patientData, barretts_esophagus: !patientData.barretts_esophagus })
                      }
                    >
                      Barrett's Esophagus: {patientData.barretts_esophagus ? 'Yes' : 'No'}
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Button
                      fullWidth
                      variant={patientData.family_history ? 'contained' : 'outlined'}
                      color={patientData.family_history ? 'warning' : 'primary'}
                      onClick={() =>
                        setPatientData({ ...patientData, family_history: !patientData.family_history })
                      }
                    >
                      Family History: {patientData.family_history ? 'Yes' : 'No'}
                    </Button>
                  </Grid>
                </Grid>
                <Box sx={{ mt: 2 }}>
                  <Button onClick={handleBack} sx={{ mr: 1 }}>
                    Back
                  </Button>
                  <Button variant="contained" onClick={handleNext}>
                    Next
                  </Button>
                </Box>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>{steps[2].label}</StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {steps[2].description}
                </Typography>
                
                {/* Tumor Information Input */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>T Stage</InputLabel>
                      <Select
                        value={cancerData.t_stage}
                        onChange={(e) =>
                          setCancerData({ ...cancerData, t_stage: e.target.value })
                        }
                      >
                        <MenuItem value="T0">T0</MenuItem>
                        <MenuItem value="T1">T1</MenuItem>
                        <MenuItem value="T2">T2</MenuItem>
                        <MenuItem value="T3">T3</MenuItem>
                        <MenuItem value="T4">T4</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>N Stage</InputLabel>
                      <Select
                        value={cancerData.n_stage}
                        onChange={(e) =>
                          setCancerData({ ...cancerData, n_stage: e.target.value })
                        }
                      >
                        <MenuItem value="N0">N0</MenuItem>
                        <MenuItem value="N1">N1</MenuItem>
                        <MenuItem value="N2">N2</MenuItem>
                        <MenuItem value="N3">N3</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>M Stage</InputLabel>
                      <Select
                        value={cancerData.m_stage}
                        onChange={(e) =>
                          setCancerData({ ...cancerData, m_stage: e.target.value })
                        }
                      >
                        <MenuItem value="M0">M0</MenuItem>
                        <MenuItem value="M1">M1</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Tumor Length (cm)"
                      type="number"
                      value={cancerData.tumor_length_cm}
                      onChange={(e) =>
                        setCancerData({ ...cancerData, tumor_length_cm: parseFloat(e.target.value) || 0 })
                      }
                      inputProps={{ min: 0, max: 20, step: 0.1 }}
                    />
                  </Grid>
                </Grid>

                {/* Tumor Information Visualization */}
                <Divider sx={{ my: 3 }} />
                <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
                  Tumor Information Visualization
                </Typography>
                <Grid container spacing={3} sx={{ mb: 3 }}>
                  {/* TNM Staging Bar Chart */}
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          TNM Staging
                        </Typography>
                        <ResponsiveContainer width="100%" height={250}>
                          <BarChart
                            data={[
                              { 
                                stage: 'T Stage', 
                                value: parseInt(cancerData.t_stage?.replace('T', '') || '0'),
                                max: 4,
                              },
                              { 
                                stage: 'N Stage', 
                                value: parseInt(cancerData.n_stage?.replace('N', '') || '0'),
                                max: 3,
                              },
                              { 
                                stage: 'M Stage', 
                                value: parseInt(cancerData.m_stage?.replace('M', '') || '0'),
                                max: 1,
                              },
                            ]}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="stage" />
                            <YAxis domain={[0, 4]} />
                            <Tooltip />
                            <Bar dataKey="value" fill="#1976d2" />
                            <Bar dataKey="max" fill="#e0e0e0" opacity={0.3} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Tumor Size Visualization */}
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Tumor Size (cm)
                        </Typography>
                        <ResponsiveContainer width="100%" height={250}>
                          <BarChart
                            data={[{
                              name: 'Tumor Length',
                              value: cancerData.tumor_length_cm || 0,
                              max: 20,
                            }]}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis domain={[0, 20]} />
                            <Tooltip />
                            <Bar dataKey="value" fill="#d32f2f" />
                            <Bar dataKey="max" fill="#e0e0e0" opacity={0.2} />
                          </BarChart>
                        </ResponsiveContainer>
                        <Box sx={{ mt: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="primary">
                            {cancerData.tumor_length_cm || 0} cm
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {cancerData.tumor_length_cm > 5 ? 'Large Tumor' : 
                             cancerData.tumor_length_cm > 3 ? 'Medium Tumor' : 'Small Tumor'}
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Stage Distribution Pie Chart */}
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Overall Stage Distribution
                        </Typography>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={[{
                                name: `T${cancerData.t_stage?.replace('T', '') || '0'}`,
                                value: parseInt(cancerData.t_stage?.replace('T', '') || '0'),
                              }, {
                                name: `N${cancerData.n_stage?.replace('N', '') || '0'}`,
                                value: parseInt(cancerData.n_stage?.replace('N', '') || '0'),
                              }, {
                                name: `M${cancerData.m_stage?.replace('M', '') || '0'}`,
                                value: parseInt(cancerData.m_stage?.replace('M', '') || '0'),
                              }]}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, value }) => `${name}: ${value}`}
                              outerRadius={100}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {[0, 1, 2].map((_, index) => {
                                const colors = ['#1976d2', '#dc004e', '#ff9800']
                                return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                              })}
                            </Pie>
                            <Tooltip />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 2 }}>
                  <Button onClick={handleBack} sx={{ mr: 1 }}>
                    Back
                  </Button>
                  <Button variant="contained" onClick={handleNext}>
                    Next
                  </Button>
                </Box>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>{steps[3].label}</StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {steps[3].description}
                </Typography>
                <Box display="flex" gap={2} sx={{ mb: 3 }}>
                  <Button
                    variant="contained"
                    startIcon={<HospitalIcon />}
                    onClick={handleRiskPrediction}
                    disabled={loading}
                  >
                    Predict Risk
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<ScienceIcon />}
                    onClick={handleTreatmentRecommendation}
                    disabled={loading}
                  >
                    Get Treatment Recommendations
                  </Button>
                </Box>

                {loading && (
                  <Box display="flex" justifyContent="center" sx={{ my: 3 }}>
                    <CircularProgress />
                  </Box>
                )}

                {riskResult && (
                  <Box sx={{ mt: 3 }}>
                    <Alert 
                      severity={
                        riskResult.risk_category === 'Very High' || riskResult.risk_category === 'High' 
                          ? 'error' 
                          : riskResult.risk_category === 'Moderate'
                          ? 'warning'
                          : 'info'
                      }
                      sx={{ mb: 3 }}
                    >
                      <Typography variant="h6">
                        Risk Score: {riskResult.risk_score} ({riskResult.risk_category})
                      </Typography>
                      <Typography>{riskResult.recommendation}</Typography>
                    </Alert>

                    {/* Prediction and Recommendation Visualization */}
                    <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
                      Prediction and Recommendation Analysis
                    </Typography>
                    <Grid container spacing={3} sx={{ mb: 3 }}>
                      {/* Risk Score Gauge */}
                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardContent>
                            <Typography variant="h6" gutterBottom>
                              Risk Score Visualization
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                              <BarChart
                                data={[{
                                  category: riskResult.risk_category,
                                  score: (riskResult.risk_score || 0) * 100,
                                  max: 100,
                                }]}
                                layout="vertical"
                              >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis type="number" domain={[0, 100]} />
                                <YAxis dataKey="category" type="category" width={120} />
                                <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                                <Bar dataKey="score" fill={
                                  riskResult.risk_category === 'Very High' || riskResult.risk_category === 'High'
                                    ? '#d32f2f'
                                    : riskResult.risk_category === 'Moderate'
                                    ? '#f57c00'
                                    : '#388e3c'
                                } />
                                <Bar dataKey="max" fill="#e0e0e0" opacity={0.2} />
                              </BarChart>
                            </ResponsiveContainer>
                            <Box sx={{ mt: 2, textAlign: 'center' }}>
                              <Typography variant="h3" color={
                                riskResult.risk_category === 'Very High' || riskResult.risk_category === 'High'
                                  ? 'error'
                                  : riskResult.risk_category === 'Moderate'
                                  ? 'warning'
                                  : 'success'
                              }>
                                {(riskResult.risk_score || 0) * 100}%
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {riskResult.risk_category} Risk
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>

                      {/* Risk Factors Contribution */}
                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardContent>
                            <Typography variant="h6" gutterBottom>
                              Risk Factors Contribution
                            </Typography>
                            {riskResult.factors && riskResult.factors.length > 0 ? (
                              <ResponsiveContainer width="100%" height={300}>
                                <BarChart
                                  data={riskResult.factors
                                    .sort((a: any, b: any) => b.contribution - a.contribution)
                                    .slice(0, 5)
                                    .map((factor: any) => ({
                                      name: factor.factor.replace('_', ' '),
                                      contribution: (factor.contribution || 0) * 100,
                                    }))}
                                  layout="vertical"
                                >
                                  <CartesianGrid strokeDasharray="3 3" />
                                  <XAxis type="number" domain={[0, 100]} />
                                  <YAxis dataKey="name" type="category" width={120} />
                                  <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                                  <Bar dataKey="contribution" fill="#1976d2" />
                                </BarChart>
                              </ResponsiveContainer>
                            ) : (
                              <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Typography color="text.secondary">No factor data available</Typography>
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>

                      {/* Risk Trend Over Time (Simulated) */}
                      <Grid item xs={12}>
                        <Card>
                          <CardContent>
                            <Typography variant="h6" gutterBottom>
                              Risk Progression Timeline
                            </Typography>
                            <ResponsiveContainer width="100%" height={250}>
                              <AreaChart
                                data={[
                                  { time: 'Baseline', risk: 0 },
                                  { time: 'Current', risk: (riskResult.risk_score || 0) * 100 },
                                  { time: 'Projected', risk: Math.min(100, (riskResult.risk_score || 0) * 100 * 1.2) },
                                ]}
                              >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis domain={[0, 100]} />
                                <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                                <Area
                                  type="monotone"
                                  dataKey="risk"
                                  stroke="#1976d2"
                                  fill="#1976d2"
                                  fillOpacity={0.6}
                                />
                              </AreaChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>

                    {riskResult.shap_explanation && (
                      <Box sx={{ mt: 3 }}>
                        <SHAPVisualization
                          explanation={riskResult}
                          prediction={riskResult.risk_score}
                          riskCategory={riskResult.risk_category}
                        />
                      </Box>
                    )}
                  </Box>
                )}

                {treatmentResult && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Treatment Recommendations
                    </Typography>
                    
                    {/* Treatment Recommendations Visualization */}
                    <Grid container spacing={3} sx={{ mb: 3 }}>
                      {/* Treatment Types Distribution */}
                      {treatmentResult.recommendations && treatmentResult.recommendations.length > 0 && (
                        <Grid item xs={12} md={6}>
                          <Card>
                            <CardContent>
                              <Typography variant="h6" gutterBottom>
                                Treatment Types Distribution
                              </Typography>
                              <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                  <Pie
                                    data={(() => {
                                      const typeCount = treatmentResult.recommendations.reduce((acc: any, rec: any) => {
                                        const type = rec.type || 'Unknown'
                                        acc[type] = (acc[type] || 0) + 1
                                        return acc
                                      }, {})
                                      return Object.entries(typeCount).map(([name, value]) => ({
                                        name,
                                        value,
                                      }))
                                    })()}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    dataKey="value"
                                  >
                                    {treatmentResult.recommendations.map((_: any, index: number) => {
                                      const colors = ['#1976d2', '#dc004e', '#ff9800', '#388e3c', '#7b1fa2']
                                      return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                    })}
                                  </Pie>
                                  <Tooltip />
                                  <Legend />
                                </PieChart>
                              </ResponsiveContainer>
                            </CardContent>
                          </Card>
                        </Grid>
                      )}

                      {/* Treatment Priority Chart */}
                      {treatmentResult.recommendations && treatmentResult.recommendations.length > 0 && (
                        <Grid item xs={12} md={6}>
                          <Card>
                            <CardContent>
                              <Typography variant="h6" gutterBottom>
                                Treatment Priority Ranking
                              </Typography>
                              <ResponsiveContainer width="100%" height={300}>
                                <BarChart
                                  data={treatmentResult.recommendations
                                    .slice(0, 5)
                                    .map((rec: any, idx: number) => ({
                                      name: rec.type || `Treatment ${idx + 1}`,
                                      priority: 5 - idx,
                                    }))}
                                  layout="vertical"
                                >
                                  <CartesianGrid strokeDasharray="3 3" />
                                  <XAxis type="number" domain={[0, 5]} />
                                  <YAxis dataKey="name" type="category" width={120} />
                                  <Tooltip />
                                  <Bar dataKey="priority" fill="#388e3c" />
                                </BarChart>
                              </ResponsiveContainer>
                            </CardContent>
                          </Card>
                        </Grid>
                      )}
                    </Grid>

                    {/* Treatment Recommendations List */}
                    {treatmentResult.recommendations?.slice(0, 5).map((rec: any, idx: number) => (
                      <Card key={idx} sx={{ mt: 1 }}>
                        <CardContent>
                          <Typography variant="subtitle1">
                            {rec.type}: {rec.regimen}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {rec.rationale}
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}

                <Box sx={{ mt: 2 }}>
                  <Button onClick={handleBack} sx={{ mr: 1 }}>
                    Back
                  </Button>
                  <Button variant="outlined" onClick={() => setActiveStep(0)}>
                    Restart
                  </Button>
                </Box>
              </StepContent>
            </Step>
          </Stepper>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <SandboxMode 
          patientData={patientData}
          setPatientData={setPatientData}
          cancerData={cancerData}
          setCancerData={setCancerData}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <ClinicalDecisionReport 
          patientData={patientData}
          cancerData={cancerData}
          riskResult={riskResult}
          treatmentResult={treatmentResult}
        />
      </TabPanel>
    </Box>
  )
}

// Sandbox Mode Component
function SandboxMode({ 
  patientData, 
  setPatientData, 
  cancerData, 
  setCancerData 
}: {
  patientData: any
  setPatientData: any
  cancerData: any
  setCancerData: any
}) {
  const [riskResult, setRiskResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [autoUpdate, setAutoUpdate] = useState(false)

  const handleRiskPrediction = useCallback(async () => {
    setLoading(true)
    try {
      const response = await api.post('/cds/risk-prediction', {
        patient_data: patientData,
        include_explanation: true,
      }, {
        timeout: 60000,
      })
      setRiskResult(response.data)
    } catch (error: any) {
      console.error('Error predicting risk:', error)
    } finally {
      setLoading(false)
    }
  }, [patientData])

  useEffect(() => {
    if (autoUpdate && !loading) {
      const timer = setTimeout(() => {
        handleRiskPrediction()
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [patientData, cancerData, autoUpdate, handleRiskPrediction, loading])

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Sandbox Mode
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        In this environment, you can change various patient parameters and observe their impact on risk prediction
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Button
          variant={autoUpdate ? 'contained' : 'outlined'}
          onClick={() => setAutoUpdate(!autoUpdate)}
          sx={{ mb: 2 }}
        >
          {autoUpdate ? 'Disable Auto-Update' : 'Enable Auto-Update'}
        </Button>
        {!autoUpdate && (
          <Button variant="contained" onClick={handleRiskPrediction} disabled={loading} sx={{ ml: 2 }}>
            {loading ? 'Calculating Risk...' : 'Calculate Risk'}
          </Button>
        )}
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Patient Information
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Age"
                    type="number"
                    value={patientData.age}
                    onChange={(e) =>
                      setPatientData({ ...patientData, age: parseInt(e.target.value) || 0 })
                    }
                    inputProps={{ min: 0, max: 120 }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Gender</InputLabel>
                    <Select
                      value={patientData.gender}
                      onChange={(e) =>
                        setPatientData({ ...patientData, gender: e.target.value })
                      }
                    >
                      <MenuItem value="Male">Male</MenuItem>
                      <MenuItem value="Female">Female</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="BMI"
                    type="number"
                    value={patientData.bmi}
                    onChange={(e) =>
                      setPatientData({ ...patientData, bmi: parseFloat(e.target.value) || 0 })
                    }
                    inputProps={{ min: 10, max: 50, step: 0.1 }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    <Chip
                      label={`Smoking: ${patientData.smoking ? 'Yes' : 'No'}`}
                      color={patientData.smoking ? 'error' : 'default'}
                      onClick={() =>
                        setPatientData({ ...patientData, smoking: !patientData.smoking })
                      }
                    />
                    <Chip
                      label={`Alcohol: ${patientData.alcohol ? 'Yes' : 'No'}`}
                      color={patientData.alcohol ? 'error' : 'default'}
                      onClick={() =>
                        setPatientData({ ...patientData, alcohol: !patientData.alcohol })
                      }
                    />
                    <Chip
                      label={`GERD: ${patientData.gerd ? 'Yes' : 'No'}`}
                      color={patientData.gerd ? 'warning' : 'default'}
                      onClick={() =>
                        setPatientData({ ...patientData, gerd: !patientData.gerd })
                      }
                    />
                    <Chip
                      label={`Barrett's: ${patientData.barretts_esophagus ? 'Yes' : 'No'}`}
                      color={patientData.barretts_esophagus ? 'error' : 'default'}
                      onClick={() =>
                        setPatientData({ ...patientData, barretts_esophagus: !patientData.barretts_esophagus })
                      }
                    />
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tumor Information
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>T Stage</InputLabel>
                    <Select
                      value={cancerData.t_stage}
                      onChange={(e) =>
                        setCancerData({ ...cancerData, t_stage: e.target.value })
                      }
                    >
                      <MenuItem value="T0">T0</MenuItem>
                      <MenuItem value="T1">T1</MenuItem>
                      <MenuItem value="T2">T2</MenuItem>
                      <MenuItem value="T3">T3</MenuItem>
                      <MenuItem value="T4">T4</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>N Stage</InputLabel>
                    <Select
                      value={cancerData.n_stage}
                      onChange={(e) =>
                        setCancerData({ ...cancerData, n_stage: e.target.value })
                      }
                    >
                      <MenuItem value="N0">N0</MenuItem>
                      <MenuItem value="N1">N1</MenuItem>
                      <MenuItem value="N2">N2</MenuItem>
                      <MenuItem value="N3">N3</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>M Stage</InputLabel>
                    <Select
                      value={cancerData.m_stage}
                      onChange={(e) =>
                        setCancerData({ ...cancerData, m_stage: e.target.value })
                      }
                    >
                      <MenuItem value="M0">M0</MenuItem>
                      <MenuItem value="M1">M1</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Tumor Length (cm)"
                    type="number"
                    value={cancerData.tumor_length_cm}
                    onChange={(e) =>
                      setCancerData({ ...cancerData, tumor_length_cm: parseFloat(e.target.value) || 0 })
                    }
                    inputProps={{ min: 0, max: 20, step: 0.1 }}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {loading && (
          <Grid item xs={12}>
            <Box display="flex" justifyContent="center">
              <CircularProgress />
            </Box>
          </Grid>
        )}

        {riskResult && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Alert 
                  severity={
                    riskResult.risk_category === 'Very High' || riskResult.risk_category === 'High' 
                      ? 'error' 
                      : riskResult.risk_category === 'Moderate'
                      ? 'warning'
                      : 'info'
                  }
                  sx={{ mb: 2 }}
                >
                  <Typography variant="h6">
                    Risk Score: {riskResult.risk_score} ({riskResult.risk_category})
                  </Typography>
                  <Typography>{riskResult.recommendation}</Typography>
                </Alert>

                {riskResult.shap_explanation && (
                  <SHAPVisualization
                    explanation={riskResult}
                    prediction={riskResult.risk_score}
                    riskCategory={riskResult.risk_category}
                  />
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Paper>
  )
}

// Clinical Decision Report Component
function ClinicalDecisionReport({
  patientData,
  cancerData,
  riskResult,
  treatmentResult,
}: {
  patientData: any
  cancerData: any
  riskResult: any
  treatmentResult: any
}) {
  const [reportData, setReportData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (riskResult || treatmentResult) {
      generateReport()
    }
  }, [riskResult, treatmentResult])

  const generateReport = () => {
    const report = {
      generatedAt: new Date().toLocaleString(),
      patientInfo: {
        age: patientData.age,
        gender: patientData.gender,
        bmi: patientData.bmi,
        riskFactors: {
          smoking: patientData.smoking ? 'Yes' : 'No',
          alcohol: patientData.alcohol ? 'Yes' : 'No',
          gerd: patientData.gerd ? 'Yes' : 'No',
          barretts_esophagus: patientData.barretts_esophagus ? 'Yes' : 'No',
          family_history: patientData.family_history ? 'Yes' : 'No',
        },
      },
      cancerInfo: {
        t_stage: cancerData.t_stage,
        n_stage: cancerData.n_stage,
        m_stage: cancerData.m_stage,
        tumor_length_cm: cancerData.tumor_length_cm,
        histological_grade: cancerData.histological_grade,
        tumor_location: cancerData.tumor_location,
      },
      riskAssessment: riskResult ? {
        risk_score: riskResult.risk_score,
        risk_category: riskResult.risk_category,
        recommendation: riskResult.recommendation,
      } : null,
      treatmentRecommendations: treatmentResult ? {
        recommendations: treatmentResult.recommendations || [],
      } : null,
    }
    setReportData(report)
  }

  const handleGenerateFullReport = async () => {
    setLoading(true)
    try {
      const [riskRes, treatmentRes] = await Promise.allSettled([
        api.post('/cds/risk-prediction', {
          patient_data: patientData,
          include_explanation: true,
        }, { timeout: 60000 }),
        api.post('/cds/treatment-recommendation', {
          patient_data: patientData,
          cancer_data: cancerData,
        }, { timeout: 60000 }),
      ])

      const report = {
        generatedAt: new Date().toLocaleString(),
        patientInfo: {
          age: patientData.age,
          gender: patientData.gender,
          bmi: patientData.bmi,
          riskFactors: {
            smoking: patientData.smoking ? 'Yes' : 'No',
            alcohol: patientData.alcohol ? 'Yes' : 'No',
            gerd: patientData.gerd ? 'Yes' : 'No',
            barretts_esophagus: patientData.barretts_esophagus ? 'Yes' : 'No',
            family_history: patientData.family_history ? 'Yes' : 'No',
          },
        },
        cancerInfo: {
          t_stage: cancerData.t_stage,
          n_stage: cancerData.n_stage,
          m_stage: cancerData.m_stage,
          tumor_length_cm: cancerData.tumor_length_cm,
          histological_grade: cancerData.histological_grade,
          tumor_location: cancerData.tumor_location,
        },
        riskAssessment: riskRes.status === 'fulfilled' ? {
          risk_score: riskRes.value.data.risk_score,
          risk_category: riskRes.value.data.risk_category,
          recommendation: riskRes.value.data.recommendation,
        } : null,
        treatmentRecommendations: treatmentRes.status === 'fulfilled' ? {
          recommendations: treatmentRes.value.data.recommendations || [],
        } : null,
      }
      setReportData(report)
    } catch (error) {
      console.error('Error generating report:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" gutterBottom>
          Clinical Decision Report
        </Typography>
        <Button
          variant="contained"
          onClick={handleGenerateFullReport}
          disabled={loading}
          startIcon={<DescriptionIcon />}
        >
          {loading ? 'Generating Report...' : 'Generate Full Report'}
        </Button>
      </Box>

      {loading && (
        <Box display="flex" justifyContent="center" sx={{ my: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {reportData ? (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Patient Information
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Age:</Typography>
                    <Typography variant="body1">{reportData.patientInfo.age} years</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Gender:</Typography>
                    <Typography variant="body1">{reportData.patientInfo.gender}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">BMI:</Typography>
                    <Typography variant="body1">{reportData.patientInfo.bmi}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Risk Factors:
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      <Chip
                        label={`Smoking: ${reportData.patientInfo.riskFactors.smoking}`}
                        color={patientData.smoking ? 'error' : 'default'}
                        size="small"
                      />
                      <Chip
                        label={`Alcohol: ${reportData.patientInfo.riskFactors.alcohol}`}
                        color={patientData.alcohol ? 'error' : 'default'}
                        size="small"
                      />
                      <Chip
                        label={`GERD: ${reportData.patientInfo.riskFactors.gerd}`}
                        color={patientData.gerd ? 'warning' : 'default'}
                        size="small"
                      />
                      <Chip
                        label={`Barrett's: ${reportData.patientInfo.riskFactors.barretts_esophagus}`}
                        color={patientData.barretts_esophagus ? 'error' : 'default'}
                        size="small"
                      />
                      <Chip
                        label={`Family History: ${reportData.patientInfo.riskFactors.family_history}`}
                        color={patientData.family_history ? 'warning' : 'default'}
                        size="small"
                      />
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Tumor Information
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {/* Tumor Information Text */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">T Stage:</Typography>
                    <Typography variant="body1" fontWeight="bold">{reportData.cancerInfo.t_stage}</Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">N Stage:</Typography>
                    <Typography variant="body1" fontWeight="bold">{reportData.cancerInfo.n_stage}</Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">M Stage:</Typography>
                    <Typography variant="body1" fontWeight="bold">{reportData.cancerInfo.m_stage}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Tumor Length:</Typography>
                    <Typography variant="body1" fontWeight="bold">{reportData.cancerInfo.tumor_length_cm} cm</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Grade:</Typography>
                    <Typography variant="body1" fontWeight="bold">{reportData.cancerInfo.histological_grade}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">Location:</Typography>
                    <Typography variant="body1" fontWeight="bold">{reportData.cancerInfo.tumor_location}</Typography>
                  </Grid>
                </Grid>

                {/* Tumor Information Visualization */}
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Tumor Staging Visualization
                </Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart
                    data={[
                      { 
                        stage: 'T Stage', 
                        value: parseInt(reportData.cancerInfo.t_stage?.replace('T', '') || '0'),
                        max: 4,
                      },
                      { 
                        stage: 'N Stage', 
                        value: parseInt(reportData.cancerInfo.n_stage?.replace('N', '') || '0'),
                        max: 3,
                      },
                      { 
                        stage: 'M Stage', 
                        value: parseInt(reportData.cancerInfo.m_stage?.replace('M', '') || '0'),
                        max: 1,
                      },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="stage" />
                    <YAxis domain={[0, 4]} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#1976d2" />
                    <Bar dataKey="max" fill="#e0e0e0" opacity={0.3} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          {reportData.riskAssessment && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Risk Assessment & Prediction
                  </Typography>
                  <Divider sx={{ mb: 3 }} />
                  
                  <Grid container spacing={3}>
                    {/* Risk Score Visualization */}
                    <Grid item xs={12} md={6}>
                      <Alert
                        severity={
                          reportData.riskAssessment.risk_category === 'Very High' ||
                          reportData.riskAssessment.risk_category === 'High'
                            ? 'error'
                            : reportData.riskAssessment.risk_category === 'Moderate'
                            ? 'warning'
                            : 'info'
                        }
                        sx={{ mb: 2 }}
                      >
                        <Typography variant="h6">
                          Risk Score: {(reportData.riskAssessment.risk_score || 0) * 100}%
                        </Typography>
                        <Typography variant="subtitle1">
                          Category: {reportData.riskAssessment.risk_category}
                        </Typography>
                      </Alert>
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart
                          data={[{
                            category: reportData.riskAssessment.risk_category,
                            score: (reportData.riskAssessment.risk_score || 0) * 100,
                            max: 100,
                          }]}
                          layout="vertical"
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" domain={[0, 100]} />
                          <YAxis dataKey="category" type="category" width={120} />
                          <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                          <Bar dataKey="score" fill={
                            reportData.riskAssessment.risk_category === 'Very High' ||
                            reportData.riskAssessment.risk_category === 'High'
                              ? '#d32f2f'
                              : reportData.riskAssessment.risk_category === 'Moderate'
                              ? '#f57c00'
                              : '#388e3c'
                          } />
                          <Bar dataKey="max" fill="#e0e0e0" opacity={0.2} />
                        </BarChart>
                      </ResponsiveContainer>
                    </Grid>

                    {/* Risk Factors Chart */}
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Risk Factors Summary
                      </Typography>
                      <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                          <Pie
                            data={(() => {
                              const factors = [
                                { name: 'Active Risk Factors', value: [
                                  reportData.patientInfo.riskFactors.smoking === 'Yes',
                                  reportData.patientInfo.riskFactors.alcohol === 'Yes',
                                  reportData.patientInfo.riskFactors.gerd === 'Yes',
                                  reportData.patientInfo.riskFactors.barretts_esophagus === 'Yes',
                                  reportData.patientInfo.riskFactors.family_history === 'Yes',
                                ].filter(Boolean).length },
                                { name: 'No Risk Factors', value: [
                                  reportData.patientInfo.riskFactors.smoking === 'Yes',
                                  reportData.patientInfo.riskFactors.alcohol === 'Yes',
                                  reportData.patientInfo.riskFactors.gerd === 'Yes',
                                  reportData.patientInfo.riskFactors.barretts_esophagus === 'Yes',
                                  reportData.patientInfo.riskFactors.family_history === 'Yes',
                                ].filter(Boolean).length === 0 ? 1 : 0 },
                              ].filter(item => item.value > 0)
                              return factors.length > 0 ? factors : [{ name: 'No Data', value: 1 }]
                            })()}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {[0, 1].map((_, index) => {
                              const activeCount = [
                                reportData.patientInfo.riskFactors.smoking === 'Yes',
                                reportData.patientInfo.riskFactors.alcohol === 'Yes',
                                reportData.patientInfo.riskFactors.gerd === 'Yes',
                                reportData.patientInfo.riskFactors.barretts_esophagus === 'Yes',
                                reportData.patientInfo.riskFactors.family_history === 'Yes',
                              ].filter(Boolean).length
                              const colors = activeCount > 0 ? ['#d32f2f', '#4caf50'] : ['#9e9e9e']
                              return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                            })}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </Grid>
                  </Grid>

                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    {reportData.riskAssessment.recommendation}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}

          {reportData.treatmentRecommendations && reportData.treatmentRecommendations.recommendations && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Treatment Recommendations
                  </Typography>
                  <Divider sx={{ mb: 3 }} />
                  
                  {/* Treatment Recommendations Visualization */}
                  <Grid container spacing={3} sx={{ mb: 3 }}>
                    {/* Treatment Types Distribution */}
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Treatment Types Distribution
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={(() => {
                              const typeCount = reportData.treatmentRecommendations.recommendations.reduce((acc: any, rec: any) => {
                                const type = rec.type || 'Unknown'
                                acc[type] = (acc[type] || 0) + 1
                                return acc
                              }, {})
                              return Object.entries(typeCount).map(([name, value]) => ({
                                name,
                                value,
                              }))
                            })()}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                            outerRadius={100}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {reportData.treatmentRecommendations.recommendations.map((_: any, index: number) => {
                              const colors = ['#1976d2', '#dc004e', '#ff9800', '#388e3c', '#7b1fa2']
                              return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                            })}
                          </Pie>
                          <Tooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </Grid>

                    {/* Treatment Priority Chart */}
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Treatment Priority Ranking
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                          data={reportData.treatmentRecommendations.recommendations
                            .slice(0, 5)
                            .map((rec: any, idx: number) => ({
                              name: rec.type || `Treatment ${idx + 1}`,
                              priority: 5 - idx,
                            }))}
                          layout="vertical"
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" domain={[0, 5]} />
                          <YAxis dataKey="name" type="category" width={120} />
                          <Tooltip />
                          <Bar dataKey="priority" fill="#388e3c" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Grid>
                  </Grid>

                  {/* Treatment Recommendations List */}
                  {reportData.treatmentRecommendations.recommendations.slice(0, 5).map((rec: any, idx: number) => (
                    <Box key={idx} sx={{ mb: 2 }}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle1" gutterBottom>
                            {rec.type}: {rec.regimen}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {rec.rationale}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          )}

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" align="center">
                  Report Generated At: {reportData.generatedAt}
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
                  This report is automatically generated and should not be considered as final medical advice.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="h6">No Report Generated</Typography>
          <Typography>
            To generate a clinical decision report, please first enter patient information in the "Clinical Workflow" tab
            and perform a risk prediction. Then click on the "Generate Full Report" button.
          </Typography>
        </Alert>
      )}
    </Paper>
  )
}

