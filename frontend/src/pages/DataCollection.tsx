import { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material'
import CloudDownloadIcon from '@mui/icons-material/CloudDownload'
import api from '../services/api'

export default function DataCollection() {
  const [source, setSource] = useState('tcga')
  const [query, setQuery] = useState('esophageal cancer')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleCollect = async () => {
    setLoading(true)
    setResult(null)
    try {
      const response = await api.post('/data-collection/collect', {
        source: source,
        query: query,
        auto_download: false,
      })
      setResult(response.data)
    } catch (error) {
      console.error('Error collecting data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Data Collection
      </Typography>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Data Source</InputLabel>
              <Select value={source} onChange={(e) => setSource(e.target.value)}>
                <MenuItem value="tcga">TCGA</MenuItem>
                <MenuItem value="geo">GEO</MenuItem>
                <MenuItem value="kaggle">Kaggle</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<CloudDownloadIcon />}
              onClick={handleCollect}
              disabled={loading}
            >
              Collect Data
            </Button>

            {loading && (
              <Box display="flex" justifyContent="center">
                <CircularProgress />
              </Box>
            )}

            {result && (
              <Alert severity="success">
                <Typography variant="h6">{result.message}</Typography>
                <Typography>Discovered: {result.datasets_discovered}</Typography>
                <Typography>Processed: {result.datasets_processed}</Typography>
              </Alert>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

