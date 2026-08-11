import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import SecurityIcon from '@mui/icons-material/Security'
import GavelIcon from '@mui/icons-material/Gavel'
import AssessmentIcon from '@mui/icons-material/Assessment'
import HistoryIcon from '@mui/icons-material/History'
import api from '../services/api'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index} role="tabpanel">
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  )
}

interface AuditLog {
  timestamp?: string
  user_id?: string
  event_type?: string
  action?: string
  resource?: string
  ip_address?: string
  [key: string]: unknown
}

export default function Compliance() {
  const [tab, setTab] = useState(0)
  const [loading, setLoading] = useState(true)
  const [complianceSummary, setComplianceSummary] = useState<Record<string, unknown> | null>(null)
  const [riskSummary, setRiskSummary] = useState<Record<string, unknown> | null>(null)
  const [qualityMetrics, setQualityMetrics] = useState<Record<string, unknown> | null>(null)
  const [changeSummary, setChangeSummary] = useState<Record<string, unknown> | null>(null)
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [retentionPolicy, setRetentionPolicy] = useState<Record<string, unknown> | null>(null)
  const [errors, setErrors] = useState<string[]>([])

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      const errs: string[] = []

      const fetchSafe = async (
        url: string,
        setter: (d: Record<string, unknown>) => void,
        label: string
      ) => {
        try {
          const res = await api.get(url)
          setter(res.data as Record<string, unknown>)
        } catch {
          errs.push(`${label} unavailable (auth may be required)`)
        }
      }

      await Promise.all([
        fetchSafe('/compliance/regulatory/compliance-summary', (d) => setComplianceSummary(d), 'Compliance summary'),
        fetchSafe('/compliance/risk/summary', (d) => setRiskSummary(d), 'Risk summary'),
        fetchSafe('/compliance/quality/metrics', (d) => setQualityMetrics(d), 'Quality metrics'),
        fetchSafe('/compliance/change-control/summary', (d) => setChangeSummary(d), 'Change control'),
        fetchSafe('/data-privacy/retention-policy', (d) => setRetentionPolicy(d), 'Retention policy'),
        (async () => {
          try {
            const res = await api.get('/audit/logs', { params: { limit: 50 } })
            setAuditLogs(res.data.logs || [])
          } catch {
            errs.push('Audit logs unavailable (admin permission required)')
          }
        })(),
      ])

      setErrors(errs)
      setLoading(false)
    }
    load()
  }, [])

  const renderKeyValue = (data: Record<string, unknown> | null, title: string) => {
    if (!data) return <Typography color="text.secondary">No data available</Typography>
    return (
      <Box>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
          {title}
        </Typography>
        <List dense>
          {Object.entries(data).map(([key, value]) => (
            <ListItem key={key} divider>
              <ListItemText
                primary={key.replace(/_/g, ' ')}
                secondary={
                  typeof value === 'object' && value !== null
                    ? JSON.stringify(value, null, 2)
                    : String(value)
                }
                primaryTypographyProps={{ textTransform: 'capitalize' }}
              />
            </ListItem>
          ))}
        </List>
      </Box>
    )
  }

  return (
    <Box p={3}>
      <Box display="flex" alignItems="center" mb={3}>
        <SecurityIcon sx={{ mr: 1, fontSize: 32, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4">Compliance & Audit</Typography>
          <Typography variant="body2" color="text.secondary">
            HIPAA/GDPR dashboard — regulatory tracking, risk management, and audit logs
          </Typography>
        </Box>
      </Box>

      {errors.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Some sections require admin authentication: {errors.join('; ')}
        </Alert>
      )}

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
          <Tab icon={<GavelIcon />} iconPosition="start" label="Regulatory" />
          <Tab icon={<AssessmentIcon />} iconPosition="start" label="Risk & Quality" />
          <Tab icon={<HistoryIcon />} iconPosition="start" label="Audit Logs" />
          <Tab icon={<SecurityIcon />} iconPosition="start" label="Data Privacy" />
        </Tabs>
      </Paper>

      {loading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TabPanel value={tab} index={0}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    {renderKeyValue(complianceSummary, 'Regulatory Compliance Summary')}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    {renderKeyValue(changeSummary, 'Change Control Summary')}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tab} index={1}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>{renderKeyValue(riskSummary, 'Risk Management Summary')}</CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>{renderKeyValue(qualityMetrics, 'Quality Assurance Metrics')}</CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tab} index={2}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Recent Audit Logs</Typography>
                  <Chip label={`${auditLogs.length} entries`} size="small" />
                </Box>
                {auditLogs.length === 0 ? (
                  <Typography color="text.secondary">
                    No audit logs available. Admin role with READ_AUDIT_LOGS permission is required.
                  </Typography>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Timestamp</TableCell>
                          <TableCell>User</TableCell>
                          <TableCell>Event</TableCell>
                          <TableCell>Action</TableCell>
                          <TableCell>Resource</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {auditLogs.map((log, i) => (
                          <TableRow key={i}>
                            <TableCell>{log.timestamp || '—'}</TableCell>
                            <TableCell>{log.user_id || '—'}</TableCell>
                            <TableCell>{log.event_type || '—'}</TableCell>
                            <TableCell>{log.action || '—'}</TableCell>
                            <TableCell>{log.resource || '—'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </TabPanel>

          <TabPanel value={tab} index={3}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      HIPAA Data Retention Policy
                    </Typography>
                    {retentionPolicy ? (
                      <List dense>
                        {Object.entries(retentionPolicy).map(([key, value]) => (
                          <ListItem key={key}>
                            <ListItemText
                              primary={key.replace(/_/g, ' ')}
                              secondary={String(value)}
                              primaryTypographyProps={{ textTransform: 'capitalize' }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    ) : (
                      <Typography color="text.secondary">
                        Retention policy requires admin access
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card sx={{ bgcolor: 'info.50' }}>
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                      GDPR Rights
                    </Typography>
                    <Typography variant="body2" paragraph>
                      Patients have the right to request data deletion (Right to be Forgotten) via the
                      data-privacy API.
                    </Typography>
                    <Chip label="HIPAA 7-year retention" color="primary" size="small" sx={{ mr: 1 }} />
                    <Chip label="GDPR compliant" color="success" size="small" />
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
        </>
      )}
    </Box>
  )
}
