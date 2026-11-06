"""What every component's container runs on. Stdlib only."""

#: anakin-sdk needs Python 3.10+. KFP's default base image changes between
#: releases (its docs still say python:3.7), so set it explicitly.
BASE_IMAGE = "python:3.11-slim"

#: Installed in the task's pod at start-up, so pods need access to PyPI.
#: kfp-anakin itself isn't needed at run time: the components' code is embedded
#: in the compiled pipeline.
RUNTIME_PACKAGES = ["anakin-sdk>=0.2.0,<0.3.0"]
