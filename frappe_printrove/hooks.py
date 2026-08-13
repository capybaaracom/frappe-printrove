app_name = "frappe_printrove"
app_title = "Frappe Printrove"
app_publisher = "Capybaara"
app_description = "Printrove"
app_email = "hello@capybaara.com"
app_license = "mit"

required_apps = ["frappe_controller", "frappe_core"]

controller_events = {
	"frappe_printrove.jobs.design.create_design": {"rate_limit_per_minute": 60, "retries": 3},
	"frappe_printrove.jobs.product.create_product": {"rate_limit_per_minute": 60, "retries": 3},
	"frappe_printrove.jobs.order.create_draft_po": {"rate_limit_per_minute": 60, "retries": 3},
	"frappe_printrove.jobs.order.process_printrove_purchase_order": {
		"rate_limit_per_minute": 30,
		"retries": 5,
	},
	"frappe_printrove.jobs.order.update_po_shipping": {"rate_limit_per_minute": 60, "retries": 3},
	"frappe_printrove.jobs.order.create_order": {"rate_limit_per_minute": 30, "retries": 3},
	"frappe_printrove.jobs.order.submit_po": {"rate_limit_per_minute": 60, "retries": 3},
}

doc_events = {
	"Item": {"on_update": "frappe_printrove.printrove.doctype.item.item.on_update"},
	"BOM": {"on_submit": "frappe_printrove.printrove.doctype.bom.bom.on_submit"},
	"Sales Order": {"on_submit": "frappe_printrove.printrove.doctype.sales_order.sales_order.on_submit"},
	"Purchase Order": {
		"on_update": "frappe_printrove.printrove.doctype.purchase_order.purchase_order.on_update"
	},
}

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "in", ["Printrove", "Frappe Printrove"]]]},
	{"dt": "Property Setter", "filters": [["module", "in", ["Printrove", "Frappe Printrove"]]]},
]
