# mypy: disable-error-code="import-untyped,import-not-found"
# ruff: noqa: E402


import pythonnet

pythonnet.load("coreclr", runtime_version="10.0")
import clr
import System as System

clr.AddReference("PKHeX.Core")
import PKHeX as PKHeX
