from unittest.mock import patch

import frappe
import requests
from frappe.tests import IntegrationTestCase


class TestSalesOrderFacade(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.db.rollback()
		settings = frappe.get_single("Printrove Settings")
		settings.enable_printrove = 1
		settings.supplier = "Printrove Products Private Limited"
		settings.client_id = "test"
		settings.client_secret = "test"
		settings.base_url = "http://test"
		settings.flags.ignore_links = True
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	@patch("frappe_printrove.packages.frappe_printrove.client.PrintroveClient.get_access_token")
	@patch("frappe_printrove.packages.frappe_printrove.client.requests.request")
	@patch("frappe_printrove.packages.frappe_printrove.doctype.sales_order.sales_order.enqueue")
	def test_live_api_interaction_via_mock(self, mock_enqueue, mock_request, mock_token):
		mock_token.return_value = "mock_token"

		# We simulate the VCR interaction with mock_request
		mock_response = requests.Response()
		mock_response.status_code = 200
		mock_response._content = b'{"id": "PR-ORD-123", "order_cost": 50.0}'
		mock_request.return_value = mock_response

		from frappe_printrove.packages.frappe_printrove.doctype.sales_order.sales_order import (
			process_outbound,
		)

		payload = {
			"reference_number": "SO-001",
			"retail_price": 100.0,
			"customer": {
				"name": "John Doe",
				"email": "john@example.com",
				"number": "1234567890",
				"address1": "123 Main St",
				"city": "Mumbai",
				"state": "MH",
				"pincode": 400001,
				"country": "India",
			},
			"order_products": [{"variant_id": 123, "quantity": 1, "is_plain": False}],
			"cod": False,
			"reference_docname": "SO-001",
			"_draft_po_name": "PO-001",
			"_total_weight": 0.2,
		}

		process_outbound(payload)

		# Verify enqueue was called to loopback
		mock_enqueue.assert_called_once()
		call_args = mock_enqueue.call_args[1]
		self.assertEqual(call_args["payload"]["printrove_order_id"], "PR-ORD-123")

	@patch("frappe_printrove.packages.frappe_printrove.client.PrintroveClient.get_access_token")
	@patch("frappe_printrove.packages.frappe_printrove.client.requests.request")
	@patch("frappe_printrove.packages.frappe_printrove.doctype.sales_order.sales_order.enqueue")
	def test_rate_limit_exhaustion_deferral(self, mock_enqueue, mock_request, mock_token):
		mock_token.return_value = "mock_token"

		# We simulate HTTP 429
		mock_response = requests.Response()
		mock_response.status_code = 429

		http_error = requests.exceptions.HTTPError(response=mock_response)
		mock_request.side_effect = http_error

		from frappe_printrove.packages.frappe_printrove.doctype.sales_order.sales_order import (
			process_outbound,
		)

		payload = {"reference_docname": "SO-001"}

		with self.assertRaises(requests.exceptions.HTTPError):
			process_outbound(payload)

		# Enqueue should not have been called because the error was raised natively
		mock_enqueue.assert_not_called()
