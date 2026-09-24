from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# 照片至少 2 张
MIN_PHOTOS = 2


class CleanConfirmCreate(BaseModel):
    residue_cleared: bool = Field(..., alias="residueCleared")
    pipe_flushed: bool = Field(..., alias="pipeFlushed")
    photo_count: int = Field(..., ge=0, alias="photoCount")
    confirmed_at: datetime = Field(..., alias="confirmedAt")
    confirmer_name: str = Field(..., min_length=1, max_length=64, alias="confirmerName")

    model_config = ConfigDict(populate_by_name=True)


class CleanConfirmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    vat_id: int = Field(serialization_alias="vatId")
    residue_cleared: bool = Field(serialization_alias="residueCleared")
    pipe_flushed: bool = Field(serialization_alias="pipeFlushed")
    photo_count: int = Field(serialization_alias="photoCount")
    confirmed_at: datetime = Field(serialization_alias="confirmedAt")
    confirmer_name: str = Field(serialization_alias="confirmerName")
    qualified: bool
