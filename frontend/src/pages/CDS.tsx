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
  Psychology as PsychologyIcon,
  Science as ScienceIcon,
  Assessment as AssessmentIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material'
import api from '../services/api'
import SHAPVisualization from '../components/SHAPVisualization'

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

export default function CDS() {
  const [activeStep, setActiveStep] = useState(0)
  const [tabValue, setTabValue] = useState(0)
  
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

  const steps = [
    {
      label: 'اطلاعات پایه بیمار',
      description: 'سن، جنسیت و شاخص‌های اولیه',
    },
    {
      label: 'عوامل خطر',
      description: 'سیگار، الکل، GERD و سایر عوامل',
    },
    {
      label: 'اطلاعات تومور',
      description: 'مرحله، درجه و مشخصات تومور',
    },
    {
      label: 'پیش‌بینی و توصیه',
      description: 'مشاهده نتایج و توصیه‌ها',
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
    try {
      const response = await api.post('/cds/risk-prediction', {
        patient_data: patientData,
        include_explanation: true,
      })
      setRiskResult(response.data)
      setActiveStep(3) // Move to results step
    } catch (error) {
      console.error('Error predicting risk:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTreatmentRecommendation = async () => {
    setLoading(true)
    try {
      const response = await api.post('/cds/treatment-recommendation', {
        patient_data: patientData,
        cancer_data: cancerData,
      })
      setTreatmentResult(response.data)
    } catch (error) {
      console.error('Error getting recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        پشتیبانی تصمیم‌گیری بالینی
      </Typography>
      <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
        این سیستم به شما کمک می‌کند تا بر اساس اطلاعات بیمار، ریسک و توصیه‌های درمانی را دریافت کنید
      </Typography>

      <Tabs value={tabValue} onChange={(_e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab icon={<AssessmentIcon />} label="گردش کار بالینی" />
        <Tab icon={<VisibilityIcon />} label="حالت شبیه‌سازی" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 3 }}>
          <Stepper activeStep={activeStep} orientation="vertical">
            <Step>
              <StepLabel>{steps[0].label}</StepLabel>
              <StepContent>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  {steps[0].description}
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="سن"
                      type="number"
                      value={patientData.age}
                      onChange={(e) =>
                        setPatientData({ ...patientData, age: parseInt(e.target.value) || 0 })
                      }
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>جنسیت</InputLabel>
                      <Select
                        value={patientData.gender}
                        onChange={(e) =>
                          setPatientData({ ...patientData, gender: e.target.value })
                        }
                      >
                        <MenuItem value="Male">مرد</MenuItem>
                        <MenuItem value="Female">زن</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="BMI"
                      type="number"
                      value={patientData.bmi}
                      onChange={(e) =>
                        setPatientData({ ...patientData, bmi: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </Grid>
                </Grid>
                <Box sx={{ mt: 2 }}>
                  <Button variant="contained" onClick={handleNext}>
                    بعدی
                  </Button>
                </Box>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>{steps[1].label}</StepLabel>
              <StepContent>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
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
                      سیگار: {patientData.smoking ? 'بله' : 'خیر'}
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
                      الکل: {patientData.alcohol ? 'بله' : 'خیر'}
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
                      GERD: {patientData.gerd ? 'بله' : 'خیر'}
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
                      Barrett's Esophagus: {patientData.barretts_esophagus ? 'بله' : 'خیر'}
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
                      سابقه خانوادگی: {patientData.family_history ? 'بله' : 'خیر'}
                    </Button>
                  </Grid>
                </Grid>
                <Box sx={{ mt: 2 }}>
                  <Button onClick={handleBack} sx={{ mr: 1 }}>
                    قبلی
                  </Button>
                  <Button variant="contained" onClick={handleNext}>
                    بعدی
                  </Button>
                </Box>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>{steps[2].label}</StepLabel>
              <StepContent>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  {steps[2].description}
                </Typography>
                <Grid container spacing={2}>
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
                      label="طول تومور (cm)"
                      type="number"
                      value={cancerData.tumor_length_cm}
                      onChange={(e) =>
                        setCancerData({ ...cancerData, tumor_length_cm: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </Grid>
                </Grid>
                <Box sx={{ mt: 2 }}>
                  <Button onClick={handleBack} sx={{ mr: 1 }}>
                    قبلی
                  </Button>
                  <Button variant="contained" onClick={handleNext}>
                    بعدی
                  </Button>
                </Box>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>{steps[3].label}</StepLabel>
              <StepContent>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  {steps[3].description}
                </Typography>
                <Box display="flex" gap={2} sx={{ mb: 3 }}>
                  <Button
                    variant="contained"
                    startIcon={<HospitalIcon />}
                    onClick={handleRiskPrediction}
                    disabled={loading}
                  >
                    پیش‌بینی ریسک
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<ScienceIcon />}
                    onClick={handleTreatmentRecommendation}
                    disabled={loading}
                  >
                    دریافت توصیه‌های درمانی
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
                      sx={{ mb: 2 }}
                    >
                      <Typography variant="h6">
                        امتیاز ریسک: {riskResult.risk_score} ({riskResult.risk_category})
                      </Typography>
                      <Typography>{riskResult.recommendation}</Typography>
                    </Alert>

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
                      توصیه‌های درمانی
                    </Typography>
                    {treatmentResult.recommendations?.slice(0, 5).map((rec: any, idx: number) => (
                      <Card key={idx} sx={{ mt: 1 }}>
                        <CardContent>
                          <Typography variant="subtitle1">
                            {rec.type}: {rec.regimen}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            {rec.rationale}
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}

                <Box sx={{ mt: 2 }}>
                  <Button onClick={handleBack} sx={{ mr: 1 }}>
                    قبلی
                  </Button>
                  <Button variant="outlined" onClick={() => setActiveStep(0)}>
                    شروع مجدد
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
      })
      setRiskResult(response.data)
    } catch (error) {
      console.error('Error predicting risk:', error)
    } finally {
      setLoading(false)
    }
  }, [patientData])

  // Auto-update when autoUpdate is enabled
  useEffect(() => {
    if (autoUpdate && !loading) {
      const timer = setTimeout(() => {
        handleRiskPrediction()
      }, 500) // Debounce 500ms
      return () => clearTimeout(timer)
    }
  }, [patientData, cancerData, autoUpdate, handleRiskPrediction, loading])

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        محیط شبیه‌سازی (Sandbox)
      </Typography>
      <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
        در این محیط می‌توانید با تغییر پارامترهای مختلف بیمار، تأثیر آن‌ها را بر پیش‌بینی ریسک مشاهده کنید
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Button
          variant={autoUpdate ? 'contained' : 'outlined'}
          onClick={() => setAutoUpdate(!autoUpdate)}
          sx={{ mb: 2 }}
        >
          {autoUpdate ? 'غیرفعال کردن به‌روزرسانی خودکار' : 'فعال کردن به‌روزرسانی خودکار'}
        </Button>
        {!autoUpdate && (
          <Button variant="contained" onClick={handleRiskPrediction} disabled={loading} sx={{ ml: 2 }}>
            محاسبه ریسک
          </Button>
        )}
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                اطلاعات بیمار
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="سن"
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
                    <InputLabel>جنسیت</InputLabel>
                    <Select
                      value={patientData.gender}
                      onChange={(e) =>
                        setPatientData({ ...patientData, gender: e.target.value })
                      }
                    >
                      <MenuItem value="Male">مرد</MenuItem>
                      <MenuItem value="Female">زن</MenuItem>
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
                      label={`سیگار: ${patientData.smoking ? 'بله' : 'خیر'}`}
                      color={patientData.smoking ? 'error' : 'default'}
                      onClick={() =>
                        setPatientData({ ...patientData, smoking: !patientData.smoking })
                      }
                    />
                    <Chip
                      label={`الکل: ${patientData.alcohol ? 'بله' : 'خیر'}`}
                      color={patientData.alcohol ? 'error' : 'default'}
                      onClick={() =>
                        setPatientData({ ...patientData, alcohol: !patientData.alcohol })
                      }
                    />
                    <Chip
                      label={`GERD: ${patientData.gerd ? 'بله' : 'خیر'}`}
                      color={patientData.gerd ? 'warning' : 'default'}
                      onClick={() =>
                        setPatientData({ ...patientData, gerd: !patientData.gerd })
                      }
                    />
                    <Chip
                      label={`Barrett's: ${patientData.barretts_esophagus ? 'بله' : 'خیر'}`}
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
                اطلاعات تومور
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
                    label="طول تومور (cm)"
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
                    امتیاز ریسک: {riskResult.risk_score} ({riskResult.risk_category})
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
