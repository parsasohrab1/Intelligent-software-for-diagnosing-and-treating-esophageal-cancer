import { Box, Typography, Card, CardContent, Alert } from '@mui/material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'

interface SHAPVisualizationProps {
  explanation: any
  prediction?: number
  riskCategory?: string
}

export default function SHAPVisualization({ explanation, prediction, riskCategory }: SHAPVisualizationProps) {
  if (!explanation) {
    return (
      <Alert severity="info">Explanation not available</Alert>
    )
  }

  if (explanation.error) {
    return (
      <Alert severity="warning">{explanation.error}</Alert>
    )
  }

  // Extract feature importance data
  let featureData: Array<{ feature: string; value: number; color: string }> = []
  
  // Check for SHAP explanation from model (nested structure)
  if (explanation.shap_explanation?.shap_explanation?.feature_importance) {
    // SHAP explanation from model (nested)
    const importance = explanation.shap_explanation.shap_explanation.feature_importance
    featureData = Object.entries(importance)
      .map(([feature, value]: [string, any]) => ({
        feature: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: Math.abs(parseFloat(value)),
        color: parseFloat(value) > 0 ? '#ef5350' : '#42a5f5'
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10)
  } else if (explanation.shap_explanation?.feature_importance) {
    // Direct feature importance in shap_explanation (rule-based)
    const importance = explanation.shap_explanation.feature_importance
    featureData = Object.entries(importance)
      .map(([feature, value]: [string, any]) => ({
        feature: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: Math.abs(parseFloat(value)),
        color: parseFloat(value) > 0 ? '#ef5350' : '#42a5f5'
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10)
  } else if (explanation.feature_importance) {
    // Direct feature importance
    featureData = Object.entries(explanation.feature_importance)
      .map(([feature, value]: [string, any]) => ({
        feature: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: Math.abs(parseFloat(value)),
        color: '#42a5f5'
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10)
  } else if (explanation.factors) {
    // Rule-based factors
    featureData = explanation.factors
      .map((factor: any) => ({
        feature: factor.factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: Math.abs(factor.contribution || factor.risk || 0),
        color: (factor.contribution || factor.risk || 0) > 0 ? '#ef5350' : '#42a5f5'
      }))
      .sort((a, b) => b.value - a.value)
  }

  if (featureData.length === 0) {
    return (
      <Alert severity="info">No data available for display</Alert>
    )
  }

  // Get SHAP values for waterfall plot if available
  const shapValues = explanation.shap_explanation?.shap_explanation?.shap_values?.[0] || 
                     explanation.shap_explanation?.shap_values?.[0] ||
                     explanation.shap_values?.[0]

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Model Explainability Analysis (SHAP)
      </Typography>
      
      {prediction !== undefined && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" gutterBottom>
            <strong>Risk Prediction:</strong> {(prediction * 100).toFixed(1)}%
          </Typography>
          {riskCategory && (
            <Typography variant="body2" color="textSecondary">
              Category: {riskCategory}
            </Typography>
          )}
        </Box>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Feature Importance
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            This chart shows which features have the most impact on the prediction
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={featureData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="feature" type="category" width={150} />
              <Tooltip 
                formatter={(value: number) => value.toFixed(4)}
                labelStyle={{ color: '#000' }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {featureData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {shapValues && Array.isArray(shapValues) && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              SHAP Values for This Patient
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Positive values (red) increase risk and negative values (blue) decrease risk
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={featureData.slice(0, 8)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="feature" 
                  angle={-45} 
                  textAnchor="end" 
                  height={100}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value">
                  {featureData.slice(0, 8).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="textSecondary">
          <strong>Explanation:</strong> This analysis shows why the system made this prediction.
          Features with higher values have more impact on the final result.
        </Typography>
      </Box>
    </Box>
  )
}

