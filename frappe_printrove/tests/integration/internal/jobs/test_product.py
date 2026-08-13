from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.jobs.product import create_product
from frappe_printrove.schemas.product import ProductCreateResponse


class TestJobsProductIntegration(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.create_product")
	def test_create_product_integration_flow(self, mock_client_product) -> None:
		mock_client_product.return_value = ProductCreateResponse(product_id=9876, name="TEST_INT_PROD")

		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_INT_FG_ITEM",
				"item_name": "Test Int FG Item",
				"item_group": "Products",
			}
		).insert()

		child = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_INT_PRINT_CHILD",
				"item_name": "Test Int Print Child",
				"item_group": "Print Files",
				"printrove_id": "54321",
			}
		).insert()

		bom = frappe.get_doc(
			{
				"doctype": "BOM",
				"item": item.name,
				"quantity": 1,
				"items": [{"item_code": child.name, "qty": 1, "rate": 100}],
			}
		).insert()

		product_id = create_product(bom.name)

		self.assertEqual(product_id, "9876")
		bom.reload()
		self.assertEqual(bom.printrove_id, "9876")
		item.reload()
		self.assertEqual(item.printrove_id, "9876")
