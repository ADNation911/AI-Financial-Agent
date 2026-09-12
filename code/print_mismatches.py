import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, 'code')
from data_loader import DataLoader
from forecaster import FinancialForecaster

def main():
    df_samples = pd.read_csv('dataset/sample_requests.csv')
    dl = DataLoader('dataset')
    forecaster = FinancialForecaster(dl)

    for idx, row in df_samples.iterrows():
        p = forecaster.evaluate_request(row)
        exp_e = str(row['earliest_date_for_full_payment']) if pd.notnull(row['earliest_date_for_full_payment']) else ''
        
        mismatches = []
        if p['affordability_status'] != row['affordability_status']: mismatches.append('status')
        if p['recommended_payment_method'] != row['recommended_payment_method']: mismatches.append('method')
        if p['payment_plan'] != row['payment_plan']: mismatches.append('plan')
        if p['earliest_date_for_full_payment'] != exp_e: mismatches.append('earliest')
        if p['spending_changes_needed'] != row['spending_changes_needed']: mismatches.append('spending')
        
        if mismatches:
            print(f"=== {row['request_id']} ({row['user_id']}) Mismatches: {mismatches} ===")
            print(f"   Req Date: {row['request_date']} | Req Amt: {row['requested_amount']} | Desired: {row['desired_completion_date']}")
            print(f"   PRED:     status={p['affordability_status']}, method={p['recommended_payment_method']}, safe={p['amount_safe_to_pay']}, plan={p['payment_plan']}, earliest={p['earliest_date_for_full_payment']}, spending={p['spending_changes_needed']}")
            print(f"   EXPECTED: status={row['affordability_status']}, method={row['recommended_payment_method']}, safe={row['amount_safe_to_pay']}, plan={row['payment_plan']}, earliest={exp_e}, spending={row['spending_changes_needed']}")
            print('-'*70)

if __name__ == '__main__':
    main()
