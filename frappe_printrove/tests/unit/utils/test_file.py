import io

import frappe
from frappe.tests.utils import FrappeTestCase
from PIL import Image

from frappe_printrove.utils.file import ensure_supported_image_format


class TestUtilsFileUnit(FrappeTestCase):
	def setUp(self) -> None:
		self.item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "TEST_IMAGE_CONV_ITEM",
				"item_name": "Test Image Conv Item",
				"item_group": "Print Files",
			}
		).insert()

	def _create_test_image_file(self, format_name: str, file_extension: str):
		buffer = io.BytesIO()
		img = Image.new("RGB", (100, 100), color="red")
		img.save(buffer, format=format_name)
		buffer.seek(0)

		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"sample.{file_extension}",
				"attached_to_doctype": "Item",
				"attached_to_name": self.item.name,
				"content": buffer.getvalue(),
				"is_private": 0,
			}
		).insert()
		return file_doc

	def test_png_supported_format_bypass(self) -> None:
		file_doc = self._create_test_image_file("PNG", "png")
		url = ensure_supported_image_format(file_doc)
		self.assertEqual(url, file_doc.file_url)

	def test_webp_unsupported_format_conversion(self) -> None:
		file_doc = self._create_test_image_file("WEBP", "webp")
		url = ensure_supported_image_format(file_doc)
		self.assertNotEqual(url, file_doc.file_url)
		self.assertTrue(url.endswith(".png"))

	def test_bmp_unsupported_format_conversion(self) -> None:
		file_doc = self._create_test_image_file("BMP", "bmp")
		url = ensure_supported_image_format(file_doc)
		self.assertNotEqual(url, file_doc.file_url)
		self.assertTrue(url.endswith(".png"))
