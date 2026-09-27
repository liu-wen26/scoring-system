import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MarkerPoint:
    """定位点"""
    x: int
    y: int
    
    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


class PerspectiveTransformer:
    """透视变换器 - 用于校正倾斜的答题卡"""
    
    def __init__(self, min_area_ratio: float = 0.1):
        """
        Args:
            min_area_ratio: 最小轮廓面积占图片面积的比例
        """
        self.min_area_ratio = min_area_ratio
    
    def detect_answer_card(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        检测答题卡区域并返回四角坐标
        
        Args:
            image: 预处理后的图片
        
        Returns:
            四角坐标数组 (4, 2) 或 None
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny 边缘检测
        edged = cv2.Canny(blurred, 50, 150)
        
        # 膨胀操作，连接断开的边缘
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        edged = cv2.dilate(edged, kernel, iterations=2)
        edged = cv2.erode(edged, kernel, iterations=1)
        
        # 查找轮廓
        contours, _ = cv2.findContours(
            edged.copy(), 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contours:
            return None
        
        # 按面积排序
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # 图片总面积
        image_area = image.shape[0] * image.shape[1]
        min_area = image_area * self.min_area_ratio
        
        # 查找最大的四边形轮廓
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            
            # 计算轮廓周长
            peri = cv2.arcLength(contour, True)
            
            # 多边形近似
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            # 如果是四边形，认为是答题卡
            if len(approx) == 4:
                return approx.reshape(4, 2)
        
        # 如果没找到四边形，尝试使用最小外接矩形
        if contours:
            largest = contours[0]
            rect = cv2.minAreaRect(largest)
            box = cv2.boxPoints(rect)
            return np.int0(box)
        
        return None
    
    def detect_by_markers(self, image: np.ndarray, 
                          marker_size: int = 20) -> Optional[np.ndarray]:
        """
        通过定位标记点检测答题卡
        
        答题卡四角通常有黑色方块标记点
        
        Args:
            image: 输入图片
            marker_size: 定位标记点大小（像素）
        
        Returns:
            四角坐标或 None
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 筛选定位标记点（小方块）
        markers = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            area = w * h
            
            # 定位标记点特征：接近正方形，面积适中
            if 0.8 < aspect_ratio < 1.2 and 100 < area < 2000:
                # 检查是否为实心方块
                mask = np.zeros(gray.shape, dtype=np.uint8)
                cv2.drawContours(mask, [contour], -1, 255, -1)
                filled_ratio = cv2.countNonZero(mask) / area
                
                if filled_ratio > 0.8:
                    markers.append((x + w//2, y + h//2))
        
        if len(markers) >= 4:
            # 按位置排序，取四个角点
            return self._select_corner_markers(markers, image.shape)
        
        return None
    
    def _select_corner_markers(self, markers: List[Tuple[int, int]], 
                               image_shape: Tuple[int, ...]) -> np.ndarray:
        """
        从标记点中选择四个角点
        
        策略：选择距离图片四个角最近的标记点
        """
        h, w = image_shape[:2]
        corners = [
            (0, 0),        # 左上
            (w, 0),        # 右上
            (w, h),        # 右下
            (0, h)         # 左下
        ]
        
        selected = []
        used = set()
        
        for corner in corners:
            min_dist = float('inf')
            best_marker = None
            
            for i, marker in enumerate(markers):
                if i in used:
                    continue
                dist = np.sqrt((marker[0] - corner[0])**2 + (marker[1] - corner[1])**2)
                if dist < min_dist:
                    min_dist = dist
                    best_marker = i
            
            if best_marker is not None:
                selected.append(markers[best_marker])
                used.add(best_marker)
        
        return np.array(selected, dtype=np.float32)
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        排序四个点：左上、右上、右下、左下
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # 按坐标和排序
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # 左上（和最小）
        rect[2] = pts[np.argmax(s)]  # 右下（和最大）
        
        # 按坐标差排序
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # 右上（差最小）
        rect[3] = pts[np.argmax(diff)]  # 左下（差最大）
        
        return rect
    
    def transform(self, image: np.ndarray, points: np.ndarray) -> np.ndarray:
        """
        透视变换 - 将倾斜的答题卡校正为标准矩形
        
        Args:
            image: 原始图片
            points: 四角坐标 (4, 2)
        
        Returns:
            校正后的图片
        """
        # 排序角点
        rect = self._order_points(points)
        (tl, tr, br, bl) = rect
        
        # 计算输出图片的宽度和高度
        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_width = max(int(width_a), int(width_b))
        
        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_height = max(int(height_a), int(height_b))
        
        # 目标坐标
        dst = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]], dtype="float32")
        
        # 计算透视变换矩阵
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # 执行透视变换
        warped = cv2.warpPerspective(image, M, (max_width, max_height))
        
        return warped
    
    def auto_correct(self, image: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        自动检测并校正答题卡
        
        Args:
            image: 输入图片
        
        Returns:
            (校正后的图片, 是否成功)
        """
        # 先尝试通过轮廓检测
        points = self.detect_answer_card(image)
        
        if points is None:
            # 再尝试通过定位标记点检测
            points = self.detect_by_markers(image)
        
        if points is not None:
            corrected = self.transform(image, points)
            return corrected, True
        
        return image, False
    
    def get_correction_preview(self, image: np.ndarray, 
                               points: np.ndarray) -> np.ndarray:
        """
        获取校正预览（在原图上绘制检测到的角点）
        """
        preview = image.copy()
        
        # 绘制角点
        for i, point in enumerate(points):
            x, y = int(point[0]), int(point[1])
            color = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0)][i]
            cv2.circle(preview, (x, y), 10, color, -1)
            cv2.putText(preview, str(i), (x + 15, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # 绘制连接线
        pts = points.astype(np.int32)
        cv2.polylines(preview, [pts], True, (0, 255, 255), 2)
        
        return preview
