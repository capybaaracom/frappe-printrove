from pathlib import Path

import vcr
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.client import PrintroveClient
from frappe_printrove.schemas.design import DesignUrlRequest
from frappe_printrove.schemas.product import DesignDimension, PlacementDesign, ProductCreateRequest
from frappe_printrove.schemas.serviceability import ServiceabilityRequest

CASSETTE_DIR = Path(__file__).parent / "fixtures" / "cassettes"

vcr_fixture = vcr.VCR(
	cassette_library_dir=str(CASSETTE_DIR),
	record_mode="none",
	filter_headers=["Authorization"],
)


class TestExternalPrintroveAPIIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.client = PrintroveClient()

	@vcr_fixture.use_cassette("test_get_access_token.yaml")
	def test_token_acquisition(self) -> None:
		token = self.client.get_token()
		self.assertTrue(token)
		self.assertIsInstance(token, str)

	@vcr_fixture.use_cassette("test_get_serviceability.yaml")
	def test_serviceability_check(self) -> None:
		req = ServiceabilityRequest(pincode="560001", weight=500, country="India", cod="false")
		res = self.client.get_serviceability(req)
		self.assertEqual(res.status, "success")
		self.assertGreater(len(res.options), 0)

	@vcr_fixture.use_cassette("test_create_design.yaml")
	def test_create_design_from_url(self) -> None:
		req = DesignUrlRequest(
			name="Test Design 842d6d8f",
			url="https://frappe.io/assets/frappe_io/images/frappe-logo.png",
		)
		res = self.client.create_design_from_url(req)
		self.assertEqual(res.id, 11926314808)
		self.assertEqual(res.name, "Test Design 842d6d8f")
