"""
API路由 - 序列管理
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.db.models import Series, ScanConfig, FilterRule, Scan
from app.schemas.series import (
    SeriesResponse, ScanCreate, ScanResponse,
    ScanConfigResponse, FilterRuleCreate, FilterRuleResponse,
    ExportRequest, ExportResponse
)
from app.services.scan_service import ScanService, ExportService

router = APIRouter()


# ========== 序列查询 ==========

@router.get("/series", response_model=List[SeriesResponse])
def get_series(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: Optional[str] = None,
    patient_name: Optional[str] = None,
    modality: Optional[str] = None,
    protocol_name: Optional[str] = None,
    study_date_from: Optional[str] = None,
    study_date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取序列列表（支持分页和筛选）"""
    query = db.query(Series).filter(Series.is_active == True)

    if patient_id:
        query = query.filter(Series.patient_id.contains(patient_id))
    if patient_name:
        query = query.filter(Series.patient_name.contains(patient_name))
    if modality:
        query = query.filter(Series.modality == modality)
    if protocol_name:
        query = query.filter(Series.protocol_name.contains(protocol_name))
    if study_date_from:
        query = query.filter(Series.study_date >= study_date_from)
    if study_date_to:
        query = query.filter(Series.study_date <= study_date_to)

    # 分页
    offset = (page - 1) * page_size
    series_list = query.order_by(Series.created_at.desc()).offset(offset).limit(page_size).all()

    return series_list


@router.get("/series/count")
def get_series_count(
    patient_id: Optional[str] = None,
    patient_name: Optional[str] = None,
    modality: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取序列总数"""
    query = db.query(Series).filter(Series.is_active == True)

    if patient_id:
        query = query.filter(Series.patient_id.contains(patient_id))
    if patient_name:
        query = query.filter(Series.patient_name.contains(patient_name))
    if modality:
        query = query.filter(Series.modality == modality)

    return {"total": query.count()}


@router.get("/series/{series_id}", response_model=SeriesResponse)
def get_series_by_id(series_id: str, db: Session = Depends(get_db)):
    """根据ID获取序列详情"""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="序列不存在")
    return series


# ========== 扫描配置管理 ==========

@router.get("/configs", response_model=List[ScanConfigResponse])
def get_configs(db: Session = Depends(get_db)):
    """获取所有扫描配置"""
    return db.query(ScanConfig).order_by(ScanConfig.created_at.desc()).all()


@router.post("/configs", response_model=ScanConfigResponse)
def create_config(config: ScanCreate, db: Session = Depends(get_db)):
    """创建扫描配置"""
    db_config = ScanConfig(
        scan_path=config.scan_path,
        description=config.description,
        schedule_type=config.schedule_type,
        filter_rules=json.dumps(config.filter_rules) if config.filter_rules else None,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.put("/configs/{config_id}", response_model=ScanConfigResponse)
def update_config(config_id: int, config: ScanCreate, db: Session = Depends(get_db)):
    """更新扫描配置"""
    db_config = db.query(ScanConfig).filter(ScanConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")

    db_config.scan_path = config.scan_path
    db_config.description = config.description
    db_config.schedule_type = config.schedule_type
    db_config.filter_rules = json.dumps(config.filter_rules) if config.filter_rules else None

    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/configs/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """删除扫描配置"""
    db_config = db.query(ScanConfig).filter(ScanConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")

    db.delete(db_config)
    db.commit()
    return {"message": "删除成功"}


# ========== 扫描执行 ==========

@router.post("/scan/{config_id}", response_model=ScanResponse)
def run_scan(config_id: int, db: Session = Depends(get_db)):
    """手动触发扫描"""
    service = ScanService(db)
    try:
        scan = service.run_scan(config_id)
        return scan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans", response_model=List[ScanResponse])
def get_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取扫描历史"""
    offset = (page - 1) * page_size
    return db.query(Scan).order_by(Scan.started_at.desc()).offset(offset).limit(page_size).all()


# ========== 筛选规则 ==========

@router.get("/filter-rules", response_model=List[FilterRuleResponse])
def get_filter_rules(db: Session = Depends(get_db)):
    """获取所有筛选规则"""
    return db.query(FilterRule).all()


@router.post("/filter-rules", response_model=FilterRuleResponse)
def create_filter_rule(rule: FilterRuleCreate, db: Session = Depends(get_db)):
    """创建筛选规则"""
    # 检查是否已存在同模态规则，存在则更新
    existing = db.query(FilterRule).filter(FilterRule.modality == rule.modality).first()
    if existing:
        existing.min_slice_thickness = rule.min_slice_thickness
        existing.min_image_count = rule.min_image_count
        db.commit()
        db.refresh(existing)
        return existing

    db_rule = FilterRule(
        modality=rule.modality,
        min_slice_thickness=rule.min_slice_thickness,
        min_image_count=rule.min_image_count,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/filter-rules/{rule_id}")
def delete_filter_rule(rule_id: int, db: Session = Depends(get_db)):
    """删除筛选规则"""
    rule = db.query(FilterRule).filter(FilterRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    db.delete(rule)
    db.commit()
    return {"message": "删除成功"}


# ========== 数据导出 ==========

@router.post("/export", response_model=ExportResponse)
def export_series(req: ExportRequest, db: Session = Depends(get_db)):
    """导出选中的序列"""
    service = ExportService(db)
    result = service.export_series(req.series_ids, req.target_dir)
    return result


# ========== 统计 ==========

@router.get("/stats/modality")
def get_modality_stats(db: Session = Depends(get_db)):
    """按模态统计"""
    from sqlalchemy import func

    results = db.query(
        Series.modality,
        func.count(Series.id).label('count')
    ).filter(Series.is_active == True).group_by(Series.modality).all()

    return [{"modality": r.modality, "count": r.count} for r in results]


@router.get("/stats/date")
def get_date_stats(db: Session = Depends(get_db)):
    """按日期统计"""
    from sqlalchemy import func

    results = db.query(
        Series.study_date,
        func.count(Series.id).label('count')
    ).filter(
        Series.is_active == True,
        Series.study_date != None
    ).group_by(Series.study_date).order_by(Series.study_date.desc()).limit(30).all()

    return [{"date": r.study_date, "count": r.count} for r in results]


import json
