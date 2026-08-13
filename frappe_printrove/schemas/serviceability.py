from pydantic import BaseModel, Field


class ServiceabilityRequest(BaseModel):
	pincode: str
	weight: int = 200
	country: str = "India"
	cod: str = "true"


class ServiceabilityOption(BaseModel):
	id: int | None = None
	courier_name: str = Field(..., alias="name")
	price: float = Field(..., alias="cost")


class ServiceabilityResponse(BaseModel):
	status: str = "success"
	options: list[ServiceabilityOption] = Field(default_factory=list, alias="couriers")
