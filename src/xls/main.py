#!/usr/bin/env python3
"""Scan a directory tree of card images and write OCR results to a readable YAML file."""

from __future__ import annotations  # Forward refs without quotes

import argparse
import sys

from enum import IntEnum, auto
from pathlib import Path

import yaml

from . import __version__


class ORIENT(IntEnum):   # tag = orient
	# Coarse shape of a text chunk's bounding box, in pixel space.

	Square    = auto()   # width and height within g_rAspectSquareMax of each other
	Portrait  = auto()   # taller than wide by more than g_rAspectSquareMax
	Landscape = auto()   # wider than tall by more than g_rAspectSquareMax

class CARD(IntEnum): # tag = card
	Back = auto()
	Start = auto()
	Game = auto()

def main() -> None:
	parser = argparse.ArgumentParser(
		prog="xls",
		description="Convert OCRed yaml from cards into an XLS sheet.",
	)
	parser.add_argument(
		"--version",
		action="version",
		version=f"%(prog)s {__version__}",
	)
	parser.add_argument(
		"--input",
		type=Path,
		default=Path("playground/ocr.yaml"),
		help="Output XLSX file path (default: 'playground/ocr.yaml')",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path("playground/decks.xlsx"),
		help="Output XLSX file path (default: 'playground/decks.xlsx')",
	)
	args = parser.parse_args()

	pathInput: Path = args.input
	pathOutput: Path = args.output

	print(f"'{pathInput}' would process to '{pathOutput}'")


if __name__ == "__main__":
	main()
