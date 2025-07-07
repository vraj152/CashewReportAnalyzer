# Personal Expense Analyzer

A simple web application to analyze and visualize personal expenses from CSV files.

## Features

- Upload and analyze expense data from CSV files
- Interactive visualizations of spending patterns
- Category-wise expense breakdown
- Monthly expense trends
- Summary metrics

## Installation

1. Clone this repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## CSV Format

Your CSV file should have the following columns:
- date: Date of expense (YYYY-MM-DD format)
- category: Expense category
- description: Description of the expense
- amount: Amount spent

## Sample Data

A sample dataset is included in the `data` directory for testing purposes. 