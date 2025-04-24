# COPIED FROM: https://github.com/theoremlp/rules_uv/blob/7bdbb0252d4c5045be0d2bce8daa0d10b9a04897/examples/typical/site_packages_extra/sitecustomize.py#L1

# This file is loaded by the Python interpreter and can alter the Python module loading process.
# We use it to inject lib/python into our PYTHON_PATH so that we can import modules relative to this directory.
import os
import sys

dirname = os.path.dirname(__file__)

# # Add site_packages_extra/lib/python to path so we can import `hello`` without the site_packages_extra.lib.python prefix
# sys.path.append(
#     os.path.abspath(os.path.join(dirname, "../../../../site_packages_extra/lib/python"))
# )

# Add repo root to the path
sys.path.append(os.path.abspath(os.path.join(dirname, "..")))
