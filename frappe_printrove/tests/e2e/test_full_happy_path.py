from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.jobs.order import create_purchase_order
from frappe_printrove.schemas.order import OrderCreateResponse
from frappe_printrove.schemas.serviceability import ServiceabilityOption, ServiceabilityResponse


class TestE2EJourneyFullHappyPath(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.get_serviceability")
	@patch("frappe_printrove.client.PrintroveClient.create_order")
	def test_e2e_full_happy_path_fast_execution(self, mock_create_order, mock_serviceability) -> None:
		mock_serviceability.return_value = ServiceabilityResponse(
			pincode="110001",
			serviceable=True,
			options=[ServiceabilityOption(courier_name="BlueDart", price=40.0, estimated_days=2)],
		)
		mock_create_order.return_value = OrderCreateResponse(
			order_id=88888, status="Placed", order_cost=540.0
		)

		# Setup pre-provisioned items and BOM
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "E2E Happy Path Customer",
				"customer_type": "Individual",
			}
		).insert(ignore_permissions=True)

		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "E2E_HAPPY_ITEM",
				"item_name": "E2E Happy Item",
				"item_group": "Print Files",
				"printrove_id": "12345",
			}
		).insert()

		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": customer.name,
				"delivery_date": frappe.utils.nowdate(),
				"items": [{"item_code": item.name, "qty": 1, "rate": 500}],
			}
		).insert(ignore_permissions=True)

		# Execute full orchestrator directly
		po_name = create_purchase_order(so.name)

		po = frappe.get_doc("Purchase Order", po_name)
		self.assertEqual(po.docstatus, 1)
		self.assertEqual(po.printrove_id, "88888")
