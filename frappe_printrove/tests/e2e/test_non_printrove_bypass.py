from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.printrove.doctype.sales_order.sales_order import on_submit


class TestE2EJourneyNonPrintroveBypass(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_non_printrove_item_clean_bypass(self, mock_enqueue) -> None:
		so = frappe._dict({"name": "SO-NON-PRINTROVE"})

		on_submit(so)
		frappe.db.commit()

		mock_enqueue.assert_called_with(
			"frappe_printrove.jobs.order.create_purchase_order",
			sales_order_name="SO-NON-PRINTROVE",
		)
