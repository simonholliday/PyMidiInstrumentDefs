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
either checking or refusing, and the comment that begins the patterns below records a
fourth of the same shape from before any of them.

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
is looked for in every document the definition cites that has no pages and could be read, and
the report says which holds it.  Both used to read as no locator at all, and two definitions
reported nothing to check while holding quotations located one of these two ways.

**Every one of the four shapes is found the same way, by pairing the quote marks in order**
over the prose with its code spans taken out.  A page and a bare key were found by a pattern
run over the whole file until #4928, and a pattern cannot tell a quotation from the prose
between two of them.  It stopped a passage at a curly mark the maker printed inside it, so
twelve quotations were counted as located and checked by nothing; it looked inside backticks,
which the other two shapes pass over; and it read back from a curly mark to whatever straight
mark came before.  A passage is now what lies between one straight mark and the next, in
pairs, whichever shape of locator follows it.

**And pairing asks more of a file than a pattern did, so the file is asked for it aloud.**
The marks have to pair, and a pair has to be an opening mark and its own closing one.  So a
quote mark inside a quotation is written as a single one, every run of backticks that opens
a code span is closed by a run of as many, and the account is a block scalar.  Where one of
those is not so, this says which
and where it can, and fails, because the other answer is a clean bill for prose nobody read.

It exits non-zero if any quotation is not on the page it cites, not in the source it names or,
where it gives a number alone, in none of the documents cited that have no pages when all of
those could be read; if any locator cannot be read; if a locator names a source its
definition does not have, which before a page is any name that is not its own and without
one is a name the bundled definitions call a document by; if a document that has pages is
cited by its key with no page, or a number alone is given where every source has pages, or
a page is cited where no source it could be in has pages; if a curly quote mark stands
outside every quotation, since only straight marks are paired; if a quotation with its
locator stands inside backticks; if a passage looks like the prose between two quotations,
which is what marks paired wrongly leave; if a paragraph's quote marks or backticks do not
pair at all; or if its account is not a block scalar.  Nothing in such a definition can be
read, or not with any confidence.

**Each of those became a failure the moment it reached nought**, which was the only moment it
could be done for nothing.  A convention that is reported and not enforced is one that
drifts, and the drift here had already cost five wrong citations in definitions released
months earlier - three of them quotations saying something the maker had not said.
"""

import argparse
import bisect
import collections
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
import yaml

import pymidiinstrumentdefs


# What can be read for text.  A scanned PDF has pages and no text in them, which is
# reported rather than counted as a failure.  A web page as it was served is read as
# text, markup and all, for a source that cites what only the page's script holds.
READABLE: typing.Final[frozenset[str]] = frozenset({".pdf", ".txt", ".html"})

# **A QUOTATION AND WHATEVER LOCATOR FOLLOWS IT ARE TAKEN WHOLE AND PARSED AFTERWARDS.**
# Twelve characters is the shortest quotation worth checking; below that a phrase matches
# half the manual.
#
# It was once one pattern that matched a quotation and a well-formed locator together, and
# that is why two silent skips happened in it.  **A pattern that matches only what it can
# read cannot report what it cannot read**: a locator it did not match looked exactly like a
# quotation with no locator, which this tool passes over without a word.  Taking the
# parenthesis whole and reading it in `read_locator()` separates two questions that were one
# - is there a locator here, and can I understand it - so the second can be answered aloud.
#
# **AND THE PASSAGE ITSELF IS NO LONGER FOUND BY A PATTERN EITHER.**  `QUOTED` and
# `BY_SOURCE`, the patterns for a page and for a bare key, ran over the whole file, and what
# lies between two quote marks in a file is as often the prose between two quotations as it is
# a quotation.  Each pattern was narrowed until the corpus stopped tripping it - a lookahead
# so that `"(OFF, 1-127)" (p. 37)` was not read back from the bracket inside it, the emphasis
# markers allowed before the locator - and each narrowing left the next case standing:
#
# - a curly mark inside a passage ended it, since the pattern's passage could hold no quote
#   mark of either kind, so `"Works the same as “start.”" (p. 62)` matched nothing and was
#   counted as located by the figures that pair.  Twelve quotations were in that state;
# - a passage inside backticks was read, where the place locators and the coverage figures
#   pass over it and the guide says the checker does;
# - prose between two quotations was checked as a quotation wherever the second began with a
#   bracket that read as a page or a key;
# - a passage in curly marks was read back to the nearest straight mark before it.
#
# So every shape is found by `paired()` now: the marks are paired in order over the prose
# with its code spans out, and only what lies between an opening mark and its closing one is
# ever a passage.  What follows it is read by `PAGE_SHAPED`, `read_locator()`, the
# definition's own keys and `place_named()`, in that order, and `stranger()` says whether
# what is left is a key mistyped or an aside.  #4928.
#
# **THE EMPHASIS MARKERS BEFORE THE LOCATOR ARE STILL ALLOWED, FOR A REASON.**  With only
# whitespace allowed between the closing mark and the bracket, `"..."**  (p. 21)` - a
# quotation emphasised in this project's own house style - did not match, and the quotation
# was skipped without a word.  **It looks located to a reader and it is not**, which makes it
# the one silence a writer cannot find by reading their own file carefully.  `LOCATOR_AFTER`
# allows `*` and `_` there, and it can only ever match more.

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

# `PAGE_SHAPED` below is the only place that decides whether a locator is trying to cite a
# page, so a bare source key like `(product_page)` never reaches `read_locator()` at all and
# cannot be mistaken for a locator this tool failed to read.
#
# **THE OTHER SHAPE A LOCATOR TAKES, FOR A DOCUMENT WITH NO PAGES TO CITE**: the source's own
# key, as in `"polyphony up to 24 voices" (product_page)`.  A key followed by a page is the
# paged form above - the page is the more precise locator and is the one worth checking.
#
# **AND A DOCUMENT THAT HAS PAGES IS NOT CITED THIS WAY.**  `"..." (manual)` was looked for
# in the whole of a manual and passed without a page ever being turned to, while
# `(manual, page 42)` beside it was refused on the ground that a document with pages is cited
# by its page.  The bare key is the same case, and 38 quotations in seven definitions were
# written so.  It is refused now, and the report says which page the passage is on so that
# the page can be written in.  Simon's decision of 2026-10-12, with #4928.
#
# **A SOURCE THE DEFINITION HAS NOT GOT IS A MISNAMED SOURCE, WITH A PAGE OR WITHOUT.**
# `(chart p. 3)` failed the run where the definition had no `chart`, and `(chart)` and
# `(chart, #243)` read as no locator at all and passed.  One quotation in the corpus was in
# that state, citing a `chart` where its definition has a `chart_article`.
#
# **AND IT IS A WORD THAT IS A SOURCE KEY SOMEWHERE, NOT ANY WORD AT ALL.**  The first form of
# this read every single lower-case word in the brackets as a key, and so failed a run on
# `(sic)`, `(default)` and `(v2)`: asides, which this tool has always reported as passages
# with no locator and never as faults, because a tool that calls an aside a fault is one
# people learn to disbelieve.  The second asked whether the word had an underscore or was
# like one of the definition's own keys, and failed `(filter_cutoff)`, `(MIDI)` beside a
# `midi_impl` and `(manually)` beside a `manual`, while passing `(guide)` in a definition
# with no guide.  So the test is neither shape nor likeness: **the word is one the bundled
# definitions call a document by, and this definition has no document of that name**.  That
# is what a writer who has the wrong document in mind types, and what an aside is not.
#
# **AND NOT EVERY KEY IS SUCH A WORD.**  The third form took any key of any bundled definition,
# and failed `(midi)`, `(pdf)`, `(system, real time)` and `(keyboard)`: ordinary words that one
# or two definitions happen to name a document by.  The fourth counted, and took a word of one
# piece that three definitions use; that still failed `(update)` and `(support)`, and a third
# definition choosing `midi` for a key would have failed `(midi)` in every other.  **So the
# words of one piece are a list, set down here and not derived**: the ones that are a
# document's name and nothing a writer says in passing.  A key with an underscore in it is
# nobody's ordinary word, and those are still read from the corpus.  `corpus_keys()`.
#
# A key mistyped into no key at all, `(manaul)`, is left where it always was, among the
# passages with no locator.  One of those words written in other capitals is not: `(Manual)`
# where the definition has a `manual` is that key and nobody's aside, and passing it let a
# capital letter get round the rule that a document with pages is cited by its page.  That is
# asked only of a key that is a document's name: `(MIDI)` in a definition keyed `midi` is an
# aside like any other.
DOCUMENT_WORDS = frozenset({
	"addendum", "changelog", "chart", "guide", "implementation", "manual", "reference",
	"specifications", "supplement"})

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
#   on a search of the whole manual without ever turning to page 42.  The first is left in the
#   no-locator figure, where it can be seen, and the second is refused with the bare key of a
#   document that has pages, which is the same case: see `unpaged_quotations()`.
# - What follows the comma is not page-shaped, or it is the paged form and a page citation.
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
# **THESE TWO WERE THE FIRST TO BE FOUND BY PAIRING THE QUOTE MARKS AND NOT BY A PATTERN.**
# A place depends on the definition's own keys and is told apart afterwards, so a pattern for
# it would have to take any bracket at all - and then `"..." (guide) and the heading
# "(10.4) Sync"` reads the words between the two quotations as a third, located `(10.4)`, and
# fails the run on prose.  It was written that way once, and that is what it did.  #4172.
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


def readings (quotation: str) -> list[list[str]]:

	"""The ways a quotation may be on a page: each is a list of parts that must all be there.

	**A SQUARE BRACKET IS THE FILE'S ADAPTATION OR THE MAKER'S OWN PRINT, AND ONLY THE PAGE
	SAYS WHICH.**  `pieces()` reads every bracket as the first: "make[s] it possible" for a
	page that says "makes it possible".  Korg prints a parameter's range in square brackets,
	and a definition quotes it so: `"[1 Note...12 Note]"`.  Read as an adaptation that passage
	has no part left to look for, **and a quotation with nothing to look for was found on
	every page of every document**.  Five quotations in the corpus were in that state, four
	passages and one of them quoted twice, and three more were looked for by one short word,
	`clock` or `note`, the bracket after it being most of what they quote.

	So there are two readings.  The first keeps the brackets as characters the page prints,
	and is the only one for a quotation that has none.  The second is `pieces()`, and counts
	only where it leaves enough to look for: eight characters of the quotation as `squash()`
	leaves it, which is without its spaces and hyphens and with its other punctuation.  A
	quotation is on a page that carries all the parts of either.

	**The second reading does not look at what is inside a bracket at all**, which is right
	for a word the file adapted and proves nothing about a bracket the maker printed: `"Sync
	mode [Internal, External]"` is found on a page that prints `Sync mode [Int, Ext]`.  So
	a quotation found by the second reading alone is named in the report, as the weaker
	check it is.
	"""

	literal = [part for part in squash(quotation).split("...") if part]
	adapted = pieces(quotation)
	ways = [literal] if literal else []

	if adapted != literal and sum(len(part) for part in adapted) >= 8:
		ways.append(adapted)

	return ways


def read_as (text: str, ways: list[list[str]]) -> int | None:

	"""Which of a quotation's readings a text carries: nought for the first, and nothing for none.

	The text has been through `squash()`.  The first reading is the passage with its square
	brackets as printed, so anything above nought is a passage found only with what is in
	them left out.
	"""

	return next((at for at, parts in enumerate(ways) if all(part in text for part in parts)), None)


def carried (text: str, ways: list[list[str]]) -> bool:

	"""Whether text that has been through `squash()` carries every part of one of these readings."""

	return read_as(text, ways) is not None


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

	if path.suffix.lower() in (".txt", ".html"):
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


	def where (self, ways: list[list[str]]) -> list[int]:

		"""Every printed page number whose own page carries a quotation, read one of these ways."""

		# A document whose first sheet is printed page 3 has printed pages past its number of
		# sheets, so the walk goes on by as much as its offsets fall below nought.  Without
		# that the last sheets were never reached, and a passage on one was said to be on
		# no page: four sources in the corpus are numbered so.
		lowest = min([self.source.page_offset] + [run.offset for run in self.source.page_runs])
		last = len(self.pages) * self.source.pages_per_sheet + max(0, -lowest)

		return [number for number in range(1, last + 1)
			if (page := self.printed(number)) is not None and carried(squash(page), ways)]


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


def cites_a_page (text: str) -> list[tuple[str, str]]:

	"""Every passage of `FLOOR` characters or more whose brackets are trying to cite a page."""

	return [(quotation, locator) for quotation, locator in paired(text) or []
		if locator is not None and len(quotation) >= FLOOR and PAGE_SHAPED.search(locator)]


def quotations (text: str) -> list[tuple[str, str | None, list[int]]]:

	"""Every quoted passage in the file with a page citation, the source it names, and the pages.

	The source is whatever the locator put before the page - `(guide p. 6)` gives `guide` -
	and is nothing where the citation is the bare `(p. 6)`.  A definition with one document
	has no reason to name it; one with four has every reason, and naming it is what lets
	the page be looked for in the right place.
	"""

	found = []

	for quotation, locator in cites_a_page(text):
		read = read_locator(locator)

		if read is not None:
			found.append((quotation, read[0], read[1]))

	return found


def named_quotations (text: str, keys: typing.Iterable[str]) -> list[tuple[str, str]]:

	"""Every quoted passage whose locator is one of these source keys and nothing more.

	A document with no pages has no page to cite, so a definition quoting one names the
	document instead.  Only the definition's own source keys count, so an ordinary
	parenthesis after a quotation is not mistaken for a locator.  Spaces inside the brackets
	are not part of the key: `( guide )` used to count as located and be checked by nothing.

	Whether the document it names has pages is not asked here: `unpaged_quotations()` finds
	the ones that have, which `check()` refuses, and `sourced_quotations()` the rest.
	"""

	known = set(keys)

	return [(quotation, locator) for quotation, locator in paired(text) or []
		if locator in known and len(quotation) >= FLOOR]


@functools.lru_cache(maxsize = 1)
def corpus_keys () -> frozenset[str]:

	"""The words the bundled definitions call a document by, and a writer says of nothing else.

	`DOCUMENT_WORDS`, and every source key with an underscore in it, whichever definition
	gives it.  `manual` is a document's name in more than a hundred definitions; `keyboard`
	is one in a single definition and a word in every manual, and is not among them.

	Read once, and only when a definition has a word in the brackets after a quotation
	that is not one of its own keys, since reading every definition takes a few seconds
	and most runs never need it.
	"""

	corpus = pathlib.Path(pymidiinstrumentdefs.__file__).parent / "corpus"
	held = {key
		for name in pymidiinstrumentdefs.available([corpus])
		for key in pymidiinstrumentdefs.load_file(corpus / f"{name}.yaml").sources or {}}

	return frozenset(key for key in held if "_" in key) | DOCUMENT_WORDS


def stranger (
		locator: str,
		known: typing.Collection[str],
		vocabulary: typing.Collection[str] | None = None) -> str | None:

	"""The word a locator offers as a source key, where the definition has no source of that name.

	The word is the whole of what is in the brackets, as in `(chart)` where the sources are
	`manual` and `chart_article`, or what stands before a comma, as in `(guide, 10.4)`.  **It
	is a stranger only if it is a document's name somewhere**: ``vocabulary``, which is
	`corpus_keys()` unless a caller gives its own.  Or if it is such a name in other
	capitals and the definition's own key, `(Manual)` for `manual`.

	Anything else is an aside and is nobody's key: `(sic)`, `(default)`, `(MIDI)`, two words,
	a sentence, a number.  A locator that cites a page is not asked about here, because the
	paged check reads its key.
	"""

	if PAGE_SHAPED.search(locator):
		return None

	word = locator.split(",", 1)[0].strip()

	if not word or word in known:
		return None

	names = corpus_keys() if vocabulary is None else vocabulary

	if word.lower() in known and word.lower() in names:
		return word

	return word if word in names else None


def misnamed_sources (
		text: str,
		keys: typing.Iterable[str],
		vocabulary: typing.Collection[str] | None = None) -> list[tuple[str, str]]:

	"""Every quotation whose locator names a source the definition does not have, and the name.

	With a page after the name or without one, in the order of the file.  **The page was the
	only shape this was ever asked of**, so `(wrong_key p. 3)` failed the run while
	`(wrong_key)` and `(wrong_key, #243)` read as no locator and passed.  Before a page any
	name that is not the definition's is refused; without one, `stranger()` says which words
	are names at all.
	"""

	known = set(keys)
	found: list[tuple[str, str]] = []

	for quotation, locator in paired(text) or []:
		if locator is None or len(quotation) < FLOOR:
			continue

		if PAGE_SHAPED.search(locator):
			read = read_locator(locator)

			if read is not None and read[0] is not None and read[0] not in known:
				found.append((quotation, read[0]))

			continue

		word = stranger(locator, known, vocabulary)

		if word is not None:
			found.append((quotation, word))

	return found


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

	**Found by ``paired()``, as every other shape is and as ``uncovered()`` counts** - same
	text, same pairing, same test of what is a place.  So they cannot disagree: a passage
	this finds is one that function calls located, and a passage with a place after it is
	never reported there as having no locator.  ``paired()`` says what the pairing costs.
	"""

	known = set(keys)

	in_source: list[tuple[str, str]] = []
	numbered: list[tuple[str, str]] = []

	for quotation, locator in paired(text) or []:
		if locator is None or len(quotation) < FLOOR:
			continue

		kind, named = place_named(locator, known, paged)

		if kind == "source":
			in_source.append((quotation, named))
		elif kind == "number":
			numbered.append((quotation, named))

	return in_source, numbered


def sourced_quotations (
		text: str,
		keys: typing.Iterable[str],
		paged: typing.Collection[str] = ()) -> list[tuple[str, str]]:

	"""Every quotation to be looked for in the whole of one named source, in the order of the file.

	The bare key of a document with no pages, and a key followed by a place: the two shapes
	`check()` looks for in one document from end to end.  One list and one order, so that what
	is reported as not in its source is reported where a reader of the file will meet it; the
	two were listed one shape after the other.
	"""

	known = set(keys)
	found: list[tuple[str, str]] = []

	for quotation, locator in paired(text) or []:
		if locator is None or len(quotation) < FLOOR:
			continue

		kind, key = ("source", locator) if locator in known else place_named(locator, known, paged)

		if kind == "source" and key not in paged:
			found.append((quotation, key))

	return found


def unpaged_quotations (
		text: str,
		keys: typing.Iterable[str],
		paged: typing.Collection[str]) -> list[tuple[str, str]]:

	"""Every quotation that cites a document with pages by its key and gives no page.

	The key alone, or the key and a place: `(manual)`, `(manual, section 4)`, `(manual, 42)`.
	**A document that has pages is cited by its page.**  Looked for in the whole of the
	document, such a passage passes without a page ever being turned to, so it is not looked
	for at all: `check()` refuses it and names the page it is on.

	`(manual, p. 42)` is not one of these.  It cites a page, with a comma the paged form
	allows.
	"""

	known = set(keys)
	found: list[tuple[str, str]] = []

	for quotation, locator in paired(text) or []:
		if locator is None or len(quotation) < FLOOR or PAGE_SHAPED.search(locator):
			continue

		key = locator.split(",", 1)[0].strip()

		if key in known and key in paged and (locator == key or SOURCE_THEN.fullmatch(locator)):
			found.append((quotation, key))

	return found


def unreadable_locators (text: str) -> list[tuple[str, str]]:

	"""Every quotation whose locator looks like a page citation this tool cannot read.

	The parenthesis is taken whole, so this is every quotation whose locator is trying to cite
	a page and cannot be read.  Reporting them is the whole purpose: they are the
	quotations that would otherwise be skipped without a word.
	**The count is nought and the run now fails if it is not**, which it could only be made
	to do once the forty-eight that were there had been read and put right.
	"""

	return [(quotation, locator) for quotation, locator in cites_a_page(text)
		if read_locator(locator) is None]


# ── Finding the passages: pairing the marks, and what a file must be for that to work ────
#
# **EVERY SEARCH FOR A QUOTATION ABOVE READS `paired()` BELOW.**  This section began as the
# figure this tool never printed.  Everything else answered "of the quotations I can see, are
# they on their pages", and nothing answered **"how many did I not see"** - and a quotation
# with no locator at all is passed over in silence, so a definition could read "5 of 5
# quotations are on the page they cite" while holding thirty nobody had looked at.
# `korg/minilogue` did exactly that, and giving its quotations locators took it to 22 of 22
# and immediately caught three that were right about the printed page and absent from its
# text layer.  #4359.
#
# **THE MARKS HAVE TO BE PAIRED RATHER THAN PATTERN-MATCHED.**  A `[^"]{12,}` between two quote
# characters matches the prose *between* a closing mark and the next opening one just as
# readily as it matches a quotation, so the obvious sweep reports about twice what is there.
# That has now been written wrongly twice - once while auditing the PĒRKONS, where it gave 49
# for a file holding 35, and once while answering whether this task was worth doing at all.
# Pairing in order is the whole fix.
#
# **AND PAIRING IN ORDER IS SOUND ONLY WHERE THE MARKS DO PAIR, WHICH IS CHECKED AND NOT
# ASSUMED.**  One stray mark makes the count odd, and `odd_quote_marks()` and
# `odd_backticks()` see it.  Two make it even again and turn everything between them inside
# out, which no count can see - and a pattern, for all its faults, was immune to: a wrong
# quotation between two inch marks failed the run while a page and a bare key were found by
# pattern, and passed once they were found by pairing.  So the pairing is also asked whether it
# looks like one: `mispaired()` for a passage that begins or ends with a space, which is what
# prose between two quotations does and a quotation does not, and `hidden()` for a quotation
# with its locator found inside backticks.  A quote mark *inside* a quotation shows the same
# way, and twelve definitions had one.  None of these tells is proof.  Each fails the run,
# because the alternative is a clean bill for a file nobody could read.  #4928.

# Straight only.  A curly mark inside a straight-marked passage is the maker's own and is part
# of the passage, and six definitions quote one.  A passage *in* curly marks would need pairing
# by direction instead of by order, so it is not paired at all, and `curly_outside()` fails
# the run on a curly mark that stands outside every passage.
QUOTE_MARK = re.compile(r"\"")

# A locator follows a quotation if a parenthesis does, allowing this project's emphasis
# markers between the two.  Whether it is a locator this tool can *read* is
# `read_locator()`'s question and is already reported; this only asks whether the writer
# gave one at all.
LOCATOR_AFTER = re.compile(r"^[\s*_]*\(([^)]*)\)")

# Page-shaped: `p.` or `pp.` and a number.  Asked in this one place, of what is in the
# brackets, so that nothing can disagree about what counts as an attempt to cite a page.
PAGE_SHAPED = re.compile(r"pp?\.\s*\d")

# The shortest quotation this tool will check, stated once so the floor and the report of
# what the floor excluded cannot drift apart.
FLOOR = 12

# A code span: a run of backticks, and everything up to the next run of as many, which is how
# Markdown reads one.  One each side is the form every definition here uses.  Two each side
# is a span too, and is how one that holds a backtick is written; it was read as two empty
# spans with prose between them.  Two spans set back to back are read as one, which loses
# nothing, since both are taken out.
#
# What stands for a span while the marks are paired is a character no definition holds, so
# that a span is neither white space, which a locator may follow a passage across, nor
# anything a key or a page could be made of.
SPANNED = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
SPAN = "\x00"

# Where YAML ends a line: the two ways a file's own lines end, and three characters more.
LINE_END = re.compile("\r\n|[\r\n\x85\u2028\u2029]")


@functools.lru_cache(maxsize = 4)
def comment_starts (text: str) -> dict[int, int]:

	"""Where the comment of each line of a file begins: the column, by the line's number.

	Lines are numbered from one and columns from nought, and a line with no comment is not
	among them.

	**The first `#` on a line that stands outside every value is where its comment begins.**
	A hundred and one `#` characters in this corpus sit inside a value - `CC#7`,
	`"Playback param #1"`, ``firmware: "#246"`` - so the first `#` on a line is often not it.

	**What is a value is YAML's question, and YAML's own scanner answers it here.**  This
	tool answered it for itself three times.  The first counted every double quote mark, read
	``title: 'The 19" guide'`` as opening a string, and lost the comment after it.  The
	second read a line at a time, so the second line of a quoted title wrapped over two was
	a comment holding one quote mark, and a correct definition failed for an odd number of
	them.  The third carried an open value from line to line and took the apostrophe of
	``'til dawn``, at the start of a wrapped plain title, for the opening of one: every
	comment after it was swallowed, and a wrong quotation in one of them passed.  PyYAML is
	what loads a definition.  It takes a `#` for a comment wherever one token has ended and
	the next not begun, so a `#` inside a scalar, a tag, an anchor, an alias or a directive
	is not one, and any other is.

	**Each token is placed by how far into the file it is, and not by its line.**  YAML ends
	a line at three characters this tool's own split does not, so a line count kept in step
	only until a quoted title held one of them; from there on every comment was judged
	against the line above.  A byte-order mark is not part of the file's first line, and the
	scanner PyYAML is built with counts from after it where its other one counts it, so it
	is taken off before either reads.  And a block scalar begins on the line after its
	indicator, where a comment may follow the indicator itself; that line ends where YAML
	ends a line, as any other does.

	A file that is not YAML raises PyYAML's own error.  `check()` loads a definition before
	it reads its prose, so none reaches here from a run.
	"""

	marked = 1 if text.startswith("\ufeff") else 0
	body = text[marked:]
	loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
	holding = (yaml.ScalarToken, yaml.TagToken, yaml.AnchorToken, yaml.AliasToken, yaml.DirectiveToken)
	held: list[tuple[int, int]] = []

	for token in yaml.scan(body, Loader = loader):
		if not isinstance(token, holding):
			continue

		begins, ends = token.start_mark.index, token.end_mark.index

		if isinstance(token, yaml.ScalarToken) and token.style in ("|", ">"):
			ended = LINE_END.search(body, begins)
			begins = len(body) if ended is None else ended.end()

		held.append((begins, ends))

	begun = [begins for begins, _ in held]
	found: dict[int, int] = {}
	so_far = 0

	for row, line in enumerate(body.split("\n")):
		at = line.find("#")

		while at >= 0:
			before = bisect.bisect_right(begun, so_far + at) - 1

			if before < 0 or so_far + at >= held[before][1]:
				found[row + 1] = at + (marked if row == 0 else 0)
				break

			at = line.find("#", at + 1)

		so_far += len(line) + 1

	return found


# The line a definition's written account begins on: `source:` at the start of the line, and a
# block scalar after it, folded or literal.  **Nothing else is read as the account.**  A
# definition may write its account as a plain or a quoted scalar, or quote the key, and load
# perfectly well, and this tool then finds no account in it at all; `check()` says so and
# fails, where it used to report a file with nothing to check.
ACCOUNT = re.compile(r"^source:\s*[>|]")


def prose_lines (text: str) -> list[tuple[int, str]]:

	"""Each line of a definition that holds prose, with its number in the file: see `prose()`."""

	kept: list[tuple[int, str]] = []
	in_account = False
	comments = comment_starts(text)

	for number, line in enumerate(text.split("\n"), 1):
		stripped = line.strip()

		# The written account is a block scalar, so it runs until something unindented
		# starts the next field.  Its own lines carry no marker of their own, and a `#` in
		# it is literal text rather than a comment, so the whole line is kept as it stands.
		if in_account:
			if stripped and not line.startswith((" ", "\t")):
				in_account = False
			else:
				kept.append((number, line))
				continue

		if ACCOUNT.match(line):
			in_account = True
			continue

		if number in comments:
			kept.append((number, line[comments[number]:]))

	return kept


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

	Where a line's comment begins is `comment_starts()`'s question.
	"""

	return "\n".join(kept for _, kept in prose_lines(text))


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

	return SPANNED.sub(" ", flowed(prose(text)))


def odd_quote_marks (text: str) -> bool:

	"""Whether a paragraph of this definition's prose holds an odd number of quote marks.

	Pairing in order is only sound where the marks pair, so a file with an odd count is one
	this tool cannot speak for.  Said out loud rather than silently mis-paired, because a
	silence was being read as a clean bill.  **Counted by the paragraph**, as `odd_places()`
	says: counted over the whole file, a stray mark in each of two paragraphs came to an
	even number and every quotation between them was paired inside out.
	"""

	return any(which == "quote marks" for _, which in odd_places(text))


def odd_backticks (text: str) -> bool:

	"""Whether a paragraph of this definition's prose holds a backtick that pairs with nothing.

	**ONE BACKTICK NEVER CLOSED TURNS EVERY LATER CODE SPAN INSIDE OUT.**  `quotable()` takes
	out what lies between one run of backticks and the next of as many, so after a stray one
	it takes out the prose between two spans and keeps what was inside them.
	`udo_audio/super_6` had one, a parameter's name opened and not closed, and from there on
	the pairing saw 7 of the 25 quotations that cite a page.  Nothing said so.  The remedy
	this tool recommends for a passage that quotes nothing is backticks, and after a stray
	one that remedy stops working too: an example inside a later span is read as a quotation.

	A run of two that no run of two closes is the same fault: ``the label is `` when unset``
	opens a span and never ends it.
	"""

	return any(which == "backticks" for _, which in odd_places(text))


def odd_places (text: str) -> list[tuple[int, str]]:

	"""Where a definition's marks fail to pair: a line number, and which mark.

	The first line of each paragraph of prose that holds a backtick left over once its code
	spans are out, or an odd number of quote marks, a paragraph being a run of comment
	lines, or of the account's lines, with no empty line in it.  Neither a quotation nor a
	code span runs from one paragraph into the next, so the paragraph with the stray mark is
	the one named, and a stray mark in each of two paragraphs is two faults and not none.

	**This is what makes "an odd number" something a writer can act on.**  One definition
	held 119 backticks, and being told that one of them was unclosed is being told nothing.
	"""

	places: list[tuple[int, str]] = []
	paragraph: list[tuple[int, str]] = []
	previous = 0

	for number, kept in prose_lines(text) + [(0, "")]:
		if paragraph and (number != previous + 1 or not kept.strip(" \t#")):
			flat = flowed("\n".join(line for _, line in paragraph))

			if "`" in SPANNED.sub("", flat):
				places.append((paragraph[0][0], "backticks"))
			elif len(QUOTE_MARK.findall(SPANNED.sub(" ", flat))) % 2:
				places.append((paragraph[0][0], "quote marks"))

			paragraph = []

		if kept.strip(" \t#"):
			paragraph.append((number, kept))

		previous = number

	return places


def raw_pairs (text: str) -> list[tuple[str, str | None]] | None:

	"""The passages between paired quote marks with each code span still one character.

	What `paired()` hands on once the spans are spaces.  `mispaired()` reads this, because
	a passage that opens or closes with a code span does not open or close with a space.
	"""

	if odd_places(text):
		return None

	flat = SPANNED.sub(SPAN, flowed(prose(text)))
	positions = list(QUOTE_MARK.finditer(flat))
	found: list[tuple[str, str | None]] = []

	for opening, closing in zip(positions[::2], positions[1::2]):
		after = LOCATOR_AFTER.match(flat[closing.end():])
		locator = None if after is None else after.group(1)

		# A span in the brackets of a page citation stays, as something no locator is made
		# of, so that the locator is refused and seen.  Anywhere else it was always white
		# space, and `(guide, `10.4`)` is an aside that names no place.
		if locator is not None:
			locator = locator.replace(SPAN, "`...`" if PAGE_SHAPED.search(locator) else " ")
			locator = " ".join(locator.split())

		found.append((flat[opening.end():closing.start()], locator))

	return found


def paired (text: str) -> list[tuple[str, str | None]] | None:

	"""Every passage between an opening quote mark and its closing one, with what follows it.

	In the order of the file: the passage, and what is in the brackets directly after it with
	its spaces closed up, or nothing where no bracket follows.  **Nothing at all where the
	quote marks or the backticks do not pair**, because pairing an odd number in order pairs
	every one after the stray wrongly; `check()` says so and the run fails.

	Every search for a quotation in this tool reads this, so that they agree about what a
	passage is.  What the pairing costs, and each is deliberate:

	- a passage in curly marks is not seen, and `curly_outside()` fails the run on one;
	- a passage inside backticks is code and is passed over, which is the point of the
	  backticks, and `hidden()` fails the run where what is passed over is a quotation with
	  its locator;
	- a code span inside a quoted passage is cut out of it before it is looked for, so
	  ``"press the `PRG` button"`` is looked for without its middle and not found;
	- a code span standing between a passage and its brackets parts them, and one inside
	  the brackets of a page citation leaves a locator nobody can read, which is reported:
	  ``(`manual` p. 4)`` named no document once the span was out, and was looked for in all;
	- a run of backticks that no run of as many closes is no span at all, and fails the run
	  as an odd quote mark does.

	**An even number of stray marks in one paragraph pairs, wrongly.**  See `mispaired()`.
	"""

	raw = raw_pairs(text)

	return None if raw is None else [(passage.replace(SPAN, " "), locator) for passage, locator in raw]


def mispaired (
		text: str,
		keys: typing.Iterable[str] = (),
		paged: typing.Collection[str] = ()) -> list[tuple[str, str | None]]:

	"""The passages that look like prose between two quotations, and what follows each.

	**A quotation does not begin or end with a space, and the prose between two quotations
	does both.**  So a passage that is empty, or has white space at either edge, says the
	marks around it are an opening and a closing mark that do not belong together:

	- a quote mark inside a quotation, which ends it early: ``"set this to "ON" or "P-Dump""``
	  is three passages and two of them are ``" or "`` and nothing at all.  Twelve
	  definitions held one, and ten quotations with a locator were looked for by their tail
	  or not at all.  The mark inside a quotation is written as a single one;
	- two stray marks, an inch mark each, with a real quotation somewhere between them.

	**And a passage does not begin by closing an emphasis and giving a locator**, which the
	prose after an emphasised quotation does: between ``**"the maker's words"** (guide). Its
	disk is 3.5"`` and the stray mark before it, the second "passage" is ``** (guide). Its
	disk is 3.5``.  The emphasis is what tells it.  A passage that begins with a bracket of
	its own, ``"(10.4) Sync and tempo"``, is a quotation like any other and ninety-one in the
	corpus begin so; the first form of this sign failed every one whose bracket read as a
	locator.

	A code span is not white space, so a quotation that opens or closes with one is sound.

	Not proof either way.  A stray pair can fall where no edge has a space: a mark inside a
	quotation and flush against a bracket, ``("ON")``, shows nothing, and one definition
	held such a one.  A writer may also want a passage that is empty or padded, and has to
	put it in backticks.  It is the tell there is, and a run fails on it.
	"""

	known = set(keys)
	found: list[tuple[str, str | None]] = []

	for passage, locator in raw_pairs(text) or []:
		opened = EMPHASIS_THEN_LOCATOR.match(passage)

		if (not passage or passage != passage.strip()
				or (opened is not None and located_by(" ".join(opened.group(1).split()), known, paged))):
			found.append((passage.replace(SPAN, "`...`"), locator))

	return found


def located_by (
		locator: str | None,
		known: typing.Collection[str],
		paged: typing.Collection[str]) -> bool:

	"""Whether what follows a passage is a locator this tool reads or refuses, and not an aside.

	A page; one of the definition's keys, alone or with a place after it; or a section or
	version number.  The key of a document with pages given with no page is one of these: it
	is refused, which is not the same as there being nothing there.
	"""

	if locator is None:
		return False

	keyed = locator.split(",", 1)[0].strip() in known and SOURCE_THEN.fullmatch(locator) is not None

	return (PAGE_SHAPED.search(locator) is not None
		or locator in known
		or keyed
		or place_named(locator, known, paged)[0] is not None)


# How the prose after an emphasised quotation begins, where a stray mark has paired it as a
# passage: the emphasis closing, and then the brackets.
EMPHASIS_THEN_LOCATOR = re.compile(r"^[*_]+\s*\(([^)]*)\)")

# A quoted passage with brackets after it, as it stands inside a code span.
QUOTED_IN_CODE = re.compile(r"\"([^\"]*)\"[\s*_]*\(([^)]*)\)")


def hidden (
		text: str,
		keys: typing.Iterable[str],
		paged: typing.Collection[str] = ()) -> list[tuple[str, str]]:

	"""Quotations with a locator that stand inside backticks, where nothing looks for them.

	**Two backticks left open hide everything between them**, exactly as one does, and the
	count is even: ``the `Sync setting ... "the maker's words" (guide) ... the `Clock
	setting`` is one long code span to this tool, with a quotation and its locator inside.
	A span that holds a passage of `FLOOR` characters or more and a locator after it is that,
	far more often than it is an example of how a locator is written - the corpus has 5,446
	code spans and not one of them holds such a thing.

	So it fails the run.  A passage in backticks that quotes nothing has no locator, and is
	passed over as it always was.
	"""

	if odd_backticks(text):
		return []

	known = set(keys)
	found: list[tuple[str, str]] = []

	for span in SPANNED.finditer(flowed(prose(text))):
		for match in QUOTED_IN_CODE.finditer(span.group(0)):
			quotation, locator = match.group(1), " ".join(match.group(2).split())

			if len(quotation) >= FLOOR and located_by(locator, known, paged):
				found.append((quotation, locator))

	return found


# A curly double quote mark, of either direction.
CURLY_MARK = re.compile(r"[“”]")


def curly_outside (text: str) -> list[str]:

	"""Each curly double quote mark standing outside every straight-marked passage, in its words.

	Only straight marks are paired, so a passage in curly marks is seen by nothing here,
	whatever follows it.  A curly mark *inside* a straight-marked passage is the maker's own
	and is left alone; one inside backticks is code.  Any other is reported with the words
	around it, and the run fails: the first form of this looked only for a curly passage
	with a locator it could read after it, and so passed one with a misnamed key, one under
	the floor, and one with a curly pair inside it.  The corpus has none.
	"""

	if odd_places(text):
		return []

	flat = quotable(text)
	positions = list(QUOTE_MARK.finditer(flat))
	outside = list(flat)

	for opening, closing in zip(positions[::2], positions[1::2]):
		outside[opening.start():closing.end()] = SPAN * (closing.end() - opening.start())

	return [" ".join(flat[max(0, mark.start() - 30):mark.end() + 30].split())
		for mark in CURLY_MARK.finditer("".join(outside))]


def uncovered (
		text: str,
		keys: typing.Iterable[str],
		paged: typing.Collection[str] = (),
		vocabulary: typing.Collection[str] | None = None) -> tuple[list[str], list[str]]:

	"""The quoted passages this tool never looked at, and why, by pairing the marks in order.

	Two answers, because there are two reasons and a reader cannot reconcile a figure against
	one of them:

	- **no locator at all**, of `FLOOR` characters or more, which is what #4359 is about;
	- **under `FLOOR` characters while carrying a locator**, which is the floor doing its job
	  and is still invisible in the figures - one definition's 62 locators against the
	  gate's 60 were two of these, `5-octave` and a version string.

	**Neither is reported as an error, and that is deliberate.**  Some of what this finds
	should not be a quotation at all: `"System Exclusive"` quoting nothing, a PDF's internal
	metadata title, one definition quoting another definition in this corpus.  The remedy for
	those is backticks rather than an invented locator, so the figure is a coverage report and
	says *passages*, not *unchecked quotations*.  A tool that called them faults would be the
	kind people learn to disbelieve.

	**What follows a passage and is trying to be a locator is not among them.**  A word that reads
	as a source key and is not one, and the key of a document with pages given with no page, are
	faults in the file and are reported as that by `check()`; an aside is neither, and is here.
	"""

	known = set(keys)

	unlocated: list[str] = []
	short: list[str] = []

	for quotation, locator in paired(text) or []:
		located = located_by(locator, known, paged)

		# A word that is some other definition's key is a misnamed source, reported and
		# failed on, so it is not also a passage with no locator.  It is no locator for a
		# passage under the floor, though: that figure is for a locator this tool would
		# have read.
		if located and len(quotation) < FLOOR:
			short.append(quotation)
		elif (not located and len(quotation) >= FLOOR
				and (locator is None or stranger(locator, known, vocabulary) is None)):
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

	"""What one definition's check came to.  Every field counts quotations, or says what it counts.

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

	# Not there.  This fails the run, and so does every fault of the file's own that
	# `faults()` adds up.
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
	# the file.  **These were collected and never printed** until #4475, and until #4928
	# only a locator with a page after the name was ever asked.
	misnamed: int = 0

	# **IN DEFINITIONS, NOT QUOTATIONS**, one of the three fields that are: one if this
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

	# **IN DEFINITIONS, NOT QUOTATIONS**: one where a paragraph of the prose holds an odd
	# number of quote marks, or a backtick that closes no code span and opens none, so
	# nothing in it can be paired and nothing in it was checked.  Nought is the whole corpus,
	# and anything else fails the run.
	unpairable: int = 0

	# Every clause on the cited page and not run together by its text layer: the weaker
	# check.  **These were printed for their definition and counted in no figure**, neither
	# passed nor missing, so the summary balanced only where they happened to be few.
	partly: int = 0

	# They cite a document that has pages and give no page: by its key, or by a number alone
	# where the definition has sources and every one has pages.  Refused, and not looked for:
	# a search of the whole document passes a passage without a page ever being turned to.
	unpaged: int = 0

	# **IN MARKS, NOT QUOTATIONS**: curly double quote marks standing outside every
	# straight-marked passage.  Only straight marks are paired, so a passage in these was
	# seen by nothing.
	curly: int = 0

	# They cite a page where no source it could be in has pages: the source named has none,
	# or none is named and none has any.  There is no page to turn to and nothing looked for
	# them.  These were counted as unchecked and named nowhere.
	pageless: int = 0

	# **IN PASSAGES, AND EACH IS ALSO IN WHATEVER FIGURE ITS LOCATOR PUTS IT IN**: passages
	# that begin or end with a space, are empty, or begin with a locator, which is what the
	# prose between two quotations looks like, so the marks around them do not belong
	# together.
	mispaired: int = 0

	# Quotations with a locator standing inside backticks, where nothing looks for them.
	hidden: int = 0

	# Counted in `passed` as well: found only with what is in their square brackets left
	# out.  Right for a word the file adapted, and a weaker check for a bracket the maker
	# prints, so each is named.
	adapted: int = 0

	# **IN DEFINITIONS, NOT QUOTATIONS**: one where the written account is not a block scalar,
	# so this tool found no account in it and checked nothing.
	accountless: int = 0


def check (name: str, path: pathlib.Path, index: dict[str, pathlib.Path]) -> Tally:

	"""Check one definition, printing what it found."""

	definition = pymidiinstrumentdefs.load_file(path)
	held, absent = documents(definition, index)
	body = path.read_text(encoding = "utf-8")
	sources = definition.sources or {}

	# A document with pages is cited by its page, so a key followed by a place is read only
	# for one without.  See `place_named()`.
	paged = {key for key, source in sources.items() if source.paginated}

	print(f"\n{name}")

	for line in absent:
		print(f"    {line}")

	# **AN ACCOUNT THIS TOOL CANNOT FIND IS NOT AN ACCOUNT WITH NOTHING IN IT.**  Every search
	# reads `prose()`, which takes the account to be a block scalar.  A definition may write
	# it as a plain or a quoted scalar and load all the same, and the pattern that used to
	# find a page and a bare key read the whole file and so still found them.
	if definition.source and not any(ACCOUNT.match(line) for line in body.split("\n")):
		print(f"    its account does not begin `source: >-` or `source: |` at the start of a "
			f"line, which is the one form this tool reads, so NOTHING IN IT WAS CHECKED")

		return Tally(accountless = 1)

	# **NOTHING CAN BE CHECKED WHERE THE MARKS DO NOT PAIR, AND THAT FAILS THE RUN.**  A page
	# and a bare key were found by a pattern and so were still checked in such a file, while
	# the place locators and both coverage figures were silently nought.  Every shape is
	# found by pairing now, so there is nothing left to check, and a definition that reported
	# a clean bill for the half this tool could still see would be the old silence again.
	places = odd_places(body)

	if places:
		kinds = {which for _, which in places}
		said = " AND ".join(words for which, words in (
			("backticks", "A BACKTICK THAT NO OTHER CLOSES"),
			("quote marks", "AN ODD NUMBER OF QUOTE MARKS")) if which in kinds)

		print(f"    its prose holds {said}, so this tool cannot pair its quote marks and NOTHING "
			f"IN IT WAS CHECKED - a mark is left open, or stands alone, and a code span is closed "
			f"by as many backticks as opened it: "
			+ "; ".join(f"in the paragraph that begins at line {line} ({which})"
				for line, which in places))

		return Tally(unpairable = 1)

	with_a_page = quotations(body)
	misnamed = misnamed_sources(body, sources)
	# A page cited where no source it could be in has pages: the source it names has none,
	# or it names none and no source of this definition has any.
	pageless = [(quotation, key or "no source named, and none here has pages")
		for quotation, key, _ in with_a_page
		if (key in sources and key not in paged) or (key is None and not paged)]
	found = [(quotation, key, pages) for quotation, key, pages in with_a_page
		if key in paged or (key is None and paged)]
	unpaged = unpaged_quotations(body, sources, paged)
	named = sourced_quotations(body, sources, paged)
	_, numbered = placed_quotations(body, sources, paged)

	# A number alone names no document, and is looked for in those that have no pages.
	# Where every source has pages there is nowhere to look that a page would not name
	# better, and it is the bare key's case: `(1.0)` passed on a search of whole manuals.
	# A definition with no sources at all is not that case: nothing in it has pages.
	numbers_refused: list[tuple[str, str]] = []

	if numbered and sources and len(paged) == len(sources):
		numbers_refused, numbered = numbered, []

	by_name = {document.name: document for document in held}
	unreadable = unreadable_locators(body)
	curly = curly_outside(body)
	apart = mispaired(body, sources, paged)
	inside = hidden(body, sources, paged)
	unlocated, short = uncovered(body, sources, paged)

	# **Computed before any of the early returns below and carried into every one of them.**
	# A definition with nothing checkable is exactly where an unlocated quotation hides, so a
	# coverage figure that only appeared on the path where checking happened would miss the
	# cases it exists for.  **And so are the faults that are the file's own**, which need no
	# document to find: a misnamed source went unreported wherever no document with pages
	# could be read, because the return for that came before the test for it.
	counted = {
		"no_locator": len(unlocated),
		"too_short": len(short),
		"unreadable": len(unreadable),
		"misnamed": len(misnamed),
		"unpaged": len(unpaged) + len(numbers_refused),
		"pageless": len(pageless),
		"curly": len(curly),
		"mispaired": len(apart),
		"hidden": len(inside),
	}

	# Said first, because it puts everything after it in doubt: where the marks are paired
	# wrongly, what is listed below as a quotation may be the prose beside one.
	if apart:
		print(f"    {len(apart)} passage(s) BEGIN OR END WITH A SPACE, ARE EMPTY, OR BEGIN BY "
			f"CLOSING AN EMPHASIS BEFORE A LOCATOR, which is what the prose between two "
			f"quotations looks like, so the marks here may be paired wrongly and what follows "
			f"may not be what was quoted - write a quote mark inside a quotation as a single "
			f"one, look for a stray mark earlier in the paragraph, and put a passage that "
			f"really is empty or padded in backticks:")

		for quotation, locator in apart:
			print(f"        {quotation[:88]!r}" + (f" ({locator})" if locator else ""))

	if inside:
		print(f"    {len(inside)} quotation(s) with a locator stand INSIDE BACKTICKS, so they are "
			f"NOT CHECKED - a backtick left open hides what follows it; and an example of how "
			f"a locator is written goes without its locator:")

		for quotation, locator in inside:
			print(f"        ({locator}): {quotation[:88]}")

	if curly:
		print(f"    {len(curly)} CURLY QUOTE MARK(S) stand outside every quotation, and this "
			f"tool pairs straight marks only, so a passage in curly marks is NOT CHECKED - write "
			f"the marks straight, or use backticks where nothing is quoted:")

		for words in curly:
			print(f"        ...{words}...")

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

	# Said even where the definition is otherwise clean, because the point of the figure is
	# that nobody knew these quotations existed.
	if unreadable:
		print(f"    {len(unreadable)} quotations have a locator this tool cannot read, so they "
			f"are NOT CHECKED - the convention is a single word before the page:")

		for quotation, locator in unreadable:
			print(f"        ({locator}): {quotation[:88]}")

	# **A DOCUMENT THAT HAS PAGES IS CITED BY ITS PAGE.**  Not looked for in the whole of it:
	# that passed a passage without a page ever being turned to.  Where the document is held,
	# the pages that carry the passage are named, so that one of them can be written in.
	if unpaged or numbers_refused:
		print(f"    {len(unpaged) + len(numbers_refused)} quotation(s) cite a document that has "
			f"pages and give NO PAGE, so they are NOT CHECKED - write the page, as (key p. 12); "
			f"or, where the document has no pages to turn to, say `paginated: false` on its "
			f"source:")

		for quotation, key in unpaged:
			print(f"        ({key}): {quotation[:88]}")

			if key in by_name:
				on = by_name[key].where(readings(quotation))

				print(f"            it is on: " + (f"printed p. {', '.join(str(n) for n in on)}"
					if on else f"no page of it as this tool reads it"))

		# A number alone names no document, and every source here has pages, so each that is
		# held is asked for the page.
		for quotation, locator in numbers_refused:
			print(f"        (a number alone, {locator}, and every source here has pages): "
				f"{quotation[:88]}")

			pages = [f"{document.name} printed p. {number}"
				for document in with_pages(held) for number in document.where(readings(quotation))]

			print(f"            it is on: "
				+ (", ".join(pages) if pages else "no page of a document held, as this tool reads it"))

	# The other way round: a page cited in a source that has none.  There is no page to
	# turn to, so it was unchecked, and nothing said which quotation or why.
	if pageless:
		print(f"    {len(pageless)} quotation(s) cite a page WHERE NO SOURCE IT COULD BE IN HAS "
			f"PAGES, so they are NOT CHECKED - cite a document with no pages by its key, as "
			f"(key) or (key, where in it); where the document does have pages, take "
			f"`paginated: false` off its source; and where the definition has no sources, give "
			f"it the one the page is in:")

		for quotation, key in pageless:
			print(f"        ({key}): {quotation[:88]}")

	# A locator naming a source the definition does not have.  The paged check declines to
	# fall back to searching every document, which is right - a page number that happens to
	# exist in another manual must not pass a quotation credited to one this definition does
	# not hold - but it then dropped the quotation without a word, so the file's mistake was
	# invisible and the quotation was never checked against anything.
	for quotation, stranger_named in misnamed:
		print(f"\n      NO SOURCE NAMED {stranger_named!r}: {quotation[:110]}")
		print(f"          this definition's sources are: "
			f"{', '.join(sorted(sources)) or 'none'} - and an aside goes in the sentence, "
			f"not in the brackets after a quotation")

	if not found and not named and not numbered:
		# One with a locator that is refused quotes something with a locator all the same.
		refused = bool(unreadable or misnamed or unpaged or numbers_refused or pageless or curly
			or apart or inside)

		if not refused:
			print(f"    no quotation in it cites a page or a source, so there is nothing to check")

		return Tally(nothing_to_check = 0 if refused else 1, **counted)

	# **A definition with no sources has no document for a number alone to be in**, which is
	# not a document that could not be read: it was counted as unchecked, beside a page in
	# the same file that failed the run.
	if not sources:
		for quotation, locator in numbered:
			print(f"\n      IN NO DOCUMENT CITED, located ({locator}): {quotation[:110]}")
			print(f"          this definition has no sources, so there is none for it to be in")

		return Tally(missing = len(numbered), **counted)

	if not held:
		print(f"    {len(found) + len(named) + len(numbered)} quotations cite a source and "
			f"none could be read")
		return Tally(unchecked = len(found) + len(named) + len(numbered), **counted)

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
	unturned: list[tuple[str, str, list[int]]] = []
	partly: list[tuple[str, list[int]]] = []
	disagreed: list[tuple[str, str, int]] = []
	adapted: list[tuple[str, str]] = []
	passed = 0

	for quotation, source, cited in found:
		ways = readings(quotation)
		where = None

		# A quotation that names its source is looked for in that document alone, which is
		# the stronger check: a page number that happens to exist in one of the other three
		# cannot pass it. A name that is not one of this definition's sources is a mistake
		# in the file rather than a reason to fall back, and is not here: `misnamed` took it
		# above, before any return. **It used to be collected and never printed**, so seven
		# of them across three definitions had never been checked against anything when
		# #4475 found them.
		looking = [d for d in turnable if d.name == source] if source else turnable

		# A page in a document of this definition's that could not be read: unchecked, and
		# said to be, which it was not.
		if source and not looking:
			unchecked += 1
			unturned.append((quotation, source, cited))
			continue

		for document in looking:
			for number in cited:
				page = document.printed(number)

				how = None if page is None else read_as(squash(page), ways)

				if how is not None:
					where = (document.name, number)

					# The first reading is the passage with its brackets as printed.
					if how:
						adapted.append((quotation, f"{document.name} p. {number}"))

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
					how = None if again is None else read_as(squash(again), ways)

					if how is not None:
						second = (document.name, number)

						if how:
							adapted.append((quotation, f"{document.name} p. {number}"))

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

	if unturned:
		print(f"    {len(unturned)} cite a page of a document that could not be read, so they "
			f"are unchecked:")

		for quotation, source, cited in unturned:
			print(f"        ({source} p. {', '.join(str(n) for n in cited)}): {quotation[:88]}")

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

		elsewhere = [f"{d.name} printed p. {number}"
			for d in turnable for number in d.where(readings(quotation))]

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

		# A bracket is read two ways, and a reader who is told a passage is absent needs to
		# know which was tried: an adaptation that leaves too little is not looked for.
		# Only where it holds a pair of brackets once folded: the maker's own cross-reference
		# is folded out before anything is looked for, and a bracket never closed is read as
		# the character it is.
		if re.search(r"\[[^\]]*\]", squash(quotation)):
			print(f"          its square brackets were looked for as printed"
				+ (", and with what is in them left out" if len(readings(quotation)) > 1
					else "; with what is in them left out, too little remains to look for"))

	# A quotation that names a source rather than a page is looked for in the whole of that
	# document, which is what `paginated: false` means: there is no page to turn to.
	wholes: dict[str, str] = {}

	def whole_of (document: Document) -> str:

		"""The whole of a held document, squashed, and read once however often it is asked for."""

		if document.name not in wholes:
			wholes[document.name] = squash("\n".join(document.pages))

		return wholes[document.name]

	second_wholes: dict[str, str | None] = {}
	one_reading: set[str] = set()

	def second_reading_holds (document: Document, ways: list[list[str]]) -> int | None:

		"""Which reading of the quotation the other extractor's whole document carries, if any."""

		if document.name not in second_wholes:
			again = read_whole_again(document.path)
			second_wholes[document.name] = None if again is None else squash(again)

			# A PDF the second extractor gave nothing for has had one reading, and an
			# absence resting on it is said to.  A text file is read as it is.
			if again is None and document.path.suffix.lower() == ".pdf":
				one_reading.add(document.name)

		again_whole = second_wholes[document.name]

		return None if again_whole is None else read_as(again_whole, ways)

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

		ways = readings(quotation)
		how = read_as(whole, ways)

		if how is None:
			how = second_reading_holds(named_document, ways)

			if how is None:
				elsewhere_missing.append((quotation, key))
				continue

			disagreed_whole.append((quotation, key))

		named_passed += 1

		if how:
			adapted.append((quotation, key))

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

	holding: list[tuple[str, str, list[str]]] = []
	nowhere: list[tuple[str, str]] = []
	perhaps_unread: list[tuple[str, str]] = []

	# **A number alone is looked for in the documents that have no pages, and in no other.**
	# It names a section or a release, which is how such a document is found one's way
	# about; in a document with pages the page says more, and a search of the whole of one
	# is what the bare key was refused for.
	searchable = [document for document in held if not document.source.paginated]
	unread = [key for key, source in sources.items() if not source.paginated and key not in by_name]

	for quotation, locator in numbered:
		ways = readings(quotation)
		read = {document.name: read_as(whole_of(document), ways) for document in searchable}
		holders = [name for name, how in read.items() if how is not None]

		if not holders:
			read = {document.name: second_reading_holds(document, ways) for document in searchable}
			holders = [name for name, how in read.items() if how is not None]

			if holders:
				disagreed_whole.append((quotation, ", ".join(holders)))

		if holders and all(read[name] for name in holders):
			adapted.append((quotation, f"({locator}) in {', '.join(holders)}"))

		# **In no document that was read is not in no document cited.**  Where one of this
		# definition's sources could not be read, the passage may be in that one, and
		# nothing here names the document it is credited to.  So it is unchecked, exactly as
		# it would be had the locator named the unread source.
		if holders:
			holding.append((quotation, locator, holders))
		elif unread:
			perhaps_unread.append((quotation, locator))
		else:
			nowhere.append((quotation, locator))

	if numbered:
		print(f"    {len(holding)} of {len(numbered)} quotations located by a section or version "
			f"number alone are in a document cited here that has no pages, which is a weaker "
			f"check than naming it" + (":" if holding else ""))

		for quotation, locator, holders in holding:
			print(f"        ({locator}) in {', '.join(holders)}: {quotation[:76]}")

	if perhaps_unread:
		print(f"    {len(perhaps_unread)} more are in no document that could be read, and "
			f"{len(unread)} cited here that have no pages could not be, so they are unchecked:")

		for quotation, locator in perhaps_unread:
			print(f"        ({locator}): {quotation[:88]}")

	if disagreed_whole:
		print(f"    {len(disagreed_whole)} of those located without a page were found only by "
			f"the second extractor, so the document carries the words and pypdf "
			f"{pypdf.__version__} reads it differently:")

		for quotation, in_document in disagreed_whole:
			print(f"        {in_document}: {quotation[:84]}")

	# **Not looked for in a document that has pages is not absent from it.**  This said "in
	# no document cited" of a passage the manual beside it printed, because a number alone
	# is no longer searched for there.  So the pages are asked.  A passage that is on one is
	# not missing: it cites a document that has pages and gives no page, and is counted so.
	paged_after_all: list[tuple[str, str, list[str]]] = []

	for quotation, locator in list(nowhere):
		pages = [f"{document.name} printed p. {number}"
			for document in turnable for number in document.where(readings(quotation))]

		if pages:
			nowhere.remove((quotation, locator))
			paged_after_all.append((quotation, locator, pages))

	if paged_after_all:
		print(f"    {len(paged_after_all)} quotation(s) located by a number alone are on a page "
			f"of a document that has pages, where a number alone is not looked for - cite the "
			f"page:")

		for quotation, locator, pages in paged_after_all:
			print(f"        ({locator}): {quotation[:88]}")
			print(f"            it is on: {', '.join(pages)}")

	for quotation, locator in nowhere:
		print(f"\n      IN NO DOCUMENT CITED{' THAT HAS NO PAGES' if paged else ''}, located "
			f"({locator}): {quotation[:110]}")

		if paged:
			print(f"          a number alone is looked for only where there are no pages, and "
				f"it is on no page of a document held either, as this tool reads it")

	if adapted:
		print(f"    {len(adapted)} of those found were found only with what is in their square "
			f"brackets left out, which is right for a word this file adapted to its sentence "
			f"and a weaker check for a bracket the maker prints:")

		for quotation, place in adapted:
			print(f"        {place}: {quotation[:88]}")

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

	return Tally(
			passed = passed + named_passed + len(holding),
			missing = len(missing) + len(elsewhere_missing) + len(nowhere),
			disagreed = len(disagreed) + len(disagreed_whole),
			unchecked = unchecked + len(named_unread) + len(perhaps_unread),
			partly = len(partly),
			adapted = len(adapted),
			**{**counted, "unpaged": counted["unpaged"] + len(paged_after_all)})


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


def faults (tally: Tally) -> int:

	"""How many things in a tally fail the run, which is every figure a writer can put right.

	A quotation that is not where it says; a locator that cannot be read; a source the
	definition does not have; a document with pages cited without one, and one without
	pages cited by a page; a curly quote mark outside every quotation; marks that are
	paired wrongly, or cannot be paired; a quotation hidden in backticks; and an account
	this tool cannot find.  What could not be checked for want of a document is not among
	them, and neither is any of the weaker checks.
	"""

	return (tally.missing + tally.unreadable + tally.misnamed + tally.unpaged + tally.pageless
		+ tally.curly + tally.mispaired + tally.hidden + tally.unpairable + tally.accountless)


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

	return summarise(wanted, tallies)


def summarise (wanted: typing.Sequence[str], tallies: typing.Sequence[Tally]) -> int:

	"""Print what a run came to, and give the status it ends with: nought only if nothing failed.

	Apart from `main()` so that it can be asked about tallies made up for the purpose: what
	fails a run is decided here, and a figure dropped from this is a fault nobody is told of.
	"""

	total = Tally()
	failed: list[str] = []
	named_in: dict[str, list[str]] = {field: [] for field in Tally._fields}

	for name, tally in zip(wanted, tallies):
		total = Tally(*(running + one for running, one in zip(total, tally)))

		# Any fault names the definition.  A locator nobody can read means a quotation
		# checked against nothing, which is as bad as one checked and wrong - worse, because
		# it looks like neither.
		if faults(tally):
			failed.append(name)

		for field, count in zip(Tally._fields, tally):
			if count:
				named_in[field].append(name)

	print(f"\n{total.passed} quotations check out across {len(wanted)} definition(s); "
		f"{total.missing} are not on the page or in the document they cite; "
		f"{total.unchecked} could not be checked")

	# Its own sentence and its own figure: these are among neither those that check out nor
	# those that are missing, and until #4928 they were in no figure at all.
	print(f"{total.partly} more have every clause on the page they cite, where its text layer "
		f"does not run them together, which is a weaker check and is in none of those three")

	# Said as its own sentence rather than folded into the figures above, because it is a
	# count of quotations nobody had looked at rather than a count of checks that ran.
	print(f"{total.unreadable} quotations across {len(named_in['unreadable'])} definition(s) have "
		f"a locator this tool cannot read, so they are not in any figure above"
		+ (f": {', '.join(named_in['unreadable'])}" if total.unreadable else ""))

	if total.disagreed:
		print(f"{total.disagreed} of those that check out were found only by the second "
			f"extractor, so two readings of one page or document differ - counted as checking "
			f"out, because it does carry the words")

	if total.adapted:
		print(f"{total.adapted} of those that check out were found only with what is in their "
			f"square brackets left out - counted as checking out, and a weaker check where the "
			f"maker prints the brackets: {', '.join(named_in['adapted'])}")

	# **Each of these is a fault of the file's own, said only where there is one**, and each
	# names its definitions.  Those counted under the first four were not looked for; a
	# passage counted as paired wrongly may have been, and found; and the last counts marks.
	for field, said in (
			("misnamed", "quotations name a source their definition does not have"),
			("unpaged", "quotations cite a document that has pages and give no page, so they "
				"were not checked"),
			("pageless", "quotations cite a page where no source it could be in has pages, so "
				"they were not checked"),
			("hidden", "quotations with a locator stand inside backticks, so they were not "
				"checked"),
			("mispaired", "passage(s) begin or end with a space, are empty, or begin by closing "
				"an emphasis before a locator, so the marks around them are probably paired wrongly"),
			("curly", "curly quote mark(s) stand outside every quotation, and only straight "
				"marks are paired")):
		if getattr(total, field):
			print(f"{getattr(total, field)} {said}: {', '.join(named_in[field])}")

	# **THE TWO FIGURES THAT MAKE THE ONE ABOVE RECONCILABLE.**  Until these existed, a hand
	# count of a file's locators could not be squared with what this tool said it checked,
	# and the difference was the whole fault: a figure could not be told from a complete
	# figure.  `korg/minilogue` read "5 of 5" while holding thirty nobody had looked at.
	# Neither fails the run - see `uncovered()` for why a coverage report must not.
	print(f"{total.no_locator} passage(s) of {FLOOR}+ characters are in quotation marks with "
		f"no locator at all, so they are in no figure above"
		+ (f": {', '.join(named_in['no_locator'])}" if total.no_locator else ""))

	print(f"{total.too_short} passage(s) carry a locator and are under {FLOOR} characters, "
		f"which is this tool's floor, so they are in no figure above")

	if total.unpairable:
		print(f"{total.unpairable} definition(s) hold quote marks or backticks that do not "
			f"pair, so nothing in them was checked: {', '.join(named_in['unpairable'])}")

	if total.accountless:
		print(f"{total.accountless} definition(s) write their account as something other than "
			f"a block scalar, so nothing in them was checked: "
			f"{', '.join(named_in['accountless'])}")

	print(f"{total.nothing_to_check} definition(s) quote nothing with a locator")

	if failed:
		print(f"not clean: {', '.join(failed)}")

	return 1 if faults(total) else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv))
