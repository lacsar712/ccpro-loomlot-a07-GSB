from pydantic import BaseModel, ConfigDict, Field


class DashboardStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dye_house_total: int = Field(serialization_alias="dyeHouseTotal")
    vat_ready_count: int = Field(serialization_alias="vatReadyCount")
    vat_dyeing_count: int = Field(serialization_alias="vatDyeingCount")
    # 染程中且尚无合格清缸确认的缸数（须与染缸列表同条件手数对账一致）
    vat_dyeing_unconfirmed_count: int = Field(
        serialization_alias="vatDyeingUnconfirmedCount"
    )
    lots_last_7d: int = Field(serialization_alias="lotsLast7d")
    checks_last_24h: int = Field(serialization_alias="checksLast24h")
