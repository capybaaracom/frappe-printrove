from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.jobs.order import create_draft_po, process_printrove_purchase_order
from frappe_printrove.schemas.order import OrderCreateResponse
from frappe_printrove.schemas.serviceability import ServiceabilityOption, ServiceabilityResponse


class TestE2EJourneySODrivenPurchaseOrder(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.get_serviceability")
	@patch("frappe_printrove.client.PrintroveClient.create_order")
	def test_so_driven_purchase_order_e2e_path(self, mock_create_order, mock_serviceability) -> None:
		mock_serviceability.return_value = ServiceabilityResponse(
			pincode="110001",
			serviceable=True,
			options=[ServiceabilityOption(courier_name="Delhivery", price=50.0, estimated_days=2)],
		)
		mock_create_order.return_value = OrderCreateResponse(
			order_id=60606, status="Processing", order_cost=550.0
		)

		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "E2E SO Driven Customer",
				"customer_type": "Individual",
			}
		).insert(ignore_permissions=True)

		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "E2E_SO_DRIVEN_ITEM",
				"item_name": "E2E SO Driven Item",
				"item_group": "Products",
				"printrove_id": "7777",
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

		# Step 1: Draft PO created from Sales Order
		po_name = create_draft_po(so.name)
		self.assertTrue(po_name)

		# Step 2: PO on_update triggers decoupled orchestrator
		submitted_po_name = process_printrove_purchase_order(po_name)
		po = frappe.get_doc("Purchase Order", submitted_po_name)

		self.assertEqual(po.docstatus, 1)
		self.assertEqual(po.printrove_id, "60606")
