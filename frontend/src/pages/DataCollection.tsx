import { useState, useEffect } from 'react'
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
  Grid,
  Paper,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material'
import CloudDownloadIcon from '@mui/icons-material/CloudDownload'
import StorageIcon from '@mui/icons-material/Storage'
import DatasetIcon from '@mui/icons-material/Dataset'
import AssessmentIcon from '@mui/icons-material/Assessment'
import RefreshIcon from '@mui/icons-material/Refresh'
import TextField from '@mui/material/TextField'
import api from '../services/api'

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
}

export default function DataCollection() {
  const [source, setSource] = useState('tcga')
  const [query, setQuery] = useState('esophageal cancer')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [aggregatedStats, setAggregatedStats] = useState<AggregatedStats | null>(null)
  const [loadingStats, setLoadingStats] = useState(true)

  useEffect(() => {
    fetchAggregatedStats()
  }, [])

  const fetchAggregatedStats = async () => {
    setLoadingStats(true)
    try {
      const response = await api.get('/data-collection/aggregated-statistics', {
        timeout: 30000, // 30 seconds for stats
      })
      setAggregatedStats(response.data)
    } catch (error: any) {
      console.error('Error fetching aggregated statistics:', error)
      // Set default empty stats on error
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
      })
    } finally {
      setLoadingStats(false)
    }
  }

  const handleCollect = async () => {
    setLoading(true)
    setResult(null)
    try {
      const response = await api.post('/data-collection/collect', {
        source: source,
        query: query,
        auto_download: false,
      }, {
        timeout: 300000, // 5 minutes for data collection
      })
      setResult(response.data)
      // Refresh statistics after collection
      setTimeout(() => {
        fetchAggregatedStats()
      }, 2000)
    } catch (error: any) {
      console.error('Error collecting data:', error)
      let errorMessage = 'Failed to collect data. '
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage += 'The operation timed out. Please check your connection and try again.'
      } else if (error.response?.data?.detail) {
        errorMessage += error.response.data.detail
      } else if (error.message) {
        errorMessage += error.message
      } else {
        errorMessage += 'Unknown error occurred.'
      }
      setResult({
        message: 'Collection failed',
        error: errorMessage,
        datasets_discovered: 0,
        datasets_processed: 0,
        datasets_failed: 0,
        output_files: [],
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Data Collection
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchAggregatedStats}
          disabled={loadingStats}
        >
          Refresh Statistics
        </Button>
      </Box>

      {/* Aggregated Statistics Section */}
      {loadingStats ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
          <CircularProgress />
        </Box>
      ) : aggregatedStats ? (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Summary Cards */}
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

          {/* Statistics by Source */}
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

          {/* File Types and Data Types */}
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

          {/* Additional Metrics */}
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
      ) : null}

      {/* Data Collection Form */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Collect New Data
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Data Source</InputLabel>
              <Select value={source} onChange={(e) => setSource(e.target.value)}>
                <MenuItem value="tcga">TCGA</MenuItem>
                <MenuItem value="geo">GEO</MenuItem>
                <MenuItem value="kaggle">Kaggle</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Search Query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., esophageal cancer"
              fullWidth
            />
            <Button
              variant="contained"
              startIcon={<CloudDownloadIcon />}
              onClick={handleCollect}
              disabled={loading}
              size="large"
            >
              Collect Data
            </Button>

            {loading && (
              <Box display="flex" justifyContent="center">
                <CircularProgress />
              </Box>
            )}

            {result && (
              <Alert severity={result.error ? "error" : "success"}>
                <Typography variant="h6">{result.message || (result.error ? 'Collection Failed' : 'Collection Successful')}</Typography>
                {result.error ? (
                  <Typography>{result.error}</Typography>
                ) : (
                  <>
                    <Typography>Discovered: {result.datasets_discovered || 0}</Typography>
                    <Typography>Processed: {result.datasets_processed || 0}</Typography>
                    <Typography>Failed: {result.datasets_failed || 0}</Typography>
                    {result.output_files && result.output_files.length > 0 && (
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Output files: {result.output_files.length}
                      </Typography>
                    )}
                  </>
                )}
              </Alert>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

