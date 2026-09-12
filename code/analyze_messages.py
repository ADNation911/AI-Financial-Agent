import pandas as pd
import json
import re

def main():
    df_msg = pd.read_csv('dataset/messages.csv')
    print(f"Total messages: {len(df_msg)}")
    
    categories = {
        'salary_change': [],
        'cancellation': [],
        'date_change': [],
        'amount_amendment': [],
        'confirmation': [],
        'other': []
    }
    
    for idx, row in df_msg.iterrows():
        text = str(row['message_text'])
        text_lower = text.lower()
        
        entry = {
            'message_id': row['message_id'],
            'user_id': row['user_id'],
            'request_id': row['request_id'] if pd.notnull(row['request_id']) else None,
            'related_event_id': row['related_event_id'] if pd.notnull(row['related_event_id']) else None,
            'source_type': row['source_type'],
            'text': text
        }
        
        if 'gaji' in text_lower or 'salary' in text_lower or 'payroll' in text_lower or 'penggajian' in text_lower or 'gehalt' in text_lower:
            categories['salary_change'].append(entry)
        elif 'cancel' in text_lower or 'batal' in text_lower or 'stornier' in text_lower or 'void' in text_lower or 'discontinue' in text_lower:
            categories['cancellation'].append(entry)
        elif 'postpone' in text_lower or 'delay' in text_lower or 'tunda' in text_lower or 'reschedule' in text_lower or 'verschieb' in text_lower:
            categories['date_change'].append(entry)
        elif 'change' in text_lower or 'update' in text_lower or 'adjust' in text_lower or 'ubal' in text_lower or 'revise' in text_lower:
            categories['amount_amendment'].append(entry)
        elif 'confirm' in text_lower or 'settle' in text_lower or 'lunas' in text_lower:
            categories['confirmation'].append(entry)
        else:
            categories['other'].append(entry)
            
    for cat, items in categories.items():
        print(f"\n=== Category: {cat} ({len(items)} items) ===")
        for item in items[:5]:
            print(f"[{item['message_id']}] User: {item['user_id']} | Event: {item['related_event_id']} | Text: {item['text'][:100]}...")

if __name__ == '__main__':
    main()
