import pandas as pd
import sys
sys.path.insert(0, 'code')
from data_loader import DataLoader

def main():
    dl = DataLoader('dataset')
    users = ['user_01', 'user_05', 'user_06', 'user_11', 'user_13', 'user_18', 'user_19', 'user_21', 'user_23']
    
    out = []
    for u in users:
        prof = dl.get_user_profile(u)
        events = dl.get_user_events(u)
        out.append(f"=== USER: {u} ===")
        out.append(f"Profile: Curr={prof['home_currency']}, StartBal={prof['current_available_balance']}, MinBal={prof['minimum_balance_to_keep']}")
        out.append(f"Considered Methods: {prof['payment_methods_user_will_consider']}")
        out.append(f"Reducible: {prof['expense_categories_user_is_willing_to_reduce']} | Stoppable: {prof['expense_categories_user_is_willing_to_stop']}")
        out.append("Events:")
        for idx, r in events.iterrows():
            out.append(f"  [{r['event_id']}] Date:{r['event_date']} Settled:{r['settlement_date']} Status:{r['status']} Cat:{r['category']} Dir:{r['direction']} Amt:{r['currency']} {r['amount']} Flex:{r['flexibility']} Desc:{r['description']}")
        out.append('-'*70)
        
    with open('code/events_debug.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print("Saved to code/events_debug.txt")

if __name__ == '__main__':
    main()
