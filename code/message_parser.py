import pandas as pd
import re
from datetime import datetime

def parse_all_messages(messages_csv_path='dataset/messages.csv'):
    """
    Parses messages.csv and extracts structured financial facts per user and per event.
    Returns:
      user_salary_updates: dict mapping user_id -> list of {'effective_date': 'YYYY-MM-DD', 'new_salary': float, 'currency': str}
      unconfirmed_gig_users: set of user_id whose gig payouts are pending/unconfirmed
      ended_employment_users: set of user_id whose employment has ended
      rent_increase_users: set of user_id whose rent increases by 12%
      childcare_users: set of user_id with new recurring childcare payment
      event_overrides: dict mapping event_id -> {'cancelled': bool, 'new_amount': float, 'new_date': str}
    """
    df_msg = pd.read_csv(messages_csv_path)
    
    user_salary_updates = {}
    unconfirmed_gig_users = set()
    ended_employment_users = set()
    rent_increase_users = set()
    childcare_users = set()
    event_overrides = {}
    
    for idx, row in df_msg.iterrows():
        user_id = str(row['user_id'])
        rel_event = str(row['related_event_id']) if pd.notnull(row['related_event_id']) else None
        text = str(row['message_text'])
        text_lower = text.lower()
        sent_at = str(row['sent_at'])[:10] if pd.notnull(row['sent_at']) else '2020-01-01'
        
        # 1. Unconfirmed Gig Payouts
        gig_keywords = ['quickcrew', 'taskloop', 'ridegrid', 'workdash', 'shiftpay', 'tasksprint']
        if any(g in text_lower for g in gig_keywords):
            if any(p in text_lower for p in ['still pending', 'not withdrawable', 'tertunda', 'belum dapat ditarik', 'can change']):
                unconfirmed_gig_users.add(user_id)
                
        # 2. Ended Employment
        if any(e in text_lower for e in ['employment has ended', 'seasonal contract has ended', 'hubungan kerja Anda telah berakhir', 'kontrak musiman saat ini telah berakhir', 'record has ended', 'telah berakhir']):
            ended_employment_users.add(user_id)

        # 3. Rent Increase
        if 'rent' in text_lower or 'sewa' in text_lower or 'lease' in text_lower:
            if any(r in text_lower for r in ['increases monthly rent by 12%', 'menaikkan biaya sewa bulanan sebesar 12%']):
                rent_increase_users.add(user_id)

        # 4. Childcare Expenses
        if 'childcare' in text_lower or 'anak' in text_lower:
            if 'recurring childcare' in text_lower or 'new recurring childcare' in text_lower:
                childcare_users.add(user_id)

        # 5. Salary / payroll updates
        if any(k in text_lower for k in ['salary', 'gaji', 'payroll', 'gehalt', 'penggajian']):
            # Check if bonus/commission is pending review (do not count as salary update)
            if any(b in text_lower for b in ['bonus', 'commission', 'komisi']) and any(p in text_lower for p in ['pending', 'subject to', 'belum disetujui']):
                # Ignore pending bonus/commission update
                pass
            else:
                m_amt = re.search(r'(?:INR|IDR|ZAR|USD|EUR|Rs\.?|Rp\.?|\$|€)\s*([0-9]+(?:[,\.][0-9]+)?)', text, re.IGNORECASE)
                if not m_amt:
                    m_amt = re.search(r'([0-9]+(?:[,\.][0-9]+)?)\s*(?:INR|IDR|ZAR|USD|EUR)', text, re.IGNORECASE)
                    
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

        # 6. Check for event-specific cancellations or amendments
        if rel_event:
            if rel_event not in event_overrides:
                event_overrides[rel_event] = {'cancelled': False, 'new_amount': None, 'new_date': None}
                
            if any(k in text_lower for k in ['cancel', 'batal', 'stornier', 'void', 'discontinue', 'terminate', 'stopped']):
                event_overrides[rel_event]['cancelled'] = True
                
            m_amt = re.search(r'(?:new amount|adjusted to|revised to|reduced to|increased to|total is)\s*(?:INR|IDR|ZAR|USD|EUR|Rs\.?|Rp\.?|\$|€)?\s*([0-9]+(?:[,\.][0-9]+)?)', text, re.IGNORECASE)
            if m_amt:
                try:
                    event_overrides[rel_event]['new_amount'] = float(m_amt.group(1).replace(',', ''))
                except ValueError:
                    pass

    return user_salary_updates, unconfirmed_gig_users, ended_employment_users, rent_increase_users, childcare_users, event_overrides

if __name__ == '__main__':
    salaries, gig_u, ended_u, rent_u, child_u, overrides = parse_all_messages()
    print(f"Extracted salary updates for {len(salaries)} users.")
    print(f"Gig unconfirmed users: {gig_u}")
    print(f"Ended employment users: {ended_u}")
    print(f"Rent increase users: {rent_u}")
    print(f"Childcare users: {child_u}")
    print(f"Extracted event overrides for {len(overrides)} events.")
