# MyOffer Monitor (MOM)

**MyOffer Dashboard Pro** is a comprehensive desktop management application built with Python and PyQt6. It is designed to streamline the workflow of managing data records, scanning site statuses, and automating browser launch tasks.

## 🚀 Features

The application is divided into three main modules:

* **📊 Data Manager:** A master list view to edit, sort, and manage client data records. Includes CSV export functionality (`Ctrl+S`).
* **🚀 Launchpad:** A dedicated interface for browser automation and client list handling.
* **🤖 Site Scanner:** An automated tool to scan pending records and update the Master List with real-time status, vendor, and configuration details.

## 🛠️ Tech Stack

* **Python 3.x**
* **PyQt6** (GUI Framework)
* **QtAwesome** (FontAwesome icons)
* **Pandas** (Data handling)

## 📂 Project Structure

The project follows a modular structure to separate logic from configuration:

```text
MOM/
│
├── main.py              # Application Entry Point
├── requirements.txt     # Python Dependencies
├── README.md            # Project Documentation
│
├── tabs/                # Application Logic Modules
│   ├── manager_tab.py
│   ├── scanner_tab.py
│   └── launchpad_tab.py
│
└── assets/              # Configuration & Styling
    └── styles.py        # Global Stylesheets & Themes