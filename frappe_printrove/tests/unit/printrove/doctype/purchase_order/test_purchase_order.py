from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.printrove.doctype.purchase_order.purchase_order import on_update


class TestDoctypePurchaseOrderUnit(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_purchase_order_on_update_hook(self, mock_enqueue) -> None:
		po = frappe._dict(
			{
				"name": "PO-TEST-UNIT-001",
				"docstatus": 0,
				"supplier": "Printrove",
				"printrove_id": None,
			}
		)

		on_update(po)
		frappe.db.commit()

		mock_enqueue.assert_called_with(
			"frappe_printrove.jobs.order.process_printrove_purchase_order",
			po_name="PO-TEST-UNIT-001",
		)
