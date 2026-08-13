# Copyright (c) 2024, Aquiveal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PrintroveSettings(Document):
	def validate(self):
		if self.enable_printrove:
			self.ensure_supplier()

	def ensure_supplier(self):
		if not self.supplier:
			# supplier look up by gst number
			supplier_name = "Printrove Products Private Limited"

			if frappe.db.has_column("Supplier", "gstin"):
				supplier_match = frappe.db.get_value("Supplier", {"gstin": "33AAICP8487B1Z9"}, "name")
				if supplier_match:
					supplier_name = supplier_match
					self.supplier = supplier_name
					return

			if not frappe.db.exists("Supplier", supplier_name):
				supplier_group = (
					frappe.db.get_single_value("Buying Settings", "supplier_group") or "Distributor"
				)
				if not frappe.db.exists("Supplier Group", supplier_group):
					frappe.get_doc(
						{"doctype": "Supplier Group", "supplier_group_name": supplier_group}
					).insert(ignore_permissions=True)

				supplier = frappe.get_doc(
					{
						"doctype": "Supplier",
						"supplier_name": supplier_name,
						"supplier_group": supplier_group,
					}
				)
				if frappe.db.has_column("Supplier", "gstin"):
					supplier.gstin = "33AAICP8487B1Z9"

				supplier.insert(ignore_permissions=True)
			self.supplier = supplier_name

	def get_api(self):
		from frappe_printrove.packages.frappe_printrove.client import PrintroveClient

		return PrintroveClient(self)

	def get_available_credit(self, company):
		if not self.printrove_credit_account:
			return 0

		# 1. Get GL Balance for the account
		gl_balance = frappe.db.sql(
			"""
            SELECT SUM(debit) - SUM(credit)
            FROM `tabGL Entry`
            WHERE account=%s AND company=%s AND is_cancelled=0
        """,
			(self.printrove_credit_account, company),
		)
		balance = gl_balance[0][0] or 0

		# 2. Get total unbilled amount from Purchase Orders linked to Printrove
		unbilled_amount = frappe.db.sql(
			"""
            SELECT SUM(grand_total * (100 - per_billed) / 100)
            FROM `tabPurchase Order`
            WHERE supplier=%s AND company=%s AND docstatus=1
            AND status NOT IN ('Completed', 'Cancelled', 'Closed')
        """,
			(self.supplier, company),
		)
		unbilled = unbilled_amount[0][0] or 0

		return float(balance) - float(unbilled)
