#!/usr/bin/env python3
"""
Script to collect real MRI images from online platforms
Supports: Kaggle, TCGA, Medical Imaging Datasets, and other public sources
"""
import sys
import os
import argparse
from pathlib import Path
import json
from typing import List, Dict, Optional
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_collectors.kaggle_collector import KaggleCollector
from app.services.data_collectors.tcga_collector import TCGACollector
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MRIImageCollector:
    """Specialized collector for MRI images from various sources"""
    
    def __init__(self, output_dir: str = "collected_mri_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup collectors
        self.kaggle_collector = KaggleCollector(
            api_key=getattr(settings, 'KAGGLE_KEY', None),
            username=getattr(settings, 'KAGGLE_USERNAME', None)
        )
        self.tcga_collector = TCGACollector(
            api_key=getattr(settings, 'TCGA_API_KEY', None)
        )
        
        # Known MRI datasets
        self.known_datasets = {
            'kaggle': [
                'radiopedia/mri-images-brain',
                'muratkokludataset/mri-images',
                'sartajbhuvaji/brain-tumor-classification-mri',
                'navoneel/brain-mri-images-for-brain-tumor-detection',
            ],
            'tcga': [
                'TCGA-ESCA',  # Esophageal Cancer
            ]
        }
    
    def collect_from_kaggle(self, dataset_id: Optional[str] = None, limit: int = 100) -> Dict:
        """Collect MRI images from Kaggle"""
        logger.info(f"Collecting MRI images from Kaggle...")
        
        results = {
            'source': 'kaggle',
            'datasets_found': 0,
            'images_downloaded': 0,
            'errors': []
        }
        
        try:
            # Search for MRI datasets
            if dataset_id:
                datasets = [{'dataset_id': dataset_id}]
            else:
                search_results = self.kaggle_collector.discover_datasets("MRI medical imaging")
                datasets = search_results[:5]  # Limit to top 5
                # Also try known datasets
                for known_id in self.known_datasets['kaggle']:
                    if not any(d.get('dataset_id') == known_id for d in datasets):
                        datasets.append({'dataset_id': known_id})
            
            results['datasets_found'] = len(datasets)
            
            for dataset in datasets:
                dataset_id = dataset.get('dataset_id')
                logger.info(f"Processing dataset: {dataset_id}")
                
                try:
                    # Create output directory for this dataset
                    dataset_dir = self.output_dir / 'kaggle' / dataset_id.replace('/', '_')
                    dataset_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Download dataset
                    if self.kaggle_collector.download_dataset(dataset_id, str(dataset_dir)):
                        # Count images downloaded
                        image_files = list(dataset_dir.rglob('*.png')) + \
                                     list(dataset_dir.rglob('*.jpg')) + \
                                     list(dataset_dir.rglob('*.jpeg')) + \
                                     list(dataset_dir.rglob('*.dcm')) + \
                                     list(dataset_dir.rglob('*.nii'))
                        
                        results['images_downloaded'] += len(image_files)
                        logger.info(f"Downloaded {len(image_files)} images from {dataset_id}")
                    else:
                        results['errors'].append(f"Failed to download {dataset_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing dataset {dataset_id}: {e}")
                    results['errors'].append(f"Error with {dataset_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error collecting from Kaggle: {e}")
            results['errors'].append(f"Kaggle collection error: {str(e)}")
        
        return results
    
    def collect_from_tcga(self, dataset_id: Optional[str] = None) -> Dict:
        """Collect MRI images from TCGA"""
        logger.info(f"Collecting MRI images from TCGA...")
        
        results = {
            'source': 'tcga',
            'datasets_found': 0,
            'images_downloaded': 0,
            'errors': []
        }
        
        try:
            # Search for esophageal cancer imaging data
            datasets = self.tcga_collector.discover_datasets("esophageal imaging")
            
            if dataset_id:
                datasets = [d for d in datasets if d.get('dataset_id') == dataset_id]
            
            results['datasets_found'] = len(datasets)
            
            for dataset in datasets[:3]:  # Limit to 3 datasets
                dataset_id = dataset.get('dataset_id')
                logger.info(f"Processing TCGA dataset: {dataset_id}")
                
                try:
                    dataset_dir = self.output_dir / 'tcga' / dataset_id
                    dataset_dir.mkdir(parents=True, exist_ok=True)
                    
                    output_file = dataset_dir / f"{dataset_id}.tsv"
                    if self.tcga_collector.download_dataset(dataset_id, str(output_file)):
                        results['images_downloaded'] += 1
                        logger.info(f"Downloaded TCGA dataset {dataset_id}")
                    else:
                        results['errors'].append(f"Failed to download {dataset_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing TCGA dataset {dataset_id}: {e}")
                    results['errors'].append(f"Error with {dataset_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error collecting from TCGA: {e}")
            results['errors'].append(f"TCGA collection error: {str(e)}")
        
        return results
    
    def collect_from_public_sources(self) -> Dict:
        """Collect from other public medical imaging sources"""
        logger.info("Collecting from public medical imaging sources...")
        
        results = {
            'source': 'public',
            'datasets_found': 0,
            'images_downloaded': 0,
            'errors': []
        }
        
        # List of public MRI datasets
        public_sources = [
            {
                'name': 'Radiopaedia',
                'url': 'https://radiopaedia.org',
                'note': 'Manual download required'
            },
            {
                'name': 'The Cancer Imaging Archive (TCIA)',
                'url': 'https://www.cancerimagingarchive.net',
                'note': 'Requires registration'
            },
            {
                'name': 'Medical Image Computing (MICCAI)',
                'url': 'https://www.miccai.org',
                'note': 'Research datasets available'
            }
        ]
        
        logger.info("Public sources identified. Manual download may be required.")
        logger.info("Consider using TCIA or Radiopaedia for high-quality MRI datasets.")
        
        # Save source information
        sources_file = self.output_dir / 'public_sources.json'
        with open(sources_file, 'w') as f:
            json.dump(public_sources, f, indent=2)
        
        results['datasets_found'] = len(public_sources)
        
        return results
    
    def process_downloaded_images(self) -> Dict:
        """Process and normalize downloaded images"""
        logger.info("Processing downloaded images...")
        
        results = {
            'images_processed': 0,
            'images_normalized': 0,
            'errors': []
        }
        
        try:
            from PIL import Image
            import numpy as np
            
            processed_dir = self.output_dir / 'processed'
            processed_dir.mkdir(exist_ok=True)
            
            # Find all image files
            image_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.tiff', '*.tif']:
                image_files.extend(self.output_dir.rglob(ext))
            
            logger.info(f"Found {len(image_files)} image files to process")
            
            for img_path in image_files:
                try:
                    # Load and normalize image
                    img = Image.open(img_path)
                    
                    # Convert to grayscale if needed
                    if img.mode != 'L':
                        img = img.convert('L')
                    
                    # Resize to standard size (512x512 for GAN training)
                    img = img.resize((512, 512), Image.LANCZOS)
                    
                    # Save normalized image
                    rel_path = img_path.relative_to(self.output_dir)
                    output_path = processed_dir / rel_path.parent / f"normalized_{rel_path.name}"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    img.save(output_path, 'PNG')
                    
                    results['images_processed'] += 1
                    results['images_normalized'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {img_path}: {e}")
                    results['errors'].append(f"Error processing {img_path}: {str(e)}")
            
            logger.info(f"Processed {results['images_processed']} images")
            
        except Exception as e:
            logger.error(f"Error in image processing: {e}")
            results['errors'].append(f"Processing error: {str(e)}")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Collect real MRI images from online platforms"
    )
    parser.add_argument(
        '--source',
        type=str,
        choices=['kaggle', 'tcga', 'public', 'all'],
        default='all',
        help='Data source to collect from'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='collected_mri_images',
        help='Output directory for collected images'
    )
    parser.add_argument(
        '--dataset-id',
        type=str,
        help='Specific dataset ID to download'
    )
    parser.add_argument(
        '--process',
        action='store_true',
        help='Process and normalize downloaded images'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Limit number of datasets to download'
    )
    
    args = parser.parse_args()
    
    collector = MRIImageCollector(output_dir=args.output_dir)
    
    all_results = []
    
    # Collect from specified sources
    if args.source in ['kaggle', 'all']:
        result = collector.collect_from_kaggle(
            dataset_id=args.dataset_id,
            limit=args.limit
        )
        all_results.append(result)
        logger.info(f"Kaggle: {result['images_downloaded']} images downloaded")
    
    if args.source in ['tcga', 'all']:
        result = collector.collect_from_tcga(dataset_id=args.dataset_id)
        all_results.append(result)
        logger.info(f"TCGA: {result['images_downloaded']} datasets downloaded")
    
    if args.source in ['public', 'all']:
        result = collector.collect_from_public_sources()
        all_results.append(result)
        logger.info(f"Public sources: {result['datasets_found']} sources identified")
    
    # Process images if requested
    if args.process:
        process_result = collector.process_downloaded_images()
        all_results.append(process_result)
        logger.info(f"Processed: {process_result['images_processed']} images normalized")
    
    # Save summary
    summary = {
        'total_images': sum(r.get('images_downloaded', 0) for r in all_results),
        'total_datasets': sum(r.get('datasets_found', 0) for r in all_results),
        'results': all_results
    }
    
    summary_file = collector.output_dir / 'collection_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\n{'='*60}")
    logger.info("Collection Summary:")
    logger.info(f"Total images downloaded: {summary['total_images']}")
    logger.info(f"Total datasets found: {summary['total_datasets']}")
    logger.info(f"Summary saved to: {summary_file}")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()
