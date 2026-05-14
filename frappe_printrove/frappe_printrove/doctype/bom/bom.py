import frappe
import jsonata
import os
from frappe import _
from frappe_printrove.utils.integration_request import create

def on_submit(doc, method=None):
	settings = frappe.get_single("Printrove Settings")
	if not settings.enable_printrove or not settings.supplier:
		return

	if not _is_printrove_item(doc.item, settings.supplier):
		return

	blank_product_id, blank_variant_id, designs = _extract_printrove_details(doc)

	if blank_product_id and blank_variant_id and designs:
		create_product(doc, blank_product_id, blank_variant_id, designs)

def _is_printrove_item(item_code, supplier):
	return frappe.db.exists("Item Supplier", {"parent": item_code, "supplier": supplier})

def _extract_printrove_details(doc):
	blank_product_id = None
	blank_variant_id = None
	designs = {}

	for item in doc.items:
		item_info = frappe.db.get_value("Item", item.item_code, ["printrove_id", "item_group", "variant_of"], as_dict=True)
		if not item_info or not item_info.printrove_id:
			continue

		if item_info.item_group == "Print Files":
			placement = (item.get("print_placement") or "Front").lower()
			designs[placement] = {
				"id": int(item_info.printrove_id),
				"dimensions": {
					"width": int((item.get("print_width") or 0) * 300),
					"height": int((item.get("print_height") or 0) * 300),
					"top": int((item.get("print_top") or 0) * 300),
					"left": int((item.get("print_left") or 0) * 300),
				},
			}
		elif item_info.item_group == "Sub Assemblies":
			blank_variant_id = item_info.printrove_id
			if item_info.variant_of:
				blank_product_id = frappe.db.get_value("Item", item_info.variant_of, "printrove_id")

	return blank_product_id, blank_variant_id, designs

def create_product(doc, blank_product_id, blank_variant_id, designs):
	"""
	Constructs the payload and queues the "Create Product" integration request to the Printrove API.
	"""
	# Handle composite ID (category_id:product_id)
	real_product_id = blank_product_id
	if ":" in str(blank_product_id):
		real_product_id = blank_product_id.split(":")[1]

	payload = {
		"product_id": int(real_product_id),
		"name": doc.item_name or doc.item,
		"variants": [{"product_id": int(blank_variant_id)}],
		"design": designs,
	}
	try:
		create("BOM", doc.name, "Create Product", payload)
	except Exception:
		frappe.log_error(message=frappe.get_traceback(), title="Printrove BOM Sync Failed")
		frappe.throw(_("Failed to queue Product to Printrove. Check Error Log for details."))

def sync_all_products():
	"""
	Scheduled job to sync all Printrove products.
	"""
	template_items = frappe.get_all(
		"Item",
		filters={"printrove_id": ["like", "%:%"], "is_stock_item": 0},
		fields=["name", "printrove_id"]
	)
	
	for item in template_items:
		try:
			category_id, product_id = item.printrove_id.split(":")
			fetch_product(category_id, product_id)
		except Exception:
			frappe.log_error(title="Printrove Scheduled Sync Failed", message=frappe.get_traceback())

def fetch_product(category_id, product_id):
	"""
	Syncs a specific Printrove product and its variants.
	"""
	settings = frappe.get_single("Printrove Settings")
	if not settings.enable_printrove:
		return

	api = settings.get_api()
	try:
		product_data = api.get_product(category_id, product_id)
		if product_data.get("status") == "success":
			process_product_variants(product_data.get("product", {}))
	except Exception:
		frappe.log_error(title="Printrove Product Sync Failed", message=frappe.get_traceback())

def process_product_variants(product_data):
	"""
	Core logic to transform API data and create/update Specifications and BOMs.
	"""
	variants = product_data.get("variants", [])
	for variant in variants:
		variant_id = str(variant.get("id"))
		
		# 1. Find ERPNext Item (Sub Assembly)
		item_name = frappe.db.get_value("Item", {
			"printrove_id": variant_id,
			"item_group": "Sub Assemblies"
		}, "name")
		
		if not item_name:
			continue

		# 2. Create Specification Templates
		front_spec_name = None
		if variant.get("front_print_width"):
			front_spec_name = create_specification(variant, "Front")
			
		back_spec_name = None
		if variant.get("back_print_width"):
			back_spec_name = create_specification(variant, "Back")

		# 3. Create Template BOM
		create_bom(item_name, variant, front_spec_name, back_spec_name)

def create_specification(variant, placement):
	"""
	Evaluates JSONata and creates a Specification Template.
	"""
	jsonata_str = load_jsonata("specification.jsonata")
	expr = jsonata.Jsonata(jsonata_str)
	
	spec_dict = expr.evaluate({"variant": variant, "placement": placement})
	
	# Set a unique name for the template
	spec_dict["name"] = f"PR-SPEC-{variant.get('id')}-{placement}"
	
	# Check if an identical specification already exists to avoid duplicates
	if frappe.db.exists("Specification", spec_dict["name"]):
		return spec_dict["name"]
		
	spec_doc = frappe.get_doc(spec_dict)
	spec_doc.insert(ignore_permissions=True)
	return spec_doc.name

def create_bom(item_name, variant, front_spec_name, back_spec_name):
	"""
	Evaluates JSONata and creates a BOM for the Sub Assembly.
	"""
	jsonata_str = load_jsonata("bom.jsonata")
	expr = jsonata.Jsonata(jsonata_str)
	
	bom_dict = expr.evaluate({
		"variant": variant,
		"sub_assembly_item_code": item_name,
		"front_spec_name": front_spec_name,
		"back_spec_name": back_spec_name
	})
	
	current_bom = frappe.db.get_value("BOM", {"item": item_name, "is_default": 1, "docstatus": 1}, "name")
	if current_bom:
		if not has_bom_changed(current_bom, bom_dict):
			return current_bom

	bom_doc = frappe.get_doc(bom_dict)
	bom_doc.custom_bom_code = f"BOM-{item_name}-TEMPLATE"
	bom_doc.flags.ignore_mandatory = True
	bom_doc.insert(ignore_permissions=True)
	bom_doc.submit()
	
	# Set as default
	frappe.db.set_value("Item", item_name, "default_bom", bom_doc.name)
	
	return bom_doc.name

def has_bom_changed(bom_name, new_bom_dict):
	"""
	Compares existing BOM operations/specifications with the new ones.
	"""
	doc = frappe.get_doc("BOM", bom_name)
	new_ops = new_bom_dict.get("operations", [])
	
	if len(doc.operations) != len(new_ops):
		return True
		
	for i, op in enumerate(doc.operations):
		new_op = new_ops[i]
		if op.operation != new_op.get("operation") or op.specification != new_op.get("specification"):
			return True
			
	return False

def load_jsonata(filename):
	doctype_name = filename.split(".")[0]
	path = frappe.get_app_path("frappe_printrove", "frappe_printrove", "doctype", doctype_name, filename)
	
	if os.path.exists(path):
		with open(path, "r") as f:
			return f.read()
				
	frappe.throw(_("JSONata file not found: {0}").format(filename))
