#!/usr/bin/env python3
"""Scan a directory tree of card images and write OCR results to a readable YAML file."""

from __future__ import annotations  # Forward refs without quotes

import argparse

from enum import StrEnum, IntEnum, auto
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, TypeAdapter

import yaml

from . import __version__


class ORIENT(StrEnum):   # tag = orient
	# Coarse shape of a text chunk's bounding box, in pixel space.

	@staticmethod
	def _generate_next_value_(name: str, *args: object) -> str:
		return name  # use the member name as-is, no lower casing

	Square    = auto()   # width and height within x% of each other
	Portrait  = auto()   # taller than wide by more than x%
	Landscape = auto()   # wider than tall by more than x%

class SChunk(BaseModel): # tag - chunk
	model_config = ConfigDict(populate_by_name=True)

	strText:		str			= Field(default='',				alias='text')
	orient:			ORIENT		= Field(default=ORIENT.Square,	alias='orientation')
	uConf:			float		= Field(default=0.0,			alias='confidence')
	x:				float		= Field(default=0.0)
	y:				float		= Field(default=0.0)
	dX:				float		= Field(default=0.0)
	dY:				float		= Field(default=0.0)

type SCard = list[SChunk]
type SCards = dict[str, SCard] # tag = cards

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

	print(f"Reading {pathInput}...")

	strYaml = pathInput.read_text(encoding="utf-8")
	objCards = yaml.safe_load(strYaml)
	cards = TypeAdapter(SCards).validate_python(objCards)

	print(f"Read {len(cards)} cards")

if __name__ == "__main__":
	main()
