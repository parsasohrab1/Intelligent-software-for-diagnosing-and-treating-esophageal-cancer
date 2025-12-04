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
  has_cancer: boolean
  cancer_type: string | null
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
      const response = await api.get('/patients/')
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
      // Set empty array on error to prevent UI issues
      setPatients([])
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

  const filteredPatients = patients.filter((patient) =>
    patient.patient_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (patient.cancer_type && patient.cancer_type.toLowerCase().includes(searchTerm.toLowerCase()))
  )

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
                onClick={() => navigate('/data-generation')}
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
          onClick={() => navigate('/data-generation')}
        >
          Generate New Data
        </Button>
      </Box>

      <TextField
        fullWidth
        placeholder="Search patients..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Patient ID</strong></TableCell>
              <TableCell><strong>Age</strong></TableCell>
              <TableCell><strong>Gender</strong></TableCell>
              <TableCell><strong>Cancer Status</strong></TableCell>
              <TableCell><strong>Cancer Type</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredPatients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    No patients found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredPatients.map((patient) => (
                <TableRow 
                  key={patient.patient_id}
                  sx={{ '&:hover': { backgroundColor: 'action.hover' } }}
                >
                  <TableCell>{patient.patient_id}</TableCell>
                  <TableCell>{patient.age}</TableCell>
                  <TableCell>{patient.gender}</TableCell>
                  <TableCell>
                    <Chip
                      label={patient.has_cancer ? 'Cancer' : 'Normal'}
                      color={patient.has_cancer ? 'error' : 'success'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{patient.cancer_type || '-'}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredPatients.length > 0 && (
        <Box mt={2}>
          <Typography variant="body2" color="text.secondary">
            Total: {filteredPatients.length} patients
          </Typography>
        </Box>
      )}
    </Box>
  )
}

