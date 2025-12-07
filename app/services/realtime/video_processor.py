"""
Real-Time Video Processing for Endoscopy
پردازش بلادرنگ ویدیو برای استفاده در اتاق آندوسکوپی
"""
import time
import logging
import numpy as np
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import threading
from queue import Queue
import cv2

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """نتیجه پردازش یک فریم"""
    frame_id: int
    timestamp: float
    processing_time_ms: float
    prediction: Optional[Dict] = None
    confidence: Optional[float] = None
    annotations: Optional[List[Dict]] = None
    surgical_guidance: Optional[Dict] = None  # راهنمای جراحی
    error: Optional[str] = None


class VideoFrameProcessor:
    """پردازشگر فریم‌های ویدیو با بهینه‌سازی برای تأخیر کم"""

    def __init__(self, target_fps: int = 30, max_latency_ms: float = 200.0):
        """
        Args:
            target_fps: فریم‌های هدف در ثانیه
            max_latency_ms: حداکثر تأخیر مجاز (میلی‌ثانیه)
        """
        self.target_fps = target_fps
        self.max_latency_ms = max_latency_ms
        self.frame_interval = 1.0 / target_fps
        
        # GPU/TPU detection
        self.device = self._detect_device()
        self.use_gpu = self.device == "gpu"
        
        # Performance tracking
        self.processing_times = []
        self.frame_count = 0
        
        logger.info(f"VideoFrameProcessor initialized with device: {self.device}, max_latency: {max_latency_ms}ms")

    def _detect_device(self) -> str:
        """تشخیص دستگاه پردازش (CPU, GPU, TPU)"""
        # Check for CUDA GPU
        try:
            import torch
            if torch.cuda.is_available():
                logger.info(f"CUDA GPU detected: {torch.cuda.get_device_name(0)}")
                return "gpu"
        except ImportError:
            pass
        
        # Check for TensorFlow GPU
        try:
            import tensorflow as tf
            if tf.config.list_physical_devices('GPU'):
                logger.info("TensorFlow GPU detected")
                return "gpu"
        except ImportError:
            pass
        
        # Check for TPU
        try:
            import tensorflow as tf
            if tf.config.list_physical_devices('TPU'):
                logger.info("TPU detected")
                return "tpu"
        except ImportError:
            pass
        
        logger.info("Using CPU")
        return "cpu"

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        پیش‌پردازش فریم برای کاهش تأخیر
        
        Args:
            frame: فریم ورودی (BGR format)
            
        Returns:
            فریم پیش‌پردازش شده
        """
        start_time = time.time()
        
        # Resize if needed (reduce resolution for faster processing)
        height, width = frame.shape[:2]
        if width > 640 or height > 480:
            scale = min(640 / width, 480 / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # Convert to RGB if needed (for most ML models)
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Normalize pixel values to [0, 1]
        frame = frame.astype(np.float32) / 255.0
        
        preprocessing_time = (time.time() - start_time) * 1000
        if preprocessing_time > 10:  # Log if preprocessing takes too long
            logger.warning(f"Preprocessing took {preprocessing_time:.2f}ms")
        
        return frame

    def process_frame(
        self,
        frame: np.ndarray,
        model: Optional[Any] = None,
        frame_id: int = 0,
        include_saliency: bool = False,
        include_surgical_guidance: bool = False
    ) -> ProcessingResult:
        """
        پردازش یک فریم با تأخیر کم
        
        Args:
            frame: فریم ورودی
            model: مدل ML برای inference
            frame_id: شناسه فریم
            
        Returns:
            نتیجه پردازش
        """
        start_time = time.time()
        timestamp = time.time()
        
        try:
            # Preprocess
            preprocessed = self.preprocess_frame(frame)
            
            # Inference
            prediction = None
            confidence = None
            annotations = []
            surgical_guidance = None
            
            # Surgical guidance (if requested)
            if include_surgical_guidance:
                try:
                    from app.services.surgical_guidance.surgical_guidance_system import (
                        SurgicalGuidanceSystem,
                        EndoscopyMode
                    )
                    guidance_system = SurgicalGuidanceSystem()
                    guidance_result = guidance_system.process_frame(
                        frame=frame,
                        frame_id=frame_id
                    )
                    
                    surgical_guidance = {
                        "tumor_count": len(guidance_result.segmentation.tumor_boundaries),
                        "mean_depth_mm": guidance_result.depth_estimation.mean_depth_mm,
                        "max_depth_mm": guidance_result.depth_estimation.max_depth_mm,
                        "invasion_level": guidance_result.depth_estimation.invasion_level,
                        "margin_distance_mm": guidance_result.safe_margin.margin_distance_mm,
                        "resection_area_mm2": guidance_result.safe_margin.resection_area_mm2,
                        "safety_score": guidance_result.safe_margin.safety_score,
                        "recommendations": guidance_result.safe_margin.recommendations,
                        "overlay_available": True
                    }
                except Exception as e:
                    logger.warning(f"Could not generate surgical guidance: {str(e)}")
            
            if model is not None:
                inference_start = time.time()
                
                # Prepare input for model
                if self.use_gpu:
                    # Move to GPU if available
                    try:
                        import torch
                        if isinstance(preprocessed, np.ndarray):
                            preprocessed = torch.from_numpy(preprocessed).cuda()
                    except:
                        pass
                
                # Run inference
                prediction_result = self._run_inference(model, preprocessed, include_saliency=include_saliency)
                
                inference_time = (time.time() - inference_start) * 1000
                
                if prediction_result:
                    prediction = prediction_result.get("prediction")
                    confidence = prediction_result.get("confidence")
                    annotations = prediction_result.get("annotations", [])
            
            processing_time = (time.time() - start_time) * 1000
            
            # Track performance
            self.processing_times.append(processing_time)
            self.frame_count += 1
            
            # Check latency
            if processing_time > self.max_latency_ms:
                logger.warning(
                    f"Frame {frame_id} processing time {processing_time:.2f}ms "
                    f"exceeds max latency {self.max_latency_ms}ms"
                )
            
            return ProcessingResult(
                frame_id=frame_id,
                timestamp=timestamp,
                processing_time_ms=processing_time,
                prediction=prediction,
                confidence=confidence,
                annotations=annotations,
                surgical_guidance=surgical_guidance
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Error processing frame {frame_id}: {str(e)}")
            return ProcessingResult(
                frame_id=frame_id,
                timestamp=timestamp,
                processing_time_ms=processing_time,
                error=str(e)
            )

    def _run_inference(self, model: Any, input_data: np.ndarray, include_saliency: bool = False) -> Optional[Dict]:
        """اجرای inference با بهینه‌سازی"""
        try:
            # Try TensorFlow/Keras model
            if hasattr(model, 'predict'):
                if self.use_gpu:
                    # TensorFlow automatically uses GPU if available
                    pass
                
                # Batch prediction (even for single frame)
                input_batch = np.expand_dims(input_data, axis=0)
                predictions = model.predict(input_batch, verbose=0)
                
                # Extract results
                if isinstance(predictions, (list, tuple)):
                    prediction = predictions[0][0] if len(predictions[0]) > 0 else None
                else:
                    prediction = predictions[0] if len(predictions) > 0 else None
                
                confidence = float(np.max(predictions)) if prediction is not None else None
                
                result = {
                    "prediction": float(prediction) if prediction is not None else None,
                    "confidence": confidence,
                    "annotations": []
                }
                
                # Add saliency map if requested
                if include_saliency:
                    try:
                        from app.services.xai.saliency_maps import SaliencyMapGenerator, SaliencyMethod
                        generator = SaliencyMapGenerator(method=SaliencyMethod.GRAD_CAM)
                        saliency_result = generator.generate_saliency_map(
                            model=model,
                            image=input_data,
                            target_class=int(prediction) if prediction is not None else None
                        )
                        if saliency_result.get("success"):
                            result["saliency_map"] = saliency_result.get("overlay")
                            result["heatmap"] = saliency_result.get("heatmap_colored")
                    except Exception as e:
                        logger.warning(f"Could not generate saliency map: {str(e)}")
                
                return result
            
            # Try PyTorch model
            elif hasattr(model, '__call__'):
                import torch
                model.eval()
                
                with torch.no_grad():
                    if isinstance(input_data, np.ndarray):
                        input_tensor = torch.from_numpy(input_data)
                    else:
                        input_tensor = input_data
                    
                    if self.use_gpu and torch.cuda.is_available():
                        input_tensor = input_tensor.cuda()
                        model = model.cuda()
                    
                    # Add batch dimension
                    if len(input_tensor.shape) == 3:
                        input_tensor = input_tensor.unsqueeze(0)
                    
                    output = model(input_tensor)
                    
                    if isinstance(output, (list, tuple)):
                        output = output[0]
                    
                    # Get prediction and confidence
                    if hasattr(output, 'cpu'):
                        output = output.cpu().numpy()
                    
                    prediction = float(np.argmax(output[0])) if len(output[0]) > 0 else None
                    confidence = float(np.max(output[0])) if len(output[0]) > 0 else None
                    
                    return {
                        "prediction": prediction,
                        "confidence": confidence,
                        "annotations": []
                    }
            
        except Exception as e:
            logger.error(f"Inference error: {str(e)}")
            return None
        
        return None

    def get_performance_stats(self) -> Dict:
        """دریافت آمار عملکرد"""
        if not self.processing_times:
            return {
                "total_frames": 0,
                "avg_latency_ms": 0,
                "min_latency_ms": 0,
                "max_latency_ms": 0,
                "p95_latency_ms": 0,
                "p99_latency_ms": 0,
                "fps": 0,
                "latency_violations": 0
            }
        
        times = np.array(self.processing_times)
        avg_latency = np.mean(times)
        min_latency = np.min(times)
        max_latency = np.max(times)
        p95_latency = np.percentile(times, 95)
        p99_latency = np.percentile(times, 99)
        
        # Calculate FPS (frames per second)
        if avg_latency > 0:
            fps = 1000.0 / avg_latency
        else:
            fps = 0
        
        # Count latency violations
        violations = np.sum(times > self.max_latency_ms)
        
        return {
            "total_frames": self.frame_count,
            "avg_latency_ms": float(avg_latency),
            "min_latency_ms": float(min_latency),
            "max_latency_ms": float(max_latency),
            "p95_latency_ms": float(p95_latency),
            "p99_latency_ms": float(p99_latency),
            "fps": float(fps),
            "latency_violations": int(violations),
            "violation_rate": float(violations / len(times) * 100) if len(times) > 0 else 0,
            "device": self.device
        }


class VideoStreamProcessor:
    """پردازشگر جریان ویدیو بلادرنگ"""

    def __init__(
        self,
        model: Optional[Any] = None,
        target_fps: int = 30,
        max_latency_ms: float = 200.0,
        buffer_size: int = 5
    ):
        """
        Args:
            model: مدل ML برای inference
            target_fps: فریم‌های هدف در ثانیه
            max_latency_ms: حداکثر تأخیر مجاز
            buffer_size: اندازه بافر برای فریم‌ها
        """
        self.model = model
        self.frame_processor = VideoFrameProcessor(target_fps, max_latency_ms)
        self.buffer_size = buffer_size
        
        # Frame buffer
        self.frame_queue = Queue(maxsize=buffer_size)
        self.result_queue = Queue()
        
        # Processing thread
        self.processing_thread = None
        self.is_processing = False
        self.frame_id = 0
        
        logger.info(f"VideoStreamProcessor initialized with max_latency: {max_latency_ms}ms")

    def start_processing(self):
        """شروع پردازش"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        logger.info("Video stream processing started")

    def stop_processing(self):
        """توقف پردازش"""
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        logger.info("Video stream processing stopped")

    def add_frame(self, frame: np.ndarray) -> bool:
        """
        افزودن فریم به بافر پردازش
        
        Returns:
            True if frame was added, False if buffer is full
        """
        if self.frame_queue.full():
            # Remove oldest frame
            try:
                self.frame_queue.get_nowait()
            except:
                pass
        
        try:
            self.frame_queue.put_nowait((self.frame_id, frame))
            self.frame_id += 1
            return True
        except:
            return False

    def get_result(self, timeout: float = 0.1) -> Optional[ProcessingResult]:
        """دریافت نتیجه پردازش"""
        try:
            return self.result_queue.get(timeout=timeout)
        except:
            return None

    def _processing_loop(self):
        """حلقه پردازش فریم‌ها"""
        while self.is_processing:
            try:
                # Get frame from queue
                try:
                    frame_id, frame = self.frame_queue.get(timeout=0.1)
                except:
                    continue
                
                # Process frame
                result = self.frame_processor.process_frame(
                    frame=frame,
                    model=self.model,
                    frame_id=frame_id
                )
                
                # Add result to queue
                try:
                    self.result_queue.put_nowait(result)
                except:
                    # Result queue is full, remove oldest
                    try:
                        self.result_queue.get_nowait()
                        self.result_queue.put_nowait(result)
                    except:
                        pass
                
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}")
                time.sleep(0.01)

    def get_performance_stats(self) -> Dict:
        """دریافت آمار عملکرد"""
        return self.frame_processor.get_performance_stats()

