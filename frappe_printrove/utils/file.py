import io

import frappe
from PIL import Image

SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG"}


def ensure_supported_image_format(file_doc) -> str:
	"""Validates attached file format.

	If format is unsupported (e.g. WEBP, BMP, TIFF), converts it to PNG using Pillow,
	saves the converted file as a new File document attached to the same Item,
	and returns the URL of the valid PNG file.
	"""
	file_path = file_doc.get_full_path()
	with Image.open(file_path) as img:
		format_name = (img.format or "").upper()
		if format_name in SUPPORTED_FORMATS:
			return file_doc.file_url

		buffer = io.BytesIO()
		if img.mode in ("RGBA", "LA", "P"):
			img = img.convert("RGBA")
		else:
			img = img.convert("RGB")
		img.save(buffer, format="PNG")
		buffer.seek(0)

		file_basename = (
			file_doc.file_name.rsplit(".", 1)[0] if "." in file_doc.file_name else file_doc.file_name
		)
		converted_file_name = f"converted_{file_basename}.png"

		converted_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": converted_file_name,
				"attached_to_doctype": file_doc.attached_to_doctype,
				"attached_to_name": file_doc.attached_to_name,
				"content": buffer.getvalue(),
				"is_private": file_doc.is_private,
			}
		).insert(ignore_permissions=True)

		return converted_doc.file_url
