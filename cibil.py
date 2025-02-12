import pdfplumber
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def extract_loan_details(pdf_path):
    loans = []
    print(f"Processing PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found.")
        return loans
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                loan_matches = re.findall(r"Sanction Amount : Rs\.([\d,]+)", text)
                emi_matches = re.findall(r"Payment Amount : Rs\.([\d,]+)", text)
                dates = re.findall(r"Date Reported : (\d{2}-\d{2}-\d{4})", text)
                bank_matches = re.findall(r"Institution : (.+)", text)  
                
                for loan, emi, date, institution in zip(loan_matches, emi_matches, dates, bank_matches):
                    loan_amount = int(loan.replace(",", ""))
                    emi_amount = int(emi.replace(",", ""))
                    is_bank_loan = "BANK" in institution.upper()
                    loans.append((date, loan_amount, emi_amount, is_bank_loan))
    return loans


def estimate_income(loans):
    income_estimates = []
    max_emi = 0
    max_emi_income = (None, 0, 0, 0, 0)  
    
    for date, loan, emi, is_bank_loan in loans:
        min_income = emi / 0.5  
        max_income = emi / 0.4  
        income_estimates.append((date, loan, emi, min_income, max_income))
        
        if emi > max_emi and is_bank_loan:
            max_emi = emi
            max_emi_income = (date, loan, emi, min_income, max_income)
    
    df = pd.DataFrame(income_estimates, columns=["Date", "Loan Amount", "EMI", "Min Income", "Max Income"])
    return df, max_emi_income

def visualize_data(df):
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
    df = df.sort_values("Date")
    
    if len(df) > 100:
        print("Too many data points, skipping visualization.")
        return
    
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=df["Date"], y=df["Max Income"], label="Max Estimated Income")
    sns.lineplot(x=df["Date"], y=df["Min Income"], label="Min Estimated Income")
    plt.xlabel("Date")
    plt.ylabel("Estimated Income (Rs)")
    plt.title("Estimated Income Over Time")
    plt.legend()
    plt.xticks(rotation=45)
    plt.show()
    
if __name__ == "__main__":
    pdf_files = ["./CreditReports/cibil_3.pdf"] 
    all_loans = []
    
    for pdf in pdf_files:
        loans = extract_loan_details(pdf)
        all_loans.extend(loans)
    
    df, max_emi_income = estimate_income(all_loans)
    print(df)
    
    if max_emi_income[0] is None:
        print("No valid max EMI found from bank loans.")
    else:
        print(f"Max EMI Info: Date - {max_emi_income[0]}, Loan - {max_emi_income[1]}, EMI - {max_emi_income[2]}, Min Income - {max_emi_income[3]}, Max Income - {max_emi_income[4]}")
    
    visualize_data(df)
