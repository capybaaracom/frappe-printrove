import frappe

from frappe_printrove.frappe_printrove.doctype.bom.bom import process_product_variants


def get_product_details(product_id):
	from frappe_printrove.frappe_printrove.doctype.printrove_settings.printrove_settings import (
		PrintroveClient,
	)

	client = PrintroveClient()
	product = client._request("GET", f"/api/external/products/{product_id}")
	print(product)


def list_products():
	from frappe_printrove.frappe_printrove.doctype.printrove_settings.printrove_settings import (
		PrintroveClient,
	)

	client = PrintroveClient()
	products = client._request("GET", "/api/external/products")
	print(products)


def trigger_sync():
	item_code = "PR-SUB-TEST-2"
	variant_id = "99998"

	# 0. Delete existing
	frappe.db.delete("Specification", {"name": ["like", f"SPEC-{item_code}-%"]})
	frappe.db.delete("BOM", {"item": item_code})

	# 1. Ensure Item exists
	if not frappe.db.exists("Item", item_code):
		item_dict = {
			"doctype": "Item",
			"item_code": item_code,
			"item_name": "Test Sub Assembly",
			"item_group": "Sub Assemblies",
			"is_stock_item": 1,
			"printrove_id": variant_id,
		}
		if frappe.db.has_column("Item", "gst_hsn_code"):
			if not frappe.db.exists("GST HSN Code", "999900"):
				frappe.get_doc(
					{"doctype": "GST HSN Code", "name": "999900", "description": "Default HSN"}
				).insert(ignore_permissions=True)
			item_dict["gst_hsn_code"] = "999900"
		item = frappe.get_doc(item_dict)
		item.insert(ignore_permissions=True)
		print(f"Created Item: {item_code}")
	else:
		frappe.db.set_value("Item", item_code, "printrove_id", variant_id)
		print(f"Updated Item: {item_code}")

	# 2. Mock product data
	product_data = {
		"id": 12345,
		"name": "Test Product",
		"variants": [
			{
				"id": int(variant_id),
				"name": "Test Variant",
				"front_print_height": 3000,
				"front_print_width": 2400,
				"back_print_height": 3000,
				"back_print_width": 2400,
			}
		],
	}

	# 3. Trigger logic
	print("Triggering process_product_variants...")
	process_product_variants(product_data)

	# 4. Verify results
	item_name = frappe.db.get_value(
		"Item", {"printrove_id": variant_id, "item_group": "Sub Assemblies"}, "name"
	)
	specs = frappe.get_all(
		"Specification", filters={"name": ["like", f"SPEC-{item_name}-%"]}, fields=["name", "width", "height"]
	)
	print(f"Created Specifications: {[s.name for s in specs]}")

	bom_name = frappe.db.get_value("BOM", {"item": item_name, "docstatus": 1}, "name")
	if bom_name:
		bom = frappe.get_doc("BOM", bom_name)
		print(f"Created BOM: {bom_name}")
		print(f"BOM Operations: {[op.operation for op in bom.operations]}")
		print(f"BOM Specifications: {[op.specification for op in bom.operations]}")
	else:
		print("BOM not found!")
