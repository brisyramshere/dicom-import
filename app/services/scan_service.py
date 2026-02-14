"""
DICOM扫描服务
负责扫描目录、解析DICOM、存入数据库
"""
import os
import json
import uuid
import hashlib
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from app.db.models import Series, SeriesPath, Scan, ScanConfig, FilterRule
from app.services.scanner import DicomScanner


def generate_series_id(series_uid: str, patient_id: str = "") -> str:
    """基于SeriesInstanceUID生成唯一ID"""
    # 使用MD5哈希，取前12位，加前缀
    hash_input = f"{series_uid}".encode()
    hash_part = hashlib.md5(hash_input).hexdigest()[:12].upper()
    return f"SER{hash_part}"


def generate_scan_id() -> str:
    """生成扫描ID"""
    return f"SCN{uuid.uuid4().hex[:12].upper()}"


class ScanService:
    """扫描服务"""

    def __init__(self, db: Session):
        self.db = db
        self.scanner = DicomScanner()

    def get_filter_rules(self, modality: str) -> Optional[Dict[str, Any]]:
        """获取指定模态的筛选规则"""
        rule = self.db.query(FilterRule).filter(
            FilterRule.modality == modality,
            FilterRule.is_active == True
        ).first()

        if rule:
            return {
                "min_slice_thickness": rule.min_slice_thickness,
                "min_image_count": rule.min_image_count,
            }
        return None

    def check_filter(self, modality: str, info: Any) -> bool:
        """检查是否符合筛选规则"""
        rule = self.get_filter_rules(modality)
        if not rule:
            return True  # 没有规则则通过

        # 检查图片数量
        if rule.get("min_image_count"):
            # 需要在group_by_series后检查
            pass

        # CT检查层厚
        if modality == "CT" and rule.get("min_slice_thickness") is not None:
            if info.slice_thickness and info.slice_thickness > rule["min_slice_thickness"]:
                return False

        return True

    def scan_path(self, scan_path: str, scan_id: str) -> Dict[str, Any]:
        """扫描指定路径"""
        print(f"开始扫描路径: {scan_path}")

        # 1. 扫描目录下所有DICOM文件
        dicom_files = self.scanner.scan_directory(scan_path, recursive=True)
        print(f"发现 {len(dicom_files)} 个DICOM文件")

        # 2. 按Series分组
        series_map = self.scanner.group_by_series(dicom_files)
        print(f"发现 {len(series_map)} 个序列")

        # 3. 处理每个序列
        series_new = 0
        series_duplicated = 0

        for series_uid, file_list in series_map.items():
            # 读取第一个文件获取元信息
            sample_info = self.scanner.read_dicom(file_list[0])
            if not sample_info:
                continue

            # 检查是否存在
            existing = self.db.query(Series).filter(
                Series.series_instance_uid == series_uid
            ).first()

            if existing:
                # 已存在，记录新路径
                for fp in file_list:
                    path_record = SeriesPath(
                        series_id=existing.id,
                        file_path=fp,
                    )
                    self.db.add(path_record)
                series_duplicated += 1
            else:
                # 新建记录
                series_id = generate_series_id(series_uid, sample_info.patient_id)

                series = Series(
                    id=series_id,
                    patient_id=sample_info.patient_id,
                    patient_name=sample_info.patient_name,
                    patient_sex=sample_info.patient_sex,
                    patient_birth_date=sample_info.patient_birth_date,
                    study_instance_uid=sample_info.study_instance_uid,
                    study_date=sample_info.study_date,
                    series_instance_uid=sample_info.series_instance_uid,
                    series_number=sample_info.series_number,
                    series_description=sample_info.series_description,
                    modality=sample_info.modality,
                    protocol_name=sample_info.protocol_name,
                    manufacturer=sample_info.manufacturer,
                    manufacturer_model=sample_info.manufacturer_model,
                    ct_params=json.dumps(sample_info.ct_params) if sample_info.ct_params else None,
                    mr_params=json.dumps(sample_info.mr_params) if sample_info.mr_params else None,
                    dx_params=json.dumps(sample_info.dx_params) if sample_info.dx_params else None,
                    file_path=file_list[0],  # 主路径
                    file_count=len(file_list),
                    file_size_total=sum(os.path.getsize(f) for f in file_list if os.path.exists(f)),
                    file_modified_date=sample_info.file_modified,
                    scan_id=scan_id,
                )
                self.db.add(series)
                series_new += 1

        self.db.commit()

        return {
            "total_files": len(dicom_files),
            "total_series": len(series_map),
            "new_series": series_new,
            "duplicated_series": series_duplicated,
        }

    def run_scan(self, scan_config_id: int) -> Scan:
        """执行扫描"""
        config = self.db.query(ScanConfig).filter(ScanConfig.id == scan_config_id).first()
        if not config:
            raise ValueError(f"扫描配置不存在: {scan_config_id}")

        scan_id = generate_scan_id()
        scan = Scan(
            id=scan_id,
            scan_path=config.scan_path,
            scan_type=config.schedule_type,
            started_at=datetime.now().isoformat(),
            status="running",
        )
        self.db.add(scan)
        self.db.commit()

        try:
            result = self.scan_path(config.scan_path, scan_id)

            scan.series_found = result["total_series"]
            scan.series_new = result["new_series"]
            scan.series_duplicated = result["duplicated_series"]
            scan.finished_at = datetime.now().isoformat()
            scan.status = "completed"

            # 更新配置的最后扫描时间
            config.last_scan_at = datetime.now().isoformat()

        except Exception as e:
            scan.status = "failed"
            scan.finished_at = datetime.now().isoformat()
            print(f"扫描失败: {e}")

        self.db.commit()
        return scan


class ExportService:
    """导出服务"""

    def __init__(self, db: Session):
        self.db = db

    def export_series(self, series_ids: List[str], target_dir: str) -> Dict[str, Any]:
        """导出序列到指定目录"""
        os.makedirs(target_dir, exist_ok=True)

        exported_count = 0
        failed_ids = []

        for series_id in series_ids:
            series = self.db.query(Series).filter(Series.id == series_id).first()
            if not series:
                failed_ids.append(series_id)
                continue

            # 获取所有路径
            paths = self.db.query(SeriesPath).filter(
                SeriesPath.series_id == series_id
            ).all()

            all_paths = [series.file_path] + [p.file_path for p in paths]

            # 创建目标文件夹
            target_folder = os.path.join(target_dir, series_id)
            os.makedirs(target_folder, exist_ok=True)

            # 拷贝文件（保持原文件名）
            success_files = 0
            for src_path in all_paths:
                if os.path.exists(src_path):
                    filename = os.path.basename(src_path)
                    dst_path = os.path.join(target_folder, filename)
                    try:
                        shutil.copy2(src_path, dst_path)
                        success_files += 1
                    except Exception as e:
                        print(f"拷贝失败 {src_path}: {e}")

            # 导出元信息
            meta = {
                "id": series.id,
                "patient_id": series.patient_id,
                "patient_name": series.patient_name,
                "patient_sex": series.patient_sex,
                "study_date": series.study_date,
                "modality": series.modality,
                "protocol_name": series.protocol_name,
                "series_description": series.series_description,
                "manufacturer": series.manufacturer,
                "manufacturer_model": series.manufacturer_model,
                "ct_params": json.loads(series.ct_params) if series.ct_params else None,
                "mr_params": json.loads(series.mr_params) if series.mr_params else None,
                "dx_params": json.loads(series.dx_params) if series.dx_params else None,
                "file_count": series.file_count,
                "original_paths": all_paths,
            }

            meta_path = os.path.join(target_folder, "meta.json")
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            if success_files > 0:
                exported_count += 1

        return {
            "success": len(failed_ids) == 0,
            "exported_count": exported_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
            "target_dir": target_dir,
        }
