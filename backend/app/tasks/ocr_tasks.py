try:
    from celery import Celery
    from app.core.config import settings
    CELERY_AVAILABLE = True
    
    celery_app = Celery(
        'scoring_system',
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=['app.tasks.ocr_tasks']
    )
    
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Shanghai',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50,
    )
except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None


def _mock_task(func):
    """模拟 Celery task 装饰器"""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.delay = lambda *a, **kw: func(*a, **kw)
    wrapper.apply_async = lambda *a, **kw: func(*a, **kw)
    return wrapper


def _do_process_scan_image(exam_id: int, subject_id: int, file_url: str,
                           page_number: int = 1, student_id: int = None):
    """实际处理扫描图片"""
    from app.core.database import SessionLocal
    from app.models.scan import ScanPage
    from app.services.ocr_processor import AnswerCardOCRProcessor

    db = SessionLocal()
    try:
        # 查找或创建 ScanPage 记录
        scan_page = db.query(ScanPage).filter(
            ScanPage.exam_id == exam_id,
            ScanPage.subject_id == subject_id,
            ScanPage.file_url == file_url
        ).first()

        if not scan_page:
            scan_page = ScanPage(
                exam_id=exam_id,
                subject_id=subject_id,
                page_number=page_number,
                file_url=file_url,
                student_id=student_id,
                status="pending"
            )
            db.add(scan_page)
            db.commit()
            db.refresh(scan_page)

        processor = AnswerCardOCRProcessor(db)
        result = processor.process_scan_page(scan_page)
        return result
    except Exception as exc:
        print(f"OCR 识别失败: {str(exc)}")
        import traceback
        traceback.print_exc()
        return {'status': 'failed', 'message': str(exc)}
    finally:
        db.close()


if CELERY_AVAILABLE:
    @celery_app.task(bind=True, max_retries=3)
    def process_scan_image(self, exam_id: int, subject_id: int,
                           file_url: str, page_number: int = 1,
                           student_id: int = None):
        result = _do_process_scan_image(exam_id, subject_id, file_url, page_number, student_id)
        if result.get('status') == 'failed':
            raise self.retry(exc=Exception(result.get('message', 'Unknown error')), countdown=60)
        return result

    @celery_app.task
    def generate_report(exam_id: int, report_type: str = 'subject'):
        print(f"生成报告: exam_id={exam_id}, type={report_type}")
        return {'status': 'success', 'exam_id': exam_id, 'report_type': report_type}
else:
    @_mock_task
    def process_scan_image(exam_id: int, subject_id: int,
                           file_url: str, page_number: int = 1,
                           student_id: int = None):
        print(f"[直接处理] 处理图片: exam_id={exam_id}, file={file_url}")
        return _do_process_scan_image(exam_id, subject_id, file_url, page_number, student_id)

    @_mock_task
    def generate_report(exam_id: int, report_type: str = 'subject'):
        print(f"[模拟] 生成报告: exam_id={exam_id}, type={report_type}")
        return {'status': 'success', 'exam_id': exam_id, 'report_type': report_type}
