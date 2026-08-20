import os
import ast
import json
import re

# We will generate a very detailed Implementation_Paper.md
OUTPUT_FILE = "Implementation_Paper.md"

def analyze_backend(base_path):
    modules = []
    apis = []
    db_schema = {}
    
    for root, dirs, files in os.walk(base_path):
        if 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                try:
                    tree = ast.parse(content)
                    funcs = []
                    classes = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            funcs.append({
                                'name': node.name,
                                'args': [a.arg for a in node.args.args],
                                'doc': ast.get_docstring(node)
                            })
                            # Check if it's a Flask route
                            for dec in node.decorator_list:
                                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == 'route':
                                    url = dec.args[0].value if dec.args else "Unknown"
                                    methods = ["GET"]
                                    for kw in dec.keywords:
                                        if kw.arg == 'methods':
                                            methods = [el.value for el in kw.value.elts]
                                    apis.append({
                                        'url': url,
                                        'methods': methods,
                                        'function': node.name,
                                        'doc': ast.get_docstring(node),
                                        'file': file
                                    })
                        elif isinstance(node, ast.ClassDef):
                            classes.append({
                                'name': node.name,
                                'doc': ast.get_docstring(node)
                            })
                    
                    modules.append({
                        'file': os.path.relpath(filepath, base_path),
                        'functions': funcs,
                        'classes': classes,
                        'content_length': len(content)
                    })
                except Exception as e:
                    pass
    return modules, apis

def analyze_frontend(base_path):
    components = []
    for root, dirs, files in os.walk(base_path):
        if 'node_modules' in root or 'dist' in root:
            continue
        for file in files:
            if file.endswith(('.jsx', '.js')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic regex to find components/functions
                funcs = re.findall(r'(?:const|function)\s+([A-Z]\w+)\s*=?\s*(?:\([^)]*\))?\s*=>?', content)
                api_calls = re.findall(r'(axios|fetch)\.?(get|post|put|delete)?\([\'"`](.*?)[\'"`]', content)
                
                components.append({
                    'file': os.path.relpath(filepath, base_path),
                    'exports': funcs,
                    'api_calls': api_calls,
                    'content_length': len(content)
                })
    return components

def generate_markdown():
    # Gather data
    backend_modules, apis = analyze_backend('backend')
    frontend_modules = analyze_frontend('frontend')
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Implementation Paper: MediScope\\n\\n")
        f.write("## 1. Title Page\\nMediScope: Disease Outbreak Monitoring System\\n\\n")
        
        f.write("## 2. Certificate\\nThis is to certify that this project is the bona fide work...\\n\\n")
        f.write("## 3. Acknowledgement\\nWe would like to thank our mentors...\\n\\n")
        f.write("## 4. Abstract\\nMediScope is a comprehensive system designed to track, analyze, and predict disease outbreaks globally...\\n\\n")
        f.write("## 5. Table of Contents\\n(Auto-generated)\\n\\n")
        
        f.write("## 6. Introduction\\nProvides global surveillance...\\n\\n")
        f.write("## 14. Technology Stack\\n- **Backend**: Python, Flask, MongoDB\\n- **Frontend**: React, Vite, TailwindCSS\\n- **Machine Learning**: Scikit-Learn (NLP, Classification)\\n\\n")
        
        f.write("## 23. API Documentation\\n")
        for api in apis:
            f.write(f"### Endpoint: {api['url']}\\n")
            f.write(f"- **Methods**: {', '.join(api['methods'])}\\n")
            f.write(f"- **Handler**: `{api['function']}`\\n")
            f.write(f"- **Description**: {api['doc'] or 'No description provided.'}\\n\\n")
            
        f.write("## 24. Backend Modules\\n")
        for mod in backend_modules:
            f.write(f"### File: {mod['file']}\\n")
            f.write(f"**Functions:**\\n")
            for func in mod['functions']:
                f.write(f"- `{func['name']}({', '.join(func['args'])})`: {func['doc'][:100] if func['doc'] else 'No docstring'}\\n")
            f.write(f"**Classes:**\\n")
            for cls in mod['classes']:
                f.write(f"- `{cls['name']}`: {cls['doc'][:100] if cls['doc'] else 'No docstring'}\\n")
            f.write("\\n")

        f.write("## 25. Frontend Modules\\n")
        for mod in frontend_modules:
            f.write(f"### File: {mod['file']}\\n")
            if mod['exports']:
                f.write(f"- **Components**: {', '.join(mod['exports'])}\\n")
            if mod['api_calls']:
                f.write(f"- **API Calls**: {len(mod['api_calls'])} calls found\\n")
            f.write("\\n")

        # More sections to be filled...
        f.write("## 43. References\\n- Flask Documentation\\n- React Documentation\\n- MongoDB Documentation\\n")
        
    print(f"Generated {OUTPUT_FILE}")

if __name__ == '__main__':
    generate_markdown()
