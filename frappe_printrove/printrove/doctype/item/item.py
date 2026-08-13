import frappe


def on_update(doc, method=None):
	"""Item on_update hook."""
	if getattr(frappe.flags, "in_printrove_sync", False):
		return

	if getattr(doc, "item_group", "") == "Print Files" and not getattr(doc, "printrove_id", None):
		frappe.db.after_commit.add(
			lambda: frappe.enqueue(
				"frappe_printrove.jobs.design.create_design",
				item_code=doc.name,
			)
		)
