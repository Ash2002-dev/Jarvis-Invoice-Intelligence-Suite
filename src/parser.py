import re
from typing import Dict, Any, List, Optional
from loguru import logger

class InvoiceParser:
    """
    Advanced Parser for CBP 7501 (Entry Summary) forms.
    Uses windowed-regex picking for high precision on jumbled OCR streams.
    """

    def parse(self, input_data: Any) -> Dict[str, Any]:
        if isinstance(input_data, list):
            # Convert structured elements to a single text stream for windowed parsing
            # We sort by Y then X to keep rows together
            sorted_elements = sorted(input_data, key=lambda x: (x['page'], x['y'], x['x']))
            raw_text = " ".join([e['text'] for e in sorted_elements])
            return self._parse_with_logic(raw_text)
        else:
            return self._parse_with_logic(input_data)

    def _parse_with_logic(self, text: str) -> Dict[str, Any]:
        data = {}
        
        # 1. Countries (Box 10, 11/14) - Keeping refined block logic for "wrong" values
        data["Country of Origin"] = self._extract_by_block(text, r"10", r"\b([A-Z]{2}|MULTI)\b")
        exp_country = self._extract_by_block(text, r"14", r"\b([A-Z]{2}|MULTI)\b")
        if not exp_country:
             exp_country = self._extract_by_block(text, r"11", r"\b([A-Z]{2}|MULTI)\b")
        data["Exporting Country"] = exp_country
        
        # 2. Waybill (Box 12) - Reverted to Label Logic
        data["Waybill Number"] = self._extract_waybill(text)
        
        # 3. Dates (Box 3, 7, 11, 15) - Reverted to Label Logic
        data["Summary Date"] = self._extract_date(text, r"3\.?\s*Summary\s*Date")
        data["Entry Date"] = self._extract_date(text, r"7\.?\s*Entry\s*Date")
        data["Import Date"] = self._extract_date(text, r"11\.?\s*Import\s*Date")
        data["Export Date"] = self._extract_date(text, r"15\.?\s*Export\s*Date")
        
        # 4. Entered Value (Box 35) - Keeping refined logic for "wrong" values
        entered_val_raw = self._extract_by_block(text, r"35", r"(?:499\s+)?(?:\$?\s*)([\d,]{3,12})")
        if entered_val_raw:
            clean_val = entered_val_raw.replace(",", "").replace("$", "").strip()
            if clean_val == "499":
                entered_val_raw = self._extract_by_block(text, r"35", r"(?:499\s+).*?([\d,]{3,12})", window=120)
                if entered_val_raw:
                    clean_val = entered_val_raw.replace(",", "").replace("$", "").strip()
            data["Total Entered Value"] = clean_val
        else:
            data["Total Entered Value"] = ""
        
        # 5. Financials (Box 37-40) - Reverted to Label Logic
        data["Duty"] = self._extract_amount_near_label(text, r"37\.?\s*Duty", window=60)
        data["Tax"]  = self._extract_amount_near_label(text, r"38\.?\s*Tax", window=60)
        data["Other"] = self._extract_amount_near_label(text, r"39\.?\s*Other", window=60)
        data["Total"] = self._extract_amount_near_label(text, r"40\.?\s*Total", window=150)

        # 6. Global fields
        data["Invoice Number"] = self._find_invoice_number(text)
        
        return data

        # 6. Global fields
        data["Invoice Number"] = self._find_invoice_number(text)
        
        return data

    def _extract_by_block(self, text: str, block_no: str, value_pattern: str, window: int = 80) -> str:
        """
        New Anchor Logic: Finds a block number (like '10.') and looks for the 
        target pattern immediately following it within a small window.
        """
        # Look for the block number as a standalone digit (e.g. "10 " or "10.")
        anchor_pattern = rf"\b{block_no}\b[\.\s]{{1,5}}"
        matches = list(re.finditer(anchor_pattern, text))
        
        if not matches:
            return ""

        # Use the LAST occurrence of the block number (usually where the data is)
        # or the one that yields a match.
        for m in reversed(matches):
            start_pos = m.end()
            window_text = text[start_pos : start_pos + window]
            
            val_match = re.search(value_pattern, window_text)
            if val_match:
                return val_match.group(1).strip()
        
        return ""

    def _extract_amount_near_label(self, text: str, label_pattern: str, window: int = 100) -> str:
        """Fallback method for standard labels."""
        pattern = rf"{label_pattern}(.{{0,{window}}})"
        m = re.search(pattern, text, re.IGNORECASE)
        if not m: return ""
        window_text = m.group(1)
        numbers = re.findall(r"\d+\.\d{2}", window_text)
        return numbers[-1] if numbers else ""

    def _extract_country_code(self, text: str, label_pattern: str) -> str:
        """Fallback method for country code labels."""
        pattern = rf"{label_pattern}.{{0,100}}?\b([A-Z]{{2}})\b"
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1) if m else ""

    def _extract_waybill(self, text: str) -> str:
        """Standard AWB pattern."""
        m = re.search(r"\b\d{3}-\d{7,10}\b", text)
        return m.group(0) if m else ""

    def _extract_date(self, text: str, label_pattern: str) -> str:
        """Standard Date pattern search."""
        pattern = rf"{label_pattern}.{{0,40}}?(\d{{1,2}}[\/\.\-]\d{{1,2}}[\/\.\-]\d{{2,4}})"
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1) if m else ""

    def _find_invoice_number(self, text: str) -> str:
        patterns = [
            r"Invoice\s*(?:#|No|Number)[:\s]+([A-Z0-9\-]{5,})",
            r"Commercial\s*Invoice\s*(?:#|No)[:\s]+([A-Z0-9\-]{5,})",
            r"Exporter\s*No[:\s]+([A-Z0-9\-]{5,})"
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m: return m.group(1).strip()
        return ""
