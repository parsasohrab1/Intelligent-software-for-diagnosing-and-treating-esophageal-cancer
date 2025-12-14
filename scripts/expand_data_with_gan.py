#!/usr/bin/env python3
"""
Script to expand MRI dataset using trained GAN
Generates synthetic images based on existing MRI data and saves to database
"""
import sys
import os
import argparse
from pathlib import Path
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.imaging_data import ImagingData
from app.models.patient import Patient
try:
    from app.services.gan.mri_image_generator import get_gan_generator
except ImportError:
    logger.error("GAN module not available. Install TensorFlow: pip install tensorflow")
    get_gan_generator = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_gan_model(model_path: Optional[str] = None):
    """Load trained GAN model"""
    if get_gan_generator is None:
        raise ImportError("GAN module not available. Install TensorFlow: pip install tensorflow")
    
    gan_gen = get_gan_generator(model_path=model_path)
    
    if gan_gen is None:
        raise ValueError("GAN generator not available. Check TensorFlow installation.")
    
    # Load weights if provided
    if model_path:
        model_path = Path(model_path)
        generator_weights = model_path / "generator.h5"
        
        if generator_weights.exists():
            logger.info(f"Loading GAN weights from {generator_weights}")
            try:
                gan_gen.generator.load_weights(str(generator_weights))
                gan_gen.is_trained = True
                logger.info("GAN weights loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load weights: {e}. Using untrained model.")
        else:
            logger.warning(f"Weights file not found: {generator_weights}")
    
    return gan_gen


def generate_synthetic_images(
    gan_gen,
    base_images: List[ImagingData],
    expansion_factor: int = 2,
    save_to_db: bool = True
) -> Dict:
    """
    Generate synthetic MRI images based on existing data
    
    Args:
        gan_gen: GAN generator instance
        base_images: List of existing ImagingData to use as base
        expansion_factor: How many synthetic images per real image
        save_to_db: Whether to save to database
    """
    logger.info(f"Generating {expansion_factor}x synthetic images from {len(base_images)} base images")
    
    results = {
        'images_generated': 0,
        'images_saved': 0,
        'errors': []
    }
    
    db = SessionLocal()
    
    try:
        for base_image in base_images:
            # Get patient for this image
            patient = db.query(Patient).filter(
                Patient.patient_id == base_image.patient_id
            ).first()
            
            if not patient:
                logger.warning(f"Patient {base_image.patient_id} not found, skipping")
                continue
            
            # Generate multiple variations
            for i in range(expansion_factor):
                try:
                    # Generate synthetic image with slight variations
                    # Add small random variations to parameters
                    tumor_variation = base_image.tumor_length_cm
                    if tumor_variation:
                        tumor_variation += random.uniform(-0.5, 0.5)
                        tumor_variation = max(0, tumor_variation)
                    
                    wall_variation = base_image.wall_thickness_cm
                    if wall_variation:
                        wall_variation += random.uniform(-0.2, 0.2)
                        wall_variation = max(0, wall_variation)
                    
                    nodes_variation = base_image.lymph_nodes_positive
                    if nodes_variation is not None:
                        nodes_variation = max(0, nodes_variation + random.randint(-1, 1))
                    
                    # Generate image
                    synthetic_image = gan_gen.generate_with_annotations(
                        image_id=base_image.image_id * 10000 + i,  # Unique ID
                        patient_id=base_image.patient_id,
                        tumor_length_cm=tumor_variation,
                        wall_thickness_cm=wall_variation,
                        lymph_nodes_positive=nodes_variation,
                        contrast_used=base_image.contrast_used,
                        findings=base_image.findings,
                        impression=base_image.impression,
                        imaging_date=str(base_image.imaging_date) if base_image.imaging_date else None
                    )
                    
                    # Create new ImagingData record
                    new_imaging = ImagingData(
                        patient_id=base_image.patient_id,
                        imaging_modality="MRI",
                        findings=base_image.findings,
                        impression=base_image.impression,
                        tumor_length_cm=tumor_variation,
                        wall_thickness_cm=wall_variation,
                        lymph_nodes_positive=nodes_variation,
                        contrast_used=base_image.contrast_used,
                        radiologist_id=base_image.radiologist_id,
                        imaging_date=base_image.imaging_date
                    )
                    
                    if save_to_db:
                        db.add(new_imaging)
                        db.commit()
                        results['images_saved'] += 1
                    
                    results['images_generated'] += 1
                    
                    if (results['images_generated'] % 10) == 0:
                        logger.info(f"Generated {results['images_generated']} synthetic images...")
                    
                except Exception as e:
                    logger.error(f"Error generating synthetic image {i} for {base_image.image_id}: {e}")
                    results['errors'].append(f"Error with image {base_image.image_id}: {str(e)}")
        
        logger.info(f"Generated {results['images_generated']} synthetic images")
        logger.info(f"Saved {results['images_saved']} images to database")
        
    except Exception as e:
        logger.error(f"Error in generation process: {e}")
        results['errors'].append(f"Generation error: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    return results


def expand_dataset(
    model_path: Optional[str] = None,
    expansion_factor: int = 2,
    patient_limit: Optional[int] = None,
    save_to_db: bool = True
) -> Dict:
    """Main function to expand dataset using GAN"""
    
    logger.info("="*60)
    logger.info("Expanding MRI Dataset with GAN")
    logger.info("="*60)
    
    # Load GAN model
    logger.info("Loading GAN model...")
    try:
        gan_gen = load_gan_model(model_path)
    except Exception as e:
        logger.error(f"Failed to load GAN: {e}")
        return {'error': str(e)}
    
    # Get existing MRI images from database
    db = SessionLocal()
    try:
        query = db.query(ImagingData).filter(
            ImagingData.imaging_modality == "MRI"
        )
        
        if patient_limit:
            # Get distinct patients and limit
            patients = db.query(Patient.patient_id).limit(patient_limit).all()
            patient_ids = [p[0] for p in patients]
            query = query.filter(ImagingData.patient_id.in_(patient_ids))
        
        base_images = query.all()
        logger.info(f"Found {len(base_images)} base MRI images")
        
        if not base_images:
            logger.warning("No MRI images found in database. Run data collection first.")
            return {'error': 'No base images found'}
        
    finally:
        db.close()
    
    # Generate synthetic images
    results = generate_synthetic_images(
        gan_gen=gan_gen,
        base_images=base_images,
        expansion_factor=expansion_factor,
        save_to_db=save_to_db
    )
    
    # Summary
    logger.info("="*60)
    logger.info("Expansion Summary:")
    logger.info(f"  Base images: {len(base_images)}")
    logger.info(f"  Images generated: {results['images_generated']}")
    logger.info(f"  Images saved: {results['images_saved']}")
    logger.info(f"  Expansion factor: {expansion_factor}x")
    if results['errors']:
        logger.warning(f"  Errors: {len(results['errors'])}")
    logger.info("="*60)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Expand MRI dataset using trained GAN"
    )
    parser.add_argument(
        '--model-path',
        type=str,
        help='Path to trained GAN model weights'
    )
    parser.add_argument(
        '--expansion-factor',
        type=int,
        default=2,
        help='How many synthetic images to generate per real image'
    )
    parser.add_argument(
        '--patient-limit',
        type=int,
        help='Limit number of patients to process'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Generate images without saving to database'
    )
    
    args = parser.parse_args()
    
    try:
        results = expand_dataset(
            model_path=args.model_path,
            expansion_factor=args.expansion_factor,
            patient_limit=args.patient_limit,
            save_to_db=not args.no_save
        )
        
        # Save results
        results_file = Path("gan_expansion_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {results_file}")
        
    except Exception as e:
        logger.error(f"Expansion failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
