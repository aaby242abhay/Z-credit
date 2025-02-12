import re
import fitz 
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

def extract_loan_details(text):
    loans = []
    account_blocks = re.split(r'RETAIL\s+Acct # \*{8}', text)[1:]
    
    for block in account_blocks:
        loan = {
            'sanction_amount': None,
            'interest_rate': None,
            'tenure': None,
            'date_opened': None,
            'type': None
        }
        
        sanction_match = re.search(r'Sanction Amount : Rs\.([\d,]+)', block)
        if sanction_match:
            loan['sanction_amount'] = float(sanction_match.group(1).replace(',', ''))
        
        rate_match = re.search(r'Interest Rate : ([\d.]+)', block)
        if rate_match:
            loan['interest_rate'] = float(rate_match.group(1))
        else:  
            if 'Personal Loan' in block:
                loan['interest_rate'] = 12.0  
            elif 'Credit Card' in block:
                loan['interest_rate'] = 40.0  
            elif 'Housing Loan' in block:
                loan['interest_rate'] = 8.5    
            
        tenure_match = re.search(r'Repayment Tenure : (\d+)', block)
        if tenure_match:
            loan['tenure'] = int(tenure_match.group(1))
        
        date_match = re.search(r'Date Opened : (\d{2}-\d{2}-\d{4})', block)
        if date_match:
            loan['date_opened'] = datetime.strptime(date_match.group(1), '%d-%m-%Y')
        
        type_match = re.search(r'Type : (.*?)\n', block)
        if type_match:
            loan['type'] = type_match.group(1).strip()
            
        if all(loan.values()): 
            loans.append(loan)
            
    return loans

def calculate_emi(principal, annual_rate, tenure_months):
    if annual_rate <= 0 or tenure_months <= 0:
        return 0
    monthly_rate = annual_rate / 1200  
    emi = (principal * monthly_rate * (1 + monthly_rate)**tenure_months) / \
          ((1 + monthly_rate)**tenure_months - 1)
    return emi

def calculate_income(loans):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)
    
    emi_calendar = defaultdict(float)
    
    for loan in loans:
        if not loan['date_opened'] or loan['date_opened'] > end_date:
            continue
            
        emi = calculate_emi(
            loan['sanction_amount'],
            loan['interest_rate'],
            loan['tenure']
        )
        
        current_date = loan['date_opened']
        months_added = 0
        
        while months_added < loan['tenure'] and current_date <= end_date:
            if current_date >= start_date:
                key = (current_date.year, current_date.month)
                emi_calendar[key] += emi
            days_in_month = calendar.monthrange(current_date.year, current_date.month)[1]
            current_date += timedelta(days=days_in_month)
            months_added += 1
    
    if not emi_calendar:
        return 0, 0
    
    max_emi = max(emi_calendar.values())
    estimated_income = max_emi / 0.4  
    return max_emi, estimated_income

def process_cibil_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    
    print(text)
    loans = extract_loan_details(text)
    max_emi, estimated_income = calculate_income(loans)
    
    print(f"Total Loans Found: {len(loans)}")
    for i, loan in enumerate(loans, 1):
        print(f"\nLoan {i}:")
        print(f"Type: {loan['type']}")
        print(f"Amount: ₹{loan['sanction_amount']:,.2f}")
        print(f"Rate: {loan['interest_rate']}%")
        print(f"Tenure: {loan['tenure']} months")
        print(f"Start Date: {loan['date_opened'].strftime('%b %Y')}")
    
    print("\n--- Financial Analysis ---")
    print(f"Maximum Monthly EMI in 3 years: ₹{max_emi:,.2f}")
    print(f"Estimated Monthly Income: ₹{estimated_income:,.2f}")
    print(f"Estimated Annual Income: ₹{estimated_income*12:,.2f}")

process_cibil_pdf("./CreditReports/cibil_3.pdf")