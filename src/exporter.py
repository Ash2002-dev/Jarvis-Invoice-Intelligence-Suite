import pandas as pd
from typing import List, Dict
from loguru import logger
import os

class ExcelExporter:
    """
    Handles exporting processed data to Excel.
    """
    
    def export(self, data: List[Dict], output_path: str):
        """
        Converts a list of dictionaries to a DataFrame and saves as Esxcel.
        """
        if not data:
            logger.warning("No data to export.")
            return

        try:
            df = pd.DataFrame(data)
            
            # Define preferred column order
            preferred_order = [
                'id', 'filename', 'Invoice Number', 'Waybill Number', 
                'Summary Date', 'Entry Date', 'Import Date', 'Export Date', 
                'Country of Origin', 'Exporting Country', 
                'Duty', 'Tax', 'Other', 'Total', 'Total Entered Value'
            ]
            
            # Filter and order columns
            existing_cols = [c for c in preferred_order if c in df.columns]
            other_cols = [c for c in df.columns if c not in preferred_order]
            
            df = df[existing_cols + other_cols]
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            df.to_excel(output_path, index=False)
            logger.info(f"Successfully exported {len(data)} records to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export data to Excel: {e}")
            raise e
