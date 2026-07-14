#!/usr/bin/env python3
"""Scan a directory tree of card images and write OCR results to a readable YAML file."""

from __future__ import annotations  # Forward refs without quotes

import argparse
import sys

from collections.abc import Iterator
from enum import IntEnum, auto
from pathlib import Path
from tqdm import tqdm
from typing import Any

import yaml
from ocrmac import ocrmac

from . import __version__


# Image file extensions we attempt to OCR (matched case-insensitively).

g_setStrImageExt = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp", ".heic"}



class ORIENT(IntEnum):   # tag = orient
	# Coarse shape of a text chunk's bounding box, in pixel space.

	Square    = auto()   # width and height within g_rAspectSquareMax of each other
	Portrait  = auto()   # taller than wide by more than g_rAspectSquareMax
	Landscape = auto()   # wider than tall by more than g_rAspectSquareMax

class CARD(IntEnum): # tag = card
	Back = auto()
	Start = auto()
	Game = auto()

type TAnnotation = tuple[str, float, tuple[float, float, float, float]] # tag = anno

class CChunk:   # tag = chunk
	# A chunk is "landscape" if its OCR rectangle is more than this many times wider than
	# tall (and vice versa for "portrait"); anything in between is "square".

	g_rAspectSquareMax = 3.0

	# One recognized line of text plus the shape of its bounding box.
	def __init__(self, anno: TAnnotation) -> None:
		strcText, gConf, (x, y, dX, dY) = anno

		self.strText = str(strcText) # ocrmac.OCR.recognize does not return python strings.
		self.gConf = gConf
		self.x = x
		self.y = y
		self.dX = dX
		self.dY = dY

		self.orient = ORIENT.Square

		if self.dY and self.dX > self.g_rAspectSquareMax * self.dY:
			self.orient = ORIENT.Landscape
		elif self.dX and self.dY > self.g_rAspectSquareMax * self.dX:
			self.orient = ORIENT.Portrait


class CPool:   # tag = pool
	# Holds the OCR chunks for a single image in reading order. 

	def __init__(self, pathRoot: Path, pathImage: Path, fLiveText: bool = True) -> None:

		self.pathRoot = pathRoot
		self.pathImage = pathImage
		self.pathRelative = self.pathImage.relative_to(self.pathRoot)

		strFramework = "livetext" if fLiveText else "vision"

		self.lChunk = [
			CChunk(anno)
			for anno in ocrmac.OCR(str(pathImage), framework=strFramework, unit="line").recognize()
		]

	def LObjChunks(self) -> list[dict[str, Any]]:
		# Catch-all consumer — drains whatever chunks remain into a flat list, each carrying
		# its text and orientation. Keep this last in g_lFnStage so smarter stages inserted
		# ahead of it get first pick.

		return [
			{
				"text": str(chunk.strText),
				"orientation": chunk.orient.name,
				"confidence": chunk.gConf,
				"x": chunk.x,
				"y": chunk.y,
				"dX": chunk.dX,
				"dY": chunk.dY,
			}
			for chunk in self.lChunk
		]


def KVFromImage(pathRoot: Path, pathImage: Path, fLiveText: bool = True) -> tuple[str, object]:
	# Build the output dict for one image by running every stage over its pool.

	pool = CPool(pathRoot, pathImage, fLiveText=fLiveText)
	
	strKey = pool.pathRelative.stem
	lObjVal = pool.LObjChunks()

	return (strKey, lObjVal)


def LPathImages(pathDir: Path) -> list[Path]:
	# All image files under pathDir, recursively, sorted for stable output.

	return sorted(
		path for path in pathDir.rglob("*")
		if path.is_file() and path.suffix.lower() in g_setStrImageExt
	)


def WriteOcrResultsYaml(pathRoot: Path, lPathImages: list[Path], pathOutput: Path, fLiveText: bool = True) -> None:
	# Recursively OCRs every image under pathDir and writes a YAML map keyed by
	# deck-relative path. Each value is the per-image stage output from ObjFromImage.

	objOut: dict[str, object] = {}

	strBarFormat = "{desc} {n_fmt}/{total_fmt}: {percentage:3.0f}%|{bar}|{postfix[0]}"

	with tqdm(total=len(lPathImages), desc="Reading Images", bar_format=strBarFormat, postfix=[" " * 20]) as pbar:
		for pathImage in lPathImages:
			pbar.postfix[0] = f"{pathImage.stem:<20}"
			pbar.update(0)
			strKey, objVal = KVFromImage(pathRoot, pathImage, fLiveText=fLiveText)
			objOut[strKey] = objVal
			pbar.update(1)


	pathOutput.parent.mkdir(parents=True, exist_ok=True)
	pathOutput.write_text(
		yaml.safe_dump(objOut, sort_keys=False, allow_unicode=True, default_flow_style=False)
	)


def main() -> None:
	parser = argparse.ArgumentParser(
		prog="ocr",
		description="Get text from card images using Apple Vision OCR.",
	)
	parser.add_argument(
		"--version",
		action="version",
		version=f"%(prog)s {__version__}",
	)
	parser.add_argument(
		"--decks-dir",
		type=Path,
		default=Path("decks"),
		help="Directory tree of card images, searched recursively (default: 'decks')",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path("playground/ocr.yaml"),
		help="Output YAML file path (default: 'playground/ocr.yaml')",
	)
	parser.add_argument(
		"--no-livetext",
		action="store_true",
		help="Use Vision framework instead of LiveText (slower, returns per-token confidence)",
	)

	args = parser.parse_args()

	pathRoot: Path = args.decks_dir
	pathOutput: Path = args.output
	fLiveText: bool = not args.no_livetext

	if not pathRoot.is_dir():
		print(f"error: decks directory not found: {pathRoot}", file=sys.stderr)
		sys.exit(1)

	lPathImages = LPathImages(pathRoot)

	if not lPathImages:
		print(f"error: no image files found under {pathRoot} (searched recursively)", file=sys.stderr)
		sys.exit(1)

	print(f"scanning {len(lPathImages)} images under '{pathRoot}'...")
	WriteOcrResultsYaml(pathRoot, lPathImages, pathOutput, fLiveText=fLiveText)
	print(f"results written to '{pathOutput}'")


if __name__ == "__main__":
	main()
