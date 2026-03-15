import pandas as pd
import os
import pdfplumber

class IngestionAgent:
    def __init__(self):
        self.unified_columns = ['Date', 'Description', 'Amount', 'Owner', 'Source']
    
    def _read_pdf(self, file_path):
        """
        Extract tables from PDF file using pdfplumber.
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                all_tables = []
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"  Extracting from PDF page {page_num}...")
                    
                    # Try default table extraction
                    tables = page.extract_tables()
                    
                    # If no tables found, try with different settings
                    if not tables or len(tables) == 0:
                        print(f"    No tables with default settings, trying alternative extraction...")
                        tables = page.extract_tables(table_settings={
                            "vertical_strategy": "lines",
                            "horizontal_strategy": "lines",
                            "explicit_vertical_lines": [],
                            "explicit_horizontal_lines": [],
                            "snap_tolerance": 3,
                            "join_tolerance": 3,
                            "edge_min_length": 3,
                            "min_words_vertical": 3,
                            "min_words_horizontal": 1,
                        })
                    
                    # If still no tables, try extracting as text and looking for patterns
                    if not tables or len(tables) == 0:
                        print(f"    No tables found, trying text extraction...")
                        text = page.extract_text()
                        if text:
                            print(f"    Found {len(text)} characters of text")
                            print(f"    Sample text: {text[:200]}")
                            # You might need OCR for image-based PDFs
                            raise ValueError(f"PDF appears to be text-based but no tables detected. It may be a scanned image or have non-standard formatting.")
                    
                    if tables:
                        for table in tables:
                            if table and len(table) > 1:  # Need at least header + 1 row
                                # Convert table to DataFrame
                                df = pd.DataFrame(table[1:], columns=table[0])
                                print(f"    Extracted table with {len(df)} rows and columns: {df.columns.tolist()}")
                                all_tables.append(df)
                
                if all_tables:
                    # Combine all tables
                    df = pd.concat(all_tables, ignore_index=True)
                    print(f"✓ Successfully extracted {len(df)} rows from PDF: {os.path.basename(file_path)}")
                    print(f"  PDF columns found: {df.columns.tolist()}")
                    return df
                else:
                    raise ValueError(f"No tables found in PDF: {file_path}. The PDF might be a scanned image or have unsupported formatting.")
        except Exception as e:
            raise ValueError(f"Error reading PDF file {file_path}: {e}")
    
    def _read_file(self, file_path, skiprows=0):
        """
        Read CSV, Excel, or PDF file with proper encoding handling.
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Handle PDF files
        if file_ext == '.pdf':
            return self._read_pdf(file_path)
        
        # Handle Excel files
        if file_ext in ['.xlsx', '.xls']:
            try:
                # Read Excel WITHOUT date parsing, keep everything as-is
                df = pd.read_excel(file_path, skiprows=skiprows, date_format=None, parse_dates=False)
                print(f"Successfully read Excel file: {os.path.basename(file_path)}")
                return df
            except Exception as e:
                raise ValueError(f"Error reading Excel file {file_path}: {e}")
        
        # Handle CSV files with encoding detection
        encodings = ['windows-1255', 'cp1255', 'utf-8', 'iso-8859-8', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    file_path, 
                    skiprows=skiprows, 
                    encoding=encoding,
                    on_bad_lines='skip',
                    engine='python'
                )
                print(f"Successfully read CSV {os.path.basename(file_path)} with {encoding} encoding")
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                if 'codec' not in str(e).lower() and 'decode' not in str(e).lower():
                    continue
        
        # Fallback to latin1
        print(f"Warning: Using latin1 fallback encoding for {os.path.basename(file_path)}")
        return pd.read_csv(
            file_path, 
            skiprows=skiprows, 
            encoding='latin1',
            on_bad_lines='skip',
            engine='python'
        )

    def parse_max(self, file_path, owner):
        # Try different skiprows to find the header
        for skip in [0, 3, 4, 5, 6]:
            try:
                df = self._read_file(file_path, skiprows=skip)
                if df is not None and len(df) > 0:
                    print(f"Max file with skiprows={skip}, columns: {df.columns.tolist()}")
                    
                    # Try to find the right columns (Hebrew names can vary)
                    column_mapping = {}
                    for col in df.columns:
                        col_str = str(col)
                        col_lower = col_str.lower()
                        if any(x in col_str for x in ['תאריך', 'תא ר', 'date', 'Date']):
                            if 'Date' not in column_mapping.values():
                                column_mapping[col] = 'Date'
                        elif any(x in col_str for x in ['בית עסק', 'שם', 'עסק', 'תיאור', 'description']):
                            if 'Description' not in column_mapping.values():
                                column_mapping[col] = 'Description'
                        elif any(x in col_str for x in ['סכום', 'חיוב', 'amount']):
                            if 'Amount' not in column_mapping.values():
                                column_mapping[col] = 'Amount'
                    
                    if len(column_mapping) == 3 and all(x in column_mapping.values() for x in ['Date', 'Description', 'Amount']):
                        print(f"✓ Successfully mapped Max columns: {column_mapping}")
                        df = df.rename(columns=column_mapping)
                        df['Owner'], df['Source'] = owner, 'Max'
                        return df[self.unified_columns]
            except Exception as e:
                print(f"Failed with skiprows={skip}: {e}")
                continue
        
        raise ValueError(f"Could not parse Max file. Could not find required columns.")

    def parse_isracard_csv(self, file_path, owner):
        # Detect if it's a PDF or CSV/Excel and adjust skiprows
        file_ext = os.path.splitext(file_path)[1].lower()
        
        skip_options = [0] if file_ext == '.pdf' else [0, 5, 7, 10, 12, 15]
        
        for skip in skip_options:
            try:
                df = self._read_file(file_path, skiprows=skip)
                if df is not None and len(df) > 0:
                    print(f"Isracard file with skiprows={skip}, columns: {df.columns.tolist()}")
                    
                    # SPECIAL CASE: Isracard files with no header - first row IS the data!
                    # Check if column names look like data (dates like "08.02.26" or numbers)
                    first_col = str(df.columns[0])
                    if '.' in first_col and len(first_col.split('.')) == 3:  # Looks like DD.MM.YY date
                        print(f"  → Detected headerless Isracard file! Re-reading with header=None...")
                        # Re-read the file with header=None so ALL rows are data (including the first)
                        if file_ext in ['.xlsx', '.xls']:
                            df = pd.read_excel(file_path, skiprows=skip, header=None, dtype=str)
                        else:
                            df = pd.read_csv(file_path, skiprows=skip, header=None, dtype=str,
                                           encoding='utf-8', on_bad_lines='skip', engine='python')
                        
                        df.columns = [f'col_{i}' for i in range(len(df.columns))]
                        print(f"  → Re-read {len(df)} rows. Columns: {df.columns.tolist()}")
                        print(f"  → First 3 rows:\n{df.head(3).to_string()}")
                        
                        # Positional mapping: col_0=Date, col_1=Description, col_4=Charge Amount (NOT col_2!)
                        # col_2 is the FULL transaction amount, col_4 is the actual monthly charge
                        # (important for installment purchases like "תשלום 1 מתוך 2")
                        column_mapping = {'col_0': 'Date', 'col_1': 'Description', 'col_4': 'Amount'}
                        print(f"  → Using positional mapping (charge amount): {column_mapping}")
                    else:
                        # Normal case: Try to find the right columns by name
                        column_mapping = {}
                        for col in df.columns:
                            col_str = str(col)
                            col_lower = col_str.lower()
                            if any(x in col_str for x in ['תאריך', 'תא ר', 'date', 'Date']):
                                if 'Date' not in column_mapping.values():
                                    column_mapping[col] = 'Date'
                            elif any(x in col_str for x in ['בית עסק', 'שם', 'עסק', 'תיאור', 'description']):
                                if 'Description' not in column_mapping.values():
                                    column_mapping[col] = 'Description'
                            elif any(x in col_str for x in ['סכום', 'חיוב', 'amount']):
                                if 'Amount' not in column_mapping.values():
                                    column_mapping[col] = 'Amount'
                    
                    if len(column_mapping) == 3 and all(x in column_mapping.values() for x in ['Date', 'Description', 'Amount']):
                        print(f"✓ Successfully mapped Isracard columns: {column_mapping}")
                        df = df.rename(columns=column_mapping)
                        
                        # CRITICAL: Clean commas from amounts before converting (prevents NaN)
                        print(f"  Cleaning amounts... Sample before: {df['Amount'].head(3).tolist()}")
                        df['Amount'] = df['Amount'].astype(str).str.replace(',', '').str.replace('₪', '').str.strip()
                        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
                        print(f"  Sample after: {df['Amount'].head(3).tolist()}")
                        
                        # Filter out summary/footer rows:
                        # - Remove rows where Date is NaN (summary rows like "סה"כ")
                        # - Remove rows where Amount is NaN or 0
                        before_count = len(df)
                        df = df.dropna(subset=['Amount', 'Date'])
                        # Remove rows where charge amount is 0 (not charged this month)
                        df = df[df['Amount'] != 0]
                        # Also remove rows where Description contains summary text
                        df = df[~df['Description'].astype(str).str.contains('סה"כ|תנאים משפטיים', na=True)]
                        after_count = len(df)
                        if before_count != after_count:
                            print(f"  ⚠️ Dropped {before_count - after_count} summary/footer rows")
                        
                        print(f"  ✓ Successfully parsed {len(df)} Isracard transactions")
                        df['Owner'], df['Source'] = owner, 'Isracard'
                        return df[self.unified_columns]
            except Exception as e:
                print(f"Failed with skiprows={skip}: {e}")
                continue
        
        raise ValueError(f"Could not parse Isracard file. Could not find required columns.")

    def parse_bank_discount(self, file_path):
        # Try different skiprows to find the header
        for skip in [0, 3, 5, 7, 8, 10]:
            try:
                df = self._read_file(file_path, skiprows=skip)
                if df is not None and len(df) > 0:
                    print(f"Bank file with skiprows={skip}, columns: {df.columns.tolist()}")
                    print(f"First row sample: {df.head(1).to_dict('records') if len(df) > 0 else 'empty'}")
                    
                    # Special case: If first column is already a datetime, it means the header row is missing
                    # and the first row is data. We need to assign column names manually.
                    if skip == 0 and len(df.columns) >= 3:
                        first_col_type = type(df.columns[0]).__name__
                        # Check if columns are datetime or if first data row contains dates
                        if 'datetime' in first_col_type.lower():
                            print("  → Detected headerless bank file with datetime columns, assigning column names...")
                            # The columns ARE the first row of data, reset them
                            new_df = pd.read_excel(file_path, skiprows=skip, header=None, dtype=str)
                            new_df.columns = [f'col_{i}' for i in range(len(new_df.columns))]
                            df = new_df
                        
                        # Try to identify columns by their data types and content
                        date_col = None
                        desc_col = None
                        amount_col = None
                        
                        for i, col in enumerate(df.columns):
                            sample = df[col].dropna().head(5)
                            if len(sample) > 0:
                                # Check if it's a date column (column 0 or contains dates)
                                if i == 0:
                                    date_col = col
                                # Check if it's a description (string with Hebrew or long text)
                                elif sample.dtype == 'object' and any(isinstance(v, str) and len(str(v)) > 3 for v in sample):
                                    if desc_col is None and i >= 2:  # Description usually in column 2 or 3
                                        desc_col = col
                                # Check if it's an amount column (numeric, negative values)
                                elif i >= 3:  # Amount columns are usually after date and description
                                    try:
                                        numeric_sample = pd.to_numeric(sample, errors='coerce')
                                        if numeric_sample.notna().any() and amount_col is None:
                                            if any(numeric_sample < 0):  # Expenses are negative
                                                amount_col = col
                                    except:
                                        pass
                            
                            if date_col and desc_col and amount_col:
                                df = df.rename(columns={date_col: 'Date', desc_col: 'Description', amount_col: 'Amount'})
                                # Make amounts positive (expenses are negative in bank files)
                                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').abs()
                                print(f"✓ Successfully mapped headerless bank columns")
                                
                                # Filter bank to only keep bank-exclusive transactions
                                exclude_patterns = [
                                    'מקס איט פי', 'ישראכרט חיוב', 'חיוב לכרטיס', 'כרטיס ממקס', 'כרטיס ויזה',
                                    'בנק פועלים משכורת', 'משכורת', 'העברה מ', 'העברה ל', 'תשלום שוברי'
                                ]
                                exclude_mask = df['Description'].astype(str).apply(lambda x: any(p in x for p in exclude_patterns))
                                if exclude_mask.sum() > 0:
                                    print(f"  ⚠️ Filtering out {exclude_mask.sum()} entries (CC payments, salaries, transfers)")
                                    df = df[~exclude_mask]
                                
                                df['Owner'], df['Source'] = 'Joint', 'Bank_Discount'
                                return df[self.unified_columns]
                    
                    # Normal case: Look for Hebrew column names
                    column_mapping = {}
                    mapped_targets = set()
                    
                    for col in df.columns:
                        col_str = str(col)
                        col_lower = col_str.lower()
                        
                        # Map Date (only once) - expanded patterns
                        if 'Date' not in mapped_targets:
                            if any(x in col_str for x in ['תאריך', 'תא ר', 'Date', 'date', 'DATE']):
                                column_mapping[col] = 'Date'
                                mapped_targets.add('Date')
                        # Map Description (only once) - expanded patterns
                        if 'Description' not in mapped_targets:
                            if any(x in col_str for x in ['בית עסק', 'עסק', 'תיאור', 'פירוט', 'description', 'Description']):
                                column_mapping[col] = 'Description'
                                mapped_targets.add('Description')
                        # Map Amount (only once) - expanded patterns
                        if 'Amount' not in mapped_targets:
                            if any(x in col_str for x in ['סכום', 'זכות', 'חובה', 'amount', 'Amount']):
                                column_mapping[col] = 'Amount'
                                mapped_targets.add('Amount')
                    
                    # Check if we found all required columns
                    if all(col in mapped_targets for col in ['Date', 'Description', 'Amount']):
                        print(f"✓ Successfully mapped columns: {column_mapping}")
                        df = df.rename(columns=column_mapping)
                        
                        # CRITICAL: Filter bank file to only keep BANK-EXCLUSIVE transactions
                        # The bank file is a summary that includes CC payments, salaries, and transfers
                        # that are already captured by other sources (CC files, manual income entry).
                        # We only keep transactions that are UNIQUE to the bank file.
                        
                        exclude_patterns = [
                            # CC aggregate payments (already itemized in credit card files)
                            'מקס איט פי',          # Max credit card payment
                            'ישראכרט חיוב',         # Isracard payment
                            'חיוב לכרטיס',          # Generic CC payment ("חיוב לכרטיס ויזה 8428")
                            'כרטיס ממקס',           # Max card payment
                            'כרטיס ויזה',           # Visa card payment
                            # Salaries (user enters manually to avoid bank date confusion)
                            'בנק פועלים משכורת',    # Bank salary deposit
                            'משכורת',               # Any salary
                            # Internal transfers (not real income or expense)
                            'העברה מ',              # Transfer FROM (incoming)
                            'העברה ל',              # Transfer TO (outgoing)
                            'תשלום שוברי',          # Payment vouchers (internal)
                        ]
                        
                        before_count = len(df)
                        exclude_mask = df['Description'].astype(str).apply(
                            lambda x: any(p in x for p in exclude_patterns)
                        )
                        excluded_count = exclude_mask.sum()
                        if excluded_count > 0:
                            excluded_descs = df[exclude_mask]['Description'].tolist()
                            print(f"  ⚠️ Filtering out {excluded_count} bank entries (CC payments, salaries, transfers):")
                            for desc in excluded_descs[:10]:  # Show first 10
                                print(f"      - {desc}")
                            df = df[~exclude_mask]
                        
                        print(f"  ✓ Keeping {len(df)} bank-exclusive transactions (mortgage, education, standing orders, gov benefits, investments, ATM)")
                        
                        df['Owner'], df['Source'] = 'Joint', 'Bank_Discount'
                        return df[self.unified_columns]
            except Exception as e:
                print(f"Failed with skiprows={skip}: {e}")
                continue
        
        # If we get here, couldn't parse the file
        raise ValueError(f"Could not parse Bank file. Tried multiple skiprows values but couldn't find Date, Description, and Amount columns.")

    def parse_discount_credit_card(self, file_path, owner):
        """
        Parse Discount credit card CSV files (e.g., card ending in 4288).
        Header is typically at row 9 (skiprows=8).
        """
        for skip in [7, 8, 9, 10]:
            try:
                df = self._read_file(file_path, skiprows=skip)
                if df is not None and len(df) > 0:
                    print(f"Discount Credit Card with skiprows={skip}, columns: {df.columns.tolist()}")
                    
                    # Try to find the right columns
                    column_mapping = {}
                    for col in df.columns:
                        col_str = str(col)
                        col_lower = col_str.lower()
                        if any(x in col_str for x in ['תאריך עסקה', 'תאריך', 'date']):
                            if 'Date' not in column_mapping.values():
                                column_mapping[col] = 'Date'
                        elif any(x in col_str for x in ['בית עסק', 'עסק', 'שם בית עסק', 'description']):
                            if 'Description' not in column_mapping.values():
                                column_mapping[col] = 'Description'
                        elif 'סכום החיוב' in col_str:
                            # Prefer charge amount over full transaction amount (for installments)
                            column_mapping[col] = 'Amount'
                        elif any(x in col_str for x in ['סכום העסקה', 'סכום עסקה', 'סכום', 'amount']):
                            if 'Amount' not in column_mapping.values():
                                column_mapping[col] = 'Amount'
                    
                    if len(column_mapping) == 3 and all(x in column_mapping.values() for x in ['Date', 'Description', 'Amount']):
                        print(f"✓ Successfully mapped Discount Credit Card columns: {column_mapping}")
                        df = df.rename(columns=column_mapping)
                        df = df[['Date', 'Description', 'Amount']].dropna()
                        df['Owner'], df['Source'] = owner, 'Discount_Credit_Card'
                        return df[self.unified_columns]
            except Exception as e:
                print(f"Failed with skiprows={skip}: {e}")
                continue
        
        raise ValueError(f"Could not parse Discount Credit Card file. Could not find required columns.")

    def run_monthly_ingestion(self, files_list):
        """
        Orchestrator method to process multiple files and return unified DataFrame.
        
        Args:
            files_list: List of file paths to process
            
        Returns:
            Unified pandas DataFrame with all transactions
        """
        all_data = []
        
        for file in files_list:
            file_lower = file.lower()
            file_basename = os.path.basename(file_lower)
            print(f"Processing file: {file}")
            
            # Enhanced file type detection with Hebrew support and card numbers
            
            # 1. Max credit card detection (רעות מקס)
            if "max" in file_lower or "מקס" in file_lower:
                owner = "Reut" if "רעות" in file_lower else "Tal"
                print(f"  → Identified as Max credit card (Owner: {owner})")
                try:
                    all_data.append(self.parse_max(file, owner))
                except Exception as e:
                    print(f"  ✗ Failed to parse Max file: {e}")
            
            # 2. Isracard detection (3172 for Tal)
            elif "isracard" in file_lower or "ישראכרט" in file_lower or "ישראכארט" in file_lower or "3172" in file_basename:
                owner = "Tal" if "3172" in file_basename or "טל" in file_lower else "Reut"
                print(f"  → Identified as Isracard (Owner: {owner})")
                try:
                    parsed_data = self.parse_isracard_csv(file, owner)
                    if parsed_data is not None and len(parsed_data) > 0:
                        all_data.append(parsed_data)
                        print(f"  ✓ Successfully added {len(parsed_data)} Isracard transactions")
                    else:
                        print(f"  ⚠️ Isracard parser returned empty data")
                except Exception as e:
                    print(f"  ✗ Failed to parse Isracard file: {e}")
                    import traceback
                    print(f"  Full error: {traceback.format_exc()}")
            
            # 3. Discount credit card detection (4288 for Tal)
            elif "4288" in file_basename:
                print(f"  → Identified as Discount Credit Card 4288 (Owner: Tal)")
                try:
                    all_data.append(self.parse_discount_credit_card(file, "Tal"))
                except Exception as e:
                    print(f"  ✗ Failed to parse Discount Credit Card: {e}")
            
            # 4. Bank checking account (עובר ושב)
            elif "דיסקונט" in file_lower or "discount" in file_lower or "עובר ושב" in file_lower or "עו\"ש" in file_lower or "bank" in file_lower:
                print("  → Identified as Discount bank/checking account")
                try:
                    all_data.append(self.parse_bank_discount(file))
                except Exception as e:
                    print(f"  ✗ Failed to parse bank file: {e}")
            
            # 5. Generic credit card detection (אשראי keyword)
            elif "אשראי" in file_lower or "credit" in file_lower:
                owner = "Tal" if "טל" in file_lower else "Reut" if "רעות" in file_lower else "Tal"
                print(f"  → Identified as Credit card (Owner: {owner}, trying Isracard parser)")
                try:
                    all_data.append(self.parse_isracard_csv(file, owner))
                except Exception as e:
                    print(f"  ✗ Failed to parse credit card file: {e}")
            
            # 6. PDF warning
            elif file_lower.endswith('.pdf'):
                print(f"  ⚠️ PDF file detected. Attempting extraction...")
                print(f"  💡 Tip: For better results, export as CSV/Excel from your bank's website")
                try:
                    # Try to parse PDF anyway
                    all_data.append(self.parse_isracard_csv(file, "Tal"))
                except Exception as e:
                    print(f"  ✗ PDF parsing failed: {e}")
                    print(f"  → Skipping this file. Please convert to Excel/CSV format.")
            
            # 7. Unknown file type - try auto-detection
            else:
                print(f"  ⚠️ Unknown file type: {file}")
                print(f"     Attempting auto-detection based on file structure...")
                try:
                    df_test = self._read_file(file, skiprows=0)
                    if df_test is not None and len(df_test) > 0:
                        # Try Isracard parser (most flexible)
                        all_data.append(self.parse_isracard_csv(file, "Tal"))
                        print(f"  ✓ Successfully parsed with Isracard parser")
                    else:
                        print(f"  ✗ Failed to parse file")
                except Exception as e:
                    print(f"  ✗ Auto-detection failed: {e}")
        
        if not all_data:
            return pd.DataFrame(columns=self.unified_columns)
        
        df = pd.concat(all_data).reset_index(drop=True)
        
        # Clean and convert Amount column to numeric
        df['Amount'] = df['Amount'].astype(str).str.replace(',', '').str.replace('₪', '').str.strip()
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        
        # Drop rows where Amount is NaN (invalid amounts)
        df = df.dropna(subset=['Amount'])
        
        # Clean and standardize Date column
        # Handle various date formats (DD/MM/YYYY, DD.MM.YYYY, YYYY-MM-DD, etc.)
        print(f"\n📅 Sample RAW dates from files (before parsing):")
        print(df['Date'].head(10).tolist())
        print(f"Date column dtype: {df['Date'].dtype}")
        
        # Try multiple date parsing strategies
        def parse_israeli_date(date_val):
            """Try multiple Israeli date formats - DD/MM/YYYY (day first!)"""
            if pd.isna(date_val):
                return None
            
            # If it's already a datetime object from Excel (handles both pd.Timestamp AND Python datetime)
            import datetime as dt_module
            if isinstance(date_val, (pd.Timestamp, dt_module.datetime)):
                # Keep it as-is (Excel dates are usually correct)
                return pd.Timestamp(date_val)
            
            date_str = str(date_val).strip()
            
            # Skip invalid values
            if 'nan' in date_str.lower() or 'none' in date_str.lower() or date_str == '':
                return None
            
            # Common Israeli formats to try (DD/MM/YYYY - day first!)
            formats = [
                '%d.%m.%y',     # 10.03.26 = March 10, 2026 (Isracard format!)
                '%d/%m/%Y',     # 10/03/2026 = March 10, 2026
                '%d/%m/%y',     # 10/03/26 = March 10, 2026
                '%d.%m.%Y',     # 10.03.2026 = March 10, 2026
                '%d-%m-%Y',     # 10-03-2026 = March 10, 2026
                '%d-%m-%y',     # 10-03-26 = March 10, 2026
            ]
            
            for fmt in formats:
                try:
                    parsed = pd.to_datetime(date_str, format=fmt, errors='raise')
                    return parsed
                except:
                    continue
            
            # Fallback to pandas general date parser WITH dayfirst=True (Israeli format)
            try:
                return pd.to_datetime(date_str, dayfirst=True, errors='coerce')
            except:
                return None
        
        # Apply the parsing function
        df['Date'] = df['Date'].apply(parse_israeli_date)
        
        # Show parsing results
        parsed_count = df['Date'].notna().sum()
        failed_count = df['Date'].isna().sum()
        print(f"\n✅ Date parsing: {parsed_count} successful, {failed_count} failed")
        
        if failed_count > 0:
            print(f"❌ Sample failed dates: {df[df['Date'].isna()]['Date'].head().tolist()}")
        
        # Drop rows with failed date parsing
        df = df.dropna(subset=['Date'])
        
        print(f"\n✅ Total transactions loaded: {len(df)}")
        print(f"Sources breakdown:\n{df['Source'].value_counts()}")
        
        return df