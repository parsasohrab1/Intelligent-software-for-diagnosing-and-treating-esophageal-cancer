import { useState } from 'react'
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
} from '@mui/material'
import {
  LocalHospital as HospitalIcon,
  Psychology as PsychologyIcon,
  Science as ScienceIcon,
} from '@mui/icons-material'
import api from '../services/api'

export default function CDS() {
  const [patientData, setPatientData] = useState({
    age: 65,
    gender: 'Male',
    smoking: false,
    alcohol: false,
    gerd: false,
    bmi: 28,
  })
  const [riskResult, setRiskResult] = useState<any>(null)
  const [treatmentResult, setTreatmentResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleRiskPrediction = async () => {
    setLoading(true)
    try {
      const response = await api.post('/cds/risk-prediction', {
        patient_data: patientData,
      })
      setRiskResult(response.data)
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
        cancer_data: {
          t_stage: 'T3',
          n_stage: 'N1',
          m_stage: 'M0',
          pdl1_status: 'Positive',
        },
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
        Clinical Decision Support
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Patient Information
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <TextField
                  label="Age"
                  type="number"
                  value={patientData.age}
                  onChange={(e) =>
                    setPatientData({ ...patientData, age: parseInt(e.target.value) })
                  }
                />
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
                <TextField
                  label="BMI"
                  type="number"
                  value={patientData.bmi}
                  onChange={(e) =>
                    setPatientData({ ...patientData, bmi: parseFloat(e.target.value) })
                  }
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Factors
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <Button
                  variant={patientData.smoking ? 'contained' : 'outlined'}
                  onClick={() =>
                    setPatientData({ ...patientData, smoking: !patientData.smoking })
                  }
                >
                  Smoking: {patientData.smoking ? 'Yes' : 'No'}
                </Button>
                <Button
                  variant={patientData.alcohol ? 'contained' : 'outlined'}
                  onClick={() =>
                    setPatientData({ ...patientData, alcohol: !patientData.alcohol })
                  }
                >
                  Alcohol: {patientData.alcohol ? 'Yes' : 'No'}
                </Button>
                <Button
                  variant={patientData.gerd ? 'contained' : 'outlined'}
                  onClick={() =>
                    setPatientData({ ...patientData, gerd: !patientData.gerd })
                  }
                >
                  GERD: {patientData.gerd ? 'Yes' : 'No'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" gap={2}>
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
                <Box display="flex" justifyContent="center" sx={{ mt: 3 }}>
                  <CircularProgress />
                </Box>
              )}

              {riskResult && (
                <Box sx={{ mt: 3 }}>
                  <Alert severity={riskResult.risk_category === 'High' ? 'error' : 'info'}>
                    <Typography variant="h6">
                      Risk Score: {riskResult.risk_score} ({riskResult.risk_category})
                    </Typography>
                    <Typography>{riskResult.recommendation}</Typography>
                  </Alert>
                </Box>
              )}

              {treatmentResult && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Treatment Recommendations
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
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

