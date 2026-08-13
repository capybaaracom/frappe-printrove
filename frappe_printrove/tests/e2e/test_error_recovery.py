from unittest.mock import patch

import frappe
import requests
from frappe.tests.utils import FrappeTestCase

from frappe_printrove.jobs.order import create_order


class TestE2EJourneyErrorRecovery(FrappeTestCase):
	@patch("requests.post")
	def test_api_network_error_exception_bubbling(self, mock_post) -> None:
		mock_res = frappe._dict({"status_code": 502})
		mock_post.side_effect = requests.exceptions.HTTPError("502 Bad Gateway", response=mock_res)

		po = frappe.get_doc(
			{
				"doctype": "Purchase Order",
				"supplier": "Printrove",
				"company": "_Test Company",
				"items": [{"item_code": "TEST_RETRY_ITEM", "qty": 1, "rate": 100}],
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(requests.exceptions.HTTPError):
			create_order(po.name)
