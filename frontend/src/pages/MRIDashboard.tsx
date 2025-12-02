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
} from '@mui/icons-material'
import api from '../services/api'

interface MRIImage {
  image_id: number
  patient_id: string
  imaging_date: string | null
  findings: string | null
  impression: string | null
  tumor_length_cm: number | null
  wall_thickness_cm: number | null
  lymph_nodes_positive: number | null
  contrast_used: boolean
  radiologist_id: string | null
}

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
}

export default function MRIDashboard() {
  const [mriImages, setMriImages] = useState<MRIImage[]>([])
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
      const [imagesResponse, reportsResponse] = await Promise.all([
        api.get('/imaging/mri'),
        api.get('/imaging/mri/reports'),
      ])
      setMriImages(imagesResponse.data)
      setMriReports(reportsResponse.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load MRI data')
      console.error('Error loading MRI data:', err)
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
    // Generate a placeholder image URL or use a data URI
    // In production, this would be replaced with actual image URLs from storage
    return `https://via.placeholder.com/400x300?text=MRI+Image+${imageId}`
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  return (
    <Box p={3}>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          <HospitalIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          MRI Report
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View and manage MRI images and reports
        </Typography>
      </Box>

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

                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <PersonIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                    Patient: {report.patient_id}
                  </Typography>
                  {report.patient_name && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Name: {report.patient_name}
                    </Typography>
                  )}
                  {report.imaging_date && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      <CalendarIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                      Date: {new Date(report.imaging_date).toLocaleDateString()}
                    </Typography>
                  )}
                </Box>

                {report.impression && (
                  <Box mb={2}>
                    <Typography variant="body2" fontWeight="bold" gutterBottom>
                      Impression:
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {report.impression.length > 100
                        ? `${report.impression.substring(0, 100)}...`
                        : report.impression}
                    </Typography>
                  </Box>
                )}

                {report.tumor_length_cm && (
                  <Box mb={1}>
                    <Typography variant="body2">
                      <strong>Tumor Length:</strong> {report.tumor_length_cm} cm
                    </Typography>
                  </Box>
                )}

                {report.wall_thickness_cm && (
                  <Box mb={1}>
                    <Typography variant="body2">
                      <strong>Wall Thickness:</strong> {report.wall_thickness_cm} cm
                    </Typography>
                  </Box>
                )}

                {report.lymph_nodes_positive !== null && (
                  <Box mb={2}>
                    <Typography variant="body2">
                      <strong>Lymph Nodes Positive:</strong> {report.lymph_nodes_positive}
                    </Typography>
                  </Box>
                )}

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

      {mriReports.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 3 }}>
          <ImageIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No MRI images found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Generate synthetic data to see MRI images and reports
          </Typography>
        </Paper>
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
            MRI Report - Image #{selectedImage?.image_id}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedImage && (
            <Box>
              <Grid container spacing={2} mb={3}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Patient ID
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {selectedImage.patient_id}
                  </Typography>
                </Grid>
                {selectedImage.patient_name && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Patient Name
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {selectedImage.patient_name}
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
                    Findings
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body1">{selectedImage.findings}</Typography>
                  </Paper>
                </Box>
              )}

              {selectedImage.impression && (
                <Box mb={3}>
                  <Typography variant="h6" gutterBottom>
                    Impression
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body1">{selectedImage.impression}</Typography>
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
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
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
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
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
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Lymph Nodes
                      </Typography>
                      <Typography variant="h6">
                        {selectedImage.lymph_nodes_positive}
                      </Typography>
                    </Paper>
                  </Grid>
                )}
              </Grid>

              <Box mt={3}>
                <Chip
                  label={selectedImage.contrast_used ? 'Contrast Used' : 'No Contrast'}
                  color={selectedImage.contrast_used ? 'primary' : 'default'}
                />
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

