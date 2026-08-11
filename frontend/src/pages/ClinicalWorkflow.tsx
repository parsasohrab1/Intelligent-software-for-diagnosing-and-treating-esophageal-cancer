import { useState } from 'react'
import {
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
  FormControlLabel,
  Switch,
} from '@mui/material'
import PersonAddIcon from '@mui/icons-material/PersonAdd'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import MedicationIcon from '@mui/icons-material/Medication'
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import api from '../services/api'
import SHAPVisualization from '../components/SHAPVisualization'
import CDSDataCompletenessAlert, {
  type CDSDataCompleteness,
} from '../components/CDSDataCompletenessAlert'

const STEPS = [
  'Register Patient',
  'Upload MRI',
  'Image Analysis',
  'CDS + SHAP',
  'Treatment Plan',
  'Monitoring',
]

interface WorkflowState {
  patientId: string
  cdsInputs: Record<string, unknown>
  mriResult: Record<string, unknown> | null
  cdsResult: Record<string, unknown> | null
  monitoringResult: Record<string, unknown> | null
}

export default function ClinicalWorkflow() {
  const [activeStep, setActiveStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [completed, setCompleted] = useState<Set<number>>(new Set())

  const [form, setForm] = useState({
    age: 65,
    gender: 'Male',
    ethnicity: 'Caucasian',
    has_cancer: true,
    smoking: false,
    alcohol: false,
    gerd: true,
    bmi: 28,
    barretts_esophagus: false,
    family_history: false,
  })

  const [workflow, setWorkflow] = useState<WorkflowState>({
    patientId: '',
    cdsInputs: {},
    mriResult: null,
    cdsResult: null,
    monitoringResult: null,
  })

  const markComplete = (step: number) => {
    setCompleted((prev) => new Set(prev).add(step))
  }

  const registerPatient = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.post('/workflow/register-patient', form)
      setWorkflow((w) => ({
        ...w,
        patientId: res.data.patient_id,
        cdsInputs: res.data.cds_inputs || {},
      }))
      markComplete(0)
      setActiveStep(1)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Registration failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const uploadMRI = async (file: File) => {
    if (!workflow.patientId) return
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('patient_id', workflow.patientId)
      formData.append('file', file)
      const res = await api.post('/workflow/upload-mri', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })
      setWorkflow((w) => ({ ...w, mriResult: res.data }))
      markComplete(1)
      setActiveStep(2)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'MRI upload failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const confirmAnalysis = () => {
    markComplete(2)
    setActiveStep(3)
  }

  const runCDS = async () => {
    if (!workflow.patientId) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.post(`/workflow/${workflow.patientId}/cds`, {
        cds_inputs: workflow.cdsInputs,
      }, { timeout: 60000 })
      setWorkflow((w) => ({ ...w, cdsResult: res.data }))
      markComplete(3)
      markComplete(4)
      setActiveStep(5)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'CDS analysis failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const loadMonitoring = async () => {
    if (!workflow.patientId) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.get(`/workflow/${workflow.patientId}/monitoring`, { timeout: 60000 })
      setWorkflow((w) => ({ ...w, monitoringResult: res.data }))
      markComplete(5)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Monitoring load failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const risk = workflow.cdsResult?.risk_prediction as Record<string, unknown> | undefined
  const treatment = workflow.cdsResult?.treatment_recommendation as Record<string, unknown> | undefined
  const monitoring = workflow.monitoringResult as Record<string, unknown> | undefined

  return (
    <Box p={3}>
      <Box display="flex" alignItems="center" mb={1}>
        <LocalHospitalIcon sx={{ mr: 1, fontSize: 36, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4">Clinical Workflow</Typography>
          <Typography variant="body2" color="text.secondary">
            End-to-end journey: Register → MRI → Analysis → CDS + SHAP → Treatment → Monitoring
          </Typography>
        </Box>
      </Box>

      {workflow.patientId && (
        <Chip
          label={`Patient: ${workflow.patientId}`}
          color="primary"
          sx={{ mb: 2 }}
          icon={<CheckCircleIcon />}
        />
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Stepper activeStep={activeStep} orientation="vertical">
            {STEPS.map((label, index) => (
              <Step key={label} completed={completed.has(index)}>
                <StepLabel
                  optional={
                    index === 5 && completed.has(5) ? (
                      <Typography variant="caption">Complete</Typography>
                    ) : undefined
                  }
                >
                  {label}
                </StepLabel>
                <StepContent>
                  <Typography variant="caption" color="text.secondary">
                    {index === 0 && 'Create patient record'}
                    {index === 1 && 'Upload MRI scan'}
                    {index === 2 && 'Review image analysis'}
                    {index === 3 && 'Risk prediction with SHAP'}
                    {index === 4 && 'NCCN-based recommendations'}
                    {index === 5 && 'Post-treatment monitoring'}
                  </Typography>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </Grid>

        <Grid item xs={12} md={8}>
          {/* Step 0: Register */}
          {activeStep === 0 && (
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <PersonAddIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Step 1 — Register Patient</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={4}>
                    <TextField
                      fullWidth
                      label="Age"
                      type="number"
                      value={form.age}
                      onChange={(e) => setForm({ ...form, age: Number(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={6} sm={4}>
                    <FormControl fullWidth>
                      <InputLabel>Gender</InputLabel>
                      <Select
                        value={form.gender}
                        label="Gender"
                        onChange={(e) => setForm({ ...form, gender: e.target.value })}
                      >
                        <MenuItem value="Male">Male</MenuItem>
                        <MenuItem value="Female">Female</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="BMI"
                      type="number"
                      value={form.bmi}
                      onChange={(e) => setForm({ ...form, bmi: Number(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={form.has_cancer}
                          onChange={(e) => setForm({ ...form, has_cancer: e.target.checked })}
                        />
                      }
                      label="Has Cancer"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={form.gerd}
                          onChange={(e) => setForm({ ...form, gerd: e.target.checked })}
                        />
                      }
                      label="GERD"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={form.smoking}
                          onChange={(e) => setForm({ ...form, smoking: e.target.checked })}
                        />
                      }
                      label="Smoking"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={form.barretts_esophagus}
                          onChange={(e) =>
                            setForm({ ...form, barretts_esophagus: e.target.checked })
                          }
                        />
                      }
                      label="Barrett's Esophagus"
                    />
                  </Grid>
                </Grid>
                <Button
                  variant="contained"
                  sx={{ mt: 3 }}
                  startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
                  onClick={registerPatient}
                  disabled={loading}
                >
                  Register Patient
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Step 1: Upload MRI */}
          {activeStep === 1 && (
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <UploadFileIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Step 2 — Upload MRI</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Upload an MRI image for patient <strong>{workflow.patientId}</strong>
                </Typography>
                <Button variant="contained" component="label" disabled={loading}>
                  {loading ? <CircularProgress size={20} /> : 'Select MRI File'}
                  <input
                    type="file"
                    hidden
                    accept="image/*,.dcm,.nii"
                    onChange={(e) => {
                      const f = e.target.files?.[0]
                      if (f) uploadMRI(f)
                      e.target.value = ''
                    }}
                  />
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Step 2: Analysis */}
          {activeStep === 2 && workflow.mriResult && (
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <AnalyticsIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Step 3 — Image Analysis</Typography>
                </Box>
                <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="subtitle2">Findings</Typography>
                  <Typography variant="body2" paragraph>
                    {String(workflow.mriResult.findings || '—')}
                  </Typography>
                  <Typography variant="subtitle2">Impression</Typography>
                  <Typography variant="body2">
                    {String(workflow.mriResult.impression || '—')}
                  </Typography>
                  <Box mt={2} display="flex" gap={1}>
                    <Chip label={`Image ID: ${workflow.mriResult.image_id}`} size="small" />
                    <Chip label="MRI" size="small" color="primary" />
                  </Box>
                </Paper>
                <Button variant="contained" onClick={confirmAnalysis}>
                  Continue to CDS
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Step 3 & 4: CDS + Treatment (combined run) */}
          {activeStep === 3 && (
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <LocalHospitalIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Step 4 & 5 — CDS + SHAP + Treatment</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Run clinical decision support with explainable AI and generate treatment
                  recommendations based on patient data and MRI findings.
                </Typography>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <MedicationIcon />}
                  onClick={runCDS}
                  disabled={loading}
                >
                  Run CDS & Treatment Recommendation
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Step 5: Results + Monitoring */}
          {activeStep >= 5 && (
            <Box>
              {workflow.cdsResult && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    {(workflow.cdsResult.data_completeness as CDSDataCompleteness) && (
                      <CDSDataCompletenessAlert
                        completeness={workflow.cdsResult.data_completeness as CDSDataCompleteness}
                      />
                    )}
                    {workflow.cdsResult.reliability_notice && (
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        {String(workflow.cdsResult.reliability_notice)}
                      </Alert>
                    )}
                    <Typography variant="h6" gutterBottom>
                      CDS Risk Prediction + SHAP
                    </Typography>
                    <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                      <Chip
                        label={`Risk: ${((risk?.risk_score as number) * 100 || 0).toFixed(0)}%`}
                        color="warning"
                      />
                      <Chip label={`Category: ${risk?.risk_category || '—'}`} />
                    </Box>
                    <SHAPVisualization
                      explanation={risk}
                      prediction={risk?.risk_score as number}
                      riskCategory={risk?.risk_category as string}
                    />
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Treatment Recommendation
                    </Typography>
                    {treatment?.primary_recommendation ? (
                      <Alert severity="info" sx={{ mb: 1 }}>
                        {String(treatment.primary_recommendation)}
                      </Alert>
                    ) : null}
                    <List dense>
                      {(treatment?.recommendations as Array<Record<string, unknown>>)?.map(
                        (rec, i) => (
                          <ListItem key={i}>
                            <ListItemText
                              primary={String(rec.treatment || rec.name || rec.regimen || `Option ${i + 1}`)}
                              secondary={String(rec.rationale || rec.description || '')}
                            />
                          </ListItem>
                        )
                      ) || (
                        <ListItem>
                          <ListItemText
                            primary={String(treatment?.recommended_regimen || 'See CDS output')}
                            secondary={String(treatment?.rationale || '')}
                          />
                        </ListItem>
                      )}
                    </List>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <MonitorHeartIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Step 6 — Patient Monitoring</Typography>
                  </Box>
                  {!workflow.monitoringResult ? (
                    <Button
                      variant="contained"
                      onClick={loadMonitoring}
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <MonitorHeartIcon />}
                    >
                      Load Monitoring Dashboard
                    </Button>
                  ) : (
                    <Box>
                      <Box display="flex" gap={1} mb={2}>
                        <Chip
                          label={`Status: ${monitoring?.overall_status || '—'}`}
                          color={
                            monitoring?.overall_status === 'stable'
                              ? 'success'
                              : monitoring?.overall_status === 'critical'
                                ? 'error'
                                : 'warning'
                          }
                        />
                      </Box>
                      {(monitoring?.alerts as string[])?.length > 0 && (
                        <Alert severity="warning" sx={{ mb: 2 }}>
                          {(monitoring?.alerts as string[]).join(' • ')}
                        </Alert>
                      )}
                      <Grid container spacing={2}>
                        {['vital_signs', 'lab_results', 'clinical_parameters'].map((section) => {
                          const params = monitoring?.[section] as Array<Record<string, unknown>> | undefined
                          if (!params?.length) return null
                          return (
                            <Grid item xs={12} md={4} key={section}>
                              <Paper variant="outlined" sx={{ p: 1.5 }}>
                                <Typography variant="subtitle2" textTransform="capitalize" gutterBottom>
                                  {section.replace(/_/g, ' ')}
                                </Typography>
                                <List dense>
                                  {params.slice(0, 4).map((p, i) => (
                                    <ListItem key={i} sx={{ py: 0 }}>
                                      <ListItemText
                                        primary={String(p.name)}
                                        secondary={`${p.value ?? '—'} ${p.unit || ''} (${p.status})`}
                                      />
                                    </ListItem>
                                  ))}
                                </List>
                              </Paper>
                            </Grid>
                          )
                        })}
                      </Grid>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}
