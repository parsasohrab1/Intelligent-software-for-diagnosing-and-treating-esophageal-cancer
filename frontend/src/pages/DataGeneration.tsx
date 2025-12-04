import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
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
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import RefreshIcon from '@mui/icons-material/Refresh'
import CloudDownloadIcon from '@mui/icons-material/CloudDownload'
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

export default function DataGeneration() {
  const navigate = useNavigate()
  const [tabValue, setTabValue] = useState(0)
  const [nPatients, setNPatients] = useState(100)
  const [cancerRatio, setCancerRatio] = useState(0.4)
  const [seed, setSeed] = useState(42)
  const [saveToDb, setSaveToDb] = useState(true)  // Default to true
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  
  // Collected datasets state
  const [collectedDatasets, setCollectedDatasets] = useState<any[]>([])
  const [loadingDatasets, setLoadingDatasets] = useState(false)
  const [importingDataset, setImportingDataset] = useState<string | null>(null)
  const [datasetError, setDatasetError] = useState<string | null>(null)

  // Load collected datasets on mount and when tab changes
  useEffect(() => {
    if (tabValue === 1) {
      fetchCollectedDatasets()
    }
  }, [tabValue])

  const fetchCollectedDatasets = async () => {
    setLoadingDatasets(true)
    try {
      // Try to get from metadata first
      let datasets: any[] = []
      try {
        const metadataResponse = await api.get('/data-collection/metadata', {
          params: { limit: 10000 }, // Increase limit to get all datasets
          timeout: 30000, // 30 seconds
        })
        const metadataDatasets = metadataResponse.data.results || metadataResponse.data || []
        datasets = Array.isArray(metadataDatasets) ? metadataDatasets : []
        console.log(`Found ${datasets.length} datasets from metadata`)
      } catch (error: any) {
        console.warn('Could not fetch metadata:', error.message || error)
        // Continue to try files list
      }

      // Also get file list from collected_data directory
      try {
        const filesResponse = await api.get('/data-collection/collected-files', {
          timeout: 30000, // 30 seconds
        })
        const files = filesResponse.data.files || filesResponse.data || []
        console.log(`Found ${files.length} files from collected_data directory`)
        
        // Merge files with metadata, avoiding duplicates
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
        // Continue with metadata only
      }

      console.log(`Total datasets after merge: ${datasets.length}`)
      setCollectedDatasets(datasets)
      setDatasetError(null)
    } catch (error: any) {
      console.error('Error fetching collected datasets:', error)
      setCollectedDatasets([])
      setDatasetError(error.message || 'Failed to load collected datasets. Please check backend connection.')
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
        timeout: 300000, // 5 minutes for data generation
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
      } else {
        errorMessage += 'Unknown error occurred.'
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

  const handleImportDataset = async (datasetPath: string, source?: string) => {
    setImportingDataset(datasetPath)
    try {
      const response = await api.post('/data-collection/import-to-database', {
        dataset_path: datasetPath,
        source: source,
      })
      alert(`✅ Successfully imported ${response.data.imported_count} patients!`)
      // Refresh datasets list
      await fetchCollectedDatasets()
    } catch (error: any) {
      console.error('Error importing dataset:', error)
      alert(`Error importing dataset: ${error.response?.data?.detail || error.message}`)
    } finally {
      setImportingDataset(null)
    }
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Data Generation & Import
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Generate Synthetic Data" />
          <Tab label="Import Real Collected Data" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>

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
                      <Typography>
                        <strong>Total Patients:</strong> {result.n_patients || 0}
                      </Typography>
                      <Typography>
                        <strong>Cancer Patients:</strong> {result.n_cancer || 0}
                      </Typography>
                      <Typography>
                        <strong>Normal Patients:</strong> {result.n_normal || 0}
                      </Typography>
                      {result.generation_time !== undefined && (
                        <Typography>
                          <strong>Generation Time:</strong> {result.generation_time}s
                        </Typography>
                      )}
                      {result.validation_status && (
                        <Typography>
                          <strong>Validation Status:</strong> {result.validation_status}
                        </Typography>
                      )}
                      {result.quality_score !== undefined && (
                        <Typography>
                          <strong>Quality Score:</strong> {result.quality_score}/100
                        </Typography>
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

      <TabPanel value={tabValue} index={1}>
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Collected Datasets
            </Typography>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchCollectedDatasets}
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
            <Alert 
              severity="info" 
              action={
                <Button 
                  color="inherit" 
                  size="small" 
                  startIcon={<CloudDownloadIcon />}
                  onClick={() => navigate('/data-collection')}
                >
                  Go to Data Collection
                </Button>
              }
            >
              <Typography variant="body1" gutterBottom>
                No collected datasets found.
              </Typography>
              <Typography variant="body2">
                Go to the Data Collection page to collect data from external sources (TCGA, GEO, Kaggle, etc.).
              </Typography>
              {datasetError && (
                <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                  Error: {datasetError}
                </Typography>
              )}
            </Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Dataset ID</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>File Size</TableCell>
                    <TableCell>File Path</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {collectedDatasets.map((dataset: any) => (
                    <TableRow key={dataset.dataset_id || dataset._id}>
                      <TableCell>
                        {dataset.dataset_id || dataset._id || 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={dataset.source?.toUpperCase() || 'Unknown'} 
                          size="small"
                          color={dataset.source === 'tcga' ? 'primary' : dataset.source === 'geo' ? 'secondary' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        {dataset.title || dataset.description || 'No title'}
                      </TableCell>
                      <TableCell>
                        {dataset.size_mb ? `${dataset.size_mb} MB` : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                          {dataset.output_files?.[0] || dataset.file_path || 'N/A'}
                        </Typography>
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
        </Box>
      </TabPanel>
    </Box>
  )
}

