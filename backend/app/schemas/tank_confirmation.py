from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TankConfirmationCreate(BaseModel):
    vat_id: int = Field(..., alias="vatId")
    # 勾选“是”：缸内残渣已清理干净
    residue_cleared: bool = Field(..., alias="residueCleared")
    # 勾选“是”：排液管路已冲洗干净
    pipe_flushed: bool = Field(..., alias="pipeFlushed")
    # 现场照片张数，至少 2 张
    photo_count: int = Field(..., ge=0, alias="photoCount")
    confirmed_at: Optional[datetime] = Field(None, alias="confirmedAt")
    confirmer: str = Field(..., min_length=1, max_length=64)

    model_config = ConfigDict(populate_by_name=True)


class TankConfirmationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    vat_id: int = Field(serialization_alias="vatId")
    residue_cleared: bool = Field(serialization_alias="residueCleared")
    pipe_flushed: bool = Field(serialization_alias="pipeFlushed")
    photo_count: int = Field(serialization_alias="photoCount")
    confirmed_at: datetime = Field(serialization_alias="confirmedAt")
    confirmer: str
    # 以本条为缸内最新确认单时，是否合格（残渣/管路均勾是且照片 >= 2）
    is_valid: bool = Field(default=False, serialization_alias="isValid")
