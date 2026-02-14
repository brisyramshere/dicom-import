from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.db.database import Base
import json


class Series(Base):
    """DICOM序列主表"""
    __tablename__ = "series"

    id = Column(String(32), primary_key=True)  # 唯一ID (基于UID生成)

    # 患者信息
    patient_id = Column(String(64), index=True)
    patient_name = Column(String(128))
    patient_sex = Column(String(8))
    patient_birth_date = Column(String(16))

    # 检查信息
    study_instance_uid = Column(String(128), index=True)
    study_date = Column(String(16))

    # 序列信息
    series_instance_uid = Column(String(128), unique=True, index=True)
    series_number = Column(Integer)
    series_description = Column(String(256))
    modality = Column(String(16), index=True)
    protocol_name = Column(String(128))

    # 设备信息
    manufacturer = Column(String(64))
    manufacturer_model = Column(String(64))

    # 模态特定参数 (JSON存储)
    ct_params = Column(Text)  # JSON: slice_thickness, kvp, rotation_time
    mr_params = Column(Text)  # JSON: tr, te, ti, flip_angle
    dx_params = Column(Text)  # JSON: exposure, kvp

    # 文件信息
    file_path = Column(String(512))  # 主路径
    file_count = Column(Integer)     # 该序列文件数
    file_size_total = Column(Integer)  # 总大小(字节)
    file_modified_date = Column(String(32))

    # 元信息
    created_at = Column(String(32), default=func.now())
    is_active = Column(Boolean, default=True)

    # 扫描来源
    scan_id = Column(String(32))

    def get_ct_params(self):
        return json.loads(self.ct_params) if self.ct_params else {}

    def get_mr_params(self):
        return json.loads(self.mr_params) if self.mr_params else {}

    def get_dx_params(self):
        return json.loads(self.dx_params) if self.dx_params else {}


class SeriesPath(Base):
    """序列的多个路径记录"""
    __tablename__ = "series_paths"

    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(String(32), index=True)
    file_path = Column(String(512))
    added_at = Column(String(32), default=func.now())


class Scan(Base):
    """扫描记录"""
    __tablename__ = "scans"

    id = Column(String(32), primary_key=True)
    scan_path = Column(String(512))
    scan_type = Column(String(16))  # manual/auto
    started_at = Column(String(32))
    finished_at = Column(String(32))
    series_found = Column(Integer, default=0)
    series_new = Column(Integer, default=0)
    series_duplicated = Column(Integer, default=0)
    status = Column(String(16), default="running")  # running/completed/failed


class ScanConfig(Base):
    """扫描配置"""
    __tablename__ = "scan_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_path = Column(String(512), unique=True)
    description = Column(String(256))
    is_active = Column(Boolean, default=True)
    schedule_type = Column(String(16))  # manual/weekly
    last_scan_at = Column(String(32))
    created_at = Column(String(32), default=func.now())

    # 筛选规则 (JSON)
    filter_rules = Column(Text)  # JSON


class FilterRule(Base):
    """筛选规则配置"""
    __tablename__ = "filter_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    modality = Column(String(16))  # CT/MR/DX等
    min_slice_thickness = Column(Integer)  # 最大层厚
    min_image_count = Column(Integer)      # 最少图片数
    is_active = Column(Boolean, default=True)
    created_at = Column(String(32), default=func.now())
