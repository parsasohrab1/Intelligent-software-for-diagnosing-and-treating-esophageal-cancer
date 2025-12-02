import { Box, Typography, Card, CardContent, TextField, Button } from '@mui/material'

export default function Settings() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            API Configuration
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField label="API Base URL" defaultValue="http://localhost:8000" />
            <Button variant="contained">Save Settings</Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

