import { useState, useRef } from 'react'
import { useQuery, useQueryClient } from 'react-query'
import { useVirtualizer } from '@tanstack/react-virtual'
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

async function fetchPatientsList(): Promise<Patient[]> {
  try {
    const response = await api.get('/patients/list', {
      params: { limit: 100 },
      timeout: 60000,
    })
    if (Array.isArray(response.data)) return response.data
    if (response.data?.patients) return response.data.patients
    return []
  } catch {
    try {
      const fallback = await api.get('/patients/dashboard', { params: { limit: 100 }, timeout: 15000 })
      return Array.isArray(fallback.data) ? fallback.data : []
    } catch {
      return []
    }
  }
}

export default function Patients() {
  const [searchTerm, setSearchTerm] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generateSuccess, setGenerateSuccess] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: patients = [], isLoading: loading } = useQuery(
    ['patients', 'list'],
    fetchPatientsList,
    { staleTime: 60 * 1000, retry: 1 }
  )

  const handleQuickGenerate = async () => {
    setGenerating(true)
    setGenerateSuccess(false)
    try {
      await api.post('/synthetic-data/generate', {
        n_patients: 100,
        cancer_ratio: 0.4,
        seed: 42,
        save_to_db: true,
      })
      setGenerateSuccess(true)
      setTimeout(() => {
        queryClient.invalidateQueries(['patients', 'list'])
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

  const parentRef = useRef<HTMLDivElement>(null)
  const useVirtual = filteredPatients.length > 80
  const rowVirtualizer = useVirtualizer({
    count: filteredPatients.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 53,
    overscan: 8,
  })
  const virtualRows = rowVirtualizer.getVirtualItems()
  const totalSize = rowVirtualizer.getTotalSize()

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
          label="Search patients"
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

      <TableContainer ref={parentRef} component={Paper} sx={{ maxHeight: 'calc(100vh - 300px)', overflow: 'auto' }}>
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
          <TableBody sx={{ position: 'relative' }}>
            {filteredPatients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    No patients found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : useVirtual ? (
              <>
                <TableRow sx={{ height: totalSize, visibility: 'hidden' }}><TableCell colSpan={9} /></TableRow>
                {virtualRows.map((virtualRow) => {
                  const patient = filteredPatients[virtualRow.index]
                  const isSynthetic = patient.patient_id.startsWith('CAN') || patient.patient_id.startsWith('NOR')
                  const dataSource = isSynthetic ? 'Synthetic' : 'Real'
                  return (
                    <TableRow
                      key={patient.patient_id}
                      sx={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        transform: `translateY(${virtualRow.start}px)`,
                        '&:hover': { backgroundColor: 'action.hover' },
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {patient.patient_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={dataSource} color={isSynthetic ? 'primary' : 'success'} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{patient.age || '-'}</TableCell>
                      <TableCell>{patient.gender || '-'}</TableCell>
                      <TableCell>{patient.ethnicity || '-'}</TableCell>
                      <TableCell>
                        <Chip label={patient.has_cancer ? 'Cancer' : 'Normal'} color={patient.has_cancer ? 'error' : 'success'} size="small" />
                      </TableCell>
                      <TableCell>{patient.cancer_type || '-'}</TableCell>
                      <TableCell>{patient.cancer_subtype || '-'}</TableCell>
                      <TableCell>{patient.created_at ? new Date(patient.created_at).toLocaleDateString() : '-'}</TableCell>
                    </TableRow>
                  )
                })}
              </>
            ) : (
              filteredPatients.map((patient) => {
                const isSynthetic = patient.patient_id.startsWith('CAN') || patient.patient_id.startsWith('NOR')
                const dataSource = isSynthetic ? 'Synthetic' : 'Real'
                return (
                  <TableRow key={patient.patient_id} sx={{ '&:hover': { backgroundColor: 'action.hover' } }}>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{patient.patient_id}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={dataSource} color={isSynthetic ? 'primary' : 'success'} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>{patient.age || '-'}</TableCell>
                    <TableCell>{patient.gender || '-'}</TableCell>
                    <TableCell>{patient.ethnicity || '-'}</TableCell>
                    <TableCell>
                      <Chip label={patient.has_cancer ? 'Cancer' : 'Normal'} color={patient.has_cancer ? 'error' : 'success'} size="small" />
                    </TableCell>
                    <TableCell>{patient.cancer_type || '-'}</TableCell>
                    <TableCell>{patient.cancer_subtype || '-'}</TableCell>
                    <TableCell>{patient.created_at ? new Date(patient.created_at).toLocaleDateString() : '-'}</TableCell>
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

