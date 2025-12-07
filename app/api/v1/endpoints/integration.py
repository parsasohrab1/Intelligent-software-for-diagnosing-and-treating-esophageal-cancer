"""
Clinical System Integration API Endpoints
API برای یکپارچه‌سازی با سیستم‌های کلینیک (PACS, Endoscopy, EHR)
"""
import logging
from typing import Dict, Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from pydantic import BaseModel, Field

from app.core.security.dependencies import get_current_user_with_role, require_role
from app.core.security.rbac import Role
from app.models.user import User
from app.services.integration.pacs_integration import PACSIntegration, PACSConnection
from app.services.integration.endoscopy_integration import EndoscopyIntegration, EndoscopyConnection, EndoscopySystemType
from app.services.integration.ehr_integration import EHRIntegration, EHRConnection, EHRSystemType
from app.services.integration.integration_adapter import (
    IntegrationManager,
    PACSAdapter,
    EndoscopyAdapter,
    EHRAdapter,
    IntegrationType
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global integration manager
_integration_manager: Optional[IntegrationManager] = None


def get_integration_manager() -> IntegrationManager:
    """Get or create integration manager"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager()
    return _integration_manager


# ========== PACS Integration ==========

class PACSConnectionRequest(BaseModel):
    """Request for PACS connection"""
    host: str
    port: int
    ae_title: str
    use_tls: bool = False


@router.post("/pacs/connect")
async def connect_pacs(
    request: PACSConnectionRequest,
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.DATA_ENGINEER))
):
    """اتصال به سیستم PACS"""
    try:
        connection = PACSConnection(
            host=request.host,
            port=request.port,
            ae_title=request.ae_title,
            use_tls=request.use_tls
        )
        
        adapter = PACSAdapter(connection)
        success = adapter.connect()
        
        if success:
            manager = get_integration_manager()
            manager.register_adapter(IntegrationType.PACS, adapter)
        
        return {
            "success": success,
            "system": "pacs",
            "ae_title": request.ae_title
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to PACS: {str(e)}")


@router.post("/pacs/store-image")
async def store_dicom_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_with_role)
):
    """ذخیره تصویر DICOM در PACS"""
    try:
        import tempfile
        import os
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            manager = get_integration_manager()
            pacs_adapter = manager.adapters.get(IntegrationType.PACS)
            
            if not pacs_adapter:
                raise HTTPException(status_code=400, detail="PACS not connected")
            
            # Store image
            result = pacs_adapter.integration.store_image(tmp_path)
            return result
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing image: {str(e)}")


@router.get("/pacs/find-studies")
async def find_pacs_studies(
    patient_id: Optional[str] = Query(None),
    study_date: Optional[str] = Query(None),
    modality: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_with_role)
):
    """جستجوی مطالعات در PACS"""
    try:
        manager = get_integration_manager()
        pacs_adapter = manager.adapters.get(IntegrationType.PACS)
        
        if not pacs_adapter:
            raise HTTPException(status_code=400, detail="PACS not connected")
        
        studies = pacs_adapter.integration.find_studies(
            patient_id=patient_id,
            study_date=study_date,
            modality=modality
        )
        
        return {"studies": studies, "count": len(studies)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding studies: {str(e)}")


# ========== Endoscopy Integration ==========

class EndoscopyConnectionRequest(BaseModel):
    """Request for Endoscopy connection"""
    system_type: EndoscopySystemType
    host: Optional[str] = None
    port: Optional[int] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None


@router.post("/endoscopy/connect")
async def connect_endoscopy(
    request: EndoscopyConnectionRequest,
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.DATA_ENGINEER))
):
    """اتصال به سیستم آندوسکوپی"""
    try:
        connection = EndoscopyConnection(
            system_type=request.system_type,
            host=request.host,
            port=request.port,
            api_endpoint=request.api_endpoint,
            api_key=request.api_key
        )
        
        adapter = EndoscopyAdapter(connection)
        success = adapter.connect()
        
        if success:
            manager = get_integration_manager()
            manager.register_adapter(IntegrationType.ENDOSCOPY, adapter)
        
        return {
            "success": success,
            "system": "endoscopy",
            "system_type": request.system_type.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Endoscopy: {str(e)}")


@router.get("/endoscopy/video-stream")
async def get_endoscopy_video_stream(
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت جریان ویدیو از سیستم آندوسکوپی"""
    try:
        manager = get_integration_manager()
        endoscopy_adapter = manager.adapters.get(IntegrationType.ENDOSCOPY)
        
        if not endoscopy_adapter:
            raise HTTPException(status_code=400, detail="Endoscopy system not connected")
        
        stream_url = endoscopy_adapter.integration.get_live_video_stream()
        
        if stream_url:
            return {"stream_url": stream_url, "format": "rtsp"}
        else:
            raise HTTPException(status_code=404, detail="Video stream not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting video stream: {str(e)}")


@router.post("/endoscopy/send-analysis")
async def send_analysis_to_endoscopy(
    procedure_id: str = Query(...),
    analysis_result: Dict = Query(...),
    annotations: Optional[List[Dict]] = Query(None),
    current_user: User = Depends(get_current_user_with_role)
):
    """ارسال نتیجه تحلیل به سیستم آندوسکوپی"""
    try:
        manager = get_integration_manager()
        endoscopy_adapter = manager.adapters.get(IntegrationType.ENDOSCOPY)
        
        if not endoscopy_adapter:
            raise HTTPException(status_code=400, detail="Endoscopy system not connected")
        
        success = endoscopy_adapter.integration.send_analysis_result(
            procedure_id=procedure_id,
            analysis_result=analysis_result,
            annotations=annotations or []
        )
        
        return {"success": success, "procedure_id": procedure_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending analysis: {str(e)}")


# ========== EHR Integration ==========

class EHRConnectionRequest(BaseModel):
    """Request for EHR connection"""
    system_type: EHRSystemType
    fhir_base_url: Optional[str] = None
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    use_oauth: bool = True


@router.post("/ehr/connect")
async def connect_ehr(
    request: EHRConnectionRequest,
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR, Role.DATA_ENGINEER))
):
    """اتصال به سیستم EHR"""
    try:
        connection = EHRConnection(
            system_type=request.system_type,
            fhir_base_url=request.fhir_base_url,
            api_key=request.api_key,
            client_id=request.client_id,
            client_secret=request.client_secret,
            use_oauth=request.use_oauth
        )
        
        adapter = EHRAdapter(connection)
        success = adapter.connect()
        
        if success:
            manager = get_integration_manager()
            manager.register_adapter(IntegrationType.EHR, adapter)
        
        return {
            "success": success,
            "system": "ehr",
            "system_type": request.system_type.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to EHR: {str(e)}")


@router.get("/ehr/patient/{patient_id}")
async def get_ehr_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت اطلاعات بیمار از EHR"""
    try:
        manager = get_integration_manager()
        ehr_adapter = manager.adapters.get(IntegrationType.EHR)
        
        if not ehr_adapter:
            raise HTTPException(status_code=400, detail="EHR not connected")
        
        patient_data = ehr_adapter.get_patient_data(patient_id)
        
        if patient_data:
            return patient_data
        else:
            raise HTTPException(status_code=404, detail="Patient not found in EHR")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting patient: {str(e)}")


@router.post("/ehr/create-observation")
async def create_ehr_observation(
    patient_id: str = Query(...),
    observation_data: Dict = Query(...),
    current_user: User = Depends(get_current_user_with_role)
):
    """ایجاد Observation در EHR"""
    try:
        manager = get_integration_manager()
        ehr_adapter = manager.adapters.get(IntegrationType.EHR)
        
        if not ehr_adapter:
            raise HTTPException(status_code=400, detail="EHR not connected")
        
        observation = ehr_adapter.integration.create_observation(
            patient_id=patient_id,
            observation_data=observation_data
        )
        
        if observation:
            return {"success": True, "observation": observation}
        else:
            raise HTTPException(status_code=500, detail="Failed to create observation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating observation: {str(e)}")


@router.post("/ehr/create-diagnostic-report")
async def create_ehr_diagnostic_report(
    patient_id: str = Query(...),
    report_data: Dict = Query(...),
    current_user: User = Depends(get_current_user_with_role)
):
    """ایجاد Diagnostic Report در EHR"""
    try:
        manager = get_integration_manager()
        ehr_adapter = manager.adapters.get(IntegrationType.EHR)
        
        if not ehr_adapter:
            raise HTTPException(status_code=400, detail="EHR not connected")
        
        report = ehr_adapter.integration.create_diagnostic_report(
            patient_id=patient_id,
            report_data=report_data
        )
        
        if report:
            return {"success": True, "report": report}
        else:
            raise HTTPException(status_code=500, detail="Failed to create diagnostic report")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating diagnostic report: {str(e)}")


# ========== Unified Integration ==========

@router.get("/status")
async def get_integration_status(
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت وضعیت اتصال تمام سیستم‌ها"""
    try:
        manager = get_integration_manager()
        status = manager.get_connection_status()
        return {"integrations": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.post("/connect-all")
async def connect_all_systems(
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """اتصال به تمام سیستم‌ها"""
    try:
        manager = get_integration_manager()
        results = manager.connect_all()
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting: {str(e)}")


@router.post("/disconnect-all")
async def disconnect_all_systems(
    current_user: User = Depends(require_role(Role.SYSTEM_ADMINISTRATOR))
):
    """قطع اتصال از تمام سیستم‌ها"""
    try:
        manager = get_integration_manager()
        results = manager.disconnect_all()
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting: {str(e)}")


@router.get("/patient/{patient_id}/all-systems")
async def get_patient_data_from_all(
    patient_id: str,
    current_user: User = Depends(get_current_user_with_role)
):
    """دریافت داده‌های بیمار از تمام سیستم‌ها"""
    try:
        manager = get_integration_manager()
        data = manager.get_patient_data_from_all(patient_id)
        return {
            "patient_id": patient_id,
            "data": data,
            "sources": list(data.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting patient data: {str(e)}")


@router.post("/patient/{patient_id}/send-results")
async def send_results_to_all_systems(
    patient_id: str,
    results: Dict,
    current_user: User = Depends(get_current_user_with_role)
):
    """ارسال نتایج به تمام سیستم‌ها"""
    try:
        manager = get_integration_manager()
        send_results = manager.send_results_to_all(patient_id, results)
        return {
            "patient_id": patient_id,
            "results": send_results,
            "all_successful": all(send_results.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending results: {str(e)}")

