from unittest.mock import MagicMock, patch

import frappe
import pytest
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.client import PrintroveClient
from frappe_printrove.schemas.design import DesignResponse, DesignUrlRequest
from frappe_printrove.schemas.order import OrderCreateRequest, OrderCreateResponse, OrderItem, ShippingAddress


class TestPrintroveClientUnit(FrappeTestCase):
	def setUp(self) -> None:
		self.client = PrintroveClient(
			base_url="https://api.printrove.com",
			email="aryan.singh@capybaara.com",
			password="Corsage3-Bunion-Army",
		)

	@patch("requests.post")
	def test_get_token(self, mock_post) -> None:
		mock_res = MagicMock()
		mock_res.json.return_value = {"token": "test_bearer_token"}
		mock_res.raise_for_status.return_value = None
		mock_post.return_value = mock_res

		frappe.cache().delete_value("printrove_access_token:aryan.singh@capybaara.com")
		token = self.client.get_token()

		self.assertEqual(token, "test_bearer_token")
		mock_post.assert_called_once()

	@patch("requests.post")
	def test_create_design_from_url(self, mock_post) -> None:
		# Mock token post
		mock_token_res = MagicMock()
		mock_token_res.json.return_value = {"token": "test_token"}
		mock_token_res.raise_for_status.return_value = None

		# Mock design post
		mock_design_res = MagicMock()
		mock_design_res.json.return_value = {"data": {"id": 12345, "name": "TEST_DESIGN"}}
		mock_design_res.raise_for_status.return_value = None

		mock_post.side_effect = [mock_token_res, mock_design_res]

		req = DesignUrlRequest(name="TEST_DESIGN", url="https://example.com/design.png")
		res = self.client.create_design_from_url(req)

		self.assertIsInstance(res, DesignResponse)
		self.assertEqual(res.id, 12345)
		self.assertEqual(res.name, "TEST_DESIGN")
