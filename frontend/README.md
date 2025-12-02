# INEsCape Frontend

Frontend application for INEsCape - Esophageal Cancer Management Platform

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Material-UI (MUI)** - Component library
- **Vite** - Build tool
- **React Router** - Routing
- **React Query** - Data fetching
- **Recharts** - Charts and visualizations
- **Axios** - HTTP client

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:3000

### Build

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable components
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── theme.ts        # MUI theme
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── public/             # Static assets
└── package.json
```

## Features

- Dashboard with statistics and charts
- Patient management
- Synthetic data generation
- Data collection from external sources
- ML model management
- Clinical Decision Support interface
- Settings and configuration

## Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

