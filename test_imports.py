# test_more.py
try:
    from generators import SyllabusGenerator
    print("generators.py - OK")
except Exception as e:
    print(f"generators.py error: {e}")

try:
    from ui_components import render_quality_review
    print("ui_components.py - OK") 
except Exception as e:
    print(f"ui_components.py error: {e}")

try:
    from content_manager import ContentManager
    print("content_manager.py - OK")
except Exception as e:
    print(f"content_manager.py error: {e}")