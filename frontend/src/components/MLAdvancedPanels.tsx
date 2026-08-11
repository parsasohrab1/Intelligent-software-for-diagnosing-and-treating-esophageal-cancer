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
  Chip,
  LinearProgress,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import HubIcon from '@mui/icons-material/Hub'
import BiotechIcon from '@mui/icons-material/Biotech'
import WorkIcon from '@mui/icons-material/Work'
import api from '../services/api'
import { useJobPolling, JobRecord } from '../hooks/useJobPolling'

interface Patient {
  patient_id: string
}

export function MultimodalFusionPanel() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [patientId, setPatientId] = useState('')
  const [useEndoscopy, setUseEndoscopy] = useState(true)
  const [useRadiomics, setUseRadiomics] = useState(true)
  const [useLab, setUseLab] = useState(true)
  const [useGenomic, setUseGenomic] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    api
      .get('/patients/list', { params: { limit: 200 } })
      .then((res) => {
        const list = res.data.patients || res.data || []
        setPatients(Array.isArray(list) ? list : [])
        if (list[0]) setPatientId(list[0].patient_id)
      })
      .catch(() => {})
  }, [])

  const predict = async () => {
    if (!patientId) return
    setLoading(true)
    setError(null)
    try {
      const response = await api.post('/multimodal-fusion/predict', {
        patient_id: patientId,
        use_endoscopy: useEndoscopy,
        use_radiomics: useRadiomics,
        use_lab: useLab,
        use_genomic: useGenomic,
        return_attention_weights: true,
      }, { timeout: 120000 })
      setResult(response.data)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Multimodal prediction failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={2}>
        <HubIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">Multi-Modal Fusion</Typography>
      </Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Patient</InputLabel>
                <Select value={patientId} label="Patient" onChange={(e) => setPatientId(e.target.value)}>
                  {patients.map((p) => (
                    <MenuItem key={p.patient_id} value={p.patient_id}>
                      {p.patient_id}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControlLabel
                control={<Switch checked={useEndoscopy} onChange={(e) => setUseEndoscopy(e.target.checked)} />}
                label="Endoscopy"
              />
              <FormControlLabel
                control={<Switch checked={useRadiomics} onChange={(e) => setUseRadiomics(e.target.checked)} />}
                label="Radiomics"
              />
              <FormControlLabel
                control={<Switch checked={useLab} onChange={(e) => setUseLab(e.target.checked)} />}
                label="Lab Results"
              />
              <FormControlLabel
                control={<Switch checked={useGenomic} onChange={(e) => setUseGenomic(e.target.checked)} />}
                label="Genomic Data"
              />
              <Button
                fullWidth
                variant="contained"
                sx={{ mt: 2 }}
                startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
                onClick={predict}
                disabled={loading || !patientId}
              >
                Run Fusion Prediction
              </Button>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              {!result ? (
                <Typography color="text.secondary">Run prediction to see fusion results</Typography>
              ) : (
                <Box>
                  <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                    <Chip label={`Prediction: ${Number(result.prediction).toFixed(3)}`} color="primary" />
                    <Chip label={`Confidence: ${(Number(result.confidence) * 100).toFixed(0)}%`} />
                    {(result.modalities_used as string[])?.map((m) => (
                      <Chip key={m} label={m} size="small" variant="outlined" />
                    ))}
                  </Box>
                  {result.attention_weights != null && typeof result.attention_weights === 'object' && (
                    <>
                      <Typography variant="subtitle2" gutterBottom>
                        Attention Weights
                      </Typography>
                      <List dense>
                        {Object.entries(result.attention_weights as Record<string, number>).map(([k, v]) => (
                          <ListItem key={k}>
                            <ListItemText primary={k} />
                            <LinearProgress
                              variant="determinate"
                              value={v * 100}
                              sx={{ width: 120, ml: 2 }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </>
                  )}
                  {result.modality_contributions != null && typeof result.modality_contributions === 'object' && (
                    <>
                      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                        Modality Contributions
                      </Typography>
                      <List dense>
                        {Object.entries(result.modality_contributions as Record<string, number>).map(([k, v]) => (
                          <ListItem key={k}>
                            <ListItemText primary={k} secondary={`${(v * 100).toFixed(1)}%`} />
                          </ListItem>
                        ))}
                      </List>
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

export function FewShotLearningPanel() {
  const [subtypes, setSubtypes] = useState<Array<Record<string, unknown>>>([])
  const [subtype, setSubtype] = useState('')
  const [method, setMethod] = useState('prototypical')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    api
      .get('/few-shot-learning/rare-subtypes')
      .then((res) => {
        const list = res.data.rare_subtypes || []
        setSubtypes(Array.isArray(list) ? list : [])
        if (list[0]?.name) setSubtype(String(list[0].name))
        else if (list[0]) setSubtype(String(list[0]))
      })
      .catch(() => {})
  }, [])

  const predictWithImages = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files?.length || !subtype) return
    e.target.value = ''
    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      Array.from(files).forEach((f) => formData.append('query_files', f))

      const response = await api.post('/few-shot-learning/predict', formData, {
        params: { subtype, method },
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })
      setResult(response.data)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Few-shot prediction failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={2}>
        <BiotechIcon sx={{ mr: 1, color: 'secondary.main' }} />
        <Typography variant="h6">Few-Shot Learning — Rare Subtypes</Typography>
      </Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Rare Subtype</InputLabel>
                <Select value={subtype} label="Rare Subtype" onChange={(e) => setSubtype(e.target.value)}>
                  {subtypes.map((s, i) => {
                    const name = String(s.name || s.subtype || s)
                    return (
                      <MenuItem key={i} value={name}>
                        {name}
                      </MenuItem>
                    )
                  })}
                  {subtypes.length === 0 && (
                    <MenuItem value="adenosquamous">Adenosquamous</MenuItem>
                  )}
                </Select>
              </FormControl>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Method</InputLabel>
                <Select value={method} label="Method" onChange={(e) => setMethod(e.target.value)}>
                  <MenuItem value="prototypical">Prototypical Networks</MenuItem>
                  <MenuItem value="transfer_learning">Transfer Learning</MenuItem>
                </Select>
              </FormControl>
              <Button variant="contained" component="label" fullWidth disabled={loading}>
                {loading ? <CircularProgress size={20} /> : 'Upload Query Images'}
                <input type="file" hidden multiple accept="image/*" onChange={predictWithImages} />
              </Button>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              {!result ? (
                <Typography color="text.secondary">
                  Upload query images to classify rare esophageal cancer subtypes
                </Typography>
              ) : (
                <Box>
                  <Chip label={`Subtype: ${result.subtype}`} sx={{ mr: 1 }} />
                  <Chip label={`Method: ${result.method}`} sx={{ mr: 1 }} />
                  <Chip label={`Confidence: ${(Number(result.confidence) * 100).toFixed(0)}%`} color="primary" />
                  {(result.predictions as number[])?.length > 0 && (
                    <Typography variant="body2" sx={{ mt: 2 }}>
                      Predictions: {(result.predictions as number[]).join(', ')}
                    </Typography>
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

export function AsyncJobsPanel() {
  const { job, polling, error, submitJob } = useJobPolling()
  const [jobType, setJobType] = useState('inference')
  const [jobHistory, setJobHistory] = useState<JobRecord[]>([])

  const runJob = async () => {
    try {
      const record = await submitJob(jobType, { source: 'ml-models-ui' })
      setJobHistory((prev) => [record, ...prev].slice(0, 10))
    } catch {
      /* error shown via hook */
    }
  }

  const statusColor = (s: string) =>
    s === 'done' ? 'success' : s === 'failed' ? 'error' : s === 'running' ? 'primary' : 'default'

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={2}>
        <WorkIcon sx={{ mr: 1, color: 'warning.main' }} />
        <Typography variant="h6">Async Inference Jobs</Typography>
      </Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Job Type</InputLabel>
                <Select value={jobType} label="Job Type" onChange={(e) => setJobType(e.target.value)}>
                  <MenuItem value="inference">ML Inference</MenuItem>
                  <MenuItem value="mri_processing">MRI Processing</MenuItem>
                  <MenuItem value="report">Report Generation</MenuItem>
                </Select>
              </FormControl>
              <Button
                fullWidth
                variant="contained"
                startIcon={polling ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
                onClick={runJob}
                disabled={polling}
              >
                Submit Job
              </Button>
              {job && (
                <Box mt={2}>
                  <Typography variant="caption">Current Job: {job.job_id}</Typography>
                  <LinearProgress sx={{ mt: 1 }} variant={polling ? 'indeterminate' : 'determinate'} value={job.status === 'done' ? 100 : 50} />
                  <Chip label={job.status} color={statusColor(job.status) as 'success' | 'error' | 'primary' | 'default'} size="small" sx={{ mt: 1 }} />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Job History
              </Typography>
              {jobHistory.length === 0 ? (
                <Typography color="text.secondary">No jobs submitted yet</Typography>
              ) : (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Job ID</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Result</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {jobHistory.map((j) => (
                      <TableRow key={String(j.job_id)}>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {String(j.job_id).slice(0, 12)}…
                        </TableCell>
                        <TableCell>{String(j.type)}</TableCell>
                        <TableCell>
                          <Chip label={String(j.status)} size="small" color={statusColor(String(j.status)) as 'success' | 'error' | 'primary' | 'default'} />
                        </TableCell>
                        <TableCell sx={{ fontSize: '0.75rem' }}>
                          {j.result ? JSON.stringify(j.result).slice(0, 60) : '—'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
