import frappe


def make_test_item_group(group_name: str = "Print Files") -> str:
	"""Ensures Item Group exists for test records."""
	if not frappe.db.exists("Item Group", group_name):
		parent = "All Item Groups" if frappe.db.exists("Item Group", "All Item Groups") else None
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": group_name,
				"parent_item_group": parent,
			}
		).insert(ignore_permissions=True)
	return group_name
