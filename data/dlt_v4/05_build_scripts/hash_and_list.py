# -*- coding: utf-8 -*-
import hashlib, os, io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def h(p):
    x = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            x.update(c)
    return x.hexdigest()

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in ['01_data/dlt_full_2933.csv', '01_data/dlt_full_2933.jsonl']:
    print(p, h(p))

# 目录文件清单
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__',)]
    for f in sorted(files):
        if f.endswith(('.log', '.pyc')):
            continue
        rel = os.path.join(root, f).replace('\\', '/').lstrip('./')
        print('FILE', rel, os.path.getsize(os.path.join(root, f)))
