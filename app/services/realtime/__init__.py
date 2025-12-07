"""
Real-Time Processing Module
ماژول پردازش بلادرنگ برای استفاده در اتاق آندوسکوپی
"""
from app.services.realtime.video_processor import (
    VideoFrameProcessor,
    VideoStreamProcessor,
    ProcessingResult
)
from app.services.realtime.edge_computing import (
    EdgeComputingManager,
    EdgeDeviceType
)

__all__ = [
    "VideoFrameProcessor",
    "VideoStreamProcessor",
    "ProcessingResult",
    "EdgeComputingManager",
    "EdgeDeviceType",
]

