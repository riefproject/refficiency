/**
 * @OnlyCurrentDoc
 * =================================================================================================
 * FINANCIAL DASHBOARD AUTOMATION SCRIPT
 * =================================================================================================
 * This script provides a comprehensive solution for automating a financial dashboard in Google Sheets.
 *
 * HOW IT WORKS:
 * 1.	It reads control values (Year and Month) from a central "Dashboard" sheet.
 * 2.	It identifies all data sheets that match a "M/YY" naming convention for the selected year.
 * 3.	It aggregates all income and expenditure data from these sheets in a single, efficient pass.
 * 4.	It populates several summary tables on the "Dashboard" sheet:
 * - Monthly Income/Expenditure/Net Summary
 * - Annual Totals
 * - Top 5 Annual Expenditures by Category
 * - Top 5 Monthly Expenditures by Category (based on a dropdown)
 *
 * TRIGGERS:
 * - `onOpen()`: Automatically refreshes the dashboard when the spreadsheet is opened and adds a custom refresh menu.
 * - `onEdit(e)`: Automatically refreshes the dashboard whenever the Year (C1) or Month (C24) control cells are changed.
 *
 * SETUP:
 * - A sheet named "Dashboard" must exist.
 * - Data sheets must be named in "M/YY" format (e.g., "1/25", "12/25").
 * - Data sheets must contain columns with the exact headers defined in the CONFIGURATION section.
 * =================================================================================================
 */

// --- CONFIGURATION ---
// These constants centralize sheet and cell references for easy updates.
const DASHBOARD_SHEET_NAME = "Dashboard";
const YEAR_CELL = "C1"; // Cell for the target year (e.g., 2025)
const MONTH_CELL = "C24"; // Cell with a dropdown for the target month (e.g., "January")

// Define the exact header names to look for in the monthly data sheets.
// This makes the script resilient to column reordering but not to header renaming.
const CATEGORY_HEADER = "Kategori";
const INCOME_HEADER = "Pemasukan";
const EXPENDITURE_HEADER = "Pengeluaran";
// --- END CONFIGURATION ---

// Constant for Indonesian Rupiah currency format.
const IDR_FORMAT = '"Rp "#,##0;-"Rp "#,##0;""';

/**
 * The main orchestrator function that triggers the entire dashboard refresh process.
 * It coordinates the flow of data from reading inputs to populating the final tables.
 */
function updateDashboard() {
	const ss = SpreadsheetApp.getActiveSpreadsheet();
	const dashboardSheet = ss.getSheetByName(DASHBOARD_SHEET_NAME);
	
	// Gracefully exit if the main dashboard sheet is missing.
	if (!dashboardSheet) {
	SpreadsheetApp.getUi().alert(`CRITICAL: The required sheet named "${DASHBOARD_SHEET_NAME}" was not found. The script cannot proceed.`);
	return;
	}

	const targetYear = dashboardSheet.getRange(YEAR_CELL).getValue();
	const targetMonthName = dashboardSheet.getRange(MONTH_CELL).getValue();

	// Input validation is crucial for preventing unexpected errors during calculations.
	if (!targetYear || typeof targetYear !== 'number') {
	SpreadsheetApp.getUi().alert(`Data validation failed: The year in cell ${YEAR_CELL} is not a valid number.`);
	return;
	}

	// It's a best practice to clear previous results to avoid displaying stale data,
	// especially if a month's data is removed or has fewer categories than before.
	clearOldData(dashboardSheet);

	// STEP 1: Aggregate all data in one go. This is far more efficient than
	// reading from sheets multiple times.
	const annualData = aggregateDataFromSheets(ss, targetYear);
	
	// STEP 2: Populate the dashboard. These functions are responsible for writing
	// the processed data into the correct cells.
	populateMonthlySummary(dashboardSheet, annualData.monthlySummaries);
	populateAnnualSummary(dashboardSheet, annualData);
	populateTopAnnualExpenditures(dashboardSheet, annualData.expendituresByCategory);
	populateTopMonthlyExpenditures(dashboardSheet, annualData.monthlySummaries, targetMonthName);

	// Forces all pending changes to be written to the sheet immediately.
	// This ensures the user sees the updated data right away.
	SpreadsheetApp.flush();
}

/**
 * Wipes the content of dynamic data areas on the dashboard.
 * This function prevents old data from persisting if the new data set is smaller
 * (e.g., fewer categories of spending).
 * @param {GoogleAppsScript.Spreadsheet.Sheet} dashboardSheet The sheet object for the "Dashboard".
 */
function clearOldData(dashboardSheet) {
	dashboardSheet.getRange("B3:D14").clearContent();	 // Target: Monthly Summary table
	dashboardSheet.getRange("F3").clearContent();	 // Target: Annual Summary 
	dashboardSheet.getRange("F5").clearContent();	 // Target: Annual Summary 
	dashboardSheet.getRange("F7").clearContent();	 // Target: Annual Summary 
	dashboardSheet.getRange("B18:C22").clearContent();	// Target: Top 5 Annual Expenditures
	dashboardSheet.getRange("B26:C30").clearContent();	// Target: Top 5 Monthly Expenditures
}

/**
 * The core data processing engine. It iterates through all sheets in the spreadsheet,
 * filters for valid monthly data sheets based on their name for the target year,
 * and aggregates all financial data into a structured object.
 *
 * @param {GoogleAppsScript.Spreadsheet.Spreadsheet} ss The active spreadsheet instance.
 * @param {number} targetYear The four-digit year (e.g., 2025) to aggregate data for.
 * @return {{
 * totalIncome: number,
 * totalExpenditure: number,
 * expendituresByCategory: {[key: string]: number},
 * monthlySummaries: {[key: number]: {income: number, expenditure: number, categories: {[key: string]: number}}}
 * }} A structured object containing all aggregated financial data for the year.
 */
function aggregateDataFromSheets(ss, targetYear) {
	const allSheets = ss.getSheets();
	const yearShort = targetYear.toString().slice(-2); // e.g., 2025 -> "25"
	
	const aggregatedData = {
	totalIncome: 0,
	totalExpenditure: 0,
	expendituresByCategory: {},
	monthlySummaries: {}
	};

	// This regex ensures we only process sheets that follow the 'M/YY' or 'MM/YY'
	// naming convention, safely ignoring other tabs like 'Dashboard' or 'Instructions'.
	const sheetNameRegex = /^\d{1,2}\/\d{2}$/;

	allSheets.forEach(sheet => {
	const sheetName = sheet.getName();
	
	// Condition: Sheet name must match the regex AND end with the target year.
	if (sheetNameRegex.test(sheetName) && sheetName.endsWith(`/${yearShort}`)) {
		const monthNumber = parseInt(sheetName.split('/')[0], 10);
		
		const dataRange = sheet.getDataRange();
		const values = dataRange.getValues();
		if (values.length < 2) return; // Skip empty or header-only sheets.

		const headers = values[0].map(h => h.toString().trim());
		const catCol = headers.indexOf(CATEGORY_HEADER);
		const incCol = headers.indexOf(INCOME_HEADER);
		const expCol = headers.indexOf(EXPENDITURE_HEADER);
		
		// This defensive check makes the script robust. If a user renames a critical
		// column header, the script will log an error and skip that sheet instead of crashing.
		if (catCol === -1 || incCol === -1 || expCol === -1) {
		console.error(`Skipping sheet "${sheetName}" due to missing required headers. Please check for "${CATEGORY_HEADER}", "${INCOME_HEADER}", and "${EXPENDITURE_HEADER}".`);
		return;
		}

		let monthIncome = 0;
		let monthExpenditure = 0;
		let monthCategories = {};

		// Start loop at 1 to skip the header row.
		for (let i = 1; i < values.length; i++) {
		const row = values[i];
		
		// Use parseFloat and isNaN to safely handle cells that might be empty or contain text.
		const income = parseFloat(row[incCol]);
		const expenditure = parseFloat(row[expCol]);
		const category = row[catCol];

		if (!isNaN(income) && income > 0) monthIncome += income;
		
		if (!isNaN(expenditure) && expenditure > 0) {
			monthExpenditure += expenditure;
			if (category) { // Only aggregate categorized expenditures.
			// The "|| 0" pattern is a concise way to initialize a category total if it's the first time we've seen it.
			aggregatedData.expendituresByCategory[category] = (aggregatedData.expendituresByCategory[category] || 0) + expenditure;
			monthCategories[category] = (monthCategories[category] || 0) + expenditure;
			}
		}
		}

		// Add this month's totals to the annual aggregates.
		aggregatedData.totalIncome += monthIncome;
		aggregatedData.totalExpenditure += monthExpenditure;
		
		// Store the detailed summary for this specific month, keyed by its number (1-12).
		aggregatedData.monthlySummaries[monthNumber] = {
		income: monthIncome,
		expenditure: monthExpenditure,
		categories: monthCategories
		};
	}
	});

	return aggregatedData;
}

/**
 * Populates the 12-month summary table (Income, Expenditure, Net) on the dashboard.
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet The dashboard sheet object.
 * @param {object} monthlySummaries The `monthlySummaries` object from `aggregateDataFromSheets`.
 */
function populateMonthlySummary(sheet, monthlySummaries) {
	const summaryData = [];
	// Loop from 1 to 12 to ensure all months are represented in the table, regardless of data existence.
	for (let month = 1; month <= 12; month++) {
	const data = monthlySummaries[month];
	if (data) {
		summaryData.push([data.income, data.expenditure, data.income - data.expenditure]);
	} else {
		// If a month has no corresponding data sheet, represent it with zeros.
		summaryData.push([0, 0, 0]);
	}
	}
	const targetRange = sheet.getRange("B3:D14");
	targetRange.setValues(summaryData);
	targetRange.setNumberFormat(IDR_FORMAT);
}

/**
 * Populates the main annual summary cells (Total Income, Total Expenditure, Net).
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet The dashboard sheet object.
 * @param {object} annualData The primary aggregated data object.
 */
function populateAnnualSummary(sheet, annualData) {
	sheet.getRange("F3").setValue(annualData.totalIncome).setNumberFormat(IDR_FORMAT);
	sheet.getRange("F5").setValue(annualData.totalExpenditure).setNumberFormat(IDR_FORMAT);
	sheet.getRange("F7").setValue(annualData.totalIncome - annualData.totalExpenditure).setNumberFormat(IDR_FORMAT);
}

/**
 * Calculates and displays the top 5 annual expenditures by category.
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet The dashboard sheet object.
 * @param {object} expendituresByCategory An object mapping category names to total expenditure amounts.
 */
function populateTopAnnualExpenditures(sheet, expendituresByCategory) {
	// Convert the object to an array of [key, value] pairs, then sort and slice.
	const sorted = Object.entries(expendituresByCategory)
	.sort(([, a], [, b]) => b - a) // Sorts in descending order based on the value (amount).
	.slice(0, 5);	// Takes only the top 5 results.
	
	if (sorted.length > 0) {
	// Write the sorted data (e.g., [['Food', 5000], ['Transport', 4000]]) to the sheet.
	sheet.getRange(18, 2, sorted.length, 2).setValues(sorted);
	// Apply currency formatting to the amount column.
	sheet.getRange(18, 3, sorted.length, 1).setNumberFormat(IDR_FORMAT);
	}
}

/**
 * Calculates and displays the top 5 expenditures for a single, selected month.
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet The dashboard sheet object.
 * @param {object} monthlySummaries The `monthlySummaries` object from `aggregateDataFromSheets`.
 * @param {string} monthName The full name of the month (e.g., "January") from the dropdown.
 */
function populateTopMonthlyExpenditures(sheet, monthlySummaries, monthName) {
	if (!monthName) return; // Do nothing if no month is selected.

	// This is a robust, locale-independent way to convert a month name string
	// (e.g., "January", "Januari") into its corresponding month number (1-12).
	const monthNumber = new Date(Date.parse(monthName +" 1, 2000")).getMonth() + 1;
	const monthData = monthlySummaries[monthNumber];

	if (monthData && monthData.categories) {
	const sorted = Object.entries(monthData.categories)
		.sort(([, a], [, b]) => b - a)
		.slice(0, 5);

	if (sorted.length > 0) {
		sheet.getRange(26, 2, sorted.length, 2).setValues(sorted);
		sheet.getRange(26, 3, sorted.length, 1).setNumberFormat(IDR_FORMAT);
	}
	}
}

// --- UI CONTROL FUNCTIONS ---

/**
 * Increments the year in the control cell. Designed to be assigned to a button/drawing.
 * Provides a user-friendly way to change the year and immediately see the updated dashboard.
 */
function incrementYear() {
	const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(DASHBOARD_SHEET_NAME);
	if (!sheet) return;
	
	const range = sheet.getRange(YEAR_CELL);
	const currentValue = range.getValue();
	
	if (typeof currentValue === 'number') {
	range.setValue(currentValue + 1);
	} else {
	// If the cell is empty or invalid, provide a sensible default.
	range.setValue(new Date().getFullYear());
	}
	updateDashboard(); // Directly call the update function.
}

/**
 * Decrements the year in the control cell. Designed to be assigned to a button/drawing.
 */
function decrementYear() {
	const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(DASHBOARD_SHEET_NAME);
	if (!sheet) return;

	const range = sheet.getRange(YEAR_CELL);
	const currentValue = range.getValue();

	if (typeof currentValue === 'number') {
	range.setValue(currentValue - 1);
	} else {
	range.setValue(new Date().getFullYear());
	}
	updateDashboard(); // Directly call the update function.
}

// --- AUTOMATIC TRIGGERS ---

/**
 * A simple trigger that executes when the spreadsheet is opened.
 * It enhances user experience by adding a custom menu for manual refreshes
 * and by running an initial data load so the dashboard is up-to-date on open.
 */
function onOpen() {
	SpreadsheetApp.getUi()
		.createMenu('🔄 Refresh Dashboard')
		.addItem('Refresh Now', 'updateDashboard')
		.addToUi();
	updateDashboard();
}

/**
 * A simple trigger that executes when a user edits any cell in the spreadsheet.
 * The logic inside ensures it only acts when specific, critical cells are changed,
 * making the dashboard interactive and responsive to user input.
 * @param {GoogleAppsScript.Events.SheetsOnEdit} e The event object passed by the trigger.
 */
function onEdit(e) {
	const range = e.range;
	const sheetName = range.getSheet().getName();
	const cellNotation = range.getA1Notation();
	
	// To prevent the script from running on every single edit, we check if the
	// edit occurred on the Dashboard sheet AND in one of the two control cells.
	if (sheetName === DASHBOARD_SHEET_NAME && (cellNotation === YEAR_CELL || cellNotation === MONTH_CELL)) {
	updateDashboard();
	}
}