import os
import glob
from tqdm import tqdm
from loguru import logger
from src.extractor import PDFExtractor
from src.parser import InvoiceParser
from src.exporter import ExcelExporter
from src.config import INPUT_FOLDER, OUTPUT_FOLDER, OUTPUT_FILENAME

def main():
    # Setup paths
    # Assuming the script is run from the root of the project or src parent
    # Adjust paths to be absolute or relative to CWD
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, INPUT_FOLDER)
    output_file = os.path.join(base_dir, OUTPUT_FOLDER, OUTPUT_FILENAME)

    logger.info(f"Starting Invoice Processing...")
    logger.info(f"Input Directory: {input_dir}")
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        logger.error(f"Input directory '{input_dir}' does not exist. Please create it and add PDF files.")
        return

    # Get all PDF files
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files.")

    if not pdf_files:
        logger.warning("No PDF files found to process.")
        return

    # Initialize components
    extractor = PDFExtractor()
    parser = InvoiceParser()
    exporter = ExcelExporter()

    extracted_data = []

    # Process files with a progress bar
    for i, pdf_path in enumerate(tqdm(pdf_files, desc="Processing Invoices"), start=1):
        filename = os.path.basename(pdf_path)
        logger.debug(f"Processing {filename}")
        
        # 1. Extract Text
        text = extractor.extract_text(pdf_path)
        if not text:
            logger.warning(f"Skipping {filename} - No text extracted (might be image-based PDF).")
            continue
            
        # 2. Parse Text
        invoice_data = parser.parse(text)
        
        # Add metadata
        invoice_data['id'] = i  # Simple sequential ID
        invoice_data['filename'] = filename
        
        extracted_data.append(invoice_data)

    # 3. Export to Excel
    exporter.export(extracted_data, output_file)
    logger.info("Processing complete.")

if __name__ == "__main__":
    main()
