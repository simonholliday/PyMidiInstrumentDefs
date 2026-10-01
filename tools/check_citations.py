#!/usr/bin/env python3

"""Check that a definition's numbers really do appear on the pages it cites.

A definition promises that every number in it was read from a document its maker
published, at a place in that document you can turn to.  This follows that
promise mechanically: it finds the document, turns to the pages the ``source``
line cites, and asks whether each control-change, LSB, NRPN and note number is
printed there.

**What a pass means, and what it does not.**  A pass means the cited page
carries the number.  It does not mean the number means what the definition says
it means, that a band boundary is right, or that nothing was left out — a number
that *should* be in the definition and is not cannot be missed by a check that
reads the definition to know what to look for.  Absences are a separate promise,
kept by recording what was searched for and where.

**Why this is not a test.**  It reads manufacturers' manuals, which are
copyrighted and are never committed here, so in CI it could only skip — and a
skip nobody reads is a green tick certifying nothing.  It is a tool you run
against a local library of documents before offering a definition.

Documents are found by **SHA-256**, not by name: a definition records the hash of
the file it was read from, so a match proves the same file rather than merely one
with a similar name.  A document the maker has since revised will not match, and
that is a finding rather than a failure of this tool — it means the citation
points into an edition nobody here has read.

::

	export PYMIDIINSTRUMENTDEFS_LIBRARY=/path/to/manuals
	python tools/check_citations.py                    # every definition on the path
	python tools/check_citations.py moog/minitaur      # one, by name
	python tools/check_citations.py instruments/korg/minilogue_xd.yaml   # or by path

It exits non-zero if any number is missing, if a citation names a page its
document does not have, if a cited document cannot be found, or if a definition
cannot be read at all — four faults with four different fixes, reported apart
from each other and never as a traceback.
"""

import argparse
import dataclasses
import hashlib
import os
import pathlib
import re
import sys
import typing

import pymidiinstrumentdefs
import pymidiinstrumentdefs.definition


# Where to look for the documents, when no --library is given.
LIBRARY_VARIABLE: typing.Final[str] = "PYMIDIINSTRUMENTDEFS_LIBRARY"

# What can be read for text.  A maker's MIDI implementation is as likely to be
# plain text as a PDF, and a plain-text one has no pages at all.
READABLE: typing.Final[frozenset[str]] = frozenset({".pdf", ".txt"})

# A page citation, however a source line phrases it: "p. 8", "pp. 30-31",
# "pp. 26-27, 30, 32-33, 40 and 50", "(p. 1)".
_CITATION: typing.Final[re.Pattern[str]] = re.compile(
	r"\bpp?\.\s*"
	r"(\d+(?:\s*[-–]\s*\d+)?"
	r"(?:(?:\s*,\s*(?:and\s+)?|\s+and\s+)\d+(?:\s*[-–]\s*\d+)?)*)"
)

# What separates one page or range from the next inside a citation.
_BETWEEN: typing.Final[re.Pattern[str]] = re.compile(r"\s*,\s*(?:and\s+)?|\s+and\s+")

# Spaces a PDF's text layer opened up *inside* a number, never a line break:
# joining across lines would fuse two separate numbers into a third.
_SPLIT_DIGITS: typing.Final[re.Pattern[str]] = re.compile(r"(?<=\d)[ \t]+(?=\d)")

_NO_PYPDF: typing.Final[str] = (
	"check_citations reads PDFs, which needs pypdf:\n"
	"    pip install pypdf\n"
	"Some makers ship their manuals encrypted, which also needs cryptography."
)


def reader_for (path: pathlib.Path) -> typing.Any:

	"""Open a PDF, unlocking the ones makers ship encrypted with an empty password.

	pypdf is imported here rather than at the top so that this file can be read,
	and its parsing tested, by an interpreter that has no PDF library at all.
	"""

	try:
		import pypdf
	except ModuleNotFoundError:
		raise SystemExit(_NO_PYPDF) from None

	opened = pypdf.PdfReader(path)

	if opened.is_encrypted:
		opened.decrypt("")

	return opened


def library_index (root: pathlib.Path) -> dict[str, pathlib.Path]:

	"""Every document under ``root``, keyed by the SHA-256 of its bytes.

	The hash is how a definition names the file it was read from, so it is also
	how that file is found again.
	"""

	index: dict[str, pathlib.Path] = {}

	for path in sorted(root.rglob("*")):
		if not path.is_file() or path.suffix.lower() not in READABLE:
			continue

		index[hashlib.sha256(path.read_bytes()).hexdigest()] = path

	return index


def cited_pages (prose: str) -> set[int]:

	"""Every printed page number a ``source`` line cites.

	Printed numbers, as the document prints them — turning one into a page of the
	file is the citation's own business, because the offset between them differs
	from document to document.
	"""

	pages: set[int] = set()

	for citation in _CITATION.finditer(prose):
		for part in _BETWEEN.split(citation.group(1)):
			edges = [int(digits) for digits in re.findall(r"\d+", part)]

			if len(edges) == 2:
				pages.update(range(edges[0], edges[1] + 1))
			elif edges:
				pages.add(edges[0])

	return pages


def numbers_on (text: str) -> set[int]:

	"""Every number a page prints, read two ways because extraction is lossy.

	A PDF's text layer often breaks a number apart: one manual's table renders
	``35 (LSB)`` as ``3 5(LSB)``, so reading it plainly loses 13 of that
	definition's 55 numbers.  Closing same-line gaps between digits recovers all
	55 — but it is not free the other way round, because where a table's value
	range abuts the next row's number, ``0-127 72`` becomes ``12772`` and loses
	both.  Measured across four documents, closing the gaps rescues 13 numbers on
	one and destroys 29 across two others.

	So the two readings are combined rather than one replacing the other, which
	finds every number that either way of reading finds.  The cost is that a
	number can be matched by digits the page never printed side by side, which is
	why a pass here means the page carries the number and nothing stronger.
	"""

	closed = _SPLIT_DIGITS.sub("", text)

	return {int(digits) for digits in re.findall(r"\d+", f"{text} {closed}")}


def wanted_numbers (
	definition: pymidiinstrumentdefs.definition.Definition,
) -> list[tuple[str, str, int]]:

	"""Every number in the definition that a cited page ought to carry.

	Controller numbers, their fine halves, NRPN numbers, and the notes a fixed
	note map assigns.  Bands, ranges and defaults are left out: they are numbers
	the document prints too, but a band boundary is a claim about *meaning*, and
	finding the digits on the page would not check it.
	"""

	wanted: list[tuple[str, str, int]] = []

	for control in definition.controls.values():
		for kind, number in (("cc", control.cc), ("lsb", control.lsb), ("nrpn", control.nrpn)):
			if number is not None:
				wanted.append((control.name, kind, number))

	for name, note in definition.voice.voices.items():
		wanted.append((name, "note", note))

	return wanted


def halves_on (nrpn: int, printed: set[int]) -> bool:

	"""Whether a page prints an NRPN as the two halves it is addressed with.

	A definition holds an NRPN as one parameter number, which is what goes on the
	wire: the MSB times 128 plus the LSB.  Plenty of makers print it that way too,
	and the number is then found on the page like any other.  Elektron prints the
	two halves in their own columns and never the sum, so a definition's 229 is on
	the page as a 1 beside a 101.

	Finding both halves is a **weaker** check than finding the number: the halves
	are small and such pages are full of small numbers.  It is reported separately
	for that reason, rather than counted as found.
	"""

	return nrpn // 128 in printed and nrpn % 128 in printed


# A range wide enough to cover most of the controller space says nothing useful:
# "0-127" would answer for every number a definition could hold. A group of
# controls is small, so only a short run counts as naming its members.

RANGE_SPAN: typing.Final[int] = 32

_PRINTED_RANGE: typing.Final[re.Pattern[str]] = re.compile(
	r"(\d{1,3})\s*(?:[-\u2013\u2014\u2026]|\.\.\.)\s*(\d{1,3})")


def inside_a_range (number: int, text: str) -> bool:

	"""Whether a page names a number only by printing the range it falls in.

	Korg's wavestate is the case: its MIDI CC Assign table gives "Layer A Mod
	Knobs 1...8" as "80...87" and never prints 81 to 86, so a definition that
	holds eight controls asks for six numbers the page does not carry.  The page
	does name them, in the only way a table of ranges can.

	This is a **weaker** check than finding the number, for two reasons: the page
	never shows the number itself, and a range is matched wherever it appears
	rather than against the row that means it.  It is reported separately for that
	reason, and never counted as found.

	Only the inside of a range counts, because an endpoint is already found by
	looking for the number itself, and only a short range counts at all: a manual
	that prints "0-127" for its note numbers would otherwise answer for every
	controller number in the file.
	"""

	for found in _PRINTED_RANGE.finditer(text):
		low, high = int(found.group(1)), int(found.group(2))

		if low < number < high and high - low <= RANGE_SPAN:
			return True

	return False


def as_ranges (numbers: typing.Iterable[int]) -> str:

	"""A run of numbers written the way a person cites them: ``21-24, 30``."""

	ordered = sorted(set(numbers))

	if not ordered:
		return "none"

	runs: list[list[int]] = [[ordered[0]]]

	for number in ordered[1:]:
		if number == runs[-1][-1] + 1:
			runs[-1].append(number)
		else:
			runs.append([number])

	return ", ".join(str(run[0]) if len(run) == 1 else f"{run[0]}-{run[-1]}" for run in runs)


@dataclasses.dataclass
class Followed:

	"""One cited document, as far as its citation could be followed."""

	key: str
	source: pymidiinstrumentdefs.definition.Source
	path: pathlib.Path | None = None
	extent: int | None = None
	pages: list[int] = dataclasses.field(default_factory=list)
	text: str = ""

	# A scan of a printed manual is a PDF of pictures: it has pages, and turning to
	# one is still worth checking, but there is no text in it to search.  Saying so
	# is not the same as saying the numbers are absent, and the two must not be
	# reported alike.
	scanned: bool = False


	def covers (self, printed: int) -> bool:

		"""Whether this document has the page a citation calls ``printed``."""

		if self.path is None or self.extent is None:
			return False

		page = self.source.file_page(printed)

		return page is not None and 1 <= page <= self.extent


def unreachable_pages (cited: set[int], documents: "list[Followed]") -> set[int]:

	"""The printed pages a citation names that no cited document has.

	A printed page nobody can turn to is a different fault from a number that is
	not there, and it has a different fix: the citation is wrong, or the document
	it belongs to was never recorded.

	**Only a paginated document can have a page**, so only those can answer.  An
	earlier version excused every page citation in a definition as soon as any of
	its sources had no pages - which meant citing a plain-text chart or a saved web
	page beside a manual silently switched off this check for the manual too.  A
	citation of a page is a claim about a document that has pages, whatever else
	the definition also cites.
	"""

	return {
		printed for printed in cited
		if not any(document.covers(printed) for document in documents)
	}


@dataclasses.dataclass
class Result:

	"""What following one definition's citations found."""

	name: str
	documents: list[Followed] = dataclasses.field(default_factory=list)
	cited: set[int] = dataclasses.field(default_factory=set)
	unreachable: set[int] = dataclasses.field(default_factory=set)
	wanted: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	missing: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	as_halves: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	in_a_range: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	unverifiable: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)


	@property
	def lost (self) -> list[Followed]:

		"""The cited documents that no file in the library matches."""

		return [document for document in self.documents if document.path is None]


	@property
	def sound (self) -> bool:

		"""True when every citation was followed and every number was on its page."""

		return not (self.missing or self.unreachable or self.lost)


def follow (
	definition: pymidiinstrumentdefs.definition.Definition,
	name: str,
	index: dict[str, pathlib.Path],
) -> Result:

	"""Follow one definition's citations into its documents and see what is there.

	Where a definition names several documents, its prose does not say which
	pages belong to which — so the cited pages are looked for in all of them, and
	a number counts as found if any cited page of any of them carries it.  That
	makes the check weaker the more documents a definition cites, and it is the
	honest reading of a citation that does not attribute its own pages.
	"""

	result = Result(name = name, cited = cited_pages(definition.source or ""))
	result.wanted = wanted_numbers(definition)

	for key, source in definition.sources.items():
		document = Followed(key = key, source = source)
		document.path = index.get(source.sha256) if source.sha256 else None

		if document.path is not None:
			if document.path.suffix.lower() == ".pdf":
				document.extent = len(reader_for(document.path).pages)
			else:
				# A plain-text implementation chart runs to numbered sections, so
				# there is no page to turn to and the whole of it is read.
				document.extent = None

		result.documents.append(document)

	result.unreachable = unreachable_pages(result.cited, result.documents)

	for document in result.documents:
		if document.path is None:
			continue

		if document.extent is None:
			document.text = document.path.read_text(encoding = "utf-8", errors = "replace")
			continue

		document.pages = sorted({
			page for printed in result.cited
			if document.covers(printed)
			for page in [document.source.file_page(printed)]
			if page is not None
		})

		opened = reader_for(document.path)
		document.text = "\n".join(
			opened.pages[page - 1].extract_text() or "" for page in document.pages
		)

		# Nothing on the cited pages is either a scan or a run of blank pages, and
		# those need different answers, so ask the whole document before deciding.

		if not document.text.strip():
			whole = "".join(page.extract_text() or "" for page in opened.pages)
			document.scanned = not whole.strip()

	printed_text = " ".join(document.text for document in result.documents)
	printed_numbers = numbers_on(printed_text)

	unreadable = any(document.scanned for document in result.documents)

	for entry in result.wanted:
		name, kind, number = entry

		if number in printed_numbers:
			continue

		if kind == "nrpn" and halves_on(number, printed_numbers):
			result.as_halves.append(entry)
			continue

		if kind == "cc" and inside_a_range(number, printed_text):
			result.in_a_range.append(entry)
			continue

		# A number absent from the text of a definition that also cites a scan may
		# be printed on the scan's own pages, where nothing can look for it.  That
		# is an unanswered question rather than a wrong citation, and calling it
		# missing would accuse a definition of a fault nobody has established.

		if unreadable:
			result.unverifiable.append(entry)
			continue

		result.missing.append(entry)

	return result


def render (result: Result, verbose: bool) -> None:

	"""Say what was followed and what was not, in the order a reader needs it."""

	print(f"{result.name}")

	for document in result.documents:
		if document.path is None:
			held = (document.source.sha256 or "no sha256 recorded")[:16]
			print(f"    {document.key}: NOT IN THE LIBRARY — nothing matches {held}")
			print(f"        {document.source.title or 'untitled'}")
			continue

		extent = f"{document.extent} pages" if document.extent else "no pages"
		print(f"    {document.key}: {document.path.name}  [{extent}]")

		if document.scanned:
			print("        a scan: it has pages, but no text in them to search")

		if document.pages:
			print(f"        printed {as_ranges(result.cited)} → file {as_ranges(document.pages)}")
		elif document.extent is None:
			print("        no pages to turn to, so the whole document was read")

	if result.unreachable:
		print(f"    ⚠ cited but in no document read: printed {as_ranges(result.unreachable)}")

	found = (len(result.wanted) - len(result.missing) - len(result.as_halves) - len(result.in_a_range)
		- len(result.unverifiable))

	if not result.wanted:
		print("    no numbers to check")
	else:
		print(f"    {found} of {len(result.wanted)} numbers found")

	if result.as_halves:
		print(
			f"        {len(result.as_halves)} NRPNs found only as the two halves the maker prints, "
			f"which is a weaker check"
		)

	if result.in_a_range:
		print(
			f"        {len(result.in_a_range)} controller numbers found only inside a range the maker "
			f"prints, which is a weaker check"
		)

	if result.unverifiable:
		print(
			f"        {len(result.unverifiable)} NOT CHECKED AT ALL: a cited document is a scan, "
			f"so no machine here can look for them"
		)

	for name, kind, number in result.missing:
		print(f"        not on any cited page: {name}.{kind} = {number}")

	if verbose:
		for name, kind, number in result.wanted:
			mark = " " if (name, kind, number) in result.missing else "✓"
			print(f"        {mark} {name}.{kind} = {number}")

	print()


def resolve (name: str) -> tuple[str, pymidiinstrumentdefs.definition.Definition]:

	"""Load a definition by its name, or by a path to a file not on the search path."""

	if name.endswith(".yaml") or name.endswith(".yml"):
		path = pathlib.Path(name)

		return str(path), pymidiinstrumentdefs.load_file(path)

	return name, pymidiinstrumentdefs.load(name)


def main (argv: list[str] | None = None) -> int:

	"""Check the named definitions, or every one on the search path."""

	parser = argparse.ArgumentParser(
		description = "Check that a definition's numbers appear on the pages it cites.",
		epilog = f"The library of documents is --library, or ${LIBRARY_VARIABLE}.",
	)
	parser.add_argument("names", nargs = "*", help = "definition names or paths; default is all of them")
	parser.add_argument("--library", help = "the folder of maker's documents to read")
	parser.add_argument("--verbose", "-v", action = "store_true", help = "list every number, found or not")

	arguments = parser.parse_args(argv)
	given = arguments.library or os.environ.get(LIBRARY_VARIABLE)

	if not given:
		parser.error(f"no document library — pass --library, or set ${LIBRARY_VARIABLE}")

	root = pathlib.Path(given).expanduser()

	if not root.is_dir():
		parser.error(f"{root} is not a folder of documents")

	index = library_index(root)
	print(f"{len(index)} documents in {root}\n")

	names = arguments.names or sorted(pymidiinstrumentdefs.available())
	faults = 0

	for given_name in names:
		# A definition too broken to load is still an answer, and a gate that
		# printed a traceback here would be read as the tool itself failing.

		try:
			name, definition = resolve(given_name)
		except (pymidiinstrumentdefs.DefinitionError, pymidiinstrumentdefs.DefinitionNotFound, OSError) as fault:
			print(f"{given_name}\n    could not be read: {fault}\n")
			faults += 1
			continue

		result = follow(definition, name, index)

		render(result, arguments.verbose)
		faults += not result.sound

	print(f"{len(names) - faults} of {len(names)} definitions check out")

	return 1 if faults else 0


if __name__ == "__main__":
	sys.exit(main())
