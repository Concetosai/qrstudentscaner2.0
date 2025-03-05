import sys
path = '/home/yourusername/secundariaoficialapp1.0'
if path not in sys.path:
    sys.path.append(path)

from wsgi import app as application