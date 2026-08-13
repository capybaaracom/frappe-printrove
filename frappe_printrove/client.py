import frappe
import requests
from frappe import _

from frappe_printrove.schemas.design import DesignResponse, DesignUrlRequest
from frappe_printrove.schemas.order import OrderCreateRequest, OrderCreateResponse
from frappe_printrove.schemas.product import ProductCreateRequest, ProductCreateResponse
from frappe_printrove.schemas.serviceability import ServiceabilityRequest, ServiceabilityResponse

DEFAULT_BASE_URL = "https://api.printrove.com"


class PrintroveClient:
	"""Pydantic-powered HTTP client for Printrove API."""

	def __init__(
		self, base_url: str | None = None, email: str | None = None, password: str | None = None
	) -> None:
		site_config = frappe.get_site_config() if hasattr(frappe, "get_site_config") else {}
		self.base_url = (
			base_url
			or frappe.conf.get("printrove_base_url")
			or site_config.get("printrove_base_url")
			or DEFAULT_BASE_URL
		).rstrip("/")
		self.email = (
			email
			or frappe.conf.get("printrove_email")
			or site_config.get("printrove_email")
			or "aryan.singh@capybaara.com"
		)
		self.password = (
			password
			or frappe.conf.get("printrove_password")
			or site_config.get("printrove_password")
			or "Corsage3-Bunion-Army"
		)

	def get_token(self) -> str:
		"""Acquires and caches Printrove API access token."""
		cache_key = f"printrove_access_token:{self.email}"
		cached_token = frappe.cache().get_value(cache_key)
		if cached_token:
			return cached_token

		url = f"{self.base_url}/api/external/token"
		response = requests.post(url, json={"email": self.email, "password": self.password}, timeout=30)
		response.raise_for_status()

		data = response.json()
		token = data.get("access_token") or data.get("token")
		if not token:
			frappe.throw(_("Failed to retrieve access token from Printrove API"), frappe.ValidationError)

		frappe.cache().set_value(cache_key, token, expires_in_sec=3600)
		return token

	def _headers(self) -> dict[str, str]:
		token = self.get_token()
		return {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/json",
			"Accept": "application/json",
		}

	def create_design_from_url(self, request: DesignUrlRequest) -> DesignResponse:
		"""POST /api/external/designs/url"""
		url = f"{self.base_url}/api/external/designs/url"
		response = requests.post(url, json=request.model_dump(), headers=self._headers(), timeout=60)
		response.raise_for_status()

		data = response.json()
		result = data.get("data") if isinstance(data, dict) and "data" in data else data
		return DesignResponse.model_validate(result)

	def create_product(self, request: ProductCreateRequest) -> ProductCreateResponse:
		"""POST /api/external/products"""
		url = f"{self.base_url}/api/external/products"
		payload = request.model_dump(by_alias=True)
		response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
		response.raise_for_status()

		data = response.json()
		result = data.get("data") if isinstance(data, dict) and "data" in data else data
		return ProductCreateResponse.model_validate(result)

	def get_serviceability(self, request: ServiceabilityRequest) -> ServiceabilityResponse:
		"""GET /api/external/serviceability"""
		url = f"{self.base_url}/api/external/serviceability"
		params = request.model_dump()
		response = requests.get(url, params=params, headers=self._headers(), timeout=30)
		response.raise_for_status()

		data = response.json()
		result = data.get("data") if isinstance(data, dict) and "data" in data else data
		return ServiceabilityResponse.model_validate(result)

	def create_order(self, request: OrderCreateRequest) -> OrderCreateResponse:
		"""POST /api/external/orders"""
		url = f"{self.base_url}/api/external/orders"
		response = requests.post(url, json=request.model_dump(), headers=self._headers(), timeout=60)
		response.raise_for_status()

		data = response.json()
		result = data.get("data") if isinstance(data, dict) and "data" in data else data
		return OrderCreateResponse.model_validate(result)
