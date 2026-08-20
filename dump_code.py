import os
import json

def gather_code():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(project_dir, 'all_code.txt')
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(project_dir):
            if any(x in root for x in ['node_modules', 'venv', '__pycache__', '.git', 'dist']):
                continue
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.html', '.css', '.json', '.md', '.txt')):
                    if file in ['all_code.txt', 'package-lock.json', 'implementationPaper.txt', 'implementationPaper_updated.txt', 'filelist.txt', 'outbreaks_v2_backup_before_migration.json', 'diseases_backup.json', 'outbreaks_backup.json', 'raw_articles_backup.json']:
                        continue
                    
                    filepath = os.path.join(root, file)
                    outfile.write(f"\n\n{'='*80}\n")
                    outfile.write(f"FILE: {os.path.relpath(filepath, project_dir)}\n")
                    outfile.write(f"{'='*80}\n\n")
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"Error reading file: {e}\n")

if __name__ == '__main__':
    gather_code()
