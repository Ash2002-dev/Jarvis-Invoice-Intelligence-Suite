import os
import sys

# --- Performance Optimization: Set Environment Variables BEFORE heavy imports ---
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TORCH_NUM_THREADS"] = "1"
os.environ["PYTHONOPTIMIZE"] = "1"
# Prevents PyInstaller from bloating the init logs
os.environ["PYINSTALLER_STRICT_UNPACK_DELAY"] = "1" 

import glob
from typing import List, Dict, Any

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                               QTableWidget, QTableWidgetItem, QProgressBar, 
                               QHeaderView, QMessageBox, QTabWidget, QStyle, QFrame,
                               QLineEdit)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QIcon

# from src.extractor import PDFExtractor  # Moved to lazy loading in worker
# from src.parser import InvoiceParser     # Moved to lazy loading in worker
# from src.exporter import ExcelExporter   # Moved to lazy loading in worker
from src.config import OUTPUT_FILENAME

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Worker Thread for Processing ---
class ProcessingWorker(QThread):
    """
    Runs the heavy invoice processing in a background thread
    so the UI doesn't freeze.
    """
    progress_update = Signal(int, int) # current, total
    file_processed = Signal(dict)      # data of the processed file
    finished = Signal(str)             # output path
    error_occurred = Signal(str)

    def __init__(self, input_dir, output_dir):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.is_running = True

    def run(self):
        try:
            pdf_files = glob.glob(os.path.join(self.input_dir, "*.pdf"))
            total_files = len(pdf_files)
            
            if total_files == 0:
                self.error_occurred.emit("No PDF files found in the selected directory.")
                return

            # Lazy loading heavy modules inside the thread
            from src.extractor import PDFExtractor
            from src.parser import InvoiceParser
            from src.exporter import ExcelExporter

            extractor = PDFExtractor()
            parser = InvoiceParser()
            exporter = ExcelExporter()
            
            extracted_data = []
            
            for i, pdf_path in enumerate(pdf_files, start=1):
                if not self.is_running:
                    break
                
                filename = os.path.basename(pdf_path)
                
                try:
                    # Extract Structured Data (Spatial)
                    structured_data = extractor.extract_structured_data(pdf_path)
                    if structured_data:
                        # Parse
                        data = parser.parse(structured_data)
                        data['id'] = i
                        data['filename'] = filename
                        
                        extracted_data.append(data)
                        self.file_processed.emit(data)
                except Exception as file_error:
                    # Log error but continue
                    print(f"Error processing {filename}: {str(file_error)}")
                    # Optionally emit a specific error signal if you want to show a log in UI
                
                self.progress_update.emit(i, total_files)

            # Export
            if extracted_data:
                output_path = os.path.join(self.output_dir, OUTPUT_FILENAME)
                exporter.export(extracted_data, output_path)
                self.finished.emit(output_path)
            else:
                self.error_occurred.emit("No data was extracted from the files.")

        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self.is_running = False

# --- Main Application Window ---
class InvoiceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvis Invoice Intelligence")
        self.resize(1280, 850)
        
        # --- App Icon Configuration ---
        icon_path = resource_path("logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # --- Deep Space Professional Theme ---
        self.setStyleSheet("""
            /* Global Reset & Typography */
            QWidget {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 13px;
                color: #F8FAFC;
            }
            QMainWindow {
                background-color: #0B0F19; /* Deep Space Background */
            }
            
            /* Layered Card Containers */
            QFrame#HeaderFrame {
                background-color: #151B27;
                border-bottom: 1px solid #2A3241;
            }
            QFrame#ControlPanel {
                background-color: #151B27;
                border: 1px solid #2A3241;
                border-radius: 12px;
            }
            
            /* Typography Highlights */
            QLabel#LogoLabel {
                font-size: 28px;
                font-weight: 800;
                color: #FFFFFF;
                letter-spacing: -0.5px;
            }
            QLabel#TaglineLabel {
                color: #94A3B8; /* Slate Gray */
                font-size: 13px;
                font-weight: 500;
            }
            
            /* Modern Integrated Inputs */
            QLineEdit {
                background-color: #0F172A;
                border: 1px solid #334155;
                padding: 10px 15px;
                border-radius: 8px;
                color: #FFFFFF; /* Brighter typed text */
            }
            QLineEdit::placeholder {
                color: #FFFFFF; /* White placeholder */
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #0078FF;
                background-color: #151B27;
            }
            
            /* Professional Dashboard Buttons */
            QPushButton {
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid transparent;
            }
            
            /* Primary (Professional Blue) */
            QPushButton#BtnStart {
                background-color: #1D4ED8;
                color: white;
                border: 1px solid #3B82F6;
            }
            QPushButton#BtnStart:hover {
                background-color: #1E40AF;
                border-color: #60A5FA;
            }
            QPushButton#BtnStart:disabled {
                background-color: #1E293B;
                border-color: #334155;
                color: #64748B;
            }

            /* Success (Enterprise Green) */
            QPushButton#BtnExport {
                background-color: #059669;
                color: white;
                border: 1px solid #10B981;
            }
            QPushButton#BtnExport:hover {
                background-color: #065F46;
                border-color: #34D399;
            }
            QPushButton#BtnExport:disabled {
                background-color: #1E293B;
                border-color: #334155;
                color: #64748B;
            }

            /* Neutral (Gray/Outline) */
            QPushButton#BtnBrowse {
                background-color: transparent;
                border: 1px solid #334155;
                color: #CBD5E1;
            }
            QPushButton#BtnBrowse:hover {
                background-color: #1E293B;
                border-color: #0078FF;
                color: white;
            }

            /* Data Table - The "Ghost Grid" Look */
            QTableWidget {
                background-color: #151B27;
                border: 1px solid #2A3241;
                border-radius: 12px;
                gridline-color: #2A3241;
                outline: none;
                selection-background-color: rgba(0, 120, 255, 0.2);
                selection-color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #0F172A;
                color: #94A3B8;
                padding: 14px;
                border: none;
                border-bottom: 1px solid #2A3241;
                font-weight: 700;
                text-transform: uppercase;
                font-size: 11px;
                letter-spacing: 1.5px;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #1E293B;
            }
            QTableWidget::item:selected {
                border-left: 3px solid #0078FF;
                background-color: rgba(0, 120, 255, 0.1);
            }

            /* ScrollBars */
            QScrollBar:vertical {
                border: none;
                background: #0B0F19;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }

            /* StatusBar */
            QStatusBar {
                background-color: #0B0F19;
                color: #64748B;
                border-top: 1px solid #1E293B;
                padding-left: 10px;
            }

            /* Dialogs */
            QMessageBox {
                background-color: #151B27;
                border: 1px solid #334155;
            }
            QMessageBox QLabel { color: #F8FAFC; }
            QMessageBox QPushButton {
                background-color: #1E293B;
                border: 1px solid #334155;
                padding: 6px 20px;
                border-radius: 6px;
            }
        """)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- 1. Header Section (Top Bar) ---
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        # Logo/Title Area
        title_box = QVBoxLayout()
        title_label = QLabel("JARVIS")
        title_label.setObjectName("LogoLabel")
        subtitle_label = QLabel("Invoice Intelligence Suite • v1.0.0")
        subtitle_label.setObjectName("TaglineLabel")
        
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        
        # Add Header to Main
        main_layout.addWidget(header_frame)

        # --- Content Container ---
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # --- 2. Control Panel (Card) ---
        control_panel = QFrame()
        control_panel.setObjectName("ControlPanel")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setSpacing(15)
        control_layout.setContentsMargins(20, 20, 20, 20)

        # Browse Area
        self.btn_browse = QPushButton("Select Source Folder")
        self.btn_browse.setObjectName("BtnBrowse")
        self.btn_browse.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.btn_browse.clicked.connect(self.browse_folder)
        
        self.btn_reset = QPushButton("Clear Workspace")
        self.btn_reset.setObjectName("BtnBrowse") # Reuse neutral style
        self.btn_reset.setMinimumWidth(120)
        self.btn_reset.clicked.connect(self.reset_app)
        self.btn_reset.hide() # Hidden initially
        
        self.path_label = QLabel("No folder selected...")
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.path_label.setCursor(Qt.IBeamCursor)
        self.path_label.setStyleSheet("color: #64748B; font-style: italic;")
        
        control_layout.addWidget(self.btn_browse)
        control_layout.addWidget(self.btn_reset)
        control_layout.addWidget(self.path_label)
        control_layout.addStretch()
        
        # Action Buttons
        self.btn_start = QPushButton("Start Processing")
        self.btn_start.setObjectName("BtnStart")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_start.clicked.connect(self.start_processing)
        self.btn_start.setEnabled(False) 

        self.btn_stop = QPushButton("Stop & Export")
        self.btn_stop.setObjectName("BtnExport") # Reddish warning style
        self.btn_stop.setStyleSheet("background-color: #EF4444; border: none;") # Override with Red
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.hide() 

        self.btn_export = QPushButton("Export Results")
        self.btn_export.setObjectName("BtnExport")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.btn_export.clicked.connect(self.export_data)
        self.btn_export.setEnabled(False)

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_export)

        content_layout.addWidget(control_panel)

        # --- Search Bar Section ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search invoices (e.g. vendor name, ID, amount)...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setMinimumWidth(400)
        self.search_input.setEnabled(False) # Enable only after processing
        
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        content_layout.addLayout(search_layout)

        # --- 3. Statistics Dashboard (Modern Card Style) ---
        stats_frame = QFrame()
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(15)
        
        def create_stat_card(label_text, color):
            card = QFrame()
            card.setMinimumWidth(140)
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #151B27;
                    border: 1px solid #2A3241;
                    border-radius: 8px;
                    padding: 8px 12px;
                }}
                QFrame:hover {{
                    border-color: {color};
                    background-color: #1E293B;
                }}
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(0)
            
            # Value Label (The number)
            value_lbl = QLabel("0")
            value_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color}; background: transparent; border: none;")
            
            # Subtitle Label
            sub_lbl = QLabel(label_text.upper())
            sub_lbl.setStyleSheet("font-size: 9px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px; background: transparent; border: none;")
            
            card_layout.addWidget(value_lbl)
            card_layout.addWidget(sub_lbl)
            return card, value_lbl

        # Create Cards
        card_total, self.lbl_total_val = create_stat_card("Total PDFs", "#FFFFFF")
        card_proc, self.lbl_proc_val = create_stat_card("Processed", "#10B981")
        card_rem, self.lbl_rem_val = create_stat_card("Remaining", "#3B82F6")
        
        stats_layout.addWidget(card_total)
        stats_layout.addWidget(card_proc)
        stats_layout.addWidget(card_rem)
        stats_layout.addStretch()
        
        content_layout.addWidget(stats_frame)

        # --- 4. Data View Section ---
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Invoice No", "Date", "Total", "Filename"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False) # Clean modern look
        self.table.setAlternatingRowColors(False) # Handle via item CSS
        self.table.setFrameShape(QFrame.NoFrame)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        content_layout.addWidget(self.table)
        
        # Progress Bar (Slim, at bottom of content)
        # Add Content to Main
        main_layout.addLayout(content_layout)

        # --- 4. Status Bar ---
        self.status_label = QLabel(" System Ready")
        self.statusBar().addWidget(self.status_label)

        # Internal State
        self.input_folder = None
        self.worker = None
        # Internal State - Ensure all demanded columns are here by default
        self.all_columns = [
            "id", "filename", "Invoice Number", "Waybill Number", 
            "Summary Date", "Entry Date", "Import Date", "Export Date", 
            "Country of Origin", "Exporting Country", 
            "Duty", "Tax", "Other", "Total", "Total Entered Value"
        ]
        self.all_data = [] 

        # Initialize Table Headers
        self.table.setColumnCount(len(self.all_columns))
        headers = [c.replace("_", " ").title() for c in self.all_columns]
        self.table.setHorizontalHeaderLabels(headers)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Invoice Folder")
        if folder:
            self.input_folder = folder
            self.path_label.setText(folder)
            self.path_label.setStyleSheet("color: #F8FAFC; font-weight: 600;")
            
            # Count Files Immediately
            pdf_files = glob.glob(os.path.join(folder, "*.pdf"))
            total = len(pdf_files)
            
            self.lbl_total_val.setText(str(total))
            self.lbl_proc_val.setText("0")
            self.lbl_rem_val.setText(str(total))
            
            self.btn_start.setEnabled(True if total > 0 else False)
            self.status_label.setText(f" Found {total} PDF files in directory")
            self.btn_browse.setText("Change Source Folder")
            self.btn_reset.show()

    def reset_app(self):
        self.input_folder = None
        self.path_label.setText("No folder selected...")
        self.path_label.setStyleSheet("color: #64748B; font-style: italic;")
        self.btn_browse.setText("Select Source Folder")
        self.btn_start.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.btn_reset.hide()
        
        # Reset Stats
        self.lbl_total_val.setText("0")
        self.lbl_proc_val.setText("0")
        self.lbl_rem_val.setText("0")
        
        # Clear Data
        self.table.setRowCount(0)
        self.all_data = [] 
        self.table.setColumnCount(len(self.all_columns))
        headers = [c.replace("_", " ").title() for c in self.all_columns]
        self.table.setHorizontalHeaderLabels(headers)
        
        self.status_label.setText(" System Ready")

    def start_processing(self):
        if not self.input_folder:
            return

        # Reset UI
        self.table.setRowCount(0)
        self.table.setColumnCount(len(self.all_columns))
        headers = [c.replace("_", " ").title() for c in self.all_columns]
        self.table.setHorizontalHeaderLabels(headers)
        self.all_data = [] 
        self.btn_start.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.search_input.setEnabled(False)
        self.search_input.clear()
        
        # Get total files again to ensure accuracy
        pdf_files = glob.glob(os.path.join(self.input_folder, "*.pdf"))
        total = len(pdf_files)
        self.lbl_total_val.setText(str(total))
        self.lbl_proc_val.setText("0")
        self.lbl_rem_val.setText(str(total))
        
        self.status_label.setText(" Processing...")
        self.btn_stop.show()
        self.btn_start.hide()

        # Start Worker
        output_dir = os.path.join(self.input_folder, "output")
        self.worker = ProcessingWorker(self.input_folder, output_dir)
        
        self.worker.progress_update.connect(self.update_progress)
        self.worker.file_processed.connect(self.add_table_row)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error_occurred.connect(self.processing_error)
        
        self.worker.start()

    @Slot(int, int)
    def update_progress(self, current, total):
        self.status_label.setText(f" Status: Processing {current} of {total} total files...")
        
        # Update Dashboard Values
        self.lbl_proc_val.setText(str(current))
        self.lbl_rem_val.setText(str(total - current))

    @Slot(dict)
    def add_table_row(self, data):
        # --- 1. Duplicate Invoices Check (Exact Content) ---
        # Strip metadata to compare pure invoice data
        new_record_clean = {k: v for k, v in data.items() if k not in ['id', 'filename']}
        
        for existing in self.all_data:
            existing_clean = {k: v for k, v in existing.items() if k not in ['id', 'filename']}
            if new_record_clean == existing_clean:
                # Exact duplicate found, skip adding to results
                current_status = self.status_label.text()
                if "Duplicates detected" not in current_status:
                    self.status_label.setText(current_status + " (Duplicates detected & grouped)")
                return

        # --- 2. Store and Display Unique Data ---
        self.all_data.append(data)

        # 1. Update Columns if new keys found
        new_keys = [k for k in data.keys() if k not in self.all_columns]
        if new_keys:
            self.all_columns.extend(new_keys)
            self.table.setColumnCount(len(self.all_columns))
            # Nicer headers
            headers = [c.replace("_", " ").title() for c in self.all_columns]
            self.table.setHorizontalHeaderLabels(headers)
        
        # 2. Add Row
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        for col_idx, key in enumerate(self.all_columns):
            val = str(data.get(key, ""))
            self.table.setItem(row_idx, col_idx, QTableWidgetItem(val))
            
        self.table.scrollToBottom()

    @Slot(str)
    def processing_finished(self, output_path):
        self.status_label.setText(" Analysis Complete")
        self.btn_start.show()
        self.btn_start.setEnabled(True)
        self.btn_stop.hide()
        self.btn_browse.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.search_input.setEnabled(True)
        
        # Determine if it was a partial export
        msg = f"Processing Complete!\n\nAccess your files at:\n{output_path}"
        if self.worker and not self.worker.is_running:
             msg = f"Processing Stopped by User.\n\nPartial results exported to:\n{output_path}"
             
        QMessageBox.information(self, "Success", msg)

    def stop_processing(self):
        if self.worker:
            self.status_label.setText(" Stopping and Exporting current progress...")
            self.btn_stop.setEnabled(False)
            self.worker.stop()

    @Slot(str)
    def processing_error(self, error_msg):
        self.status_label.setText(" Error")
        self.btn_start.show()
        self.btn_start.setEnabled(True)
        self.btn_stop.hide()
        self.btn_browse.setEnabled(True)
        
        # Friendly message for permission errors (file open)
        if "Permission denied" in error_msg or "PermissionError" in error_msg:
            friendly_msg = ("The output Excel file is currently open in another program.\n\n"
                            "Please close it and click 'Start Processing' again.")
            QMessageBox.warning(self, "File Access Error", friendly_msg)
        else:
            QMessageBox.critical(self, "System Error", error_msg)

    def export_data(self):
        if not self.all_data:
            QMessageBox.warning(self, "No Data", "No data to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")
        if file_path:
            try:
                # Lazy loading to keep main thread fast at startup
                from src.exporter import ExcelExporter
                exporter = ExcelExporter()
                exporter.export(self.all_data, file_path)
                QMessageBox.information(self, "Success", f"Successfully exported data to:\n{file_path}")
            except PermissionError:
                QMessageBox.warning(self, "Export Failed", 
                                    f"The file '{os.path.basename(file_path)}' is currently open in another program (like Excel).\n\n"
                                    "Please close the file and try exporting again.")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"An unexpected error occurred:\n{str(e)}")

    def filter_table(self):
        query = self.search_input.text().lower().strip()
        
        for row in range(self.table.rowCount()):
            match = False
            # Check every column in this row for a match
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            
            # Show or hide row based on match
            self.table.setRowHidden(row, not match)
        
        # Update status bar with filter results
        visible_rows = sum(1 for r in range(self.table.rowCount()) if not self.table.isRowHidden(r))
        if query:
            self.status_label.setText(f" Filtered: Showing {visible_rows} of {self.table.rowCount()} invoices")
        else:
            self.status_label.setText(" Analysis Complete")

if __name__ == "__main__":
    # --- Windows Taskbar Icon Fix ---
    if sys.platform == 'win32':
        import ctypes
        myappid = 'antigravity.jarvis.invoice.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    
    # Set global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = InvoiceApp()
    window.show()
    
    sys.exit(app.exec())
