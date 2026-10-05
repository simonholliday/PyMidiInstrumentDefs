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

**Three things it used to pass over in silence, and now counts.**  A locator it cannot
parse - ``(user guide p. 104)``, where only one word is allowed before the page - was
indistinguishable from no locator at all, and the rule for no locator is to say nothing:
forty-eight quotations across thirteen definitions were neither checked nor reported as
unchecked.  A locator naming a source the definition does not have was collected and then
never printed.  And the summary's third figure added definitions with nothing to check to
quotations that could not be read, so a change of one definition looked like a change of
one quotation.

**A tool that decides what to check by matching a pattern has to say what it matched and
skipped.**  Each of those three read as complete while being silent, which is worse than
either checking or refusing, and the comment on ``QUOTED`` records a fourth of the same
shape from before any of them.

**And a page is read twice before a quotation is called absent.**  ``pypdf`` turns some
makers' ordinary hyphens into an ``x`` - ``nonxregistered`` for ``non-registered`` - and
since ``squash()`` folds hyphens away on purpose, a hyphen *dropped* costs nothing while a
hyphen become a letter is the one thing the folding cannot absorb.  So a quotation the first
reading cannot find is looked for again in a second extractor's reading of the same page,
run in a subprocess on the system Python.  One it finds is on the page it cites and passes,
and the disagreement is printed, because a page two extractors read differently is worth
knowing about whichever of them is right.

It exits non-zero if any quotation is not on the page it cites, if any locator cannot be
read, or if any locator names a source its definition does not have.

**The last two became failures the moment they reached nought**, which was the only moment it
could be done for nothing.  A convention that is reported and not enforced is one that
drifts, and the drift here had already cost five wrong citations in definitions released
months earlier - three of them quotations saying something the maker had not said.
"""

import hashlib
import logging
import os
import pathlib
import re
import subprocess
import sys
import typing

import pypdf

import pymidiinstrumentdefs


# What can be read for text.  A scanned PDF has pages and no text in them, which is
# reported rather than counted as a failure.
READABLE: typing.Final[frozenset[str]] = frozenset({".pdf", ".txt"})

# A quotation and whatever locator follows it, **taken whole and parsed afterwards**.
# Twelve characters is the shortest quotation worth checking; below that a phrase matches
# half the manual.
#
# It used to be one pattern that matched a quotation and a well-formed locator together, and
# that is why two silent skips happened in it.  **A pattern that matches only what it can
# read cannot report what it cannot read**: a locator it did not match looked exactly like a
# quotation with no locator, which this tool passes over without a word.  Taking the
# parenthesis whole and reading it in `read_locator()` separates two questions that were one
# - is there a locator here, and can I understand it - so the second can be answered aloud.
# **THE LOOKAHEAD IS LOAD-BEARING AND WAS LEARNED THE HARD WAY.** Without it this pattern
# matched any parenthesis at all, and a quotation can begin with one: `"(OFF, 1-127)" (p. 37)`
# quotes a value range the maker prints. The prose before it ends at a closing quote, and
# `[^"]{12,}` starting *there* runs to the quote that opens the real quotation - whose next
# character is the `(` of `(OFF`. So the engine matched prose-plus-`OFF, 1-127`, found nothing
# page-shaped in it, skipped it without a word, and **the real quotation after it was never
# looked at**. Two were lost that way, which is this task's own defect in a new costume.
#
# Requiring the parenthesis to be *trying* to cite a page rejects that pairing, so the engine
# advances and finds the true one. It keeps the split that matters: the pattern decides whether
# a locator is there, `read_locator()` decides whether it can be read, and only the second is
# allowed to fail quietly - by being reported.
QUOTED = re.compile(r"[“\"]([^”\"]{12,})[”\"]\s*\((?=[^)]*pp?\.\s*\d)([^)]*)\)")

# **THE WHOLE OF A LOCATOR**: an optional source key, then the page or pages.  `p. 42`,
# `pp. 42-43`, `p. 42, 44`, `guide p. 6`, `manual, p. 110`, and nothing else - which is the
# convention #4475 settled on, and `fullmatch` is how it is enforced rather than suggested.
#
# A comma inside the pages is more pages of one citation, which is how `check_citations.py`
# reads a comma followed by a number too.  A locator naming **two** documents was allowed
# here briefly, for a passage both of a maker's documents print.  The one instrument that
# seemed to need it turned out not to: its two documents word the sentence differently - one
# prints "Bend Up > -64" and the other "Bend Up -64" - so the quotation belonged to one
# document all along and the citation was simply wrong.  **The shape went out with the case
# that justified it.**  A writer who reaches for it now gets an unreadable locator, reported
# and counted, which is the loud failure this task was about.
PAIR = re.compile(r"(?:([a-z][a-z0-9_]*),?\s+)?pp?\.\s*([\d,\s-]+)")

# There is deliberately no second "is this page-shaped" test anywhere below.  `QUOTED`'s
# lookahead is the only place that decides, so a bare source key like `(product_page)` never
# reaches `read_locator()` at all and cannot be mistaken for a locator this tool failed to
# read.  A guard repeating that test would always pass, and would suggest a case it catches.

# The other shape a locator takes, for a document with no pages to cite: the source's own
# key, as in `"polyphony up to 24 voices" (product_page)`.  A key followed by a page is the
# paged form above and deliberately does not match here - the page is the more precise
# locator and is the one worth checking.
BY_SOURCE = re.compile(r"[“\"]([^”\"]{12,})[”\"]\s*\(([a-z][a-z0-9_]*)\)")

# **WHY A LOCATOR THIS TOOL CANNOT READ IS NOW REPORTED RATHER THAN SKIPPED.**
#
# A locator that did not parse was indistinguishable from no locator at all, and the rule for
# a quotation with no locator is to pass over it without a word.  So `(user guide p. 104)` -
# two words where the old pattern allowed one - was not checked, was not counted as
# unchecked, and nothing in this tool's output said it existed.  When this was found,
# forty-eight quotations across thirteen definitions were in that state, and
# `novation/circuit_tracks` reported fourteen of fourteen while holding thirty-four
# quotations that cite a page.  Reading them where they stood turned up five that were not on
# the pages they cite, in definitions that had been released for months.
#
# The convention is therefore `(p. N)` or `(source_key p. N)`, exactly one pair, and
# `read_locator()` refuses anything else out loud rather than passing it over.  #4475.

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
	# **A SOFT HYPHEN GOES ENTIRELY**, because it is a discretionary line break and not a
	# character of the word. Elektron's manuals carry between 86 and 320 of them each - the
	# Octatrack's 309 - and the text layer returns "mes­ sages" where the page prints
	# "messages" unbroken. So a quotation spanning one could never be found, and every
	# Elektron definition here was written around that without anybody naming it.
	# This can only make more quotations match and never fewer: nothing a definition could
	# type contains U+00AD, so removing it cannot create a false match.
	"­": "",
}


# A maker's own cross-reference, printed inside its own sentence: the MiniFreak manual's
# page 81 reads "sending the MiniFreak a MIDI [p.112] Start command", and a definition
# quoting that sentence as a reader sees it is right rather than wrong.
CROSS_REFERENCE = re.compile(r"\[\s*p\.?\s*\d+\s*\]", re.IGNORECASE)


# A second reading of one page, asked for only where the first reading could not find a
# quotation.  `pypdf` turns some makers' ordinary hyphens into an `x`: across one 126-sheet
# Elektron manual it reads 2,816 hyphens where PyMuPDF reads 3,764, and returns
# `nonxregistered` where the page prints `non-registered`.  `squash()` folds hyphens away on
# purpose, so a hyphen an extractor *drops* costs nothing, and this - a hyphen become a
# letter - is the one case that folding cannot absorb.  #4483.
#
# **IT IS A SUBPROCESS AND NOT AN IMPORT, DELIBERATELY.**  #2522 splits the interpreters so
# that the two readers of an instrument cannot reach for the same extractor: `fitz` is on the
# system Python alone and `pypdf` in the project venv alone.  That rule is about *readers*,
# and this is a tool, so the exception is a narrow one - but installing `fitz` into the venv
# would make the wrong thing merely inadvisable for a second reader where it is now
# impossible.  So it stays out, and the rule stays a fact about the interpreter rather than a
# convention somebody has to remember.
SECOND_READER = "/usr/bin/python3"

SECOND_READING = """
import sys

import fitz

document = fitz.open(sys.argv[1])
sys.stdout.write(document[int(sys.argv[2]) - 1].get_text())
"""


def read_again (path: pathlib.Path, file_page: int) -> str | None:

	"""One file page of a document as a second extractor reads it, or nothing at all.

	Nothing where that extractor is not installed, and that is not a failure: the run is
	then honest about having had one reading of the page rather than two.
	"""

	try:
		done = subprocess.run(
				[SECOND_READER, "-c", SECOND_READING, str(path), str(file_page)],
				capture_output = True, text = True, timeout = 120)

	except (OSError, subprocess.SubprocessError):
		return None

	return done.stdout if done.returncode == 0 else None


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


def flowed (text: str) -> str:

	"""The file's prose with its line breaks and comment markers closed up.

	A comment runs over several lines, so a quotation or the locator after it can be broken
	across two of them.  **Every search in this tool reads this rather than the file, and
	they must all read the same thing**: a sweep written against the raw text instead
	invented an unparsable ``(manual # p. 95)`` for every citation in the corpus that
	happened to wrap, which looked exactly like a finding and was not.  It was three copies
	of this one expression before that happened.
	"""

	return re.sub(r"\n\s*#?\s*", " ", text)


def read_locator (locator: str) -> tuple[str | None, list[int]] | None:

	"""The source and pages a locator names, or nothing at all if it cannot be read.

	Only ever called about a locator that is trying to cite a page, so ``None`` means one
	thing: **this cites a page and I cannot understand it**, which is reported rather than
	passed over.  Anything the pattern does not account for whole - a two-word document name,
	a version number, the writer's own aside after the page - is that answer.
	"""

	match = PAIR.fullmatch(locator.strip())

	if match is None:
		return None

	source, cited = match.groups()

	return source or None, [int(n) for n in re.findall(r"\d+", cited)]


def quotations (text: str) -> list[tuple[str, str | None, list[int]]]:

	"""Every quoted passage in the file with a page citation, the source it names, and the pages.

	The source is whatever the locator put before the page - `(guide p. 6)` gives `guide` -
	and is nothing where the citation is the bare `(p. 6)`.  A definition with one document
	has no reason to name it; one with four has every reason, and naming it is what lets
	the page be looked for in the right place.
	"""

	found = []

	for quotation, locator in QUOTED.findall(flowed(text)):
		read = read_locator(locator)

		if read is not None:
			found.append((quotation, read[0], read[1]))

	return found


def named_quotations (text: str, keys: typing.Iterable[str]) -> list[tuple[str, str]]:

	"""Every quoted passage whose locator is one of these source keys.

	A document with no pages has no page to cite, so a definition quoting one names the
	document instead.  Only the definition's own source keys count, so an ordinary
	parenthesis after a quotation is not mistaken for a locator.
	"""

	known = set(keys)

	return [(quotation, where)
		for quotation, where in BY_SOURCE.findall(flowed(text)) if where in known]


def unreadable_locators (text: str) -> list[tuple[str, str]]:

	"""Every quotation whose locator looks like a page citation this tool cannot read.

	``QUOTED`` takes the parenthesis whole, so this is every quotation whose locator is trying
	to cite a page and cannot be read.  Reporting them is the whole purpose: they are the
	quotations that would otherwise be skipped without a word.
	**The count is nought and the run now fails if it is not**, which it could only be made
	to do once the forty-eight that were there had been read and put right.
	"""

	return [(quotation, " ".join(locator.split()))
		for quotation, locator in QUOTED.findall(flowed(text))
		if read_locator(locator) is None]


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


class Tally (typing.NamedTuple):

	"""What one definition's check came to.  Every field counts quotations but one.

	**The third figure used to add two different things together.**  A definition with
	nothing to check returned 1, meaning one definition, and a definition whose documents
	could not be read returned a count of its quotations - so "27 could not be checked"
	was definitions and quotations summed.  That is what made a change of one definition
	show up as a change of one quotation, which is the only reason the silent skip above
	was found at all.  Counting them apart costs two fields and lets each figure answer
	one question.

	Every field defaults to nought so that a running total starts at ``Tally()``.
	"""

	# On the page they cite, or inside the source they name.
	passed: int = 0

	# Not there, which is the only thing that fails the run.
	missing: int = 0

	# Counted in `passed` as well, because the page does carry the words: these are the
	# ones only the second extractor could find.  A figure above nought says two readings
	# of one page differ, which is worth knowing whichever is right.
	disagreed: int = 0

	# They cite a page or a source, and no document that could hold it could be read: a
	# scan, or a manual nobody has put in the library.
	unchecked: int = 0

	# Their locator looks like a page citation and this tool cannot read it.
	unreadable: int = 0

	# Their locator names a source this definition does not have, which is a mistake in
	# the file.  **These were collected and never printed** until #4475.
	misnamed: int = 0

	# **IN DEFINITIONS, NOT QUOTATIONS**, and the only field that is: one if this
	# definition quotes nothing with a locator at all, nought otherwise.
	nothing_to_check: int = 0


def check (name: str, path: pathlib.Path, index: dict[str, pathlib.Path]) -> Tally:

	"""Check one definition, printing what it found."""

	definition = pymidiinstrumentdefs.load_file(path)
	held, absent = documents(definition, index)
	body = path.read_text(encoding = "utf-8")
	found = quotations(body)
	named = named_quotations(body, (definition.sources or {}))
	unreadable = unreadable_locators(body)

	print(f"\n{name}")

	for line in absent:
		print(f"    {line}")

	# Said before anything else, and said even where the definition is otherwise clean,
	# because the point of the figure is that nobody knew these quotations existed.
	if unreadable:
		print(f"    {len(unreadable)} quotations have a locator this tool cannot read, so they "
			f"are NOT CHECKED - the convention is a single word before the page:")

		for quotation, locator in unreadable:
			print(f"        ({locator}): {quotation[:88]}")

	if not found and not named:
		print(f"    no quotation in it cites a page or a source, so there is nothing to check")
		return Tally(unreadable = len(unreadable), nothing_to_check = 1)

	if not held:
		print(f"    {len(found) + len(named)} quotations cite a source and none could be read")
		return Tally(unchecked = len(found) + len(named), unreadable = len(unreadable))

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
	disagreed: list[tuple[str, str, int]] = []
	passed = 0

	for quotation, source, cited in found:
		parts = pieces(quotation)
		where = None

		# A quotation that names its source is looked for in that document alone, which is
		# the stronger check: a page number that happens to exist in one of the other three
		# cannot pass it. A name that is not one of this definition's sources is a mistake
		# in the file rather than a reason to fall back - and **it used to be collected and
		# never printed**, so seven of them across three definitions had never been checked
		# against anything when #4475 found them.
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
			# **BEFORE CALLING A QUOTATION ABSENT, ASK THE OTHER EXTRACTOR.** The page may
			# carry the words and this tool's reading of it may be the thing at fault, which
			# is what #4483 was: a correct quotation reported as on "no page of any document
			# held", the strongest wording here, because `pypdf` had turned a hyphen into an
			# `x`. A quotation the second reading finds **is** on the page it cites, so it
			# passes - and the disagreement is printed, because a page two extractors read
			# differently is worth knowing about whichever of them is right.
			second = None

			for document in looking:
				for number in cited:
					at = document.source.file_page(number)

					if at is None or not 1 <= at <= len(document.pages):
						continue

					again = read_again(document.path, at)

					if again is not None and all(part in squash(again) for part in parts):
						second = (document.name, number)
						break

				if second:
					break

			if second is not None:
				disagreed.append((quotation, second[0], second[1]))
				passed += 1
				continue

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

	if disagreed:
		print(f"    {len(disagreed)} of those were found only by the second extractor, so the "
			f"page carries the words and pypdf {pypdf.__version__} reads it differently:")

		for quotation, in_document, number in disagreed:
			print(f"        {in_document} printed p. {number}: {quotation[:84]}")

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

		# **THE STRONGEST WORDING THIS TOOL HAS, SAID ABOUT THE DEFINITION, WHEN THE FAULT
		# CAN BE THE TOOL'S.**  Every page here was read by one extractor, and `pypdf` turns
		# some makers' ordinary hyphens into an `x`: across one 126-sheet Elektron manual it
		# reads 2,816 hyphens where PyMuPDF reads 3,764, and returns `nonxregistered`,
		# `highxpass`, `hixhat` - exactly the words a MIDI definition wants to quote.
		# `squash()` drops hyphens on both sides on purpose, so a *lost* hyphen is harmless
		# and this, a hyphen replaced by a letter, is the one case the folding cannot absorb.
		# So the reader who meets this has to be told what read the page, or they conclude
		# their own transcription is wrong and reword a correct quotation.  #4483.
		if not elsewhere:
			print(f"          read with pypdf {pypdf.__version__}, and that is one reading of "
				f"the page rather than the page: if the quotation crosses a hyphen, check "
				f"what is printed before changing it (#4483)")

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

	# A locator naming a source the definition does not have.  The loop above declines to
	# fall back to searching every document, which is right - a page number that happens to
	# exist in another manual must not pass a quotation credited to one this definition does
	# not hold - but it then dropped the quotation without a word, so the file's mistake was
	# invisible and the quotation was never checked against anything.
	for quotation, source in misnamed:
		print(f"\n      NO SOURCE NAMED {source!r}: {quotation[:110]}")
		print(f"          this definition's sources are: "
			f"{', '.join(sorted(definition.sources or {})) or 'none'}")

	return Tally(
			passed = passed + named_passed,
			missing = len(missing) + len(elsewhere_missing),
			disagreed = len(disagreed),
			unchecked = unchecked,
			unreadable = len(unreadable),
			misnamed = len(misnamed))


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

	total = Tally()
	failed: list[str] = []
	unreadable_in: list[str] = []

	for name in wanted:
		path = corpus / f"{name}.yaml"

		if not path.exists():
			print(f"\n{name}\n    no such definition")
			return 2

		tally = check(name, path, index)
		total = Tally(*(running + one for running, one in zip(total, tally)))

		# Any of the three is a failure, so any of the three names the definition.  A locator
		# nobody can read means a quotation checked against nothing, which is as bad as one
		# checked and wrong - worse, because it looks like neither.
		if tally.missing or tally.unreadable or tally.misnamed:
			failed.append(name)

		if tally.unreadable:
			unreadable_in.append(name)

	print(f"\n{total.passed} quotations check out across {len(wanted)} definition(s); "
		f"{total.missing} are not on the page they cite; "
		f"{total.unchecked} could not be checked")

	# Said as its own sentence rather than folded into the figures above, because it is a
	# count of quotations nobody had looked at rather than a count of checks that ran.
	print(f"{total.unreadable} quotations across {len(unreadable_in)} definition(s) have a "
		f"locator this tool cannot read, so they are not in any figure above"
		+ (f": {', '.join(unreadable_in)}" if unreadable_in else ""))

	if total.disagreed:
		print(f"{total.disagreed} of those were found only by the second extractor, so two "
			f"readings of one page differ - counted above as checking out, because the page "
			f"does carry the words")

	if total.misnamed:
		print(f"{total.misnamed} quotations name a source their definition does not have")

	print(f"{total.nothing_to_check} definition(s) quote nothing with a locator")

	if failed:
		print(f"not clean: {', '.join(failed)}")

	return 1 if total.missing or total.unreadable or total.misnamed else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv))
