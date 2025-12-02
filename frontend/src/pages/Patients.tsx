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
  Button,
  Chip,
  CircularProgress,
  TextField,
  InputAdornment,
  Alert,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import AddIcon from '@mui/icons-material/Add'
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
          Patients
        </Typography>
        <Alert severity="info" sx={{ mt: 2 }}>
          No patients found. Please generate data first.
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              onClick={() => window.location.href = '/data-generation'}
            >
              Go to Data Generation
            </Button>
          </Box>
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Patients</Typography>
        <Button variant="contained" startIcon={<AddIcon />}>
          Add Patient
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
              <TableCell>Patient ID</TableCell>
              <TableCell>Age</TableCell>
              <TableCell>Gender</TableCell>
              <TableCell>Cancer Status</TableCell>
              <TableCell>Cancer Type</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredPatients.map((patient) => (
              <TableRow key={patient.patient_id}>
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
                <TableCell>
                  <Button size="small" variant="outlined">
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}

