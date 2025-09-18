import os
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
print("__file__ :",__file__)
print("os.path.dirname(__file__) :",os.path.dirname(__file__))
print("""os.path.join(os.path.dirname(__file__), "logs") :""",os.path.join(os.path.dirname(__file__), "logs"))