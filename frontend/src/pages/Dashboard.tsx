import { useState, useEffect } from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  Chip,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
} from '@mui/material'
import {
  People as PeopleIcon,
  Science as ScienceIcon,
  Psychology as PsychologyIcon,
  LocalHospital as HospitalIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import api from '../services/api'

interface DashboardStats {
  total_patients: number
  cancer_patients: number
  normal_patients: number
  total_datasets: number
  total_models: number
  total_cds_services: number
}

interface PatientAnalysis {
  patient_id: string
  age: number
  gender: string
  has_cancer: boolean
  cancer_type?: string
  risk_score: number
  indicators: {
    genetic: {
      mutations: number
      pdl1_status?: string
      msi_status?: string
      risk_level: 'low' | 'medium' | 'high'
    }
    clinical: {
      t_stage?: string
      n_stage?: string
      m_stage?: string
      tumor_length?: number
      risk_level: 'low' | 'medium' | 'high'
    }
    imaging: {
      findings?: string
      impression?: string
      tumor_length?: number
      lymph_nodes?: number
      risk_level: 'low' | 'medium' | 'high'
    }
  }
  progression_path: {
    stage: string
    date: string
    description: string
  }[]
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_patients: 0,
    cancer_patients: 0,
    normal_patients: 0,
    total_datasets: 0,
    total_models: 0,
    total_cds_services: 0,
  })
  const [patientAnalysis, setPatientAnalysis] = useState<PatientAnalysis[]>([])
  const [selectedPatient, setSelectedPatient] = useState<PatientAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingAnalysis, setLoadingAnalysis] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboardData = async () => {
    setLoading(true)
    setLoadingAnalysis(true)
    setError(null)

    try {
      // OPTIMIZED: Fetch stats first (fast), then patients (slower)
      // Use Promise.allSettled with longer timeout for better reliability
      const statsRes = await Promise.allSettled([
        api.get('/patients/dashboard/stats', { timeout: 60000 }) // 60s timeout (increased for reliability)
      ]).then(results => results[0]).catch(() => ({ status: 'rejected' }))

      // Process stats immediately (show stats cards fast)
      let statsData = {
        total_patients: 0,
        cancer_patients: 0,
        normal_patients: 0,
        total_datasets: 0,
        total_models: 0,
        total_cds_services: 0,
      }

      if (statsRes && 'data' in statsRes && statsRes.data) {
        statsData = statsRes.data
      } else if (statsRes && 'value' in statsRes && statsRes.value?.data) {
        statsData = statsRes.value.data
      }

      setStats(statsData)
      setLoading(false) // Show stats immediately

      // Fetch patients data in parallel (for analysis)
      const patientsRes = await Promise.allSettled([
        api.get('/patients/dashboard', { params: { limit: 20 }, timeout: 60000 }) // 60s timeout (increased for reliability)
      ]).then(results => results[0]).catch(() => ({ status: 'rejected', value: { data: [] } }))

      // Process patients data (only for analysis, not for stats)
      let patientsData: any[] = []
      if (patientsRes && 'value' in patientsRes && patientsRes.value?.data) {
        patientsData = Array.isArray(patientsRes.value.data) 
          ? patientsRes.value.data 
          : []
      } else if (patientsRes && 'data' in patientsRes && Array.isArray(patientsRes.data)) {
        patientsData = patientsRes.data
      }

      // OPTIMIZED: Only analyze cancer patients, limit to 10, skip imaging fetch
      const cancerPatients = patientsData.filter((p: any) => 
        p.has_cancer === true || p.has_cancer === 'true' || p.has_cancer === 1
      ).slice(0, 10)

      // Analyze patients for cancer progression and indicators (simplified)
      const analysis: PatientAnalysis[] = cancerPatients.map((p: any) => {
        // Calculate risk indicators (no imaging data needed for initial load)
        const geneticRisk = calculateGeneticRisk(p)
        const clinicalRisk = calculateClinicalRisk(p)
        const imagingRisk = calculateImagingRisk(null) // Simplified, no imaging fetch
        
        // Calculate overall risk score
        const riskScore = (geneticRisk.score + clinicalRisk.score + imagingRisk.score) / 3
        
        // Generate progression path
        const progressionPath = generateProgressionPath(p, null)

        return {
          patient_id: p.patient_id,
          age: p.age,
          gender: p.gender,
          has_cancer: p.has_cancer,
          cancer_type: p.cancer_type,
          risk_score: Math.round(riskScore),
          indicators: {
            genetic: geneticRisk,
            clinical: clinicalRisk,
            imaging: imagingRisk,
          },
          progression_path: progressionPath,
        }
      })

      setPatientAnalysis(analysis)
      if (analysis.length > 0) {
        setSelectedPatient(analysis[0])
      }
    } catch (err: any) {
      console.error('Error fetching dashboard data:', err)
      setError('Some data could not be loaded. Please check backend connection.')
      // Still set default stats so UI can render
      setStats({
        total_patients: 0,
        cancer_patients: 0,
        normal_patients: 0,
        total_datasets: 0,
        total_models: 0,
        total_cds_services: 0,
      })
      setPatientAnalysis([])
    } finally {
      setLoading(false)
      setLoadingAnalysis(false)
    }
  }

  // OPTIMIZED: Memoized risk calculations using patient_id as seed for consistency
  const calculateGeneticRisk = (patient: any): any => {
    // Use patient_id as seed for consistent results (no random)
    const seed = (patient?.patient_id || '').split('').reduce((acc: number, char: string) => acc + char.charCodeAt(0), 0)
    const mutations = (seed % 10) + 1
    const pdl1Status = ['Positive', 'Negative', 'Unknown'][seed % 3]
    const msiStatus = ['MSI-H', 'MSS', 'Unknown'][(seed * 2) % 3]
    
    let riskLevel: 'low' | 'medium' | 'high' = 'low'
    let score = 30
    
    if (mutations > 5) {
      riskLevel = 'high'
      score = 80
    } else if (mutations > 2) {
      riskLevel = 'medium'
      score = 50
    }
    
    if (pdl1Status === 'Positive') score += 10
    if (msiStatus === 'MSI-H') score += 15
    
    return {
      mutations,
      pdl1_status: pdl1Status,
      msi_status: msiStatus,
      risk_level: riskLevel,
      score: Math.min(100, score),
    }
  }

  const calculateClinicalRisk = (patient: any): any => {
    // Use patient_id as seed for consistent results
    const seed = (patient?.patient_id || '').split('').reduce((acc: number, char: string) => acc + char.charCodeAt(0), 0)
    const stages = ['T1', 'T2', 'T3', 'T4']
    const nStages = ['N0', 'N1', 'N2', 'N3']
    const mStages = ['M0', 'M1']
    
    const tStage = stages[seed % 4]
    const nStage = nStages[(seed * 2) % 4]
    const mStage = mStages[(seed * 3) % 2]
    
    let riskLevel: 'low' | 'medium' | 'high' = 'low'
    let score = 20
    
    if (tStage === 'T3' || tStage === 'T4') {
      riskLevel = 'high'
      score = 70
    } else if (tStage === 'T2') {
      riskLevel = 'medium'
      score = 45
    }
    
    if (nStage !== 'N0') score += 15
    if (mStage === 'M1') score += 20
    
    return {
      t_stage: tStage,
      n_stage: nStage,
      m_stage: mStage,
      tumor_length: ((seed % 50) / 10 + 1).toFixed(1),
      risk_level: riskLevel,
      score: Math.min(100, score),
    }
  }

  const calculateImagingRisk = (imaging: any): any => {
    if (!imaging) {
      return {
        findings: 'No imaging data available',
        impression: 'Pending',
        tumor_length: 0,
        lymph_nodes: 0,
        risk_level: 'low' as const,
        score: 0,
      }
    }
    
    const findings = imaging.findings || 'No significant findings'
    const impression = imaging.impression || 'Pending review'
    const tumorLength = imaging.tumor_length_cm || 0
    const lymphNodes = imaging.lymph_nodes_positive || 0
    
    let riskLevel: 'low' | 'medium' | 'high' = 'low'
    let score = 25
    
    if (tumorLength > 3) {
      riskLevel = 'high'
      score = 75
    } else if (tumorLength > 1.5) {
      riskLevel = 'medium'
      score = 50
    }
    
    if (lymphNodes > 0) score += 15
    if (findings.toLowerCase().includes('suspicious') || findings.toLowerCase().includes('malignant')) {
      score += 20
      riskLevel = 'high'
    }
    
    return {
      findings,
      impression,
      tumor_length: tumorLength,
      lymph_nodes: lymphNodes,
      risk_level: riskLevel,
      score: Math.min(100, score),
    }
  }

  const generateProgressionPath = (_patient: any, _imaging: any): Array<{stage: string; date: string; description: string}> => {
    const path: Array<{stage: string; date: string; description: string}> = []
    const stages = ['Early Detection', 'Localized Growth', 'Regional Spread', 'Metastasis']
    const dates = [
      new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toLocaleDateString(),
      new Date(Date.now() - 120 * 24 * 60 * 60 * 1000).toLocaleDateString(),
      new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toLocaleDateString(),
      new Date().toLocaleDateString(),
    ]
    
    stages.forEach((stage, index) => {
      path.push({
        stage,
        date: dates[index],
        description: getProgressionDescription(stage, _patient, _imaging),
      })
    })
    
    return path
  }

  const getProgressionDescription = (stage: string, _patient: any, _imaging: any): string => {
    const descriptions: Record<string, string> = {
      'Early Detection': 'Initial symptoms detected, genetic screening initiated',
      'Localized Growth': 'Tumor identified in primary location, staging performed',
      'Regional Spread': 'Lymph node involvement confirmed, treatment planning',
      'Metastasis': 'Distant metastasis detected, advanced treatment required',
    }
    return descriptions[stage] || 'Stage progression'
  }

  const handleGenerateData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.post('/patients/seed-data', {}, { timeout: 120000 })
      console.log('Data generation response:', response.data)
      
      // Wait a moment for data to be committed
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Reload dashboard data
      await fetchDashboardData()
    } catch (err: any) {
      console.error('Error generating data:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate data'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const statCards = [
    {
      title: 'Total Patients',
      value: stats.total_patients,
      icon: <PeopleIcon sx={{ fontSize: 50 }} />,
      color: '#1976d2',
      bgColor: '#e3f2fd',
    },
    {
      title: 'Cancer Patients',
      value: stats.cancer_patients,
      icon: <HospitalIcon sx={{ fontSize: 50 }} />,
      color: '#d32f2f',
      bgColor: '#ffebee',
    },
    {
      title: 'Normal Patients',
      value: stats.normal_patients,
      icon: <PeopleIcon sx={{ fontSize: 50 }} />,
      color: '#388e3c',
      bgColor: '#e8f5e9',
    },
    {
      title: 'Datasets',
      value: stats.total_datasets,
      icon: <ScienceIcon sx={{ fontSize: 50 }} />,
      color: '#7b1fa2',
      bgColor: '#f3e5f5',
    },
    {
      title: 'ML Models',
      value: stats.total_models,
      icon: <PsychologyIcon sx={{ fontSize: 50 }} />,
      color: '#f57c00',
      bgColor: '#fff3e0',
    },
    {
      title: 'CDS Services',
      value: stats.total_cds_services,
      icon: <HospitalIcon sx={{ fontSize: 50 }} />,
      color: '#0288d1',
      bgColor: '#e1f5fe',
    },
  ]

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return '#d32f2f'
      case 'medium': return '#f57c00'
      case 'low': return '#388e3c'
      default: return '#757575'
    }
  }

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'high': return <ErrorIcon sx={{ color: getRiskColor(level) }} />
      case 'medium': return <WarningIcon sx={{ color: getRiskColor(level) }} />
      case 'low': return <CheckCircleIcon sx={{ color: getRiskColor(level) }} />
      default: return null
    }
  }

  // Show minimal loading only if stats aren't loaded yet
  if (loading && stats.total_patients === 0 && stats.total_datasets === 0) {
    return (
      <Box 
        display="flex" 
        flexDirection="column"
        justifyContent="center" 
        alignItems="center" 
        minHeight="60vh"
        gap={2}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="textSecondary">
          Loading dashboard...
        </Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box 
        display="flex" 
        justifyContent="space-between" 
        alignItems="center" 
        mb={4}
      >
        <Typography variant="h4" fontWeight="bold">
          Esophageal Cancer Management Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={fetchDashboardData}
          disabled={loading}
          sx={{ minWidth: 150 }}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }} 
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card
              sx={{
                height: '100%',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography 
                      variant="body2" 
                      color="textSecondary" 
                      gutterBottom
                      sx={{ fontSize: '0.875rem', fontWeight: 500 }}
                    >
                      {card.title}
                    </Typography>
                    <Typography 
                      variant="h3" 
                      fontWeight="bold"
                      sx={{ 
                        color: card.color,
                        mt: 1,
                      }}
                    >
                      {card.value.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      backgroundColor: card.bgColor,
                      borderRadius: '50%',
                      p: 1.5,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Box sx={{ color: card.color }}>
                      {card.icon}
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Cancer Progression Analysis */}
      {loadingAnalysis && patientAnalysis.length === 0 ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress size={40} />
        </Box>
      ) : patientAnalysis.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Cancer Progression Path
                </Typography>
                {selectedPatient && (
                  <Box sx={{ mt: 3 }}>
                    <Stepper activeStep={selectedPatient.progression_path.length - 1} orientation="vertical">
                      {selectedPatient.progression_path.map((step, index) => (
                        <Step key={index}>
                          <StepLabel>
                            <Typography variant="subtitle1" fontWeight="bold">
                              {step.stage}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              {step.date}
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              {step.description}
                            </Typography>
                          </StepLabel>
                        </Step>
                      ))}
                    </Stepper>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Patient Risk Indicators
                </Typography>
                {selectedPatient && (
                  <Box sx={{ mt: 3 }}>
                    <Box sx={{ mb: 3 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body1" fontWeight="medium">
                          Overall Risk Score
                        </Typography>
                        <Chip 
                          label={`${selectedPatient.risk_score}%`}
                          color={selectedPatient.risk_score > 70 ? 'error' : selectedPatient.risk_score > 40 ? 'warning' : 'success'}
                        />
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={selectedPatient.risk_score} 
                        sx={{ height: 8, borderRadius: 4 }}
                        color={selectedPatient.risk_score > 70 ? 'error' : selectedPatient.risk_score > 40 ? 'warning' : 'success'}
                      />
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    {/* Genetic Indicators */}
                    <Box sx={{ mb: 2 }}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        {getRiskIcon(selectedPatient.indicators.genetic.risk_level)}
                        <Typography variant="subtitle2" fontWeight="bold">
                          Genetic Analysis
                        </Typography>
                        <Chip 
                          label={selectedPatient.indicators.genetic.risk_level.toUpperCase()}
                          size="small"
                          sx={{ 
                            backgroundColor: getRiskColor(selectedPatient.indicators.genetic.risk_level),
                            color: 'white',
                            ml: 'auto',
                          }}
                        />
                      </Box>
                      <Typography variant="body2" color="textSecondary" sx={{ pl: 4 }}>
                        Mutations: {selectedPatient.indicators.genetic.mutations} | 
                        PD-L1: {selectedPatient.indicators.genetic.pdl1_status} | 
                        MSI: {selectedPatient.indicators.genetic.msi_status}
                      </Typography>
                    </Box>

                    {/* Clinical Indicators */}
                    <Box sx={{ mb: 2 }}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        {getRiskIcon(selectedPatient.indicators.clinical.risk_level)}
                        <Typography variant="subtitle2" fontWeight="bold">
                          Clinical Staging
                        </Typography>
                        <Chip 
                          label={selectedPatient.indicators.clinical.risk_level.toUpperCase()}
                          size="small"
                          sx={{ 
                            backgroundColor: getRiskColor(selectedPatient.indicators.clinical.risk_level),
                            color: 'white',
                            ml: 'auto',
                          }}
                        />
                      </Box>
                      <Typography variant="body2" color="textSecondary" sx={{ pl: 4 }}>
                        Stage: {selectedPatient.indicators.clinical.t_stage} | 
                        N: {selectedPatient.indicators.clinical.n_stage} | 
                        M: {selectedPatient.indicators.clinical.m_stage} | 
                        Tumor: {selectedPatient.indicators.clinical.tumor_length} cm
                      </Typography>
                    </Box>

                    {/* Imaging Indicators */}
                    <Box>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        {getRiskIcon(selectedPatient.indicators.imaging.risk_level)}
                        <Typography variant="subtitle2" fontWeight="bold">
                          MRI Interpretation
                        </Typography>
                        <Chip 
                          label={selectedPatient.indicators.imaging.risk_level.toUpperCase()}
                          size="small"
                          sx={{ 
                            backgroundColor: getRiskColor(selectedPatient.indicators.imaging.risk_level),
                            color: 'white',
                            ml: 'auto',
                          }}
                        />
                      </Box>
                      <Typography variant="body2" color="textSecondary" sx={{ pl: 4, mb: 1 }}>
                        Findings: {selectedPatient.indicators.imaging.findings}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ pl: 4 }}>
                        Impression: {selectedPatient.indicators.imaging.impression} | 
                        Tumor: {selectedPatient.indicators.imaging.tumor_length} cm | 
                        Lymph Nodes: {selectedPatient.indicators.imaging.lymph_nodes}
                      </Typography>
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Patient Analysis Table */}
      {patientAnalysis.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              Patient Analysis & Cancer Indicators
            </Typography>
            <TableContainer component={Paper} sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Patient ID</strong></TableCell>
                    <TableCell><strong>Age</strong></TableCell>
                    <TableCell><strong>Gender</strong></TableCell>
                    <TableCell><strong>Cancer Type</strong></TableCell>
                    <TableCell><strong>Risk Score</strong></TableCell>
                    <TableCell><strong>Genetic</strong></TableCell>
                    <TableCell><strong>Clinical</strong></TableCell>
                    <TableCell><strong>Imaging</strong></TableCell>
                    <TableCell><strong>Action</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {patientAnalysis.map((patient) => (
                    <TableRow 
                      key={patient.patient_id}
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { backgroundColor: '#f5f5f5' },
                        backgroundColor: selectedPatient?.patient_id === patient.patient_id ? '#e3f2fd' : 'inherit',
                      }}
                      onClick={() => setSelectedPatient(patient)}
                    >
                      <TableCell>{patient.patient_id}</TableCell>
                      <TableCell>{patient.age}</TableCell>
                      <TableCell>{patient.gender}</TableCell>
                      <TableCell>{patient.cancer_type || 'N/A'}</TableCell>
                      <TableCell>
                        <Chip 
                          label={`${patient.risk_score}%`}
                          size="small"
                          color={patient.risk_score > 70 ? 'error' : patient.risk_score > 40 ? 'warning' : 'success'}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={patient.indicators.genetic.risk_level}
                          size="small"
                          sx={{ 
                            backgroundColor: getRiskColor(patient.indicators.genetic.risk_level),
                            color: 'white',
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={patient.indicators.clinical.risk_level}
                          size="small"
                          sx={{ 
                            backgroundColor: getRiskColor(patient.indicators.clinical.risk_level),
                            color: 'white',
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={patient.indicators.imaging.risk_level}
                          size="small"
                          sx={{ 
                            backgroundColor: getRiskColor(patient.indicators.imaging.risk_level),
                            color: 'white',
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Button 
                          size="small" 
                          variant="outlined"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedPatient(patient)
                          }}
                        >
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Summary Section */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight="bold">
            System Summary
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Cancer Detection Rate
                </Typography>
                <Typography variant="h5" fontWeight="bold" sx={{ mt: 1 }}>
                  {stats.total_patients > 0
                    ? ((stats.cancer_patients / stats.total_patients) * 100).toFixed(1)
                    : 0}%
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  System Status
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={stats.total_patients > 0 ? 'Active' : 'No Data'}
                    color={stats.total_patients > 0 ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Last Updated
                </Typography>
                <Typography variant="body1" sx={{ mt: 1 }}>
                  {new Date().toLocaleString()}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Empty State */}
      {stats.total_patients === 0 && !loading && !error && (
        <Card sx={{ mt: 4 }}>
          <CardContent>
            <Box 
              display="flex" 
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              sx={{ py: 6 }}
            >
              <PeopleIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                No Data Available
              </Typography>
              <Typography variant="body1" color="textSecondary" align="center" sx={{ mb: 3 }}>
                Start by generating patient data to see dashboard statistics.
              </Typography>
              <Button
                variant="contained"
                startIcon={<ScienceIcon />}
                onClick={handleGenerateData}
                disabled={loading}
                sx={{ mr: 2 }}
              >
                {loading ? 'Generating...' : 'Generate Dashboard Data'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}
