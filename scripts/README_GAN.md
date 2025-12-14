# GAN-based MRI Image Generation Pipeline

Complete pipeline for collecting real MRI data, training GAN, and expanding datasets.

## Overview

This pipeline consists of three main scripts:

1. **collect_mri_images.py** - Collects real MRI images from online platforms
2. **train_gan.py** - Trains GAN on collected images
3. **expand_data_with_gan.py** - Uses trained GAN to generate synthetic images
4. **gan_pipeline.py** - Runs the complete pipeline end-to-end

## Quick Start

### Option 1: Run Complete Pipeline

```bash
python scripts/gan_pipeline.py
```

This will:
1. Collect MRI images from Kaggle
2. Train GAN on collected images
3. Expand your dataset with synthetic images

### Option 2: Run Steps Individually

#### Step 1: Collect Real MRI Images

```bash
# Collect from Kaggle
python scripts/collect_mri_images.py --source kaggle --process

# Collect from TCGA
python scripts/collect_mri_images.py --source tcga

# Collect from all sources
python scripts/collect_mri_images.py --source all --process
```

**Requirements:**
- Kaggle API credentials (set `KAGGLE_USERNAME` and `KAGGLE_KEY` in environment or `.env`)
- For TCGA: May require API key

**Output:** Images saved to `collected_mri_images/processed/`

#### Step 2: Train GAN

```bash
# Train with default settings
python scripts/train_gan.py --data-dir collected_mri_images/processed

# Train with custom settings
python scripts/train_gan.py \
    --data-dir collected_mri_images/processed \
    --epochs 200 \
    --batch-size 32 \
    --image-size 512 512 \
    --save-dir models/gan
```

**Requirements:**
- TensorFlow installed
- At least 50-100 training images (more is better)
- GPU recommended for faster training

**Output:** Trained model saved to `models/gan/final_model/`

#### Step 3: Expand Dataset

```bash
# Expand with trained model
python scripts/expand_data_with_gan.py \
    --model-path models/gan/final_model \
    --expansion-factor 3

# Expand without saving to database (for testing)
python scripts/expand_data_with_gan.py --no-save --expansion-factor 2
```

**Output:** Synthetic images generated and saved to database

## Data Sources

### Kaggle Datasets

Popular MRI datasets on Kaggle:
- `radiopedia/mri-images-brain`
- `muratkokludataset/mri-images`
- `sartajbhuvaji/brain-tumor-classification-mri`
- `navoneel/brain-mri-images-for-brain-tumor-detection`

### TCGA (The Cancer Genome Atlas)

- TCGA-ESCA: Esophageal Cancer imaging data
- Requires registration and API access

### Other Public Sources

- **Radiopaedia**: https://radiopaedia.org (manual download)
- **TCIA**: https://www.cancerimagingarchive.net (requires registration)
- **MICCAI**: Research datasets from medical imaging conferences

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Kaggle API
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# TCGA API (if available)
TCGA_API_KEY=your_tcga_key
```

### Kaggle API Setup

1. Go to https://www.kaggle.com/account
2. Create API token
3. Download `kaggle.json`
4. Place in `~/.kaggle/kaggle.json` or set environment variables

## Training Tips

1. **More Data = Better Results**: Collect at least 100-200 images for decent results
2. **Image Quality**: Use high-quality, normalized images (512x512 or 256x256)
3. **Training Time**: Expect 2-4 hours for 100 epochs on GPU, 8-12 hours on CPU
4. **Monitor Training**: Check sample images generated during training in `models/gan/`
5. **Adjust Parameters**: 
   - Increase `latent_dim` for more variation
   - Adjust `batch_size` based on GPU memory
   - More epochs = better quality (but diminishing returns)

## Usage Examples

### Example 1: Quick Test Run

```bash
# Collect a small dataset
python scripts/collect_mri_images.py --source kaggle --limit 1 --process

# Train for a few epochs
python scripts/train_gan.py --data-dir collected_mri_images/processed --epochs 10

# Generate a few synthetic images
python scripts/expand_data_with_gan.py --expansion-factor 1 --no-save
```

### Example 2: Production Pipeline

```bash
# Collect comprehensive dataset
python scripts/collect_mri_images.py --source all --process

# Train extensively
python scripts/train_gan.py \
    --data-dir collected_mri_images/processed \
    --epochs 200 \
    --batch-size 32

# Expand dataset 5x
python scripts/expand_data_with_gan.py \
    --model-path models/gan/final_model \
    --expansion-factor 5
```

## Troubleshooting

### No Images Collected

- Check API credentials
- Verify internet connection
- Try manual download and place in `collected_mri_images/processed/`

### GAN Training Fails

- Ensure TensorFlow is installed: `pip install tensorflow`
- Check GPU availability: `python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"`
- Reduce batch size if out of memory
- Verify training images are in correct format (PNG/JPG, grayscale)

### Poor Image Quality

- Train for more epochs (100-200+)
- Use more training data (200+ images)
- Adjust GAN architecture parameters
- Check training samples in `models/gan/sample_epoch_*.png`

## Output Structure

```
collected_mri_images/
├── kaggle/
│   └── [dataset_name]/
│       └── [images]
├── tcga/
│   └── [dataset_name]/
│       └── [data files]
└── processed/
    └── [normalized images]

models/gan/
├── final_model/
│   ├── generator.h5
│   └── discriminator.h5
├── sample_epoch_*.png
└── training_history.json
```

## Next Steps

1. **Collect Real Data**: Start with Kaggle datasets
2. **Train GAN**: Use collected data to train the model
3. **Expand Dataset**: Generate synthetic images to augment your dataset
4. **Evaluate**: Check generated images in MRI dashboard
5. **Iterate**: Collect more data and retrain for better results

## Notes

- GAN works without training but produces abstract images
- For realistic medical images, training on real data is essential
- Synthetic images are automatically annotated with findings and impressions
- All generated images are saved to database and appear in MRI dashboard
