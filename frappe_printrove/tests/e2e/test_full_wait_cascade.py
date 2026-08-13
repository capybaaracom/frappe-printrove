import io
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from PIL import Image

from frappe_printrove.jobs.design import create_design
from frappe_printrove.jobs.order import create_purchase_order
from frappe_printrove.jobs.product import create_product
from frappe_printrove.schemas.design import DesignResponse
from frappe_printrove.schemas.order import OrderCreateResponse
from frappe_printrove.schemas.product import ProductCreateResponse
from frappe_printrove.schemas.serviceability import ServiceabilityOption, ServiceabilityResponse


class TestE2EJourneyFullWaitCascade(FrappeTestCase):
	@patch("frappe_printrove.client.PrintroveClient.create_design_from_url")
	@patch("frappe_printrove.client.PrintroveClient.create_product")
	@patch("frappe_printrove.client.PrintroveClient.get_serviceability")
	@patch("frappe_printrove.client.PrintroveClient.create_order")
	def test_e2e_full_wait_cascade_lifecycle(
		self, mock_create_order, mock_serviceability, mock_create_product, mock_create_design
	) -> None:
		mock_create_design.return_value = DesignResponse(id=10101, name="CASCADE_ITEM")
		mock_create_product.return_value = ProductCreateResponse(product_id=20202, name="CASCADE_PRODUCT")
		mock_serviceability.return_value = ServiceabilityResponse(
			pincode="110001",
			serviceable=True,
			options=[ServiceabilityOption(courier_name="XpressBees", price=35.0)],
		)
		mock_create_order.return_value = OrderCreateResponse(
			order_id=30303, status="Placed", order_cost=535.0
		)

		# Phase 1: Item created without file -> Pillow WEBP conversion
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "E2E_CASCADE_ITEM",
				"item_name": "E2E Cascade Item",
				"item_group": "Print Files",
			}
		).insert()

		buffer = io.BytesIO()
		img = Image.new("RGB", (100, 100), color="blue")
		img.save(buffer, format="WEBP")
		buffer.seek(0)

		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "cascade.webp",
				"attached_to_doctype": "Item",
				"attached_to_name": item.name,
				"content": buffer.getvalue(),
			}
		).insert()

		# Design creation
		design_id = create_design(item.name)
		self.assertEqual(design_id, "10101")

		# Phase 2: BOM creation & product sync
		bom = frappe.get_doc(
			{
				"doctype": "BOM",
				"item": item.name,
				"quantity": 1,
				"items": [{"item_code": item.name, "qty": 1, "rate": 100}],
			}
		).insert()

		product_id = create_product(bom.name)
		self.assertEqual(product_id, "20202")

		# Phase 3: Sales Order fulfillment
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "E2E Cascade Customer",
				"customer_type": "Individual",
			}
		).insert(ignore_permissions=True)

		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": customer.name,
				"delivery_date": frappe.utils.nowdate(),
				"items": [{"item_code": item.name, "qty": 1, "rate": 500}],
			}
		).insert(ignore_permissions=True)

		po_name = create_purchase_order(so.name)
		po_doc = frappe.get_doc("Purchase Order", po_name)
		self.assertEqual(po_doc.docstatus, 1)
		self.assertEqual(po_doc.printrove_id, "30303")
