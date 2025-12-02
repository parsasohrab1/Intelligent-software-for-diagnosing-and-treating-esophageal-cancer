import { useState, useEffect } from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material'
import {
  People as PeopleIcon,
  Science as ScienceIcon,
  Psychology as PsychologyIcon,
  LocalHospital as HospitalIcon,
} from '@mui/icons-material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../services/api'

interface DashboardStats {
  total_patients: number
  cancer_patients: number
  normal_patients: number
  total_datasets: number
  total_models: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      // Fetch statistics from various endpoints with better error handling
      const [patientsRes, datasetsRes, modelsRes] = await Promise.allSettled([
        api.get('/patients/'),
        api.get('/data-collection/metadata/statistics'),
        api.get('/ml-models/models'),
      ])

      // Extract data from settled promises
      const patientsData = patientsRes.status === 'fulfilled' 
        ? (Array.isArray(patientsRes.value.data) ? patientsRes.value.data : [])
        : []
      
      const datasetsData = datasetsRes.status === 'fulfilled'
        ? datasetsRes.value.data
        : { total_datasets: 0 }
      
      const modelsData = modelsRes.status === 'fulfilled'
        ? modelsRes.value.data
        : { count: 0, models: [] }

      // Calculate cancer patients from patient data
      const cancerPatients = patientsData.filter((p: any) => 
        p.has_cancer === true || p.has_cancer === 'true' || p.has_cancer === 1
      ).length
      const normalPatients = patientsData.length - cancerPatients

      setStats({
        total_patients: patientsData.length || 0,
        cancer_patients: cancerPatients,
        normal_patients: normalPatients,
        total_datasets: datasetsData?.total_datasets || 0,
        total_models: modelsData?.count || modelsData?.models?.length || 0,
      })
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      // Set default values on error
      setStats({
        total_patients: 0,
        cancer_patients: 0,
        normal_patients: 0,
        total_datasets: 0,
        total_models: 0,
      })
    } finally {
      setLoading(false)
    }
  }

  const statCards = [
    {
      title: 'Total Patients',
      value: stats?.total_patients || 0,
      icon: <PeopleIcon sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: 'Datasets',
      value: stats?.total_datasets || 0,
      icon: <ScienceIcon sx={{ fontSize: 40 }} />,
      color: '#42a5f5',
    },
    {
      title: 'ML Models',
      value: stats?.total_models || 0,
      icon: <PsychologyIcon sx={{ fontSize: 40 }} />,
      color: '#dc004e',
    },
    {
      title: 'CDS Services',
      value: 6,
      icon: <HospitalIcon sx={{ fontSize: 40 }} />,
      color: '#9c27b0',
    },
  ]

  const sampleData = [
    { name: 'Jan', patients: 100, predictions: 85 },
    { name: 'Feb', patients: 150, predictions: 120 },
    { name: 'Mar', patients: 200, predictions: 180 },
    { name: 'Apr', patients: 180, predictions: 160 },
    { name: 'May', patients: 220, predictions: 200 },
  ]

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      {card.title}
                    </Typography>
                    <Typography variant="h4">{card.value}</Typography>
                  </Box>
                  <Box sx={{ color: card.color }}>{card.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Activity Overview
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={sampleData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="patients" stroke="#1976d2" name="Patients" />
                  <Line type="monotone" dataKey="predictions" stroke="#dc004e" name="Predictions" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ mt: 2 }}>
                {/* Quick action buttons would go here */}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

