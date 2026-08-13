import frappe


def on_update(doc, method=None):
	"""Purchase Order on_update hook."""
	if getattr(frappe.flags, "in_printrove_sync", False):
		return

	target_supplier = frappe.conf.get("printrove_supplier") or "Printrove"

	if doc.docstatus == 0 and doc.supplier == target_supplier and not getattr(doc, "printrove_id", None):
		frappe.db.after_commit.add(
			lambda: frappe.enqueue(
				"frappe_printrove.jobs.order.process_printrove_purchase_order",
				po_name=doc.name,
			)
		)
