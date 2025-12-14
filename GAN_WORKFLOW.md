# GAN-based MRI Image Generation Workflow

Complete guide for collecting real MRI data and expanding datasets using GAN.

## Overview

This system provides a complete pipeline to:
1. **Collect** real MRI images from online platforms (Kaggle, TCGA, etc.)
2. **Train** a GAN (Generative Adversarial Network) on collected images
3. **Expand** your dataset by generating synthetic MRI images
4. **Display** generated images in the MRI dashboard with interpretations

## Quick Start

### Complete Pipeline (Recommended)

Run all steps in one command:

```bash
python scripts/gan_pipeline.py
```

This will:
- Collect MRI images from Kaggle
- Train GAN on collected images (50 epochs)
- Generate synthetic images to expand your dataset

### Step-by-Step

#### 1. Collect Real MRI Images

```bash
# From Kaggle (requires API credentials)
python scripts/collect_mri_images.py --source kaggle --process

# From TCGA
python scripts/collect_mri_images.py --source tcga

# From all sources
python scripts/collect_mri_images.py --source all --process
```

**Setup Kaggle API:**
1. Go to https://www.kaggle.com/account
2. Create API token
3. Set environment variables:
   ```bash
   export KAGGLE_USERNAME=your_username
   export KAGGLE_KEY=your_api_key
   ```
   Or add to `.env` file:
   ```
   KAGGLE_USERNAME=your_username
   KAGGLE_KEY=your_api_key
   ```

**Output:** Images saved to `collected_mri_images/processed/`

#### 2. Train GAN

```bash
# Basic training
python scripts/train_gan.py --data-dir collected_mri_images/processed

# Advanced training
python scripts/train_gan.py \
    --data-dir collected_mri_images/processed \
    --epochs 200 \
    --batch-size 32 \
    --image-size 512 512 \
    --save-dir models/gan
```

**Requirements:**
- TensorFlow installed
- At least 50-100 training images (200+ recommended)
- GPU recommended (but works on CPU)

**Output:** Trained model in `models/gan/final_model/`

#### 3. Expand Dataset with GAN

```bash
# Generate 2x synthetic images
python scripts/expand_data_with_gan.py \
    --model-path models/gan/final_model \
    --expansion-factor 2

# Generate 5x synthetic images
python scripts/expand_data_with_gan.py \
    --model-path models/gan/final_model \
    --expansion-factor 5
```

**Output:** Synthetic images saved to database, visible in MRI dashboard

## Data Sources

### Kaggle Datasets

Popular MRI datasets:
- `radiopedia/mri-images-brain`
- `muratkokludataset/mri-images`
- `sartajbhuvaji/brain-tumor-classification-mri`
- `navoneel/brain-mri-images-for-brain-tumor-detection`

### TCGA (The Cancer Genome Atlas)

- TCGA-ESCA: Esophageal Cancer imaging data
- Requires registration

### Other Sources

- **Radiopaedia**: https://radiopaedia.org
- **TCIA**: https://www.cancerimagingarchive.net
- **MICCAI**: Medical imaging research datasets

## How It Works

### 1. Data Collection

The `collect_mri_images.py` script:
- Searches Kaggle for MRI datasets
- Downloads images automatically
- Normalizes images to 512x512 grayscale
- Organizes by source

### 2. GAN Training

The `train_gan.py` script:
- Loads normalized images
- Trains generator and discriminator networks
- Saves checkpoints during training
- Generates sample images to monitor progress

### 3. Data Expansion

The `expand_data_with_gan.py` script:
- Loads trained GAN model
- Reads existing MRI data from database
- Generates synthetic images with variations
- Adds annotations (findings, impressions)
- Saves to database

### 4. Image Display

The MRI dashboard:
- Fetches images from `/api/v1/imaging/mri/{image_id}/image`
- Uses GAN if available (falls back to geometric method)
- Displays images with annotations
- Shows findings and impressions

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Kaggle API
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# GAN Model Path (optional)
GAN_MODEL_PATH=models/gan/final_model
```

### Model Settings

In `app/core/config.py`:
- `GAN_MODEL_PATH`: Path to trained model weights
- `GAN_ENABLED`: Enable/disable GAN generation

## Usage Examples

### Example 1: Quick Test

```bash
# Collect small dataset
python scripts/collect_mri_images.py --source kaggle --limit 1 --process

# Quick training (10 epochs)
python scripts/train_gan.py --data-dir collected_mri_images/processed --epochs 10

# Generate test images
python scripts/expand_data_with_gan.py --expansion-factor 1 --no-save
```

### Example 2: Production Setup

```bash
# Collect comprehensive dataset
python scripts/collect_mri_images.py --source all --process

# Full training
python scripts/train_gan.py \
    --data-dir collected_mri_images/processed \
    --epochs 200 \
    --batch-size 32

# Expand dataset 5x
python scripts/expand_data_with_gan.py \
    --model-path models/gan/final_model \
    --expansion-factor 5
```

## Output Structure

```
collected_mri_images/
├── kaggle/
│   └── [datasets]/
│       └── [images]
├── processed/
│   └── [normalized images]
└── collection_summary.json

models/gan/
├── final_model/
│   ├── generator.h5
│   └── discriminator.h5
├── sample_epoch_*.png
└── training_history.json
```

## Troubleshooting

### No Images Collected

- **Check API credentials**: Verify Kaggle username/key
- **Manual download**: Download images manually and place in `collected_mri_images/processed/`
- **Check internet**: Ensure connection to Kaggle/TCGA

### GAN Training Issues

- **TensorFlow not installed**: `pip install tensorflow`
- **Out of memory**: Reduce `--batch-size` (try 16 or 8)
- **No GPU**: Training works on CPU but is slower
- **Poor quality**: Train for more epochs (100-200+)

### Generated Images Not Showing

- **Check model path**: Verify `models/gan/final_model/generator.h5` exists
- **Check logs**: Look for GAN loading errors
- **Fallback**: System automatically falls back to geometric method

## Best Practices

1. **Data Quality**: Use high-quality, normalized images (512x512)
2. **Training Data**: Collect 200+ images for good results
3. **Training Time**: Allow 2-4 hours for 100 epochs (GPU) or 8-12 hours (CPU)
4. **Monitor Progress**: Check `models/gan/sample_epoch_*.png` during training
5. **Iterative Improvement**: 
   - Start with small dataset
   - Train for few epochs
   - Evaluate results
   - Collect more data and retrain

## Integration

The GAN is automatically integrated with:
- **MRI Dashboard**: Images displayed with annotations
- **API Endpoint**: `/api/v1/imaging/mri/{image_id}/image?use_gan=true`
- **Database**: Synthetic images saved alongside real data
- **Fallback**: Geometric visualization if GAN unavailable

## Next Steps

1. **Collect Data**: Start with Kaggle datasets
2. **Train Model**: Use collected images to train GAN
3. **Expand Dataset**: Generate synthetic images
4. **View Results**: Check MRI dashboard for generated images
5. **Iterate**: Improve by collecting more data and retraining

## Notes

- GAN works without training but produces abstract images
- For realistic medical images, training is essential
- All generated images include annotations (findings, impressions)
- Synthetic images are marked and can be filtered in dashboard
