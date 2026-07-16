#!/usr/bin/env python3
"""Scan a directory tree of card images and write OCR results to a readable YAML file."""

from __future__ import annotations  # Forward refs without quotes

import argparse
import re
import sys

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

type SCard = list[SChunk] # tag = card
type SCards = dict[str, SCard] # tag = cards

class DECK(StrEnum):
	RubberDucky = 'rd'
	BloodBath = 'bb'
	JAcuzzi = 'ja'

class ENTRYK(IntEnum): # tag = entryk
	Back = auto()
	Start = auto()
	Game = auto()

class CEntry:
	s_reCardNo = re.compile(r'(Card )(\d+)')

	def __init__(self, strName: str, card: SCard):
		self.strName = strName
		self.card = card
		strDeck, strSeqScan = self.strName.split('.')
		self.deck = DECK(strDeck)
		self.seqScan = int(strSeqScan)
		
		if self.seqScan == 0:
			self.entryk = ENTRYK.Back
			self.strCopyright = ''
			self.seqCard = 999
		elif self.seqScan == 1:
			self.entryk = ENTRYK.Start
			self.strCopyright = ''
			self.seqCard = 0
		else:
			self.entryk = ENTRYK.Game

			strCardNo = ''
			iChunkCardNo = -1
			for iChunk, chunk in enumerate(card):
				match = self.s_reCardNo.search(chunk.strText)
				if not match:
					continue
				if strCardNo:
					sys.exit(f"error: card has two numbers:\n  {strCardNo}\n  {chunk.strText}")
				self.strCopyright = chunk.strText
				strCardNo = match.group(2)
				iChunkCardNo = iChunk
			if not strCardNo:
				sys.exit(f"error: card {self.strName} has no numbers")
		
			self.seqCard = int(strCardNo)

			# print(f"{self.strName}: {self.strCardNo}")

	def StrNameOld(self) -> str:
		return f"{self.strName}.png"
		
	def StrNameNew(self) -> str:
		return f"{self.deck.value}-{self.seqCard:03d}.png"

class CDatabase:
	def __init__(self, cards: SCards):
		self.lEntry = [CEntry(strName, card) for strName, card in cards.items()]

	def WriteRenameScripts(self):
		mpDeckSetEntry: dict[DECK, set[CEntry]] = {}

		for entry in self.lEntry:
			mpDeckSetEntry.setdefault(entry.deck, set()).add(entry)

		for deck, setEntry in mpDeckSetEntry.items():
			lStrRename: list[str] = []

			for entry in setEntry:
				lStrRename.append(f"git mv images/{entry.StrNameOld()} {entry.StrNameNew()}")
			
			pathOutput = Path('decks') / (deck.value + '.sh')

			print(f"Writing to {pathOutput}")
			
			pathOutput.parent.mkdir(parents=True, exist_ok=True)
			pathOutput.write_text('\n'.join(lStrRename))




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

	db = CDatabase(cards)

	print(f"Processed {len(db.lEntry)} entries")

	db.WriteRenameScripts()

if __name__ == "__main__":
	main()
