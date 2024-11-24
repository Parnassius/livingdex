# mypy: disable-error-code="import-untyped,import-not-found"
# ruff: noqa: E402

from __future__ import annotations

import pythonnet

pythonnet.load("coreclr")

import clr

clr.AddReference("PKHeX.Core")

import PKHeX as PKHeX
