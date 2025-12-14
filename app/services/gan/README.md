# GAN-based MRI Image Generator

This service uses Generative Adversarial Networks (GANs) to generate synthetic MRI images based on clinical parameters.

## Features

- **Conditional GAN**: Generates images based on clinical parameters (tumor size, wall thickness, lymph nodes, etc.)
- **Automatic Annotations**: Adds patient info, measurements, findings, and impressions to generated images
- **Fallback Support**: Automatically falls back to geometric visualization if GAN is unavailable

## Usage

The GAN is automatically used when requesting MRI images via:
```
GET /api/v1/imaging/mri/{image_id}/image?use_gan=true
```

## Training the GAN

For best results, the GAN should be trained on real MRI data. To train:

1. **Prepare Training Data**: Collect real MRI images and normalize them to 256x256 or 512x512 grayscale
2. **Train the Model**: Use the training script (to be created) or train manually:

```python
from app.services.gan.mri_image_generator import MRIGANGenerator
import numpy as np

# Initialize generator
gan = MRIGANGenerator(image_size=(512, 512))
gan.build_gan()

# Load your training data (real MRI images)
# X_train should be numpy array of shape (n_samples, height, width, 1)
# Normalized to [-1, 1] range

# Train the GAN
epochs = 100
batch_size = 32

for epoch in range(epochs):
    # Train discriminator
    # Train generator
    # (Full training loop implementation needed)
```

3. **Save Model Weights**: After training, save the generator weights:
```python
gan.generator.save_weights('models/mri_gan_generator.h5')
```

4. **Load Pre-trained Weights**: In production, load pre-trained weights:
```python
gan.generator.load_weights('models/mri_gan_generator.h5')
```

## Current Status

- ✅ GAN architecture implemented
- ✅ Conditional generation based on clinical parameters
- ✅ Automatic annotation overlay
- ⚠️ Model needs training on real data for realistic images
- ✅ Fallback to geometric method if GAN unavailable

## Notes

- Without training, the GAN will generate abstract/artistic images
- For realistic medical images, train on a dataset of real MRI scans
- The geometric fallback method provides interpretable visualizations even without GAN training
