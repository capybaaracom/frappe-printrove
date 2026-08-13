from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.schemas.product import ProductCreateResponse


class TestJobsProductUnit(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.create_product")
	def test_create_product_unit(self, mock_create_product) -> None:
		mock_create_product.return_value = ProductCreateResponse(product_id=8888, name="TEST_PRODUCT")

		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_FINISHED_GOOD_UNIT",
				"item_name": "Test Finished Good Unit",
				"item_group": "Products",
			}
		).insert()

		child_item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_PRINT_CHILD_UNIT",
				"item_name": "Test Print Child Unit",
				"item_group": "Print Files",
				"printrove_id": "999",
			}
		).insert()

		bom = frappe.get_doc(
			{
				"doctype": "BOM",
				"item": item.name,
				"quantity": 1,
				"items": [
					{
						"item_code": child_item.name,
						"qty": 1,
						"rate": 100,
					}
				],
			}
		).insert()

		from frappe_printrove.jobs.product import create_product

		product_id = create_product(bom.name)

		self.assertEqual(product_id, "8888")
		bom.reload()
		self.assertEqual(bom.printrove_id, "8888")
		item.reload()
		self.assertEqual(item.printrove_id, "8888")
