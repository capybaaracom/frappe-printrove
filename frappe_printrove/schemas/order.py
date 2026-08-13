from pydantic import BaseModel


class ShippingAddress(BaseModel):
	name: str
	address_line1: str
	address_line2: str | None = None
	city: str
	state: str
	pincode: str
	phone: str


class OrderItem(BaseModel):
	printrove_id: int
	qty: int


class OrderCreateRequest(BaseModel):
	reference_number: str
	shipping_address: ShippingAddress
	items: list[OrderItem]


class OrderCreateResponse(BaseModel):
	order_id: int
	status: str
	order_cost: float
