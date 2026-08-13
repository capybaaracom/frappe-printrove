import frappe


def on_submit(doc, method=None):
	"""Sales Order on_submit hook."""
	frappe.db.after_commit.add(
		lambda: frappe.enqueue(
			"frappe_printrove.jobs.order.create_purchase_order",
			sales_order_name=doc.name,
		)
	)
