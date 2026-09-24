from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.vat import Vat


class TankConfirmation(Base):
    """清缸确认单：染缸排液前必须先填写，与排液动作绑死。"""

    __tablename__ = "tank_confirmations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vat_id: Mapped[int] = mapped_column(ForeignKey("vats.id"), nullable=False, index=True)
    # 残渣已清（勾“是”表示缸内残渣已清理干净）
    residue_cleared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 管路已冲（勾“是”表示排液管路已冲洗干净）
    pipe_flushed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 现场照片张数，至少 2 张才算合格
    photo_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmer: Mapped[str] = mapped_column(String(64), nullable=False)

    vat: Mapped["Vat"] = relationship("Vat", back_populates="tank_confirmations")
