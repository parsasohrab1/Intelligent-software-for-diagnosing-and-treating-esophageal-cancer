import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  CircularProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Paper,
  Divider,
} from '@mui/material'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import api from '../services/api'
import { hexToBlobUrl } from '../utils/imageUtils'

interface MarginStandard {
  margin_mm: number
  description: string
}

interface GuidanceResult {
  frame_id: number
  processing_time_ms: number
  tumor_count: number
  depth_estimation: {
    mean_depth_mm: number
    max_depth_mm: number
    min_depth_mm: number
    invasion_level: string
    confidence: number
  }
  safe_margin: {
    margin_distance_mm: number
    resection_area_mm2: number
    safety_score: number
    recommendations: string[]
  }
  segmentation_confidence: number
  overlay_image_base64?: string
}

const ANATOMY_REGIONS = [
  { id: 'cervical', label: 'Cervical', y: 8, color: '#e3f2fd' },
  { id: 'upper', label: 'Upper Thoracic', y: 28, color: '#bbdefb' },
  { id: 'middle', label: 'Middle Thoracic', y: 48, color: '#90caf9' },
  { id: 'lower', label: 'Lower Thoracic', y: 68, color: '#64b5f6' },
  { id: 'gej', label: 'GE Junction', y: 88, color: '#42a5f5' },
]

function EsophagusAnatomyMap({ invasionLevel }: { invasionLevel?: string }) {
  const highlight =
    invasionLevel?.toLowerCase().includes('deep')
      ? 'lower'
      : invasionLevel?.toLowerCase().includes('moderate')
        ? 'middle'
        : invasionLevel?.toLowerCase().includes('superficial')
          ? 'upper'
          : null

  return (
    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
      <Typography variant="subtitle2" gutterBottom fontWeight="bold">
        Esophageal Anatomy Map
      </Typography>
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
        <svg width="120" height="280" viewBox="0 0 120 280">
          {ANATOMY_REGIONS.map((region) => (
            <g key={region.id}>
              <rect
                x="40"
                y={region.y}
                width="40"
                height="18"
                rx="4"
                fill={highlight === region.id ? '#f44336' : region.color}
                stroke={highlight === region.id ? '#b71c1c' : '#1976d2'}
                strokeWidth={highlight === region.id ? 2 : 1}
                opacity={highlight === region.id ? 1 : 0.85}
              />
              <text x="85" y={region.y + 12} fontSize="8" fill="#333">
                {region.label}
              </text>
            </g>
          ))}
          <ellipse cx="60" cy="6" rx="18" ry="6" fill="#ffcdd2" stroke="#e53935" />
          <text x="60" y="8" textAnchor="middle" fontSize="7" fill="#333">
            Pharynx
          </text>
          <ellipse cx="60" cy="272" rx="22" ry="8" fill="#c8e6c9" stroke="#388e3c" />
          <text x="60" y="275" textAnchor="middle" fontSize="7" fill="#333">
            Stomach
          </text>
        </svg>
      </Box>
      {invasionLevel && (
        <Chip
          label={`Invasion: ${invasionLevel}`}
          color="warning"
          size="small"
          sx={{ mt: 1 }}
        />
      )}
    </Paper>
  )
}

export default function SurgicalGuidance() {
  const [endoscopyMode, setEndoscopyMode] = useState('auto')
  const [customMargin, setCustomMargin] = useState<string>('')
  const [marginStandards, setMarginStandards] = useState<Record<string, MarginStandard>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<GuidanceResult | null>(null)
  const [overlayUrl, setOverlayUrl] = useState<string | null>(null)
  const [streaming, setStreaming] = useState(false)
  const [streamFrames, setStreamFrames] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const streamIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    api
      .get('/surgical-guidance/margin-standards')
      .then((res) => setMarginStandards(res.data.margin_standards || {}))
      .catch(() => {})
  }, [])

  useEffect(() => {
    return () => {
      if (overlayUrl) URL.revokeObjectURL(overlayUrl)
      stopStream()
    }
  }, [overlayUrl])

  const processFrame = async (file: File) => {
    setLoading(true)
    setError(null)
    if (overlayUrl) {
      URL.revokeObjectURL(overlayUrl)
      setOverlayUrl(null)
    }

    try {
      const formData = new FormData()
      formData.append('file', file)

      const params: Record<string, string> = { endoscopy_mode: endoscopyMode }
      if (customMargin) params.custom_margin_mm = customMargin

      const response = await api.post<GuidanceResult>('/surgical-guidance/process-frame', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })

      setResult(response.data)
      if (response.data.overlay_image_base64) {
        setOverlayUrl(hexToBlobUrl(response.data.overlay_image_base64))
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err instanceof Error ? err.message : 'Failed to process frame')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) processFrame(file)
    e.target.value = ''
  }

  const stopStream = () => {
    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current)
      streamIntervalRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStreaming(false)
  }

  const startSimulatedStream = () => {
    if (!fileInputRef.current) return
    fileInputRef.current.click()
    setStreaming(true)
    setStreamFrames(0)

    streamIntervalRef.current = setInterval(() => {
      setStreamFrames((n) => n + 1)
    }, 2000)
  }

  const handleStreamFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/surgical-guidance/real-time-stream`

    try {
      const reader = new FileReader()
      reader.onload = async () => {
        await processFrame(file)
        setStreamFrames(1)
      }
      reader.readAsArrayBuffer(file)

      try {
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws
        ws.onopen = () => {
          file.arrayBuffer().then((buf) => {
            if (ws.readyState === WebSocket.OPEN) ws.send(buf)
          })
        }
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          if (!data.error) {
            setResult((prev) => ({
              ...prev,
              ...data,
              depth_estimation: data.depth_estimation,
              safe_margin: data.safe_margin,
            }))
            setStreamFrames((n) => n + 1)
          }
        }
        ws.onerror = () => stopStream()
        ws.onclose = () => setStreaming(false)
      } catch {
        setStreaming(false)
      }
    } catch {
      setError('Real-time stream unavailable; showing single-frame result')
      setStreaming(false)
    }
  }

  const safetyColor =
    (result?.safe_margin?.safety_score ?? 0) >= 0.8
      ? 'success'
      : (result?.safe_margin?.safety_score ?? 0) >= 0.5
        ? 'warning'
        : 'error'

  return (
    <Box p={3}>
      <Box display="flex" alignItems="center" mb={3}>
        <LocalHospitalIcon sx={{ mr: 1, fontSize: 32, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4">Surgical Guidance</Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time tumor boundary detection, depth estimation, and safe resection margins
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configuration
              </Typography>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Endoscopy Mode</InputLabel>
                <Select
                  value={endoscopyMode}
                  label="Endoscopy Mode"
                  onChange={(e) => setEndoscopyMode(e.target.value)}
                >
                  <MenuItem value="auto">Auto</MenuItem>
                  <MenuItem value="nbi">NBI</MenuItem>
                  <MenuItem value="wli">WLI</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                label="Custom Margin (mm)"
                type="number"
                value={customMargin}
                onChange={(e) => setCustomMargin(e.target.value)}
                sx={{ mb: 2 }}
                helperText="Optional override for safe resection margin"
              />
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                hidden
                onChange={streaming ? handleStreamFile : handleFileSelect}
              />
              <Button
                fullWidth
                variant="contained"
                startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <UploadFileIcon />}
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                sx={{ mb: 1 }}
              >
                Upload Endoscopy Frame
              </Button>
              <Button
                fullWidth
                variant="outlined"
                startIcon={streaming ? <StopIcon /> : <PlayArrowIcon />}
                onClick={streaming ? stopStream : startSimulatedStream}
                disabled={loading}
                color={streaming ? 'error' : 'primary'}
              >
                {streaming ? 'Stop Real-Time' : 'Real-Time Guidance'}
              </Button>
              {streaming && (
                <Box mt={2}>
                  <Typography variant="caption" color="text.secondary">
                    Frames processed: {streamFrames}
                  </Typography>
                  <LinearProgress sx={{ mt: 0.5 }} />
                </Box>
              )}
            </CardContent>
          </Card>

          <Box mt={2}>
            <EsophagusAnatomyMap invasionLevel={result?.depth_estimation?.invasion_level} />
          </Box>

          {Object.keys(marginStandards).length > 0 && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Margin Standards
                </Typography>
                <List dense>
                  {Object.entries(marginStandards).map(([key, std]) => (
                    <ListItem key={key} divider>
                      <ListItemText
                        primary={`${key}: ${std.margin_mm} mm`}
                        secondary={std.description}
                        primaryTypographyProps={{ textTransform: 'capitalize' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid item xs={12} md={8}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Segmentation Overlay
                  </Typography>
                  {overlayUrl ? (
                    <Box
                      component="img"
                      src={overlayUrl}
                      alt="Tumor segmentation overlay"
                      sx={{ width: '100%', borderRadius: 1, border: '1px solid #ddd' }}
                    />
                  ) : (
                    <Box
                      sx={{
                        height: 240,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        bgcolor: 'grey.100',
                        borderRadius: 1,
                      }}
                    >
                      <Typography color="text.secondary">Upload a frame to see overlay</Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Analysis Results
                  </Typography>
                  {!result ? (
                    <Typography color="text.secondary">No analysis yet</Typography>
                  ) : (
                    <Box>
                      <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                        <Chip label={`${result.tumor_count} tumor(s)`} size="small" />
                        <Chip
                          label={`${result.processing_time_ms.toFixed(0)} ms`}
                          size="small"
                          color={result.processing_time_ms <= 200 ? 'success' : 'warning'}
                        />
                        <Chip
                          label={`Confidence: ${(result.segmentation_confidence * 100).toFixed(0)}%`}
                          size="small"
                        />
                      </Box>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Depth Estimation
                      </Typography>
                      <Typography variant="body2">
                        Mean: {result.depth_estimation.mean_depth_mm.toFixed(2)} mm | Max:{' '}
                        {result.depth_estimation.max_depth_mm.toFixed(2)} mm
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        Level: {result.depth_estimation.invasion_level}
                      </Typography>
                      <Typography variant="subtitle2" gutterBottom>
                        Safe Margin
                      </Typography>
                      <Typography variant="body2">
                        Distance: {result.safe_margin.margin_distance_mm.toFixed(2)} mm
                      </Typography>
                      <Typography variant="body2">
                        Resection area: {result.safe_margin.resection_area_mm2.toFixed(1)} mm²
                      </Typography>
                      <Box mt={1} mb={2}>
                        <Typography variant="caption">Safety Score</Typography>
                        <LinearProgress
                          variant="determinate"
                          value={result.safe_margin.safety_score * 100}
                          color={safetyColor}
                          sx={{ height: 8, borderRadius: 1 }}
                        />
                      </Box>
                      {result.safe_margin.recommendations?.length > 0 && (
                        <>
                          <Typography variant="subtitle2" gutterBottom>
                            Recommendations
                          </Typography>
                          <List dense>
                            {result.safe_margin.recommendations.map((rec, i) => (
                              <ListItem key={i} sx={{ py: 0 }}>
                                <ListItemText primary={`• ${rec}`} />
                              </ListItem>
                            ))}
                          </List>
                        </>
                      )}
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  )
}
