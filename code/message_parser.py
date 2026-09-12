import pandas as pd
import re
from datetime import datetime

def parse_all_messages(messages_csv_path='dataset/messages.csv'):
    """
    Parses messages.csv and extracts structured financial facts per user and per event.
    Returns:
      user_salary_updates: dict mapping user_id -> list of {'effective_date': 'YYYY-MM-DD', 'new_salary': float, 'currency': str}
      event_overrides: dict mapping event_id -> {'cancelled': bool, 'new_amount': float, 'new_date': str}
    """
    df_msg = pd.read_csv(messages_csv_path)
    
    user_salary_updates = {}
    event_overrides = {}
    
    for idx, row in df_msg.iterrows():
        user_id = str(row['user_id'])
        rel_event = str(row['related_event_id']) if pd.notnull(row['related_event_id']) else None
        text = str(row['message_text'])
        text_lower = text.lower()
        sent_at = str(row['sent_at'])[:10] if pd.notnull(row['sent_at']) else '2020-01-01'
        
        # 1. Check for salary / payroll updates
        if 'salary' in text_lower or 'gaji' in text_lower or 'payroll' in text_lower or 'gehalt' in text_lower or 'penggajian' in text_lower:
            # Extract currency and amount
            # E.g. "IDR 42750000", "EUR 3,500", "ZAR 45000", "INR 120000", "$4500"
            m_amt = re.search(r'(?:INR|IDR|ZAR|USD|EUR|Rs\.?|Rp\.?|\$|€)\s*([0-9]+(?:[,\.][0-9]+)?)', text, re.IGNORECASE)
            if not m_amt:
                m_amt = re.search(r'([0-9]+(?:[,\.][0-9]+)?)\s*(?:INR|IDR|ZAR|USD|EUR)', text, re.IGNORECASE)
                
            # Extract effective date (YYYY-MM-DD or DD Month YYYY or Month YYYY)
            m_date = re.search(r'\b(20[2-3][0-9]-[0-1][0-9]-[0-3][0-9])\b', text)
            effective_date = m_date.group(1) if m_date else sent_at
            
            if m_amt:
                amt_str = m_amt.group(1).replace(',', '')
                try:
                    salary_val = float(amt_str)
                    if salary_val > 100:  # Valid salary
                        if user_id not in user_salary_updates:
                            user_salary_updates[user_id] = []
                        user_salary_updates[user_id].append({
                            'sent_at': sent_at,
                            'effective_date': effective_date,
                            'new_salary': salary_val,
                            'message_id': row['message_id']
                        })
                except ValueError:
                    pass

        # 2. Check for event-specific cancellations or amendments
        if rel_event:
            if rel_event not in event_overrides:
                event_overrides[rel_event] = {'cancelled': False, 'new_amount': None, 'new_date': None}
                
            # Check cancellation / void / stop / disconnect
            if any(k in text_lower for k in ['cancel', 'batal', 'stornier', 'void', 'discontinue', 'terminate', 'stopped']):
                event_overrides[rel_event]['cancelled'] = True
                
            # Check new amount
            m_amt = re.search(r'(?:new amount|adjusted to|revised to|reduced to|increased to|total is)\s*(?:INR|IDR|ZAR|USD|EUR|Rs\.?|Rp\.?|\$|€)?\s*([0-9]+(?:[,\.][0-9]+)?)', text, re.IGNORECASE)
            if m_amt:
                try:
                    event_overrides[rel_event]['new_amount'] = float(m_amt.group(1).replace(',', ''))
                except ValueError:
                    pass

    return user_salary_updates, event_overrides

if __name__ == '__main__':
    salaries, overrides = parse_all_messages()
    print(f"Extracted salary updates for {len(salaries)} users.")
    print(f"Extracted event overrides for {len(overrides)} events.")
