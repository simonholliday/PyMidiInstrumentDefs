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

**A number is looked for in the order of what finding it proves.**  Printed whole
on a cited page is the result this tool calls found.  Everything after that is a
weaker check, reported apart and never counted with it: an NRPN as two
hexadecimal bytes side by side, as two halves in decimal, a controller inside a
range the maker prints, the digits of a number with a gap between them on one
line, and last a byte in hexadecimal.  **The digits with a gap came first once,
with the numbers printed whole**, and so `5: 0.5      21: 2.1` was a found 521:
nine of one definition's NRPNs were counted as found on pages that print none of
them whole, and the bytes that are on those pages were never looked at.

**A page is read only in the document its citation names.**  `chart p. 2` turns
the chart to its second sheet and no other document.  A page cited with no source
key before it is nobody's, so it is still read in every document that has pages:
the report says which pages were read that way, and at its end how many.

``--pool`` reads every cited page in every document, which is what this tool did
until 2026-10-13.  Then `manual p. 2` turned the chart to its second sheet as
well, and the more a definition cited the less a pass proved.  Over the 171
definitions bundled when reading by key was written it moved 22 numbers in seven
of them out of found, each into a weaker check or into the numbers nothing here
can look for.  It is kept for comparing against, and is not a gate.
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
# plain text as a PDF, and a plain-text one has no pages at all.  A web page as it
# was served is read the same way, markup and all: a definition cites one where what
# it cites is in the page's script payload and so not in its visible text.
READABLE: typing.Final[frozenset[str]] = frozenset({".pdf", ".txt", ".html"})

# A page citation, however a source line phrases it: "p. 8", "pp. 30-31",
# "pp. 26-27, 30, 32-33, 40 and 50", "(p. 1)".
_CITATION: typing.Final[re.Pattern[str]] = re.compile(
	r"\bpp?\.\s*"
	r"(\d+(?:\s*[-–]\s*\d+)?"
	r"(?:(?:\s*,\s*(?:and\s+)?|\s+and\s+)\d+(?:\s*[-–]\s*\d+)?)*)"
)

# What separates one page or range from the next inside a citation.
_BETWEEN: typing.Final[re.Pattern[str]] = re.compile(r"\s*,\s*(?:and\s+)?|\s+and\s+")

# The word standing before a citation, where one does: `implementation p. 9` and
# `manual, pp. 26-27` each name the document the page is in.  Whether the word is one
# of the definition's own source keys is asked afterwards, since most words before a
# `p.` are `at` and `on`.
_KEYED: typing.Final[re.Pattern[str]] = re.compile(
	r"(?:(?<![\w\-\u2010\u2011\u2012\u2013])([a-z][a-z0-9_]*),?\s+)?" + _CITATION.pattern)

# A number the maker marks as hexadecimal, `0x21`.  Its digits are not a decimal number,
# so no reading of a page in decimal takes them for one: not as printed, not with a gap
# closed, and not as the end of a range.  **A word of its own**, so the `0x8` in
# `1280x800` and in `12.0x8.5 in` is left as the dimensions it is.
_MARKED_HEX: typing.Final[re.Pattern[str]] = re.compile(
	r"(?<![0-9A-Za-z])(?<![0-9]\.)0[xX][0-9A-Fa-f]+(?![0-9A-Za-z]|\.[0-9])")

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


def whole_text (path: pathlib.Path) -> str:

	"""Every word of a document that has no page to turn to.

	A PDF reaches this when its source says ``paginated: false``, which is how the
	format describes a document the maker did not number - so its pages are read and
	joined rather than its bytes being read as text, which would yield nothing.
	"""

	if path.suffix.lower() == ".pdf":
		return "\n".join(page.extract_text() or "" for page in reader_for(path).pages)

	return path.read_text(encoding = "utf-8", errors = "replace")


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
		pages.update(listed_pages(citation.group(1)))

	return pages


def listed_pages (listed: str) -> set[int]:

	"""The pages one citation lists after its `p.`: single pages, and ranges with both their ends."""

	pages: set[int] = set()

	for part in _BETWEEN.split(listed):
		edges = [int(digits) for digits in re.findall(r"\d+", part)]

		if len(edges) == 2:
			pages.update(range(edges[0], edges[1] + 1))
		elif edges:
			pages.add(edges[0])

	return pages


def cited_by_key (prose: str, keys: typing.Collection[str]) -> tuple[dict[str, set[int]], set[int]]:

	"""The pages a ``source`` line cites, sorted by the document each citation names.

	Two answers.  The first is the pages cited with one of these source keys standing
	before them, under that key: `implementation p. 9` is page 9 of `implementation`
	and of no other document.  The second is the pages cited with no key, as `(p. 9)`
	or `at pp. 30-31` are: nothing says which document those are in, so they are
	every document's.

	**Only the word standing directly before the `p.` is asked**, and only as it is
	written under ``sources``.  So `Chart p. 1`, `the chart (p. 2)` and `the manual's
	p. 4` name no document here, and in `manual p. 3 and p. 4` the 4 is nobody's.  And
	`see the chart p. 4 of the manual` credits page 4 to `chart`, which no pattern can
	tell from the citation it looks like.
	"""

	keyed: dict[str, set[int]] = {}
	bare: set[int] = set()

	for citation in _KEYED.finditer(prose):
		word, pages = citation.group(1), listed_pages(citation.group(2))

		if word in keys:
			keyed.setdefault(word, set()).update(pages)
		else:
			bare.update(pages)

	return keyed, bare


def numbers_as_printed (text: str) -> set[int]:

	"""Every number a page prints, each as the run of digits it stands in.

	Not the digits of a form marked as hexadecimal: `0x21` prints no 0 and no 21.
	"""

	return {int(digits) for digits in re.findall(r"\d+", _MARKED_HEX.sub("x", text))}


def numbers_closed_up (text: str) -> set[int]:

	"""The numbers a page yields once the gaps between digits on a line are closed.

	A PDF's text layer often breaks a number apart: one manual's table renders
	``35 (LSB)`` as ``3 5(LSB)``, so reading it plainly loses 13 of that
	definition's 55 numbers.  Closing same-line gaps between digits recovers them
	— and makes numbers the page never printed: where a table's value range abuts
	the next row's number, ``0-127 72`` becomes ``12772``, and ``5: 0.5      21:
	2.1`` holds a 521.

	So this is a reading of its own and a weaker one, tried only for a number that
	is not printed whole, is not an NRPN's bytes or halves, and is not inside a
	printed range.  Read together with the numbers as printed, as it was at first,
	it counted nine of one definition's NRPNs as found on pages that print each as
	two bytes and none of them whole.  **Nothing reads the two together now**: the
	halves of an NRPN are looked for among the numbers as printed alone, since a half
	made by closing a gap is a number the page may never have printed.
	"""

	return {int(digits) for digits in re.findall(r"\d+", _SPLIT_DIGITS.sub("", _MARKED_HEX.sub("x", text)))}


def wanted_numbers (
	definition: pymidiinstrumentdefs.definition.Definition,
) -> list[tuple[str, str, int]]:

	"""Every number in the definition that a cited page ought to carry.

	Controller numbers, their fine halves, NRPN numbers, every note a voice of the
	instrument's own map answers to, and every note the instrument sends for one.
	Bands, ranges and defaults are left out: they are numbers the document prints
	too, but a band boundary is a claim about *meaning*, and finding the digits on
	the page would not check it.
	"""

	wanted: list[tuple[str, str, int]] = []

	for control in definition.controls.values():
		for kind, number in (("cc", control.cc), ("lsb", control.lsb), ("nrpn", control.nrpn)):
			if number is not None:
				wanted.append((control.name, kind, number))

	for name, notes in definition.voice.voice_notes.items():
		for note in notes:
			wanted.append((name, "note", note))

	for setting, sent in definition.voice.voices_sent.items():
		for name, note in sent.notes.items():
			wanted.append((f"{setting}.{name}", "sent", note))

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


def as_a_byte_pair (nrpn: int, text: str) -> bool:

	"""Whether a page prints an NRPN as its two bytes side by side, in hexadecimal.

	Korg's RADIAS is the case: its MIDI implementation gives every NRPN as two
	hexadecimal bytes in one cell, so Vocoder Band14 Panpot is ``04  5D``.  A
	definition holds that as 4 x 128 + 93 = 605, and the pages that print the
	table print neither 605 nor 93.

	**Both bytes must be on one line with nothing but spaces or tabs between
	them**, each as two digits in capitals, the pair standing as words of its own
	and not against a full stop, a colon, a stroke or a hash.  Standing together
	is what lets a byte made only of digits count here, where `hexadecimal_form`
	refuses one on its own: a lone ``60`` is far likelier sixty than 96.

	**A pair is read wherever two such words stand together, and no column is
	looked for.**  So two decimal numbers of two digits each are read as bytes,
	and so is an address in a system exclusive table.  Measured over this corpus,
	seven wrong values at most pass that did not before on the pages of any
	definition here that holds an NRPN.  And every row of a table is on the page,
	so a number taken from another row is found as readily as the right one, a
	byte of digits read as decimal among them: that is usually some other row.

	The pair itself is not found for two slips a reader of bytes makes: ``04  5D``
	does not answer for the two bytes joined as one number, or for the halves
	changed places.  **That does not refuse them.**  Such a number is still looked
	for as two halves in decimal, and two small decimal numbers are somewhere on
	almost any page of MIDI tables.

	**So where a definition's NRPNs are found both ways, the fewer are named.**  The
	tables a definition is read off usually set an NRPN down one way.  If most
	were found as pairs, the few found only as decimal halves are the likelier
	slips; if most were found as halves, the few found as pairs are the likelier
	coincidences; and where as many were found each way, all are named.  **That
	catches a slip made on one row and not one made on every row**: joined as one
	number throughout, the wrong numbers are the many and none is named; read as
	decimal throughout, most are other rows' pairs.

	It is tried before the decimal halves because it asks more of the page.  It
	is reported apart from the numbers found as themselves and never counted
	with them: it is not the number, and it is matched wherever it stands.  That
	is weaker than finding a number of three digits or more printed whole.  It is
	not always weaker than finding a small one, since a 20 is on a page of MIDI
	tables many times over.

	No other way of setting two bytes down is read: not one under the other, not
	with a bar, a comma or a colon between them, and not with an H after each.
	"""

	return 0 <= nrpn <= 0x3FFF and pair_of_bytes(nrpn).search(text) is not None


def pair_of_bytes (nrpn: int) -> re.Pattern[str]:

	"""An NRPN's two bytes side by side, as `as_a_byte_pair` says a page must print them."""

	return re.compile(
		rf"(?<![0-9A-Za-z.#:/]){nrpn // 128:02X}[ \t]+{nrpn % 128:02X}(?![0-9A-Za-z.#:/])")


def beside_its_label (nrpn: int, label: str | None, text: str) -> bool:

	"""Whether one line carries an NRPN's two bytes and its control's label as well.

	**This is the one check here that is of a row and not of a page.**  A pair of
	bytes is matched wherever it stands, and every row of a table is on the page,
	so a number taken from the row above is found as readily as the right one: a
	slip made on every row passes entire.  The label is what tells the rows apart.
	Where a definition's labels are the table's own words, each pair stands on the
	line that also carries its label, and a number from another row does not:
	measured on the two definitions whose NRPNs are printed so, 108 of 108 and 29
	of 29 are beside their labels, and with every number moved down one row, none.

	The label is compared with its spaces, case and punctuation out, as a text
	layer may set any of them differently, and it has to stand as words of its own
	in what the line holds besides the pair: `Pan` is not beside the row of a
	`Panpot`, `Band1` is not beside `Band14`, and no label is found in the two bytes
	themselves.  A label with no letter in it is beside nothing, since a row's own
	range of values would answer for it.

	**It says nothing where the labels are not the table's words**, which is why it
	is reported as a count and fails no definition.  It says no of a label the table
	wraps onto a second line, or abbreviates.  **And it does not make the columns
	hexadecimal.**  Two decimal numbers on a label's line are read as bytes like any
	others, so a number no page prints may stand "beside its label" too.

	A definition that gives a control no label has the control's own key for one,
	and that is compared in the same way.
	"""

	if not label or not re.search(r"[A-Za-z]", label) or not 0 <= nrpn <= 0x3FFF:
		return False

	# The label's letters and digits in order, with anything or nothing between them.
	wanted = re.compile(r"(?<![a-z0-9])"
		+ r"[^a-z0-9]*".join(re.findall(r"[a-z0-9]", label.lower())) + r"(?![a-z0-9])")
	pair = pair_of_bytes(nrpn)

	for line in text.split("\n"):
		found = pair.search(line)

		if found is None:
			continue

		if wanted.search((line[:found.start()] + " " + line[found.end():]).lower()):
			return True

	return False


# A range wide enough to cover most of the controller space says nothing useful:
# "0-127" would answer for every number a definition could hold. A group of
# controls is small, so only a short run counts as naming its members.

RANGE_SPAN: typing.Final[int] = 32

# A number may be written with a hash in front of it, and a maker who does that usually does it
# on both ends of a range: Waldorf's modulation-source table prints "MIDI CC #22 - #31", which a
# pattern expecting bare digits around the dash does not see at all.  The hash is optional on
# each end rather than required, so "22-31" still matches.
_PRINTED_RANGE: typing.Final[re.Pattern[str]] = re.compile(
	r"#?\s*(\d{1,3})\s*(?:[-\u2013\u2014\u2026]|\.\.\.)\s*#?\s*(\d{1,3})")


def ranges_holding (number: int, text: str) -> dict[str, str]:

	"""Each short range a page prints that a number falls inside, and the line it stands on.

	The range as it stands there, against the whole of its line with the spaces closed up.

	Korg's wavestate is the case: its MIDI CC Assign table gives "Layer A Mod
	Knobs 1...8" as "80...87" and never prints 81 to 86, so a definition that
	holds eight controls asks for six numbers the page does not carry.  The page
	does name them, in the only way a table of ranges can.

	A fine half is named the same way where a maker gives the fine halves by a
	rule: Moog's Theremini prints "All implemented controller numbers 0 - 31 have
	corresponding LSB (fine) controls at locations 32 - 63." and no fine half's
	own number, so a definition that holds fifteen of them asks for numbers from
	39 to 62 that no row carries.

	This is a **weaker** check than finding the number, for two reasons: the page
	never shows the number itself, and a range is matched wherever it appears
	rather than against the row that means it.  It is reported separately for that
	reason, and never counted as found.

	**Which range it was is the whole of what this reading proves, so every one is
	given**, in the order of the page, each once.  One definition's fine half 53
	was found inside `49-54`, which is a row of a table of clock divisions and no
	controller's; and two of another's controllers were inside `1-16`, the chart's
	Basic Channel row, which stands above the `12-31` of its Control Change row.
	The first on the page is as likely the wrong one as the right.  **And the line a range
	stands on is what tells a group of controls from a row of a chart**: `80...87` after
	`Layer A Mod Knobs 1...8` names six controls, and `67-95` in a row of eight ranges
	names none of them.

	Only the inside of a range counts, because an endpoint is already found by
	looking for the number itself, and only a short range counts at all: a manual
	that prints "0-127" for its note numbers would otherwise answer for every
	controller number in the file.  The digits of a form marked as hexadecimal are
	the end of no range.
	"""

	# Rubbed out letter for letter, so that a place in one text is the same place in the
	# other and the line can be given as the page has it.
	scrubbed = _MARKED_HEX.sub(lambda marked: "x" * len(marked.group(0)), text)
	holding: dict[tuple[int, int], tuple[str, str]] = {}

	for found in _PRINTED_RANGE.finditer(scrubbed):
		low, high = int(found.group(1)), int(found.group(2))

		# One range printed twice, or once as `32 - 63` and once as `32-63`, is one range.
		if low < number < high and high - low <= RANGE_SPAN and (low, high) not in holding:
			# From the number itself: the pattern may begin in the white space before it,
			# which is the end of the line above.
			begins = scrubbed.rfind("\n", 0, found.start(1)) + 1
			ends = scrubbed.find("\n", found.end())
			line = text[begins:len(text) if ends < 0 else ends]

			holding[low, high] = (" ".join(found.group(0).split()), " ".join(line.split()))

	return dict(holding.values())


def hexadecimal_form (number: int, text: str) -> str | None:

	"""The hexadecimal form a page prints a number in, as it stands there, if it prints one.

	The form is the two hexadecimal digits of its byte, or any number of them where the
	maker marks the form as hexadecimal.

	Behringer's TD-3-MO is the case: its guide's message table gives its one
	controller as ``Bn 4A xx`` and never prints 74, so a definition holding 74
	asks for a number the page carries only in another base.

	Only a form containing a letter counts, and only standing as a word of its
	own, in capitals as makers print a byte.  A form made only of digits is far
	likelier to be a decimal number than a byte, so ``40`` never stands for 64,
	and a word such as ``B4A`` or ``4AH`` is not ``4A``.

	**Unless the maker marks it as hexadecimal.**  Behringer's Neutron prints its
	modulation wheel's two halves as ``MIDI CC 0x01 (MSB) & MIDI CC 0x21 (LSB)``,
	and ``0x21`` is 33 and nothing else, digits or not.  That form is read in
	either case, since ``0x2a`` is written as often as ``0x2A``, and at any width:
	``0x7`` is 7, and ``0x12C`` is the 300 no two digits can hold.  **A marked form
	is read as one number and never as two bytes**: ``0x045D`` is 1117, where a
	table that means MSB 04 and LSB 5D means 605, and two marked bytes side by
	side, ``0x04 0x5D``, are not read as a pair either.  No definition here cites
	such a page.

	This is a **weaker** check than finding the number: a page of MIDI bytes is
	full of short hexadecimal words, and one is matched wherever it appears rather
	than against the row that means it.  Prose has them too - a Nymphes manual's
	power adapter "rated for at least 1A" reads as 26.  So it is tried last, only
	for a number that would otherwise be missing, and each number found this way
	is named in the report beside the form that matched, never counted as found.
	Where a page has both forms, the marked one is the one named.
	"""

	if not 0 <= number <= 0x3FFF:
		return None

	marked = re.search(
		rf"(?<![0-9A-Za-z])(?<![0-9]\.)0[xX]0*(?i:{number:X})(?![0-9A-Za-z]|\.[0-9])", text)

	if marked is not None:
		return marked.group(0)

	form = f"{number:02X}"

	if number > 0xFF or form.isdigit():
		return None

	return form if re.search(rf"(?<![0-9A-Za-z]){form}(?![0-9A-Za-z])", text) is not None else None


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

	# The printed pages turned to in this document: those cited for it that it has.
	cited: set[int] = dataclasses.field(default_factory=set)

	# A scan of a printed manual is a PDF of pictures: it has pages, and turning to
	# one is still worth checking, but there is no text in it to search.  Saying so
	# is not the same as saying the numbers are absent, and the two must not be
	# reported alike.
	scanned: bool = False

	# The pages this document's source declares as carrying their numbers only in a
	# picture, narrowed to the ones the definition actually cites and the document
	# actually has.  A declaration about a page nobody cites switches nothing off.
	pictured: list[int] = dataclasses.field(default_factory=list)

	# Declared pages that carry no image at all, which is a fault in the
	# declaration rather than in the definition's numbers.
	unpictured: list[int] = dataclasses.field(default_factory=list)


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
	as_byte_pairs: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	as_halves: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	in_a_range: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	across_a_gap: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	as_hex: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	unverifiable: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)

	# The form each number in `as_hex` was found in, as the page has it: `4A`, or `0x21`.
	hex_forms: dict[str, str] = dataclasses.field(default_factory=dict)

	# The ranges each number in `in_a_range` was found inside, as the page has them, the
	# line each range stands on, and those of the numbers whose digits also stand on one
	# line with a gap between them.
	range_forms: dict[str, list[str]] = dataclasses.field(default_factory=dict)
	range_lines: dict[str, str] = dataclasses.field(default_factory=dict)
	also_across_a_gap: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)

	# The NRPNs whose two bytes stand side by side somewhere on a cited page, whatever else
	# found them, and those of them that stand so on a line that also carries their
	# control's label.
	paired: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)
	beside_label: list[tuple[str, str, int]] = dataclasses.field(default_factory=list)

	# Whether each cited page was read only in the document its citation names, and the
	# pages that were cited with no document named and so read in all of them.
	attributed: bool = True
	unattributed: set[int] = dataclasses.field(default_factory=set)


	@property
	def found (self) -> list[tuple[str, str, int]]:

		"""The numbers printed whole on a cited page, which is the one result called found."""

		weaker = (self.missing + self.as_byte_pairs + self.as_halves + self.in_a_range
			+ self.across_a_gap + self.as_hex + self.unverifiable)

		return [entry for entry in self.wanted if entry not in weaker]


	@property
	def lost (self) -> list[Followed]:

		"""The cited documents that no file in the library matches."""

		return [document for document in self.documents if document.path is None]


	@property
	def misdeclared (self) -> list[tuple[str, int]]:

		"""Pages declared as pictured that carry no image at all.

		**This is the half of the declaration that can be checked.** Nothing here
		can tell whether a number is inside a picture, but it can tell that a page
		said to hold one holds none - which catches a mistyped page number and a
		declaration left behind after a maker revised the document.
		"""

		return [
			(document.key, page)
			for document in self.documents for page in document.unpictured
		]


	@property
	def sound (self) -> bool:

		"""True when every citation was followed and every number was on its page.

		A misdeclared pictured page counts against it: the declaration is what
		excuses the numbers, so a declaration that is not true leaves them excused
		by nothing.
		"""

		return not (self.missing or self.unreachable or self.lost or self.misdeclared)


def follow (
	definition: pymidiinstrumentdefs.definition.Definition,
	name: str,
	index: dict[str, pathlib.Path],
	attribute: bool = True,
) -> Result:

	"""Follow one definition's citations into its documents and see what is there.

	**A page cited as `chart p. 2` is read in `chart` alone.**  A page cited with
	no document named is still every document's, because nothing says whose it
	is, and the result holds those pages.

	With ``attribute`` off, every cited page is looked for in every document, as
	it was until 2026-10-13.  A number then counts as found if any cited page of
	any of them carries it, which makes the check weaker the more documents a
	definition cites: `manual p. 2` turns the chart to its second sheet too, and
	seven of one definition's numbers were found there and nowhere its account
	points.
	"""

	result = Result(name = name, cited = cited_pages(definition.source or ""), attributed = attribute)
	result.wanted = wanted_numbers(definition)

	keyed, bare = cited_by_key(definition.source or "", set(definition.sources))
	result.unattributed = bare if attribute else set()

	def cited_in (key: str) -> set[int]:

		"""The printed pages to turn to in one document."""

		return keyed.get(key, set()) | bare if attribute else result.cited

	for key, source in definition.sources.items():
		document = Followed(key = key, source = source)
		document.path = index.get(source.sha256) if source.sha256 else None

		if document.path is not None:
			# A document with no page to turn to is read whole, whatever it is made of.
			# A plain-text implementation chart runs to numbered sections rather than
			# pages; so does a document bound into the back of a manual whose own pages
			# the maker left unnumbered, and that one is a PDF.  Deciding this from the
			# file's extension alone read nothing at all from such a PDF, and said
			# nothing about having read nothing.
			if document.path.suffix.lower() == ".pdf" and source.paginated:
				document.extent = len(reader_for(document.path).pages)
			else:
				document.extent = None

		result.documents.append(document)

	# A page credited to one document has to be in that document.  Read in all of them it
	# was reachable if any had it, which is how a page of the wrong document passed.  A
	# document with no pages has no page to be cited by, so a page credited to one is
	# unreachable like any other.
	if attribute:
		result.unreachable = unreachable_pages(bare, result.documents) | {
			printed for document in result.documents
			for printed in keyed.get(document.key, set()) if not document.covers(printed)}
	else:
		result.unreachable = unreachable_pages(result.cited, result.documents)

	for document in result.documents:
		if document.path is None:
			continue

		if document.extent is None:
			document.text = whole_text(document.path)
			continue

		document.cited = {printed for printed in cited_in(document.key) if document.covers(printed)}
		document.pages = sorted({
			page for printed in document.cited
			for page in [document.source.file_page(printed)]
			if page is not None
		})

		opened = reader_for(document.path)
		document.text = "\n".join(
			opened.pages[page - 1].extract_text() or "" for page in document.pages
		)

		# A declared pictured page counts only if the definition cites it and the
		# document has it, and it is then checked for carrying an image at all.
		for printed in document.source.pictured_pages:
			if printed not in document.cited:
				continue

			page = document.source.file_page(printed)

			if page is None:
				continue

			document.pictured.append(printed)

			try:
				images = len(opened.pages[page - 1].images)
			except Exception:
				# A page whose images cannot be decoded is not a page with none, so
				# the declaration is left standing rather than called a fault.
				continue

			if not images:
				document.unpictured.append(printed)

		# Nothing on the cited pages is either a scan or a run of blank pages, and
		# those need different answers, so ask the whole document before deciding.
		# **Where each page is read in its own document, a document read on no page is
		# not asked**: a scan nobody cites a page of excuses no number.

		if not document.text.strip() and (document.pages or not attribute):
			whole = "".join(page.extract_text() or "" for page in opened.pages)
			document.scanned = not whole.strip()

	# One document ends and the next begins on a new line, never on the same one: a
	# space between them is a gap `numbers_closed_up` closes, so the last digit of one
	# document and the first of the next would be read as a number neither printed.
	printed_text = "\n".join(document.text for document in result.documents)
	printed_numbers = numbers_as_printed(printed_text)
	closed_numbers = numbers_closed_up(printed_text)

	# The one check of a row, made of every NRPN whatever else finds it: see the function.
	labels = {control.name: control.label for control in definition.controls.values()}
	result.paired = [entry for entry in result.wanted
		if entry[1] == "nrpn" and as_a_byte_pair(entry[2], printed_text)]
	result.beside_label = [entry for entry in result.paired
		if beside_its_label(entry[2], labels.get(entry[0]), printed_text)]
	paired = set(result.paired)

	unreadable = any(document.scanned for document in result.documents)

	# A definition that declares some of its cited pages as carrying their numbers
	# only in a picture is in the same position as one citing a scan: the text was
	# read and the numbers were never in it to find.  The declaration has to have
	# been made in the file - nothing is inferred from a page merely having an
	# image on it, because most pages of most manuals do.
	pictured = any(document.pictured for document in result.documents)

	for entry in result.wanted:
		name, kind, number = entry

		if number in printed_numbers:
			continue

		if entry in paired:
			result.as_byte_pairs.append(entry)
			continue

		# Both halves as the page prints them.  A half made by closing a gap is not one:
		# `Level 1 | 10 1` holds no 101, and was once a found 229.
		if kind == "nrpn" and halves_on(number, printed_numbers):
			result.as_halves.append(entry)
			continue

		# **A range before a gap, and both said where both hold.**  Neither order is right
		# for every page: one definition's 53 is printed `5 3` and is also inside a table
		# of clock divisions' `49-54`, and another's 74 is inside the `71-76` that means it
		# and is also the `7 4` of a postcode.  So the range is named, and so is the gap.
		within = ranges_holding(number, printed_text) if kind in ("cc", "lsb") else {}

		if within:
			result.in_a_range.append(entry)
			result.range_forms[f"{name}.{kind}"] = list(within)

			for spelt, line in within.items():
				result.range_lines.setdefault(spelt, line)

			if number in closed_numbers:
				result.also_across_a_gap.append(entry)

			continue

		# The digits with a gap between them on one line: after the readings above,
		# because this one finds numbers nobody printed.
		if number in closed_numbers:
			result.across_a_gap.append(entry)
			continue

		# A number absent from the text of a definition that also cites a scan may
		# be printed on the scan's own pages, where nothing can look for it.  That
		# is an unanswered question rather than a wrong citation, and calling it
		# missing would accuse a definition of a fault nobody has established.

		if unreadable or pictured:
			result.unverifiable.append(entry)
			continue

		# Last of all, and only for a number that would otherwise be missing: a byte
		# is the weakest match there is, and prose prints short hexadecimal words too.

		form = hexadecimal_form(number, printed_text)

		if form is not None:
			result.as_hex.append(entry)
			result.hex_forms[f"{name}.{kind}"] = form
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

		if document.pictured:
			print(f"        declares printed {as_ranges(set(document.pictured))} as carrying "
				f"their numbers only in a picture")

		for printed in document.unpictured:
			print(f"        ⚠ DECLARES printed {printed} as pictured AND IT CARRIES NO IMAGE")

		if document.pages:
			cited = document.cited if result.attributed else result.cited

			print(f"        printed {as_ranges(cited)} → file {as_ranges(document.pages)}")
		elif document.extent is None:
			print("        no pages to turn to, so the whole document was read")
		else:
			print("        no page cited is in it, so none of it was read")

	if result.unreachable:
		print(f"    ⚠ cited but in no document read: printed {as_ranges(result.unreachable)}")

	nobodys = read_in_every_document(result)

	if nobodys:
		print(f"    printed {as_ranges(nobodys)} cited with no document named, so "
			f"read in every document that has pages")

	if not result.wanted:
		print("    no numbers to check")
	else:
		print(f"    {len(result.found)} of {len(result.wanted)} numbers found")

	if result.as_byte_pairs:
		print(
			f"        {len(result.as_byte_pairs)} NRPNs found only as two hexadecimal bytes side by side, "
			f"which is a weaker check"
		)

	if result.as_halves:
		print(
			f"        {len(result.as_halves)} NRPNs found only as the two halves the maker prints, "
			f"which is a weaker check"
		)

	# The tables a definition is read off usually set an NRPN down one way.  So where its
	# NRPNs were found both ways, the fewer are the likelier slips or coincidences, and
	# each of those is named with what was matched.  As many each way, and all are.

	if result.as_byte_pairs and result.as_halves:
		pairs, halves = len(result.as_byte_pairs), len(result.as_halves)

		if pairs == halves:
			which = "as many each way, so all"
		elif pairs < halves:
			which = "the fewer, as bytes side by side,"
		else:
			which = "the fewer, as halves in decimal,"

		print(
			f"        NRPNs were found both ways here, and a table prints one or the other: {which} are "
			f"named to be read on their page"
		)

		if pairs <= halves:
			for name, kind, number in result.as_byte_pairs:
				print(f"            {name}.{kind} = {number}, as {number // 128:02X} {number % 128:02X} side by side")

		if halves <= pairs:
			for name, kind, number in result.as_halves:
				print(f"            {name}.{kind} = {number}, as {number // 128} and {number % 128} in decimal")

	# **THE ROW CHECK, SAID WHEREVER A NUMBER RESTS ON ITS PAIR OR MOST PAIRS STAND BESIDE A LABEL.**
	# A pair is matched wherever it stands, so a slip made on every row passes entire; a pair
	# on the line that carries its control's label is that control's row.  Where most of the
	# NRPNs whose pair is on a cited page at all stand beside their labels, the table's words
	# are the labels, and an NRPN that is not beside its own is named.
	#
	# **One found as itself is named only where it is below 128**, and it is what the naming
	# is for: a byte of the first bank read as decimal, `00 14` held as 14, is printed whole
	# while its own pair, `00 0E`, is nowhere.  That slip cannot make a bigger number.  One of
	# 128 or more printed whole is a number read off another table that prints it so, and
	# naming every row of that table was the price of the measure below.  Those found as
	# decimal halves are not named here either: where both halves and pairs were found, the
	# block above names the fewer.
	#
	# **Measured over the pairs and not over every NRPN**, which was the first measure: a
	# second table, printed in decimal, then diluted the count, and a definition with one
	# table of each named nobody.  **And never on one pair alone**, since where one or two
	# pairs are on the pages in all, a single address row that happens to carry a control's
	# label would otherwise set the naming off.
	#
	# The first set is every pair on a page; a result made by hand may hold the pairs a
	# number rests on and not that, so both are taken.
	on_a_page = set(result.paired) | set(result.as_byte_pairs)
	beside = set(result.beside_label)
	mostly = len(beside) >= 2 and 2 * len(beside) > len(on_a_page)

	if result.as_byte_pairs or mostly:
		whole = set(result.found)
		passed_over = beside | set(result.as_halves) | {entry for entry in whole if entry[2] >= 128}

		print(
			f"        {len(beside)} of {len(on_a_page)} NRPNs whose two bytes stand side by side on a cited "
			f"page stand so on a line that also carries their control's label, which is the sign that "
			f"a number is its own row's"
		)

		if mostly:
			for name, kind, number in result.wanted:
				if kind == "nrpn" and (name, kind, number) not in passed_over:
					print(f"            not beside its label: {name}.{kind} = {number}, "
						f"which would be {number // 128:02X} {number % 128:02X}"
						+ (", and is printed whole on a cited page" if (name, kind, number) in whole else ""))

	if result.in_a_range:
		print(
			f"        {len(result.in_a_range)} controller numbers found only inside a range the maker "
			f"prints, which is a weaker check"
		)

		# A range is matched wherever it stands, so which range it was is what there is to
		# read: every one that holds a number is named, with the numbers found inside it, and
		# under them the line each range stands on, once, where the line has more on it.
		inside: dict[tuple[str, ...], list[str]] = {}
		shown: set[str] = set()

		for name, kind, number in result.in_a_range:
			gapped = ""

			if (name, kind, number) in result.also_across_a_gap:
				gapped = " (and by closing a gap between digits)"

			inside.setdefault(tuple(result.range_forms.get(f"{name}.{kind}", [])), []).append(
				f"{name}.{kind} = {number}{gapped}")

		for ranges, numbers in inside.items():
			if not ranges:
				continue

			print(f"            inside {' and '.join(ranges)}: {', '.join(numbers)}")

			for spelt in ranges:
				line = result.range_lines.get(spelt, spelt)

				if line != spelt and spelt not in shown:
					print(f"                {spelt} stands in: "
						+ (line if len(line) <= 96 else line[:93] + "..."))

				shown.add(spelt)

	if result.across_a_gap:
		print(
			f"        {len(result.across_a_gap)} numbers found only by closing a gap the page leaves "
			f"between digits on one line, which is a weaker check, so each is named to be read on its page"
		)

		for name, kind, number in result.across_a_gap:
			print(f"            {name}.{kind} = {number}")

	if result.as_hex:
		print(
			f"        {len(result.as_hex)} numbers found only in hexadecimal, as the maker prints them, "
			f"which is a weaker check, so each is named to be read on its page"
		)

		for name, kind, number in result.as_hex:
			print(f"            {name}.{kind} = {number}, printed as "
				f"{result.hex_forms.get(f'{name}.{kind}', f'{number:02X}')}")

	if result.unverifiable:
		why = ("a cited page publishes its numbers only in a picture"
			if any(document.pictured for document in result.documents)
			else "a cited document is a scan")

		print(
			f"        {len(result.unverifiable)} NOT CHECKED AT ALL: {why}, "
			f"so no machine here can look for them"
		)

	for name, kind, number in result.missing:
		print(f"        not on any cited page: {name}.{kind} = {number}")

	# **A tick is for a number printed whole on a cited page, and for no other.**  Every
	# number that was not missing was ticked, one nobody could look for among them, beneath
	# a line saying it was not checked at all.
	if verbose:
		how = {entry: said for said, entries in (
			("as two bytes side by side", result.as_byte_pairs),
			("as two halves", result.as_halves),
			("inside a range", result.in_a_range),
			("across a gap", result.across_a_gap),
			("in hexadecimal", result.as_hex),
			("not checked", result.unverifiable),
			("not found", result.missing)) for entry in entries}

		for name, kind, number in result.wanted:
			weaker = how.get((name, kind, number))

			print(f"        {' ' if weaker else '✓'} {name}.{kind} = {number}"
				+ (f"  ({weaker})" if weaker else ""))

	print()


def resolve (name: str) -> tuple[str, pymidiinstrumentdefs.definition.Definition]:

	"""Load a definition by its name, or by a path to a file not on the search path."""

	if name.endswith(".yaml") or name.endswith(".yml"):
		path = pathlib.Path(name)

		return str(path), pymidiinstrumentdefs.load_file(path)

	return name, pymidiinstrumentdefs.load(name)


def read_in_every_document (result: Result) -> set[int]:

	"""The pages a definition cites with no document named, where that leaves a choice.

	A definition with one paged document has nothing to choose between, so a page it
	cites with no key is not one of these.
	"""

	paged = [document for document in result.documents if document.extent]

	return set(result.unattributed) if result.attributed and len(paged) > 1 else set()


def main (argv: list[str] | None = None) -> int:

	"""Check the named definitions, or every one on the search path."""

	parser = argparse.ArgumentParser(
		description = "Check that a definition's numbers appear on the pages it cites.",
		epilog = f"The library of documents is --library, or ${LIBRARY_VARIABLE}.",
	)
	parser.add_argument("names", nargs = "*", help = "definition names or paths; default is all of them")
	parser.add_argument("--library", help = "the folder of maker's documents to read")
	parser.add_argument("--verbose", "-v", action = "store_true", help = "list every number, found or not")
	parser.add_argument("--attribute", action = "store_true",
		help = "what is done without asking since 2026-10-13, and kept so an older command still runs: "
			"read a page cited with a source key before it, as `chart p. 2`, in that document alone")
	parser.add_argument("--pool", action = "store_true",
		help = "read every cited page in every document that has pages, as before: a weaker check, "
			"kept for comparing against")

	arguments = parser.parse_args(argv)

	if arguments.attribute and arguments.pool:
		parser.error("--attribute and --pool ask for opposite things")

	attribute = not arguments.pool
	given = arguments.library or os.environ.get(LIBRARY_VARIABLE)

	if not given:
		parser.error(f"no document library — pass --library, or set ${LIBRARY_VARIABLE}")

	root = pathlib.Path(given).expanduser()

	if not root.is_dir():
		parser.error(f"{root} is not a folder of documents")

	index = library_index(root)
	print(f"{len(index)} documents in {root}")

	if attribute:
		print("each page cited with a source key before it is read in that document alone")
	else:
		print("every cited page is read in every document that has pages (--pool)")

	print()

	names = arguments.names or sorted(pymidiinstrumentdefs.available())
	faults = 0
	nobodys: list[int] = []

	for given_name in names:
		# A definition too broken to load is still an answer, and a gate that
		# printed a traceback here would be read as the tool itself failing.

		try:
			name, definition = resolve(given_name)
		except (pymidiinstrumentdefs.DefinitionError, pymidiinstrumentdefs.DefinitionNotFound, OSError) as fault:
			print(f"{given_name}\n    could not be read: {fault}\n")
			faults += 1
			continue

		result = follow(definition, name, index, attribute = attribute)

		render(result, arguments.verbose)
		faults += not result.sound
		nobodys.append(len(read_in_every_document(result)))

	# How much of the run was still read the weaker way, so that a pass is not taken for
	# more than it is.  Said before the last line, which is the one a gate reads.
	if any(nobodys):
		print(f"{sum(nobodys)} page(s) in {sum(1 for count in nobodys if count)} definition(s) are cited "
			f"with no document named where there is more than one to turn to, and were read in every one")

	print(f"{len(names) - faults} of {len(names)} definitions check out")

	return 1 if faults else 0


if __name__ == "__main__":
	sys.exit(main())
