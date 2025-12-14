#!/usr/bin/env python3
"""
Complete pipeline: Collect data -> Train GAN -> Expand dataset
"""
import sys
import os
import argparse
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_complete_pipeline(
    collect_data: bool = True,
    train_gan: bool = True,
    expand_data: bool = True,
    data_dir: str = "collected_mri_images",
    model_dir: str = "models/gan",
    expansion_factor: int = 2
):
    """Run the complete GAN pipeline"""
    
    logger.info("="*60)
    logger.info("GAN Pipeline: Collect -> Train -> Expand")
    logger.info("="*60)
    
    # Step 1: Collect data
    if collect_data:
        logger.info("\n[Step 1/3] Collecting MRI images from online platforms...")
        try:
            from scripts.collect_mri_images import MRIImageCollector
            
            collector = MRIImageCollector(output_dir=data_dir)
            result = collector.collect_from_kaggle(limit=5)
            
            if result['images_downloaded'] > 0:
                # Process images
                collector.process_downloaded_images()
                logger.info(f"✓ Collected {result['images_downloaded']} images")
            else:
                logger.warning("No images collected. You may need to manually add images to the data directory.")
                logger.info(f"Place images in: {data_dir}/processed/")
                
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            if not Path(data_dir).exists():
                logger.error("Data directory not found. Skipping to training with existing data.")
                train_gan = False
                expand_data = False
    
    # Step 2: Train GAN
    if train_gan:
        logger.info("\n[Step 2/3] Training GAN on collected images...")
        try:
            from scripts.train_gan import train_gan
            
            processed_dir = Path(data_dir) / "processed"
            if not processed_dir.exists():
                processed_dir = Path(data_dir)
            
            train_gan(
                data_dir=str(processed_dir),
                epochs=50,  # Reduced for faster training
                batch_size=16,
                image_size=(512, 512),
                save_dir=model_dir
            )
            logger.info("✓ GAN training completed")
            
        except Exception as e:
            logger.error(f"GAN training failed: {e}")
            logger.warning("Continuing with untrained model...")
    
    # Step 3: Expand dataset
    if expand_data:
        logger.info("\n[Step 3/3] Expanding dataset with GAN...")
        try:
            from scripts.expand_data_with_gan import expand_dataset
            
            model_path = Path(model_dir) / "final_model"
            if not model_path.exists():
                model_path = None
                logger.warning("No trained model found, using untrained GAN")
            
            results = expand_dataset(
                model_path=str(model_path) if model_path else None,
                expansion_factor=expansion_factor,
                save_to_db=True
            )
            
            if 'error' not in results:
                logger.info(f"✓ Generated {results['images_generated']} synthetic images")
                logger.info(f"✓ Saved {results['images_saved']} images to database")
            else:
                logger.error(f"Expansion failed: {results.get('error')}")
                
        except Exception as e:
            logger.error(f"Data expansion failed: {e}")
    
    logger.info("\n" + "="*60)
    logger.info("Pipeline completed!")
    logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Complete GAN pipeline: Collect data, train GAN, expand dataset"
    )
    parser.add_argument(
        '--skip-collect',
        action='store_true',
        help='Skip data collection step'
    )
    parser.add_argument(
        '--skip-train',
        action='store_true',
        help='Skip GAN training step'
    )
    parser.add_argument(
        '--skip-expand',
        action='store_true',
        help='Skip data expansion step'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='collected_mri_images',
        help='Directory for collected images'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='models/gan',
        help='Directory for trained models'
    )
    parser.add_argument(
        '--expansion-factor',
        type=int,
        default=2,
        help='Expansion factor for synthetic data generation'
    )
    
    args = parser.parse_args()
    
    run_complete_pipeline(
        collect_data=not args.skip_collect,
        train_gan=not args.skip_train,
        expand_data=not args.skip_expand,
        data_dir=args.data_dir,
        model_dir=args.model_dir,
        expansion_factor=args.expansion_factor
    )


if __name__ == '__main__':
    main()
