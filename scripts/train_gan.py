#!/usr/bin/env python3
"""
Script to train GAN on collected MRI images
"""
import sys
import os
import argparse
from pathlib import Path
import logging
import json
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    from PIL import Image
    TF_AVAILABLE = True
except ImportError as e:
    TF_AVAILABLE = False
    logger.error(f"TensorFlow not available: {e}")
    logger.error("Install with: pip install tensorflow pillow numpy")


def load_training_images(data_dir: Path, image_size: tuple = (512, 512)) -> np.ndarray:
    """Load and preprocess training images"""
    logger.info(f"Loading images from {data_dir}")
    
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.tiff', '*.tif']:
        image_files.extend(data_dir.rglob(ext))
    
    if not image_files:
        raise ValueError(f"No image files found in {data_dir}")
    
    logger.info(f"Found {len(image_files)} image files")
    
    images = []
    for img_path in image_files:
        try:
            img = Image.open(img_path)
            
            # Convert to grayscale
            if img.mode != 'L':
                img = img.convert('L')
            
            # Resize to target size
            img = img.resize(image_size, Image.LANCZOS)
            
            # Convert to numpy array and normalize to [-1, 1]
            img_array = np.array(img, dtype=np.float32)
            img_array = (img_array / 127.5) - 1.0
            
            # Add channel dimension
            img_array = np.expand_dims(img_array, axis=-1)
            
            images.append(img_array)
            
        except Exception as e:
            logger.warning(f"Error loading {img_path}: {e}")
            continue
    
    if not images:
        raise ValueError("No valid images could be loaded")
    
    images_array = np.array(images)
    logger.info(f"Loaded {len(images)} images, shape: {images_array.shape}")
    
    return images_array


def train_gan(
    data_dir: str,
    epochs: int = 100,
    batch_size: int = 32,
    image_size: tuple = (512, 512),
    save_dir: str = "models/gan",
    latent_dim: int = 100
):
    """Train the GAN model on MRI images"""
    
    if not TF_AVAILABLE:
        raise ImportError("TensorFlow is required for GAN training")
    
    from app.services.gan.mri_image_generator import MRIGANGenerator
    
    logger.info("="*60)
    logger.info("GAN Training for MRI Image Generation")
    logger.info("="*60)
    
    # Load training data
    data_path = Path(data_dir)
    if not data_path.exists():
        raise ValueError(f"Data directory does not exist: {data_dir}")
    
    X_train = load_training_images(data_path, image_size)
    
    # Initialize GAN
    logger.info("Initializing GAN...")
    gan = MRIGANGenerator(image_size=image_size, latent_dim=latent_dim)
    gan.build_gan()
    
    # Create save directory
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Training parameters
    half_batch = batch_size // 2
    
    logger.info(f"Starting training...")
    logger.info(f"  Epochs: {epochs}")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Training samples: {len(X_train)}")
    logger.info(f"  Image size: {image_size}")
    
    # Training history
    history = {
        'd_loss': [],
        'd_acc': [],
        'g_loss': []
    }
    
    # Training loop
    for epoch in range(epochs):
        # Train discriminator
        # Select random real images
        idx = np.random.randint(0, X_train.shape[0], half_batch)
        real_images = X_train[idx]
        
        # Generate fake images
        noise = np.random.normal(0, 1, (half_batch, latent_dim))
        fake_images = gan.generator.predict(noise, verbose=0)
        
        # Create labels
        real_labels = np.ones((half_batch, 1))
        fake_labels = np.zeros((half_batch, 1))
        
        # Train discriminator on real and fake
        d_loss_real = gan.discriminator.train_on_batch(real_images, real_labels)
        d_loss_fake = gan.discriminator.train_on_batch(fake_images, fake_labels)
        d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)
        
        # Train generator
        noise = np.random.normal(0, 1, (batch_size, latent_dim))
        valid_labels = np.ones((batch_size, 1))  # We want generator to fool discriminator
        
        g_loss = gan.gan.train_on_batch(noise, valid_labels)
        
        # Save history
        history['d_loss'].append(float(d_loss[0]))
        history['d_acc'].append(float(d_loss[1]))
        history['g_loss'].append(float(g_loss))
        
        # Log progress
        if (epoch + 1) % 10 == 0 or epoch == 0:
            logger.info(
                f"Epoch {epoch+1}/{epochs} - "
                f"D Loss: {d_loss[0]:.4f}, D Acc: {d_loss[1]:.4f}, "
                f"G Loss: {g_loss:.4f}"
            )
            
            # Generate sample image
            sample_noise = np.random.normal(0, 1, (1, latent_dim))
            generated = gan.generator.predict(sample_noise, verbose=0)
            
            # Save sample
            sample_img = ((generated[0, :, :, 0] + 1) * 127.5).astype(np.uint8)
            sample_pil = Image.fromarray(sample_img, mode='L')
            sample_path = save_path / f"sample_epoch_{epoch+1}.png"
            sample_pil.save(sample_path)
        
        # Save checkpoint every 25 epochs
        if (epoch + 1) % 25 == 0:
            checkpoint_path = save_path / f"gan_checkpoint_epoch_{epoch+1}"
            checkpoint_path.mkdir(exist_ok=True)
            gan.generator.save_weights(str(checkpoint_path / "generator.h5"))
            gan.discriminator.save_weights(str(checkpoint_path / "discriminator.h5"))
            logger.info(f"Checkpoint saved at epoch {epoch+1}")
    
    # Save final model
    logger.info("Saving final model...")
    final_path = save_path / "final_model"
    final_path.mkdir(exist_ok=True)
    gan.generator.save_weights(str(final_path / "generator.h5"))
    gan.discriminator.save_weights(str(final_path / "discriminator.h5"))
    
    # Save training history
    history_path = save_path / "training_history.json"
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    
    logger.info(f"Training complete!")
    logger.info(f"Model saved to: {final_path}")
    logger.info(f"Training history saved to: {history_path}")
    
    return gan, history


def main():
    parser = argparse.ArgumentParser(
        description="Train GAN on collected MRI images"
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        required=True,
        help='Directory containing training images'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for training'
    )
    parser.add_argument(
        '--image-size',
        type=int,
        nargs=2,
        default=[512, 512],
        help='Image size (width height)'
    )
    parser.add_argument(
        '--save-dir',
        type=str,
        default='models/gan',
        help='Directory to save trained model'
    )
    parser.add_argument(
        '--latent-dim',
        type=int,
        default=100,
        help='Latent dimension for GAN'
    )
    
    args = parser.parse_args()
    
    if not TF_AVAILABLE:
        logger.error("TensorFlow is required. Install with: pip install tensorflow")
        return
    
    try:
        train_gan(
            data_dir=args.data_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            image_size=tuple(args.image_size),
            save_dir=args.save_dir,
            latent_dim=args.latent_dim
        )
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
