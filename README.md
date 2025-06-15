# Reefficiency - Telegram Finance Bot

**Reefficiency** is a Telegram bot application designed to simplify personal financial tracking and reporting. With full integration into Google Sheets, this bot not only acts as a transaction logger but also powers a dynamic and automated financial dashboard.

---

## Table of Contents

-   [Overview](#overview)
-   [Key Features](#key-features)
-   [System Architecture](#system-architecture)
-   [Tech Stack](#tech-stack)
-   [Prerequisites](#prerequisites)
-   [Installation & Configuration](#installation--configuration)
    -   [1. Clone the Repository](#1-clone-the-repository)
    -   [2. Install Dependencies](#2-install-dependencies)
    -   [3. Configure the Environment](#3-configure-the-environment)
-   [Google Sheets Setup (Required)](#google-sheets-setup-required)
    -   [Step 1: Create & Share the Google Sheet](#step-1-create--share-the-google-sheet)
    -   [Step 2: Set Up the Dashboard Layout](#step-2-set-up-the-dashboard-layout)
    -   [Step 3: Set Up the Google Apps Script](#step-3-set-up-the-google-apps-script)
-   [Usage](#usage)
    -   [Running the Bot](#running-the-bot)
    -   [Available Commands](#available-commands)
-   [Database Schema](#database-schema)
-   [Project Structure](#project-structure)

---

## Overview

This project aims to solve the challenge of tracking daily finances. Instead of using complex applications, users can quickly log every income and expense directly from Telegram. All data is automatically stored and processed in a Google Sheet, which also serves as a visual interface for data analysis through an interactive dashboard.

## Key Features

-   **Quick Transaction Logging**: Log income and expenses with simple commands directly in Telegram.
-   **Instant Financial Reports**: Get monthly or annual reports on-demand via a command.
-   **Automated Dashboard**: The integrated Google Sheet features a dashboard that automatically summarizes data, including monthly overviews, annual totals, and top spending categories.
-   **Secure Multi-User Access**: Bot access can be restricted to specific, pre-authorized Telegram user IDs.
-   **Flexible Dating**: Transactions can be logged for the current date (default) or a specific date in the past.
-   **Dynamic Data Structure**: The bot automatically creates a new monthly sheet if one doesn't already exist for the transaction date.

## System Architecture

The system consists of four main components working together:

1.  **User (via Telegram)**: Interacts with the system using commands in the Telegram app.
2.  **Telegram Bot (Interface)**: Receives commands from the user and displays replies from the backend application.
3.  **Python Application (Backend)**:
    -   Built with `python-telegram-bot`.
    -   Receives and processes the logic for each command (logging, reporting, etc.).
    -   Handles user authentication.
    -   Communicates with the Google Sheets API using the `gspread` library to read and write data.
4.  **Google Sheets (Database & Frontend)**:
    -   Acts as the database for storing all raw transaction data.
    -   Serves as the frontend for data visualization via a `Dashboard` sheet, which includes automation scripts (Google Apps Script).

\#\# Tech Stack

-   **Backend**: Python 3
-   **Telegram Bot Framework**: `python-telegram-bot`
-   **Google Sheets API Client**: `gspread`
-   **Environment Variables**: `python-dotenv`
-   **Database & Dashboard**: Google Sheets
-   **Automation**: Google Apps Script

## Prerequisites

Before you begin, ensure you have the following:

-   Python 3.8 or higher.
-   A Telegram account and a bot created via [BotFather](https://t.me/botfather) to obtain a `TELEGRAM_BOT_TOKEN`.
-   A Google Cloud Project with the **Google Sheets API** and **Google Drive API** enabled.
-   A Service Account credential file (`credentials.json`) downloaded from your Google Cloud Project.
-   Your Telegram User ID (you can get this from a bot like `@userinfobot`).

## Installation & Configuration

#### 1\. Clone the Repository

```bash
git clone https://github.com/username/reefficiency.git
cd reefficiency
```

#### 2\. Install Dependencies

It's recommended to use a virtual environment.

```bash
python -m venv env
source env/bin/activate  # For Linux/macOS
# or
env\Scripts\activate  # For Windows

pip install -r requirements.txt
```

_(Note: A `requirements.txt` file should be present or created via `pip freeze > requirements.txt`)_

#### 3\. Configure the Environment

Create a file named `.env` in the project's root directory. Copy the contents of `.env.example` (if it exists) or fill it with the following variables:

```env
# The bot token obtained from BotFather
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"

# The path to your Google Service Account credentials file
GOOGLE_SHEETS_CREDENTIALS_PATH="credentials.json"

# The name of the Google Sheet you will use
GOOGLE_SHEET_NAME="Financial Report Bot"

# A comma-separated list of Telegram user IDs that are allowed to use the bot
ALLOWED_TELEGRAM_IDS="12345678,87654321"
```

Ensure your `credentials.json` file is placed in the correct path.

## Google Sheets Setup (Required)

This is the most critical step. Follow these instructions carefully.

#### Step 1: Create & Share the Google Sheet

1.  Go to [Google Sheets](https://docs.google.com/spreadsheets/create) and create a new spreadsheet.
2.  Name the spreadsheet exactly as you defined `GOOGLE_SHEET_NAME` in your `.env` file.
3.  Open your `credentials.json` file and find the service account's email address (e.g., `bot-name@your-project.iam.gserviceaccount.com`).
4.  Click the **"Share"** button in your Google Sheet, enter the service account's email, and grant it **"Editor"** access. This is mandatory for the bot to write data.

#### Step 2: Set Up the Dashboard Layout

1.  Create a new sheet (tab) and rename it to `Dashboard`. The name is case-sensitive.
2.  Set up the following cells exactly as described below, as the bot and scripts rely on this structure:
    -   `A1`: `Financial Dashboard Summary` (Title)
    -   `C1`: Enter the current year (e.g., `2025`). This cell controls the annual data displayed.
    -   `A2:D2`: Table headers: `Month`, `Total Income`, `Total Expenditure`, `Net Difference`
    -   `A3:A14`: The names of the months (`Jan`, `Feb`, etc.)
    -   `F2`: `Total Annual Income`
    -   `F4`: `Total Annual Expenditure`
    -   `A16`: `Top 5 Annual Expenditures`
    -   `A17:C17`: Headers: `Rank`, `Category`, `Total Expenditure`
    -   `A24`: `Top 5 Monthly Expenditures (Select Month Below)`
    -   `C24`: Create a month dropdown. Click the cell, go to `Data > Data validation`, choose criteria "Dropdown (from a range)," and input the English month names.

#### Step 3: Set Up the Google Apps Script

This script automates all calculations on the dashboard.

1.  In your Google Sheet, go to `Extensions > Apps Script`.
2.  Delete any default code in the editor.
3.  Copy the entire code from the `google_sheet/src/scripts.gs` file (if available, or create a basic `updateDashboard` function).
4.  Paste it into the Apps Script editor and save the project.
5.  Run the `updateDashboard` function once manually from the editor to grant the necessary permissions.

## Usage

#### Running the Bot

To start the bot, run `main.py` from the root directory:

```bash
python main.py
```

You should see a message in your terminal indicating that the bot is running.

#### Available Commands

The primary interaction with the bot is through the following commands:

-   `/start`
    Displays a welcome message and a list of available commands.

-   `/catat`
    Logs a new transaction. The format is very specific.
    **Format**: `/catat <type> <category> <amount> [description] [date]`

    -   `type`: `pemasukan` (income) or `pengeluaran` (expense).
    -   `category`: The transaction category (e.g., `food`, `transport`, `salary`).
    -   `amount`: A number without commas or periods.
    -   `description` (optional): A brief note about the transaction.
    -   `date` (optional): Format `YYYY-MM-DD`. If omitted, the current date is used.
        **Examples**:

    <!-- end list -->

    ```
    /catat pengeluaran food 50000 Padang rice
    /catat pemasukan salary 5000000 Monthly salary 2025-06-25
    ```

-   `/laporan`
    Generates a financial report for a requested period.
    **Format**:

    -   `/laporan <month>`: Report for a specific month in the current year.
    -   `/laporan <year>`: Report for a full year.
    -   `/laporan <month> <year>`: Report for a specific month and year.
        **Examples**:

    <!-- end list -->

    ```
    /laporan june
    /laporan 2024
    /laporan february 2025
    ```

## Database Schema

The bot does not use a traditional database. Instead, it stores data in Google Sheets with the following structure:

-   For each month, a new sheet is automatically created with the name format `M/YY`, e.g., `6/25` for June 2025.
-   Each monthly sheet has the following columns:
    1.  `Tanggal`: The transaction date (format `YYYY-MM-DD`).
    2.  `Kategori`: The user-defined category.
    3.  `Deskripsi`: The optional description.
    4.  `Pemasukan`: The income amount (the `Pengeluaran` column will be empty).
    5.  `Pengeluaran`: The expense amount (the `Pemasukan` column will be empty).

## Project Structure

```
riefproject/reefficiency/
│
├── .gitignore
├── architecture.md
├── main.py
├── README.md
│
├── config/
│   └── settings.py       # Loads environment variables and sets up logging
│
├── docs/
│   └── assets/           # Images for documentation
│
├── google_sheet/
│   └── README.md         # Specific documentation for Google Sheets setup
│
├── handlers/
│   ├── start.py          # Logic for /start command
│   ├── catat.py          # Logic for /catat command
│   ├── laporan.py        # Logic for /laporan command
│   └── error.py          # Error handling
│
├── models/
│   └── transaction.py    # Data model class for a transaction
│
└── services/
    ├── auth.py           # Service for user authentication
    └── gsheets.py        # Service for all interactions with Google Sheets
```

---

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

Don't forget to give the project a star\! Thanks again\!

## License

Distributed under the MIT License.

**Copyright (c) 2025, riefproject**
