from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.printrove.doctype.item.item import on_update


class TestDoctypeItemUnit(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_item_on_update_print_file(self, mock_enqueue) -> None:
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_ITEM_UNIT_HOOK",
				"item_name": "Test Item Unit Hook",
				"item_group": "Print Files",
			}
		).insert()

		on_update(item)
		frappe.db.commit()

		mock_enqueue.assert_called_with(
			"frappe_printrove.jobs.design.create_design",
			item_code=item.name,
		)
