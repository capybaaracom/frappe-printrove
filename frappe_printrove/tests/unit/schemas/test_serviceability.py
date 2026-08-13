from frappe.tests.utils import FrappeTestCase

from frappe_printrove.schemas.serviceability import (
	ServiceabilityOption,
	ServiceabilityRequest,
	ServiceabilityResponse,
)


class TestSchemasServiceabilityUnit(FrappeTestCase):
	def test_serviceability_request_defaults(self) -> None:
		req = ServiceabilityRequest(pincode="110001")
		self.assertEqual(req.pincode, "110001")
		self.assertEqual(req.weight, 200)
		self.assertEqual(req.country, "India")
		self.assertEqual(req.cod, "true")

	def test_serviceability_response_validation(self) -> None:
		res = ServiceabilityResponse.model_validate(
			{
				"status": "success",
				"couriers": [{"id": 44, "name": "Delhivery Air", "cost": 110.0}],
			}
		)
		self.assertEqual(res.status, "success")
		self.assertEqual(len(res.options), 1)
		self.assertEqual(res.options[0].courier_name, "Delhivery Air")
		self.assertEqual(res.options[0].price, 110.0)
