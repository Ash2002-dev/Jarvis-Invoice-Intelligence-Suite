from typing import List, Dict

# Configuration for file paths
INPUT_FOLDER = "input_invoices"
OUTPUT_FOLDER = "output"
OUTPUT_FILENAME = "consolidated_invoices.xlsx"

# Mappings for variable terms
# This dictionary maps the standard field name we want in Excel to a list of possible keywords found in PDFs.
# Case insensitive matching will be used.
# Field Mappings: Text to Standard Keys
FIELD_MAPPINGS: Dict[str, List[str]] = {
    "summary_date": ["Summary Date"],
    "entry_date": ["Entry Date"],
    "import_date": ["Import Date"],
    "export_date": ["Export Date"],
    "country_of_origin": ["Country of Origin", "Origin"],
    "exporting_country": ["Exporting Country"],
    "duty": ["Duty"],
    "tax": ["Tax"],
    "other": ["Other"],
    "total": ["Total"],
    "total_entered_value": ["Total Entered Value"],
    "waybill_number": ["Bill of Lading", "WayBill Number", "Waybill"],
    "invoice_number": ["Invoice Number", "Exporter Number", "Invoice No", "Exporter No"],
}
