"""
Surgical Guidance API Endpoints
API برای راهنمای جراحی Real-Time
"""
import logging
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import numpy as np
import cv2

from app.core.security.dependencies import get_current_user_with_role, require_role
from app.core.security.rbac import Role
from app.models.user import User
from app.services.surgical_guidance.surgical_guidance_system import (
    SurgicalGuidanceSystem,
    EndoscopyMode
)

logger = logging.getLogger(__name__)

router = APIRouter()


class SurgicalGuidanceRequest(BaseModel):
    """Request for surgical guidance"""
    endoscopy_mode: str = Field("auto", description="Endoscopy mode: nbi, wli, or auto")
    custom_margin_mm: Optional[float] = Field(None, description="Custom margin in mm")


@router.post("/process-frame")
async def process_frame_surgical_guidance(
    file: UploadFile = File(...),
    endoscopy_mode: str = Query("auto"),
    custom_margin_mm: Optional[float] = Query(None),
    current_user: User = Depends(get_current_user_with_role)
):
    """
    پردازش یک فریم برای راهنمای جراحی
    
    مشخص کردن مرزهای تومور، تخمین عمق نفوذ، و تعیین حاشیه امن برداشت
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Convert mode
        try:
            mode = EndoscopyMode(endoscopy_mode.lower())
        except ValueError:
            mode = EndoscopyMode.AUTO
        
        # Process
        guidance_system = SurgicalGuidanceSystem(endoscopy_mode=mode)
        result = guidance_system.process_frame(
            frame=frame,
            frame_id=0,
            endoscopy_mode=mode,
            custom_margin_mm=custom_margin_mm
        )
        
        if result.error:
            raise HTTPException(status_code=500, detail=result.error)
        
        # Encode overlay image
        _, buffer = cv2.imencode('.jpg', result.overlay_image)
        overlay_base64 = np.frombuffer(buffer, dtype=np.uint8).tobytes()
        
        return {
            "frame_id": result.frame_id,
            "processing_time_ms": result.processing_time_ms,
            "tumor_count": len(result.segmentation.tumor_boundaries),
            "tumor_boundaries": [
                {
                    "area": b.area,
                    "perimeter": b.perimeter,
                    "centroid": b.centroid,
                    "bbox": b.bbox,
                    "confidence": b.confidence
                }
                for b in result.segmentation.tumor_boundaries
            ],
            "depth_estimation": {
                "mean_depth_mm": result.depth_estimation.mean_depth_mm,
                "max_depth_mm": result.depth_estimation.max_depth_mm,
                "min_depth_mm": result.depth_estimation.min_depth_mm,
                "invasion_level": result.depth_estimation.invasion_level,
                "confidence": result.depth_estimation.confidence
            },
            "safe_margin": {
                "margin_distance_mm": result.safe_margin.margin_distance_mm,
                "resection_area_mm2": result.safe_margin.resection_area_mm2,
                "safety_score": result.safe_margin.safety_score,
                "recommendations": result.safe_margin.recommendations
            },
            "overlay_image_base64": overlay_base64.hex(),  # Return as hex for JSON
            "segmentation_confidence": result.segmentation.confidence
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing frame for surgical guidance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing frame: {str(e)}")


@router.websocket("/real-time-stream")
async def real_time_surgical_guidance(websocket: WebSocket):
    """
    WebSocket endpoint برای راهنمای جراحی Real-Time
    
    Client sends video frames, server returns surgical guidance results
    """
    await websocket.accept()
    
    guidance_system = SurgicalGuidanceSystem()
    frame_id = 0
    
    try:
        while True:
            # Receive frame
            try:
                data = await websocket.receive_bytes()
                
                # Decode frame
                nparr = np.frombuffer(data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
                
                # Process frame
                result = guidance_system.process_frame(
                    frame=frame,
                    frame_id=frame_id
                )
                
                # Send result
                response = {
                    "frame_id": result.frame_id,
                    "processing_time_ms": result.processing_time_ms,
                    "tumor_count": len(result.segmentation.tumor_boundaries),
                    "tumor_boundaries": [
                        {
                            "area": float(b.area),
                            "perimeter": float(b.perimeter),
                            "centroid": b.centroid,
                            "bbox": b.bbox,
                            "confidence": float(b.confidence)
                        }
                        for b in result.segmentation.tumor_boundaries
                    ],
                    "depth_estimation": {
                        "mean_depth_mm": float(result.depth_estimation.mean_depth_mm),
                        "max_depth_mm": float(result.depth_estimation.max_depth_mm),
                        "min_depth_mm": float(result.depth_estimation.min_depth_mm),
                        "invasion_level": result.depth_estimation.invasion_level,
                        "confidence": float(result.depth_estimation.confidence)
                    },
                    "safe_margin": {
                        "margin_distance_mm": float(result.safe_margin.margin_distance_mm),
                        "resection_area_mm2": float(result.safe_margin.resection_area_mm2),
                        "safety_score": float(result.safe_margin.safety_score),
                        "recommendations": result.safe_margin.recommendations
                    },
                    "segmentation_confidence": float(result.segmentation.confidence),
                    "meets_latency_requirement": result.processing_time_ms <= 200.0
                }
                
                await websocket.send_json(response)
                
                frame_id += 1
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in real-time stream: {str(e)}")
                await websocket.send_json({"error": str(e)})
                break
                
    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}")
    finally:
        await websocket.close()


@router.get("/margin-standards")
async def get_margin_standards(
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت استانداردهای حاشیه امن"""
    return {
        "margin_standards": {
            "superficial": {
                "margin_mm": 2.0,
                "description": "Superficial invasion (<1mm) - mucosa only"
            },
            "moderate": {
                "margin_mm": 5.0,
                "description": "Moderate invasion (1-3mm) - submucosa"
            },
            "deep": {
                "margin_mm": 10.0,
                "description": "Deep invasion (>3mm) - muscularis propria or beyond"
            }
        },
        "note": "These are general guidelines. Clinical judgment should always be used."
    }

