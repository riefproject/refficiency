# Architecture Overview

This document outlines the architecture of a Telegram-based financial management application that integrates with Google Sheets for data storage and visualization. The architecture is presented in two models: a high-level overview and a detailed component breakdown.

### **Model 1: High-Level Overview**

This model provides a simplified view of the system, focusing on the main actors and their interactions.

<div style="display: flex; gap: 10px;  align-items: center;justify-content: center;">
<img style="border-radius:20;" src="docs/assets/arch1.png" alt="Architecture Overview" width="800"/>
</div>

### **Model 2: Component and Responsibility Canvas**

This model provides more detail, breaking down each major part into its components and responsibilities.

| **User**                                                                   | **Telegram Infrastructure**                                                                                                   | **Python Application (Backend)**                                                                                                                                                            | **Google Sheets (Database & Frontend)**                                                                                                                                                         |
| :------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Actor:** <br> - Finance Owner                                            | **Platform:** <br> - Telegram Bot API                                                                                         | **Core Components:** <br> - `main.py` (Entry Point) <br> - `handlers/` (Command Logic) <br> - `services/` (Business Logic) <br> - `models/` (Data Structure)                                | **Core Components:** <br> - `Dashboard` Sheet <br> - Monthly Sheets (`6/25`, `7/25`, etc.) <br> - Google Apps Script (Automation)                                                               |
| **Actions:** <br> - Send `/start` <br> - Send `/log` <br> - Send `/report` | **Tasks:** <br> - Receive messages from user <br> - Forward to Python webhook/polling <br> - Send replies from Python to user | **Tasks:** <br> - Authenticate user <br> - Validate command format <br> - Process data (create `Transaction` object) <br> - Contact Google Sheets API <br> - Format and send report replies | **Tasks:** <br> - Store raw transaction data <br> - Act as a data source for the dashboard <br> - Execute `onEdit` and `onOpen` scripts <br> - Display data visualizations (tables & summaries) |
| **Output:** <br> - Confirmation messages <br> - Financial reports          | **Connection:** <br> - `TELEGRAM_BOT_TOKEN`                                                                                   | **Connection:** <br> - `credentials.json` <br> - `gspread` library                                                                                                                          | **Connection:** <br> - Editor Access for Service Account                                                                                                                                        |

## ...

<div style="display: flex; gap: 10px;  align-items: center;justify-content: center;">
<img src="docs/assets/arch2.png" width="800">
</div>
