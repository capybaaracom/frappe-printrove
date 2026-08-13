import frappe

from frappe_printrove.client import PrintroveClient
from frappe_printrove.schemas.design import DesignUrlRequest
from frappe_printrove.utils.image import ensure_supported_image_format


def create_design(item_code: str) -> str:
	"""Action 1: Background job to create design on Printrove API for an Item."""
	item = frappe.get_doc("Item", item_code)
	if item.printrove_id:
		return str(item.printrove_id)

	# Query attached files
	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Item", "attached_to_name": item_code},
		fields=["name", "file_name", "file_url", "is_private"],
		order_by="creation desc",
	)

	if not files:
		# Non-blocking wait for file attachment
		frappe.wait_for(
			event_key="after_insert",
			filters={"doctype": "File", "attached_to_doctype": "Item", "attached_to_name": item_code},
		)
		# Re-query file upon resumption
		files = frappe.get_all(
			"File",
			filters={"attached_to_doctype": "Item", "attached_to_name": item_code},
			fields=["name", "file_name", "file_url", "is_private"],
			order_by="creation desc",
		)
		if not files:
			frappe.throw(f"No file attached to Item {item_code}", frappe.DoesNotExistError)

	file_doc = frappe.get_doc("File", files[0].name)

	# Ensure supported image format using Pillow auto-conversion
	file_url = ensure_supported_image_format(file_doc)

	# Make presigned or absolute URL if relative
	if file_url.startswith("/"):
		site_url = frappe.utils.get_url()
		file_url = f"{site_url}{file_url}"

	client = PrintroveClient()
	request = DesignUrlRequest(name=item_code, url=file_url)
	response = client.create_design_from_url(request)

	design_id = str(response.id)
	item.db_set("printrove_id", design_id)

	return design_id
