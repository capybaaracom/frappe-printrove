import unittest
import frappe
from unittest.mock import patch, MagicMock
from frappe_printrove.frappe_printrove.doctype.bom.bom import on_submit, fetch_product, process_product_variants

class TestBOM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings = frappe.get_doc("Printrove Settings")
        settings.enable_printrove = 1
        settings.client_id = "test@example.com"
        settings.client_secret = "test_password"
        settings.supplier = "Printrove Products Private Limited"
        settings.save(ignore_permissions=True)
        frappe.db.commit()

        if not frappe.db.exists("Item Group", "Print Files"):
            frappe.get_doc(
                {"doctype": "Item Group", "item_group_name": "Print Files", "is_group": 0}
            ).insert(ignore_permissions=True)

        if not frappe.db.exists("Item Group", "Sub Assemblies"):
            frappe.get_doc(
                {"doctype": "Item Group", "item_group_name": "Sub Assemblies", "is_group": 0}
            ).insert(ignore_permissions=True)

        if not frappe.db.exists("Item Attribute", "Test Size"):
            frappe.get_doc({
                "doctype": "Item Attribute",
                "attribute_name": "Test Size",
                "item_attribute_values": [{"attribute_value": "M", "abbr": "M"}]
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("GST HSN Code", "999900"):
            frappe.get_doc({"doctype": "GST HSN Code", "name": "999900", "description": "Default HSN"}).insert(ignore_permissions=True)

        if not frappe.db.exists("Workstation Type", "Printing"):
            frappe.get_doc({
                "doctype": "Workstation Type",
                "workstation_type": "Printing"
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Operation", "Printing"):
            frappe.get_doc({
                "doctype": "Operation",
                "name": "Printing",
                "workstation_type": "Printing"
            }).insert(ignore_permissions=True)

        template_name = "PR-SUB-TEMPLATE"
        if not frappe.db.exists("Item", template_name):
            template_dict = {
                "doctype": "Item",
                "item_code": template_name,
                "item_name": "Test Template Product",
                "item_group": "Sub Assemblies",
                "is_stock_item": 0,
                "has_variants": 1,
                "attributes": [{"attribute": "Test Size"}],
                "printrove_id": "25:460"
            }
            if frappe.db.has_column("Item", "gst_hsn_code"):
                template_dict["gst_hsn_code"] = "999900"
            
            doc = frappe.get_doc(template_dict)
            doc.flags.ignore_mandatory = True
            doc.flags.ignore_validate = True
            doc.insert(ignore_permissions=True, set_name=template_name)
        else:
            frappe.db.set_value("Item", template_name, "printrove_id", "25:460")

        variant_name = "PR-SUB-1"
        if not frappe.db.exists("Item", variant_name):
            item_dict1 = {
                "doctype": "Item",
                "item_code": variant_name,
                "item_name": "Test Blank Product",
                "item_group": "Sub Assemblies",
                "is_stock_item": 1,
                "variant_of": template_name,
                "printrove_id": "264",
                "attributes": [{"attribute": "Test Size", "attribute_value": "M"}]
            }
            if frappe.db.has_column("Item", "gst_hsn_code"):
                item_dict1["gst_hsn_code"] = "999900"
            
            doc = frappe.get_doc(item_dict1)
            doc.flags.ignore_mandatory = True
            doc.flags.ignore_validate = True
            doc.insert(ignore_permissions=True, set_name=variant_name)
        else:
            frappe.db.set_value("Item", variant_name, "printrove_id", "264")
            frappe.db.set_value("Item", variant_name, "item_group", "Sub Assemblies")
            frappe.db.set_value("Item", variant_name, "variant_of", template_name)

        if not frappe.db.exists("Item", "Test Print File"):
            item_dict2 = {
                "doctype": "Item",
                "item_code": "Test Print File",
                "item_name": "Test Print File",
                "item_group": "Print Files",
                "is_stock_item": 1,
                "printrove_id": "123"
            }
            if frappe.db.has_column("Item", "gst_hsn_code"):
                item_dict2["gst_hsn_code"] = "999900"
            frappe.get_doc(item_dict2).insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Item", "Test Print File", "printrove_id", "123")

        if not frappe.db.exists("Item", "Test Finished Product"):
            item_dict3 = {
                "doctype": "Item",
                "item_code": "Test Finished Product",
                "item_name": "Test Finished Product",
                "item_group": "All Item Groups",
                "is_stock_item": 1
            }
            if frappe.db.has_column("Item", "gst_hsn_code"):
                item_dict3["gst_hsn_code"] = "999900"
            frappe.get_doc(item_dict3).insert(ignore_permissions=True)
        
        doc = frappe.get_doc("Item", "Test Finished Product")
        if not any(s.supplier == "Printrove Products Private Limited" for s in doc.supplier_items):
            doc.append("supplier_items", {"supplier": "Printrove Products Private Limited"})
            doc.save(ignore_permissions=True)
        frappe.db.commit()

    def test_on_submit(self):
        import uuid
        uid = str(uuid.uuid4())[:8]
        bom = frappe.new_doc("BOM")
        bom.item = "Test Finished Product"
        bom.qty = 1
        bom.custom_bom_code = f"BOM-TEST-{uid}"
        bom.append("items", {"item_code": "PR-SUB-1", "qty": 1})
        bom.append("items", {
            "item_code": "Test Print File",
            "qty": 1,
            "print_placement": "Front",
            "print_width": 10.0,
            "print_height": 12.0
        })
        bom.insert(ignore_permissions=True)
        
        with patch("frappe_printrove.frappe_printrove.doctype.printrove_settings.printrove_settings.PrintroveClient") as MockAPI:
            mock_instance = MockAPI.return_value
            mock_instance.create_product.return_value = {"product": {"id": "prod_123", "variants": [{"id": "var_123"}]}}
            
            on_submit(bom)
            
            from frappe_printrove.utils.integration_request import process_product_request
            req = frappe.get_last_doc("Integration Request", filters={"reference_docname": bom.name, "request_description": "Create Product"})
            if req:
                process_product_request(req.name)
            
            bom.reload()
            self.assertEqual(bom.printrove_id, "var_123")
            self.assertEqual(frappe.db.get_value("Item", "Test Finished Product", "printrove_id"), "var_123")

    @patch("frappe_printrove.frappe_printrove.doctype.printrove_settings.printrove_settings.PrintroveClient.get_access_token")
    def test_process_product_variants(self, mock_token):
        """
        Test the core logic of transforming API data into Specifications and BOMs.
        """
        mock_token.return_value = "mock_token"
        mock_product_data = {
            "id": 460,
            "name": "Half Sleeve Round Neck T-Shirt",
            "variants": [
                {
                    "id": 264,
                    "name": "White S Men Round",
                    "front_print_height": 5880,
                    "front_print_width": 4680,
                    "back_print_height": 5880,
                    "back_print_width": 4680
                }
            ]
        }

        # Clear existing BOMs for the test item
        frappe.db.sql("delete from `tabBOM` where item='PR-SUB-1'")
        
        process_product_variants(mock_product_data)

        # Verify Specifications were created
        specs = frappe.get_all("Specification", filters={"is_template": 1}, fields=["name", "width", "height"])
        self.assertGreaterEqual(len(specs), 2)
        
        # Verify BOM was created for the Sub Assembly
        bom_name = frappe.db.get_value("BOM", {"item": "PR-SUB-1", "docstatus": 1}, "name")
        self.assertTrue(bom_name)
        
        bom = frappe.get_doc("BOM", bom_name)
        self.assertEqual(len(bom.operations), 2)
        self.assertEqual(bom.operations[0].operation, "Printing")
        self.assertTrue(bom.operations[0].specification)
        
        # Verify Item default BOM
        default_bom = frappe.db.get_value("Item", "PR-SUB-1", "default_bom")
        self.assertEqual(default_bom, bom_name)

    @patch("frappe_printrove.frappe_printrove.doctype.printrove_settings.printrove_settings.PrintroveClient.get_access_token")
    @patch("frappe_printrove.frappe_printrove.doctype.printrove_settings.printrove_settings.PrintroveClient.get_product")
    def test_fetch_product(self, mock_get_product, mock_token):
        """
        Test the orchestrator entry point.
        """
        mock_token.return_value = "mock_token"
        mock_get_product.return_value = {
            "status": "success",
            "product": {
                "id": 460,
                "variants": [
                    {
                        "id": 264,
                        "front_print_height": 5880,
                        "front_print_width": 4680
                    }
                ]
            }
        }
        
        fetch_product("25", "460")
        
        mock_get_product.assert_called_once_with("25", "460")
        
        # Verify BOM exists
        self.assertTrue(frappe.db.exists("BOM", {"item": "PR-SUB-1"}))

    def test_jsonata_specification(self):
        """
        Test the specification JSONata transformation directly.
        """
        from frappe_printrove.frappe_printrove.doctype.bom.bom import load_jsonata
        import jsonata
        
        jsonata_str = load_jsonata("specification.jsonata")
        expr = jsonata.Jsonata(jsonata_str)
        
        variant = {"id": 264, "front_print_width": 4680, "front_print_height": 5880}
        result = expr.evaluate({"variant": variant, "placement": "Front"})
        
        self.assertEqual(result["doctype"], "Specification")
        self.assertEqual(result["is_template"], 1)
        self.assertEqual(result["width"], 15.6) # 4680 / 300
        self.assertEqual(result["height"], 19.6) # 5880 / 300

    def test_jsonata_bom(self):
        """
        Test the BOM JSONata transformation directly.
        """
        from frappe_printrove.frappe_printrove.doctype.bom.bom import load_jsonata
        import jsonata
        
        jsonata_str = load_jsonata("bom.jsonata")
        expr = jsonata.Jsonata(jsonata_str)
        
        context = {
            "variant": {"id": 264},
            "sub_assembly_item_code": "PR-SUB-1",
            "front_spec_name": "SPEC-FRONT-1",
            "back_spec_name": "SPEC-BACK-1"
        }
        result = expr.evaluate(context)
        
        self.assertEqual(result["doctype"], "BOM")
        self.assertEqual(result["item"], "PR-SUB-1")
        self.assertEqual(len(result["operations"]), 2)
        self.assertEqual(result["operations"][0]["specification"], "SPEC-FRONT-1")
