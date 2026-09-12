import os
import glob
import json
import re
import pandas as pd
import easyocr

def main():
    print("Loading EasyOCR reader...")
    reader = easyocr.Reader(['en'], gpu=False)
    img_dir = 'dataset/media/images'
    results = {}
    
    df_img = pd.read_csv('dataset/images.csv')
    
    for path in sorted(glob.glob(os.path.join(img_dir, '*.png'))):
        img_name = os.path.basename(path)
        img_id = os.path.splitext(img_name)[0]
        print(f"Processing {img_name}...")
        ocr_res = reader.readtext(path, detail=0)
        full_text = ' '.join(ocr_res)
        
        match_row = df_img[df_img['image_id'] == img_id]
        rel_event = match_row['related_event_id'].values[0] if len(match_row) > 0 else None
        user_id = match_row['user_id'].values[0] if len(match_row) > 0 else None
        req_id = match_row['request_id'].values[0] if len(match_row) > 0 else None
        
        results[img_id] = {
            'image_id': img_id,
            'user_id': str(user_id) if pd.notnull(user_id) else None,
            'request_id': str(req_id) if pd.notnull(req_id) else None,
            'related_event_id': str(rel_event) if pd.notnull(rel_event) else None,
            'raw_text': full_text
        }
        print(f"  [{img_id}] -> Event: {rel_event} | Text snippet: {full_text[:80]}")

    os.makedirs('code', exist_ok=True)
    out_path = 'code/ocr_results.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Successfully saved OCR results for {len(results)} images to {out_path}")

if __name__ == '__main__':
    main()
