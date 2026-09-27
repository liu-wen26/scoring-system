import os
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.answer_card import AnswerCardConfig
from app.models.scan import ScanPage
from app.models.mark import MarkResult
from app.services.storage import MinIOStorage
from app.ocr.answer_detector import ChoiceAnswerDetector, ChoiceConfig
from datetime import datetime


class AnswerCardOCRProcessor:
    """答题卡 OCR 处理器：识别客观题、切割主观题"""

    def __init__(self, db: Session):
        self.db = db
        self.storage = MinIOStorage()

    def load_image(self, file_url: str) -> Optional[np.ndarray]:
        """从文件 URL 加载图片"""
        try:
            if file_url.startswith("http://") or file_url.startswith("https://"):
                import requests
                response = requests.get(file_url, timeout=30)
                image_data = response.content
            else:
                # 本地路径 /uploads/...
                object_name = file_url
                if object_name.startswith("/uploads/"):
                    object_name = object_name[len("/uploads/"):]
                local_path = os.path.join(self.storage.local_dir, object_name)
                if not os.path.exists(local_path):
                    return None
                with open(local_path, "rb") as f:
                    image_data = f.read()

            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            print(f"加载图片失败: {file_url}, 错误: {e}")
            return None

    def get_config(self, exam_id: int, subject_id: int) -> Optional[AnswerCardConfig]:
        """获取答题卡配置"""
        return self.db.query(AnswerCardConfig).filter(
            AnswerCardConfig.exam_id == exam_id,
            AnswerCardConfig.subject_id == subject_id
        ).first()

    def _parse_template_size(self, config: AnswerCardConfig) -> Tuple[int, int]:
        """从配置中解析模板尺寸，优先使用已存储字段，缺失时从图片解析"""
        if config.template_width and config.template_height:
            return config.template_width, config.template_height

        previews = config.page_previews or []
        image_url = previews[0] if previews else config.template_image
        if not image_url:
            return 0, 0

        try:
            if image_url.startswith("data:"):
                import base64
                import io
                from PIL import Image
                image_url = image_url.split(",", 1)[1]
                img_bytes = base64.b64decode(image_url)
                img = Image.open(io.BytesIO(img_bytes))
                width, height = img.width, img.height
            else:
                # 本地路径 /uploads/...
                object_name = image_url
                if object_name.startswith("/uploads/"):
                    object_name = object_name[len("/uploads/"):]
                local_path = os.path.join(self.storage.local_dir, object_name)
                if not os.path.exists(local_path):
                    return 0, 0
                from PIL import Image
                img = Image.open(local_path)
                width, height = img.width, img.height

            # 同步写回数据库，避免下次重复解析
            config.template_width = width
            config.template_height = height
            self.db.commit()
            return width, height
        except Exception as e:
            print(f"解析模板尺寸失败: {e}")
            return 0, 0

    def scale_regions_to_image(
        self,
        regions: List[Dict],
        image: np.ndarray,
        template_width: int,
        template_height: int
    ) -> List[Dict]:
        """将基于模板预览图的 region 坐标缩放到扫描图片尺寸"""
        if template_width <= 0 or template_height <= 0:
            print(f"[scale_regions] 模板尺寸无效 ({template_width}x{template_height})，跳过缩放")
            return regions

        img_h, img_w = image.shape[:2]
        scale_x = img_w / template_width
        scale_y = img_h / template_height

        # 相对差异超过 10% 时告警，但仍使用平均缩放，避免完全不缩放导致位置偏移
        relative_diff = abs(scale_x - scale_y) / max(scale_x, scale_y, 1e-6)
        if relative_diff > 0.1:
            print(f"[scale_regions] 宽高比差异较大: scale_x={scale_x:.4f}, scale_y={scale_y:.4f}, diff={relative_diff:.2%}，继续平均缩放")
        else:
            print(f"[scale_regions] 模板{template_width}x{template_height}, 扫描图{img_w}x{img_h}, scale_x={scale_x:.4f}, scale_y={scale_y:.4f}")

        scale = (scale_x + scale_y) / 2
        scaled = []
        for r in regions:
            scaled.append({
                **r,
                "x": int(round(r.get("x", 0) * scale)),
                "y": int(round(r.get("y", 0) * scale)),
                "w": int(round(r.get("w", 0) * scale)),
                "h": int(round(r.get("h", 0) * scale)),
            })
        return scaled

    def detect_choice_answers(
        self,
        image: np.ndarray,
        regions: List[Dict],
        standard_answers: Dict,
        question_groups: List[Dict]
    ) -> Tuple[float, List[Dict]]:
        """
        识别客观题答案
        返回: (客观题得分, 识别结果列表)
        """
        total_score = 0.0
        results = []

        # 按题号组织区域
        region_map = {}
        for r in regions:
            if r.get("type") == "objective":
                qno = r.get("questionNo") or r.get("question_no") or ""
                region_map[str(qno)] = r

        # 按题目组确定选项数量
        group_options = {}
        for group in question_groups:
            if group.get("type") == "choice":
                options = group.get("options", ["A", "B", "C", "D"])
                start = group.get("startNo") or group.get("start_no") or 1
                end = group.get("endNo") or group.get("end_no")
                if not end:
                    count = group.get("count") or 0
                    end = start + count - 1 if count > 0 else start
                for no in range(int(start), int(end) + 1):
                    group_options[str(no)] = options

        for no_str, region in region_map.items():
            if not no_str or not no_str.isdigit():
                continue
            x, y, w, h = region.get("x", 0), region.get("y", 0), region.get("w", 0), region.get("h", 0)
            if w <= 0 or h <= 0:
                continue

            # 坐标是相对于模板图片原图的，需要确保图片尺寸足够
            img_h, img_w = image.shape[:2]
            x = max(0, min(x, img_w - 1))
            y = max(0, min(y, img_h - 1))
            w = min(w, img_w - x)
            h = min(h, img_h - y)

            question_image = image[y:y + h, x:x + w]
            if question_image.size == 0:
                continue

            options = group_options.get(no_str, ["A", "B", "C", "D"])
            multi_select = len(standard_answers.get(no_str, "")) > 1

            config = ChoiceConfig(
                option_count=len(options),
                fill_threshold=0.15,
                multi_select=multi_select
            )
            detector = ChoiceAnswerDetector(config)
            result = detector.detect_single(question_image, int(no_str))

            selected = "".join(result.selected_options)
            std_answer = standard_answers.get(no_str, "")
            score = float(region.get("score") or 0)
            if score == 0:
                for g in question_groups:
                    if g.get("type") == "choice":
                        g_start = g.get("startNo") or g.get("start_no") or 1
                        g_count = g.get("count") or 0
                        g_end = g.get("endNo") or g.get("end_no") or (g_start + g_count - 1)
                        if g_start <= int(no_str) <= g_end:
                            score = float(g.get("scorePerQuestion") or g.get("score_per_question") or 0)
                            break

            # 判断对错
            is_correct = False
            if std_answer and selected:
                if multi_select:
                    is_correct = set(selected.upper()) == set(std_answer.upper())
                else:
                    is_correct = selected.upper() == std_answer.upper()

            got_score = score if is_correct else 0
            total_score += got_score

            results.append({
                "question_no": int(no_str),
                "selected": selected,
                "standard_answer": std_answer,
                "is_correct": is_correct,
                "score": got_score,
                "full_score": score,
                "confidence": round(result.confidence, 4),
                "fill_ratios": {k: round(v, 4) for k, v in result.fill_ratios.items()}
            })

        return round(total_score, 2), results

    def cut_subjective_regions(
        self,
        image: np.ndarray,
        regions: List[Dict],
        exam_id: int,
        subject_id: int,
        scan_page_id: int
    ) -> List[Dict]:
        """
        切割主观题区域并保存图片
        返回: 主观题切割结果列表
        """
        results = []

        for r in regions:
            if r.get("type") != "subjective":
                continue

            x, y, w, h = r.get("x", 0), r.get("y", 0), r.get("w", 0), r.get("h", 0)
            img_h, img_w = image.shape[:2]
            x = max(0, min(x, img_w - 1))
            y = max(0, min(y, img_h - 1))
            w = min(w, img_w - x)
            h = min(h, img_h - y)

            if w <= 0 or h <= 0:
                continue

            region_image = image[y:y + h, x:x + w]
            if region_image.size == 0:
                continue

            no = str(r.get("questionNo") or r.get("question_no") or "")
            filename = f"sub_q{no}_page{scan_page_id}.jpg"

            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            file_url = loop.run_until_complete(
                self.storage.save_image_from_array(region_image, exam_id, subject_id, filename)
            )

            results.append({
                "question_no": int(no) if no.isdigit() else no,
                "file_url": file_url,
                "x": x, "y": y, "w": w, "h": h,
                "full_score": float(r.get("score") or 0)
            })

        return results

    def process_scan_page(self, scan_page: ScanPage) -> Dict:
        """
        处理单页扫描图片
        """
        exam_id = scan_page.exam_id
        subject_id = scan_page.subject_id

        config = self.get_config(exam_id, subject_id)

        # 即使没有答题卡配置，也要创建 MarkResult，保证阅卷流程可用
        if not config:
            print(f"[process_scan_page] 未找到答题卡配置 exam_id={exam_id}, subject_id={subject_id}，创建基础 MarkResult")
            scan_page.status = "processed"
            scan_page.processed_at = datetime.now()
            ocr_result = {"choice": [], "subjective_cuts": [], "choice_score": 0, "subjective_score": 0}
            scan_page.ocr_result = ocr_result

            mark_result = self.db.query(MarkResult).filter(
                MarkResult.scan_page_id == scan_page.id
            ).first()
            if not mark_result:
                mark_result = MarkResult(
                    exam_id=exam_id,
                    subject_id=subject_id,
                    student_id=scan_page.student_id,
                    scan_page_id=scan_page.id,
                    choice_score=0,
                    subjective_score=0,
                    total_score=0,
                    choice_result={"results": []},
                    subjective_result={"cuts": []},
                    status="pending"
                )
                self.db.add(mark_result)
            self.db.commit()
            return {"status": "success", "scan_page_id": scan_page.id, "choice_score": 0, "choice_count": 0, "subjective_count": 0, "message": "无答题卡配置，已创建基础阅卷记录"}

        questions_config = config.questions_config or {}
        question_groups = questions_config.get("questionGroups") or questions_config.get("question_groups") or []
        standard_answers = config.standard_answers or {}
        regions = config.regions or []

        image = self.load_image(scan_page.file_url)

        try:
            if image is None:
                print(f"[process_scan_page] 无法加载图片: {scan_page.file_url}，创建基础 MarkResult")
                scan_page.status = "processed"
                scan_page.processed_at = datetime.now()
                ocr_result = {"choice": [], "subjective_cuts": [], "choice_score": 0, "subjective_score": 0}
                scan_page.ocr_result = ocr_result

                mark_result = self.db.query(MarkResult).filter(
                    MarkResult.scan_page_id == scan_page.id
                ).first()
                if not mark_result:
                    mark_result = MarkResult(
                        exam_id=exam_id,
                        subject_id=subject_id,
                        student_id=scan_page.student_id,
                        scan_page_id=scan_page.id,
                        choice_score=0,
                        subjective_score=0,
                        total_score=0,
                        choice_result={"results": []},
                        subjective_result={"cuts": []},
                        status="pending"
                    )
                    self.db.add(mark_result)
                self.db.commit()
                return {"status": "success", "scan_page_id": scan_page.id, "choice_score": 0, "choice_count": 0, "subjective_count": 0, "message": "图片加载失败，已创建基础阅卷记录"}

            # region 坐标基于模板预览图，需要缩放到扫描图尺寸
            template_width, template_height = self._parse_template_size(config)
            print(f"[process_scan_page] scan_page_id={scan_page.id}, 模板尺寸={template_width}x{template_height}, 扫描图尺寸={image.shape[1]}x{image.shape[0]}, 区域数={len(regions)}")

            scaled_regions = self.scale_regions_to_image(
                regions, image, template_width, template_height
            )

            # 1. 识别客观题
            choice_score, choice_results = self.detect_choice_answers(
                image, scaled_regions, standard_answers, question_groups
            )

            # 2. 切割主观题
            subjective_cuts = self.cut_subjective_regions(
                image, scaled_regions, exam_id, subject_id, scan_page.id
            )

            # 3. 保存结果
            ocr_result = {
                "choice": choice_results,
                "subjective_cuts": subjective_cuts,
                "choice_score": choice_score,
                "subjective_score": 0
            }

            scan_page.ocr_result = ocr_result
            scan_page.status = "processed"
            scan_page.processed_at = datetime.now()

            # 4. 更新或创建阅卷结果
            mark_result = self.db.query(MarkResult).filter(
                MarkResult.scan_page_id == scan_page.id
            ).first()
            if not mark_result:
                mark_result = MarkResult(
                    exam_id=exam_id,
                    subject_id=subject_id,
                    student_id=scan_page.student_id,
                    scan_page_id=scan_page.id,
                    choice_score=choice_score,
                    subjective_score=0,
                    total_score=choice_score,
                    choice_result={"results": choice_results},
                    subjective_result={"cuts": subjective_cuts},
                    status="pending"
                )
                self.db.add(mark_result)
            else:
                mark_result.choice_score = choice_score
                mark_result.total_score = choice_score + float(mark_result.subjective_score or 0)
                mark_result.choice_result = {"results": choice_results}
                mark_result.subjective_result = {"cuts": subjective_cuts}

            self.db.commit()

            return {
                "status": "success",
                "scan_page_id": scan_page.id,
                "choice_score": choice_score,
                "choice_count": len(choice_results),
                "subjective_count": len(subjective_cuts)
            }

        except Exception as e:
            import traceback
            scan_page.status = "failed"
            scan_page.error_message = str(e)
            # 即使失败也创建 MarkResult，保证阅卷流程可用
            mark_result = self.db.query(MarkResult).filter(
                MarkResult.scan_page_id == scan_page.id
            ).first()
            if not mark_result:
                mark_result = MarkResult(
                    exam_id=exam_id,
                    subject_id=subject_id,
                    student_id=scan_page.student_id,
                    scan_page_id=scan_page.id,
                    choice_score=0,
                    subjective_score=0,
                    total_score=0,
                    choice_result={"results": []},
                    subjective_result={"cuts": []},
                    status="pending"
                )
                self.db.add(mark_result)
            self.db.commit()
            print(f"OCR 处理失败: {e}")
            traceback.print_exc()
            return {"status": "failed", "message": str(e)}