import pandas as pd
import sys
sys.path.insert(0, 'code')
from data_loader import DataLoader

def debug_user(user_id):
    dl = DataLoader('dataset')
    events = dl.get_user_events(user_id)
    print(f"=== Events for {user_id} ===")
    for idx, row in events.iterrows():
        print(f"[{row['event_id']}] {row['event_date']} | Status: {row['status']} | Cat: {row['category']} | Dir: {row['direction']} | Amt: {row['currency']} {row['amount']} | Flex: {row['flexibility']} | Desc: {row['description']}")

if __name__ == '__main__':
    for u in ['user_01', 'user_06', 'user_11', 'user_21']:
        debug_user(u)
        print('='*70)
