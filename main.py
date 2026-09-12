import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))
from data_loader import DataLoader
from forecaster import FinancialForecaster

def run_agent(dataset_dir='dataset', input_csv='dataset/sample_requests.csv', output_csv='output.csv'):
    print(f"Initializing DataLoader with dataset from '{dataset_dir}'...")
    dl = DataLoader(dataset_dir)
    
    print("Initializing FinancialForecaster agent...")
    forecaster = FinancialForecaster(dl)
    
    print(f"Loading user requests from '{input_csv}'...")
    df_requests = pd.read_csv(input_csv)
    
    results = []
    for idx, row in df_requests.iterrows():
        req_id = row['request_id']
        user_id = row['user_id']
        print(f"Evaluating Request [{req_id}] for [{user_id}]...")
        
        prediction = forecaster.evaluate_request(row)
        
        # Ensure correct formatting of amount_safe_to_pay
        safe_amt = round(float(prediction['amount_safe_to_pay']), 2)
        if safe_amt.is_integer():
            safe_amt = float(int(safe_amt))
            
        results.append({
            'request_id': req_id,
            'user_id': user_id,
            'amount_safe_to_pay': safe_amt,
            'affordability_status': prediction['affordability_status'],
            'recommended_payment_method': prediction['recommended_payment_method'],
            'payment_plan': prediction['payment_plan'],
            'earliest_date_for_full_payment': prediction['earliest_date_for_full_payment'],
            'spending_changes_needed': prediction['spending_changes_needed'],
            'decision_explanation': prediction['decision_explanation']
        })
        
    df_out = pd.DataFrame(results)
    
    # Save output CSV
    df_out.to_csv(output_csv, index=False)
    print(f"Successfully processed {len(df_out)} requests. Results saved to '{output_csv}'.")

if __name__ == '__main__':
    dataset_dir = sys.argv[1] if len(sys.argv) > 1 else 'dataset'
    input_csv = sys.argv[2] if len(sys.argv) > 2 else os.path.join(dataset_dir, 'sample_requests.csv')
    output_csv = sys.argv[3] if len(sys.argv) > 3 else 'output.csv'
    
    run_agent(dataset_dir, input_csv, output_csv)
