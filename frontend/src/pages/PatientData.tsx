import { useState, useEffect } from 'react'
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
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Autocomplete,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import RefreshIcon from '@mui/icons-material/Refresh'
import CloudDownloadIcon from '@mui/icons-material/CloudDownload'
import StorageIcon from '@mui/icons-material/Storage'
import DatasetIcon from '@mui/icons-material/Dataset'
import AssessmentIcon from '@mui/icons-material/Assessment'
import api from '../services/api'

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
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

interface AggregatedStats {
  summary: {
    total_datasets: number
    total_files: number
    total_size_mb: number
    total_size_gb: number
    average_file_size_mb: number
    latest_collection_date: string | null
  }
  by_source: {
    counts: Record<string, number>
    details: Record<string, { count: number; total_size_mb: number }>
    metadata_counts: Record<string, number>
  }
  by_data_type: {
    file_types: Record<string, number>
    metadata_types: Record<string, number>
  }
  quality_metrics: {
    average_quality_score: number | null
    datasets_with_quality: number
  }
  collection_activity: {
    sources_active: number
    files_collected: number
    last_update: string | null
  }
  patient_statistics?: {
    total_patients: number
    cancer_patients: number
    normal_patients: number
  } | null
}

export default function PatientData() {
  const [tabValue, setTabValue] = useState(0)
  
  // Generate Synthetic Data state
  const [nPatients, setNPatients] = useState(100)
  const [cancerRatio, setCancerRatio] = useState(0.4)
  const [seed, setSeed] = useState(42)
  const [saveToDb, setSaveToDb] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  
  // Collect Data state (removed - no longer needed)
  
  // Collected datasets state
  const [collectedDatasets, setCollectedDatasets] = useState<any[]>([])
  const [loadingDatasets, setLoadingDatasets] = useState(false)
  const [importingDataset, setImportingDataset] = useState<string | null>(null)
  const [datasetError, setDatasetError] = useState<string | null>(null)
  
  // Statistics state
  const [aggregatedStats, setAggregatedStats] = useState<AggregatedStats | null>(null)
  const [loadingStats, setLoadingStats] = useState(true)

  // Load data based on active tab
  useEffect(() => {
    if (tabValue === 1) {
      // Real Data tab - load both datasets and stats
      fetchCollectedDatasets()
      fetchAggregatedStats()
    }
    if (tabValue === 2) {
      // Statistics tab
      fetchAggregatedStats()
    }
  }, [tabValue])

  const fetchAggregatedStats = async () => {
    setLoadingStats(true)
    try {
      // Try to fetch from multiple sources
      const [statsRes, patientsRes] = await Promise.allSettled([
        api.get('/data-collection/aggregated-statistics', { timeout: 15000 }),
        api.get('/patients/dashboard/stats', { timeout: 10000 }),
      ])

      let dataCollectionStats: any = null
      let patientStats: any = null

      if (statsRes.status === 'fulfilled' && statsRes.value?.data) {
        dataCollectionStats = statsRes.value.data
      }

      if (patientsRes.status === 'fulfilled' && patientsRes.value?.data) {
        patientStats = patientsRes.value.data
      }

      // Merge statistics
      const mergedStats = {
        summary: {
          total_datasets: dataCollectionStats?.summary?.total_datasets || 0,
          total_files: dataCollectionStats?.summary?.total_files || 0,
          total_size_mb: dataCollectionStats?.summary?.total_size_mb || 0,
          total_size_gb: dataCollectionStats?.summary?.total_size_gb || 0,
          average_file_size_mb: dataCollectionStats?.summary?.average_file_size_mb || 0,
          latest_collection_date: dataCollectionStats?.summary?.latest_collection_date || null,
        },
        by_source: dataCollectionStats?.by_source || { counts: {}, details: {}, metadata_counts: {} },
        by_data_type: dataCollectionStats?.by_data_type || { file_types: {}, metadata_types: {} },
        quality_metrics: dataCollectionStats?.quality_metrics || { average_quality_score: null, datasets_with_quality: 0 },
        collection_activity: dataCollectionStats?.collection_activity || { sources_active: 0, files_collected: 0, last_update: null },
        patient_statistics: patientStats ? {
          total_patients: patientStats.total_patients || 0,
          cancer_patients: patientStats.cancer_patients || 0,
          normal_patients: patientStats.normal_patients || 0,
        } : null,
      }

      setAggregatedStats(mergedStats)
    } catch (error: any) {
      console.error('Error fetching aggregated statistics:', error)
      // Set default stats with patient data if available
      setAggregatedStats({
        summary: {
          total_datasets: 0,
          total_files: 0,
          total_size_mb: 0,
          total_size_gb: 0,
          average_file_size_mb: 0,
          latest_collection_date: null,
        },
        by_source: { counts: {}, details: {}, metadata_counts: {} },
        by_data_type: { file_types: {}, metadata_types: {} },
        quality_metrics: { average_quality_score: null, datasets_with_quality: 0 },
        collection_activity: { sources_active: 0, files_collected: 0, last_update: null },
        patient_statistics: null,
      })
    } finally {
      setLoadingStats(false)
    }
  }

  const fetchCollectedDatasets = async () => {
    setLoadingDatasets(true)
    try {
      let datasets: any[] = []
      try {
        const metadataResponse = await api.get('/data-collection/metadata', {
          params: { limit: 10000 },
          timeout: 30000,
        })
        const metadataDatasets = metadataResponse.data.results || metadataResponse.data || []
        datasets = Array.isArray(metadataDatasets) ? metadataDatasets : []
      } catch (error: any) {
        console.warn('Could not fetch metadata:', error.message || error)
      }

      try {
        const filesResponse = await api.get('/data-collection/collected-files', {
          timeout: 30000,
        })
        const files = filesResponse.data.files || filesResponse.data || []
        
        const filePaths = new Set(datasets.map((d: any) => d.file_path || d.output_files?.[0] || d.dataset_id))
        
        files.forEach((file: any) => {
          const filePath = file.file_path || file.output_files?.[0]
          if (filePath && !filePaths.has(filePath)) {
            datasets.push({
              dataset_id: file.dataset_id || file.file_name || `file_${filePath}`,
              file_path: filePath,
              source: file.source || 'unknown',
              title: file.title || file.file_name || filePath.split('/').pop() || filePath.split('\\').pop(),
              output_files: [filePath],
              size_mb: file.size_mb || (file.size_bytes ? Math.round(file.size_bytes / (1024 * 1024) * 100) / 100 : null),
              modified_at: file.modified_at || file.modified_date,
            })
            filePaths.add(filePath)
          }
        })
      } catch (error: any) {
        console.warn('Could not fetch collected files:', error.message || error)
      }

      setCollectedDatasets(datasets)
      setDatasetError(null)
    } catch (error: any) {
      console.error('Error fetching collected datasets:', error)
      setCollectedDatasets([])
      setDatasetError(error.message || 'Failed to load collected datasets.')
    } finally {
      setLoadingDatasets(false)
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setResult(null)
    try {
      const response = await api.post('/synthetic-data/generate', {
        n_patients: nPatients,
        cancer_ratio: cancerRatio,
        seed: seed,
        save_to_db: saveToDb,
      }, {
        timeout: 300000,
      })
      setResult(response.data)
    } catch (error: any) {
      console.error('Error generating data:', error)
      let errorMessage = 'Failed to generate data. '
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage += 'The operation timed out. Please try with fewer patients or check your connection.'
      } else if (error.response?.data?.detail) {
        errorMessage += error.response.data.detail
      } else if (error.message) {
        errorMessage += error.message
      }
      alert(errorMessage)
      setResult({
        message: 'Generation failed',
        error: errorMessage,
      })
    } finally {
      setLoading(false)
    }
  }

  // handleCollect function removed - collect button no longer available

  const handleImportDataset = async (datasetPath: string, source?: string) => {
    setImportingDataset(datasetPath)
    try {
      const response = await api.post('/data-collection/import-to-database', {
        dataset_path: datasetPath,
        source: source,
      })
      alert(`✅ Successfully imported ${response.data.imported_count} patients!`)
      await fetchCollectedDatasets()
    } catch (error: any) {
      console.error('Error importing dataset:', error)
      alert(`Error importing dataset: ${error.response?.data?.detail || error.message}`)
    } finally {
      setImportingDataset(null)
    }
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Patient Data Management
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Generate synthetic patient data, collect real data from external sources, and view comprehensive statistics
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Synthetic Data" />
          <Tab label="Real Data" />
          <Tab label="Statistics & Indicators" />
        </Tabs>
      </Box>

      {/* Tab 1: Generate Synthetic Data */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
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
                    fullWidth
                  />
                  <TextField
                    label="Cancer Ratio"
                    type="number"
                    inputProps={{ step: 0.1, min: 0, max: 1 }}
                    value={cancerRatio}
                    onChange={(e) => setCancerRatio(parseFloat(e.target.value))}
                    fullWidth
                  />
                  <TextField
                    label="Random Seed"
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value))}
                    fullWidth
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
                    fullWidth
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
                  {result.error ? (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      {result.error}
                    </Alert>
                  ) : (
                    <>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        {result.message}
                      </Alert>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Typography><strong>Total Patients:</strong> {result.n_patients || 0}</Typography>
                        <Typography><strong>Cancer Patients:</strong> {result.n_cancer || 0}</Typography>
                        <Typography><strong>Normal Patients:</strong> {result.n_normal || 0}</Typography>
                        {result.generation_time !== undefined && (
                          <Typography><strong>Generation Time:</strong> {result.generation_time}s</Typography>
                        )}
                        {result.quality_score !== undefined && (
                          <Typography><strong>Quality Score:</strong> {result.quality_score}/100</Typography>
                        )}
                      </Box>
                    </>
                  )}
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>
      </TabPanel>

      {/* Tab 2: Real Data - All Data Sources Combined */}
      <TabPanel value={tabValue} index={1}>
        <Box>
          {/* All Collected Datasets with Full Details */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box>
                  <Typography variant="h6">All Data Sources - Combined View</Typography>
                  {!loadingDatasets && collectedDatasets.length > 0 && (
                    <Typography variant="body2" color="text.secondary">
                      Showing {collectedDatasets.length} dataset{collectedDatasets.length !== 1 ? 's' : ''} from all sources with complete details
                    </Typography>
                  )}
                </Box>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => {
                    fetchCollectedDatasets()
                    fetchAggregatedStats()
                  }}
                  disabled={loadingDatasets}
                >
                  Refresh
                </Button>
              </Box>

              {loadingDatasets ? (
                <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                  <CircularProgress />
                </Box>
              ) : collectedDatasets.length === 0 ? (
                <Alert severity="info">
                  <Typography variant="body1" gutterBottom>
                    No collected datasets found.
                  </Typography>
                  <Typography variant="body2">
                    Data from all sources (TCGA, GEO, Kaggle, etc.) will appear here when available.
                  </Typography>
                  {datasetError && (
                    <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                      Error: {datasetError}
                    </Typography>
                  )}
                </Alert>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Dataset ID</strong></TableCell>
                        <TableCell><strong>Source</strong></TableCell>
                        <TableCell><strong>Title/Description</strong></TableCell>
                        <TableCell><strong>Data Type</strong></TableCell>
                        <TableCell><strong>File Size</strong></TableCell>
                        <TableCell><strong>Modified Date</strong></TableCell>
                        <TableCell><strong>File Path</strong></TableCell>
                        <TableCell><strong>Quality Score</strong></TableCell>
                        <TableCell align="right"><strong>Actions</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {collectedDatasets.map((dataset: any) => (
                        <TableRow key={dataset.dataset_id || dataset._id} hover>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                              {dataset.dataset_id || dataset._id || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={dataset.source?.toUpperCase() || 'Unknown'} 
                              size="small"
                              color={dataset.source === 'tcga' ? 'primary' : dataset.source === 'geo' ? 'secondary' : 'default'}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {dataset.title || dataset.description || 'No title'}
                            </Typography>
                            {dataset.description && dataset.title && dataset.description !== dataset.title && (
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                {dataset.description}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {dataset.data_type ? (
                              <Chip 
                                label={dataset.data_type} 
                                size="small" 
                                color="primary"
                                variant="outlined"
                              />
                            ) : (
                              <Typography variant="body2" color="text.secondary">N/A</Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {dataset.size_mb ? (
                              <Typography variant="body2">
                                {dataset.size_mb.toFixed(2)} MB
                              </Typography>
                            ) : dataset.size_bytes ? (
                              <Typography variant="body2">
                                {(dataset.size_bytes / (1024 * 1024)).toFixed(2)} MB
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="text.secondary">N/A</Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {dataset.modified_at || dataset.modified_date ? (
                              <Typography variant="body2">
                                {new Date(dataset.modified_at || dataset.modified_date).toLocaleDateString()}
                              </Typography>
                            ) : dataset.created_at ? (
                              <Typography variant="body2">
                                {new Date(dataset.created_at).toLocaleDateString()}
                              </Typography>
                            ) : (
                              'N/A'
                            )}
                          </TableCell>
                          <TableCell>
                            <Tooltip title={dataset.output_files?.[0] || dataset.file_path || 'N/A'}>
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontFamily: 'monospace', 
                                  fontSize: '0.75rem',
                                  maxWidth: '300px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {dataset.output_files?.[0] || dataset.file_path || 'N/A'}
                              </Typography>
                            </Tooltip>
                            {dataset.output_files && dataset.output_files.length > 1 && (
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                +{dataset.output_files.length - 1} more file{dataset.output_files.length - 1 !== 1 ? 's' : ''}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {dataset.quality_score !== undefined && dataset.quality_score !== null ? (
                              <Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {dataset.quality_score}/100
                                </Typography>
                                <LinearProgress 
                                  variant="determinate" 
                                  value={dataset.quality_score} 
                                  sx={{ mt: 0.5, height: 4, borderRadius: 2 }}
                                  color={dataset.quality_score >= 80 ? 'success' : dataset.quality_score >= 60 ? 'warning' : 'error'}
                                />
                              </Box>
                            ) : (
                              <Typography variant="body2" color="text.secondary">N/A</Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">
                            <Tooltip title="Import to Database">
                              <IconButton
                                color="primary"
                                onClick={() => handleImportDataset(
                                  dataset.output_files?.[0] || dataset.file_path,
                                  dataset.source
                                )}
                                disabled={importingDataset === (dataset.output_files?.[0] || dataset.file_path)}
                              >
                                {importingDataset === (dataset.output_files?.[0] || dataset.file_path) ? (
                                  <CircularProgress size={24} />
                                ) : (
                                  <CloudUploadIcon />
                                )}
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Box>
      </TabPanel>

      {/* Tab 3: Statistics & Indicators */}
      <TabPanel value={tabValue} index={2}>
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">Data Collection Statistics</Typography>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchAggregatedStats}
              disabled={loadingStats}
            >
              Refresh Statistics
            </Button>
          </Box>

          {loadingStats ? (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
              <CircularProgress />
            </Box>
          ) : aggregatedStats ? (
            <Grid container spacing={3}>
              {/* Patient Statistics Section */}
              {aggregatedStats.patient_statistics && (
                <>
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Patient Database Statistics
                        </Typography>
                        <Grid container spacing={3} sx={{ mt: 1 }}>
                          <Grid item xs={12} sm={4}>
                            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                              <Typography variant="h4" fontWeight="bold">
                                {aggregatedStats.patient_statistics.total_patients}
                              </Typography>
                              <Typography variant="body2">
                                Total Patients
                              </Typography>
                            </Paper>
                          </Grid>
                          <Grid item xs={12} sm={4}>
                            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'error.light', color: 'error.contrastText' }}>
                              <Typography variant="h4" fontWeight="bold">
                                {aggregatedStats.patient_statistics.cancer_patients}
                              </Typography>
                              <Typography variant="body2">
                                Cancer Patients
                              </Typography>
                            </Paper>
                          </Grid>
                          <Grid item xs={12} sm={4}>
                            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                              <Typography variant="h4" fontWeight="bold">
                                {aggregatedStats.patient_statistics.normal_patients}
                              </Typography>
                              <Typography variant="body2">
                                Normal Patients
                              </Typography>
                            </Paper>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                </>
              )}

              {/* Data Collection Statistics */}
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <DatasetIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6">Total Datasets</Typography>
                    </Box>
                    <Typography variant="h4" color="primary">
                      {aggregatedStats.summary.total_datasets}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Metadata entries
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <StorageIcon sx={{ mr: 1, color: 'secondary.main' }} />
                      <Typography variant="h6">Total Files</Typography>
                    </Box>
                    <Typography variant="h4" color="secondary">
                      {aggregatedStats.summary.total_files}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Collected files
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <StorageIcon sx={{ mr: 1, color: 'success.main' }} />
                      <Typography variant="h6">Total Size</Typography>
                    </Box>
                    <Typography variant="h4" color="success.main">
                      {aggregatedStats.summary.total_size_gb.toFixed(2)} GB
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {aggregatedStats.summary.total_size_mb.toFixed(2)} MB
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <AssessmentIcon sx={{ mr: 1, color: 'warning.main' }} />
                      <Typography variant="h6">Avg Quality</Typography>
                    </Box>
                    <Typography variant="h4" color="warning.main">
                      {aggregatedStats.quality_metrics.average_quality_score 
                        ? `${aggregatedStats.quality_metrics.average_quality_score.toFixed(1)}/100`
                        : 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {aggregatedStats.quality_metrics.datasets_with_quality} datasets
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Statistics by Source
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Source</TableCell>
                            <TableCell align="right">Files</TableCell>
                            <TableCell align="right">Size (MB)</TableCell>
                            <TableCell align="right">Metadata</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {Object.entries(aggregatedStats.by_source.counts).map(([source, count]) => (
                            <TableRow key={source}>
                              <TableCell>
                                <Chip label={source} size="small" color="primary" />
                              </TableCell>
                              <TableCell align="right">{count}</TableCell>
                              <TableCell align="right">
                                {aggregatedStats.by_source.details[source]?.total_size_mb.toFixed(2) || '0'}
                              </TableCell>
                              <TableCell align="right">
                                {aggregatedStats.by_source.metadata_counts[source] || 0}
                              </TableCell>
                            </TableRow>
                          ))}
                          {Object.keys(aggregatedStats.by_source.counts).length === 0 && (
                            <TableRow>
                              <TableCell colSpan={4} align="center">
                                <Typography variant="body2" color="text.secondary">
                                  No data collected yet
                                </Typography>
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      File & Data Types
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          File Types
                        </Typography>
                        {Object.entries(aggregatedStats.by_data_type.file_types).map(([type, count]) => (
                          <Box key={type} sx={{ mb: 1 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="body2">{type.toUpperCase()}</Typography>
                              <Typography variant="body2" fontWeight="bold">{count}</Typography>
                            </Box>
                            <LinearProgress 
                              variant="determinate" 
                              value={(count / aggregatedStats.summary.total_files) * 100}
                              sx={{ height: 6, borderRadius: 3 }}
                            />
                          </Box>
                        ))}
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Data Types
                        </Typography>
                        {Object.entries(aggregatedStats.by_data_type.metadata_types).map(([type, count]) => (
                          <Box key={type} sx={{ mb: 1 }}>
                            <Chip 
                              label={`${type}: ${count}`} 
                              size="small" 
                              sx={{ mb: 0.5 }}
                            />
                          </Box>
                        ))}
                        {Object.keys(aggregatedStats.by_data_type.metadata_types).length === 0 && (
                          <Typography variant="body2" color="text.secondary">
                            No metadata types
                          </Typography>
                        )}
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Additional Indicators
                    </Typography>
                    <Grid container spacing={3}>
                      <Grid item xs={12} sm={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="primary">
                            {aggregatedStats.summary.average_file_size_mb.toFixed(2)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Avg File Size (MB)
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="secondary">
                            {aggregatedStats.collection_activity.sources_active}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Active Sources
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="success.main">
                            {aggregatedStats.collection_activity.files_collected}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Files Collected
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            Last Update
                          </Typography>
                          <Typography variant="body1">
                            {aggregatedStats.summary.latest_collection_date
                              ? new Date(aggregatedStats.summary.latest_collection_date).toLocaleDateString()
                              : 'Never'}
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : (
            <Alert severity="info">
              <Typography variant="body1" gutterBottom>
                No statistics available yet.
              </Typography>
              <Typography variant="body2">
                Statistics will appear here once you collect data or generate patient data.
              </Typography>
            </Alert>
          )}
        </Box>
      </TabPanel>
    </Box>
  )
}

// Removed Combined Patient Data View Component - functionality merged into Real Data tab
function _CombinedPatientDataViewComponent_Removed() {
  const [patients, setPatients] = useState<any[]>([])
  const [selectedPatientId, setSelectedPatientId] = useState<string>('')
  const [combinedData, setCombinedData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [loadingPatients, setLoadingPatients] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPatientsList()
  }, [])

  useEffect(() => {
    if (selectedPatientId) {
      fetchCombinedData(selectedPatientId)
    }
  }, [selectedPatientId])

  const fetchPatientsList = async () => {
    setLoadingPatients(true)
    try {
      const response = await api.get('/patients/list', { params: { limit: 1000 }, timeout: 15000 })
      const patientsList = Array.isArray(response.data) ? response.data : []
      setPatients(patientsList)
      if (patientsList.length > 0 && !selectedPatientId) {
        setSelectedPatientId(patientsList[0].patient_id)
      }
    } catch (error: any) {
      console.error('Error fetching patients:', error)
      setPatients([])
    } finally {
      setLoadingPatients(false)
    }
  }

  const fetchCombinedData = async (patientId: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(`/patients/${patientId}/combined`, { timeout: 20000 })
      setCombinedData(response.data)
    } catch (error: any) {
      console.error('Error fetching combined data:', error)
      setError(error.response?.data?.detail || error.message || 'Failed to load patient data')
      setCombinedData(null)
    } finally {
      setLoading(false)
    }
  }

  if (loadingPatients) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Select Patient to View Combined Data
          </Typography>
          <Autocomplete
            options={patients}
            getOptionLabel={(option) => `${option.patient_id} - ${option.age}yo ${option.gender}${option.has_cancer ? ' (Cancer)' : ''}`}
            value={patients.find(p => p.patient_id === selectedPatientId) || null}
            onChange={(_, newValue) => {
              if (newValue) {
                setSelectedPatientId(newValue.patient_id)
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Select Patient"
                placeholder="Search by patient ID..."
                fullWidth
              />
            )}
            sx={{ mt: 2 }}
          />
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : combinedData ? (
        <Grid container spacing={3}>
          {/* Patient Info */}
          {combinedData.patient_info && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Patient Information
                  </Typography>
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    <Grid item xs={6} md={3}>
                      <Typography variant="body2" color="text.secondary">Patient ID</Typography>
                      <Typography variant="body1" fontWeight="bold">{combinedData.patient_info.patient_id}</Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="body2" color="text.secondary">Age</Typography>
                      <Typography variant="body1">{combinedData.patient_info.age} years</Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="body2" color="text.secondary">Gender</Typography>
                      <Typography variant="body1">{combinedData.patient_info.gender}</Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="body2" color="text.secondary">Cancer Status</Typography>
                      <Chip
                        label={combinedData.patient_info.has_cancer ? 'Cancer' : 'Normal'}
                        color={combinedData.patient_info.has_cancer ? 'error' : 'success'}
                        size="small"
                      />
                    </Grid>
                    {combinedData.patient_info.cancer_type && (
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary">Cancer Type</Typography>
                        <Typography variant="body1">{combinedData.patient_info.cancer_type}</Typography>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Imaging Data */}
          {combinedData.imaging_data && combinedData.imaging_data.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Imaging Data ({combinedData.imaging_data.length})
                  </Typography>
                  <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 400, mt: 2 }}>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>Modality</TableCell>
                          <TableCell>Date</TableCell>
                          <TableCell>Findings</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {combinedData.imaging_data.map((img: any, idx: number) => (
                          <TableRow key={idx}>
                            <TableCell>
                              <Chip label={img.imaging_modality || 'N/A'} size="small" />
                            </TableCell>
                            <TableCell>
                              {img.imaging_date ? new Date(img.imaging_date).toLocaleDateString() : 'N/A'}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {img.findings || img.impression || 'N/A'}
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Lab Results */}
          {combinedData.lab_results && combinedData.lab_results.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Lab Results ({combinedData.lab_results.length})
                  </Typography>
                  <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 400, mt: 2 }}>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>Date</TableCell>
                          <TableCell>Hemoglobin</TableCell>
                          <TableCell>WBC</TableCell>
                          <TableCell>CEA</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {combinedData.lab_results.map((lab: any, idx: number) => (
                          <TableRow key={idx}>
                            <TableCell>
                              {lab.test_date ? new Date(lab.test_date).toLocaleDateString() : 'N/A'}
                            </TableCell>
                            <TableCell>{lab.hemoglobin || '-'}</TableCell>
                            <TableCell>{lab.wbc_count || '-'}</TableCell>
                            <TableCell>{lab.cea || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Clinical Data */}
          {combinedData.clinical_data && combinedData.clinical_data.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Clinical Notes ({combinedData.clinical_data.length})
                  </Typography>
                  {combinedData.clinical_data.map((clinical: any, idx: number) => (
                    <Box key={idx} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        {clinical.record_date ? new Date(clinical.record_date).toLocaleDateString() : 'No date'}
                      </Typography>
                      {clinical.diagnosis && (
                        <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                          Diagnosis: {clinical.diagnosis}
                        </Typography>
                      )}
                      {clinical.clinical_notes && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {clinical.clinical_notes}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Treatment Data */}
          {combinedData.treatment_data && combinedData.treatment_data.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Treatment History ({combinedData.treatment_data.length})
                  </Typography>
                  {combinedData.treatment_data.map((treatment: any, idx: number) => (
                    <Box key={idx} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2">
                          {treatment.treatment_type || 'Treatment'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {treatment.treatment_date ? new Date(treatment.treatment_date).toLocaleDateString() : 'No date'}
                        </Typography>
                      </Box>
                      {treatment.treatment_details && (
                        <Typography variant="body2">{treatment.treatment_details}</Typography>
                      )}
                      {treatment.response && (
                        <Chip
                          label={`Response: ${treatment.response}`}
                          size="small"
                          color={treatment.response.toLowerCase().includes('positive') ? 'success' : 'default'}
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Genomic Data */}
          {combinedData.genomic_data && combinedData.genomic_data.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Genomic Data ({combinedData.genomic_data.length})
                  </Typography>
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    {combinedData.genomic_data.map((genomic: any, idx: number) => (
                      <Grid item xs={12} md={4} key={idx}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle2" color="text.secondary">
                            {genomic.test_date ? new Date(genomic.test_date).toLocaleDateString() : 'No date'}
                          </Typography>
                          {genomic.pdl1_status && (
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              PD-L1: <strong>{genomic.pdl1_status}</strong>
                            </Typography>
                          )}
                          {genomic.msi_status && (
                            <Typography variant="body2">
                              MSI: <strong>{genomic.msi_status}</strong>
                            </Typography>
                          )}
                          {genomic.mutations && (
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              Mutations: {genomic.mutations}
                            </Typography>
                          )}
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Data Sources Summary */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Data Sources
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                  {combinedData.sources && combinedData.sources.length > 0 ? (
                    combinedData.sources.map((source: string) => (
                      <Chip key={source} label={source.replace('_', ' ').toUpperCase()} color="primary" variant="outlined" />
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">No data sources available</Typography>
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Last updated: {combinedData.timestamp ? new Date(combinedData.timestamp).toLocaleString() : 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {(!combinedData.patient_info && combinedData.imaging_data?.length === 0 && 
            combinedData.lab_results?.length === 0 && combinedData.clinical_data?.length === 0) && (
            <Grid item xs={12}>
              <Alert severity="info">
                No data found for this patient. Data may not be available from all sources.
              </Alert>
            </Grid>
          )}
        </Grid>
      ) : selectedPatientId ? (
        <Alert severity="info">
          Select a patient to view combined data from all sources.
        </Alert>
      ) : null}
    </Box>
  )
}

