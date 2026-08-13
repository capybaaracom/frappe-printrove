from pydantic import BaseModel, Field


class DesignDimension(BaseModel):
	width: int
	height: int
	top: int = 0
	left: int = 0


class PlacementDesign(BaseModel):
	id: int
	dimensions: DesignDimension


class ProductCreateRequest(BaseModel):
	product_id: int = Field(..., alias="blank_product_id")
	variant_id: int = Field(..., alias="blank_variant_id")
	designs: dict[str, PlacementDesign]


class ProductCreateResponse(BaseModel):
	product_id: int
	name: str | None = None
