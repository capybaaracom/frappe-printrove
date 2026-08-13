from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.jobs.order import process_printrove_purchase_order
from frappe_printrove.schemas.order import OrderCreateResponse
from frappe_printrove.schemas.serviceability import ServiceabilityOption, ServiceabilityResponse


class TestE2EJourneyManualPurchaseOrder(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.get_serviceability")
	@patch("frappe_printrove.client.PrintroveClient.create_order")
	def test_manual_purchase_order_e2e_path(self, mock_create_order, mock_serviceability) -> None:
		mock_serviceability.return_value = ServiceabilityResponse(
			pincode="110001",
			serviceable=True,
			options=[ServiceabilityOption(courier_name="BlueDart", price=45.0, estimated_days=2)],
		)
		mock_create_order.return_value = OrderCreateResponse(
			order_id=70707, status="Processing", order_cost=545.0
		)

		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "E2E_MANUAL_PO_ITEM",
				"item_name": "E2E Manual PO Item",
				"item_group": "Products",
				"printrove_id": "8888",
			}
		).insert()

		# Direct manual draft Purchase Order creation by user / Material Request
		po = frappe.get_doc(
			{
				"doctype": "Purchase Order",
				"supplier": "Printrove",
				"company": "_Test Company",
				"schedule_date": frappe.utils.nowdate(),
				"items": [
					{"item_code": item.name, "qty": 1, "rate": 500, "schedule_date": frappe.utils.nowdate()}
				],
			}
		).insert(ignore_permissions=True)

		# Trigger orchestrator directly (simulating PO on_update hook)
		submitted_po_name = process_printrove_purchase_order(po.name)
		po_res = frappe.get_doc("Purchase Order", submitted_po_name)

		self.assertEqual(po_res.docstatus, 1)
		self.assertEqual(po_res.printrove_id, "70707")
