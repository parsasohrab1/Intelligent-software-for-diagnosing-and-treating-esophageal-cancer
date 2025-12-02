import { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Grid,
  FormControlLabel,
  Checkbox,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import api from '../services/api'

export default function DataGeneration() {
  const [nPatients, setNPatients] = useState(100)
  const [cancerRatio, setCancerRatio] = useState(0.4)
  const [seed, setSeed] = useState(42)
  const [saveToDb, setSaveToDb] = useState(true)  // Default to true
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleGenerate = async () => {
    setLoading(true)
    setResult(null)
    try {
      const response = await api.post('/synthetic-data/generate', {
        n_patients: nPatients,
        cancer_ratio: cancerRatio,
        seed: seed,
        save_to_db: saveToDb,
      })
      setResult(response.data)
    } catch (error) {
      console.error('Error generating data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Synthetic Data Generation
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generation Parameters
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <TextField
                  label="Number of Patients"
                  type="number"
                  value={nPatients}
                  onChange={(e) => setNPatients(parseInt(e.target.value))}
                />
                <TextField
                  label="Cancer Ratio"
                  type="number"
                  inputProps={{ step: 0.1, min: 0, max: 1 }}
                  value={cancerRatio}
                  onChange={(e) => setCancerRatio(parseFloat(e.target.value))}
                />
                <TextField
                  label="Random Seed"
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(parseInt(e.target.value))}
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={saveToDb}
                      onChange={(e) => setSaveToDb(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Save to Database"
                />
                <Button
                  variant="contained"
                  startIcon={<PlayArrowIcon />}
                  onClick={handleGenerate}
                  disabled={loading}
                  size="large"
                >
                  Generate Data
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          {loading && (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
              <CircularProgress />
            </Box>
          )}

          {result && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Generation Results
                </Typography>
                <Alert severity="success" sx={{ mb: 2 }}>
                  {result.message}
                </Alert>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Typography>
                    <strong>Total Patients:</strong> {result.n_patients}
                  </Typography>
                  <Typography>
                    <strong>Cancer Patients:</strong> {result.n_cancer}
                  </Typography>
                  <Typography>
                    <strong>Normal Patients:</strong> {result.n_normal}
                  </Typography>
                  <Typography>
                    <strong>Generation Time:</strong> {result.generation_time}s
                  </Typography>
                  <Typography>
                    <strong>Validation Status:</strong> {result.validation_status}
                  </Typography>
                  <Typography>
                    <strong>Quality Score:</strong> {result.quality_score}/100
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

