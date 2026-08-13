from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.printrove.doctype.purchase_order.purchase_order import on_update


class TestDoctypePurchaseOrderIntegration(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_purchase_order_integration_trigger(self, mock_enqueue) -> None:
		po = frappe.get_doc(
			{
				"doctype": "Purchase Order",
				"supplier": "Printrove",
				"company": "_Test Company",
				"schedule_date": frappe.utils.nowdate(),
				"items": [
					{
						"item_code": "TEST_INT_ITEM",
						"qty": 1,
						"rate": 100,
						"schedule_date": frappe.utils.nowdate(),
					}
				],
			}
		).insert(ignore_permissions=True)

		on_update(po)
		frappe.db.commit()

		mock_enqueue.assert_called_with(
			"frappe_printrove.jobs.order.process_printrove_purchase_order",
			po_name=po.name,
		)
