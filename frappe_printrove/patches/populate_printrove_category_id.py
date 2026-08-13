import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	# Ensure the custom field exists before updating
	if not frappe.db.has_column("Item", "printrove_category_id"):
		create_custom_field(
			"Item",
			{
				"fieldname": "printrove_category_id",
				"label": "Printrove Category ID",
				"fieldtype": "Data",
				"insert_after": "printrove_id",
				"module": "Frappe Printrove",
			},
		)

	# Find all items with composite IDs or missing category IDs for templates
	items = frappe.get_all("Item", filters={"printrove_id": ["like", "%:%"]}, fields=["name", "printrove_id"])

	for item in items:
		if ":" in str(item.printrove_id):
			category_id, product_id = item.printrove_id.split(":")

			# Update the item with separated IDs
			frappe.db.set_value(
				"Item",
				item.name,
				{"printrove_category_id": category_id, "printrove_id": product_id},
				update_modified=False,
			)

			frappe.logger().info(f"Split composite ID for Item {item.name}: {category_id}:{product_id}")
