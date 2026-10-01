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


class TestFindingAnNrpnThatIsPrintedAsTwoHalves:

	def test_the_sum_is_found_when_the_page_prints_the_halves (self) -> None:
		"""A Digitone's NRPN 1/101 is 229 on the wire, and the page prints a 1 and a 101.

		A definition holds the one number that is addressed; the maker prints the two
		columns it is built from. Neither is wrong, so the check has to know both.
		"""
		assert tool.halves_on(229, {1, 101, 94}) is True

	def test_a_missing_half_is_not_found (self) -> None:
		assert tool.halves_on(229, {1, 100}) is False
		assert tool.halves_on(229, {101}) is False

	def test_an_nrpn_in_the_first_bank_needs_a_zero_msb_on_the_page (self) -> None:
		"""A Take 5 prints its NRPNs whole, so this path is not what finds them."""
		assert tool.halves_on(36, {0, 36}) is True
		assert tool.halves_on(36, {36}) is False


class TestFindingANumberThatIsOnlyInsideAPrintedRange:

	def test_a_short_range_names_the_numbers_inside_it (self) -> None:
		"""Korg's wavestate prints "80...87" for eight knobs and never prints 81 to 86."""
		page = "Layer A Mod Knobs 1...8 80...87"

		assert tool.inside_a_range(83, page)
		assert tool.inside_a_range(86, page)

	def test_an_endpoint_is_not_this_rule_s_business (self) -> None:
		"""It is on the page as itself, and is found by looking for it."""
		assert not tool.inside_a_range(80, "80...87")
		assert not tool.inside_a_range(87, "80...87")

	def test_a_wide_range_names_nothing (self) -> None:
		"""A note row reading 0-127 would otherwise answer for every controller in the file."""
		assert not tool.inside_a_range(74, "Note Number 0-127 0-127")
		assert not tool.inside_a_range(99, "0 - 127")

	def test_the_dashes_a_maker_actually_uses (self) -> None:
		"""One Korg page prints an ellipsis, a hyphen and an en dash on the same sheet."""
		for printed in ("102...109", "102-109", "102\u2013109", "102 \u2026 109"):
			assert tool.inside_a_range(105, printed), printed

	def test_it_is_reported_as_weaker_and_never_counted_as_found (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""The whole point: a page that names a range has not printed the number."""
		result = tool.Result(name = "korg/wavestate", documents = [])
		result.wanted = [("layer_a_mod_4", "cc", 83)]
		result.in_a_range = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "0 of 1 numbers found" in printed
		assert "1 controller numbers found only inside a range the maker prints" in printed


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

	def test_a_page_citation_is_still_checked_beside_a_document_with_no_pages (self) -> None:
		"""Citing a plain-text chart or a saved web page must not excuse the manual's pages.

		An earlier version stopped reporting unreachable pages for a whole
		definition the moment any of its sources had no pages.  A Korg minilogue xd
		pairs a PDF manual with a plain-text MIDI implementation, which is exactly
		the shape that would have hidden a wrong citation.
		"""
		manual = self.make("page_offset: 0")
		chart = self.make("paginated: false")
		chart.extent = None

		assert tool.unreachable_pages({5, 400}, [manual, chart]) == {400}

	def test_a_page_of_a_document_with_no_pages_is_unreachable (self) -> None:
		"""A document with no pages has no page 5, so citing one is a fault to report."""
		chart = self.make("paginated: false")
		chart.extent = None

		assert tool.unreachable_pages({5}, [chart]) == {5}

	def test_a_document_that_is_not_in_the_library_covers_nothing (self) -> None:
		"""Nothing can be checked against a file nobody has, and that is its own fault."""
		document = self.make("page_offset: 0")
		document.path = None

		assert document.covers(1) is False


class TestACitedDocumentThatIsAScan:

	"""A scan has pages and no text, so it answers one question and not the other.

	The Yamaha DX7's manual is the case: its controller numbers are printed only in
	an appendix that Yamaha's own text edition leaves out, and the scan it does
	publish has no text layer at all - 0 characters on every one of its 34 pages.
	Reported as ordinary misses, that definition would look like 23 wrong citations.
	"""

	def document (self, scanned: bool) -> typing.Any:
		"""One cited document, found in the library, readable or not."""
		source = pymidiinstrumentdefs.parse(
			"definition: 1\nmodel: {name: X}\nsources: {m: {page_offset: 0}}",
			source = "x.yaml",
		).sources["m"]

		return tool.Followed(
			key = "m", source = source, path = pathlib.Path("m.pdf"), extent = 34, scanned = scanned,
		)

	def test_a_scan_still_answers_whether_it_has_the_page (self) -> None:
		"""Turning to a cited page is checkable even when reading it is not."""
		scan = self.document(scanned = True)

		assert tool.unreachable_pages({30, 32}, [scan]) == set()
		assert tool.unreachable_pages({35}, [scan]) == {35}

	def test_numbers_nobody_could_look_for_are_not_called_missing (self) -> None:
		""""Not on the page you cited" accuses the definition; this does not."""
		result = tool.Result(name = "yamaha/dx7", documents = [self.document(scanned = True)])
		result.unverifiable = [("volume", "cc", 7)]

		assert result.missing == []
		assert result.sound is True

	def test_what_could_not_be_checked_is_said_out_loud (self, capsys: typing.Any) -> None:
		"""A pass that checked nothing must not read like a pass that checked everything."""
		result = tool.Result(name = "yamaha/dx7", documents = [self.document(scanned = True)])
		result.wanted = [("volume", "cc", 7)]
		result.unverifiable = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "a scan: it has pages, but no text in them to search" in printed
		assert "1 NOT CHECKED AT ALL" in printed

		# The count above those lines is the one a reader takes in first, and it said
		# "1 of 1 numbers found" until this test was written: a number nobody could look
		# for had been counted as a number found on the page.
		assert "0 of 1 numbers found" in printed
		assert "1 of 1 numbers found" not in printed
