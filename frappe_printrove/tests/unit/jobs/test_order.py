from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.schemas.order import OrderCreateResponse
from frappe_printrove.schemas.serviceability import ServiceabilityOption, ServiceabilityResponse


class TestJobsOrderUnit(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.get_serviceability")
	@patch("frappe_printrove.client.PrintroveClient.create_order")
	def test_order_child_jobs(self, mock_create_order, mock_serviceability) -> None:
		mock_serviceability.return_value = ServiceabilityResponse(
			pincode="110001",
			serviceable=True,
			options=[ServiceabilityOption(courier_name="BlueDart", price=50.0, estimated_days=2)],
		)
		mock_create_order.return_value = OrderCreateResponse(
			order_id=77777, status="Processing", order_cost=550.0
		)

		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Test Customer Unit",
				"customer_type": "Individual",
			}
		).insert(ignore_permissions=True)

		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_SO_ITEM_UNIT",
				"item_name": "Test SO Item Unit",
				"item_group": "Products",
				"printrove_id": "8888",
			}
		).insert()

		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": customer.name,
				"delivery_date": frappe.utils.nowdate(),
				"items": [
					{
						"item_code": item.name,
						"qty": 1,
						"rate": 500,
					}
				],
			}
		).insert(ignore_permissions=True)

		from frappe_printrove.jobs.order import create_draft_po, create_order, submit_po, update_po_shipping

		po_name = create_draft_po(so.name)
		self.assertTrue(po_name)

		po_name_updated = update_po_shipping(po_name)
		self.assertEqual(po_name_updated, po_name)

		order_id = create_order(po_name)
		self.assertEqual(order_id, "77777")

		submitted_po_name = submit_po(po_name)
		self.assertEqual(submitted_po_name, po_name)
		po = frappe.get_doc("Purchase Order", po_name)
		self.assertEqual(po.docstatus, 1)
