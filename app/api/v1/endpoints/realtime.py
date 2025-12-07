"""
Real-Time Video Processing API Endpoints
API برای پردازش بلادرنگ ویدیو در اتاق آندوسکوپی
"""
import time
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import numpy as np
import cv2
import io
from pydantic import BaseModel

from app.services.realtime.video_processor import VideoStreamProcessor, VideoFrameProcessor
from app.services.realtime.edge_computing import EdgeComputingManager
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class VideoProcessingRequest(BaseModel):
    """درخواست پردازش ویدیو"""
    model_id: Optional[str] = None
    target_fps: int = 30
    max_latency_ms: float = 200.0
    enable_annotations: bool = True


class ProcessingStatsResponse(BaseModel):
    """پاسخ آمار پردازش"""
    total_frames: int
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    fps: float
    latency_violations: int
    violation_rate: float
    device: str


# Global processor instance (in production, use proper session management)
_processor: Optional[VideoStreamProcessor] = None
_edge_manager: Optional[EdgeComputingManager] = None


def get_edge_manager() -> EdgeComputingManager:
    """Get or create edge computing manager"""
    global _edge_manager
    if _edge_manager is None:
        _edge_manager = EdgeComputingManager()
    return _edge_manager


@router.post("/video/process-frame")
async def process_video_frame(
    file: UploadFile = File(...),
    model_id: Optional[str] = None,
    max_latency_ms: float = 200.0
):
    """
    پردازش یک فریم ویدیو با تأخیر کم
    
    برای استفاده در اتاق آندوسکوپی با تأخیر زیر 200ms
    """
    start_time = time.time()
    
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Load model if provided
        model = None
        if model_id:
            try:
                from app.services.ml_models.model_registry import ModelRegistry
                registry = ModelRegistry()
                model_info = registry.get_model(model_id)
                
                if model_info:
                    # Load model (simplified - in production, use model cache)
                    # This would load the actual model
                    pass
            except Exception as e:
                logger.warning(f"Could not load model {model_id}: {str(e)}")
        
        # Optimize model for edge computing
        edge_manager = get_edge_manager()
        if model:
            model = edge_manager.optimize_model_for_edge(model)
        
        # Process frame
        processor = VideoFrameProcessor(target_fps=30, max_latency_ms=max_latency_ms)
        result = processor.process_frame(
            frame, 
            model, 
            frame_id=0,
            include_surgical_guidance=True  # Enable surgical guidance
        )
        
        total_time = (time.time() - start_time) * 1000
        
        response = {
            "frame_id": result.frame_id,
            "processing_time_ms": result.processing_time_ms,
            "total_time_ms": total_time,
            "prediction": result.prediction,
            "confidence": result.confidence,
            "annotations": result.annotations,
            "error": result.error,
            "meets_latency_requirement": result.processing_time_ms <= max_latency_ms
        }
        
        # Add surgical guidance if available
        if result.surgical_guidance:
            response["surgical_guidance"] = result.surgical_guidance
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing video frame: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing frame: {str(e)}")


@router.websocket("/video/stream")
async def video_stream_websocket(websocket: WebSocket):
    """
    WebSocket endpoint برای پردازش جریان ویدیو بلادرنگ
    
    Client sends video frames, server returns processing results
    """
    await websocket.accept()
    
    processor = None
    
    try:
        # Initialize processor
        edge_manager = get_edge_manager()
        processor = VideoStreamProcessor(
            model=None,  # Model would be loaded based on configuration
            target_fps=30,
            max_latency_ms=200.0
        )
        processor.start_processing()
        
        frame_id = 0
        
        while True:
            # Receive frame from client
            try:
                data = await websocket.receive_bytes()
                
                # Decode frame
                nparr = np.frombuffer(data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
                
                # Add frame to processor
                processor.add_frame(frame)
                
                # Get result (non-blocking)
                result = processor.get_result(timeout=0.05)
                
                if result:
                    # Send result back to client
                    response = {
                        "frame_id": result.frame_id,
                        "processing_time_ms": result.processing_time_ms,
                        "prediction": result.prediction,
                        "confidence": result.confidence,
                        "annotations": result.annotations,
                        "error": result.error
                    }
                    
                    # Add surgical guidance if available
                    if result.surgical_guidance:
                        response["surgical_guidance"] = result.surgical_guidance
                    
                    await websocket.send_json(response)
                
                frame_id += 1
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in video stream: {str(e)}")
                await websocket.send_json({"error": str(e)})
                break
    
    finally:
        if processor:
            processor.stop_processing()


@router.get("/video/stats", response_model=ProcessingStatsResponse)
async def get_processing_stats():
    """دریافت آمار عملکرد پردازش"""
    global _processor
    
    if _processor is None:
        raise HTTPException(status_code=404, detail="No active video processing session")
    
    stats = _processor.get_performance_stats()
    return ProcessingStatsResponse(**stats)


@router.get("/edge/device-info")
async def get_edge_device_info():
    """دریافت اطلاعات دستگاه Edge"""
    edge_manager = get_edge_manager()
    info = edge_manager.get_device_info()
    return info


@router.post("/video/start-stream")
async def start_video_stream(request: VideoProcessingRequest):
    """شروع جریان پردازش ویدیو"""
    global _processor
    
    try:
        # Load model if provided
        model = None
        if request.model_id:
            from app.services.ml_models.model_registry import ModelRegistry
            registry = ModelRegistry()
            model_info = registry.get_model(request.model_id)
            
            if model_info:
                # Load model (simplified)
                pass
        
        # Optimize for edge
        edge_manager = get_edge_manager()
        if model:
            model = edge_manager.optimize_model_for_edge(model)
        
        # Create processor
        _processor = VideoStreamProcessor(
            model=model,
            target_fps=request.target_fps,
            max_latency_ms=request.max_latency_ms
        )
        _processor.start_processing()
        
        return {
            "status": "started",
            "target_fps": request.target_fps,
            "max_latency_ms": request.max_latency_ms,
            "device": edge_manager.device_type.value
        }
        
    except Exception as e:
        logger.error(f"Error starting video stream: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting stream: {str(e)}")


@router.post("/video/stop-stream")
async def stop_video_stream():
    """توقف جریان پردازش ویدیو"""
    global _processor
    
    if _processor:
        _processor.stop_processing()
        stats = _processor.get_performance_stats()
        _processor = None
        
        return {
            "status": "stopped",
            "final_stats": stats
        }
    
    return {"status": "no_active_stream"}

