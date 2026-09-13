"""The parts of ``tools/check_citations.py`` that can be checked without a manual.

The check itself is deliberately not a test.  It reads manufacturers' documents,
which are copyrighted and are never committed here, so in CI it could only ever
skip — and a skip nobody reads is a green tick certifying nothing.

What is tested here needs no document at all: reading page numbers out of a
source line, and reading numbers out of a page of extracted text.  Both are
worth testing because both have been silently wrong.  An early version of the
parser read *no* pages from ``(p. 1)`` and quietly dropped ``51-52`` from a list
that ended in "and", and it reported success either way.
"""

import importlib.util
import pathlib
import typing

import pytest

import pymidiinstrumentdefs


def load_tool () -> typing.Any:

	"""Load the checker, which is a script beside the package rather than in it."""

	path = pathlib.Path(__file__).resolve().parent.parent / "tools" / "check_citations.py"
	spec = importlib.util.spec_from_file_location("check_citations", path)

	assert spec is not None and spec.loader is not None, f"{path} is not importable"

	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)

	return module


tool = load_tool()


class TestReadingACitation:

	def test_a_page_in_brackets_is_still_a_page (self) -> None:
		"""The TR-8S cites its only page as "(p. 1)", which one parser read as none.

		A citation that yields nothing at all looks exactly like a definition that
		cites nothing, so the fault is invisible in the result.
		"""
		assert tool.cited_pages("a single page (p. 1), and every row of it is below") == {1}

	def test_a_list_is_not_cut_short_by_the_word_and (self) -> None:
		"""The Carbon8M's last cited page and the Vermona's last two follow an "and"."""
		assert tool.cited_pages("at pp. 26-27, 30, 32-33, 40 and 50.") == {26, 27, 30, 32, 33, 40, 50}
		assert tool.cited_pages("User manual pp. 19-20 and 23-24.") == {19, 20, 23, 24}

	def test_a_range_covers_every_page_between_its_ends (self) -> None:
		assert tool.cited_pages("the tables at pp. 10-13") == {10, 11, 12, 13}

	def test_a_comma_and_then_prose_ends_the_list (self) -> None:
		"""The Matriarch's list ends ", and the MMA v2 chart at pp. 70-74"."""
		found = tool.cited_pages("pp. 5, 9-10, 54, 57-59, and the MMA v2 chart at pp. 70-74.")

		assert found == {5, 9, 10, 54, 57, 58, 59, 70, 71, 72, 73, 74}

	def test_a_count_of_pages_is_not_a_page_number (self) -> None:
		"""Documents state their own extent, and the Matriarch's says "(88pp)"."""
		assert tool.cited_pages("User manual (88pp), pp. 5, 9-10") == {5, 9, 10}
		assert tool.cited_pages("MIDI Implementation V2, 17 pages: settings at p. 1") == {1}

	def test_a_source_line_citing_nothing_yields_nothing (self) -> None:
		"""The DFAM's manual is searched entire, so it names no page, and that is honest."""
		assert tool.cited_pages("User manual, 44 pages, in which MIDI does not appear") == set()

	def test_every_bundled_citation_still_parses (self) -> None:
		"""Every definition that cites pages must still be seen to cite them.

		This is the shape of the original fault: the parser went on working for
		most files while reading none at all from one of them.
		"""
		silent = [
			name for name in pymidiinstrumentdefs.available()
			if "p. " in (pymidiinstrumentdefs.load(name).source or "")
			and not tool.cited_pages(pymidiinstrumentdefs.load(name).source or "")
		]

		assert silent == []


class TestReadingNumbersOffAPage:

	def test_digits_a_pdf_split_apart_are_still_found (self) -> None:
		"""One manual's table renders "35 (LSB)" as "3 5(LSB)".

		Reading that page plainly loses 13 of the definition's 55 numbers.
		"""
		assert 35 in tool.numbers_on("3(MSB)\n3 5(LSB)\n0-127")

	def test_closing_gaps_does_not_lose_numbers_that_were_already_apart (self) -> None:
		"""Where a value range abuts the next row's number, "0-127 72" fuses to "12772".

		Closing the gaps is therefore not a substitute for reading the page
		plainly, and combining the two readings is what keeps both numbers.
		"""
		found = tool.numbers_on("70 String Registration 0-127 72 Solo Tone 0-127")

		assert {70, 72, 127} <= found

	def test_digits_are_never_joined_across_a_line_break (self) -> None:
		"""Joining down a column would invent a number the page never printed."""
		assert 12 not in tool.numbers_on("1\n2")


class TestWritingPagesBack:

	def test_a_run_of_pages_prints_as_a_range (self) -> None:
		assert tool.as_ranges([21, 22, 23, 24]) == "21-24"

	def test_gaps_are_kept_apart (self) -> None:
		assert tool.as_ranges([5, 9, 10, 30]) == "5, 9-10, 30"

	def test_nothing_says_so (self) -> None:
		assert tool.as_ranges([]) == "none"


class TestFollowingAPageIntoAFile:

	def make (self, body: str) -> typing.Any:
		"""One cited document, with the geometry a definition would record."""
		source = pymidiinstrumentdefs.parse(
			f"definition: 1\nmodel: {{name: X}}\nsources: {{m: {{{body}}}}}",
			source = "x.yaml",
		).sources["m"]

		return tool.Followed(key = "m", source = source, path = pathlib.Path("m.pdf"), extent = 19)

	def test_a_two_up_manual_reaches_a_page_a_naive_reading_would_call_missing (self) -> None:
		"""The Minitaur cites pp. 21-24 of a file with 19 pages, printing two to a sheet."""
		document = self.make("page_offset: 2, pages_per_sheet: 2")

		assert [document.covers(printed) for printed in (21, 24)] == [True, True]

	def test_a_page_past_the_end_is_not_covered (self) -> None:
		document = self.make("page_offset: 0")

		assert document.covers(20) is False

	def test_a_document_that_is_not_in_the_library_covers_nothing (self) -> None:
		"""Nothing can be checked against a file nobody has, and that is its own fault."""
		document = self.make("page_offset: 0")
		document.path = None

		assert document.covers(1) is False
