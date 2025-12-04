"""
Multi-Modality Data Processing Endpoints
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Optional
from pydantic import BaseModel, Field

from app.services.data_processing.multi_modality import MultiModalityProcessor

router = APIRouter()


class ProcessTextRequest(BaseModel):
    """Request model for processing text report"""
    text: str = Field(..., description="Text report content")
    report_type: str = Field("clinical", description="Type of report (clinical, radiology, etc.)")


@router.post("/process-image")
async def process_image(
    file: UploadFile = File(...),
    modality: str = Form("CT", description="Imaging modality (CT, MRI, etc.)"),
    text_report: Optional[str] = Form(None, description="Optional text report"),
):
    """Process medical image with optional text report"""
    try:
        import tempfile
        import os

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            processor = MultiModalityProcessor()
            result = processor.process_imaging_data(
                image_path=tmp_path,
                modality=modality,
                text_report=text_report,
            )
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/process-text")
async def process_text(request: ProcessTextRequest):
    """Process unstructured text report"""
    try:
        processor = MultiModalityProcessor()
        result = processor.process_text_only(
            text=request.text,
            report_type=request.report_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


@router.post("/process-multi-modality")
async def process_multi_modality(
    file: UploadFile = File(...),
    modality: str = Form("CT"),
    text_report: str = Form(...),
):
    """Process both image and text report together"""
    try:
        import tempfile
        import os

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            processor = MultiModalityProcessor()
            result = processor.process_imaging_data(
                image_path=tmp_path,
                modality=modality,
                text_report=text_report,
            )
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing multi-modality data: {str(e)}")

