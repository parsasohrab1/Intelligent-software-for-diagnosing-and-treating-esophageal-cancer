"""
GAN-based MRI Image Generator
Generates synthetic MRI images using Generative Adversarial Networks
"""
import numpy as np
import logging
from typing import Optional, Tuple, Dict, Any
from PIL import Image
import io

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available. GAN image generation will be disabled.")


class MRIGANGenerator:
    """GAN-based generator for synthetic MRI images"""
    
    def __init__(self, image_size: Tuple[int, int] = (256, 256), latent_dim: int = 100):
        self.image_size = image_size
        self.latent_dim = latent_dim
        self.generator = None
        self.discriminator = None
        self.gan = None
        self.is_trained = False
        
    def build_generator(self) -> keras.Model:
        """Build the generator network"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for GAN generation")
            
        model = keras.Sequential([
            # Input layer
            layers.Dense(256 * 8 * 8, use_bias=False, input_shape=(self.latent_dim,)),
            layers.BatchNormalization(),
            layers.LeakyReLU(alpha=0.2),
            layers.Reshape((8, 8, 256)),
            
            # Upsampling blocks
            layers.Conv2DTranspose(128, (5, 5), strides=(2, 2), padding='same', use_bias=False),
            layers.BatchNormalization(),
            layers.LeakyReLU(alpha=0.2),
            
            layers.Conv2DTranspose(64, (5, 5), strides=(2, 2), padding='same', use_bias=False),
            layers.BatchNormalization(),
            layers.LeakyReLU(alpha=0.2),
            
            layers.Conv2DTranspose(32, (5, 5), strides=(2, 2), padding='same', use_bias=False),
            layers.BatchNormalization(),
            layers.LeakyReLU(alpha=0.2),
            
            layers.Conv2DTranspose(16, (5, 5), strides=(2, 2), padding='same', use_bias=False),
            layers.BatchNormalization(),
            layers.LeakyReLU(alpha=0.2),
            
            # Output layer - grayscale medical image
            layers.Conv2DTranspose(1, (5, 5), strides=(2, 2), padding='same', use_bias=False, activation='tanh')
        ])
        
        return model
    
    def build_discriminator(self) -> keras.Model:
        """Build the discriminator network"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for GAN generation")
            
        model = keras.Sequential([
            # Input layer
            layers.Conv2D(64, (5, 5), strides=(2, 2), padding='same', input_shape=(*self.image_size, 1)),
            layers.LeakyReLU(alpha=0.2),
            layers.Dropout(0.3),
            
            layers.Conv2D(128, (5, 5), strides=(2, 2), padding='same'),
            layers.BatchNormalization(),
            layers.LeakyReLU(alpha=0.2),
            layers.Dropout(0.3),
            
            layers.Conv2D(256, (5, 5), strides=(2, 2), padding='same'),
            layers.BatchNormalization(),
            layers.LeakyReLU(alpha=0.2),
            layers.Dropout(0.3),
            
            layers.Conv2D(512, (5, 5), strides=(2, 2), padding='same'),
            layers.BatchNormalization(),
            layers.LeakyReLU(alpha=0.2),
            layers.Dropout(0.3),
            
            # Output layer
            layers.Flatten(),
            layers.Dense(1, activation='sigmoid')
        ])
        
        return model
    
    def build_gan(self):
        """Build the complete GAN model"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for GAN generation")
            
        # Build generator and discriminator
        self.generator = self.build_generator()
        self.discriminator = self.build_discriminator()
        
        # Compile discriminator
        self.discriminator.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0002, beta_1=0.5),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Freeze discriminator during generator training
        self.discriminator.trainable = False
        
        # Build GAN
        gan_input = keras.Input(shape=(self.latent_dim,))
        generated_image = self.generator(gan_input)
        gan_output = self.discriminator(generated_image)
        
        self.gan = keras.Model(gan_input, gan_output)
        self.gan.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0002, beta_1=0.5),
            loss='binary_crossentropy'
        )
        
        # Initialize with random weights - in production, load pre-trained weights
        logger.info("GAN model built. Note: For best results, train the model on real MRI data.")
    
    def generate_image(
        self,
        tumor_length_cm: Optional[float] = None,
        wall_thickness_cm: Optional[float] = None,
        lymph_nodes_positive: Optional[int] = None,
        contrast_used: bool = False,
        seed: Optional[int] = None
    ) -> Image.Image:
        """
        Generate a synthetic MRI image based on clinical parameters
        
        Args:
            tumor_length_cm: Tumor length in cm
            wall_thickness_cm: Wall thickness in cm
            lymph_nodes_positive: Number of positive lymph nodes
            contrast_used: Whether contrast was used
            seed: Random seed for reproducibility
            
        Returns:
            PIL Image of generated MRI
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for GAN generation")
        
        # Initialize GAN if not built
        if self.gan is None:
            self.build_gan()
        
        # Set random seed
        if seed is not None:
            np.random.seed(seed)
            tf.random.set_seed(seed)
        
        # Create conditional latent vector based on clinical parameters
        noise = np.random.normal(0, 1, (1, self.latent_dim))
        
        # Modify noise based on clinical parameters (conditional GAN approach)
        if tumor_length_cm is not None:
            # Larger tumors -> more variation in certain dimensions
            tumor_factor = min(tumor_length_cm / 10.0, 1.0)  # Normalize to 0-1
            noise[0, :20] += tumor_factor * 0.5
        
        if wall_thickness_cm is not None:
            thickness_factor = min(wall_thickness_cm / 5.0, 1.0)
            noise[0, 20:40] += thickness_factor * 0.3
        
        if lymph_nodes_positive is not None:
            nodes_factor = min(lymph_nodes_positive / 10.0, 1.0)
            noise[0, 40:60] += nodes_factor * 0.4
        
        if contrast_used:
            noise[0, 60:80] += 0.3  # Contrast enhancement
        
        # Generate image
        generated = self.generator.predict(noise, verbose=0)
        
        # Post-process image
        # Convert from [-1, 1] to [0, 255]
        img_array = ((generated[0, :, :, 0] + 1) * 127.5).astype(np.uint8)
        
        # Resize to target size if needed
        if img_array.shape != self.image_size:
            img = Image.fromarray(img_array, mode='L')
            img = img.resize(self.image_size, Image.LANCZOS)
            img_array = np.array(img)
        
        # Apply medical imaging style adjustments
        # Enhance contrast for medical imaging look
        img_array = np.clip(img_array * 1.3, 0, 255).astype(np.uint8)
        
        # Apply histogram equalization for better contrast
        from PIL import ImageEnhance
        img = Image.fromarray(img_array, mode='L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        img_array = np.array(img)
        
        # Add subtle noise for realism (medical imaging has noise)
        noise_mask = np.random.normal(0, 3, img_array.shape).astype(np.int16)
        img_array = np.clip(img_array.astype(np.int16) + noise_mask, 0, 255).astype(np.uint8)
        
        # Apply Gaussian blur for smoother medical imaging appearance
        from PIL import ImageFilter
        img = Image.fromarray(img_array, mode='L')
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return img
    
    def generate_with_annotations(
        self,
        image_id: int,
        patient_id: str,
        tumor_length_cm: Optional[float] = None,
        wall_thickness_cm: Optional[float] = None,
        lymph_nodes_positive: Optional[int] = None,
        contrast_used: bool = False,
        findings: Optional[str] = None,
        impression: Optional[str] = None,
        imaging_date: Optional[str] = None
    ) -> Image.Image:
        """
        Generate MRI image with annotations and text overlays
        
        Returns:
            PIL Image with annotations
        """
        # Generate base image
        base_img = self.generate_image(
            tumor_length_cm=tumor_length_cm,
            wall_thickness_cm=wall_thickness_cm,
            lymph_nodes_positive=lymph_nodes_positive,
            contrast_used=contrast_used,
            seed=image_id  # Use image_id as seed for consistency
        )
        
        # Convert to RGB for text overlay
        img_rgb = base_img.convert('RGB')
        
        # Add annotations using PIL
        from PIL import ImageDraw, ImageFont
        
        draw = ImageDraw.Draw(img_rgb)
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Add header
        draw.text((10, 10), f"MRI #{image_id}", fill='white', font=font_large)
        if patient_id:
            draw.text((10, 30), f"Patient: {patient_id}", fill='lightblue', font=font_small)
        if imaging_date:
            draw.text((10, 50), f"Date: {imaging_date}", fill='lightblue', font=font_small)
        
        # Add measurements
        x_pos = img_rgb.width - 200
        y_pos = 10
        draw.rectangle(
            [x_pos - 5, y_pos - 5, img_rgb.width - 5, y_pos + 80],
            outline='white', width=1, fill=(0, 0, 0, 180)
        )
        draw.text((x_pos, y_pos), "Measurements", fill='yellow', font=font_small)
        y_pos += 18
        
        if tumor_length_cm:
            draw.text((x_pos, y_pos), f"Tumor: {tumor_length_cm} cm", fill='red', font=font_small)
            y_pos += 16
        if wall_thickness_cm:
            draw.text((x_pos, y_pos), f"Wall: {wall_thickness_cm} cm", fill='yellow', font=font_small)
            y_pos += 16
        if lymph_nodes_positive:
            draw.text((x_pos, y_pos), f"Nodes: {lymph_nodes_positive}", fill='orange', font=font_small)
        
        # Add findings and impression at bottom
        if findings or impression:
            y_start = img_rgb.height - 120
            draw.rectangle(
                [5, y_start, img_rgb.width - 5, img_rgb.height - 5],
                outline='cyan', width=1, fill=(0, 0, 0, 200)
            )
            
            y_text = y_start + 5
            if findings:
                draw.text((10, y_text), "Findings:", fill='yellow', font=font_small)
                findings_short = findings[:80] + "..." if len(findings) > 80 else findings
                draw.text((10, y_text + 16), findings_short, fill='white', font=font_small)
                y_text += 40
            
            if impression:
                draw.text((10, y_text), "Impression:", fill='cyan', font=font_small)
                impression_short = impression[:80] + "..." if len(impression) > 80 else impression
                draw.text((10, y_text + 16), impression_short, fill='lightcyan', font=font_small)
        
        return img_rgb


# Global instance
_gan_generator: Optional[MRIGANGenerator] = None


def get_gan_generator(model_path: Optional[str] = None) -> Optional[MRIGANGenerator]:
    """
    Get or create the global GAN generator instance
    
    Args:
        model_path: Optional path to pre-trained model weights
    """
    global _gan_generator
    
    if not TF_AVAILABLE:
        return None
    
    if _gan_generator is None:
        try:
            _gan_generator = MRIGANGenerator(image_size=(512, 512))
            _gan_generator.build_gan()
            
            # Load pre-trained weights if provided
            if model_path:
                from pathlib import Path
                model_path_obj = Path(model_path)
                
                generator_weights = model_path_obj / "generator.h5"
                if not generator_weights.exists() and model_path_obj.is_file():
                    generator_weights = model_path_obj
                
                if generator_weights.exists():
                    try:
                        _gan_generator.generator.load_weights(str(generator_weights))
                        _gan_generator.is_trained = True
                        logger.info(f"Loaded pre-trained GAN weights from {generator_weights}")
                    except Exception as e:
                        logger.warning(f"Failed to load weights from {generator_weights}: {e}")
                else:
                    logger.warning(f"Model weights not found at {generator_weights}")
            
            logger.info("GAN generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GAN generator: {e}")
            return None
    
    return _gan_generator
