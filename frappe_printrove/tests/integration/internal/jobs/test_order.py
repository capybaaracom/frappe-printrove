from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.jobs.order import create_draft_po, create_order, submit_po, update_po_shipping
from frappe_printrove.schemas.order import OrderCreateResponse
from frappe_printrove.schemas.serviceability import ServiceabilityOption, ServiceabilityResponse


class TestJobsOrderIntegration(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.get_serviceability")
	@patch("frappe_printrove.client.PrintroveClient.create_order")
	def test_order_integration_child_pipeline(self, mock_create_order, mock_serviceability) -> None:
		mock_serviceability.return_value = ServiceabilityResponse(
			pincode="110001",
			serviceable=True,
			options=[ServiceabilityOption(courier_name="Delhivery", price=60.0, estimated_days=3)],
		)
		mock_create_order.return_value = OrderCreateResponse(
			order_id=11111, status="Processing", order_cost=660.0
		)

		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Test Customer Integration",
				"customer_type": "Individual",
			}
		).insert(ignore_permissions=True)

		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_INT_ORDER_ITEM",
				"item_name": "Test Int Order Item",
				"item_group": "Products",
				"printrove_id": "9876",
			}
		).insert()

		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": customer.name,
				"delivery_date": frappe.utils.nowdate(),
				"items": [{"item_code": item.name, "qty": 1, "rate": 600}],
			}
		).insert(ignore_permissions=True)

		po_name = create_draft_po(so.name)
		self.assertTrue(po_name)

		po_name = update_po_shipping(po_name)
		order_id = create_order(po_name)
		self.assertEqual(order_id, "11111")

		po_submitted = submit_po(po_name)
		po_doc = frappe.get_doc("Purchase Order", po_submitted)
		self.assertEqual(po_doc.docstatus, 1)
		self.assertEqual(po_doc.printrove_id, "11111")
