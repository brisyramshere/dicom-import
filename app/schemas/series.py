from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class SeriesBase(BaseModel):
    """序列基础信息"""
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_sex: Optional[str] = None
    patient_birth_date: Optional[str] = None

    study_instance_uid: Optional[str] = None
    study_date: Optional[str] = None

    series_instance_uid: Optional[str] = None
    series_number: Optional[int] = None
    series_description: Optional[str] = None
    modality: Optional[str] = None
    protocol_name: Optional[str] = None

    manufacturer: Optional[str] = None
    manufacturer_model: Optional[str] = None


class SeriesCreate(SeriesBase):
    """创建序列的请求"""
    ct_params: Optional[Dict[str, Any]] = None
    mr_params: Optional[Dict[str, Any]] = None
    dx_params: Optional[Dict[str, Any]] = None
    file_path: str
    file_count: int
    file_size_total: int
    file_modified_date: Optional[str] = None
    scan_id: str


class SeriesResponse(SeriesBase):
    """序列响应"""
    id: str
    ct_params: Optional[Dict[str, Any]] = None
    mr_params: Optional[Dict[str, Any]] = None
    dx_params: Optional[Dict[str, Any]] = None

    file_path: str
    file_count: int
    file_size_total: int
    file_modified_date: Optional[str] = None

    created_at: str
    is_active: bool
    scan_id: Optional[str] = None

    class Config:
        from_attributes = True


class SeriesPathResponse(BaseModel):
    """序列路径响应"""
    id: int
    series_id: str
    file_path: str
    added_at: str

    class Config:
        from_attributes = True


class ScanCreate(BaseModel):
    """创建扫描请求"""
    scan_path: str
    scan_type: str = "manual"
    description: Optional[str] = None
    schedule_type: str = "manual"  # manual/weekly
    filter_rules: Optional[Dict[str, Any]] = None


class ScanResponse(BaseModel):
    """扫描响应"""
    id: str
    scan_path: str
    scan_type: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    series_found: int = 0
    series_new: int = 0
    series_duplicated: int = 0
    status: str

    class Config:
        from_attributes = True


class ScanConfigResponse(BaseModel):
    """扫描配置响应"""
    id: int
    scan_path: str
    description: Optional[str] = None
    is_active: bool
    schedule_type: str
    last_scan_at: Optional[str] = None
    filter_rules: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class FilterRuleCreate(BaseModel):
    """筛选规则创建"""
    modality: str
    min_slice_thickness: Optional[int] = None
    min_image_count: Optional[int] = None


class FilterRuleResponse(BaseModel):
    """筛选规则响应"""
    id: int
    modality: str
    min_slice_thickness: Optional[int] = None
    min_image_count: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    """导出请求"""
    series_ids: List[str]
    target_dir: str


class ExportResponse(BaseModel):
    """导出响应"""
    success: bool
    exported_count: int
    target_dir: str
    message: str
