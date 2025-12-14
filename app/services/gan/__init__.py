"""
GAN services for synthetic image generation
"""
from app.services.gan.mri_image_generator import MRIGANGenerator, get_gan_generator

__all__ = ['MRIGANGenerator', 'get_gan_generator']
