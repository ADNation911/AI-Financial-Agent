import json
import re
import pandas as pd

def extract_amount_from_text(text, event_type, description, category):
    """
    Extract exact monetary amount from OCR raw text based on keywords like Total, Amount, Paid, Net, Salary, etc.
    """
    text_clean = text.replace(',', '')
    
    # Common invoice/receipt amount patterns
    # Pattern 1: Total / Net Amount / Total Paid / Grand Total / Amount Paid / Total Amount
    patterns = [
        r'(?:total|net amount|total paid|grand total|amount paid|total amount|subtotal|amount|charged amount|paid|salary|net pay|total due)\s*[:=]?\s*(?:INR|IDR|ZAR|USD|EUR|Rs\.?|Rp\.?|\$|€)?\s*([0-9]+(?:\.[0-9]+)?)',
        r'(?:INR|IDR|ZAR|USD|EUR|Rs\.?|Rp\.?|\$|€)\s*([0-9]+(?:\.[0-9]+)?)',
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:INR|IDR|ZAR|USD|EUR)'
    ]
    
    for pat in patterns:
        matches = re.findall(pat, text_clean, re.IGNORECASE)
        if matches:
            # Pick highest reasonable number or exact match
            nums = [float(m) for m in matches if float(m) > 0]
            if nums:
                return nums[0]
                
    # Fallback: extract all numbers with decimals or 3+ digits
    nums = re.findall(r'\b[0-9]+(?:\.[0-9]+)?\b', text_clean)
    nums = [float(n) for n in nums if float(n) > 10]
    if nums:
        return max(nums)
        
    return None

def main():
    with open('code/ocr_results.json', 'r', encoding='utf-8') as f:
        ocr_data = json.load(f)
        
    df_events = pd.read_csv('dataset/financial_events.csv')
    df_images = pd.read_csv('dataset/images.csv')
    
    image_amounts = {}
    
    print("=== Image Amount Extractions ===")
    for img_id, info in ocr_data.items():
        rel_event = info['related_event_id']
        raw_text = info['raw_text']
        
        event_row = df_events[df_events['event_id'] == rel_event]
        if len(event_row) > 0:
            ev = event_row.iloc[0]
            amt = extract_amount_from_text(raw_text, ev['event_type'], ev['description'], ev['category'])
            image_amounts[rel_event] = amt
            print(f"Image: {img_id} | Event: {rel_event} | Desc: {ev['description']} | User: {ev['user_id']} | Extracted Amount: {amt}")
            print(f"   Raw text: {raw_text[:120]}...\n")
            
    with open('code/extracted_image_amounts.json', 'w', encoding='utf-8') as f:
        json.dump(image_amounts, f, indent=2)

if __name__ == '__main__':
    main()
