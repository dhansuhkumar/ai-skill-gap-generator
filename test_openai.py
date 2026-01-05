import sys
print("Sys Path:", sys.path)
try:
    import openai
    print("OpenAI imported:", openai)
    from openai import OpenAI
    print("OpenAI Client imported")
except ImportError as e:
    print("ImportError:", e)
except Exception as e:
    print("Error:", e)
