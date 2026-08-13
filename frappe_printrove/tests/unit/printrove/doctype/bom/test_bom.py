from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.printrove.doctype.bom.bom import on_submit


class TestDoctypeBOMUnit(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_bom_on_submit(self, mock_enqueue) -> None:
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_BOM_ITEM_UNIT",
				"item_name": "Test BOM Item Unit",
				"item_group": "Products",
			}
		).insert()

		bom = frappe.get_doc(
			{
				"doctype": "BOM",
				"item": item.name,
				"quantity": 1,
				"items": [{"item_code": item.name, "qty": 1, "rate": 10}],
			}
		).insert()

		on_submit(bom)
		frappe.db.commit()

		mock_enqueue.assert_called_with(
			"frappe_printrove.jobs.product.create_product",
			bom_name=bom.name,
		)
