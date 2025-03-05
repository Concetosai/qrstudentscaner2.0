import sys
path = '/home/yourusername/secundariaoficialapp1.0'
if path not in sys.path:
    sys.path.append(path)

from app import app

if __name__ == "__main__":
    app.run()