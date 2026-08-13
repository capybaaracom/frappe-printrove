import frappe


def on_submit(doc, method=None):
	"""BOM on_submit hook."""
	frappe.db.after_commit.add(
		lambda: frappe.enqueue(
			"frappe_printrove.jobs.product.create_product",
			bom_name=doc.name,
		)
	)
