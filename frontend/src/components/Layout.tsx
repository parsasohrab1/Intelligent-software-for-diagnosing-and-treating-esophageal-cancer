import { useState, ReactNode } from 'react'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import RouteIcon from '@mui/icons-material/Route'
import DashboardIcon from '@mui/icons-material/Dashboard'
import PeopleIcon from '@mui/icons-material/People'
import ScienceIcon from '@mui/icons-material/Science'
import PsychologyIcon from '@mui/icons-material/Psychology'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import ImageIcon from '@mui/icons-material/Image'
import MonitorIcon from '@mui/icons-material/MonitorHeart'
import HealingIcon from '@mui/icons-material/Healing'
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined'
import SchoolIcon from '@mui/icons-material/School'
import SecurityIcon from '@mui/icons-material/Security'
import SettingsIcon from '@mui/icons-material/Settings'
import { useNavigate, useLocation } from 'react-router-dom'

const drawerWidth = 240

interface LayoutProps {
  children: ReactNode
}

const menuItems = [
  { text: 'Clinical Workflow', icon: <RouteIcon />, path: '/workflow' },
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Patients', icon: <PeopleIcon />, path: '/patients' },
  { text: 'Patient Data', icon: <ScienceIcon />, path: '/patient-data' },
  { text: 'ML Models', icon: <PsychologyIcon />, path: '/ml-models' },
  { text: 'Clinical Decision Support', icon: <LocalHospitalIcon />, path: '/cds' },
  { text: 'Surgical Guidance', icon: <HealingIcon />, path: '/surgical-guidance' },
  { text: 'Treatment Response', icon: <ScienceOutlinedIcon />, path: '/treatment-response' },
  { text: 'MRI Report', icon: <ImageIcon />, path: '/mri' },
  { text: 'Patient Monitoring', icon: <MonitorIcon />, path: '/monitoring' },
  { text: 'Training', icon: <SchoolIcon />, path: '/training' },
  { text: 'Compliance', icon: <SecurityIcon />, path: '/compliance' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
]

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          INEsCape
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path)
                setMobileOpen(false)
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            Esophageal Cancer Management Platform
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  )
}

