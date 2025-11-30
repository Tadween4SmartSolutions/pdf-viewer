#!/usr/bin/env python3
import os
import re
import sys

# ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

pattern = re.compile(r"url_for\(\s*['\"]([^'\"]+)['\"]")
used = set()

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip virtualenv and migrations/versions compiled files
    if '.venv' in dirpath.split(os.sep) or 'venv' in dirpath.split(os.sep):
        continue
    if 'node_modules' in dirpath.split(os.sep):
        continue
    for fname in filenames:
        if not fname.endswith(('.py', '.html')):
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue
        for m in pattern.finditer(content):
            used.add(m.group(1))

print(f"Found {len(used)} distinct `url_for` usages in repo files:\n")
for name in sorted(used):
    print(' -', name)

# Try to import app and create app instance
missing = set()
try:
    from app import create_app
    app = create_app()
    registered = set(app.view_functions.keys())
    print('\nRegistered endpoints (count=%d):' % len(registered))
    for ep in sorted(registered):
        print(' -', ep)

    # Exclude common endpoints that are not view functions
    allowed_extras = set(['static'])
    for name in sorted(used):
        # if name contains a dot (blueprint-qualified) check directly
        if name in registered or name in allowed_extras:
            continue
        # Could be a blueprint endpoint but missing blueprint name: try to guess
        if '.' not in name:
            # check if any registered endpoint ends with '.'+name
            matches = [ep for ep in registered if ep.split('.')[-1] == name]
            if matches:
                print(f"Note: `{name}` may resolve to: {matches}")
                continue
        missing.add(name)

    if missing:
        print('\nMISSING endpoints (referenced in templates/code but not registered):')
        for m in sorted(missing):
            print(' -', m)
    else:
        print('\nAll referenced endpoints appear to be registered (or have possible matches).')

except Exception as e:
    print('\nFailed to create app or inspect view functions:')
    import traceback
    traceback.print_exc()
    sys.exit(2)
