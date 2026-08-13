from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.schemas.design import DesignResponse


class TestJobsDesignUnit(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.create_design_from_url")
	@patch("frappe_printrove.utils.file.ensure_supported_image_format")
	def test_create_design_with_file(self, mock_ensure_format, mock_api_create) -> None:
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_PRINT_ITEM_UNIT",
				"item_name": "Test Print Item Unit",
				"item_group": "Print Files",
			}
		).insert()

		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "test_design.png",
				"attached_to_doctype": "Item",
				"attached_to_name": item.name,
				"file_url": "/files/test_design.png",
			}
		).insert()

		mock_ensure_format.return_value = "/files/test_design.png"
		mock_api_create.return_value = DesignResponse(id=999, name=item.name)

		from frappe_printrove.jobs.design import create_design

		design_id = create_design(item.name)

		self.assertEqual(design_id, "999")
		item.reload()
		self.assertEqual(item.printrove_id, "999")
