"""Module entry point — enables `python -m wm_doc_graph <verb>`."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
