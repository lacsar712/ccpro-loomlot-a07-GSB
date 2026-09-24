"""清缸确认相关共享查询。

排液放行判断与「读最新确认单」必须走同一条查询，统一收口在这里：
一次查询同时拿到染缸与其最新一张确认单（无确认则第二项为 None）。
"""

from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.clean_confirm import CleanConfirm
from app.models.vat import Vat


def get_vat_with_latest_confirm(
    db: Session, vat_id: int
) -> Optional[Tuple[Vat, Optional[CleanConfirm]]]:
    """返回 (染缸, 最新确认单)；染缸不存在返回 None；无确认单时确认单为 None。"""
    latest_sub = (
        db.query(
            CleanConfirm.vat_id.label("vat_id"),
            func.max(CleanConfirm.id).label("latest_id"),
        )
        .filter(CleanConfirm.vat_id == vat_id)
        .group_by(CleanConfirm.vat_id)
        .subquery()
    )
    return (
        db.query(Vat, CleanConfirm)
        .outerjoin(latest_sub, latest_sub.c.vat_id == Vat.id)
        .outerjoin(CleanConfirm, CleanConfirm.id == latest_sub.c.latest_id)
        .filter(Vat.id == vat_id)
        .first()
    )
