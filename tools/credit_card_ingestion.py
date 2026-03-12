import pandas as pd
import os

class IngestionAgent:
    def __init__(self):
        self.unified_columns = ['Date', 'Description', 'Amount', 'Owner', 'Source']
    
    def _read_file(self, file_path, skiprows=0):
        """
        Read either CSV or Excel file with proper encoding handling.
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Handle Excel files
        if file_ext in ['.xlsx', '.xls']:
            try:
                df = pd.read_excel(file_path, skiprows=skiprows)
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
        # Max files usually start the data at row 4
        df = self._read_file(file_path, skiprows=3)
        
        print(f"Max file columns: {df.columns.tolist()}")
        
        # Try to find the right columns (Hebrew names can vary)
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if 'תאריך' in col or 'date' in col_lower:
                column_mapping[col] = 'Date'
            elif 'בית עסק' in col or 'שם' in col or 'description' in col_lower:
                column_mapping[col] = 'Description'
            elif 'סכום' in col or 'חיוב' in col or 'amount' in col_lower:
                column_mapping[col] = 'Amount'
        
        df = df.rename(columns=column_mapping)
        
        # Ensure we have the required columns
        if not all(col in df.columns for col in ['Date', 'Description', 'Amount']):
            raise ValueError(f"Could not find required columns in Max file. Found: {df.columns.tolist()}")
        
        df['Owner'], df['Source'] = owner, 'Max'
        return df[self.unified_columns]

    def parse_isracard_csv(self, file_path, owner):
        # Isracard metadata is longer (~10 rows)
        df = self._read_file(file_path, skiprows=10)
        
        print(f"Isracard file columns: {df.columns.tolist()}")
        
        # Try to find the right columns
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if 'תאריך' in col or 'date' in col_lower:
                column_mapping[col] = 'Date'
            elif 'בית עסק' in col or 'שם' in col or 'description' in col_lower:
                column_mapping[col] = 'Description'
            elif 'סכום' in col or 'חיוב' in col or 'amount' in col_lower:
                column_mapping[col] = 'Amount'
        
        df = df.rename(columns=column_mapping)
        
        # Ensure we have the required columns
        if not all(col in df.columns for col in ['Date', 'Description', 'Amount']):
            raise ValueError(f"Could not find required columns in Isracard file. Found: {df.columns.tolist()}")
        
        df['Owner'], df['Source'] = owner, 'Isracard'
        return df[self.unified_columns]

    def parse_bank_discount(self, file_path):
        df = self._read_file(file_path, skiprows=8)
        
        print(f"Bank file columns: {df.columns.tolist()}")
        
        # Try to find the right columns (only map each target once)
        column_mapping = {}
        mapped_targets = set()
        
        for col in df.columns:
            col_str = str(col)
            col_lower = col_str.lower()
            
            # Map Date (only once)
            if 'Date' not in mapped_targets and ('תאריך' in col_str or col_str == 'Date'):
                column_mapping[col] = 'Date'
                mapped_targets.add('Date')
            # Map Description (only once)
            elif 'Description' not in mapped_targets and ('בית עסק' in col_str or 'description' in col_lower):
                column_mapping[col] = 'Description'
                mapped_targets.add('Description')
            # Map Amount (only once) - prefer 'סכום החיוב' (charged amount)
            elif 'Amount' not in mapped_targets and ('סכום החיוב' in col_str or 'סכום חיוב' in col_str):
                column_mapping[col] = 'Amount'
                mapped_targets.add('Amount')
        
        # If Amount still not mapped, try other amount-related columns
        if 'Amount' not in mapped_targets:
            for col in df.columns:
                col_str = str(col)
                col_lower = col_str.lower()
                if 'סכום' in col_str or 'זכות' in col_str or 'חובה' in col_str or 'amount' in col_lower:
                    column_mapping[col] = 'Amount'
                    mapped_targets.add('Amount')
                    break
        
        df = df.rename(columns=column_mapping)
        
        # Ensure we have the required columns
        if not all(col in df.columns for col in ['Date', 'Description', 'Amount']):
            missing = [col for col in ['Date', 'Description', 'Amount'] if col not in df.columns]
            raise ValueError(f"Could not find required columns in Bank file. Missing: {missing}. Column mapping: {column_mapping}")
        
        df['Owner'], df['Source'] = 'Joint', 'Bank_Discount'
        return df[self.unified_columns]

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
            print(f"Processing file: {file}")
            
            if "max" in file_lower:
                print("  → Identified as Max credit card")
                all_data.append(self.parse_max(file, "Tal"))
            elif "isracard" in file_lower or "ישראכרט" in file_lower:
                print("  → Identified as Isracard")
                all_data.append(self.parse_isracard_csv(file, "Tal"))
            elif "דיסקונט" in file_lower or "discount" in file_lower:
                print("  → Identified as Discount bank/card")
                all_data.append(self.parse_bank_discount(file))
            else:
                print(f"  ⚠️ Unknown file type, skipping: {file}")
        
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
        df['Date'] = df['Date'].astype(str).str.strip()
        
        # Show sample dates for debugging
        print(f"\n📅 Sample dates from files:")
        print(df['Date'].head(10).tolist())
        
        print(f"\n✅ Total transactions loaded: {len(df)}")
        print(f"Sources breakdown:\n{df['Source'].value_counts()}")
        
        return df