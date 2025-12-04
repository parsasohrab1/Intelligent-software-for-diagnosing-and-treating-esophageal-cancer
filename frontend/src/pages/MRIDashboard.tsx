import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  CircularProgress,
  Alert,
  Paper,
  Divider,
} from '@mui/material'
import {
  Image as ImageIcon,
  Description as DescriptionIcon,
  CalendarToday as CalendarIcon,
  Person as PersonIcon,
  LocalHospital as HospitalIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import api from '../services/api'

interface MRIReport {
  image_id: number
  patient_id: string
  patient_name: string | null
  imaging_date: string | null
  findings: string | null
  impression: string | null
  tumor_length_cm: number | null
  wall_thickness_cm: number | null
  lymph_nodes_positive: number | null
  contrast_used: boolean
  radiologist_id: string | null
  report_summary: string
  // Patient details
  patient_age?: number | null
  patient_gender?: string | null
  patient_ethnicity?: string | null
  patient_has_cancer?: boolean | null
  patient_cancer_type?: string | null
  patient_cancer_subtype?: string | null
  data_source?: string
}

export default function MRIDashboard() {
  const [mriReports, setMriReports] = useState<MRIReport[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedImage, setSelectedImage] = useState<MRIReport | null>(null)
  const [reportDialogOpen, setReportDialogOpen] = useState(false)

  useEffect(() => {
    loadMRIData()
  }, [])

  const loadMRIData = async () => {
    setLoading(true)
    setError(null)
    try {
      const reportsResponse = await Promise.allSettled([
        api.get('/imaging/mri/reports', { 
          params: { limit: 10000 },
          timeout: 60000 
        }),
      ])
      
      // Handle reports response
      if (reportsResponse[0].status === 'fulfilled') {
        const reportsData = reportsResponse[0].value.data
        setMriReports(Array.isArray(reportsData) ? reportsData : [])
      } else {
        console.warn('Failed to load MRI reports:', reportsResponse[0].reason)
        setMriReports([])
        setError('Error loading MRI data. Please check backend connection.')
      }
    } catch (err: any) {
      console.error('Error loading MRI data:', err)
      setError(err.response?.data?.detail || 'Error loading MRI data')
      setMriReports([])
    } finally {
      setLoading(false)
    }
  }

  const handleViewReport = async (imageId: number) => {
    try {
      const response = await api.get(`/imaging/mri/${imageId}/report`)
      setSelectedImage(response.data)
      setReportDialogOpen(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load report')
    }
  }

  const generateImagePlaceholder = (imageId: number) => {
    // Generate a more realistic MRI placeholder
    // In production, this would be replaced with actual image URLs from storage
    const colors = ['2563eb', 'dc2626', '059669', '7c3aed', 'ea580c']
    const color = colors[imageId % colors.length]
    return `https://via.placeholder.com/400x300/${color}/ffffff?text=MRI+Scan+${imageId}`
  }

  return (
    <Box p={3}>
      <Box mb={4} display="flex" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="h4" gutterBottom>
            <HospitalIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            MRI Imaging Reports
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View and manage MRI images and interpretation reports from all sources (real and synthetic data) with complete patient details
          </Typography>
          {!loading && mriReports.length > 0 && (
            <Box display="flex" gap={2} sx={{ mt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Showing {mriReports.length} MRI report{mriReports.length !== 1 ? 's' : ''} with full details
              </Typography>
              <Chip
                label={`Real: ${mriReports.filter(r => r.data_source === 'Real' || (!r.data_source && !r.patient_id.startsWith('CAN') && !r.patient_id.startsWith('NOR'))).length}`}
                color="success"
                size="small"
                variant="outlined"
              />
              <Chip
                label={`Synthetic: ${mriReports.filter(r => r.data_source === 'Synthetic' || r.patient_id.startsWith('CAN') || r.patient_id.startsWith('NOR')).length}`}
                color="primary"
                size="small"
                variant="outlined"
              />
            </Box>
          )}
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadMRIData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : mriReports.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 3 }}>
          <ImageIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No MRI Images Found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 3 }}>
            No MRI images and reports are available in the database. Import or generate patient data to view MRI images and interpretation reports.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {mriReports.map((report) => (
            <Grid item xs={12} sm={6} md={4} key={report.image_id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardMedia
                  component="img"
                  height="200"
                  image={generateImagePlaceholder(report.image_id)}
                  alt={`MRI Image ${report.image_id}`}
                  sx={{ objectFit: 'cover' }}
                />
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" component="div">
                      Image #{report.image_id}
                    </Typography>
                    <Chip
                      label={report.contrast_used ? 'With Contrast' : 'No Contrast'}
                      color={report.contrast_used ? 'primary' : 'default'}
                      size="small"
                    />
                  </Box>

                  {/* Data Source Indicator */}
                  {(report.data_source || report.patient_id.startsWith('CAN') || report.patient_id.startsWith('NOR')) && (
                    <Box mb={1}>
                      <Chip
                        label={report.data_source || (report.patient_id.startsWith('CAN') || report.patient_id.startsWith('NOR') ? 'Synthetic' : 'Real')}
                        color={report.data_source === 'Synthetic' || report.patient_id.startsWith('CAN') || report.patient_id.startsWith('NOR') ? 'primary' : 'success'}
                        size="small"
                        variant="outlined"
                        sx={{ mb: 1 }}
                      />
                    </Box>
                  )}

                  {/* Patient Information */}
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      <PersonIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                      <strong>Patient ID:</strong> {report.patient_id}
                    </Typography>
                    {report.patient_age !== null && report.patient_age !== undefined && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Age:</strong> {report.patient_age} years
                      </Typography>
                    )}
                    {report.patient_gender && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Gender:</strong> {report.patient_gender}
                      </Typography>
                    )}
                    {report.patient_ethnicity && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Ethnicity:</strong> {report.patient_ethnicity}
                      </Typography>
                    )}
                    {report.patient_cancer_type && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Cancer Type:</strong> {report.patient_cancer_type}
                      </Typography>
                    )}
                    {report.patient_cancer_subtype && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Cancer Subtype:</strong> {report.patient_cancer_subtype}
                      </Typography>
                    )}
                    {report.imaging_date && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <CalendarIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                        <strong>Imaging Date:</strong> {new Date(report.imaging_date).toLocaleDateString()}
                      </Typography>
                    )}
                  </Box>

                  {report.radiologist_id && (
                    <Box mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Radiologist ID:</strong> {report.radiologist_id}
                      </Typography>
                    </Box>
                  )}

                  {report.findings && (
                    <Box mb={2}>
                      <Typography variant="body2" fontWeight="bold" gutterBottom>
                        Findings:
                      </Typography>
                      <Typography 
                        variant="body2" 
                        color="text.secondary"
                        sx={{ 
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          maxHeight: '150px',
                          overflowY: 'auto'
                        }}
                      >
                        {report.findings}
                      </Typography>
                    </Box>
                  )}

                  {report.impression && (
                    <Box mb={2}>
                      <Typography variant="body2" fontWeight="bold" gutterBottom>
                        Impression:
                      </Typography>
                      <Typography 
                        variant="body2" 
                        color="text.secondary"
                        sx={{ 
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          maxHeight: '150px',
                          overflowY: 'auto'
                        }}
                      >
                        {report.impression}
                      </Typography>
                    </Box>
                  )}

                  <Divider sx={{ my: 1.5 }} />

                  <Grid container spacing={1} sx={{ mb: 2 }}>
                    {report.tumor_length_cm !== null && report.tumor_length_cm !== undefined && (
                      <Grid item xs={6}>
                        <Paper sx={{ p: 1, bgcolor: 'error.light', textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary" display="block">
                            Tumor Length
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {report.tumor_length_cm} cm
                          </Typography>
                        </Paper>
                      </Grid>
                    )}

                    {report.wall_thickness_cm !== null && report.wall_thickness_cm !== undefined && (
                      <Grid item xs={6}>
                        <Paper sx={{ p: 1, bgcolor: 'warning.light', textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary" display="block">
                            Wall Thickness
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {report.wall_thickness_cm} cm
                          </Typography>
                        </Paper>
                      </Grid>
                    )}

                    {report.lymph_nodes_positive !== null && report.lymph_nodes_positive !== undefined && (
                      <Grid item xs={6}>
                        <Paper sx={{ p: 1, bgcolor: 'info.light', textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary" display="block">
                            Lymph Nodes
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {report.lymph_nodes_positive} positive
                          </Typography>
                        </Paper>
                      </Grid>
                    )}
                  </Grid>

                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<DescriptionIcon />}
                    onClick={() => handleViewReport(report.image_id)}
                    sx={{ mt: 2 }}
                  >
                    View Full Report
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Report Dialog */}
      <Dialog
        open={reportDialogOpen}
        onClose={() => setReportDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center">
            <DescriptionIcon sx={{ mr: 1 }} />
            Full MRI Report - Image #{selectedImage?.image_id}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedImage && (
            <Box>
              {/* MRI Image Display */}
              <Box mb={3}>
                <CardMedia
                  component="img"
                  height="300"
                  image={generateImagePlaceholder(selectedImage.image_id)}
                  alt={`MRI Image ${selectedImage.image_id}`}
                  sx={{ objectFit: 'contain', bgcolor: 'grey.100', borderRadius: 1 }}
                />
              </Box>

              {/* Data Source */}
              {(selectedImage.data_source || selectedImage.patient_id.startsWith('CAN') || selectedImage.patient_id.startsWith('NOR')) && (
                <Box mb={2}>
                  <Chip
                    label={selectedImage.data_source || (selectedImage.patient_id.startsWith('CAN') || selectedImage.patient_id.startsWith('NOR') ? 'Synthetic' : 'Real')}
                    color={selectedImage.data_source === 'Synthetic' || selectedImage.patient_id.startsWith('CAN') || selectedImage.patient_id.startsWith('NOR') ? 'primary' : 'success'}
                    variant="outlined"
                  />
                </Box>
              )}

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Patient Information
              </Typography>
              <Grid container spacing={2} mb={3}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Patient ID
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {selectedImage.patient_id}
                  </Typography>
                </Grid>
                {selectedImage.patient_age !== null && selectedImage.patient_age !== undefined && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Age
                    </Typography>
                    <Typography variant="body1">
                      {selectedImage.patient_age} years
                    </Typography>
                  </Grid>
                )}
                {selectedImage.patient_gender && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Gender
                    </Typography>
                    <Typography variant="body1">
                      {selectedImage.patient_gender}
                    </Typography>
                  </Grid>
                )}
                {selectedImage.patient_ethnicity && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Ethnicity
                    </Typography>
                    <Typography variant="body1">
                      {selectedImage.patient_ethnicity}
                    </Typography>
                  </Grid>
                )}
                {selectedImage.patient_cancer_type && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Cancer Type
                    </Typography>
                    <Typography variant="body1">
                      {selectedImage.patient_cancer_type}
                    </Typography>
                  </Grid>
                )}
                {selectedImage.patient_cancer_subtype && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Cancer Subtype
                    </Typography>
                    <Typography variant="body1">
                      {selectedImage.patient_cancer_subtype}
                    </Typography>
                  </Grid>
                )}
                {selectedImage.imaging_date && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Imaging Date
                    </Typography>
                    <Typography variant="body1">
                      {new Date(selectedImage.imaging_date).toLocaleDateString()}
                    </Typography>
                  </Grid>
                )}
                {selectedImage.radiologist_id && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Radiologist ID
                    </Typography>
                    <Typography variant="body1">
                      {selectedImage.radiologist_id}
                    </Typography>
                  </Grid>
                )}
              </Grid>

              <Divider sx={{ my: 2 }} />

              {selectedImage.findings && (
                <Box mb={3}>
                  <Typography variant="h6" gutterBottom>
                    Imaging Findings
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {selectedImage.findings}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {selectedImage.impression && (
                <Box mb={3}>
                  <Typography variant="h6" gutterBottom>
                    Impression and Conclusion
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {selectedImage.impression}
                    </Typography>
                  </Paper>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Measurements
              </Typography>
              <Grid container spacing={2}>
                {selectedImage.tumor_length_cm && (
                  <Grid item xs={4}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'error.light' }}>
                      <Typography variant="body2" color="text.secondary">
                        Tumor Length
                      </Typography>
                      <Typography variant="h6">
                        {selectedImage.tumor_length_cm} cm
                      </Typography>
                    </Paper>
                  </Grid>
                )}
                {selectedImage.wall_thickness_cm && (
                  <Grid item xs={4}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light' }}>
                      <Typography variant="body2" color="text.secondary">
                        Wall Thickness
                      </Typography>
                      <Typography variant="h6">
                        {selectedImage.wall_thickness_cm} cm
                      </Typography>
                    </Paper>
                  </Grid>
                )}
                {selectedImage.lymph_nodes_positive !== null && (
                  <Grid item xs={4}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'secondary.light' }}>
                      <Typography variant="body2" color="text.secondary">
                        Lymph Nodes Positive
                      </Typography>
                      <Typography variant="h6">
                        {selectedImage.lymph_nodes_positive}
                      </Typography>
                    </Paper>
                  </Grid>
                )}
              </Grid>

              <Box mt={3} display="flex" gap={2}>
                <Chip
                  label={selectedImage.contrast_used ? 'With Contrast' : 'No Contrast'}
                  color={selectedImage.contrast_used ? 'primary' : 'default'}
                />
                {selectedImage.report_summary && (
                  <Chip
                    label="Full Report"
                    color="info"
                    variant="outlined"
                  />
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReportDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
