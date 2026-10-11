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
locator beside it, since there is nothing to check it against.

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

**And a page is read twice before a quotation is called absent**, and so is a whole document
where the locator names no page, wherever the second extractor is there to ask.  ``pypdf``
turns some makers' ordinary hyphens into an ``x`` - ``nonxregistered`` for
``non-registered`` - and
since ``squash()`` folds hyphens away on purpose, a hyphen *dropped* costs nothing while a
hyphen become a letter is the one thing the folding cannot absorb.  So a quotation the first
reading cannot find is looked for again in a second extractor's reading of the same page,
run in a subprocess on the system Python.  One it finds is on the page it cites and passes,
and the disagreement is printed, because a page two extractors read differently is worth
knowing about whichever of them is right.  Where the second extractor is not installed, or
gives nothing, the report says so of a quotation located without a page that it calls absent:
it had one reading of the document it was looked for in.

**A document with no pages has places in it all the same, and two more shapes of locator
name them.**  ``(os_updates, #243)`` names a source with no pages and then an entry in it, and
is looked for in that source; what follows the comma is the writer's note and is not checked.
``(15.6)`` is a number alone, a section's or a release's, and names no document, so the passage
is looked for in every document the definition cites that could be read, and the report says
which holds it.  Both used to read as no locator at all, and two definitions reported nothing
to check while holding quotations located one of these two ways.

It exits non-zero if any quotation is not on the page it cites, not in the source it names or,
where it gives a number alone, in none of the documents cited when all of them could be read;
if any locator cannot be read; or if a page locator names a source its definition does not
have.

**The last two became failures the moment they reached nought**, which was the only moment it
could be done for nothing.  A convention that is reported and not enforced is one that
drifts, and the drift here had already cost five wrong citations in definitions released
months earlier - three of them quotations saying something the maker had not said.
"""

import argparse
import concurrent.futures
import contextlib
import functools
import hashlib
import io
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
#
# **AND THE EMPHASIS MARKERS ARE PART OF THE PATTERN FOR A REASON.**  It allowed only
# whitespace between the closing quote mark and the locator, so `"..."**  (p. 21)` - a
# quotation emphasised in this project's own house style, with the markers closing before the
# parenthesis - did not match, and the quotation was skipped without a word.  **It looks
# located to a reader and it is not**, which makes it the one silence a writer cannot find by
# reading their own file carefully.  Three definitions were in that state when it was found;
# their files were put right, and the pattern was not, so the next writer to type it would
# have paid again.  Allowing `*` and `_` here is strictly better than asking everybody to
# remember, and it can only ever match more.
QUOTED = re.compile(r"[“\"]([^”\"]{12,})[”\"][\s*_]*\((?=[^)]*pp?\.\s*\d)([^)]*)\)")

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

# There is deliberately no second "is this page-shaped" test on the way to `read_locator()`.
# `QUOTED`'s lookahead is the only place that decides, so a bare source key like
# `(product_page)` never reaches it at all and cannot be mistaken for a locator this tool
# failed to read.  A guard repeating that test would always pass, and would suggest a case it
# catches.  `PAGE_SHAPED` below asks the same question in the same words for the coverage
# figures and for the place locators, which must leave a page citation to this pattern.

# The other shape a locator takes, for a document with no pages to cite: the source's own
# key, as in `"polyphony up to 24 voices" (product_page)`.  A key followed by a page is the
# paged form above and deliberately does not match here - the page is the more precise
# locator and is the one worth checking.
# The emphasis markers are allowed here for the same reason as in `QUOTED` above.
BY_SOURCE = re.compile(r"[“\"]([^”\"]{12,})[”\"][\s*_]*\(([a-z][a-z0-9_]*)\)")

# **TWO MORE SHAPES, FOR A DOCUMENT WITH NO PAGES THAT STILL HAS PLACES IN IT.**  A maker's
# website of numbered sections, or a list of release notes, has no page to cite, and a
# definition quoting one says where in it instead: `"..." (os_updates, #243)` names the source
# and then the entry, and `"..." (15.6)` gives a number and no source at all.  Neither is a
# page and neither is a bare key, so both read as no locator, and `teenage_engineering/op_1`
# reported nothing to check while holding twelve quotations located one of these two ways.
#
# The first is looked for in the source it names, exactly as a bare key is.  **What follows
# the comma is the writer's note of where and is not checked**: this tool can no more turn to
# an entry than to a section.  The second names no document, so the passage is looked for in
# **every** document the definition cites that this tool holds and can read, and the report
# says which holds it.  That is a weaker claim than a page and still worth having: it says the
# passage is in a document cited here, and which.  The number is as often a release's as a
# section's - `(1.55D)` is an OS version heading a list of fixes - so the report says number.
#
# **BOTH ARE NARROW ON PURPOSE, SO THAT PROSE IN BRACKETS IS STILL NOT A LOCATOR.**
#
# - The key is one of the definition's own, **of a source with no pages**, and **a comma
#   follows it**.  `(manual paraphrased)` is an aside that happens to begin with a key.
#   `(manual, page 42)` is a page citation mistyped, and reading it as a place would pass it
#   on a search of the whole manual without ever turning to page 42.  Both are left in the
#   no-locator figure, where they can be seen.
# - What follows the comma is not page-shaped, or it is the paged form and `QUOTED`'s.
# - A number alone has **a dot in it, or a word for section before it**: `15.6`, `1.55D`,
#   `v1.0.6`, `section 4`, `§ 4`.  A bare `(16)`, `(2025)` or `(5V)` is a channel, a year or a
#   voltage far more often than a section, and a forgotten `p.` besides, so none is read.
#   **A dotted number is read whatever it measures**, because `(1.01)` and `(1.55D)` are
#   releases here and `(0.5)` and `(3.3V)` have their shape: a passage followed by one of
#   those is looked for like any other, and found if it is a quotation.
#
# Each was first written wider - any text after a key, any digits at all - and each wider
# form failed a run on an aside or passed a mistyped page.
#
# **AND THESE TWO ARE FOUND BY PAIRING THE QUOTE MARKS, NOT BY A PATTERN** - see
# `placed_quotations()`.  `QUOTED` and `BY_SOURCE` can each say in the pattern what the
# brackets must hold, which narrows the false pairing of prose between two quotations with
# the bracket that opens the second.  A place depends on the definition's own keys and is told
# apart afterwards, so a pattern for it would have to take any bracket at all - and then
# `"..." (guide) and the heading "(10.4) Sync"` reads the words between the two quotations as
# a third, located `(10.4)`, and fails the run on prose.  It was written that way once, and
# that is what it did.  #4172.
SOURCE_THEN = re.compile(r"([a-z][a-z0-9_]*)\s*,\s*\S.*")
NUMBERED = re.compile(
	r"(?:(?:section|sec\.)\s+|§\s*)\d+(?:\.\d+)*[A-Za-z]?|v?\d+(?:\.\d+)+[A-Za-z]?", re.IGNORECASE)

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
	# **AND A LOW LINE IS READ BACK AS AN `f`**, because some text layers put one where the
	# page prints an `f` ligature. The Waldorf Protein's manual is the case: made in Pages and
	# exported by Quartz, it returns `_ilter` where the page prints `filter`, `shuf_led` for
	# `shuffled` and `over_low` for `overflow` - **226 times across its 71 sheets**, the stand-in
	# followed only ever by `i` (197) or `l` (29), which are the two ligatures it sets.
	# So a quotation containing any of `filter`, `defines`, `specifies`, `confirm`, `firmware`,
	# `first`, `fixed` or `flow` could never be found in that document, and those are the words
	# a MIDI definition quotes.
	# **Reading it as `f` reconstructs every one of that manual's 60 affected words exactly**,
	# which is the test this fold has to pass: `Ampli_ier` is `Amplifier` and not `Amplifiier`.
	# Unlike the soft hyphen above, a definition *could* type a real underscore - a file name,
	# a parameter like `OSC_1` - so this fold is not free. It is safe because `squash()` applies
	# it to the page and to the quotation alike: `Protein_Manual.pdf` becomes `proteinfmanual`
	# on both sides and still matches. What it costs is the ability to tell `A_B` from `AfB`,
	# which is the hyphen's bargain and no reader of a citation is misled by it.
	"_": "f",
	# **AND THE LATIN LIGATURES ARE SPELT OUT**, because a typesetter's `ﬁ` is one character and
	# the `fi` a definition types is two, so a quotation containing `specifics`, `off`, `flow` or
	# `efficient` could never be found in a document that sets them as ligatures.
	# **37 documents in this library do** - 611 occurrences in their first thirty sheets alone,
	# the volca bass's manual 116 of them and the Nymphes's release notes 23 - and each character
	# has exactly one reading, so this fold is simply a decomposition rather than a bargain.
	# Like the soft hyphen above it can only make more quotations match and never fewer: nothing
	# a definition could reasonably type is U+FB00 to U+FB06.
	"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st",
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


SECOND_READING_WHOLE = """
import sys

import fitz

sys.stdout.write(chr(10).join(page.get_text() for page in fitz.open(sys.argv[1])))
"""


def read_whole_again (path: pathlib.Path) -> str | None:

	"""A whole document as the second extractor reads it, or nothing at all.

	For a quotation that names no page: one located by a source key or by a number alone is
	looked for in a whole document, and `pypdf`'s reading of that document can lose it just
	as its reading of one page can.  Nothing for a text file, which is read as it is and has
	no second reading to have, and nothing where the extractor is not installed, fails, or
	returns no text at all - which `check()` says aloud, since an absence then rests on one
	reading.

	Not cached here.  `check()` asks once for each document of a definition and keeps the
	answer, squashed, for as long as that definition is being checked.
	"""

	if path.suffix.lower() != ".pdf":
		return None

	try:
		done = subprocess.run(
				[SECOND_READER, "-c", SECOND_READING_WHOLE, str(path)],
				capture_output = True, text = True, timeout = 600)

	except (OSError, subprocess.SubprocessError):
		return None

	return done.stdout if done.returncode == 0 and done.stdout.strip() else None


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


# **A SMALL CACHE, BECAUSE THE REPEATS ARE NEIGHBOURS RATHER THAN SCATTERED.**  Extracting a
# document's text is the expensive part of a run, and 19 of the corpus's 432 source entries
# name a document another definition has already read - the reface Data List serves three
# instruments, one Korg chart serves four.  Those siblings sort next to each other, so the
# second reading is nearly always within a few definitions of the first and a handful of
# entries catches it.  Deliberately not unbounded: holding all 413 documents' page text at
# once is a lot of memory for a 4% saving, and that is what the measurement said it is worth.
#
# **Safe only because nothing mutates what this returns**, which was checked rather than
# assumed: `Document.printed` indexes the list, `Document.where` iterates it, and `documents`
# only asks whether any page has text.  A caller that edited a page in place would be editing
# every later caller's copy of it, so if one ever needs to, this returns a tuple instead.
@functools.lru_cache(maxsize = 8)
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

		# Annotated rather than inferred: `source` is the loader's own object and arrives
		# untyped here, so without this the page number is `Any`, and indexing a list with
		# `Any` makes the text this returns `Any` too - which mypy reports and is right to.
		at: int | None = self.source.file_page(number)

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


def place_named (
		locator: str,
		known: typing.Collection[str],
		paged: typing.Collection[str] = ()) -> tuple[str | None, str]:

	"""What kind of place a locator names, where it is one this tool cannot turn to.

	``("source", key)`` for one of the definition's source keys, a comma, and more;
	``("number", locator)`` for a section or version number alone; and ``(None, "")`` for
	anything else: a page, a bare key, or prose in brackets.

	``paged`` is the keys whose documents have pages.  A key among them followed by a place
	is not read, because a document with pages is cited by its page: ``(manual, page 42)``
	is a mistyped page citation, and a search of the whole manual would pass it unturned.
	"""

	inside = " ".join(locator.split())

	if PAGE_SHAPED.search(inside) or inside in known:
		return None, ""

	then = SOURCE_THEN.fullmatch(inside)

	if then is not None and then.group(1) in known and then.group(1) not in paged:
		return "source", then.group(1)

	if NUMBERED.fullmatch(inside):
		return "number", inside

	return None, ""


def placed_quotations (
		text: str,
		keys: typing.Iterable[str],
		paged: typing.Collection[str] = ()) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:

	"""Quotations located by a place rather than a page: in a named source, or by a number alone.

	Two lists.  The first is ``(quotation, source key)`` for a locator that names one of this
	definition's sources and then says where in it, as ``(os_updates, #243)`` does; it is
	checked exactly as a bare key is.  The second is ``(quotation, locator)`` for a locator
	that is a section or version number and nothing else, as ``(15.6)`` is; it names no
	document, so the passage is looked for in all of them.

	**Found by pairing the quote marks in order, over the prose with its code spans taken
	out, exactly as ``uncovered()`` does** - same text, same pairing, same test of what is a
	place.  So the two cannot disagree: a passage this finds is one that function calls
	located, and a passage with a place after it is never reported there as having no
	locator.  And only what lies between an opening mark and its closing mark is ever a
	quotation, which a pattern run over the whole file cannot promise.

	What that costs is what it costs ``uncovered()``, four things:

	- a file whose marks do not pair gives nothing here, which ``check()`` says aloud;
	- a passage in curly marks is not seen;
	- a passage inside backticks is code and is passed over, which is the point of the
	  backticks - **and a backtick that is never closed turns each later code span inside
	  out**, so that prose between two later spans is passed over and an example inside one
	  is read as a quotation, which nothing in the report says;
	- a code span inside a quoted passage is cut out of it before it is looked for, so
	  ``"press the `PRG` button"`` is looked for without its middle and not found.
	"""

	flat = quotable(text)

	if len(QUOTE_MARK.findall(flat)) % 2:
		return [], []

	known = set(keys)
	positions = list(QUOTE_MARK.finditer(flat))

	in_source: list[tuple[str, str]] = []
	numbered: list[tuple[str, str]] = []

	for opening, closing in zip(positions[::2], positions[1::2]):
		quotation = flat[opening.end():closing.start()]
		after = LOCATOR_AFTER.match(flat[closing.end():])

		if after is None or len(quotation) < FLOOR:
			continue

		kind, named = place_named(after.group(1), known, paged)

		if kind == "source":
			in_source.append((quotation, named))
		elif kind == "number":
			numbered.append((quotation, named))

	return in_source, numbered


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


# ── What this tool did not look at, which is the figure it never printed ─────────────────
#
# Everything above answers "of the quotations I can see, are they on their pages".  Nothing
# above answers **"how many did I not see"** - and a quotation with no locator at all is
# passed over in silence, so a definition could read "5 of 5 quotations are on the page they
# cite" while holding thirty nobody had looked at.  `korg/minilogue` did exactly that, and
# giving its quotations locators took it to 22 of 22 and immediately caught three that were
# right about the printed page and absent from its text layer.  #4359.
#
# **THE COUNT HAS TO PAIR THE QUOTE MARKS RATHER THAN PATTERN-MATCH THEM.**  A `[^"]{12,}`
# between two quote characters matches the prose *between* a closing mark and the next
# opening one just as readily as it matches a quotation, so the obvious sweep reports about
# twice what is there.  That has now been written wrongly twice - once while auditing the
# PĒRKONS, where it gave 49 for a file holding 35, and once while answering whether this
# task was worth doing at all.  Pairing in order is the whole fix, and it is sound here: no
# definition in the corpus uses a curly double quote, and every one holds an even number of
# straight ones, which `odd_quote_marks()` below asserts rather than assumes.

# Straight only, because nothing in the corpus writes a curly double quote and a curly pair
# would need pairing by direction instead of by order.
QUOTE_MARK = re.compile(r"\"")

# A locator follows a quotation if a parenthesis does, allowing this project's emphasis
# markers exactly as `QUOTED` does.  Whether it is a locator this tool can *read* is
# `read_locator()`'s question and is already reported; this only asks whether the writer
# gave one at all.
LOCATOR_AFTER = re.compile(r"^[\s*_]*\(([^)]*)\)")

# Page-shaped, in the same words `QUOTED`'s lookahead uses, so the two cannot disagree about
# what counts as an attempt to cite a page.
PAGE_SHAPED = re.compile(r"pp?\.\s*\d")

# The shortest quotation this tool will check, stated once so the floor and the report of
# what the floor excluded cannot drift apart.
FLOOR = 12


def prose (text: str) -> str:

	"""The part of a definition a quotation can live in: its comments and its written account.

	**A quotation lives in prose, and a pair of quote marks anywhere else is YAML syntax.**
	`elektron/octatrack` is the case that settles it: 99 of its controls carry a label in
	quote marks, not because the label is quoted from anywhere but because this maker writes
	parameter names with commas and brackets in them and a flow mapping cannot hold either
	bare.  A sweep over that whole file reports 113 unlocated quotations of which 99 are
	labels - and **a sweep that invents a hundred faults on a correct file is one nobody reads
	twice**, which is the same reason `check_provenance_digests.py` had to stop calling two
	sound records faulty.

	So this keeps the `source` block scalar and **the comment part of every line that has
	one**, and drops the field and value in front of it - a title, a url, a sha256, a
	control's mapping.  Comments are kept wherever they are, including inside the controls
	block, because a comment there is prose like any other.

	**A TRAILING COMMENT IS PROSE AND KEEPING ONLY WHOLE COMMENT LINES MISSED IT.**  That was
	this function's own first bug, and `odd_quote_marks()` caught it on the first corpus run:
	`arturia/minifreak` writes ``programmable: true   # "Bend Range: sets the range of pitch
	bend messages`` and carries the quotation on into the next line, so the opening mark was
	dropped with the field and the closing one kept.  The count came out odd, which is the
	only reason anybody looked.  A hundred and one lines in the corpus are that shape, so the
	prose being dropped was not a corner.

	**The comment cannot be found by splitting on the first `#`.**  A hundred and one `#`
	characters in this corpus sit inside a quoted value - `CC#7`, `"Playback param #1"`,
	``firmware: "#246"`` - so the test is whether an *even* number of quote marks precedes it,
	which is what says it is outside a string rather than in one.
	"""

	kept = []
	in_account = False

	for line in text.split("\n"):
		stripped = line.strip()

		# The written account is a block scalar, so it runs until something unindented
		# starts the next field.  Its own lines carry no marker of their own, and a `#` in
		# it is literal text rather than a comment, so the whole line is kept as it stands.
		if in_account:
			if stripped and not line.startswith((" ", "\t")):
				in_account = False
			else:
				kept.append(line)
				continue

		if re.match(r"^source:\s*[>|]", line):
			in_account = True
			continue

		for mark in re.finditer(r"#", line):
			if line[:mark.start()].count("\"") % 2 == 0:
				kept.append(line[mark.start():])
				break

	return "\n".join(kept)


def quotable (text: str) -> str:

	"""The prose a quotation can be found in, flowed, with code spans taken out.

	**A quoted passage inside backticks is code and not a quotation**, and honouring that is
	not a nicety: the remedy this tool recommends for a passage that quotes nothing is to put
	it in backticks, so a sweep that went on reporting it afterwards would be telling people
	to do something that does not work.  `elektron/octatrack` is the case - its account
	explains the label trap by quoting a label as an example, inside backticks, and that one
	line was the only false positive left in the file once the YAML values were out.

	Flowed first and stripped second, because a code span can be broken across two comment
	lines exactly as a quotation can.
	"""

	return re.sub(r"`[^`]*`", " ", flowed(prose(text)))


def odd_quote_marks (text: str) -> bool:

	"""Whether this definition's prose holds an odd number of quote marks.

	Pairing in order is only sound where the marks pair, so a file with an odd count is one
	this coverage figure cannot speak for.  Said out loud rather than silently mis-paired,
	because the whole point of the figure is that a silence was being read as a clean bill.
	"""

	return len(QUOTE_MARK.findall(quotable(text))) % 2 == 1


def uncovered (
		text: str,
		keys: typing.Iterable[str],
		paged: typing.Collection[str] = ()) -> tuple[list[str], list[str]]:

	"""The quoted passages this tool never looked at, and why, by pairing the marks in order.

	Two answers, because there are two reasons and a reader cannot reconcile a figure against
	one of them:

	- **no locator at all**, of `FLOOR` characters or more, which is what #4359 is about;
	- **under `FLOOR` characters while carrying a locator**, which is the floor doing its job
	  and is still invisible in the figures - the PolyBrute 12's 62 locators against the
	  gate's 60 are these two, `5-octave` and a version string.

	**Neither is reported as an error, and that is deliberate.**  Some of what this finds
	should not be a quotation at all: `"System Exclusive"` quoting nothing, a PDF's internal
	metadata title, one definition quoting another definition in this corpus.  The remedy for
	those is backticks rather than an invented locator, so the figure is a coverage report and
	says *passages*, not *unchecked quotations*.  A tool that called them faults would be the
	kind people learn to disbelieve.
	"""

	flat = quotable(text)

	if len(QUOTE_MARK.findall(flat)) % 2:
		return [], []

	known = set(keys)
	positions = list(QUOTE_MARK.finditer(flat))

	unlocated: list[str] = []
	short: list[str] = []

	for opening, closing in zip(positions[::2], positions[1::2]):
		quotation = flat[opening.end():closing.start()]
		after = LOCATOR_AFTER.match(flat[closing.end():])

		located = after is not None and (
			PAGE_SHAPED.search(after.group(1)) is not None
			or after.group(1).strip() in known
			or place_named(after.group(1), known, paged)[0] is not None)

		if located and len(quotation) < FLOOR:
			short.append(quotation)
		elif not located and len(quotation) >= FLOOR:
			unlocated.append(quotation)

	return unlocated, short


def offsets (source: typing.Any) -> str:

	"""A source's offset as a reader would say it: one figure, or each run's from its first page."""

	runs = getattr(source, "page_runs", ())

	if not runs:
		return f"{source.page_offset:+d}"

	return ", ".join(f"{run.offset:+d} from p. {run.from_printed}" for run in runs)


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

	"""What one definition's check came to.  Every field counts quotations but two.

	**The third figure used to add two different things together.**  A definition with
	nothing to check returned 1, meaning one definition, and a definition whose documents
	could not be read returned a count of its quotations - so "27 could not be checked"
	was definitions and quotations summed.  That is what made a change of one definition
	show up as a change of one quotation, which is the only reason the silent skip above
	was found at all.  Counting them apart costs two fields and lets each figure answer
	one question.

	Every field defaults to nought so that a running total starts at ``Tally()``.
	"""

	# On the page they cite, inside the source they name, or - where the locator is a number
	# alone - in one of the documents cited.
	passed: int = 0

	# Not there.  This, an unreadable locator and a misnamed source are what fail the run.
	missing: int = 0

	# Counted in `passed` as well, because the page does carry the words: these are the
	# ones only the second extractor could find.  A figure above nought says two readings
	# of one page, or of one whole document, differ, which is worth knowing whichever is right.
	disagreed: int = 0

	# They cite a page or a source, and no document that could hold it could be read: a
	# scan, or a manual nobody has put in the library.  One located by a number alone is
	# here too where it is in no document that was read and another cited could not be.
	unchecked: int = 0

	# Their locator looks like a page citation and this tool cannot read it.
	unreadable: int = 0

	# Their locator names a source this definition does not have, which is a mistake in
	# the file.  **These were collected and never printed** until #4475.
	misnamed: int = 0

	# **IN DEFINITIONS, NOT QUOTATIONS**, one of the two fields that are: one if this
	# definition quotes nothing with a locator at all, nought otherwise.  Nought too where
	# its marks do not pair: a place locator is found by pairing them, so nobody knows that
	# it has none, and `unpairable` counts it instead.
	nothing_to_check: int = 0

	# Quoted passages of `FLOOR` characters or more with no locator at all, which this tool
	# never looked at and never counted.  **A coverage figure rather than a fault**: some of
	# what it finds should be backticks rather than a quotation, so it is reported and does
	# not fail the run.  #4359.
	no_locator: int = 0

	# Quoted passages that carry a locator and are shorter than `FLOOR`, so the floor
	# excluded them.  The floor is right and its effect was invisible, which is what stopped
	# a hand count ever reconciling with the figures above.
	too_short: int = 0

	# **IN DEFINITIONS, NOT QUOTATIONS**: one where the prose holds an odd number of quote
	# marks, so the two figures above cannot be computed for it by pairing.  Nought is the
	# whole corpus today and this says so rather than mis-pairing in silence.
	unpairable: int = 0


def check (name: str, path: pathlib.Path, index: dict[str, pathlib.Path]) -> Tally:

	"""Check one definition, printing what it found."""

	definition = pymidiinstrumentdefs.load_file(path)
	held, absent = documents(definition, index)
	body = path.read_text(encoding = "utf-8")
	sources = definition.sources or {}

	# A document with pages is cited by its page, so a key followed by a place is read only
	# for one without.  See `place_named()`.
	paged = {key for key, source in sources.items() if source.paginated}

	found = quotations(body)
	in_source, numbered = placed_quotations(body, sources, paged)
	named = named_quotations(body, sources) + in_source
	unreadable = unreadable_locators(body)

	# **Computed before any of the early returns below and carried into every one of them.**
	# A definition with nothing checkable is exactly where an unlocated quotation hides, so a
	# coverage figure that only appeared on the path where checking happened would miss the
	# cases it exists for.
	unpairable = odd_quote_marks(body)
	unlocated, short = ([], []) if unpairable else uncovered(body, sources, paged)

	coverage = {
		"no_locator": len(unlocated),
		"too_short": len(short),
		"unpairable": 1 if unpairable else 0,
	}

	print(f"\n{name}")

	for line in absent:
		print(f"    {line}")

	if unpairable:
		print(f"    its prose holds an ODD NUMBER OF QUOTE MARKS, so this tool cannot pair "
			f"them: no locator that names a place and not a page was looked for, and it "
			f"says nothing about what it did not check here")

	# Said whether or not anything else is wrong, because the point of the figure is that
	# these passages were in no figure at all.
	if unlocated:
		print(f"    {len(unlocated)} passage(s) of {FLOOR}+ characters are in quotation marks "
			f"with NO LOCATOR, so they were not checked - give each one a locator, or use "
			f"backticks where it is not quoting a document:")

		for quotation in unlocated:
			print(f"        {quotation[:88]}")

	if short:
		print(f"    {len(short)} passage(s) carry a locator and are under {FLOOR} characters, "
			f"which is this tool's floor, so they were not checked: "
			+ ", ".join(repr(quotation) for quotation in short))

	# Said before anything else, and said even where the definition is otherwise clean,
	# because the point of the figure is that nobody knew these quotations existed.
	if unreadable:
		print(f"    {len(unreadable)} quotations have a locator this tool cannot read, so they "
			f"are NOT CHECKED - the convention is a single word before the page:")

		for quotation, locator in unreadable:
			print(f"        ({locator}): {quotation[:88]}")

	if not found and not named and not numbered:
		# A place locator is found by pairing the marks.  Where they do not pair nobody
		# looked for one, so this is not known to be a definition with nothing to check.
		if unpairable:
			print(f"    no quotation in it cites a page or a source by its key alone")

			return Tally(unreadable = len(unreadable), **coverage)

		print(f"    no quotation in it cites a page or a source, so there is nothing to check")

		return Tally(unreadable = len(unreadable), nothing_to_check = 1, **coverage)

	if not held:
		print(f"    {len(found) + len(named) + len(numbered)} quotations cite a source and "
			f"none could be read")
		return Tally(unchecked = len(found) + len(named) + len(numbered),
			unreadable = len(unreadable), **coverage)

	print(f"    {len(held)} document(s): " + ", ".join(
		f"{d.name} [{len(d.pages)} sheets, offset {offsets(d.source)}"
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
	wholes: dict[str, str] = {}

	def whole_of (document: Document) -> str:

		"""The whole of a held document, squashed, and read once however often it is asked for."""

		if document.name not in wholes:
			wholes[document.name] = squash("\n".join(document.pages))

		return wholes[document.name]

	second_wholes: dict[str, str | None] = {}
	one_reading: set[str] = set()

	def second_reading_holds (document: Document, parts: list[str]) -> bool:

		"""Whether the other extractor's reading of the whole document carries every part."""

		if document.name not in second_wholes:
			again = read_whole_again(document.path)
			second_wholes[document.name] = None if again is None else squash(again)

			# A PDF the second extractor gave nothing for has had one reading, and an
			# absence resting on it is said to.  A text file is read as it is.
			if again is None and document.path.suffix.lower() == ".pdf":
				one_reading.add(document.name)

		again_whole = second_wholes[document.name]

		return again_whole is not None and all(part in again_whole for part in parts)

	# **BEFORE CALLING ONE OF THESE ABSENT, ASK THE OTHER EXTRACTOR, AS THE PAGED CHECK DOES.**
	# A whole document is one `pypdf` reading as surely as one page is, and #4483's hyphen
	# turned into an `x` is lost the same way wherever it is looked for.
	disagreed_whole: list[tuple[str, str]] = []
	elsewhere_missing: list[tuple[str, str]] = []
	named_unread: list[tuple[str, str]] = []
	named_passed = 0

	for quotation, key in named:
		named_document = by_name.get(key)

		# The key is one of this definition's own, or it would not be here, so a document
		# that is not held is one that could not be read: not in the library, or a scan.
		# **That is unchecked, not wrong**, which is what a page cited in it gets too.  It
		# used to be reported as `NOT IN` the source, the wording for a passage looked for
		# and not found, about a document nobody had opened.
		if named_document is None:
			named_unread.append((quotation, key))
			continue

		whole = whole_of(named_document)

		# An empty document makes every quotation look absent, so it is this tool's fault
		# before it is a finding.  `documents()` has already dropped a scan, so reaching
		# here with nothing to search means something else is wrong.
		assert whole, f"{key} read as empty, which is a bug in this tool and not a finding"

		parts = pieces(quotation)

		if all(part in whole for part in parts):
			named_passed += 1
		elif second_reading_holds(named_document, parts):
			disagreed_whole.append((quotation, key))
			named_passed += 1
		else:
			elsewhere_missing.append((quotation, key))

	if len(named) > len(named_unread):
		print(f"    {named_passed} of {len(named) - len(named_unread)} quotations that name a "
			f"source are in it")

	if named_unread:
		print(f"    {len(named_unread)} name a source that could not be read, so they are "
			f"unchecked:")

		for quotation, key in named_unread:
			print(f"        ({key}): {quotation[:88]}")

	for quotation, key in elsewhere_missing:
		print(f"\n      NOT IN {key}: {quotation[:120]}")

	# A quotation located by a number alone names no document, so it is looked for in every
	# one this definition cites that could be read, and the report says which holds it.
	holding: list[tuple[str, str, list[str]]] = []
	nowhere: list[tuple[str, str]] = []
	perhaps_unread: list[tuple[str, str]] = []

	for quotation, locator in numbered:
		parts = pieces(quotation)
		holders = [document.name for document in held
			if all(part in whole_of(document) for part in parts)]

		if not holders:
			holders = [document.name for document in held if second_reading_holds(document, parts)]

			if holders:
				disagreed_whole.append((quotation, ", ".join(holders)))

		# **In no document that was read is not in no document cited.**  Where one of this
		# definition's sources could not be read, the passage may be in that one, and
		# nothing here names the document it is credited to.  So it is unchecked, exactly as
		# it would be had the locator named the unread source.
		if holders:
			holding.append((quotation, locator, holders))
		elif absent:
			perhaps_unread.append((quotation, locator))
		else:
			nowhere.append((quotation, locator))

	if numbered:
		print(f"    {len(holding)} of {len(numbered)} quotations located by a section or version "
			f"number alone are in a document cited here, which is a weaker check than a page"
			+ (":" if holding else ""))

		for quotation, locator, holders in holding:
			print(f"        ({locator}) in {', '.join(holders)}: {quotation[:76]}")

	if perhaps_unread:
		print(f"    {len(perhaps_unread)} more are in no document that could be read, and "
			f"{len(absent)} cited here could not be, so they are unchecked:")

		for quotation, locator in perhaps_unread:
			print(f"        ({locator}): {quotation[:88]}")

	if disagreed_whole:
		print(f"    {len(disagreed_whole)} of those located without a page were found only by "
			f"the second extractor, so the document carries the words and pypdf "
			f"{pypdf.__version__} reads it differently:")

		for quotation, in_document in disagreed_whole:
			print(f"        {in_document}: {quotation[:84]}")

	for quotation, locator in nowhere:
		print(f"\n      IN NO DOCUMENT CITED, located ({locator}): {quotation[:110]}")

	# The caveat the paged check prints, for the same reason: an absence the second
	# extractor was never asked about, or could not answer, rests on one reading.  Said of
	# the documents an absence was looked for in and of no other: a passage credited to a
	# text file is not made doubtful by a PDF beside it.
	rests_on_one = {key for _, key in elsewhere_missing if key in one_reading}

	if nowhere:
		rests_on_one |= one_reading

	if rests_on_one:
		print(f"\n          {', '.join(sorted(rests_on_one))} read with pypdf {pypdf.__version__} "
			f"alone, the second extractor giving nothing, and that is one reading of a "
			f"document rather than the document: if a quotation crosses a hyphen, check what "
			f"is printed before changing it (#4483)")

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
			passed = passed + named_passed + len(holding),
			missing = len(missing) + len(elsewhere_missing) + len(nowhere),
			disagreed = len(disagreed) + len(disagreed_whole),
			unchecked = unchecked + len(named_unread) + len(perhaps_unread),
			unreadable = len(unreadable),
			misnamed = len(misnamed),
			**coverage)


# Where a worker keeps the library index between tasks.  It is handed over once when the
# worker starts rather than with each definition: the index is one entry per readable document
# and there are 492 of them, so sending it alongside all 125 tasks is pure copying.
HELD_INDEX: dict[str, pathlib.Path] = {}


def remember_index (index: dict[str, pathlib.Path]) -> None:

	"""Keep the library index where this worker's own checks can find it."""

	global HELD_INDEX

	HELD_INDEX = index


def check_captured (work: tuple[str, pathlib.Path]) -> tuple[str, Tally]:

	"""Check one definition and hand back what it would have printed, instead of printing it.

	A worker cannot print to the terminal directly, because several definitions are being
	checked at once and their lines would interleave into something nobody can read.  So
	each worker's output is held as text and the parent prints them in the order they were
	submitted - which is what makes a run on six cores produce the same report, line for
	line, as a run on one.
	"""

	name, path = work

	held = io.StringIO()

	with contextlib.redirect_stdout(held):
		tally = check(name, path, HELD_INDEX)

	return held.getvalue(), tally


def cores_to_use (asked: int | None) -> int:

	"""How many processes to check with: what was asked for, or two short of every core.

	Two are left free on purpose.  Reading a manual for text is the expensive part of this
	check and it saturates a core, so a sweep over the whole corpus would otherwise take
	the machine over - and the question that prompted this arrived while a test suite was
	running in another checkout.  A gate worth running often is one that leaves room to
	work while it runs.
	"""

	if asked is not None:
		return max(1, asked)

	return max(1, (os.cpu_count() or 1) - 2)


def main (argv: list[str]) -> int:

	"""Check every definition named, or every bundled one."""

	parser = argparse.ArgumentParser(
		description = "Check that every passage a definition quotes is printed on the page it cites.",
		epilog = "The library of documents is $PYMIDIINSTRUMENTDEFS_LIBRARY.")

	parser.add_argument("names", nargs = "*",
		help = "definition names; the default is every bundled one")

	parser.add_argument("--jobs", "-j", type = int, default = None, metavar = "N",
		help = "check N definitions at once; the default leaves two cores free, "
			"and 1 is the single-process path every release so far has used")

	parsed = parser.parse_args(argv[1:])

	root = os.environ.get("PYMIDIINSTRUMENTDEFS_LIBRARY")

	if not root:
		print("PYMIDIINSTRUMENTDEFS_LIBRARY names the folder the documents are in")
		return 2

	index = library_index(pathlib.Path(root))
	print(f"{len(index)} readable documents in {root}")

	corpus = pathlib.Path(pymidiinstrumentdefs.__file__).parent / "corpus"
	wanted = parsed.names or pymidiinstrumentdefs.available([corpus])
	work = [(name, corpus / f"{name}.yaml") for name in wanted]

	for name, path in work:
		if not path.exists():
			print(f"\n{name}\n    no such definition")
			return 2

	cores = cores_to_use(parsed.jobs)

	# **To the error stream, so that the report itself stays comparable between runs.**  The
	# whole point of the ordering above is that one core and six produce the same lines; a
	# progress note naming the number of cores would be the one line that differs, and
	# diffing two runs is how this tool's parallel path is proved correct.
	print(f"checking {len(work)} definition(s) on {cores} core(s)", file = sys.stderr)

	if cores == 1:
		# **Kept as its own path rather than one worker through the capture**, because that is
		# what makes it a reference: it is the code every release before this ran, printing as
		# it goes, and a parallel run is correct exactly when its output matches this one's.
		tallies = [check(name, path, index) for name, path in work]

	else:
		with concurrent.futures.ProcessPoolExecutor(max_workers = cores,
			initializer = remember_index, initargs = (index,)) as pool:

			tallies = []

			# `map` yields in the order the work was submitted, however the workers finish, so
			# the report reads the same as a single-process one even though it was not built
			# in that order.
			for text, tally in pool.map(check_captured, work):
				print(text, end = "")
				tallies.append(tally)

	total = Tally()
	failed: list[str] = []
	unreadable_in: list[str] = []
	unlocated_in: list[str] = []
	unpairable_in: list[str] = []

	for name, tally in zip(wanted, tallies):
		total = Tally(*(running + one for running, one in zip(total, tally)))

		# Any of the three is a failure, so any of the three names the definition.  A locator
		# nobody can read means a quotation checked against nothing, which is as bad as one
		# checked and wrong - worse, because it looks like neither.
		if tally.missing or tally.unreadable or tally.misnamed:
			failed.append(name)

		if tally.unreadable:
			unreadable_in.append(name)

		if tally.no_locator:
			unlocated_in.append(name)

		if tally.unpairable:
			unpairable_in.append(name)

	print(f"\n{total.passed} quotations check out across {len(wanted)} definition(s); "
		f"{total.missing} are not on the page or in the document they cite; "
		f"{total.unchecked} could not be checked")

	# Said as its own sentence rather than folded into the figures above, because it is a
	# count of quotations nobody had looked at rather than a count of checks that ran.
	print(f"{total.unreadable} quotations across {len(unreadable_in)} definition(s) have a "
		f"locator this tool cannot read, so they are not in any figure above"
		+ (f": {', '.join(unreadable_in)}" if unreadable_in else ""))

	if total.disagreed:
		print(f"{total.disagreed} of those were found only by the second extractor, so two "
			f"readings of one page or document differ - counted above as checking out, because "
			f"it does carry the words")

	if total.misnamed:
		print(f"{total.misnamed} quotations name a source their definition does not have")

	# **THE TWO FIGURES THAT MAKE THE ONE ABOVE RECONCILABLE.**  Until these existed, a hand
	# count of a file's locators could not be squared with what this tool said it checked,
	# and the difference was the whole fault: a figure could not be told from a complete
	# figure.  `korg/minilogue` read "5 of 5" while holding thirty nobody had looked at.
	# Neither fails the run - see `uncovered()` for why a coverage report must not.
	print(f"{total.no_locator} passage(s) of {FLOOR}+ characters are in quotation marks with "
		f"no locator at all, so they are in no figure above"
		+ (f": {', '.join(unlocated_in)}" if unlocated_in else ""))

	print(f"{total.too_short} passage(s) carry a locator and are under {FLOOR} characters, "
		f"which is this tool's floor, so they are in no figure above")

	if total.unpairable:
		print(f"{total.unpairable} definition(s) hold an odd number of quote marks in their "
			f"prose, so the two figures above do not speak for them: "
			f"{', '.join(unpairable_in)}")

	print(f"{total.nothing_to_check} definition(s) quote nothing with a locator")

	if failed:
		print(f"not clean: {', '.join(failed)}")

	return 1 if total.missing or total.unreadable or total.misnamed else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv))
