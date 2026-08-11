import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
} from '@mui/material'
import SchoolIcon from '@mui/icons-material/School'
import PlayCircleIcon from '@mui/icons-material/PlayCircle'
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import api from '../services/api'

interface TrainingModule {
  module_id: string
  title: string
  description?: string
  training_type: string
  duration_minutes?: number
  difficulty_level?: string
  enrollment_status?: string
  progress?: number
  video_url?: string
  documentation_url?: string
}

interface UserProgress {
  total_enrollments: number
  completed: number
  in_progress: number
  not_started: number
  completion_rate: number
  enrollments: Array<{
    module_id: string
    status: string
    progress: number
    score?: number
  }>
}

interface ActiveModule extends TrainingModule {
  enrollment_id?: string
}

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'warning'> = {
  not_enrolled: 'default',
  not_started: 'default',
  in_progress: 'primary',
  completed: 'success',
  failed: 'warning',
}

export default function Training() {
  const [modules, setModules] = useState<TrainingModule[]>([])
  const [progress, setProgress] = useState<UserProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeModule, setActiveModule] = useState<ActiveModule | null>(null)
  const [enrollmentMap, setEnrollmentMap] = useState<Record<string, string>>({})
  const [actionLoading, setActionLoading] = useState(false)
  const [certificateDialog, setCertificateDialog] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [modulesRes, progressRes] = await Promise.allSettled([
        api.get('/training/modules'),
        api.get('/training/progress'),
      ])

      if (modulesRes.status === 'fulfilled') {
        setModules(modulesRes.value.data.modules || [])
      } else {
        setModules([])
      }

      if (progressRes.status === 'fulfilled') {
        const prog = progressRes.value.data as UserProgress
        setProgress(prog)
        const map: Record<string, string> = {}
        prog.enrollments?.forEach((e, i) => {
          map[e.module_id] = `enr-${e.module_id}-${i}`
        })
        setEnrollmentMap(map)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load training data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const enroll = async (moduleId: string) => {
    setActionLoading(true)
    try {
      const res = await api.post('/training/enroll', { module_id: moduleId })
      setEnrollmentMap((prev) => ({ ...prev, [moduleId]: res.data.enrollment_id }))
      await fetchData()
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Enrollment failed'
      setError(msg)
    } finally {
      setActionLoading(false)
    }
  }

  const updateProgress = async (enrollmentId: string, pct: number) => {
    await api.post('/training/update-progress', {
      enrollment_id: enrollmentId,
      progress_percentage: pct,
      status: pct >= 100 ? 'completed' : 'in_progress',
    })
  }

  const openModule = async (mod: TrainingModule) => {
    let enrollmentId = enrollmentMap[mod.module_id]

    if (mod.enrollment_status === 'not_enrolled' || !enrollmentId) {
      setActionLoading(true)
      try {
        const res = await api.post('/training/enroll', { module_id: mod.module_id })
        enrollmentId = res.data.enrollment_id
        setEnrollmentMap((prev) => ({ ...prev, [mod.module_id]: enrollmentId! }))
      } catch (err: unknown) {
        setError('Could not enroll in module')
        setActionLoading(false)
        return
      }
      setActionLoading(false)
    }

    const currentProgress = mod.progress ?? 0
    const nextProgress = Math.min(100, currentProgress + 25)

    if (enrollmentId && nextProgress > currentProgress) {
      try {
        await updateProgress(enrollmentId, nextProgress)
        await fetchData()
      } catch {
        /* continue showing module */
      }
    }

    setActiveModule({ ...mod, enrollment_id: enrollmentId })
  }

  const completeModule = async () => {
    if (!activeModule?.enrollment_id) return
    setActionLoading(true)
    try {
      await api.post('/training/complete', {
        enrollment_id: activeModule.enrollment_id,
        score: 85,
      })
      setActiveModule(null)
      setCertificateDialog(true)
      await fetchData()
    } catch (err: unknown) {
      setError('Could not complete training')
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <Box p={3}>
      <Box display="flex" alignItems="center" mb={3}>
        <SchoolIcon sx={{ mr: 1, fontSize: 32, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4">Training Portal</Typography>
          <Typography variant="body2" color="text.secondary">
            Team education modules with progress tracking and certificates
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {progress && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {progress.completed}
              </Typography>
              <Typography variant="caption">Completed</Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {progress.in_progress}
              </Typography>
              <Typography variant="caption">In Progress</Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4">{progress.total_enrollments}</Typography>
              <Typography variant="caption">Enrolled</Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {progress.completion_rate.toFixed(0)}%
              </Typography>
              <Typography variant="caption">Completion Rate</Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      ) : modules.length === 0 ? (
        <Alert severity="info">
          No training modules found. Run{' '}
          <code>python scripts/create_initial_training_modules.py</code> to seed modules.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {modules.map((mod) => {
            const status = mod.enrollment_status || 'not_enrolled'
            const pct = mod.progress ?? 0
            return (
              <Grid item xs={12} md={6} lg={4} key={mod.module_id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flex: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Typography variant="h6" fontSize="1rem">
                        {mod.title}
                      </Typography>
                      <Chip label={status.replace(/_/g, ' ')} size="small" color={STATUS_COLOR[status] || 'default'} />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 40 }}>
                      {mod.description || 'No description'}
                    </Typography>
                    <Box display="flex" gap={1} mb={2}>
                      {mod.duration_minutes && (
                        <Chip label={`${mod.duration_minutes} min`} size="small" variant="outlined" />
                      )}
                      {mod.difficulty_level && (
                        <Chip label={mod.difficulty_level} size="small" variant="outlined" />
                      )}
                    </Box>
                    {status !== 'not_enrolled' && (
                      <Box mb={2}>
                        <Box display="flex" justifyContent="space-between" mb={0.5}>
                          <Typography variant="caption">Progress</Typography>
                          <Typography variant="caption">{pct}%</Typography>
                        </Box>
                        <LinearProgress variant="determinate" value={pct} />
                      </Box>
                    )}
                  </CardContent>
                  <Box px={2} pb={2}>
                    {status === 'completed' ? (
                      <Button fullWidth variant="outlined" startIcon={<EmojiEventsIcon />} disabled>
                        Certificate Earned
                      </Button>
                    ) : status === 'not_enrolled' ? (
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<PlayCircleIcon />}
                        onClick={() => enroll(mod.module_id)}
                        disabled={actionLoading}
                      >
                        Enroll
                      </Button>
                    ) : (
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<PlayCircleIcon />}
                        onClick={() => openModule(mod)}
                        disabled={actionLoading}
                      >
                        {pct >= 75 ? 'Complete Module' : 'Continue Learning'}
                      </Button>
                    )}
                  </Box>
                </Card>
              </Grid>
            )
          })}
        </Grid>
      )}

      <Dialog open={!!activeModule} onClose={() => setActiveModule(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{activeModule?.title}</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            {activeModule?.description}
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText primary="Type" secondary={activeModule?.training_type} />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Duration"
                secondary={`${activeModule?.duration_minutes ?? '—'} minutes`}
              />
            </ListItem>
          </List>
          <LinearProgress
            variant="determinate"
            value={activeModule?.progress ?? 0}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActiveModule(null)}>Close</Button>
          {(activeModule?.progress ?? 0) >= 75 ? (
            <Button variant="contained" onClick={completeModule} disabled={actionLoading}>
              Finish & Get Certificate
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={() => activeModule && openModule(activeModule)}
              disabled={actionLoading}
            >
              Mark 25% Progress
            </Button>
          )}
        </DialogActions>
      </Dialog>

      <Dialog open={certificateDialog} onClose={() => setCertificateDialog(false)}>
        <DialogTitle sx={{ textAlign: 'center' }}>
          <CheckCircleIcon color="success" sx={{ fontSize: 48, display: 'block', mx: 'auto', mb: 1 }} />
          Training Complete!
        </DialogTitle>
        <DialogContent>
          <Typography align="center">
            Congratulations! You have earned a certificate for completing this module.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button fullWidth variant="contained" onClick={() => setCertificateDialog(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
