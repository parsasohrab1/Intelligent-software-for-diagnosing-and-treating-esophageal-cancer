import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  TextField,
  InputAdornment,
  Alert,
  Button,
  Stack,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import AddIcon from '@mui/icons-material/Add'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

interface Patient {
  patient_id: string
  age: number
  gender: string
  ethnicity?: string | null
  has_cancer: boolean
  cancer_type: string | null
  cancer_subtype?: string | null
  created_at?: string
  updated_at?: string
  [key: string]: any
}

export default function Patients() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generateSuccess, setGenerateSuccess] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetchPatients()
  }, [])

  const fetchPatients = async () => {
    try {
      // Use public endpoint that doesn't require authentication
      const response = await api.get('/patients/list', {
        params: { limit: 100 },
        timeout: 60000, // 60 seconds timeout (increased for reliability)
      })
      // Handle both array and object responses
      if (Array.isArray(response.data)) {
        setPatients(response.data)
      } else if (response.data && Array.isArray(response.data.patients)) {
        setPatients(response.data.patients)
      } else {
        setPatients([])
      }
    } catch (error: any) {
      console.error('Error fetching patients:', error)
      // Try fallback to dashboard endpoint if list fails
      try {
        const fallbackResponse = await api.get('/patients/dashboard', {
          params: { limit: 100 },
          timeout: 15000,
        })
        if (Array.isArray(fallbackResponse.data)) {
          setPatients(fallbackResponse.data)
        } else {
          setPatients([])
        }
      } catch (fallbackError) {
        console.error('Fallback endpoint also failed:', fallbackError)
        setPatients([])
      }
    } finally {
      setLoading(false)
    }
  }

  const handleQuickGenerate = async () => {
    setGenerating(true)
    setGenerateSuccess(false)
    try {
      const response = await api.post('/synthetic-data/generate', {
        n_patients: 100,
        cancer_ratio: 0.4,
        seed: 42,
        save_to_db: true,
      })
      
      console.log('Data generation started:', response.data)
      setGenerateSuccess(true)
      
      // Wait a bit for the background task to complete, then refresh
      setTimeout(() => {
        fetchPatients()
        setGenerateSuccess(false)
      }, 3000)
    } catch (error: any) {
      console.error('Error generating data:', error)
      alert('Error generating data. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const filteredPatients = patients.filter((patient) => {
    const searchLower = searchTerm.toLowerCase()
    return (
      patient.patient_id.toLowerCase().includes(searchLower) ||
      (patient.cancer_type && patient.cancer_type.toLowerCase().includes(searchLower)) ||
      (patient.cancer_subtype && patient.cancer_subtype.toLowerCase().includes(searchLower)) ||
      (patient.ethnicity && patient.ethnicity.toLowerCase().includes(searchLower)) ||
      patient.gender.toLowerCase().includes(searchLower) ||
      (patient.patient_id.startsWith('CAN') || patient.patient_id.startsWith('NOR') ? 'synthetic' : 'real').includes(searchLower)
    )
  })

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (patients.length === 0 && !loading) {
    return (
      <Box p={3}>
        <Typography variant="h4" gutterBottom>
          Patient List
        </Typography>
        {generateSuccess && (
          <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
            Data generated successfully. Loading...
          </Alert>
        )}
        <Alert 
          severity="info" 
          sx={{ mt: 2, mb: 2 }}
          action={
            <Stack direction="row" spacing={2}>
              <Button
                color="inherit"
                size="small"
                onClick={handleQuickGenerate}
                disabled={generating}
                startIcon={generating ? <CircularProgress size={16} /> : <PlayArrowIcon />}
              >
                {generating ? 'Generating...' : 'Quick Generate (100 patients)'}
              </Button>
              <Button
                color="inherit"
                size="small"
                onClick={() => navigate('/patient-data')}
                startIcon={<AddIcon />}
              >
                Generate with Settings
              </Button>
            </Stack>
          }
        >
          No patients found. Please generate data first.
        </Alert>
      </Box>
    )
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">
          Patient List
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/patient-data')}
        >
          Generate New Data
        </Button>
      </Box>

      <Box display="flex" gap={2} mb={3}>
        <TextField
          fullWidth
          placeholder="Search by ID, cancer type, subtype, ethnicity, gender, or data source..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
        <Box display="flex" gap={1} alignItems="center">
          <Chip
            label={`Total: ${filteredPatients.length}`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`Real: ${filteredPatients.filter(p => !p.patient_id.startsWith('CAN') && !p.patient_id.startsWith('NOR')).length}`}
            color="success"
            variant="outlined"
          />
          <Chip
            label={`Synthetic: ${filteredPatients.filter(p => p.patient_id.startsWith('CAN') || p.patient_id.startsWith('NOR')).length}`}
            color="info"
            variant="outlined"
          />
        </Box>
      </Box>

      <TableContainer component={Paper} sx={{ maxHeight: 'calc(100vh - 300px)', overflowX: 'auto' }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell><strong>Patient ID</strong></TableCell>
              <TableCell><strong>Data Source</strong></TableCell>
              <TableCell><strong>Age</strong></TableCell>
              <TableCell><strong>Gender</strong></TableCell>
              <TableCell><strong>Ethnicity</strong></TableCell>
              <TableCell><strong>Cancer Status</strong></TableCell>
              <TableCell><strong>Cancer Type</strong></TableCell>
              <TableCell><strong>Cancer Subtype</strong></TableCell>
              <TableCell><strong>Created Date</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredPatients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    No patients found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredPatients.map((patient) => {
                // Determine data source based on patient_id pattern
                const isSynthetic = patient.patient_id.startsWith('CAN') || patient.patient_id.startsWith('NOR')
                const dataSource = isSynthetic ? 'Synthetic' : 'Real'
                
                return (
                  <TableRow 
                    key={patient.patient_id}
                    sx={{ '&:hover': { backgroundColor: 'action.hover' } }}
                  >
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                        {patient.patient_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={dataSource}
                        color={isSynthetic ? 'primary' : 'success'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{patient.age || '-'}</TableCell>
                    <TableCell>{patient.gender || '-'}</TableCell>
                    <TableCell>{patient.ethnicity || '-'}</TableCell>
                    <TableCell>
                      <Chip
                        label={patient.has_cancer ? 'Cancer' : 'Normal'}
                        color={patient.has_cancer ? 'error' : 'success'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{patient.cancer_type || '-'}</TableCell>
                    <TableCell>{patient.cancer_subtype || '-'}</TableCell>
                    <TableCell>
                      {patient.created_at 
                        ? new Date(patient.created_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

    </Box>
  )
}

