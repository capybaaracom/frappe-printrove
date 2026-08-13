from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.printrove.doctype.sales_order.sales_order import on_submit


class TestDoctypeSalesOrderUnit(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_sales_order_on_submit(self, mock_enqueue) -> None:
		so = frappe._dict({"name": "SO-00001"})

		on_submit(so)
		frappe.db.commit()

		mock_enqueue.assert_called_with(
			"frappe_printrove.jobs.order.create_purchase_order",
			sales_order_name="SO-00001",
		)
