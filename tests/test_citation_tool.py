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

import hashlib
import importlib.util
import pathlib
import typing

import pypdf
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


def followed (tmp_path: pathlib.Path, controls: str, *pages: str, extra: str = "") -> typing.Any:

	"""Follow a definition of these controls into one chart with no pages for each text given.

	The check itself, run on documents written for the test. ``extra`` is more of the
	``sources`` mapping, for a document that is not a chart of text.
	"""

	sources = []

	for position, page in enumerate(pages):
		chart = tmp_path / f"chart{position}.txt"
		chart.write_text(page, encoding = "utf-8")
		digest = hashlib.sha256(chart.read_bytes()).hexdigest()
		sources.append(f"chart{position}: {{sha256: {digest}, paginated: false}}")

	definition = pymidiinstrumentdefs.parse(
		"definition: 1\nmodel: {name: X}\n"
		f"sources: {{{', '.join(sources)}{extra}}}\n"
		f"controls: {{{controls}}}\n",
		source = "x.yaml",
	)

	return tool.follow(definition, "x", tool.library_index(tmp_path))


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


class TestFindingAnNrpnPrintedAsTwoBytesSideBySide:

	"""A maker who prints an NRPN as two hexadecimal bytes prints nothing a definition holds.

	Korg's RADIAS is the case. Its MIDI implementation gives Vocoder Band14 Panpot as
	``04  5D``, which is 4 x 128 + 93 = 605 on the wire, and the pages that print the
	table print neither 605 nor 93. A definition citing those pages was told the number
	was on none of them, and most of its other NRPNs passed only because a 4 or a 5 and
	the other half happened to be printed in decimal somewhere on the pages cited: for
	instance a page number, a controller, or the digits of another row's byte.
	"""

	ROW = "| 04  5D  | Vocoder Band14 Panpot       | *3-8                   |"

	def test_the_two_bytes_of_a_row_name_its_number (self) -> None:
		assert tool.as_a_byte_pair(605, self.ROW)

	def test_a_byte_of_digits_alone_counts_when_it_stands_in_a_pair (self) -> None:
		"""04 60 is 4 x 128 + 96. Alone, a 60 is sixty; beside its other byte it is a byte.

		And it is not read as decimal: 4 x 128 + 60 is 04 3C, which this row does not print.
		"""
		row = "| 04  60  | Vocoder Fc Mod.Source       | *3-4                   |"

		assert tool.as_a_byte_pair(4 * 128 + 96, row)
		assert not tool.as_a_byte_pair(4 * 128 + 60, row)

	def test_one_row_s_pair_is_not_found_for_the_slips_a_reader_of_bytes_makes (self) -> None:
		"""The bytes joined as one number, the halves changed places, another first byte.

		Nor for the rows beside it, on this one row. On the page every row is printed, so
		a number taken from the wrong row is found as readily as the right one.
		"""
		assert not tool.as_a_byte_pair(0x045D, self.ROW)
		assert not tool.as_a_byte_pair(0x5D * 128 + 0x04, self.ROW)
		assert not tool.as_a_byte_pair(5 * 128 + 93, self.ROW)
		assert not tool.as_a_byte_pair(604, self.ROW)
		assert not tool.as_a_byte_pair(606, self.ROW)

		beside = "| 04  5E  | Vocoder Band15 Panpot       | *3-8                   |"

		assert tool.as_a_byte_pair(606, f"{self.ROW}\n{beside}")

	def test_both_bytes_must_be_on_one_line (self) -> None:
		"""Down a column, 04 over 5D is two rows' bytes and not one row's pair."""
		assert not tool.as_a_byte_pair(605, "| 04 |\n| 5D |")
		assert not tool.as_a_byte_pair(605, "04\n5D")

	def test_each_byte_must_stand_as_a_word_of_two_digits_in_capitals (self) -> None:
		for printed in ("104  5D", "04  5DH", "04  5d", "4  5D", "x04 5D", "04 5D7", "045D"):
			assert not tool.as_a_byte_pair(605, printed), printed

		# A year is not two bytes, though 20 and 05 are both in it.
		assert not tool.as_a_byte_pair(0x20 * 128 + 0x05, "(C) 2005 KORG INC")

	def test_nothing_but_spaces_or_tabs_may_stand_between_them (self) -> None:
		"""No other way of setting two bytes down is read, and this says which were tried."""
		for printed in ("04:5D", "04,5D", "04/5D", "04 | 5D", "04h 5Dh", "04H 5DH", "04 - 5D"):
			assert not tool.as_a_byte_pair(605, printed), printed

		assert tool.as_a_byte_pair(605, "04\t5D") and tool.as_a_byte_pair(605, "04 5D")

	def test_a_pair_against_a_stop_a_colon_a_stroke_or_a_hash_is_not_read (self) -> None:
		"""Which is how some decimal numbers that look like a pair are printed, about one in eight.

		A microKORG's table of EQ frequencies prints "1.75        13:", and an AstroLab's
		power rating "3.0A 36.0W". Each of the four is refused on either side of the pair,
		which costs a pair set tight against a label or at the end of a sentence.
		"""
		assert not tool.as_a_byte_pair(0x75 * 128 + 0x13, "3: 1.75        13: 4.25        23: 9.00")
		assert not tool.as_a_byte_pair(0x0A * 128 + 0x36, "3.0A 36.0W Max")

		for printed in ("1.04 5D", "04 5D.5", "#04 5D", "04 5D#", "NRPN:04 5D", "04 5D:", "1/04 5D", "04 5D/2"):
			assert not tool.as_a_byte_pair(605, printed), printed

	def test_a_pair_against_a_bar_a_comma_or_a_hyphen_is_still_read (self) -> None:
		"""A table drawn tight sets a bar against its bytes, and must not be lost for it."""
		for printed in ("|04 5D|", "04 5D, 04 5E", "04 5D-04 5F", "(04 5D)", "MSB/LSB=04 5D", "04 5D~04 5F"):
			assert tool.as_a_byte_pair(605, printed), printed

	def test_two_decimal_numbers_standing_together_are_read_as_bytes (self) -> None:
		"""The price of reading a pair wherever it stands, pinned so that it is known.

		A Digitone's row "Ratio B 16 48 1 75" is two controllers and two decimal halves,
		and 16 beside 48 answers for NRPN 0x16 x 128 + 0x48, which no document prints.
		"""
		assert tool.as_a_byte_pair(0x16 * 128 + 0x48, "Ratio B 16 48 1 75")

	def test_a_number_no_nrpn_can_be_has_no_pair (self) -> None:
		assert not tool.as_a_byte_pair(0xA0 * 128 + 0x5D, "A0 5D")
		assert not tool.as_a_byte_pair(0x4000, "80 00")
		assert not tool.as_a_byte_pair(-1, "-1 7F")

	def test_the_check_calls_it_neither_found_nor_missing (self, tmp_path: pathlib.Path) -> None:
		"""Which is what stopped a definition: a number on its page, reported as on no page."""
		result = followed(tmp_path, "band14_panpot: {nrpn: 605}", self.ROW)

		assert result.as_byte_pairs == [("band14_panpot", "nrpn", 605)]
		assert result.missing == [] and result.as_halves == []
		assert result.sound

	def test_a_pair_is_looked_for_before_two_halves_in_decimal (self, tmp_path: pathlib.Path) -> None:
		"""A 4 and a 93 elsewhere on the page are the weaker evidence, and the pair is on it."""
		result = followed(tmp_path, "band14_panpot: {nrpn: 605}", f"p. 4 of 93\n{self.ROW}")

		assert result.as_byte_pairs == [("band14_panpot", "nrpn", 605)]
		assert result.as_halves == []

	def test_two_halves_in_decimal_are_still_found_where_no_pair_is_printed (self, tmp_path: pathlib.Path) -> None:
		"""A Digitone's row "Mute 94 1 101" prints a 1 and a 101, and is found as it was."""
		result = followed(tmp_path, "mute: {nrpn: 229}", "Mute 94 1 101")

		assert result.as_halves == [("mute", "nrpn", 229)]
		assert result.as_byte_pairs == []

	def test_a_number_the_page_prints_whole_is_simply_found (self, tmp_path: pathlib.Path) -> None:
		"""The weaker rules are tried only for a number that is not on the page as itself."""
		result = followed(tmp_path, "band14_panpot: {nrpn: 605}", f"605 {self.ROW}")

		assert result.as_byte_pairs == [] and result.missing == []

	def test_a_wrong_number_beside_the_right_row_is_missing_where_no_decimal_excuses_it (self, tmp_path: pathlib.Path) -> None:
		"""1117 is 04 5D read as one number, which would be printed 08 5D.

		The row prints no 08 5D, and no 93 for the halves rule to find beside its 8.
		"""
		result = followed(tmp_path, "band14_panpot: {nrpn: 1117}", self.ROW)

		assert result.missing == [("band14_panpot", "nrpn", 1117)]
		assert not result.sound

	def test_the_same_slip_passes_as_halves_where_a_decimal_does_excuse_it (self, tmp_path: pathlib.Path) -> None:
		"""One 93 anywhere on the page, a page number say, and the slip is no longer missing.

		The pair does not refuse a slip; it only does not answer for one. So the slip is
		found as two decimal halves beside a number found as a pair, and the report names
		both, there being one of each.
		"""
		result = followed(
			tmp_path, "band14_panpot: {nrpn: 605}, band14_level: {nrpn: 1117}", f"{self.ROW}\npage 93",
		)

		assert result.as_byte_pairs == [("band14_panpot", "nrpn", 605)]
		assert result.as_halves == [("band14_level", "nrpn", 1117)]
		assert result.sound

	def test_an_nrpn_below_128_is_found_by_its_pair_or_by_its_one_byte (self, tmp_path: pathlib.Path) -> None:
		"""00 4A names both bytes of NRPN 74. A maker who writes "NRPN 4A" prints one."""
		paired = followed(tmp_path, "cutoff: {nrpn: 74}", "| 00  4A  | Cutoff |")

		assert paired.as_byte_pairs == [("cutoff", "nrpn", 74)] and paired.as_hex == []

		alone = followed(tmp_path, "cutoff: {nrpn: 74}", "NRPN 4A Cutoff")

		assert alone.as_hex == [("cutoff", "nrpn", 74)] and alone.as_byte_pairs == []

	def test_a_controller_is_never_read_as_a_pair (self, tmp_path: pathlib.Path) -> None:
		"""Controller 93 is one byte. A 00 beside its 5D is not an address."""
		result = followed(tmp_path, "chorus: {cc: 93}", "| 00  5D  | Chorus |")

		assert result.as_hex == [("chorus", "cc", 93)]
		assert result.as_byte_pairs == []

	def test_a_pair_on_a_page_of_text_is_found_beside_a_scan (self, tmp_path: pathlib.Path) -> None:
		"""A number whose pair is on a readable page was looked for, whatever else is cited.

		Only what is on no readable page is left as not checked, where a scan is cited too.
		"""
		scan = tmp_path / "scan.pdf"
		writer = pypdf.PdfWriter()
		writer.add_blank_page(width = 200, height = 200)
		writer.write(scan)
		digest = hashlib.sha256(scan.read_bytes()).hexdigest()

		result = followed(
			tmp_path, "band14_panpot: {nrpn: 605}, band15_panpot: {nrpn: 606}", self.ROW,
			extra = f", scan: {{sha256: {digest}, page_offset: 0}}",
		)

		assert [document.scanned for document in result.documents] == [False, True]
		assert result.as_byte_pairs == [("band14_panpot", "nrpn", 605)]
		assert result.unverifiable == [("band15_panpot", "nrpn", 606)]

	def test_it_is_reported_as_weaker_and_never_counted_as_found (self, capsys: pytest.CaptureFixture[str]) -> None:
		result = tool.Result(name = "korg/radias", documents = [])
		result.wanted = [("vocoder_band14_panpot", "nrpn", 605)]
		result.as_byte_pairs = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert result.sound
		assert "0 of 1 numbers found" in printed
		assert "1 NRPNs found only as two hexadecimal bytes side by side" in printed

	def test_the_few_found_only_as_decimal_halves_among_pairs_are_named (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""A table of byte pairs was read, so the one found only in decimal is the likelier slip."""
		result = tool.Result(name = "example", documents = [])
		result.wanted = [("a", "nrpn", 604), ("b", "nrpn", 605), ("c", "nrpn", 606), ("d", "nrpn", 1117)]
		result.as_byte_pairs = result.wanted[:3]
		result.as_halves = result.wanted[3:]

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "0 of 4 numbers found" in printed
		assert "the fewer, as halves in decimal, are named" in printed
		assert "d.nrpn = 1117, as 8 and 93 in decimal" in printed
		assert not [name for name in ("a.nrpn", "b.nrpn", "c.nrpn") if name in printed]

	def test_the_few_found_as_pairs_among_decimal_halves_are_named (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""A table of decimal columns was read, so the one pair is the likelier coincidence.

		A Digitone's "Ratio B 16 48 1 75" read as bytes is 2888. Naming the halves there
		would name every right number and leave out the one wrong one.
		"""
		result = tool.Result(name = "example", documents = [])
		result.wanted = [("ratio_b", "nrpn", 2888), ("mute", "nrpn", 229), ("volume", "nrpn", 166)]
		result.as_byte_pairs = result.wanted[:1]
		result.as_halves = result.wanted[1:]

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "the fewer, as bytes side by side, are named" in printed
		assert "ratio_b.nrpn = 2888, as 16 48 side by side" in printed
		assert "mute.nrpn" not in printed and "volume.nrpn" not in printed

	def test_a_named_pair_is_written_as_two_digits_each_in_capitals (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""04 5D, and not 4 5d."""
		result = tool.Result(name = "example", documents = [])
		result.wanted = [("panpot", "nrpn", 605), ("mute", "nrpn", 229), ("volume", "nrpn", 166)]
		result.as_byte_pairs = result.wanted[:1]
		result.as_halves = result.wanted[1:]

		tool.render(result, verbose = False)

		assert "panpot.nrpn = 605, as 04 5D side by side" in capsys.readouterr().out

	def test_every_one_of_the_fewer_is_named_and_not_the_first_alone (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""Two slips among three pairs, and then two coincidences among three halves."""
		result = tool.Result(name = "example", documents = [])
		result.wanted = [("a", "nrpn", 604), ("b", "nrpn", 605), ("c", "nrpn", 606), ("d", "nrpn", 1095), ("e", "nrpn", 8196)]
		result.as_byte_pairs = result.wanted[:3]
		result.as_halves = result.wanted[3:]

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "d.nrpn = 1095, as 8 and 71 in decimal" in printed
		assert "e.nrpn = 8196, as 64 and 4 in decimal" in printed

		result = tool.Result(name = "example", documents = [])
		result.wanted = [("a", "nrpn", 2888), ("b", "nrpn", 3017), ("c", "nrpn", 229), ("d", "nrpn", 166), ("e", "nrpn", 203)]
		result.as_byte_pairs = result.wanted[:2]
		result.as_halves = result.wanted[2:]

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "a.nrpn = 2888, as 16 48 side by side" in printed
		assert "b.nrpn = 3017, as 17 49 side by side" in printed

	def test_as_many_found_each_way_and_all_are_named (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""Neither kind is the fewer, so neither is taken for the right one.

		A Digitone's "Ratio B 16 48 1 75" held as 2888 beside its "Mute 94 1 101" held as
		229: named alone, the halves would name the right number and leave out the wrong.
		"""
		result = tool.Result(name = "example", documents = [])
		result.wanted = [("ratio_b", "nrpn", 2888), ("mute", "nrpn", 229)]
		result.as_byte_pairs = result.wanted[:1]
		result.as_halves = result.wanted[1:]

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "as many each way, so all are named" in printed and "the fewer" not in printed
		assert "ratio_b.nrpn = 2888, as 16 48 side by side" in printed
		assert "mute.nrpn = 229, as 1 and 101 in decimal" in printed

	def test_nothing_is_named_where_every_nrpn_was_found_one_way (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""An Elektron's list is all decimal halves, and naming a hundred of them would say nothing."""
		result = tool.Result(name = "elektron/digitone", documents = [])
		result.wanted = [("mute", "nrpn", 229)]
		result.as_halves = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "1 NRPNs found only as the two halves the maker prints" in printed
		assert "mute.nrpn" not in printed and "both ways" not in printed

		result = tool.Result(name = "korg/radias", documents = [])
		result.wanted = [("vocoder_band14_panpot", "nrpn", 605)]
		result.as_byte_pairs = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "vocoder_band14_panpot.nrpn" not in printed and "both ways" not in printed


class TestTwoDocumentsAreNeverReadAsOne:

	def test_the_end_of_one_and_the_start_of_the_next_do_not_make_a_number (self, tmp_path: pathlib.Path) -> None:
		"""A chart ending "page 6" and a second beginning "05" printed no 605 between them.

		Joined by a space they did, because a gap between digits on one line is closed
		when numbers are read, to mend the ones a PDF's text layer splits apart.
		"""
		result = followed(tmp_path, "band14_panpot: {nrpn: 605}", "see page 6", "05 Bn 4A")

		assert result.missing == [("band14_panpot", "nrpn", 605)]

	def test_nor_a_pair_of_bytes (self, tmp_path: pathlib.Path) -> None:
		result = followed(tmp_path, "band14_panpot: {nrpn: 605}", "Bn 04", "5D vv")

		assert result.as_byte_pairs == []
		assert result.missing == [("band14_panpot", "nrpn", 605)]


class TestADocumentWithNoPageToTurnTo:

	"""A source saying ``paginated: false`` is read whole, whatever it is made of.

	This was wrong in a way nothing reported: the choice was made from the file's
	extension, so a PDF whose maker left its pages unnumbered had **no** text read from
	it, and the tool still listed it as a document it had followed. The Minitaur's v2.1
	addendum is the real case - two unnumbered pages bound into the back of a manual
	whose other pages are all numbered.
	"""

	def test_an_unnumbered_pdf_is_read_rather_than_skipped (self, tmp_path: pathlib.Path) -> None:
		"""Its pages are extracted and joined, where reading its bytes would give nothing."""
		made = tmp_path / "unnumbered.pdf"
		writer = pypdf.PdfWriter()
		writer.add_blank_page(width = 200, height = 200)
		writer.write(made)

		text = tool.whole_text(made)

		# A blank page extracts to an empty string rather than raising, which is the
		# thing that matters: the PDF was opened as a PDF.
		assert text == ""

	def test_a_text_document_is_read_as_text (self, tmp_path: pathlib.Path) -> None:
		"""The other half of the same decision, which was never broken and is pinned here."""
		made = tmp_path / "chart.txt"
		made.write_text("CC 74 Filter Cutoff\n", encoding = "utf-8")

		assert "Filter Cutoff" in tool.whole_text(made)

	def test_the_bytes_of_a_pdf_are_never_read_as_text (self, tmp_path: pathlib.Path) -> None:
		"""Which is what used to happen, and yielded a page of binary with no words in it."""
		made = tmp_path / "unnumbered.pdf"
		writer = pypdf.PdfWriter()
		writer.add_blank_page(width = 200, height = 200)
		writer.write(made)

		assert "%PDF" not in tool.whole_text(made)


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

	def test_a_fine_half_given_by_a_rule_is_found_inside_the_range_the_rule_prints (self, tmp_path: pathlib.Path) -> None:
		"""Moog's Theremini gives every controller below 32 a fine control "at locations 32 - 63".

		It prints no fine half's own number, so a definition that holds one for controller 9
		asks for a 41 that no row carries, and the page has named it in the only way a rule can.
		"""
		page = ("7 Master Volume\n9 Wavetable Scan Rate\n"
			"All implemented controller numbers 0 - 31 have corresponding LSB (fine) controls at locations 32 - 63.")
		result = followed(tmp_path, "scan_rate: {cc: 9, lsb: 41}", page)

		assert result.in_a_range == [("scan_rate", "lsb", 41)]
		assert not result.missing

	def test_a_fine_half_inside_no_printed_range_is_still_missing (self, tmp_path: pathlib.Path) -> None:
		"""The rule is what names it. A table that prints the coarse number alone has not."""
		result = followed(tmp_path, "scan_rate: {cc: 9, lsb: 41}", "7 Master Volume\n9 Wavetable Scan Rate")

		assert result.missing == [("scan_rate", "lsb", 41)]
		assert not result.in_a_range

	def test_it_is_reported_as_weaker_and_never_counted_as_found (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""The whole point: a page that names a range has not printed the number."""
		result = tool.Result(name = "korg/wavestate", documents = [])
		result.wanted = [("layer_a_mod_4", "cc", 83)]
		result.in_a_range = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "0 of 1 numbers found" in printed
		assert "1 controller numbers found only inside a range the maker prints" in printed


class TestFindingANumberPrintedOnlyInHexadecimal:

	def test_a_byte_with_a_letter_names_its_number (self) -> None:
		"""Behringer's TD-3-MO prints its one controller as "Bn 4A xx" and never prints 74."""
		assert tool.in_hexadecimal(74, "Bn 4A xx \u2014 Filter Cutoff")

	def test_a_form_of_digits_alone_is_never_read_as_hexadecimal (self) -> None:
		"""A page that prints 40 is far likelier to mean forty than 64."""
		assert not tool.in_hexadecimal(64, "Bn 40 xx")
		assert not tool.in_hexadecimal(16, "Bn 10 xx")

	def test_it_must_stand_as_a_word_of_its_own (self) -> None:
		"""Part of a longer word is not the byte, whatever letters surround it."""
		for printed in ("B4A", "4A7", "4AH", "0x4A", "x4Ay"):
			assert not tool.in_hexadecimal(74, printed), printed

	def test_it_must_be_printed_in_capitals (self) -> None:
		"""Makers print bytes in capitals, and "4a" in running text is far likelier a label."""
		assert not tool.in_hexadecimal(74, "Bn 4a xx")

	def test_a_number_wider_than_a_byte_has_no_two_digit_form (self) -> None:
		"""An NRPN of 300 would be 12C, which this rule does not read."""
		assert not tool.in_hexadecimal(300, "12C 2C")

	def test_it_is_reported_as_weaker_and_never_counted_as_found (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""A page that prints a byte has not printed the number in the base the definition holds."""
		result = tool.Result(name = "behringer/td_3_mo", documents = [])
		result.wanted = [("filter_cutoff", "cc", 74)]
		result.as_hex = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert result.sound
		assert "0 of 1 numbers found" in printed
		assert "1 numbers found only as the hexadecimal byte the maker prints" in printed

	def test_each_number_found_this_way_is_named_with_its_form (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""Prose prints short hexadecimal words too: a Nymphes manual's adapter rated at 1A reads as 26.

		So a count is not enough. Each is named, so a person can turn to the page and see
		whether the byte is a message or an ampere.
		"""
		result = tool.Result(name = "example", documents = [])
		result.wanted = [("filter_cutoff", "cc", 74), ("lfo_2_delay", "cc", 26)]
		result.as_hex = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "filter_cutoff.cc = 74, printed as 4A" in printed
		assert "lfo_2_delay.cc = 26, printed as 1A" in printed


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


class TestAPageThatPublishesItsNumbersOnlyInAPicture:

	"""A declared pictured page excuses a number the text cannot carry, and is checked.

	The Arturia DrumBrute Impact is the case: 107 pages of ordinary text in which the
	one page giving the drum map gives it as a screenshot of the maker's editor. This
	is deliberately a declaration in the file rather than something inferred from a
	page having an image on it - most pages of most manuals do, so inferring it would
	excuse an invented number nearly everywhere.
	"""

	def document (self, declared: str, pictured: list[int], unpictured: list[int]) -> typing.Any:
		"""One cited document, found in the library, with a declaration already checked."""
		source = pymidiinstrumentdefs.parse(
			f"definition: 1\nmodel: {{name: X}}\nsources: {{m: {{page_offset: 5, {declared}}}}}",
			source = "x.yaml",
		).sources["m"]

		return tool.Followed(
			key = "m", source = source, path = pathlib.Path("m.pdf"), extent = 107,
			pictured = pictured, unpictured = unpictured,
		)

	def test_the_declaration_is_read_and_sorted (self) -> None:
		"""Two files declaring the same pages in different orders declare the same thing."""
		source = pymidiinstrumentdefs.parse(
			"definition: 1\nmodel: {name: X}\n"
			"sources: {m: {page_offset: 0, pictured_pages: [99, 12]}}",
			source = "x.yaml",
		).sources["m"]

		assert source.pictured_pages == (12, 99)

	def test_a_number_nobody_could_look_for_is_not_called_missing (self) -> None:
		""""Not on the page you cited" accuses the definition; this does not."""
		result = tool.Result(name = "arturia/drumbrute_impact",
			documents = [self.document("pictured_pages: [99]", [99], [])])
		result.unverifiable = [("kick", "note", 36)]

		assert result.missing == []
		assert result.sound is True

	def test_a_declaration_about_a_page_with_no_image_is_a_fault (self) -> None:
		"""The half of the claim a machine can check, and it must not pass quietly.

		Nothing here can tell whether a number is inside a picture. It can tell that a
		page said to hold one holds none, which catches a mistyped page number and a
		declaration left behind after a maker revised the document.
		"""
		result = tool.Result(name = "arturia/drumbrute_impact",
			documents = [self.document("pictured_pages: [99]", [99], [99])])

		assert result.misdeclared == [("m", 99)]
		assert result.sound is False

	def test_the_reason_it_could_not_be_checked_names_the_picture (self, capsys: typing.Any) -> None:
		"""A scan and a pictured page are different facts and must read differently."""
		result = tool.Result(name = "arturia/drumbrute_impact",
			documents = [self.document("pictured_pages: [99]", [99], [])])
		result.wanted = [("kick", "note", 36)]
		result.unverifiable = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "declares printed 99 as carrying their numbers only in a picture" in printed
		assert "1 NOT CHECKED AT ALL: a cited page publishes its numbers only in a picture" \
			in printed

		# And the count above those lines must not read like a pass.
		assert "0 of 1 numbers found" in printed

	def test_a_misdeclaration_is_shouted_rather_than_mentioned (self, capsys: typing.Any) -> None:
		"""It is the thing that would otherwise make the whole declaration worthless."""
		result = tool.Result(name = "arturia/drumbrute_impact",
			documents = [self.document("pictured_pages: [99]", [99], [99])])

		tool.render(result, verbose = False)

		assert "DECLARES printed 99 as pictured AND IT CARRIES NO IMAGE" in capsys.readouterr().out
