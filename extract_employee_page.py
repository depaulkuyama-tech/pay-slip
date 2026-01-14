from pypdf import PdfReader, PdfWriter
import os
from datetime import datetime, timedelta

# ------------------ CONFIG ------------------
FOLDER = r"C:\Users\Paul.Kuyama\Desktop\Pay Slip"
OUTPUT_DIR = os.path.join(FOLDER, "Employee_Payslips")
MASTER_PDF_DIR = os.path.join(FOLDER, "Master_PDFs")  # Put all 26 PDFs here

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------ FUNCTIONS ------------------
def generate_pay_periods(start_date="07-01-2026", num_periods=26):
    """Generate 26 fortnightly pay periods starting from start_date."""
    first_date = datetime.strptime(start_date, "%d-%m-%Y")
    periods = []
    for i in range(num_periods):
        pay_date = first_date + timedelta(days=i*14)
        filename = pay_date.strftime("%d-%b-%Y") + ".pdf"
        filepath = os.path.join(MASTER_PDF_DIR, filename)
        periods.append({
            "pay_date": pay_date.strftime("%d-%b-%Y"),
            "filepath": filepath,
            "available": os.path.exists(filepath)
        })
    return periods

def extract_payslip(employee_number, master_pdf_path, pay_date_str):
    """Extract employee page from a master PDF for a given pay date."""
    if not os.path.exists(master_pdf_path):
        return None

    reader = PdfReader(master_pdf_path)
    writer = PdfWriter()
    found = False

    for page_number, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and employee_number in text:
            writer.add_page(page)
            found = True
            print(f"Employee {employee_number} found on page {page_number + 1} of {pay_date_str}")

    if not found:
        return None

    output_pdf = os.path.join(OUTPUT_DIR, f"employee_{employee_number}_{pay_date_str}.pdf")
    with open(output_pdf, "wb") as f:
        writer.write(f)
    return output_pdf

# ------------------ MAIN SCRIPT ------------------
employee_number = input("Enter employee number (e.g. 13616733): ").strip()

pay_periods = generate_pay_periods()

for period in pay_periods:
    if not period["available"]:
        print(f"Pay slip for {period['pay_date']} not available yet.")
        continue

    output_file = extract_payslip(employee_number, period["filepath"], period["pay_date"])
    if output_file:
        print(f"Extracted payslip saved: {output_file}")
    else:
        print(f"Employee {employee_number} not found in pay slip for {period['pay_date']}")
