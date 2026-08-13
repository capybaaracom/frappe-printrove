from frappe.tests.utils import FrappeTestCase

from frappe_printrove.jobs.order import get_available_credit


class TestDoctypePrintroveSettingsUnit(FrappeTestCase):
	def test_get_available_credit_default(self) -> None:
		credit = get_available_credit("NonExistentCompany")
		self.assertGreaterEqual(credit, 0.0)
