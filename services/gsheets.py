import gspread
import logging
from datetime import datetime
from config.settings import GOOGLE_SHEETS_CREDENTIALS_PATH, GOOGLE_SHEET_NAME

# Set up a logger for this module to provide visibility into the script's operations.
logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """
    A service class to abstract all interactions with the Google Sheets API.
    
    This class handles connecting to the Google Sheets service, creating and managing
    monthly transaction sheets, and updating a central dashboard with aggregated financial data.
    It is designed to be a singleton or a long-lived service instance within an application.
    """

    def __init__(self):
        """
        Initializes the GoogleSheetsService instance.
        
        The connection objects `gc` (gspread client) and `spreadsheet` are initialized
        to None. They will be populated upon a successful connection attempt.
        """
        self.gc = None
        self.spreadsheet = None

    def init_connection(self) -> bool:
        """
        Establishes and authenticates the connection to the Google Sheets API.
        
        This method uses service account credentials to connect to gspread and open the
        specified spreadsheet by its name. It also ensures the main 'Dashboard' sheet
        exists, creating it if necessary.
        
        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        if not GOOGLE_SHEETS_CREDENTIALS_PATH or not GOOGLE_SHEET_NAME:
            logger.error("❌ Google Sheets credentials path or sheet name are not set in environment variables.")
            return False
            
        try:
            logger.info("🔄 Attempting to connect to Google Sheets...")
            self.gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS_PATH)
            self.spreadsheet = self.gc.open(GOOGLE_SHEET_NAME)
            logger.info(f"✅ Successfully connected to Google Spreadsheet: '{GOOGLE_SHEET_NAME}'")
            
            # After connecting, ensure the main dashboard sheet is present.
            self.ensure_dashboard_exists()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets. Error: {e}", exc_info=True)
            # Reset connection objects on failure to prevent using stale connections.
            self.gc = None
            self.spreadsheet = None
            return False

    def ensure_connection(self) -> bool:
        """
        Ensures that an active connection to Google Sheets exists.
        
        If the connection has not been initialized yet (`self.gc` is None), this method
        will trigger `init_connection()`. This allows for lazy initialization.
        
        Returns:
            bool: True if a connection is active or was successfully established, False otherwise.
        """
        if self.gc is None or self.spreadsheet is None:
            return self.init_connection()
        return True

    def get_sheet_name_from_date(self, date_str: str) -> str | None:
        """
        Converts a date string from 'YYYY-MM-DD' format to the 'M/YY' sheet name format.
        
        Args:
            date_str (str): The date string in 'YYYY-MM-DD' format.
            
        Returns:
            str | None: The formatted sheet name (e.g., "6/25") or None if the format is invalid.
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month = date_obj.month
            year = str(date_obj.year)[2:]  # Get the last two digits of the year
            return f"{month}/{year}"
        except ValueError:
            logger.error(f"❌ Invalid date format provided: '{date_str}'. Expected 'YYYY-MM-DD'.")
            return None

    def get_or_create_sheet(self, sheet_name: str) -> gspread.Worksheet:
        """
        Retrieves an existing worksheet by name or creates it if it doesn't exist.
        
        If a new sheet is created, it is automatically populated with a default
        set of headers for financial transactions.
        
        Args:
            sheet_name (str): The name of the worksheet to get or create (e.g., "6/25").
            
        Returns:
            gspread.Worksheet: The worksheet object.
            
        Raises:
            Exception: If there is an error accessing or creating the sheet.
        """
        try:
            # First, attempt to retrieve the existing sheet.
            worksheet = self.spreadsheet.worksheet(sheet_name)
            logger.info(f"📋 Using existing sheet: '{sheet_name}'")
            return worksheet
            
        except gspread.WorksheetNotFound:
            # If the sheet doesn't exist, create a new one.
            logger.info(f"🆕 Worksheet '{sheet_name}' not found. Creating a new one.")
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
            
            # Add headers to the newly created sheet.
            headers = ["Tanggal", "Kategori", "Deskripsi", "Pemasukan", "Pengeluaran"]
            worksheet.append_row(headers)
            logger.info(f"✅ Created new sheet '{sheet_name}' and added headers.")
            return worksheet
            
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred while accessing/creating sheet '{sheet_name}': {e}", exc_info=True)
            raise

    def add_transaction(self, transaction_data: dict) -> bool:
        """
        Adds a new transaction record to the appropriate monthly sheet.
        
        This method determines the correct sheet based on the transaction date, creates
        the sheet if it doesn't exist, and appends the new transaction data as a row.
        It then triggers a dashboard update.
        
        Args:
            transaction_data (dict): A dictionary containing transaction details.
                                     Must include a "Tanggal" key in 'YYYY-MM-DD' format.
        
        Returns:
            bool: True if the transaction was added successfully, otherwise it raises an exception.
            
        Raises:
            Exception: If the connection is unavailable or if transaction data is invalid.
        """
        if not self.ensure_connection():
            raise Exception("Google Sheets connection is not available.")
            
        try:
            # Extract the date from the transaction data to determine the target sheet.
            date_value = transaction_data.get("Tanggal")
            if not date_value:
                raise Exception("Transaction date ('Tanggal') not found in the provided data.")
            
            # Determine the target sheet name (e.g., "6/25") from the date.
            sheet_name = self.get_sheet_name_from_date(str(date_value).split(" ")[0])
            if not sheet_name:
                raise Exception(f"Invalid date format for transaction: '{date_value}'")
            
            # Get the worksheet object, creating it if necessary.
            worksheet = self.get_or_create_sheet(sheet_name)
            
            # Fetch headers from the sheet to ensure correct column mapping.
            headers = worksheet.row_values(1)
            if not headers:
                # This is a fallback, as get_or_create_sheet should have already added headers.
                headers = ["Tanggal", "Kategori", "Deskripsi", "Pemasukan", "Pengeluaran"]
                worksheet.append_row(headers)
                logger.warning(f"Headers were missing in sheet '{sheet_name}' and have been recreated.")
            
            logger.info(f"📊 Preparing to add transaction to sheet '{sheet_name}': {transaction_data}")
            
            # Prepare the new row by mapping dictionary keys to header positions.
            # This makes the order of keys in transaction_data irrelevant.
            new_row = [""] * len(headers)
            for key, value in transaction_data.items():
                if key in headers:
                    index = headers.index(key)
                    # For dates, ensure only the 'YYYY-MM-DD' part is stored.
                    if key == "Tanggal" and value and " " in str(value):
                        value = str(value).split(" ")[0]
                    new_row[index] = str(value) if value is not None else ""
            
            logger.info(f"📝 Final row data for sheet '{sheet_name}': {new_row}")
            worksheet.append_row(new_row)
            logger.info(f"✅ Transaction successfully added to sheet '{sheet_name}'.")
            
            # After adding data, trigger the dashboard refresh.
            self.update_dashboard_data()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add transaction. Error: {e}", exc_info=True)
            raise

    def create_dashboard_sheet(self) -> gspread.Worksheet:
        """
        Creates the main 'Dashboard' worksheet with a predefined layout if it doesn't exist.
        
        Returns:
            gspread.Worksheet: The 'Dashboard' worksheet object.
            
        Raises:
            Exception: If there is an error creating the dashboard sheet.
        """
        try:
            # Check if the 'Dashboard' sheet already exists to avoid duplication.
            return self.spreadsheet.worksheet("Dashboard")
        except gspread.WorksheetNotFound:
            logger.info("🆕 'Dashboard' sheet not found. Creating and initializing it...")
            dashboard = self.spreadsheet.add_worksheet(title="Dashboard", rows=50, cols=10)
            
            # Set up the static layout (headers, titles).
            self._setup_dashboard_layout(dashboard)
            self._format_dashboard_headers(dashboard)
            
            logger.info("✅ 'Dashboard' sheet created and configured successfully.")
            return dashboard
        except Exception as e:
            logger.error(f"❌ Failed to create the 'Dashboard' sheet. Error: {e}", exc_info=True)
            raise

    def _setup_dashboard_layout(self, worksheet: gspread.Worksheet):
        """
        Sets up the static layout and headers for the 'Dashboard' sheet.
        
        This is a private helper method called only during dashboard creation.
        It writes all the titles and column headers for the summary tables.
        
        Args:
            worksheet (gspread.Worksheet): The 'Dashboard' worksheet object.
        """
        try:
            # Main header and year controller cell
            worksheet.update('A1', 'Financial Dashboard Summary')
            worksheet.update('C1', str(datetime.now().year)) # Default to current year
            
            # Monthly summary table headers
            worksheet.update('A2:D2', [['Month', 'Total Income', 'Total Expenditure', 'Net Difference']])
            
            # Month names
            months = [['Jan'], ['Feb'], ['Mar'], ['Apr'], ['May'], ['Jun'], 
                      ['Jul'], ['Aug'], ['Sep'], ['Oct'], ['Nov'], ['Dec']]
            worksheet.update('A3:A14', months)
            
            # Annual summary headers
            worksheet.update('F2', 'Total Annual Income')
            worksheet.update('F4', 'Total Annual Expenditure')
            worksheet.update('F6', 'Net Annual Difference')
            
            # Top Annual Expenditure section
            worksheet.update('A16', 'Top 5 Annual Expenditures')
            worksheet.update('A17:C17', [['Rank', 'Category', 'Total Expenditure']])
            worksheet.update('A18:A22', [[str(i)] for i in range(1, 6)])
            
            # Top Monthly Expenditure section
            worksheet.update('A24', 'Top 5 Monthly Expenditures (Select Month Below)')
            # Add a data validation rule for the month selection dropdown
            worksheet.data_validation('C24', gspread.DataValidationRule(
                gspread.BooleanCondition('ONE_OF_LIST', ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']),
                allow_invalid=False
            ))
            worksheet.update('A25:C25', [['Rank', 'Category', 'Total Expenditure']])
            worksheet.update('A26:A30', [[str(i)] for i in range(1, 6)])
            
            logger.info("📊 Dashboard layout setup completed.")
            
        except Exception as e:
            logger.error(f"❌ An error occurred while setting up the dashboard layout: {e}", exc_info=True)
            raise

    def _format_dashboard_headers(self, worksheet: gspread.Worksheet):
        """
        Applies basic formatting (bold text, background color) to dashboard headers.
        
        Args:
            worksheet (gspread.Worksheet): The 'Dashboard' worksheet object.
        """
        try:
            header_format = {
                'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85},
                'textFormat': {'bold': True}
            }
            # Define all ranges that need the header format
            header_ranges = ['A2:D2', 'F2', 'F4', 'F6', 'A17:C17', 'A25:C25']
            worksheet.batch_format(header_ranges, {'cell': header_format})
            
            logger.info("🎨 Dashboard header formatting applied.")
        except Exception as e:
            # Formatting is non-critical, so log a warning instead of an error.
            logger.warning(f"⚠️ Could not apply formatting to dashboard headers. This is non-critical. Error: {e}")

    def ensure_dashboard_exists(self) -> bool:
        """
        Public method to ensure the 'Dashboard' sheet exists, creating it if necessary.
        
        Returns:
            bool: True if the dashboard exists or was created, False on failure.
        """
        if not self.ensure_connection():
            return False
            
        try:
            self.create_dashboard_sheet()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to ensure the 'Dashboard' sheet exists. Error: {e}", exc_info=True)
            return False

    def update_dashboard_data(self) -> bool:
        """
        Orchestrates the full update of the dashboard's dynamic data.
        
        This method fetches data from all monthly sheets, aggregates it, and then
        populates the summary tables on the 'Dashboard' sheet.
        
        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if not self.ensure_connection():
            return False
            
        try:
            logger.info("🔄 Starting dashboard data update...")
            dashboard = self.spreadsheet.worksheet("Dashboard")
            
            # Step 1: Get all monthly sheets and their pre-calculated summaries.
            monthly_sheets_data = self.get_monthly_sheets()
            
            # Step 2: Update each section of the dashboard.
            self._update_monthly_summary(dashboard, monthly_sheets_data)
            self._update_annual_totals(dashboard, monthly_sheets_data)
            self._update_top_expenditures(dashboard, monthly_sheets_data)
            
            logger.info("✅ Dashboard data update completed successfully.")
            return True
            
        except Exception as e:
            logger.error(f"❌ A critical error occurred during dashboard update. Error: {e}", exc_info=True)
            return False

    def get_monthly_sheets(self) -> dict:
        """
        Fetches all valid monthly worksheets and calculates their summaries.
        
        A valid monthly sheet has a name in the 'M/YY' format.
        
        Returns:
            dict: A dictionary where keys are sheet names (e.g., "6/25") and values
                  are objects containing the month, year, worksheet object, and summary data.
        """
        monthly_data = {}
        try:
            worksheets = self.spreadsheet.worksheets()
            
            for ws in worksheets:
                sheet_name = ws.title
                # A simple check to identify monthly data sheets and exclude others like 'Dashboard'.
                if '/' in sheet_name and sheet_name.lower() != "dashboard":
                    try:
                        month_str, year_str = sheet_name.split('/')
                        month_num = int(month_str)
                        year_num = int(f"20{year_str}") # Assumes 21st century
                        
                        summary = self._get_sheet_summary(ws)
                        
                        monthly_data[sheet_name] = {
                            'month': month_num,
                            'year': year_num,
                            'worksheet': ws,
                            'data': summary
                        }
                    except (ValueError, IndexError):
                        # Ignore sheets with names that look like 'M/YY' but aren't (e.g., 'Notes/Ideas').
                        logger.warning(f"⚠️ Sheet '{sheet_name}' resembles a monthly sheet but could not be parsed. Skipping.")
                        continue
                        
            logger.info(f"📊 Found and processed {len(monthly_data)} monthly data sheets.")
            return monthly_data
            
        except Exception as e:
            logger.error(f"❌ An error occurred while fetching monthly sheets. Error: {e}", exc_info=True)
            return {}

    def _get_sheet_summary(self, worksheet: gspread.Worksheet) -> dict:
        """
        Calculates total income, expenditure, and categorical spending for a single worksheet.
        
        Args:
            worksheet (gspread.Worksheet): The worksheet to analyze.
            
        Returns:
            dict: A summary containing total_income, total_expenditure, net_difference,
                  and a dictionary of spending by category.
        """
        try:
            all_data = worksheet.get_all_records()
            
            total_income = 0.0
            total_expenditure = 0.0
            categories = {}
            
            for row in all_data:
                # Process income, safely handling non-numeric or empty values.
                income_val = row.get('Pemasukan', '')
                if income_val and str(income_val).strip():
                    try:
                        total_income += float(str(income_val).replace(',', ''))
                    except (ValueError, TypeError):
                        pass # Ignore cells that cannot be converted to float.
                
                # Process expenditure and aggregate by category.
                expenditure_val = row.get('Pengeluaran', '')
                if expenditure_val and str(expenditure_val).strip():
                    try:
                        amount = float(str(expenditure_val).replace(',', ''))
                        total_expenditure += amount
                        
                        category = row.get('Kategori', 'Uncategorized')
                        categories[category] = categories.get(category, 0.0) + amount
                    except (ValueError, TypeError):
                        pass # Ignore cells that cannot be converted to float.
            
            return {
                'total_income': total_income,
                'total_expenditure': total_expenditure,
                'net_difference': total_income - total_expenditure,
                'categories': categories
            }
        except Exception as e:
            logger.error(f"❌ Error summarizing sheet '{worksheet.title}'. Error: {e}", exc_info=True)
            return {
                'total_income': 0, 'total_expenditure': 0, 
                'net_difference': 0, 'categories': {}
            }

    def _update_monthly_summary(self, dashboard: gspread.Worksheet, monthly_data: dict):
        """
        Updates the monthly summary table (B3:D14) on the Dashboard sheet.
        
        It filters data based on the year specified in the control cell 'C1'.
        
        Args:
            dashboard (gspread.Worksheet): The 'Dashboard' worksheet object.
            monthly_data (dict): The aggregated data from all monthly sheets.
        """
        try:
            # Read the target year from the control cell C1.
            target_year_str = dashboard.acell('C1').value
            target_year = int(target_year_str) if target_year_str and target_year_str.isdigit() else datetime.now().year
            logger.info(f"📅 Updating monthly summary table for the year: {target_year}")
            
            update_payload = []
            for month_num in range(1, 13):
                # Find the data for the current month and target year.
                found_data = None
                for sheet_info in monthly_data.values():
                    if sheet_info['month'] == month_num and sheet_info['year'] == target_year:
                        found_data = sheet_info['data']
                        break
                
                if found_data:
                    update_payload.append([
                        found_data['total_income'],
                        found_data['total_expenditure'],
                        found_data['net_difference']
                    ])
                else:
                    # If no data exists for that month, fill with empty strings to clear old data.
                    update_payload.append(['', '', ''])
            
            # Perform a single batch update for efficiency.
            dashboard.update('B3:D14', update_payload)
            logger.info(f"📊 Monthly summary table updated for the year {target_year}.")
        except Exception as e:
            logger.error(f"❌ Failed to update the monthly summary table. Error: {e}", exc_info=True)

    def _update_annual_totals(self, dashboard: gspread.Worksheet, monthly_data: dict):
        """
        Updates the annual total cells (F3, F5, F7) on the Dashboard sheet.
        
        It aggregates totals from all monthly sheets belonging to the target year in cell 'C1'.
        
        Args:
            dashboard (gspread.Worksheet): The 'Dashboard' worksheet object.
            monthly_data (dict): The aggregated data from all monthly sheets.
        """
        try:
            target_year_str = dashboard.acell('C1').value
            target_year = int(target_year_str) if target_year_str and target_year_str.isdigit() else datetime.now().year
            
            total_annual_income = 0.0
            total_annual_expenditure = 0.0
            
            # Sum up data for all months in the target year.
            for data in monthly_data.values():
                if data['year'] == target_year:
                    total_annual_income += data['data']['total_income']
                    total_annual_expenditure += data['data']['total_expenditure']
            
            net_annual = total_annual_income - total_annual_expenditure
            
            # Use batch update for better performance
            dashboard.batch_update([
                {'range': 'F3', 'values': [[total_annual_income]]},
                {'range': 'F5', 'values': [[total_annual_expenditure]]},
                {'range': 'F7', 'values': [[net_annual]]}
            ])
            
            logger.info(f"📊 Annual totals updated for year {target_year}: Income={total_annual_income}, Expenditure={total_annual_expenditure}")
        except Exception as e:
            logger.error(f"❌ Failed to update annual totals. Error: {e}", exc_info=True)
    
    def _update_top_expenditures(self, dashboard: gspread.Worksheet, monthly_data: dict):
        """
        Updates the Top 5 Annual and Top 5 Monthly expenditure tables.
        
        Annual data is based on the year in C1. Monthly data is based on the month
        selected in the dropdown in C24.
        
        Args:
            dashboard (gspread.Worksheet): The 'Dashboard' worksheet object.
            monthly_data (dict): The aggregated data from all monthly sheets.
        """
        try:
            target_year_str = dashboard.acell('C1').value
            target_year = int(target_year_str) if target_year_str and target_year_str.isdigit() else datetime.now().year
            
            # --- UPDATE TOP 5 ANNUAL EXPENDITURES ---
            all_categories_annual = {}
            for data in monthly_data.values():
                if data['year'] == target_year:
                    for category, amount in data['data']['categories'].items():
                        all_categories_annual[category] = all_categories_annual.get(category, 0.0) + amount
            
            top_annual = sorted(all_categories_annual.items(), key=lambda item: item[1], reverse=True)[:5]
            
            annual_payload = [['', ''] for _ in range(5)] # Create a blank payload
            for i, (category, amount) in enumerate(top_annual):
                annual_payload[i] = [category, amount]
            dashboard.update('B18:C22', annual_payload)
            
            # --- UPDATE TOP 5 MONTHLY EXPENDITURES ---
            target_month_str = dashboard.acell('C24').value
            target_month_num = None
            if target_month_str:
                try:
                    # Convert month name to month number
                    target_month_num = datetime.strptime(target_month_str, "%B").month
                except ValueError:
                    logger.warning(f"⚠️ Invalid month name in C24: '{target_month_str}'. Skipping monthly update.")
            
            monthly_payload = [['', ''] for _ in range(5)] # Blank payload for monthly data
            if target_month_num:
                monthly_categories = {}
                for data in monthly_data.values():
                    if data['month'] == target_month_num and data['year'] == target_year:
                        monthly_categories = data['data']['categories']
                        break
                
                top_monthly = sorted(monthly_categories.items(), key=lambda item: item[1], reverse=True)[:5]
                for i, (category, amount) in enumerate(top_monthly):
                    monthly_payload[i] = [category, amount]
            
            dashboard.update('B26:C30', monthly_payload)
            logger.info(f"📊 Top expenditures updated for year {target_year} and month '{target_month_str}'.")
            
        except Exception as e:
            logger.error(f"❌ Failed to update top expenditures. Error: {e}", exc_info=True)


# It's common practice to create a single instance of the service
# that can be imported and used throughout the application.
sheets_service = GoogleSheetsService()
