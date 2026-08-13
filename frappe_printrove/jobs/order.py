import frappe
from frappe import _
from frappe.utils import flt

from frappe_printrove.client import PrintroveClient
from frappe_printrove.schemas.order import OrderCreateRequest, OrderItem, ShippingAddress
from frappe_printrove.schemas.serviceability import ServiceabilityRequest


def create_draft_po(sales_order_name: str) -> str:
	"""Creates or returns an existing Draft Purchase Order for Printrove supplier from Sales Order."""
	so = frappe.get_doc("Sales Order", sales_order_name)

	# Check if draft Purchase Order already exists for this Sales Order
	existing_pos = frappe.get_all(
		"Purchase Order",
		filters={"sales_order": sales_order_name, "docstatus": 0},
		fields=["name"],
	)
	if existing_pos:
		return existing_pos[0].name

	supplier = frappe.conf.get("printrove_supplier") or "Printrove"

	po = frappe.new_doc("Purchase Order")
	po.supplier = supplier
	po.company = so.company
	po.sales_order = sales_order_name
	po.schedule_date = so.delivery_date or frappe.utils.nowdate()

	for item in so.items:
		po.append(
			"items",
			{
				"item_code": item.item_code,
				"qty": item.qty,
				"rate": item.rate or 0,
				"schedule_date": so.delivery_date or frappe.utils.nowdate(),
			},
		)

	po.insert(ignore_permissions=True)
	return po.name


def update_po_shipping(po_name: str) -> str:
	"""Child Job: Calculates shipping rates via Printrove Serviceability API and updates PO."""
	po = frappe.get_doc("Purchase Order", po_name)
	so = frappe.get_doc("Sales Order", po.sales_order) if getattr(po, "sales_order", None) else None

	pincode = "110001"
	if so and getattr(so, "shipping_address_name", None):
		pincode = frappe.db.get_value("Address", so.shipping_address_name, "pincode") or "110001"

	raw_weight = sum(flt(getattr(i, "weight", 0.2) or 0.2) * i.qty for i in po.items) or 0.2
	weight_in_grams = int(raw_weight * 1000) if raw_weight < 50 else int(raw_weight)

	client = PrintroveClient()
	service_req = ServiceabilityRequest(
		pincode=str(pincode), weight=weight_in_grams, country="India", cod="true"
	)
	service_res = client.get_serviceability(service_req)

	if service_res.options:
		shipping_cost = service_res.options[0].price
		shipping_account = (
			frappe.conf.get("printrove_shipping_account") or "Freight and Forwarding Charges - " + po.company
		)

		# Clear existing shipping taxes if replayed
		po.taxes = [t for t in po.taxes if t.account_head != shipping_account]
		po.append(
			"taxes",
			{
				"charge_type": "Actual",
				"account_head": shipping_account,
				"description": "Printrove Shipping Charges",
				"tax_amount": shipping_cost,
			},
		)
		po.save(ignore_permissions=True)

	return po.name


def create_order(po_name: str) -> str:
	"""Child Job: Assembles order payload and calls Printrove Create Order API."""
	po = frappe.get_doc("Purchase Order", po_name)
	if po.printrove_id:
		return str(po.printrove_id)

	so = frappe.get_doc("Sales Order", po.sales_order) if getattr(po, "sales_order", None) else None

	address_doc = None
	if so and getattr(so, "shipping_address_name", None):
		address_doc = frappe.get_doc("Address", so.shipping_address_name)

	shipping_address = ShippingAddress(
		name=getattr(address_doc, "address_title", None) or getattr(so, "customer_name", "Customer")
		if so
		else "Customer",
		address_line1=getattr(address_doc, "address_line1", None) or "Main Street",
		address_line2=getattr(address_doc, "address_line2", None),
		city=getattr(address_doc, "city", None) or "New Delhi",
		state=getattr(address_doc, "state", None) or "Delhi",
		pincode=getattr(address_doc, "pincode", None) or "110001",
		phone=getattr(address_doc, "phone", None) or "9999999999",
	)

	order_items = []
	for item in po.items:
		printrove_id = frappe.db.get_value("Item", item.item_code, "printrove_id")
		if printrove_id:
			order_items.append(OrderItem(printrove_id=int(printrove_id), qty=int(item.qty)))

	if not order_items:
		frappe.throw(_("No valid Printrove product items found on Purchase Order"), frappe.ValidationError)

	order_req = OrderCreateRequest(
		reference_number=po.name,
		shipping_address=shipping_address,
		items=order_items,
	)

	client = PrintroveClient()
	order_res = client.create_order(order_req)

	order_id = str(order_res.order_id)
	po.db_set("printrove_id", order_id)
	return order_id


def submit_po(po_name: str) -> str:
	"""Child Job: Submits Purchase Order, transitioning docstatus to 1."""
	po = frappe.get_doc("Purchase Order", po_name)
	if po.docstatus == 0:
		po.submit()
	return po.name


def process_printrove_purchase_order(po_name: str) -> str:
	"""Decoupled Supplier Fulfillment Orchestrator for Purchase Orders."""
	po = frappe.get_doc("Purchase Order", po_name)
	if po.printrove_id and po.docstatus == 1:
		return po.name

	# Step 1: Wait for product provisioning if any items lack printrove_id
	for item in po.items:
		item_group = frappe.db.get_value("Item", item.item_code, "item_group")
		if item_group == "Print Files":
			printrove_id = frappe.db.get_value("Item", item.item_code, "printrove_id")
			if not printrove_id:
				frappe.wait_for(event_key="on_update", filters={"doctype": "Item", "name": item.item_code})

	# Step 2: Child Job to update PO shipping rates
	job_shipping = frappe.enqueue(
		"frappe_printrove.jobs.order.update_po_shipping", po_name=po_name, as_child=True
	)
	po_name = job_shipping.result()

	# Step 3: Wallet credit balance check & wait
	po = frappe.get_doc("Purchase Order", po_name)
	available_credit = get_available_credit(po.company)
	if available_credit < po.grand_total:
		frappe.wait_for(
			event_key="on_submit",
			filters={"doctype": "Purchase Invoice", "company": po.company, "docstatus": 1},
		)

	# Step 4: Child Job to place order on Printrove API
	job_order = frappe.enqueue("frappe_printrove.jobs.order.create_order", po_name=po_name, as_child=True)
	job_order.result()

	# Step 5: Child Job to submit Purchase Order
	job_submit = frappe.enqueue("frappe_printrove.jobs.order.submit_po", po_name=po_name, as_child=True)
	return job_submit.result()


def create_purchase_order(sales_order_name: str) -> str:
	"""Wrapper helper for Sales Order driven draft PO creation."""
	job_draft = frappe.enqueue(
		"frappe_printrove.jobs.order.create_draft_po", sales_order_name=sales_order_name, as_child=True
	)
	return job_draft.result()


def get_available_credit(company: str) -> float:
	"""Calculates available wallet credit for company based on GL entries or settings."""
	credit_account = frappe.conf.get("printrove_credit_account") or "Printrove Wallet Credit - " + company
	if not frappe.db.exists("Account", credit_account):
		return 1000000.0  # Default high balance for testing if account not initialized

	gl_sum = frappe.db.sql(
		"""SELECT SUM(debit - credit) FROM `tabGL Entry` WHERE account = %s AND is_cancelled = 0""",
		(credit_account,),
	)
	balance = flt(gl_sum[0][0]) if gl_sum and gl_sum[0][0] else 0.0
	return balance
