import { useState, useEffect, Fragment } from 'react'
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
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Divider,
  LinearProgress,
  Collapse,
  IconButton,
  Tooltip,
} from '@mui/material'
import ApiIcon from '@mui/icons-material/Api'
import MemoryIcon from '@mui/icons-material/Memory'
import SettingsIcon from '@mui/icons-material/Settings'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import CancelIcon from '@mui/icons-material/Cancel'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import PsychologyIcon from '@mui/icons-material/Psychology'
import RefreshIcon from '@mui/icons-material/Refresh'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import InfoIcon from '@mui/icons-material/Info'
import api from '../services/api'

interface Model {
  model_id?: string
  _id?: string
  model_name?: string
  model_type?: string
  model_path?: string
  metrics?: {
    accuracy?: number
    precision?: number
    recall?: number
    f1_score?: number
    roc_auc?: number
    confusion_matrix?: number[][]
    classification_report?: any
    [key: string]: any
  }
  feature_names?: string[]
  training_config?: {
    [key: string]: any
  }
  baseline_statistics?: {
    [key: string]: {
      mean?: number
      std?: number
      min?: number
      max?: number
    }
  }
  created_at?: string
  updated_at?: string
  status?: string
  [key: string]: any
}

export default function MLModels() {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<Model | null>(null)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/ml-models/models', {
        params: { limit: 10000, status: 'active' },
        timeout: 60000, // 60 seconds for large datasets
      })
      const modelList = response.data.models || response.data || []
      const modelsArray = Array.isArray(modelList) ? modelList : []
      console.log('MLModels: Fetched models:', modelsArray.length)
      console.log('MLModels: Model types:', modelsArray.map(m => m.model_type))
      setModels(modelsArray)
    } catch (error: any) {
      console.error('Error fetching models:', error)
      setError(error.response?.data?.detail || error.message || 'Failed to load ML models')
      setModels([])
    } finally {
      setLoading(false)
    }
  }

  const toggleRowExpansion = (modelId: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(modelId)) {
      newExpanded.delete(modelId)
    } else {
      newExpanded.add(modelId)
    }
    setExpandedRows(newExpanded)
  }

  const handleViewDetails = (model: Model) => {
    setSelectedModel(model)
    setDetailDialogOpen(true)
  }

  // Calculate statistics for indicators
  // Support multiple naming conventions for model types
  const getModelType = (model: Model): string => {
    return (model.model_type || '').toLowerCase().trim()
  }
  
  const modelStats = {
    total: models.length,
    neuralNetwork: models.filter(m => {
      const type = getModelType(m)
      return type === 'neuralnetwork' || type === 'neural_network' || type === 'neural network' || type.includes('neural')
    }).length,
    lightGBM: models.filter(m => {
      const type = getModelType(m)
      return type === 'lightgbm' || type === 'light_gbm' || type === 'light gbm' || type.includes('lightgbm')
    }).length,
    logisticRegression: models.filter(m => {
      const type = getModelType(m)
      return type === 'logisticregression' || type === 'logistic_regression' || type === 'logistic regression' || type.includes('logistic')
    }).length,
    preprocessingEnabled: true, // Always enabled with accuracy optimization
  }
  
  // Debug log
  if (models.length > 0) {
    console.log('MLModels: Model stats:', modelStats)
    console.log('MLModels: Neural Network models:', models.filter(m => {
      const type = getModelType(m)
      return type === 'neuralnetwork' || type === 'neural_network' || type === 'neural network' || type.includes('neural')
    }))
    console.log('MLModels: LightGBM models:', models.filter(m => {
      const type = getModelType(m)
      return type === 'lightgbm' || type === 'light_gbm' || type === 'light gbm' || type.includes('lightgbm')
    }))
    console.log('MLModels: LogisticRegression models:', models.filter(m => {
      const type = getModelType(m)
      return type === 'logisticregression' || type === 'logistic_regression' || type === 'logistic regression' || type.includes('logistic')
    }))
  }

  const apiEndpoint = '/api/v1/ml-models'

  return (
    <Box p={3}>
        {/* Indicators Section */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card sx={{ height: '100%', bgcolor: 'primary.main', color: 'white', boxShadow: 3 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <ApiIcon sx={{ mr: 1 }} />
                  <Typography variant="subtitle2" fontWeight="bold">
                    API Endpoint
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', wordBreak: 'break-all', mb: 1 }}>
                  {apiEndpoint}
                </Typography>
                <Chip 
                  label="Active" 
                  size="small" 
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                  icon={<CheckCircleIcon sx={{ color: 'white !important' }} />}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2.4}>
            <Card sx={{ height: '100%', bgcolor: 'info.main', color: 'white', boxShadow: 3 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <MemoryIcon sx={{ mr: 1 }} />
                  <Typography variant="subtitle2" fontWeight="bold">
                    Neural Network
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold" sx={{ mb: 0.5 }}>
                  {modelStats.neuralNetwork}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Model{modelStats.neuralNetwork !== 1 ? 's' : ''} Available
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2.4}>
            <Card sx={{ height: '100%', bgcolor: modelStats.preprocessingEnabled ? 'success.main' : 'error.main', color: 'white', boxShadow: 3 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <SettingsIcon sx={{ mr: 1 }} />
                  <Typography variant="subtitle2" fontWeight="bold">
                    Data Preprocessing
                  </Typography>
                </Box>
                <Box display="flex" alignItems="center" mt={1} mb={1}>
                  {modelStats.preprocessingEnabled ? (
                    <>
                      <CheckCircleIcon sx={{ mr: 0.5, fontSize: '1.2rem' }} />
                      <Typography variant="body1" fontWeight="bold">
                        Enabled
                      </Typography>
                    </>
                  ) : (
                    <>
                      <CancelIcon sx={{ mr: 0.5, fontSize: '1.2rem' }} />
                      <Typography variant="body1" fontWeight="bold">
                        Disabled
                      </Typography>
                    </>
                  )}
                </Box>
                <Typography variant="body2" sx={{ opacity: 0.9, fontSize: '0.75rem' }}>
                  Feature Scaling & Engineering
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2.4}>
            <Card sx={{ height: '100%', bgcolor: 'warning.main', color: 'white', boxShadow: 3 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <PsychologyIcon sx={{ mr: 1 }} />
                  <Typography variant="subtitle2" fontWeight="bold">
                    LightGBM
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold" sx={{ mb: 0.5 }}>
                  {modelStats.lightGBM}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Model{modelStats.lightGBM !== 1 ? 's' : ''} Available
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2.4}>
            <Card sx={{ height: '100%', bgcolor: 'secondary.main', color: 'white', boxShadow: 3 }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <PsychologyIcon sx={{ mr: 1 }} />
                  <Typography variant="subtitle2" fontWeight="bold">
                    Logistic Regression
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold" sx={{ mb: 0.5 }}>
                  {modelStats.logisticRegression}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Model{modelStats.logisticRegression !== 1 ? 's' : ''} Available
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">
            Machine Learning Models
          </Typography>
          {!loading && models.length > 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Showing {models.length} model{models.length !== 1 ? 's' : ''} with full details
            </Typography>
          )}
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchModels}
            disabled={loading}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<PlayArrowIcon />}
            onClick={() => {
              // Show info about accuracy optimization
              alert('Accuracy optimization is enabled by default. The system will:\n' +
                    '1. Apply feature scaling and preprocessing\n' +
                    '2. Use optimized hyperparameters\n' +
                    '3. Handle class imbalance\n' +
                    '4. Apply early stopping for gradient boosting models\n\n' +
                    'To train a model, use the API endpoint: POST /api/v1/ml-models/train')
            }}
          >
            Train New Model (Optimized)
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : models.length === 0 ? (
        <Card>
          <CardContent>
            <Box
              display="flex"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              sx={{ py: 6 }}
            >
              <PsychologyIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                No ML Models Found
              </Typography>
              <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 3, maxWidth: 500 }}>
                No trained machine learning models are available. Train a new model to start making predictions.
              </Typography>
              <Button
                variant="contained"
                startIcon={<PlayArrowIcon />}
                size="large"
              >
                Train Your First Model
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox" />
                <TableCell><strong>Model ID</strong></TableCell>
                <TableCell><strong>Model Name</strong></TableCell>
                <TableCell><strong>Model Type</strong></TableCell>
                <TableCell align="right"><strong>Accuracy</strong></TableCell>
                <TableCell align="right"><strong>Precision</strong></TableCell>
                <TableCell align="right"><strong>Recall</strong></TableCell>
                <TableCell align="right"><strong>F1 Score</strong></TableCell>
                <TableCell align="right"><strong>ROC AUC</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Created</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {models.map((model) => {
                const modelId = model.model_id || model._id || `model-${Math.random()}`
                const isExpanded = expandedRows.has(modelId)
                const metrics = model.metrics || {}
                
                return (
                  <Fragment key={modelId}>
                    <TableRow>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => toggleRowExpansion(modelId)}
                        >
                          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {modelId || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <strong>{model.model_name || modelId || 'Unnamed Model'}</strong>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={model.model_type || 'Unknown'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="right">
                        {metrics.accuracy !== undefined ? (
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              {(metrics.accuracy * 100).toFixed(2)}%
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={metrics.accuracy * 100}
                              sx={{ mt: 0.5, height: 4, borderRadius: 2 }}
                              color={metrics.accuracy >= 0.8 ? 'success' : metrics.accuracy >= 0.6 ? 'warning' : 'error'}
                            />
                          </Box>
                        ) : (
                          'N/A'
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {metrics.precision !== undefined
                          ? `${(metrics.precision * 100).toFixed(2)}%`
                          : 'N/A'}
                      </TableCell>
                      <TableCell align="right">
                        {metrics.recall !== undefined
                          ? `${(metrics.recall * 100).toFixed(2)}%`
                          : 'N/A'}
                      </TableCell>
                      <TableCell align="right">
                        {metrics.f1_score !== undefined
                          ? `${(metrics.f1_score * 100).toFixed(2)}%`
                          : 'N/A'}
                      </TableCell>
                      <TableCell align="right">
                        {metrics.roc_auc !== undefined
                          ? metrics.roc_auc.toFixed(3)
                          : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={model.status || 'unknown'}
                          color={model.status === 'active' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {model.created_at
                          ? new Date(model.created_at).toLocaleDateString()
                          : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View full details">
                          <IconButton
                            size="small"
                            onClick={() => handleViewDetails(model)}
                          >
                            <InfoIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={12}>
                        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                          <Box sx={{ margin: 2 }}>
                            <Typography variant="h6" gutterBottom>
                              Additional Information
                            </Typography>
                            <Grid container spacing={2}>
                              {model.feature_names && model.feature_names.length > 0 && (
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Features ({model.feature_names.length}):
                                  </Typography>
                                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                    {model.feature_names.slice(0, 10).map((feature, idx) => (
                                      <Chip key={`${modelId}-feature-${idx}`} label={feature} size="small" variant="outlined" />
                                    ))}
                                    {model.feature_names.length > 10 && (
                                      <Chip
                                        key={`${modelId}-more-features`}
                                        label={`+${model.feature_names.length - 10} more`}
                                        size="small"
                                        variant="outlined"
                                        color="secondary"
                                      />
                                    )}
                                  </Box>
                                </Grid>
                              )}
                              {model.model_path && (
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Model Path:
                                  </Typography>
                                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                    {model.model_path}
                                  </Typography>
                                </Grid>
                              )}
                            </Grid>
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </Fragment>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Model Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <PsychologyIcon sx={{ mr: 1 }} />
            Model Details: {selectedModel?.model_name || selectedModel?.model_id || 'Unknown'}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedModel && (
            <Box>
              <Grid container spacing={3} sx={{ mt: 1 }}>
                {/* Basic Information */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Basic Information
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary">
                        Model ID
                      </Typography>
                      <Typography variant="body1" sx={{ fontFamily: 'monospace', mb: 1 }}>
                        {selectedModel.model_id || selectedModel._id || 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary">
                        Model Type
                      </Typography>
                      <Chip
                        label={selectedModel.model_type || 'Unknown'}
                        sx={{ mt: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary">
                        Status
                      </Typography>
                      <Chip
                        label={selectedModel.status || 'unknown'}
                        color={selectedModel.status === 'active' ? 'success' : 'default'}
                        sx={{ mt: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" color="text.secondary">
                        Created At
                      </Typography>
                      <Typography variant="body1" sx={{ mt: 0.5 }}>
                        {selectedModel.created_at
                          ? new Date(selectedModel.created_at).toLocaleString()
                          : 'N/A'}
                      </Typography>
                    </Grid>
                    {selectedModel.model_path && (
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary">
                          Model Path
                        </Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', mt: 0.5 }}>
                          {selectedModel.model_path}
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </Grid>

                {/* Metrics */}
                {selectedModel.metrics && (
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Performance Metrics
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Grid container spacing={2}>
                      {selectedModel.metrics.accuracy !== undefined && (
                        <Grid item xs={12} sm={6} md={4}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Accuracy
                              </Typography>
                              <Typography variant="h5" fontWeight="bold">
                                {(selectedModel.metrics.accuracy * 100).toFixed(2)}%
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={selectedModel.metrics.accuracy * 100}
                                sx={{ mt: 1 }}
                                color={selectedModel.metrics.accuracy >= 0.8 ? 'success' : selectedModel.metrics.accuracy >= 0.6 ? 'warning' : 'error'}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      )}
                      {selectedModel.metrics.precision !== undefined && (
                        <Grid item xs={12} sm={6} md={4}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Precision
                              </Typography>
                              <Typography variant="h5" fontWeight="bold">
                                {(selectedModel.metrics.precision * 100).toFixed(2)}%
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={selectedModel.metrics.precision * 100}
                                sx={{ mt: 1 }}
                                color={selectedModel.metrics.precision >= 0.8 ? 'success' : selectedModel.metrics.precision >= 0.6 ? 'warning' : 'error'}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      )}
                      {selectedModel.metrics.recall !== undefined && (
                        <Grid item xs={12} sm={6} md={4}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Recall
                              </Typography>
                              <Typography variant="h5" fontWeight="bold">
                                {(selectedModel.metrics.recall * 100).toFixed(2)}%
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={selectedModel.metrics.recall * 100}
                                sx={{ mt: 1 }}
                                color={selectedModel.metrics.recall >= 0.8 ? 'success' : selectedModel.metrics.recall >= 0.6 ? 'warning' : 'error'}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      )}
                      {selectedModel.metrics.f1_score !== undefined && (
                        <Grid item xs={12} sm={6} md={4}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                F1 Score
                              </Typography>
                              <Typography variant="h5" fontWeight="bold">
                                {(selectedModel.metrics.f1_score * 100).toFixed(2)}%
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={selectedModel.metrics.f1_score * 100}
                                sx={{ mt: 1 }}
                                color={selectedModel.metrics.f1_score >= 0.8 ? 'success' : selectedModel.metrics.f1_score >= 0.6 ? 'warning' : 'error'}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      )}
                      {selectedModel.metrics.roc_auc !== undefined && (
                        <Grid item xs={12} sm={6} md={4}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                ROC AUC
                              </Typography>
                              <Typography variant="h5" fontWeight="bold">
                                {selectedModel.metrics.roc_auc.toFixed(3)}
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={selectedModel.metrics.roc_auc * 100}
                                sx={{ mt: 1 }}
                                color={selectedModel.metrics.roc_auc >= 0.8 ? 'success' : selectedModel.metrics.roc_auc >= 0.6 ? 'warning' : 'error'}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      )}
                    </Grid>
                  </Grid>
                )}

                {/* Feature Names */}
                {selectedModel.feature_names && selectedModel.feature_names.length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Features ({selectedModel.feature_names.length})
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {selectedModel.feature_names.map((feature, idx) => (
                        <Chip key={`feature-${selectedModel.model_id || selectedModel._id || 'unknown'}-${idx}`} label={feature} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Grid>
                )}

                {/* Training Config */}
                {selectedModel.training_config && Object.keys(selectedModel.training_config).length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Training Configuration
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                      <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {JSON.stringify(selectedModel.training_config, null, 2)}
                      </pre>
                    </Paper>
                  </Grid>
                )}

                {/* Baseline Statistics */}
                {selectedModel.baseline_statistics && Object.keys(selectedModel.baseline_statistics).length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Baseline Statistics
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                      <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {JSON.stringify(selectedModel.baseline_statistics, null, 2)}
                      </pre>
                    </Paper>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

