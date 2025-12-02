import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import api from '../services/api'

interface Model {
  model_id: string
  model_name: string
  model_type: string
  metrics: {
    accuracy: number
    roc_auc: number
  }
  created_at: string
  status: string
}

export default function MLModels() {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    try {
      const response = await api.get('/ml-models/models')
      setModels(response.data.models || [])
    } catch (error) {
      console.error('Error fetching models:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Machine Learning Models</Typography>
        <Button variant="contained" startIcon={<PlayArrowIcon />}>
          Train New Model
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Model ID</TableCell>
              <TableCell>Model Type</TableCell>
              <TableCell>Accuracy</TableCell>
              <TableCell>ROC AUC</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {models.map((model) => (
              <TableRow key={model.model_id}>
                <TableCell>{model.model_id}</TableCell>
                <TableCell>{model.model_type}</TableCell>
                <TableCell>
                  {(model.metrics?.accuracy * 100).toFixed(2)}%
                </TableCell>
                <TableCell>
                  {model.metrics?.roc_auc?.toFixed(3) || 'N/A'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={model.status}
                    color={model.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {new Date(model.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <Button size="small" variant="outlined">
                    Use
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

