#!/usr/bin/env python
"""Test if auth routes are loaded"""
try:
    from main import app
    print("OK: App loaded successfully")
    print("\nRegistered routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', [])
            print(f"  {route.path} - {methods}")

    # Check auth routes specifically
    auth_routes = [r for r in app.routes if hasattr(r, 'path') and '/auth' in r.path]
    print(f"\nAuth routes found: {len(auth_routes)}")
    for route in auth_routes:
        print(f"  {route.path}")

except Exception as e:
    print(f"ERROR: Error loading app: {e}")
    import traceback
    traceback.print_exc()
