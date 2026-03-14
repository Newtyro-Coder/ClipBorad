import sys
from core.app import ClipboardApp

if __name__ == "__main__":
    app = ClipboardApp(sys.argv)
    sys.exit(app.exec_())