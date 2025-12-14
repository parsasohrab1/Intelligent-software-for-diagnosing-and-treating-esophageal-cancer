"""
Script to create initial training modules
ایجاد ماژول‌های آموزش اولیه
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from app.core.database import SessionLocal
from app.services.training.training_system import TrainingSystem, TrainingType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_initial_modules():
    """ایجاد ماژول‌های آموزش اولیه"""
    db = SessionLocal()
    training_system = TrainingSystem(db)
    
    modules = [
        {
            "title": "معرفی سیستم",
            "training_type": TrainingType.SYSTEM_OVERVIEW,
            "description": "آشنایی با سیستم تشخیص و درمان سرطان مری",
            "content": """
# معرفی سیستم

این سیستم یک پلتفرم جامع برای تشخیص و درمان سرطان مری است که شامل:

- مدیریت بیماران
- تحلیل تصاویر پزشکی
- پشتیبانی از تصمیم‌گیری بالینی
- پیش‌بینی پاسخ به درمان
- راهنمای جراحی Real-Time
            """,
            "duration_minutes": 30,
            "difficulty_level": "beginner",
            "order": 1
        },
        {
            "title": "مدیریت بیماران",
            "training_type": TrainingType.PATIENT_MANAGEMENT,
            "description": "آموزش استفاده از سیستم مدیریت بیماران",
            "content": """
# مدیریت بیماران

این ماژول شامل:
- افزودن بیمار جدید
- مشاهده اطلاعات بیمار
- افزودن داده‌های بالینی
- مدیریت رضایت‌نامه‌ها
            """,
            "duration_minutes": 45,
            "difficulty_level": "beginner",
            "order": 2
        },
        {
            "title": "تحلیل تصاویر پزشکی",
            "training_type": TrainingType.IMAGING_ANALYSIS,
            "description": "آموزش استفاده از سیستم تحلیل تصاویر",
            "content": """
# تحلیل تصاویر پزشکی

این ماژول شامل:
- آپلود تصاویر
- تحلیل خودکار
- تفسیر نتایج
- استفاده از Explainable AI
            """,
            "duration_minutes": 60,
            "difficulty_level": "intermediate",
            "order": 3
        },
        {
            "title": "پشتیبانی از تصمیم‌گیری بالینی (CDS)",
            "training_type": TrainingType.CDS_USAGE,
            "description": "آموزش استفاده از سیستم CDS",
            "content": """
# پشتیبانی از تصمیم‌گیری بالینی

این ماژول شامل:
- پیش‌بینی ریسک
- توصیه‌های درمانی
- امتیاز پیش‌آگهی
- تطبیق با کارآزمایی‌های بالینی
            """,
            "duration_minutes": 45,
            "difficulty_level": "intermediate",
            "order": 4
        },
        {
            "title": "راهنمای جراحی Real-Time",
            "training_type": TrainingType.ADVANCED_FEATURES,
            "description": "آموزش استفاده از سیستم راهنمای جراحی",
            "content": """
# راهنمای جراحی Real-Time

این ماژول شامل:
- تشخیص مرزهای تومور
- تخمین عمق نفوذ
- محاسبه حاشیه امن
- استفاده در حین عمل
            """,
            "duration_minutes": 60,
            "difficulty_level": "advanced",
            "order": 5
        },
        {
            "title": "امنیت و حریم خصوصی",
            "training_type": TrainingType.SECURITY,
            "description": "آموزش امنیت داده و حریم خصوصی",
            "content": """
# امنیت و حریم خصوصی

این ماژول شامل:
- کنترل دسترسی
- رمزگذاری داده
- مدیریت رضایت‌نامه
- انطباق با HIPAA/GDPR
            """,
            "duration_minutes": 30,
            "difficulty_level": "beginner",
            "order": 6
        },
        {
            "title": "استفاده از API",
            "training_type": TrainingType.API_USAGE,
            "description": "آموزش استفاده از API برای توسعه‌دهندگان",
            "content": """
# استفاده از API

این ماژول شامل:
- احراز هویت
- Endpoints اصلی
- مثال‌های استفاده
- یکپارچه‌سازی
            """,
            "duration_minutes": 90,
            "difficulty_level": "advanced",
            "order": 7
        }
    ]
    
    created_count = 0
    for module_data in modules:
        try:
            training_system.create_module(
                title=module_data["title"],
                training_type=module_data["training_type"],
                description=module_data["description"],
                content=module_data["content"],
                duration_minutes=module_data["duration_minutes"],
                difficulty_level=module_data["difficulty_level"],
                order=module_data["order"]
            )
            created_count += 1
            logger.info(f"✅ Created module: {module_data['title']}")
        except Exception as e:
            logger.warning(f"Could not create module {module_data['title']}: {str(e)}")
    
    logger.info(f"✅ Created {created_count} training modules")
    db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Creating Initial Training Modules")
    print("=" * 60)
    create_initial_modules()
    print("=" * 60)

