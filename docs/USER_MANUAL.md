# INEsCape User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Roles](#user-roles)
4. [Features](#features)
5. [Common Tasks](#common-tasks)
6. [Troubleshooting](#troubleshooting)

## Introduction

INEsCape is an integrated platform for diagnosing and treating esophageal cancer. This manual provides guidance for all user types.

## Getting Started

### Accessing the Platform

1. Navigate to the platform URL
2. Login with your credentials
3. You will be redirected to the dashboard

### First Login

- Change your default password
- Complete your profile
- Review the tutorial

## User Roles

### Data Scientist

**Capabilities:**
- Generate synthetic data
- Train machine learning models
- Analyze datasets
- Access synthetic and de-identified data

**Key Features:**
- Data Generation Dashboard
- Model Training Interface
- Experiment Tracking

### Clinical Researcher

**Capabilities:**
- Collect real-world data
- Annotate clinical data
- Access de-identified datasets
- Generate reports

**Key Features:**
- Data Collection Tools
- Annotation Interface
- Analysis Tools

### Medical Oncologist

**Capabilities:**
- View patient data (de-identified)
- Use Clinical Decision Support
- Access treatment recommendations
- View prognostic scores

**Key Features:**
- Patient Dashboard
- CDS Interface
- Treatment Planning Tools

### System Administrator

**Capabilities:**
- Manage users
- View audit logs
- System configuration
- Monitor system health

**Key Features:**
- User Management
- Audit Log Viewer
- System Monitoring

## Features

### Synthetic Data Generation

1. Navigate to **Data Generation**
2. Set parameters:
   - Number of patients
   - Cancer ratio
   - Random seed
3. Click **Generate**
4. Review results and download

### Data Collection

1. Navigate to **Data Collection**
2. Select data source (TCGA, GEO, Kaggle)
3. Enter search query
4. Click **Collect**
5. Monitor collection progress

### Machine Learning Models

1. Navigate to **ML Models**
2. Click **Train New Model**
3. Select:
   - Training data
   - Model type
   - Hyperparameters
4. Start training
5. View results and metrics

### Clinical Decision Support

1. Navigate to **CDS**
2. Enter patient information
3. Select risk factors
4. Click **Predict Risk**
5. Review recommendations

## Common Tasks

### Generating Synthetic Data

```bash
# Via API
POST /api/v1/synthetic-data/generate
{
  "n_patients": 1000,
  "cancer_ratio": 0.3,
  "seed": 42
}
```

### Training a Model

```bash
# Via API
POST /api/v1/ml-models/train
{
  "data_path": "data.csv",
  "target_column": "has_cancer",
  "model_type": "RandomForest"
}
```

### Risk Prediction

```bash
# Via API
POST /api/v1/cds/risk-prediction
{
  "patient_data": {
    "age": 65,
    "gender": "Male",
    "smoking": true
  }
}
```

## Troubleshooting

### Cannot Login

- Check username and password
- Contact administrator if account is locked
- Reset password if forgotten

### Data Generation Fails

- Check parameter values
- Verify database connection
- Review error logs

### Model Training Errors

- Verify data format
- Check feature columns
- Review error messages

## Support

For additional support:
- Email: support@inescape.com
- Documentation: https://docs.inescape.com
- Issue Tracker: https://github.com/inescape/issues

