import cv2
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class PreprocessConfig:
    """预处理配置参数"""
    gaussian_kernel: Tuple[int, int] = (5, 5)
    gaussian_sigma: float = 0.0
    clahe_clip_limit: float = 3.0
    clahe_grid_size: Tuple[int, int] = (8, 8)
    adaptive_block_size: int = 11
    adaptive_c: int = 2
    median_kernel: int = 5


class ImagePreprocessor:
    """图像预处理器"""
    
    def __init__(self, config: Optional[PreprocessConfig] = None):
        self.config = config or PreprocessConfig()
    
    def preprocess(self, image: np.ndarray, steps: list = None) -> np.ndarray:
        """
        完整预处理流程
        
        Args:
            image: 输入图片 (BGR格式)
            steps: 指定处理步骤，默认全部执行
        
        Returns:
            预处理后的图片
        """
        if steps is None:
            steps = ['denoise', 'enhance', 'grayscale', 'binarize']
        
        result = image.copy()
        
        for step in steps:
            if step == 'denoise':
                result = self.denoise(result)
            elif step == 'enhance':
                result = self.enhance_contrast(result)
            elif step == 'grayscale':
                result = self.to_grayscale(result)
            elif step == 'binarize':
                result = self.binarize(result)
        
        return result
    
    def denoise(self, image: np.ndarray, method: str = 'gaussian') -> np.ndarray:
        """
        图像去噪
        
        Args:
            image: 输入图片
            method: 去噪方法 ('gaussian', 'median', 'bilateral')
        
        Returns:
            去噪后的图片
        """
        if method == 'gaussian':
            return cv2.GaussianBlur(
                image, 
                self.config.gaussian_kernel, 
                self.config.gaussian_sigma
            )
        elif method == 'median':
            return cv2.medianBlur(image, self.config.median_kernel)
        elif method == 'bilateral':
            return cv2.bilateralFilter(image, 9, 75, 75)
        else:
            raise ValueError(f"不支持的去噪方法: {method}")
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        对比度增强 (CLAHE)
        
        适用于光照不均匀的扫描图片
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(
            clipLimit=self.config.clahe_clip_limit,
            tileGridSize=self.config.clahe_grid_size
        )
        l = clahe.apply(l)
        
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """转换为灰度图"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def binarize(self, image: np.ndarray, method: str = 'adaptive') -> np.ndarray:
        """
        二值化
        
        Args:
            image: 灰度图
            method: 二值化方法 ('adaptive', 'otsu', 'simple')
        
        Returns:
            二值化图片
        """
        if method == 'adaptive':
            return cv2.adaptiveThreshold(
                image, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.config.adaptive_block_size,
                self.config.adaptive_c
            )
        elif method == 'otsu':
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        elif method == 'simple':
            _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            return binary
        else:
            raise ValueError(f"不支持的二值化方法: {method}")
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        图片倾斜校正
        """
        gray = self.to_grayscale(image)
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))
        
        M[0, 2] += (nW / 2) - center[0]
        M[1, 2] += (nH / 2) - center[1]
        
        return cv2.warpAffine(image, M, (nW, nH), borderValue=(255, 255, 255))
