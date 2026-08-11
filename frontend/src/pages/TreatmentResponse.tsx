import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material'
import ScienceIcon from '@mui/icons-material/Science'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import api from '../services/api'

interface Patient {
  patient_id: string
  age?: number
  has_cancer?: boolean
}

interface PredictionResult {
  patient_id: string
  treatment_type: string
  response_probability: number
  response_category: string
  confidence: number
  biomarkers_contribution: Record<string, number>
  radiomics_contribution: Record<string, number>
  key_factors: string[]
  recommendation: string
  timestamp: string
}

export default function TreatmentResponse() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [patientId, setPatientId] = useState('')
  const [treatmentType, setTreatmentType] = useState('Chemotherapy')
  const [loading, setLoading] = useState(false)
  const [loadingPatients, setLoadingPatients] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PredictionResult | null>(null)

  useEffect(() => {
    api
      .get('/patients/list', { params: { limit: 500 }, timeout: 30000 })
      .then((res) => {
        const list = res.data.patients || res.data || []
        setPatients(Array.isArray(list) ? list : [])
        if (list.length > 0) setPatientId(list[0].patient_id)
      })
      .catch(() => setPatients([]))
      .finally(() => setLoadingPatients(false))
  }, [])

  const runPrediction = async () => {
    if (!patientId) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await api.post<PredictionResult>('/treatment-response/predict', {
        patient_id: patientId,
        treatment_type: treatmentType,
        use_imaging: true,
      })
      setResult(response.data)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err instanceof Error ? err.message : 'Prediction failed')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const responseColor =
    (result?.response_probability ?? 0) >= 0.7
      ? 'success'
      : (result?.response_probability ?? 0) >= 0.4
        ? 'warning'
        : 'error'

  return (
    <Box p={3}>
      <Box display="flex" alignItems="center" mb={3}>
        <ScienceIcon sx={{ mr: 1, fontSize: 32, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4">Treatment Response Prediction</Typography>
          <Typography variant="body2" color="text.secondary">
            Predict neoadjuvant chemotherapy or radiotherapy response using biomarkers and radiomics
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Parameters
              </Typography>
              {loadingPatients ? (
                <CircularProgress size={24} />
              ) : (
                <>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Patient</InputLabel>
                    <Select
                      value={patientId}
                      label="Patient"
                      onChange={(e) => setPatientId(e.target.value)}
                    >
                      {patients.map((p) => (
                        <MenuItem key={p.patient_id} value={p.patient_id}>
                          {p.patient_id}
                          {p.has_cancer ? ' (cancer)' : ''}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Treatment Type</InputLabel>
                    <Select
                      value={treatmentType}
                      label="Treatment Type"
                      onChange={(e) => setTreatmentType(e.target.value)}
                    >
                      <MenuItem value="Chemotherapy">Chemotherapy</MenuItem>
                      <MenuItem value="Radiotherapy">Radiotherapy</MenuItem>
                    </Select>
                  </FormControl>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
                    onClick={runPrediction}
                    disabled={loading || !patientId}
                  >
                    Predict Response
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Prediction Results
              </Typography>
              {!result ? (
                <Typography color="text.secondary">
                  Select a patient and run prediction to see results
                </Typography>
              ) : (
                <Box>
                  <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                    <Chip label={result.response_category} color={responseColor} />
                    <Chip label={`Confidence: ${(result.confidence * 100).toFixed(0)}%`} />
                    <Chip label={result.treatment_type} variant="outlined" />
                  </Box>

                  <Typography variant="subtitle2" gutterBottom>
                    Response Probability
                  </Typography>
                  <Box display="flex" alignItems="center" gap={2} mb={3}>
                    <LinearProgress
                      variant="determinate"
                      value={result.response_probability * 100}
                      color={responseColor}
                      sx={{ flex: 1, height: 12, borderRadius: 1 }}
                    />
                    <Typography variant="h5" fontWeight="bold">
                      {(result.response_probability * 100).toFixed(1)}%
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        Biomarker Contributions
                      </Typography>
                      {Object.entries(result.biomarkers_contribution || {}).map(([k, v]) => (
                        <Box key={k} mb={1}>
                          <Typography variant="caption" textTransform="capitalize">
                            {k.replace(/_/g, ' ')}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={Math.min(100, Math.abs(v) * 100)}
                            sx={{ height: 6, borderRadius: 1 }}
                          />
                        </Box>
                      ))}
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        Radiomics Contributions
                      </Typography>
                      {Object.entries(result.radiomics_contribution || {}).map(([k, v]) => (
                        <Box key={k} mb={1}>
                          <Typography variant="caption" textTransform="capitalize">
                            {k.replace(/_/g, ' ')}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={Math.min(100, Math.abs(v) * 100)}
                            color="secondary"
                            sx={{ height: 6, borderRadius: 1 }}
                          />
                        </Box>
                      ))}
                    </Grid>
                  </Grid>

                  {result.key_factors?.length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Key Factors
                      </Typography>
                      <List dense>
                        {result.key_factors.map((f, i) => (
                          <ListItem key={i}>
                            <ListItemText primary={f} />
                          </ListItem>
                        ))}
                      </List>
                    </>
                  )}

                  {result.recommendation && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Alert severity="info">{result.recommendation}</Alert>
                    </>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
