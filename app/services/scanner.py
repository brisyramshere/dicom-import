import pydicom
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
import hashlib
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DicomInfo:
    """DICOM文件信息"""
    file_path: str
    patient_id: str
    patient_name: str
    patient_sex: Optional[str] = None
    patient_birth_date: Optional[str] = None

    study_instance_uid: str = ""
    study_date: Optional[str] = None

    series_instance_uid: str = ""
    series_number: Optional[int] = None
    series_description: Optional[str] = None
    modality: str = ""
    protocol_name: Optional[str] = None

    manufacturer: Optional[str] = None
    manufacturer_model: Optional[str] = None

    # CT参数
    slice_thickness: Optional[float] = None
    ct_params: Optional[Dict[str, Any]] = None

    # MR参数
    mr_params: Optional[Dict[str, Any]] = None

    # DR参数
    dx_params: Optional[Dict[str, Any]] = None

    file_size: int = 0
    file_modified: Optional[str] = None


class DicomScanner:
    """DICOM扫描器"""

    # 需要提取的Tag
    TAGS = {
        'patient_id': ('0010', '0020'),
        'patient_name': ('0010', '0010'),
        'patient_sex': ('0010', '0040'),
        'patient_birth_date': ('0010', '0030'),
        'study_instance_uid': ('0020', '000D'),
        'study_date': ('0008', '0020'),
        'series_instance_uid': ('0020', '000E'),
        'series_number': ('0020', '0011'),
        'series_description': ('0008', '103E'),
        'modality': ('0008', '0060'),
        'protocol_name': ('0018', '1030'),
        'manufacturer': ('0008', '0070'),
        'manufacturer_model': ('0008', '1090'),
        # CT特定
        'slice_thickness': ('0018', '0050'),
        'kvp': ('0018', '0060'),
        'rotation_time': ('0018', '0050'),
        # MR特定
        'tr': ('0018', '0080'),
        'te': ('0018', '0081'),
        'ti': ('0018', '0082'),
        'flip_angle': ('0018', '1314'),
        # DR特定
        'exposure': ('0018', '1152'),
    }

    @staticmethod
    def is_dicom_file(file_path: str) -> bool:
        """判断文件是否为DICOM"""
        try:
            with open(file_path, 'rb') as f:
                f.seek(128)
                return f.read(4) == b'DICM'
        except Exception:
            return False

    @staticmethod
    def read_dicom(file_path: str) -> Optional[DicomInfo]:
        """读取DICOM文件信息"""
        try:
            ds = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)

            # 获取文件信息
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

            info = DicomInfo(
                file_path=file_path,
                patient_id=str(getattr(ds, 'PatientID', '')),
                patient_name=str(getattr(ds, 'PatientName', '')),
                patient_sex=str(getattr(ds, 'PatientSex', '')) or None,
                patient_birth_date=str(getattr(ds, 'PatientBirthDate', '')) or None,
                study_instance_uid=str(getattr(ds, 'StudyInstanceUID', '')),
                study_date=str(getattr(ds, 'StudyDate', '')) or None,
                series_instance_uid=str(getattr(ds, 'SeriesInstanceUID', '')),
                series_number=getattr(ds, 'SeriesNumber', None),
                series_description=str(getattr(ds, 'SeriesDescription', '')) or None,
                modality=str(getattr(ds, 'Modality', '')),
                protocol_name=str(getattr(ds, 'ProtocolName', '')) or None,
                manufacturer=str(getattr(ds, 'Manufacturer', '')) or None,
                manufacturer_model=str(getattr(ds, 'ManufacturerModelName', '')) or None,
                file_size=file_size,
                file_modified=file_mtime,
            )

            # 提取模态特定参数
            if info.modality == 'CT':
                info.slice_thickness = getattr(ds, 'SliceThickness', None)
                info.ct_params = {
                    'slice_thickness': info.slice_thickness,
                    'kvp': getattr(ds, 'KVP', None),
                    'rotation_time': getattr(ds, 'RotationTime', None),
                }

            elif info.modality == 'MR':
                info.mr_params = {
                    'tr': getattr(ds, 'RepetitionTime', None),
                    'te': getattr(ds, 'EchoTime', None),
                    'ti': getattr(ds, 'InversionTime', None),
                    'flip_angle': getattr(ds, 'FlipAngle', None),
                }

            elif info.modality in ['DR', 'DX', 'CR']:
                info.dx_params = {
                    'exposure': getattr(ds, 'Exposure', None),
                    'kvp': getattr(ds, 'KVP', None),
                }

            return info

        except InvalidDicomError:
            return None
        except Exception as e:
            logger.warning(f"读取DICOM失败 {file_path}: {e}")
            return None

    @staticmethod
    def scan_directory(root_path: str, recursive: bool = True) -> List[str]:
        """扫描目录下所有DICOM文件"""
        dicom_files = []

        if recursive:
            for dirpath, dirnames, filenames in os.walk(root_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if DicomScanner.is_dicom_file(file_path):
                        dicom_files.append(file_path)
        else:
            for filename in os.listdir(root_path):
                file_path = os.path.join(root_path, filename)
                if os.path.isfile(file_path) and DicomScanner.is_dicom_file(file_path):
                    dicom_files.append(file_path)

        return dicom_files

    @staticmethod
    def group_by_series(file_paths: List[str]) -> Dict[str, List[str]]:
        """按SeriesInstanceUID分组"""
        series_map: Dict[str, List[str]] = {}

        for file_path in file_paths:
            info = DicomScanner.read_dicom(file_path)
            if info and info.series_instance_uid:
                if info.series_instance_uid not in series_map:
                    series_map[info.series_instance_uid] = []
                series_map[info.series_instance_uid].append(file_path)

        return series_map
