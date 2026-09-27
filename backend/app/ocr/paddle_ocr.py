import numpy as np
from typing import List, Dict, Tuple, Optional
import cv2
import logging

logger = logging.getLogger(__name__)

# 尝试导入 PaddleOCR，如果不可用则使用模拟实现
try:
    from paddleocr import PaddleOCR
    PADDLE_OCR_AVAILABLE = True
except ImportError:
    PADDLE_OCR_AVAILABLE = False
    logger.warning("PaddleOCR 未安装，将使用模拟 OCR 实现。生产环境请安装 paddleocr 和 paddlepaddle。")


class PaddleOCRService:
    """PaddleOCR 封装服务"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式，避免重复初始化模型"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, use_angle_cls: bool = True, lang: str = 'ch', use_gpu: bool = False):
        if self._initialized:
            return
        
        if PADDLE_OCR_AVAILABLE:
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang,
                use_gpu=use_gpu,
                show_log=False,
                enable_mkldnn=True
            )
        else:
            self.ocr = None
        
        self._initialized = True
    
    def recognize_text(self, image: np.ndarray) -> List[Dict]:
        """
        识别图片中的文字
        
        Args:
            image: 输入图片 (numpy array)
        
        Returns:
            识别结果列表，每项包含文字、坐标、置信度
        """
        if not PADDLE_OCR_AVAILABLE or self.ocr is None:
            # 模拟 OCR 结果
            return self._mock_recognize(image)
        
        result = self.ocr.ocr(image, cls=True)
        
        texts = []
        if result and result[0]:
            for line in result[0]:
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]
                
                texts.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': confidence
                })
        
        return texts
    
    def _mock_recognize(self, image: np.ndarray) -> List[Dict]:
        """模拟 OCR 识别结果（用于开发和测试环境）"""
        h, w = image.shape[:2]
        return [
            {
                'bbox': [[10, 10], [w//2, 10], [w//2, h//4], [10, h//4]],
                'text': '模拟识别文字',
                'confidence': 0.85
            }
        ]
    
    def recognize_text_regions(self, image: np.ndarray, 
                               regions: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """
        识别指定区域的文字
        
        Args:
            image: 完整图片
            regions: 区域列表 [(x, y, w, h), ...]
        
        Returns:
            各区域的识别结果
        """
        results = []
        
        for i, (x, y, w, h) in enumerate(regions):
            region_image = image[y:y+h, x:x+w]
            texts = self.recognize_text(region_image)
            
            results.append({
                'region_id': i,
                'region': (x, y, w, h),
                'texts': texts
            })
        
        return results
    
    def detect_student_id(self, image: np.ndarray, 
                          region: Optional[Tuple[int, int, int, int]] = None) -> Optional[str]:
        """
        检测学号
        
        Args:
            image: 答题卡图片
            region: 学号填写区域坐标 (x, y, w, h)
        
        Returns:
            识别到的学号字符串
        """
        if region:
            x, y, w, h = region
            image = image[y:y+h, x:x+w]
        
        texts = self.recognize_text(image)
        
        # 过滤出数字（学号通常是纯数字）
        for item in texts:
            text = item['text'].strip()
            if text.isdigit() and len(text) >= 6:
                return text
        
        # 如果没有纯数字，返回第一个识别结果
        if texts:
            return texts[0]['text'].strip()
        
        return None
    
    def detect_name(self, image: np.ndarray,
                    region: Optional[Tuple[int, int, int, int]] = None) -> Optional[str]:
        """
        检测姓名
        
        Args:
            image: 答题卡图片
            region: 姓名填写区域
        
        Returns:
            识别到的姓名
        """
        if region:
            x, y, w, h = region
            image = image[y:y+h, x:x+w]
        
        texts = self.recognize_text(image)
        
        # 过滤出中文姓名（2-4个中文字符）
        for item in texts:
            text = item['text'].strip()
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            if 2 <= chinese_chars <= 4:
                return text
        
        if texts:
            return texts[0]['text'].strip()
        
        return None
    
    def detect_handwritten_answer(self, image: np.ndarray) -> Dict:
        """
        检测手写答案区域
        
        Args:
            image: 主观题答题区域图片
        
        Returns:
            识别结果，包含文字和置信度
        """
        texts = self.recognize_text(image)
        
        full_text = ' '.join([t['text'] for t in texts])
        avg_confidence = sum([t['confidence'] for t in texts]) / len(texts) if texts else 0
        
        return {
            'text': full_text,
            'confidence': avg_confidence,
            'details': texts
        }
    
    def batch_recognize(self, images: List[np.ndarray]) -> List[List[Dict]]:
        """
        批量识别多张图片
        
        Args:
            images: 图片列表
        
        Returns:
            每张图片的识别结果
        """
        results = []
        for image in images:
            texts = self.recognize_text(image)
            results.append(texts)
        return results
    
    def get_text_image(self, image: np.ndarray, text_result: Dict) -> np.ndarray:
        """
        从原图中裁剪出文字区域
        
        Args:
            image: 原图
            text_result: recognize_text 返回的单条结果
        
        Returns:
            文字区域的图片
        """
        bbox = text_result['bbox']
        pts = np.array(bbox, dtype=np.int32)
        
        # 获取边界框
        x, y, w, h = cv2.boundingRect(pts)
        
        return image[y:y+h, x:x+w]


class AnswerCardOCR:
    """答题卡 OCR 识别器 - 整合图像处理和文字识别"""
    
    def __init__(self, ocr_service: Optional[PaddleOCRService] = None):
        self.ocr = ocr_service or PaddleOCRService()
    
    def process_answer_card(self, image: np.ndarray) -> Dict:
        """
        处理整张答题卡
        
        Args:
            image: 校正后的答题卡图片
        
        Returns:
            完整的识别结果
        """
        # 识别所有文字
        all_texts = self.ocr.recognize_text(image)
        
        # 识别学号区域（假设在左上角）
        h, w = image.shape[:2]
        student_id = self.ocr.detect_student_id(image, region=(0, 0, w//3, h//6))
        
        # 识别姓名区域
        name = self.ocr.detect_name(image, region=(w//3, 0, w//3, h//6))
        
        return {
            'student_id': student_id,
            'name': name,
            'all_texts': all_texts,
            'text_count': len(all_texts)
        }
    
    def process_subjective_question(self, image: np.ndarray, 
                                    question_regions: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """
        处理主观题区域
        
        Args:
            image: 答题卡图片
            question_regions: 各主观题区域坐标
        
        Returns:
            每道题的识别结果
        """
        results = []
        
        for i, (x, y, w, h) in enumerate(question_regions, 1):
            region_image = image[y:y+h, x:x+w]
            result = self.ocr.detect_handwritten_answer(region_image)
            
            results.append({
                'question_number': i,
                'answer_text': result['text'],
                'confidence': result['confidence'],
                'region': (x, y, w, h)
            })
        
        return results
