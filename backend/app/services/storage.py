import io
import os
import uuid
from datetime import datetime
from typing import Optional
import numpy as np

from app.core.config import settings

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False


class MinIOStorage:
    """MinIO 对象存储服务（支持本地文件存储备选）"""
    
    def __init__(self):
        self.use_local = not MINIO_AVAILABLE
        
        if self.use_local:
            self.local_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
            os.makedirs(self.local_dir, exist_ok=True)
        else:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_SSL
            )
            self.bucket = settings.MINIO_BUCKET
            self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            print(f"MinIO 存储桶初始化失败，将使用本地存储: {e}")
            self.use_local = True
            self.local_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
            os.makedirs(self.local_dir, exist_ok=True)
    
    async def save_image(
        self,
        image_data: bytes,
        exam_id: int,
        subject_id: int,
        filename: Optional[str] = None
    ) -> str:
        """
        保存图片
        
        Args:
            image_data: 图片二进制数据
            exam_id: 考试 ID
            subject_id: 科目 ID
            filename: 文件名，默认自动生成
        
        Returns:
            文件访问 URL
        """
        if filename is None:
            filename = f"{uuid.uuid4().hex}.jpg"
        
        date_path = datetime.now().strftime("%Y/%m/%d")
        
        if self.use_local:
            # 本地存储
            file_path = os.path.join(self.local_dir, str(exam_id), str(subject_id), date_path)
            os.makedirs(file_path, exist_ok=True)
            full_path = os.path.join(file_path, filename)
            with open(full_path, "wb") as f:
                f.write(image_data)
            return f"/uploads/{exam_id}/{subject_id}/{date_path}/{filename}"
        else:
            # MinIO 存储
            object_name = f"exams/{exam_id}/subjects/{subject_id}/{date_path}/{filename}"
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=io.BytesIO(image_data),
                length=len(image_data),
                content_type="image/jpeg"
            )
            return f"/{self.bucket}/{object_name}"
    
    async def save_image_from_array(
        self,
        image: np.ndarray,
        exam_id: int,
        subject_id: int,
        filename: Optional[str] = None
    ) -> str:
        """
        从 numpy 数组保存图片
        """
        import cv2
        _, buffer = cv2.imencode('.jpg', image)
        image_data = buffer.tobytes()
        return await self.save_image(image_data, exam_id, subject_id, filename)
    
    def get_image(self, object_name: str) -> bytes:
        """获取图片"""
        if self.use_local:
            file_path = os.path.join(self.local_dir, object_name.lstrip("/uploads/"))
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read()
            return b""
        else:
            response = self.client.get_object(self.bucket, object_name)
            return response.read()
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """获取预签名 URL"""
        if self.use_local:
            return object_name
        else:
            return self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=object_name,
                expires=expires
            )
    
    def delete_image(self, object_name: str):
        """删除图片"""
        if self.use_local:
            file_path = os.path.join(self.local_dir, object_name.lstrip("/uploads/"))
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            self.client.remove_object(self.bucket, object_name)
