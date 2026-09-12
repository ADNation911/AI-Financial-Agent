import pandas as pd
import json
import sys
import os

sys.path.insert(0, 'code')
from data_loader import DataLoader
from forecaster import FinancialForecaster

def main():
    df_samples = pd.read_csv('dataset/sample_requests.csv')
    dl = DataLoader('dataset')
    forecaster = FinancialForecaster(dl)

    out = []
    for idx, row in df_samples.iterrows():
        pred = forecaster.evaluate_request(row)
        out.append(f"=== {row['request_id']} ({row['user_id']}) ===")
        out.append(f"Request Date: {row['request_date']} | Type: {row['request_type']} | Amt: {row['requested_amount']} | Desired: {row['desired_completion_date']}")
        out.append(f"PRED:     status={pred['affordability_status']}, method={pred['recommended_payment_method']}, safe_amt={pred['amount_safe_to_pay']}, plan={pred['payment_plan']}, earliest={pred['earliest_date_for_full_payment']}, spending={pred['spending_changes_needed']}")
        out.append(f"EXPECTED: status={row['affordability_status']}, method={row['recommended_payment_method']}, safe_amt={row['amount_safe_to_pay']}, plan={row['payment_plan']}, earliest={row['earliest_date_for_full_payment']}, spending={row['spending_changes_needed']}")
        out.append(f"EXPLANATION PRED: {pred['decision_explanation']}")
        out.append(f"EXPLANATION EXP:  {row['decision_explanation']}")
        out.append('-'*70)

    out_file = 'code/eval_debug_out.txt'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f"Written debug log to {out_file}")

if __name__ == '__main__':
    main()
