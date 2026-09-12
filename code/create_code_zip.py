import zipfile
import os
import sys

def create_code_zip(output_zip='code.zip'):
    root_dir = '.'
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'dataset', 'node_modules', '.gemini'}
    exclude_files = {'code.zip', 'output.csv', 'log.txt', '.DS_Store'}
    
    print(f"Creating submission package '{output_zip}'...")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Exclude specified directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                if file in exclude_files or file.endswith('.pyc') or file.endswith('.zip'):
                    continue
                    
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                print(f"  Adding {rel_path}")
                zipf.write(full_path, rel_path)
                
    print(f"Successfully created '{output_zip}'. File size: {os.path.getsize(output_zip) / 1024:.1f} KB")

if __name__ == '__main__':
    create_code_zip()
