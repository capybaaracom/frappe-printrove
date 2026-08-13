from typing import Optional

from pydantic import BaseModel, field_validator


class DesignUrlRequest(BaseModel):
	name: str
	url: str

	@field_validator("url")
	def validate_url(cls, v: str) -> str:
		if not v.startswith(("http://", "https://", "/files/")):
			raise ValueError("Design URL must be a valid HTTP/HTTPS URL or local site file path")
		return v


class DesignResponse(BaseModel):
	id: int
	name: str
	url: str | None = None
