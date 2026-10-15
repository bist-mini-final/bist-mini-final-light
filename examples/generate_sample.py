"""Generate a small, synthetic financial workbook for learning."""

from pathlib import Path

from openpyxl import Workbook


def main() -> None:
    workbook = Workbook()
    workbook.remove(workbook.active)
    statements = {
        "Income Statement": [
            ["Revenue", 1000, 1200, 1500],
            ["Cost of Goods Sold", 600, 700, 850],
            ["Gross Profit", 400, 500, 650],
            ["Operating Income", 180, 230, 310],
            ["Net Income", 120, 160, 220],
        ],
        "Balance Sheet": [
            ["Total Assets", 2000, 2300, 2700],
            ["Total Liabilities", 800, 900, 1000],
            ["Total Equity", 1200, 1400, 1700],
            ["Cash and Cash Equivalents", 300, 400, 550],
        ],
        "Cash Flow": [
            ["Operating Cash Flow", 200, 280, 360],
            ["Investing Cash Flow", -100, -120, -150],
            ["Financing Cash Flow", -50, -60, -60],
        ],
    }
    for name, rows in statements.items():
        sheet = workbook.create_sheet(name)
        sheet.append(["Company", "Example IPP Co"])
        sheet.append(["Currency", "USD", "Synthetic data for learning only"])
        sheet.append(["Metric", "FY2023", "FY2024", "FY2025"])
        for row in rows:
            sheet.append(row)
        sheet.column_dimensions["A"].width = 30
        for column in "BCD":
            sheet.column_dimensions[column].width = 24
        sheet.freeze_panes = "B4"
    destination = Path(__file__).with_name("sample_financials.xlsx")
    workbook.save(destination)
    print(destination)


if __name__ == "__main__":
    main()
