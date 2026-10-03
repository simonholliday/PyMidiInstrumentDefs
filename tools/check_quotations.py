#!/usr/bin/env python3

"""Check that every passage a definition quotes is printed on the page it cites.

``check_citations.py`` beside this one checks that every **number** in a definition
appears on a cited page.  It says nothing about the prose, and a definition quotes its
manual dozens of times with a page beside each quotation.  **A page number copied from
the wrong line is invisible to every other check here**, and sends a reader to a page
that does not carry what they were promised.

So this finds every quoted passage with a page citation after it and looks for that
passage on that page of the document itself.  Run against the corpus the first time, it
found five things: four citations a page or two out, and one quotation that was a
paraphrase of the maker's sentence rather than the maker's sentence.

**What a pass means, and what it does not.**  A pass means the cited page carries the
words.  It does not mean the quotation is apt, that the page says what the definition
concludes from it, or that anything is missing.  Nor does it look at a quotation with no
page beside it, since there is nothing to check it against.

Four things make the comparison about the words rather than the typesetting, and each is
there because a correct quotation failed without it:

* **The spaces come out.**  A maker's text layer puts them inside words, so "FI LTER"
  and "FILTER" are the same word on the page and differ as strings.
* **The case comes out.**  A manual sets a table heading in capitals and a definition
  quotes it in a sentence.
* **The punctuation is folded**, including quote marks: a definition quoting a sentence
  that itself contains a quoted word has to change the maker's double quotes to single
  ones, because the quotation is already inside double quotes.
* **The maker's own cross-references come out.**  One manual's page reads "sending the
  MiniFreak a MIDI [p.112] Start command", and a definition quoting that sentence as a
  reader sees it is right rather than wrong.

A quotation split by an ellipsis, or adapted with a square bracket - "make[s] it
possible" for a page that says "makes it possible" - is matched in the pieces either
side.  Where every clause is on the cited page but its text layer does not run them
together, which is what a specification table does, that is reported as the weaker thing
it is rather than as a wrong page: the same answer the citation tool gives a number it
finds only inside a range the maker prints.

Documents are found the way the citation tool finds them, **by the SHA-256 a definition
records**, so a match proves the same file rather than one with a similar name.  Each
document's own ``page_offset`` and ``pages_per_sheet`` are applied, because printed page
and file page differ from document to document, and one manual here prints two pages to
a sheet.  An unpaginated document is skipped rather than guessed at, and a scan is
reported as one.

A quotation counts as found if it is on the cited page of **any** of the definition's
documents, since a citation names a page and not which document it is in.

::

	export PYMIDIINSTRUMENTDEFS_LIBRARY=/path/to/manuals
	python tools/check_quotations.py                      # every bundled definition
	python tools/check_quotations.py moog/subsequent_37   # one, by name

It exits non-zero if any quotation is not on the page it cites.
"""

import hashlib
import logging
import os
import pathlib
import re
import sys
import typing

import pypdf

import pymidiinstrumentdefs


# What can be read for text.  A scanned PDF has pages and no text in them, which is
# reported rather than counted as a failure.
READABLE: typing.Final[frozenset[str]] = frozenset({".pdf", ".txt"})

# A quotation and the page it is credited to: "...text..." (p. 42), or (pp. 42-43), or -
# where a definition cites more than one document - "...text..." (guide p. 6) and
# "...text..." (manual, p. 110), which name the source the page belongs to.
# Twelve characters is the shortest that is worth checking; below that a phrase matches
# half the manual.
#
# **THE NAMED FORMS WERE SILENTLY SKIPPED** until the comment below was read against this
# pattern: it said a key followed by a page "is the paged form above", and this did not
# match one.  Thirty-three quotations across eight definitions were therefore never
# verified, and every one of them looked verified in the count.  Naming the source now
# makes a quotation *more* strongly checked rather than not checked at all, because the
# page is then looked for in that document alone.
QUOTED = re.compile(
	r"[“\"]([^”\"]{12,})[”\"]\s*\((?:([a-z][a-z0-9_]*),?\s+)?p{1,2}\.\s*([\d,\s-]+)\)")

# The other shape a locator takes, for a document with no pages to cite: the source's own
# key, as in `"polyphony up to 24 voices" (product_page)`.  A key followed by a page is the
# paged form above and deliberately does not match here - the page is the more precise
# locator and is the one worth checking.
BY_SOURCE = re.compile(r"[“\"]([^”\"]{12,})[”\"]\s*\(([a-z][a-z0-9_]*)\)")

# A quotation is retyped with the keyboard's punctuation and the page prints the
# typesetter's, so the two never match on the character.
FOLDED: typing.Final[dict[str, str]] = {
	# Quote marks go entirely. A definition quoting a sentence that itself contains a
	# quoted word has to change the maker's double quotes to single ones, because the
	# quotation is already inside double quotes: the MicroFreak manual's page 77 reads
	# in "Play" mode and the definition quotes it as in 'Play' mode.
	"“": "", "”": "", "‘": "", "’": "", '"': "", "'": "",
	"ʼ": "", "′": "",
	"–": "-", "—": "-", "…": "...",
}


# A maker's own cross-reference, printed inside its own sentence: the MiniFreak manual's
# page 81 reads "sending the MiniFreak a MIDI [p.112] Start command", and a definition
# quoting that sentence as a reader sees it is right rather than wrong.
CROSS_REFERENCE = re.compile(r"\[\s*p\.?\s*\d+\s*\]", re.IGNORECASE)


def squash (text: str) -> str:

	"""Text reduced to the letters and digits of its words, for comparing two readings.

	The spaces go because a maker's text layer puts them inside words, so "FI LTER" and
	"FILTER" are the same word on the page and differ as strings. **The case goes too**:
	a manual sets a table heading in capitals and a definition quotes it in a sentence,
	which is ordinary practice here and is not what this check is looking for.

	**And the hyphens go**, for the reason the spaces do. A typesetter breaks a word at the
	end of a line and the text layer keeps the break: the Analog Rytm MKII's page 21 reads
	"can be voiced simulta-neously with the eight physical voices", and a definition quoting
	the word the page *prints* is right rather than wrong. Dropping the hyphen on one side
	only would then break a real one - "built-in" broken as "built-\nin" matched before this
	and must still - so it is dropped on both, which costs only the ability to tell
	"pre-delay" from "predelay", a difference no reader of a citation is misled by.
	"""

	for printed, typed in FOLDED.items():
		text = text.replace(printed, typed)

	text = CROSS_REFERENCE.sub("", text)

	return re.sub(r"[\s-]+", "", text).lower()


def pieces (quotation: str) -> list[str]:

	"""The parts of a quotation that must all be on one page for it to be found there.

	A quotation is split at two things the file does to the maker's words. An ellipsis
	is the file leaving something out. **A square bracket is the file adapting a word
	to its own sentence** - "make[s] it possible to play Digitakt" quotes a page that
	says "makes it possible" - so the bracket and what surrounds it cannot be matched
	as one string, and each side is looked for instead.
	"""

	text = squash(quotation)

	for part in re.findall(r"\[[^\]]*\]", text):
		text = text.replace(part, "...")

	return [part for part in text.split("...") if part]


def library_index (root: pathlib.Path) -> dict[str, pathlib.Path]:

	"""Every readable document under ``root``, keyed by the SHA-256 of its bytes."""

	index: dict[str, pathlib.Path] = {}

	for path in sorted(root.rglob("*")):
		if path.is_file() and path.suffix.lower() in READABLE:
			index[hashlib.sha256(path.read_bytes()).hexdigest()] = path

	return index


def pages_of (path: pathlib.Path) -> list[str]:

	"""Each page of the document as text, or one entry for a file with no pages."""

	if path.suffix.lower() == ".txt":
		return [path.read_text(encoding = "utf-8", errors = "replace")]

	logging.disable(logging.WARNING)

	return [page.extract_text() or "" for page in pypdf.PdfReader(str(path)).pages]


class Document (typing.NamedTuple):

	"""One of a definition's sources, found in the library and read for text."""

	name: str
	path: pathlib.Path
	source: typing.Any
	pages: list[str]


	def printed (self, number: int) -> str | None:

		"""The text of the page this document prints that number on, if it has one.

		The arithmetic is the format's own, because there is more to it than an
		offset: one manual here prints two pages to a sheet, so its printed page 61
		and printed page 60 are both on file page 30.
		"""

		at = self.source.file_page(number)

		if at is None or not 1 <= at <= len(self.pages):
			return None

		return self.pages[at - 1]


	def where (self, parts: list[str]) -> list[int]:

		"""Every printed page number whose own page carries all of these parts."""

		return [number for number in range(1, len(self.pages) * self.source.pages_per_sheet + 1)
			if (page := self.printed(number)) is not None
			and all(part in squash(page) for part in parts)]


def documents (definition: typing.Any, index: dict[str, pathlib.Path]) -> tuple[list[Document], list[str]]:

	"""The definition's sources, as far as they can be found and read."""

	found: list[Document] = []
	absent: list[str] = []

	for name, source in (definition.sources or {}).items():
		if not source.sha256:
			absent.append(f"{name}: records no sha256")
			continue

		path = index.get(source.sha256)

		if path is None:
			absent.append(f"{name}: no document in the library hashes to {source.sha256[:16]}")
			continue

		pages = pages_of(path)

		if not any(page.strip() for page in pages):
			absent.append(f"{name}: {path.name} is a scan, so no quotation can be looked for in it")
			continue

		found.append(Document(name, path, source, pages))

	return found, absent


def quotations (text: str) -> list[tuple[str, str | None, list[int]]]:

	"""Every quoted passage in the file with a page citation, the source it names, and the pages.

	A comment is folded over several lines, so the file's own line breaks and comment
	markers are closed up before the quotations are found.

	The source is whatever the locator put before the page - `(guide p. 6)` gives `guide` -
	and is nothing where the citation is the bare `(p. 6)`.  A definition with one document
	has no reason to name it; one with four has every reason, and naming it is what lets
	the page be looked for in the right place.
	"""

	flowed = re.sub(r"\n\s*#?\s*", " ", text)

	return [(quotation, source or None, [int(n) for n in re.findall(r"\d+", cited)])
		for quotation, source, cited in QUOTED.findall(flowed)]


def named_quotations (text: str, keys: typing.Iterable[str]) -> list[tuple[str, str]]:

	"""Every quoted passage whose locator is one of these source keys.

	A document with no pages has no page to cite, so a definition quoting one names the
	document instead.  Only the definition's own source keys count, so an ordinary
	parenthesis after a quotation is not mistaken for a locator.
	"""

	flowed = re.sub(r"\n\s*#?\s*", " ", text)
	known = set(keys)

	return [(quotation, where) for quotation, where in BY_SOURCE.findall(flowed) if where in known]


def with_pages (held: list[Document]) -> list[Document]:

	"""The documents a page citation could be found in at all.

	A definition may cite both kinds at once: a scanned manual nobody here can search, and
	a saved web page anybody can.  Judging "p. 27" against the web page finds it absent
	every time, because an unpaginated document has no page to turn to - so a quotation
	whose definition has no searchable paginated source is **unchecked** rather than wrong.
	That is the distinction the citation tool already keeps, and reporting a maker's own
	words as a mistake is the one failure that stops this tool's output being read.
	"""

	return [document for document in held if document.source.paginated]


def check (name: str, path: pathlib.Path, index: dict[str, pathlib.Path]) -> tuple[int, int, int]:

	"""Check one definition, printing what it found.  Returns found, missing, unquoted."""

	definition = pymidiinstrumentdefs.load_file(path)
	held, absent = documents(definition, index)
	body = path.read_text(encoding = "utf-8")
	found = quotations(body)
	named = named_quotations(body, (definition.sources or {}))

	print(f"\n{name}")

	for line in absent:
		print(f"    {line}")

	if not found and not named:
		print(f"    no quotation in it cites a page or a source, so there is nothing to check")
		return 0, 0, 1

	if not held:
		print(f"    {len(found) + len(named)} quotations cite a source and none could be read")
		return 0, 0, len(found) + len(named)

	print(f"    {len(held)} document(s): " + ", ".join(
		f"{d.name} [{len(d.pages)} sheets, offset {d.source.page_offset:+d}"
		+ (f", {d.source.pages_per_sheet} printed pages to a sheet]" if d.source.pages_per_sheet != 1 else "]")
		for d in held))

	turnable = with_pages(held)
	unchecked = 0

	if found and not turnable:
		print(f"    {len(found)} quotations cite a page, and no document with pages could be read")
		unchecked, found = len(found), []

	missing: list[tuple[str, list[int]]] = []
	partly: list[tuple[str, list[int]]] = []
	misnamed: list[tuple[str, str]] = []
	passed = 0

	for quotation, source, cited in found:
		parts = pieces(quotation)
		where = None

		# A quotation that names its source is looked for in that document alone, which is
		# the stronger check: a page number that happens to exist in one of the other three
		# cannot pass it. A name that is not one of this definition's sources is a mistake
		# in the file rather than a reason to fall back.
		if source is not None and source not in (definition.sources or {}):
			misnamed.append((quotation, source))
			continue

		looking = [d for d in turnable if d.name == source] if source else turnable

		if source and not looking:
			unchecked += 1
			continue

		for document in looking:
			for number in cited:
				page = document.printed(number)

				if page is not None and all(part in squash(page) for part in parts):
					where = (document.name, number)
					break

			if where:
				break

		if where is None:
			# Every clause on the cited page, but not run together by its text layer: a
			# specification table read across its cells, or a parameter's name joined to
			# its description with a dash. The citation is sound and the match cannot be
			# made, so this is reported as the weaker thing it is rather than as a wrong
			# page - the same answer the citation tool gives a number it finds only
			# inside a range the maker prints.
			clauses = [squash(clause) for clause in re.split(r"[:;,]|\s-\s", quotation)]
			clauses = [clause for clause in clauses if len(clause) > 6]

			split = clauses and any(
				all(clause in squash(page) for clause in clauses)
				for document in looking
				for number in cited
				if (page := document.printed(number)) is not None
			)

			(partly if split else missing).append((quotation, cited))
			continue

		passed += 1

	if found:
		print(f"    {passed} of {len(found)} quotations are on the page they cite")

	if partly:
		print(f"    {len(partly)} more have every clause on the cited page, but its text layer "
			f"does not run them together, which is a weaker check:")

		for quotation, cited in partly:
			print(f"        p. {', '.join(str(n) for n in cited)}: {quotation[:95]}")

	for quotation, cited in missing:
		print(f"\n      NOT ON p. {', '.join(str(n) for n in cited)}: {quotation[:120]}")

		parts = pieces(quotation)
		elsewhere = [f"{d.name} printed p. {number}" for d in turnable for number in d.where(parts)]

		print(f"          it is on: {', '.join(elsewhere) if elsewhere else 'no page of any document held'}")

	# A quotation that names a source rather than a page is looked for in the whole of that
	# document, which is what `paginated: false` means: there is no page to turn to.
	by_name = {document.name: document for document in held}
	elsewhere_missing: list[tuple[str, str]] = []
	named_passed = 0

	for quotation, key in named:
		named_document = by_name.get(key)

		if named_document is None:
			elsewhere_missing.append((quotation, key))
			continue

		whole = squash("\n".join(named_document.pages))

		# An empty document makes every quotation look absent, so it is this tool's fault
		# before it is a finding.  `documents()` has already dropped a scan, so reaching
		# here with nothing to search means something else is wrong.
		assert whole, f"{key} read as empty, which is a bug in this tool and not a finding"

		if all(part in whole for part in pieces(quotation)):
			named_passed += 1
		else:
			elsewhere_missing.append((quotation, key))

	if named:
		print(f"    {named_passed} of {len(named)} quotations that name a source are in it")

	for quotation, key in elsewhere_missing:
		print(f"\n      NOT IN {key}: {quotation[:120]}")

	return passed + named_passed, len(missing) + len(elsewhere_missing), unchecked


def main (argv: list[str]) -> int:

	"""Check every definition named, or every bundled one."""

	root = os.environ.get("PYMIDIINSTRUMENTDEFS_LIBRARY")

	if not root:
		print("PYMIDIINSTRUMENTDEFS_LIBRARY names the folder the documents are in")
		return 2

	index = library_index(pathlib.Path(root))
	print(f"{len(index)} readable documents in {root}")

	corpus = pathlib.Path(pymidiinstrumentdefs.__file__).parent / "corpus"
	wanted = argv[1:] or pymidiinstrumentdefs.available([corpus])

	found = missing = unquoted = 0
	failed: list[str] = []

	for name in wanted:
		path = corpus / f"{name}.yaml"

		if not path.exists():
			print(f"\n{name}\n    no such definition")
			return 2

		a, b, c = check(name, path, index)
		found += a
		missing += b
		unquoted += c

		if b:
			failed.append(name)

	print(f"\n{found} quotations check out across {len(wanted)} definition(s); "
		f"{missing} are not on the page they cite; {unquoted} could not be checked")

	if failed:
		print(f"not clean: {', '.join(failed)}")

	return 1 if missing else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv))
