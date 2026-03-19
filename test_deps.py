
import sys
import os

dependencies = [
    "streamlit",
    "pandas",
    "plotly",
    "langchain",
    "langchain_google_genai",
    "google.generativeai",
    "dotenv"
]

print(f"Python version: {sys.version}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

missing = []
for dep in dependencies:
    try:
        __import__(dep.replace('-', '_').replace('.', '_'))
        print(f"[OK] {dep}")
    except ImportError:
        try:
             # Try common mappings
             if dep == "langchain_google_genai": __import__("langchain_google_genai")
             elif dep == "google.generativeai": __import__("google.generativeai")
             elif dep == "dotenv": __import__("dotenv")
             print(f"[OK] {dep}")
        except ImportError:
            missing.append(dep)
            print(f"[MISSING] {dep}")

if missing:
    print(f"\nMissing dependencies: {', '.join(missing)}")
else:
    print("\nAll dependencies seem to be present in the current environment.")
