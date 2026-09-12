import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_loader import DataLoader
from forecaster import FinancialForecaster

def evaluate_sample_requests(sample_csv_path='dataset/sample_requests.csv'):
    if not os.path.exists(sample_csv_path):
        sample_csv_path = os.path.join('..', sample_csv_path)
        
    df_samples = pd.read_csv(sample_csv_path)
    dl = DataLoader(dataset_dir=os.path.dirname(sample_csv_path) if '/' in sample_csv_path or '\\' in sample_csv_path else 'dataset')
    forecaster = FinancialForecaster(dl)
    
    total = len(df_samples)
    correct_status = 0
    correct_method = 0
    correct_plan = 0
    correct_earliest_date = 0
    correct_spending_changes = 0
    safe_amount_diffs = []
    
    print(f"=== Running Evaluation on {total} Sample Requests ===")
    
    for idx, row in df_samples.iterrows():
        req_id = row['request_id']
        pred = forecaster.evaluate_request(row)
        
        expected_status = str(row['affordability_status'])
        expected_method = str(row['recommended_payment_method'])
        expected_plan = str(row['payment_plan'])
        expected_earliest = str(row['earliest_date_for_full_payment']) if pd.notnull(row['earliest_date_for_full_payment']) else ''
        expected_spending = str(row['spending_changes_needed'])
        expected_safe_amt = float(row['amount_safe_to_pay'])
        
        pred_status = str(pred['affordability_status'])
        pred_method = str(pred['recommended_payment_method'])
        pred_plan = str(pred['payment_plan'])
        pred_earliest = str(pred['earliest_date_for_full_payment'])
        pred_spending = str(pred['spending_changes_needed'])
        pred_safe_amt = float(pred['amount_safe_to_pay'])
        
        is_status_ok = (pred_status == expected_status)
        is_method_ok = (pred_method == expected_method)
        is_plan_ok = (pred_plan == expected_plan)
        is_earliest_ok = (pred_earliest == expected_earliest)
        is_spending_ok = (pred_spending == expected_spending)
        amt_diff = abs(pred_safe_amt - expected_safe_amt)
        
        if is_status_ok: correct_status += 1
        if is_method_ok: correct_method += 1
        if is_plan_ok: correct_plan += 1
        if is_earliest_ok: correct_earliest_date += 1
        if is_spending_ok: correct_spending_changes += 1
        safe_amount_diffs.append(amt_diff)
        
        print(f"[{req_id}] User: {row['user_id']} | Req Amt: {row['requested_amount']}")
        print(f"   Status: Pred={pred_status} | Exp={expected_status} ({'OK' if is_status_ok else 'MISMATCH'})")
        print(f"   Method: Pred={pred_method} | Exp={expected_method} ({'OK' if is_method_ok else 'MISMATCH'})")
        print(f"   Plan:   Pred={pred_plan} | Exp={expected_plan} ({'OK' if is_plan_ok else 'MISMATCH'})")
        print(f"   Earliest Date: Pred={pred_earliest} | Exp={expected_earliest} ({'OK' if is_earliest_ok else 'MISMATCH'})")
        print(f"   Safe Amt: Pred={pred_safe_amt} | Exp={expected_safe_amt} (Diff={amt_diff:.2f})")
        print('-'*60)
        
    print("\n" + "="*60)
    print("=== SUMMARY METRICS ===")
    print(f"Affordability Status Accuracy:       {correct_status}/{total} ({correct_status/total*100:.1f}%)")
    print(f"Payment Method Accuracy:             {correct_method}/{total} ({correct_method/total*100:.1f}%)")
    print(f"Payment Plan Accuracy:               {correct_plan}/{total} ({correct_plan/total*100:.1f}%)")
    print(f"Earliest Full Date Accuracy:         {correct_earliest_date}/{total} ({correct_earliest_date/total*100:.1f}%)")
    print(f"Spending Changes Accuracy:           {correct_spending_changes}/{total} ({correct_spending_changes/total*100:.1f}%)")
    print(f"Mean Absolute Safe Amount Diff:      {np.mean(safe_amount_diffs):.2f}")
    print("="*60)

if __name__ == '__main__':
    evaluate_sample_requests()
