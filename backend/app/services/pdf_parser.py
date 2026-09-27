import fitz
from PIL import Image
import io
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class PDFPage:
    """PDF 页面信息"""
    page_number: int
    image: np.ndarray
    width: int
    height: int
    dpi: float
    format: str


@dataclass
class PDFParseResult:
    """PDF 解析结果"""
    total_pages: int
    pages: List[PDFPage]
    metadata: Dict
    file_size: int


class PDFParser:
    """PDF 解析器"""
    
    def __init__(self, target_dpi: int = 300):
        self.target_dpi = target_dpi
        self.min_dpi = 200
    
    def parse(self, pdf_path: str, 
              page_range: Optional[Tuple[int, int]] = None) -> PDFParseResult:
        """解析 PDF 文件，提取所有页面为图片"""
        doc = fitz.open(pdf_path)
        
        total_pages = doc.page_count
        start_page = page_range[0] if page_range else 0
        end_page = page_range[1] if page_range else total_pages
        
        pages = []
        
        for page_num in range(start_page, min(end_page, total_pages)):
            page = doc[page_num]
            
            page_image = self._extract_page_image(page)
            detected_dpi = self._detect_dpi(page, page_image)
            
            if detected_dpi < self.min_dpi:
                page_image = self._extract_page_image(page, force_dpi=self.target_dpi)
                detected_dpi = self.target_dpi
            
            pages.append(PDFPage(
                page_number=page_num + 1,
                image=page_image,
                width=page_image.shape[1],
                height=page_image.shape[0],
                dpi=detected_dpi,
                format='jpeg'
            ))
        
        doc.close()
        
        return PDFParseResult(
            total_pages=len(pages),
            pages=pages,
            metadata={
                'original_pages': total_pages,
                'extracted_pages': len(pages),
                'target_dpi': self.target_dpi
            },
            file_size=os.path.getsize(pdf_path)
        )
    
    def _extract_page_image(self, page: fitz.Page, 
                            force_dpi: Optional[int] = None) -> np.ndarray:
        """提取单页为图片"""
        if force_dpi:
            target_width = int(8.27 * force_dpi)
            target_height = int(11.69 * force_dpi)
            
            rect = page.rect
            zoom_x = target_width / rect.width
            zoom_y = target_height / rect.height
            mat = fitz.Matrix(zoom_x, zoom_y)
        else:
            mat = fitz.Matrix(2, 2)
        
        pix = page.get_pixmap(matrix=mat)
        
        img_data = pix.tobytes("png")
        nparr = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return image
    
    def _detect_dpi(self, page: fitz.Page, image: np.ndarray) -> float:
        """检测 PDF 页面的实际 DPI"""
        rect = page.rect
        page_width_inches = rect.width / 72
        
        image_width = image.shape[1]
        dpi = image_width / page_width_inches
        
        return dpi
    
    def detect_student_id(self, page_image: np.ndarray) -> Optional[str]:
        """从页面中检测学号"""
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            return None
        
        h, w = page_image.shape[:2]
        top_region = page_image[0:h//4, :]
        
        ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        result = ocr.ocr(top_region, cls=True)
        
        if result[0]:
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                
                import re
                match = re.search(r'\b\d{6,20}\b', text)
                if match and confidence > 0.7:
                    return match.group()
        
        return None


class PDFUploadService:
    """PDF 上传服务"""
    
    def __init__(self, parser: PDFParser, storage_service):
        self.parser = parser
        self.storage = storage_service
    
    async def process_upload(self, pdf_file: bytes, metadata: Dict) -> Dict:
        """处理 PDF 上传"""
        temp_path = f"/tmp/upload_{metadata['upload_id']}.pdf"
        with open(temp_path, 'wb') as f:
            f.write(pdf_file)
        
        try:
            parse_result = self.parser.parse(temp_path)
            
            saved_pages = []
            for page in parse_result.pages:
                file_url = await self.storage.save_image_from_array(
                    image=page.image,
                    exam_id=metadata['exam_id'],
                    subject_id=metadata['subject_id'],
                    filename=f"page_{page.page_number}.jpg"
                )
                
                saved_pages.append({
                    'page_number': page.page_number,
                    'file_url': file_url,
                    'width': page.width,
                    'height': page.height,
                    'dpi': page.dpi
                })
            
            student_bindings = await self._bind_students(
                parse_result, metadata
            )
            
            return {
                'success': True,
                'total_pages': parse_result.total_pages,
                'pages': saved_pages,
                'student_bindings': student_bindings,
                'metadata': parse_result.metadata
            }
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    async def _bind_students(self, parse_result: PDFParseResult, 
                             metadata: Dict) -> List[Dict]:
        """关联学生"""
        bindings = []
        
        student_list = metadata.get('student_list', [])
        binding_mode = metadata.get('binding_mode', 'auto')
        
        for i, page in enumerate(parse_result.pages):
            binding = {
                'page_number': page.page_number,
                'student_id': None,
                'student_name': None,
                'status': 'pending'
            }
            
            if binding_mode == 'sequential' and i < len(student_list):
                student = student_list[i]
                binding['student_id'] = student['id']
                binding['student_name'] = student['name']
                binding['status'] = 'bound'
                
            elif binding_mode == 'auto':
                student_id = self.parser.detect_student_id(page.image)
                if student_id:
                    binding['student_id'] = student_id
                    binding['status'] = 'auto_detected'
            
            bindings.append(binding)
        
        return bindings
