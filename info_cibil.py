import re
import fitz 
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def extract_loan_details(text):
    loans = []
    account_blocks = re.split(r'RETAIL\s+Acct # \*{8}', text)[1:]
    
    for block in account_blocks:
        loan = {
            'sanction_amount': 0.0,
            'interest_rate': 0.0,
            'tenure': 0,
            'date_opened': None,
            'type': 'Unknown',
            'days_past_due': 0,
            'asset_classification': 'Standard',
            'default_history': [],
            'write_off_amount': 0.0
        }
        
        type_match = re.search(r'Type : (.*?)(\n|$)', block)
        if type_match:
            loan['type'] = type_match.group(1).strip() or 'Unknown'

        sanction_match = re.search(r'Sanction Amount : Rs\.([\d,]+)', block)
        if sanction_match:
            try:
                loan['sanction_amount'] = float(sanction_match.group(1).replace(',', ''))
            except:
                pass

        rate_match = re.search(r'Interest Rate : ([\d.]+)', block)
        if rate_match:
            try:
                loan['interest_rate'] = float(rate_match.group(1))
            except:
                pass

        tenure_match = re.search(r'Repayment Tenure : (\d+)', block)
        if tenure_match:
            try:
                loan['tenure'] = int(tenure_match.group(1))
            except:
                pass

        date_match = re.search(r'Date Opened : (\d{2}-\d{2}-\d{4})', block)
        if date_match:
            try:
                loan['date_opened'] = datetime.strptime(date_match.group(1), '%d-%m-%Y')
            except:
                loan['date_opened'] = None

        history_matches = re.finditer(r'(\d{2} - \d{2})\s+(\d{3})', block)
        for match in history_matches:
            period = match.group(1)
            status = match.group(2)
            if status != '000':
                loan['default_history'].append((period, status))

        loans.append(loan)
            
    return loans

def plot_emi_timeline(emi_calendar):
    if not emi_calendar:
        print("No EMI data to plot")
        return

    end_date = datetime.now()
    start_date = end_date - timedelta(days=36*30)
    
    dates = []
    emis = []
    
    current = start_date
    while current <= end_date:
        key = (current.year, current.month)
        dates.append(current)
        emis.append(emi_calendar.get(key, 0))
        days_in_month = calendar.monthrange(current.year, current.month)[1]
        current += timedelta(days=days_in_month)
    
    plt.figure(figsize=(12, 6))
    plt.bar(dates, emis, width=25, color='skyblue')
    plt.title('Monthly EMI Payments Over Last 3 Years')
    plt.xlabel('Month')
    plt.ylabel('Total EMI (₹)')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0

def calculate_emi(principal, annual_rate, tenure_months):
    principal = safe_float(principal)
    annual_rate = safe_float(annual_rate)
    tenure_months = int(safe_float(tenure_months))
    
    if tenure_months <= 0 or annual_rate <= 0:
        return 0.0
    
    monthly_rate = annual_rate / 1200
    try:
        emi = (principal * monthly_rate * (1 + monthly_rate)**tenure_months) / \
              ((1 + monthly_rate)**tenure_months - 1)
    except:
        return 0.0
    return emi

def calculate_income(loans):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)
    
    emi_calendar = defaultdict(float)
    
    for loan in loans:
        principal = loan.get('sanction_amount', 0) or 0
        rate = loan.get('interest_rate', 0) or 0
        tenure = loan.get('tenure', 0) or 0
        start_date_loan = loan.get('date_opened') or end_date
        
        emi = calculate_emi(principal, rate, tenure)
        
        current_date = start_date_loan
        months_added = 0
        
        while months_added < tenure and current_date <= end_date:
            if current_date >= start_date:
                key = (current_date.year, current_date.month)
                emi_calendar[key] += emi
            try:
                days_in_month = calendar.monthrange(current_date.year, current_date.month)[1]
                current_date += timedelta(days=days_in_month)
                months_added += 1
            except:
                break
    
    max_emi = max(emi_calendar.values(), default=0)
    estimated_income = max_emi / 0.4 if max_emi else 0
    return max_emi, estimated_income, emi_calendar  

def process_cibil_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    
    loans = extract_loan_details(text)
    max_emi, estimated_income, emi_calendar = calculate_income(loans)
    
    print(f"Total Loans Found: {len(loans)}")
    for i, loan in enumerate(loans, 1):
        print(f"\nLoan {i}:")
        print(f"Type: {loan.get('type', 'Unknown')}")
        print(f"Amount: ₹{loan.get('sanction_amount', 0):,.2f}")
        print(f"Rate: {loan.get('interest_rate', 0)}%")
        print(f"Tenure: {loan.get('tenure', 0)} months")
        if loan.get('date_opened'):
            print(f"Start Date: {loan['date_opened'].strftime('%b %Y')}")
        else:
            print("Start Date: Unknown")
    
    print("\n--- Financial Analysis ---")
    print(f"Maximum Monthly EMI in 3 years: ₹{max_emi:,.2f}")
    print(f"Estimated Monthly Income: ₹{estimated_income:,.2f}")
    print(f"Estimated Annual Income: ₹{estimated_income*12:,.2f}")
    
    plot_emi_timeline(emi_calendar)

process_cibil_pdf("./CreditReports/cibil_3.pdf")