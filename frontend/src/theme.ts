import { createTheme, Theme } from '@mui/material/styles'
import { PaletteMode } from '@mui/material'

const sharedTypography = {
  fontFamily: [
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ].join(','),
  h1: {
    fontSize: '2.5rem',
    fontWeight: 600,
  },
  h2: {
    fontSize: '2rem',
    fontWeight: 600,
  },
  h3: {
    fontSize: '1.75rem',
    fontWeight: 600,
  },
}

const sharedComponents = {
  MuiButton: {
    styleOverrides: {
      root: {
        textTransform: 'none' as const,
        borderRadius: 8,
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 12,
      },
    },
  },
}

/**
 * Build a light or dark MUI theme. Dark mode reuses the same brand colors
 * (primary/secondary) but swaps the background/paper/shadow tokens so
 * contrast stays reasonable instead of naively inverting the light theme.
 */
export function getTheme(mode: PaletteMode): Theme {
  const isDark = mode === 'dark'

  return createTheme({
    palette: {
      mode,
      primary: {
        main: '#1976d2',
        light: '#42a5f5',
        dark: '#1565c0',
      },
      secondary: {
        main: '#dc004e',
        light: '#e33371',
        dark: '#9a0036',
      },
      background: isDark
        ? { default: '#0f1720', paper: '#1a2432' }
        : { default: '#f5f5f5', paper: '#ffffff' },
    },
    typography: sharedTypography,
    components: {
      ...sharedComponents,
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: isDark
              ? '0 2px 8px rgba(0,0,0,0.4)'
              : '0 2px 8px rgba(0,0,0,0.1)',
          },
        },
      },
    },
  })
}

// Kept for any code that still imports the default light theme directly.
const theme = getTheme('light')
export default theme
