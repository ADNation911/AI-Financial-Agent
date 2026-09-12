import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

sys.path.insert(0, 'code')
from data_loader import DataLoader
from forecaster import FinancialForecaster

def test():
    dl = DataLoader('dataset')
    forecaster = FinancialForecaster(dl)
    df_samples = pd.read_csv('dataset/sample_requests.csv')

    m_status, m_method, m_plan, m_earliest, m_spending = 0, 0, 0, 0, 0
    safe_diffs = []

    for idx, row in df_samples.iterrows():
        p = forecaster.evaluate_request(row)
        if p['affordability_status'] == row['affordability_status']: m_status += 1
        if p['recommended_payment_method'] == row['recommended_payment_method']: m_method += 1
        if p['payment_plan'] == row['payment_plan']: m_plan += 1
        exp_e = str(row['earliest_date_for_full_payment']) if pd.notnull(row['earliest_date_for_full_payment']) else ''
        if p['earliest_date_for_full_payment'] == exp_e: m_earliest += 1
        if p['spending_changes_needed'] == row['spending_changes_needed']: m_spending += 1
        safe_diffs.append(abs(p['amount_safe_to_pay'] - float(row['amount_safe_to_pay'])))

    print(f"Status:           {m_status}/25 ({m_status/25*100:.1f}%)")
    print(f"Method:           {m_method}/25 ({m_method/25*100:.1f}%)")
    print(f"Plan:             {m_plan}/25 ({m_plan/25*100:.1f}%)")
    print(f"Earliest Date:    {m_earliest}/25 ({m_earliest/25*100:.1f}%)")
    print(f"Spending Changes: {m_spending}/25 ({m_spending/25*100:.1f}%)")
    print(f"Safe Amt MAE:     {np.mean(safe_diffs):.2f}")

if __name__ == '__main__':
    test()
