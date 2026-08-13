import frappe

from frappe_printrove.client import PrintroveClient
from frappe_printrove.schemas.product import DesignDimension, PlacementDesign, ProductCreateRequest


def create_product(bom_name: str) -> str:
	"""Action 2: Background job to create product on Printrove API for a BOM."""
	bom = frappe.get_doc("BOM", bom_name)
	if bom.printrove_id:
		return str(bom.printrove_id)

	# Collect print file items in BOM
	designs_map = {}
	for row in bom.items:
		item_group = frappe.db.get_value("Item", row.item_code, "item_group")
		if item_group == "Print Files":
			design_id = frappe.db.get_value("Item", row.item_code, "printrove_id")
			if not design_id:
				# Wait for design creation item update
				frappe.wait_for(event_key="on_update", filters={"doctype": "Item", "name": row.item_code})
				design_id = frappe.db.get_value("Item", row.item_code, "printrove_id")

			if design_id:
				# Map print position placement
				placement_key = getattr(row, "printrove_placement", None) or "front"
				width = int(getattr(row, "print_width", 3000) or 3000)
				height = int(getattr(row, "print_height", 4000) or 4000)
				top = int(getattr(row, "print_top", 0) or 0)
				left = int(getattr(row, "print_left", 0) or 0)

				designs_map[placement_key] = PlacementDesign(
					id=int(design_id),
					dimensions=DesignDimension(width=width, height=height, top=top, left=left),
				)

	# Default blank product/variant IDs from BOM or Settings if custom fields absent
	blank_product_id = int(getattr(bom, "printrove_blank_product_id", 1) or 1)
	blank_variant_id = int(getattr(bom, "printrove_blank_variant_id", 1) or 1)

	request = ProductCreateRequest(
		blank_product_id=blank_product_id,
		blank_variant_id=blank_variant_id,
		designs=designs_map,
	)

	client = PrintroveClient()
	response = client.create_product(request)

	product_id = str(response.product_id)
	bom.db_set("printrove_id", product_id)

	# Set finished good Item printrove_id
	if bom.item:
		frappe.db.set_value("Item", bom.item, "printrove_id", product_id)

	return product_id
