import {
  Alert,
  AlertTitle,
  Box,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
} from '@mui/material'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'

export interface CDSWarning {
  field: string
  severity: 'error' | 'warning' | 'info'
  message: string
  message_fa?: string
}

export interface CDSDataCompleteness {
  is_complete?: boolean
  completeness_score?: number
  reliability?: 'high' | 'moderate' | 'low'
  missing_required?: string[]
  missing_recommended?: string[]
  warnings?: CDSWarning[]
  clinical_guidance?: string
  prediction_reliable?: boolean
}

interface CDSDataCompletenessAlertProps {
  completeness: CDSDataCompleteness | null | undefined
  /** Show bilingual messages (English + Persian) */
  bilingual?: boolean
  /** Compact mode for inline display */
  compact?: boolean
}

export function validatePatientDataClient(patientData: Record<string, unknown>): CDSDataCompleteness {
  const warnings: CDSWarning[] = []
  const missingRequired: string[] = []
  const missingRecommended: string[] = []

  const absent = (key: string) =>
    patientData[key] === undefined || patientData[key] === null || patientData[key] === ''

  if (absent('age') || Number(patientData.age) <= 0) {
    missingRequired.push('age')
    warnings.push({
      field: 'age',
      severity: 'error',
      message: 'Patient age is required.',
      message_fa: 'سن بیمار الزامی است.',
    })
  }

  if (absent('gender')) {
    missingRequired.push('gender')
    warnings.push({
      field: 'gender',
      severity: 'error',
      message: 'Patient gender is required.',
      message_fa: 'جنسیت بیمار الزامی است.',
    })
  }

  const recommended = ['bmi', 'smoking', 'alcohol', 'gerd', 'barretts_esophagus', 'family_history'] as const
  const labels: Record<string, { en: string; fa: string }> = {
    bmi: { en: 'BMI not documented', fa: 'BMI مستند نشده' },
    smoking: { en: 'Smoking status not documented', fa: 'وضعیت سیگار مستند نشده' },
    alcohol: { en: 'Alcohol use not documented', fa: 'مصرف الکل مستند نشده' },
    gerd: { en: 'GERD history not documented', fa: 'سابقه GERD مستند نشده' },
    barretts_esophagus: { en: "Barrett's esophagus not documented", fa: 'مری بارت مستند نشده' },
    family_history: { en: 'Family history not documented', fa: 'سابقه خانوادگی مستند نشده' },
  }

  recommended.forEach((field) => {
    if (absent(field)) {
      missingRecommended.push(field)
      warnings.push({
        field,
        severity: 'warning',
        message: labels[field].en,
        message_fa: labels[field].fa,
      })
    }
  })

  const total = 2 + recommended.length
  const score = Math.max(0, (total - missingRequired.length - missingRecommended.length) / total)

  return {
    is_complete: missingRequired.length === 0 && missingRecommended.length === 0,
    completeness_score: Math.round(score * 100) / 100,
    reliability: missingRequired.length > 0 ? 'low' : missingRecommended.length > 0 ? 'moderate' : 'high',
    missing_required: missingRequired,
    missing_recommended: missingRecommended,
    warnings,
    prediction_reliable: missingRequired.length === 0,
    clinical_guidance:
      missingRequired.length > 0
        ? 'Complete required fields before running CDS.'
        : missingRecommended.length > 0
          ? 'Some recommended fields are missing; results may be less accurate.'
          : 'Input data looks complete.',
  }
}

export function validateCancerDataClient(cancerData: Record<string, unknown> | null | undefined): CDSDataCompleteness {
  if (!cancerData) {
    return {
      is_complete: false,
      completeness_score: 0,
      reliability: 'low',
      missing_required: ['cancer_data'],
      warnings: [
        {
          field: 'cancer_data',
          severity: 'error',
          message: 'Tumor staging data is required for treatment recommendations.',
          message_fa: 'داده staging برای پیشنهاد درمان الزامی است.',
        },
      ],
      prediction_reliable: false,
    }
  }

  const warnings: CDSWarning[] = []
  const missingRequired: string[] = []
  const missingRecommended: string[] = []

  const unknown = (v: unknown) =>
    typeof v === 'string' && ['unknown', 'n/a', 'na', ''].includes(v.trim().toLowerCase())

  ;['t_stage', 'n_stage', 'm_stage'].forEach((field) => {
    const val = cancerData[field]
    if (val === undefined || val === null || val === '' || unknown(val)) {
      missingRequired.push(field)
      warnings.push({
        field,
        severity: 'error',
        message: `${field.replace('_', ' ').toUpperCase()} is required for treatment staging.`,
        message_fa: `${field} برای staging درمان الزامی است.`,
      })
    }
  })
  ;['histological_grade', 'tumor_length_cm', 'pdl1_status'].forEach((field) => {
    const val = cancerData[field]
    if (val === undefined || val === null || val === '' || unknown(val)) {
      missingRecommended.push(field)
      warnings.push({
        field,
        severity: 'warning',
        message: `${field.replace(/_/g, ' ')} not fully documented.`,
        message_fa: `${field} به‌طور کامل مستند نشده است.`,
      })
    }
  })

  const total = 6
  const score = Math.max(0, (total - missingRequired.length - missingRecommended.length) / total)

  return {
    is_complete: missingRequired.length === 0 && missingRecommended.length === 0,
    completeness_score: Math.round(score * 100) / 100,
    reliability: missingRequired.length > 0 ? 'low' : missingRecommended.length > 0 ? 'moderate' : 'high',
    missing_required: missingRequired,
    missing_recommended: missingRecommended,
    warnings,
    prediction_reliable: missingRequired.length === 0,
  }
}

export default function CDSDataCompletenessAlert({
  completeness,
  bilingual = true,
  compact = false,
}: CDSDataCompletenessAlertProps) {
  if (!completeness || !completeness.warnings?.length) {
    if (completeness?.is_complete) {
      return (
        <Alert severity="success" sx={{ mb: 2 }}>
          Clinical input data is complete. CDS output is suitable for review.
        </Alert>
      )
    }
    return null
  }

  const severity =
    completeness.reliability === 'low' || (completeness.missing_required?.length ?? 0) > 0
      ? 'error'
      : completeness.reliability === 'moderate'
        ? 'warning'
        : 'info'

  const scorePct = Math.round((completeness.completeness_score ?? 0) * 100)

  if (compact) {
    return (
      <Alert severity={severity} sx={{ mb: 2 }}>
        <Typography variant="body2">
          Data completeness: {scorePct}% — {completeness.clinical_guidance || 'Review missing fields.'}
        </Typography>
      </Alert>
    )
  }

  return (
    <Alert severity={severity} sx={{ mb: 2 }}>
      <AlertTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        Incomplete Clinical Data
        <Chip label={`${scorePct}% complete`} size="small" color={severity === 'error' ? 'error' : 'warning'} />
        {completeness.reliability && (
          <Chip
            label={`Reliability: ${completeness.reliability}`}
            size="small"
            variant="outlined"
          />
        )}
      </AlertTitle>

      {completeness.clinical_guidance && (
        <Typography variant="body2" sx={{ mb: 1.5, fontWeight: 500 }}>
          {completeness.clinical_guidance}
        </Typography>
      )}

      <Box sx={{ mb: 1 }}>
        <LinearProgress
          variant="determinate"
          value={scorePct}
          color={severity === 'error' ? 'error' : severity === 'warning' ? 'warning' : 'primary'}
          sx={{ height: 6, borderRadius: 1 }}
        />
      </Box>

      <List dense disablePadding>
        {completeness.warnings.map((w, i) => (
          <ListItem key={`${w.field}-${i}`} disableGutters sx={{ py: 0.25 }}>
            <ListItemIcon sx={{ minWidth: 32 }}>
              {w.severity === 'error' ? (
                <ErrorOutlineIcon color="error" fontSize="small" />
              ) : w.severity === 'warning' ? (
                <WarningAmberIcon color="warning" fontSize="small" />
              ) : (
                <InfoOutlinedIcon color="info" fontSize="small" />
              )}
            </ListItemIcon>
            <ListItemText
              primary={
                <Typography variant="body2">
                  <strong>{w.field.replace(/_/g, ' ')}:</strong> {w.message}
                </Typography>
              }
              secondary={
                bilingual && w.message_fa ? (
                  <Typography variant="caption" color="text.secondary">
                    {w.message_fa}
                  </Typography>
                ) : undefined
              }
            />
          </ListItem>
        ))}
      </List>

      {completeness.prediction_reliable === false && (
        <Typography variant="caption" color="error.main" display="block" sx={{ mt: 1 }}>
          Do not use CDS output for clinical decisions until required fields are completed.
        </Typography>
      )}
    </Alert>
  )
}
