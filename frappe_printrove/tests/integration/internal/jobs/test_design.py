from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.jobs.design import create_design
from frappe_printrove.schemas.design import DesignResponse


class TestJobsDesignIntegration(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.create_design_from_url")
	def test_create_design_integration_flow(self, mock_client_create) -> None:
		mock_client_create.return_value = DesignResponse(id=54321, name="TEST_INT_ITEM")

		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_INT_DESIGN_ITEM",
				"item_name": "Test Int Design Item",
				"item_group": "Print Files",
			}
		).insert()

		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "test_design_int.png",
				"attached_to_doctype": "Item",
				"attached_to_name": item.name,
				"file_url": "/files/test_design_int.png",
				"content": b"dummy_png_bytes",
			}
		).insert()

		design_id = create_design(item.name)

		self.assertEqual(design_id, "54321")
		item.reload()
		self.assertEqual(item.printrove_id, "54321")
