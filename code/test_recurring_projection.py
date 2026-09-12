import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
sys.path.insert(0, 'code')
from data_loader import DataLoader

def detect_recurring_patterns(events_df, request_date_str):
    """
    Detects recurring income and expenses from past events (before request_date)
    and returns a list of recurring item definitions:
      [{'description': str, 'category': str, 'direction': str, 'amount': float, 'currency': str, 'day_of_month': int, 'flexibility': str}]
    """
    req_date = datetime.strptime(request_date_str, '%Y-%m-%d').date()
    past_events = events_df[
        (events_df['status'] == 'settled') & 
        (pd.to_datetime(events_df['event_date']) <= pd.to_datetime(request_date_str))
    ].copy()
    
    recurring_items = []
    
    for (desc, cat, direction), grp in past_events.groupby(['description', 'category', 'direction']):
        if len(grp) >= 2:  # Occurred at least twice in history
            dates = pd.to_datetime(grp['event_date']).sort_values()
            # Calculate day of month median
            days = [d.day for d in dates]
            med_day = int(np.median(days))
            latest_row = grp.sort_values('event_date').iloc[-1]
            amt = float(latest_row['amount']) if pd.notnull(latest_row['amount']) else 0.0
            flex = str(latest_row['flexibility']) if pd.notnull(latest_row['flexibility']) else 'fixed'
            
            recurring_items.append({
                'description': desc,
                'category': cat,
                'direction': direction,
                'amount': amt,
                'currency': latest_row['currency'],
                'day_of_month': med_day,
                'flexibility': flex,
                'sample_event_id': str(latest_row['event_id'])
            })
            
    return recurring_items

def main():
    dl = DataLoader('dataset')
    events_df = dl.get_user_events('user_02')
    rec = detect_recurring_patterns(events_df, '2025-08-05')
    print("=== Detected Recurring Items for user_02 ===")
    for r in rec:
        print(f"Desc: {r['description']} ({r['category']}) | Dir: {r['direction']} | Amt: {r['currency']} {r['amount']:,.2f} | Day: {r['day_of_month']}")

if __name__ == '__main__':
    main()
