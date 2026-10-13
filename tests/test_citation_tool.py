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


def followed (tmp_path: pathlib.Path, controls: str, *pages: str, extra: str = "", account: str = "") -> typing.Any:

	"""Follow a definition of these controls into one chart with no pages for each text given.

	The check itself, run on documents written for the test. ``extra`` is more of the
	``sources`` mapping, for a document that is not a chart of text, and ``account`` is the
	definition's source account, for a test that needs a page of such a document cited.
	"""

	sources = []

	for position, page in enumerate(pages):
		chart = tmp_path / f"chart{position}.txt"
		chart.write_text(page, encoding = "utf-8")
		digest = hashlib.sha256(chart.read_bytes()).hexdigest()
		sources.append(f"chart{position}: {{sha256: {digest}, paginated: false}}")

	said = f"source: >-\n  {account}\n" if account else ""

	definition = pymidiinstrumentdefs.parse(
		"definition: 1\nmodel: {name: X}\n"
		f"{said}"
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
		assert 35 in tool.numbers_closed_up("3(MSB)\n3 5(LSB)\n0-127")
		assert 35 not in tool.numbers_as_printed("3(MSB)\n3 5(LSB)\n0-127")

	def test_closing_gaps_does_not_lose_numbers_that_were_already_apart (self) -> None:
		"""Where a value range abuts the next row's number, "0-127 72" fuses to "12772".

		Closing the gaps is therefore not a substitute for reading the page
		plainly, which is the reading that keeps both numbers.
		"""
		page = "70 String Registration 0-127 72 Solo Tone 0-127"

		assert {70, 72, 127} <= tool.numbers_as_printed(page)
		assert 12772 in tool.numbers_closed_up(page) and 72 not in tool.numbers_closed_up(page)

	def test_digits_are_never_joined_across_a_line_break (self) -> None:
		"""Joining down a column would invent a number the page never printed."""
		assert 12 not in tool.numbers_closed_up("1\n2")

	def test_the_digits_of_a_marked_hexadecimal_form_are_not_a_decimal_number (self) -> None:
		"""`0x21` is 33.  Its 21 was found whole, for a definition that held twenty-one."""
		page = "MIDI CC 0x01 (MSB) & MIDI CC 0x21 (LSB), 5 0x10 7"

		assert tool.numbers_as_printed(page) == {5, 7}
		assert tool.numbers_closed_up(page) == {5, 7}, "nor are 5 and 7 joined across it"


class TestDigitsWithAGapBetweenThem:

	"""Closing a gap between digits is a reading of its own, and the weakest but one.

	It was read together with the numbers as printed, so `5: 0.5      21: 2.1` was a found
	521.  Nine of the RADIAS's NRPNs were counted as found on pages that print each as two
	bytes and none of them whole, and the bytes were never looked at.
	"""

	PAGE = "5: 0.5      21: 2.1\n"

	def test_the_two_readings_are_apart (self) -> None:
		"""The number made by closing the gap is in one reading and not in the other."""
		assert 521 not in tool.numbers_as_printed(self.PAGE)
		assert 521 in tool.numbers_closed_up(self.PAGE)
		assert {5, 21} <= tool.numbers_as_printed(self.PAGE)

	def test_a_number_made_by_closing_a_gap_is_not_found (self, tmp_path: pathlib.Path) -> None:
		"""It is not missing either: it is the weaker result, and the definition stands."""
		result = followed(tmp_path, "patch: {nrpn: 521}", self.PAGE)

		assert result.across_a_gap == [("patch", "nrpn", 521)]
		assert not result.missing and result.sound

	def test_the_bytes_on_the_page_are_looked_at_first (self, tmp_path: pathlib.Path) -> None:
		"""521 is 04 09, and that is what the page prints."""
		result = followed(tmp_path, "patch: {nrpn: 521}", self.PAGE + "04  09   Patch2 Destination\n")

		assert result.as_byte_pairs == [("patch", "nrpn", 521)]
		assert not result.across_a_gap

	def test_a_number_a_text_layer_split_is_still_not_missing (self, tmp_path: pathlib.Path) -> None:
		"""Which is what closing the gaps was for: `3 5(LSB)` is a 35 the page does print."""
		result = followed(tmp_path, "wheel: {cc: 3, lsb: 35}", "3 (MSB) 3 5(LSB) Mod Wheel\n")

		assert result.across_a_gap == [("wheel", "lsb", 35)]
		assert not result.missing

	def test_it_is_reported_as_weaker_and_each_is_named (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Counted apart from the numbers found, with each one named to be read on its page."""
		result = followed(tmp_path, "patch: {nrpn: 521}", self.PAGE)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "0 of 1 numbers found" in printed
		assert "1 numbers found only by closing a gap the page leaves between digits" in printed
		assert "patch.nrpn = 521" in printed

	def test_a_half_made_by_closing_a_gap_is_no_half (self, tmp_path: pathlib.Path) -> None:
		"""`Level 1 | 10 1` holds no 101, and 229 is 1 and 101."""
		result = followed(tmp_path, "mute: {nrpn: 229}", "Level 1 | 10 1\n")

		assert not result.as_halves
		assert result.missing == [("mute", "nrpn", 229)]

	def test_an_nrpn_a_text_layer_split_is_across_a_gap_and_not_two_halves (
			self, tmp_path: pathlib.Path) -> None:
		"""35 is 0 and 35, and the 0 of `0-127` with a 35 made of `3 5` was "the two halves"."""
		result = followed(tmp_path, "cutoff: {nrpn: 35}", "0-127\nCutoff 3 5\n")

		assert not result.as_halves
		assert result.across_a_gap == [("cutoff", "nrpn", 35)]

	def test_a_range_is_tried_before_a_gap_and_both_are_said (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The Minitaur's `5 3(LSB)` beside a table of clock divisions that prints `49-54`."""
		result = followed(tmp_path, "resonance: {cc: 21, lsb: 53}",
			"21 (MSB)\n5 3(LSB)\nDotted 1/4 Note Triplet    1/4 DOT    49-54\n")

		assert result.in_a_range == [("resonance", "lsb", 53)]
		assert result.also_across_a_gap == [("resonance", "lsb", 53)]
		assert not result.across_a_gap

		tool.render(result, verbose = False)

		assert "inside 49-54: resonance.lsb = 53 (and by closing a gap between digits)" in capsys.readouterr().out

	def test_a_gap_is_tried_before_what_excuses_a_number_and_before_hexadecimal (
			self, tmp_path: pathlib.Path) -> None:
		"""`4 A` is no byte, and the `7 4` on the page is found before any byte is looked for."""
		result = followed(tmp_path, "cutoff: {cc: 74}", "Bn 4A xx\nRG7 4SA\n")

		assert result.across_a_gap == [("cutoff", "cc", 74)]
		assert not result.as_hex


class TestAPairOfBytesBesideItsLabel:

	"""The one check of a row: a pair of bytes on the line that carries its control's label.

	A pair is matched wherever it stands and every row of a table is on the page, so a
	number taken from the row above is found as readily as the right one, and a slip made
	on every row passes entire.  On the RADIAS's pages 108 of 108 pairs are beside their
	labels, and with every number moved down a row, none.
	"""

	TABLE = (
		"04  5C   Vocoder Band13 Panpot   0~127\n"
		"04  5D   Vocoder Band14 Panpot   0~127\n"
		"00  14   Arp Octaves             0~3\n")

	def test_a_pair_on_its_label_s_line (self) -> None:
		"""The row as the table prints it."""
		assert tool.beside_its_label(605, "Vocoder Band14 Panpot", self.TABLE)

	def test_spacing_case_and_punctuation_do_not_matter (self) -> None:
		"""A text layer may set any of them differently from the definition's label."""
		assert tool.beside_its_label(605, "vocoder band 14: pan-pot", self.TABLE)

	def test_another_row_s_label_is_not_beside_it (self) -> None:
		"""Which is the whole use of it: the row above is on the page too."""
		assert not tool.beside_its_label(605, "Vocoder Band13 Panpot", self.TABLE)
		assert not tool.beside_its_label(604, "Vocoder Band14 Panpot", self.TABLE)

	def test_a_label_on_another_line_is_not_beside_it (self) -> None:
		"""A row is one line, so a label wrapped onto the next is not seen."""
		assert not tool.beside_its_label(605, "Vocoder Band14 Panpot", "Vocoder Band14 Panpot\n04  5D\n")

	def test_no_label_is_beside_nothing (self) -> None:
		"""For a caller that has none: a loaded control has its own key where it gives no label."""
		assert not tool.beside_its_label(605, None, self.TABLE)
		assert not tool.beside_its_label(605, " - ", self.TABLE)

	def test_a_label_is_not_found_inside_another_word_or_in_the_pair (self) -> None:
		"""Each of these was beside the row, as a run of letters somewhere on its line."""
		for label in ("A", "D", "5D", "Pan", "Band1", "ocoder"):
			assert not tool.beside_its_label(605, label, self.TABLE), label

	def test_a_label_with_no_letter_is_beside_nothing (self) -> None:
		"""The row's own range of values would answer for it."""
		for label in ("4", "0", "127", "0~127"):
			assert not tool.beside_its_label(605, label, self.TABLE), label

	def test_a_word_of_the_row_is_beside_it (self) -> None:
		"""Part of the table's words, standing as a word: a weaker label, and still the row's."""
		assert tool.beside_its_label(605, "Vocoder", self.TABLE)
		assert tool.beside_its_label(605, "Band14 Panpot", self.TABLE)

	def test_a_control_with_no_label_is_compared_by_its_key (self, tmp_path: pathlib.Path) -> None:
		"""The loader stands the key in for a label, and `arp_octaves` is the row's words."""
		result = followed(tmp_path, "arp_octaves: {nrpn: 20}", self.TABLE)

		assert result.beside_label == [("arp_octaves", "nrpn", 20)]

	def test_each_row_s_own_number_is_beside_its_label (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Both counted, and nothing named, where each number is its own row's."""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 604}, band14: {label: Vocoder Band14 Panpot, nrpn: 605}",
			self.TABLE)

		assert result.beside_label == [("band13", "nrpn", 604), ("band14", "nrpn", 605)]

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert ("2 of 2 NRPNs whose two bytes stand side by side on a cited page stand so on a line that"
			" also carries their control's label") in printed
		assert "not beside its label" not in printed

	def test_a_slip_on_every_row_passes_as_pairs_and_is_beside_no_label (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Each control holds the other row's number: both pairs are on the page."""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 605}, band14: {label: Vocoder Band14 Panpot, nrpn: 604}",
			self.TABLE)

		assert len(result.as_byte_pairs) == 2 and not result.missing
		assert result.beside_label == []

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert ("0 of 2 NRPNs whose two bytes stand side by side on a cited page stand so on a line that"
			" also carries their control's label") in printed
		assert "not beside its label" not in printed, "none is named until most are beside theirs"

	def test_a_byte_of_the_first_bank_read_as_decimal_is_named (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""`00 14` is NRPN 20.  Held as 14, it is found as itself, because the page prints a 14."""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 604}, band14: {label: Vocoder Band14 Panpot, nrpn: 605},"
			" octaves: {label: Arp Octaves, nrpn: 14}",
			self.TABLE)

		assert not result.missing and ("octaves", "nrpn", 14) not in result.as_byte_pairs
		assert len(result.beside_label) == 2

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		# Its own pair, `00 0E`, is nowhere, so it is not one of the two the count is of.
		assert result.paired == [("band13", "nrpn", 604), ("band14", "nrpn", 605)]
		assert "2 of 2 NRPNs whose two bytes stand side by side" in printed
		assert "not beside its label: octaves.nrpn = 14, which would be 00 0E, and is printed whole" in printed

	def test_a_second_table_printed_in_decimal_does_not_dilute_the_count (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Measured over every NRPN this was 2 of 6, nobody was named, and the slip went unsaid."""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 604}, band14: {label: Vocoder Band14 Panpot, nrpn: 605},"
			" octaves: {label: Arp Octaves, nrpn: 14},"
			" mute: {label: Mute, nrpn: 229}, volume: {label: Volume, nrpn: 166}, pan: {label: Pan, nrpn: 203}",
			self.TABLE + "Mute 94 1 101\nVolume 95 1 38\nPan 96 1 75\n")

		assert len(result.as_halves) == 3 and len(result.paired) == 2

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "2 of 2 NRPNs whose two bytes stand side by side" in printed
		assert "not beside its label: octaves.nrpn = 14" in printed

		# Those found as decimal halves have lines of their own above, and are not named here.
		assert "not beside its label: mute" not in printed

	def test_one_pair_beside_its_label_names_nobody (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""One NRPN in a hundred has its pair on a row that carries its label by coincidence."""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 604}, octaves: {label: Arp Octaves, nrpn: 14}",
			"04  5C   Vocoder Band13 Panpot   0~127\n00  14   Arp Octaves   0~3\n")

		assert result.beside_label == [("band13", "nrpn", 604)]

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		# The 14 is below 128 and printed whole, which is what would be named were one pair enough.
		assert "1 of 1 NRPNs whose two bytes stand side by side" in printed
		assert "not beside its label" not in printed

	def test_half_beside_their_labels_is_not_most (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Two of four: the other two hold numbers whose pairs are other rows'."""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 604}, octaves: {label: Arp Octaves, nrpn: 20},"
			" alpha: {label: Alpha, nrpn: 605}, beta: {label: Beta, nrpn: 604}",
			self.TABLE)

		assert (len(result.paired), len(result.beside_label)) == (4, 2)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "2 of 4 NRPNs whose two bytes stand side by side" in printed
		assert "not beside its label" not in printed

	def test_only_an_nrpn_is_asked_whether_it_stands_beside_its_label (self, tmp_path: pathlib.Path) -> None:
		"""A controller's number is one byte, and `00 05` beside its label is nobody's pair."""
		result = followed(tmp_path, "pan: {label: Vocoder Band14 Panpot, cc: 5}", "00  05   Vocoder Band14 Panpot\n")

		assert (result.paired, result.beside_label) == ([], [])

	def test_one_not_printed_whole_is_named_without_saying_it_is (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""`04 5C` is on the page for both controls, and one of them holds the other's number."""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 604}, band14: {label: Vocoder Band14 Panpot, nrpn: 605},"
			" octaves: {label: Arp Octaves, nrpn: 20}, level: {label: Level, nrpn: 604}",
			self.TABLE)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "3 of 4 NRPNs whose two bytes stand side by side" in printed
		assert "not beside its label: level.nrpn = 604, which would be 04 5C\n" in printed

	def test_the_line_is_said_where_most_are_beside_a_label_though_none_rests_on_its_pair (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Every number is printed whole as well, so nothing was found only as a pair."""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 604}, band14: {label: Vocoder Band14 Panpot, nrpn: 605}",
			self.TABLE + "604 605\n")

		assert not result.as_byte_pairs and len(result.beside_label) == 2

		tool.render(result, verbose = False)

		assert "2 of 2 NRPNs whose two bytes stand side by side" in capsys.readouterr().out

	def test_a_number_of_128_or_more_printed_whole_is_another_table_s_and_is_not_named (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The slip the naming is for is a byte read as decimal, and no byte makes a number so big.

		Naming every NRPN not beside its label named every row of a second table that prints
		its numbers whole, and that list grew with the table.
		"""
		result = followed(tmp_path,
			"band13: {label: Vocoder Band13 Panpot, nrpn: 604}, band14: {label: Vocoder Band14 Panpot, nrpn: 605},"
			" octaves: {label: Arp Octaves, nrpn: 14}, bend: {label: Bend Range, nrpn: 1234},"
			" glide: {label: Glide, nrpn: 1235}, last: {label: Last Byte, nrpn: 127},"
			" first: {label: First Past, nrpn: 128}, volume: {label: Volume, cc: 7}",
			self.TABLE + "NRPN 1234 Bend Range\nNRPN 1235 Glide\n127 Last Byte\n128 First Past\n7 Volume\n")

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "not beside its label: octaves.nrpn = 14, which would be 00 0E, and is printed whole" in printed
		assert "not beside its label: bend" not in printed and "not beside its label: glide" not in printed

		# The line is at 128: a byte holds 127 and no more.
		assert "not beside its label: last.nrpn = 127" in printed
		assert "not beside its label: first" not in printed

		# And only an NRPN is ever named: the controller on the same page is no row of this table.
		assert "not beside its label: volume" not in printed

	def test_nothing_is_said_where_no_number_is_printed_as_bytes (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A definition whose NRPNs are printed whole has no rows to ask about."""
		result = followed(tmp_path, "cutoff: {label: Cutoff, nrpn: 300}", "300 Cutoff\n")

		tool.render(result, verbose = False)

		assert "two bytes stand side by side" not in capsys.readouterr().out


class TestReadingAPageInTheDocumentItsCitationNames:

	"""A page cited as `chart p. 2` is read in `chart` alone, since 2026-10-13 without asking.

	Read in every document, the manual's `p. 2` turns the chart to its second sheet too:
	seven of the JU-06A's controller numbers are on that sheet, its account cited `chart
	p. 1` and `manual p. 2` and no `chart p. 2`, and all seven were found.  That reading is
	still there to compare against, as `attribute = False` and as `--pool`.
	"""

	PAGES = {
		"manual.pdf": ["the manual's first page", "the manual's second page"],
		"chart.pdf": ["1 2 3 the chart's first sheet", "47 70 79 the chart's second sheet"],
	}

	def follow (
			self,
			monkeypatch: pytest.MonkeyPatch,
			account: str,
			attribute: bool | None,
			pages: dict[str, list[str]] | None = None,
			sources: str = "manual: {sha256: aa}, chart: {sha256: bb}",
			pictures: tuple[tuple[str, int], ...] = ()) -> typing.Any:

		"""Follow a definition of three controllers into a manual and a chart of two pages each.

		``attribute`` of ``None`` asks for nothing, which is how the tool is run by default.
		``pictures`` names the sheets that carry an image, by file and sheet.
		"""

		held = pages or self.PAGES

		class Page:

			"""One sheet of a document: its text, and its images."""

			def __init__ (self, said: str, images: int) -> None:

				"""A sheet that says this and carries so many pictures."""

				self.said = said
				self.images: list[typing.Any] = [object()] * images

			def extract_text (self) -> str:

				"""What the sheet says."""

				return self.said

		class Reader:

			"""What the tool asks of a PDF it has opened: its pages."""

			def __init__ (self, path: pathlib.Path) -> None:

				"""Open the document of this name."""

				self.pages = [Page(said, (path.name, sheet) in pictures)
					for sheet, said in enumerate(held[path.name], 1)]

		monkeypatch.setattr(tool, "reader_for", Reader)

		definition = pymidiinstrumentdefs.parse(
			"definition: 1\nmodel: {name: X}\n"
			f"source: >-\n  {account}\n"
			f"sources: {{{sources}}}\n"
			"controls: {range: {cc: 47}, chorus: {cc: 70}, hpf: {cc: 79}}\n",
			source = "x.yaml",
		)
		index = {"aa": pathlib.Path("manual.pdf"), "bb": pathlib.Path("chart.pdf")}

		if attribute is None:
			return tool.follow(definition, "x", index)

		return tool.follow(definition, "x", index, attribute = attribute)

	def test_asked_for_nothing_a_keyed_page_is_read_in_its_own_document (self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""Which is the stronger reading, and the one a gate should be: the three are missing."""
		result = self.follow(monkeypatch, "The chart (chart p. 1) and the mode (manual p. 2).", None)

		assert result.attributed
		assert [number for _, _, number in result.missing] == [47, 70, 79]

	def test_the_command_line_reads_by_key_and_one_flag_pools_the_pages (
			self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""`--pool` is the one way back to the weaker reading, and it has to reach the check."""
		asked: list[bool] = []

		def follow (definition: typing.Any, name: str, index: typing.Any, attribute: bool = True) -> typing.Any:

			"""Note what was asked for, and find nothing."""

			asked.append(attribute)

			return tool.Result(name = name, attributed = attribute)

		monkeypatch.setattr(tool, "follow", follow)

		assert tool.main(["--library", str(tmp_path), "moog/minitaur"]) == 0
		assert "each page cited with a source key before it is read in that document alone" in capsys.readouterr().out

		# The flag from when this was a switch still runs, and asks for what is done anyway.
		assert tool.main(["--library", str(tmp_path), "--attribute", "moog/minitaur"]) == 0
		assert "each page cited with a source key before it is read in that document alone" in capsys.readouterr().out

		assert tool.main(["--library", str(tmp_path), "--pool", "moog/minitaur"]) == 0
		assert "every cited page is read in every document that has pages (--pool)" in capsys.readouterr().out

		assert asked == [True, True, False]

		with pytest.raises(SystemExit):
			tool.main(["--library", str(tmp_path), "--attribute", "--pool", "moog/minitaur"])

	def test_the_run_ends_by_counting_the_pages_that_named_no_document (
			self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""So that a pass is not taken for more than it is, and before the line a gate reads."""

		def follow (definition: typing.Any, name: str, index: typing.Any, attribute: bool = True) -> typing.Any:

			"""Two paged documents in each, and bare pages in the Minitaur alone."""

			result = tool.Result(name = name, attributed = attribute)
			result.documents = [tool.Followed(key = key, source = None) for key in ("manual", "chart")]

			for document in result.documents:
				document.path = tmp_path / f"{document.key}.pdf"
				document.extent = 2

			result.unattributed = {2, 9} if name == "moog/minitaur" else set()

			return result

		monkeypatch.setattr(tool, "follow", follow)
		monkeypatch.setattr(tool, "render", lambda result, verbose: None)

		assert tool.main(["--library", str(tmp_path), "moog/minitaur", "moog/dfam"]) == 0

		lines = capsys.readouterr().out.strip().splitlines()

		assert lines[-2] == ("2 page(s) in 1 definition(s) are cited with no document named where there is "
			"more than one to turn to, and were read in every one")
		assert lines[-1] == "2 of 2 definitions check out"

		# Pooled, every page is everybody's, so there is nothing of the kind to count.
		assert tool.main(["--library", str(tmp_path), "--pool", "moog/minitaur", "moog/dfam"]) == 0
		assert "cited with no document named" not in capsys.readouterr().out

	def test_the_command_line_fails_where_a_definition_does (
			self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""One number missing in one definition of two: the run says which fraction is sound, and fails."""

		def follow (definition: typing.Any, name: str, index: typing.Any, attribute: bool = False) -> typing.Any:

			"""Find one number missing in the Minitaur and nothing wrong in the other."""

			result = tool.Result(name = name, wanted = [("volume", "cc", 7)])

			if name == "moog/minitaur":
				result.missing = list(result.wanted)

			return result

		monkeypatch.setattr(tool, "follow", follow)

		assert tool.main(["--library", str(tmp_path), "moog/minitaur", "moog/dfam"]) == 1

		printed = capsys.readouterr().out

		assert "not on any cited page: volume.cc = 7" in printed
		assert "1 of 2 definitions check out" in printed

	def test_a_definition_that_cannot_be_read_is_a_fault_and_not_a_traceback (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It is an answer about that definition, and the run goes on to the next."""
		assert tool.main(["--library", str(tmp_path), "zz/no_such_instrument"]) == 1

		printed = capsys.readouterr().out

		assert "zz/no_such_instrument\n    could not be read:" in printed
		assert "0 of 1 definitions check out" in printed

	def test_a_citation_is_sorted_by_the_key_before_it (self) -> None:
		"""With a comma or without, and a page with no key before it is nobody's."""
		keyed, bare = tool.cited_by_key(
			"The table is at manual p. 2 and chart, pp. 1-2, with a note on p. 9 and (p. 4).",
			{"manual", "chart"})

		assert keyed == {"manual": {2}, "chart": {1, 2}}
		assert bare == {4, 9}

	def test_a_word_that_is_no_key_names_no_document (self) -> None:
		"""`manual` and `guide` are words in a sentence unless the sources have them."""
		keyed, bare = tool.cited_by_key("User manual pp. 19-20 and guide p. 3.", {"reference"})

		assert keyed == {}
		assert bare == {3, 19, 20}

	def test_a_key_is_a_word_of_its_own_and_is_written_as_the_sources_write_it (self) -> None:
		"""`flow-chart` is not `chart`, and neither is `Chart`."""
		keyed, bare = tool.cited_by_key("See the flow-chart p. 2 and Chart p. 3.", {"chart"})

		assert keyed == {}
		assert bare == {2, 3}

		# Whichever hyphen it is: a text layer may set a non-breaking one, or a dash for one.
		for hyphen in ("\u2010", "\u2011", "\u2012", "\u2013"):
			assert tool.cited_by_key(f"See the re{hyphen}chart p. 2.", {"chart"}) == ({}, {2}), hyphen

		# A long dash is punctuation between two clauses, and the word after it is a word.
		assert tool.cited_by_key("The tables\u2014chart p. 2\u2014are two.", {"chart"}) == ({"chart": {2}}, set())

	def test_only_the_word_directly_before_the_page_is_asked (self) -> None:
		"""What the rule cannot see, set down so that nobody takes it for more than it is."""
		keyed, bare = tool.cited_by_key(
			"The chart (p. 2), the manual's p. 4, and manual p. 3 and p. 5.", {"manual", "chart"})

		assert keyed == {"manual": {3}}
		assert bare == {2, 4, 5}

		# And a key by accident: the page is the manual's, and the word before it is `chart`.
		assert tool.cited_by_key("see the chart p. 4 of the manual", {"manual", "chart"}) == ({"chart": {4}}, set())

	def test_read_in_every_document_another_s_page_finds_the_numbers (
			self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""The fault as it was: the manual's page 2 turns the chart to its second sheet."""
		result = self.follow(monkeypatch, "The chart (chart p. 1) and the mode (manual p. 2).", False)

		assert not result.missing

	def test_read_in_its_own_document_they_are_missing (self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""The chart is cited by its first sheet alone, and the numbers are on its second."""
		result = self.follow(monkeypatch, "The chart (chart p. 1) and the mode (manual p. 2).", True)

		assert [number for _, _, number in result.missing] == [47, 70, 79]

	def test_and_found_once_the_account_cites_their_page (self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""The remedy is in the account and not in the tool."""
		result = self.follow(monkeypatch,
			"The chart (chart p. 1), its second sheet (chart p. 2) and the mode (manual p. 2).", True)

		assert not result.missing and result.sound

	def test_a_page_with_no_document_named_is_every_document_s (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""Nothing says whose it is, so it is read in each, and the report says which pages were."""
		result = self.follow(monkeypatch, "The chart (chart p. 1) and its second sheet (p. 2).", True)

		assert not result.missing
		assert result.unattributed == {2}

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "printed 2 cited with no document named, so read in every document that has pages" in printed

	def test_that_is_not_said_where_only_one_document_has_pages (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""There is then one document a page could be in, and nothing to say."""
		result = self.follow(monkeypatch, "Its second sheet (p. 2).", True,
			sources = "manual: {sha256: aa, paginated: false}, chart: {sha256: bb}")

		tool.render(result, verbose = False)

		assert result.unattributed == {2}
		assert "cited with no document named" not in capsys.readouterr().out

	ONE_PAGE_MANUAL = {
		"manual.pdf": ["the manual's only page"],
		"chart.pdf": ["1 2 3 the chart's first sheet", "47 70 79 the chart's second sheet"],
	}

	def test_a_page_its_own_document_has_not_got_is_unreachable (self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""Though another document has a page of that number, which is how it used to pass."""
		account = "The chart (chart p. 2) and the mode (manual p. 2)."
		pooled = self.follow(monkeypatch, account, False, pages = self.ONE_PAGE_MANUAL)

		assert not pooled.unreachable and pooled.sound

		result = self.follow(monkeypatch, account, True, pages = self.ONE_PAGE_MANUAL)

		assert result.unreachable == {2}
		assert not result.sound

	def test_a_page_with_no_document_named_that_none_has_is_unreachable (
			self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""As it is where every page is read in every document."""
		result = self.follow(monkeypatch, "The chart (chart p. 2) and a note (p. 9).", True)

		assert result.unreachable == {9}

	def test_a_page_credited_to_a_document_with_no_pages_is_unreachable (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""It was reported read in every document, and said nothing at all read in its own."""
		account = "The numbers are at chart p. 2, and the mode at manual p. 1."
		sources = "manual: {sha256: aa}, chart: {sha256: bb, paginated: false}"
		pages = {"manual.pdf": ["the manual's only page"], "chart.pdf": ["47 70 79 the chart"]}
		pooled = self.follow(monkeypatch, account, False, pages = pages, sources = sources)

		assert pooled.unreachable == {2}

		result = self.follow(monkeypatch, account, True, pages = pages, sources = sources)

		assert result.unreachable == {2}
		assert not result.sound

		tool.render(result, verbose = False)

		assert "⚠ cited but in no document read: printed 2" in capsys.readouterr().out

	def test_read_in_every_document_each_line_names_every_page_cited (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""As it always did, and nothing is said of pages that name no document."""
		result = self.follow(monkeypatch, "The chart (chart p. 2), the mode (manual p. 1) and a note (p. 1).", False)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "manual: manual.pdf  [2 pages]\n        printed 1-2 → file 1-2\n" in printed
		assert "chart: chart.pdf  [2 pages]\n        printed 1-2 → file 1-2\n" in printed
		assert "cited with no document named" not in printed

		# Every page cited, and the pages of the file that were read for them: a manual of one
		# page is turned to that page alone, and its line still says what was asked of it.
		result = self.follow(monkeypatch, "The chart (chart p. 2) and the mode (manual p. 1).", False,
			pages = self.ONE_PAGE_MANUAL)

		tool.render(result, verbose = False)

		assert "manual: manual.pdf  [1 pages]\n        printed 1-2 → file 1\n" in capsys.readouterr().out

	def test_a_page_with_no_document_named_is_listed_only_for_a_document_that_has_it (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""Page 2 is read in every document, and the manual has one page."""
		result = self.follow(monkeypatch, "The mode (manual p. 1), the chart (chart p. 1) and a note (p. 2).",
			True, pages = self.ONE_PAGE_MANUAL)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "manual: manual.pdf  [1 pages]\n        printed 1 → file 1\n" in printed
		assert "chart: chart.pdf  [2 pages]\n        printed 1-2 → file 1-2\n" in printed

	def test_a_document_with_no_pages_is_read_whole_and_says_that (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""It has no page to be cited by, which is not the same as none of its pages being cited."""
		result = self.follow(monkeypatch, "The chart (chart p. 2).", True,
			sources = "manual: {sha256: aa, paginated: false}, chart: {sha256: bb}")

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "manual: manual.pdf  [no pages]\n        no pages to turn to, so the whole document was read\n" in printed
		assert "no page cited is in it" not in printed

	def test_a_gap_is_closed_before_a_scan_excuses_and_a_byte_is_read_only_after (
			self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""Beside a scan: `4 7` is still a 47 the page has, and `4F` is a byte nobody need read."""
		pages = {"manual.pdf": ["", ""], "chart.pdf": ["the code is 4 7 here, and Bn 4F xx", "nothing"]}
		result = self.follow(monkeypatch, "The chart (chart p. 1) and the manual (manual p. 2).", False, pages = pages)

		assert result.documents[0].scanned
		assert result.across_a_gap == [("range", "cc", 47)]
		assert result.unverifiable == [("chorus", "cc", 70), ("hpf", "cc", 79)]
		assert not result.as_hex and not result.missing

	def test_each_document_s_line_names_the_pages_cited_for_it (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""And not every page the account cites, which is what the line said of each."""
		result = self.follow(monkeypatch, "The chart (chart p. 2) and the mode (manual p. 1).", True)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "manual: manual.pdf  [2 pages]\n        printed 1 → file 1\n" in printed
		assert "chart: chart.pdf  [2 pages]\n        printed 2 → file 2\n" in printed

	def test_two_printed_pages_on_one_sheet_are_not_both_one_document_s (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""Page 4 is the chart's.  The manual prints two to a sheet, and its sheet 2 holds a page 4."""
		result = self.follow(monkeypatch, "The mode (manual p. 3) and the chart (chart p. 2).", True,
			sources = "manual: {sha256: aa, pages_per_sheet: 2}, chart: {sha256: bb}")

		tool.render(result, verbose = False)

		assert "manual: manual.pdf  [2 pages]\n        printed 3 → file 2\n" in capsys.readouterr().out

	def test_a_document_read_on_no_page_says_so (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""A line with nothing under it could not be told from a document nobody cites."""
		result = self.follow(monkeypatch, "The chart (chart p. 2).", True)

		tool.render(result, verbose = False)

		printed = capsys.readouterr().out

		assert "manual: manual.pdf  [2 pages]\n        no page cited is in it, so none of it was read\n" in printed

	def test_a_pictured_page_excuses_only_where_it_is_cited_for_its_document (
			self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""The manual declares its page 2 a picture, and page 2 is cited for the chart."""
		sources = "manual: {sha256: aa, pictured_pages: [2]}, chart: {sha256: bb}"
		pages = {"manual.pdf": ["one", "two"], "chart.pdf": ["1 2 3", "nothing wanted here"]}
		pictures = (("manual.pdf", 2),)
		account = "The mode (manual p. 1) and the chart (chart p. 2)."
		pooled = self.follow(monkeypatch, account, False, pages = pages, sources = sources, pictures = pictures)

		assert len(pooled.unverifiable) == 3 and pooled.documents[0].pictured == [2]

		result = self.follow(monkeypatch, account, True, pages = pages, sources = sources, pictures = pictures)

		assert result.documents[0].pictured == []
		assert len(result.missing) == 3 and not result.unverifiable

	def test_a_declared_picture_on_a_page_cited_for_its_document_is_checked_for_an_image (
			self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""The declaration holds where the page is the document's own, and is still checked."""
		sources = "manual: {sha256: aa, pictured_pages: [2]}, chart: {sha256: bb}"
		account = "The mode (manual p. 2) and the chart (chart p. 1)."
		result = self.follow(monkeypatch, account, True, sources = sources, pictures = (("manual.pdf", 2),))

		assert result.documents[0].pictured == [2] and not result.misdeclared
		assert len(result.unverifiable) == 3

		result = self.follow(monkeypatch, account, True, sources = sources)

		assert result.misdeclared == [("manual", 2)]

	def test_a_scan_nobody_cites_a_page_of_excuses_no_number (self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""Read in every document it is turned to and found blank, and every number is excused."""
		pages = {"manual.pdf": ["", ""], "chart.pdf": ["1 2 3", "nothing wanted here"]}
		account = "The chart (chart p. 2)."
		pooled = self.follow(monkeypatch, account, False, pages = pages)

		assert pooled.documents[0].scanned and len(pooled.unverifiable) == 3

		result = self.follow(monkeypatch, account, True, pages = pages)

		assert not result.documents[0].scanned
		assert len(result.missing) == 3

	def test_a_scan_that_is_cited_still_excuses (self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""Its numbers are where nothing can look for them, as before."""
		pages = {"manual.pdf": ["", ""], "chart.pdf": ["1 2 3", "nothing wanted here"]}
		result = self.follow(monkeypatch, "The numbers (manual p. 2) and the chart (chart p. 2).", True, pages = pages)

		assert result.documents[0].scanned and len(result.unverifiable) == 3

	def test_a_lost_document_fails_a_definition_whose_pages_are_all_reachable (
			self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""Nothing can be checked against a file nobody has, whatever the others hold."""
		result = self.follow(monkeypatch, "The chart (chart p. 2).", False,
			sources = "manual: {sha256: zz}, chart: {sha256: bb}")

		assert [document.key for document in result.lost] == ["manual"]
		assert not result.unreachable and not result.missing
		assert not result.sound

	def test_every_number_is_listed_with_how_it_was_found_and_only_the_found_are_ticked (
			self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
		"""A number nobody could look for was ticked, under a line saying it was not checked at all."""
		pages = {"manual.pdf": ["", ""], "chart.pdf": ["47 and the code is 7 0 here", "nothing"]}
		result = self.follow(monkeypatch, "The chart (chart p. 1) and the manual (manual p. 2).", False, pages = pages)

		tool.render(result, verbose = True)
		printed = capsys.readouterr().out

		assert "        ✓ range.cc = 47\n" in printed
		assert "          chorus.cc = 70  (across a gap)\n" in printed
		assert "          hpf.cc = 79  (not checked)\n" in printed
		assert printed.count("✓") == 1

	def test_each_weaker_way_of_finding_a_number_has_its_own_words (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""Seven ways a number is not simply found, and none of them is a tick."""
		ways = (
			("as_byte_pairs", "as two bytes side by side"), ("as_halves", "as two halves"),
			("in_a_range", "inside a range"), ("across_a_gap", "across a gap"), ("as_hex", "in hexadecimal"),
			("unverifiable", "not checked"), ("missing", "not found"))
		result = tool.Result(name = "x", documents = [])
		result.wanted = [("whole", "cc", 7)] + [(field, "nrpn", 200 + at) for at, (field, _) in enumerate(ways)]

		for at, (field, _) in enumerate(ways):
			setattr(result, field, [(field, "nrpn", 200 + at)])

		tool.render(result, verbose = True)
		printed = capsys.readouterr().out

		assert "        ✓ whole.cc = 7\n" in printed and printed.count("✓") == 1

		for at, (field, said) in enumerate(ways):
			assert f"          {field}.nrpn = {200 + at}  ({said})\n" in printed, field

	def test_a_document_that_is_not_in_the_library_is_still_lost (self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""And the page credited to it is one nobody could turn to."""
		result = self.follow(monkeypatch, "The chart (chart p. 2) and the mode (manual p. 2).", True,
			sources = "manual: {sha256: zz}, chart: {sha256: bb}")

		assert [document.key for document in result.lost] == ["manual"]
		assert result.unreachable == {2}
		assert not result.sound

	def test_a_page_offset_is_followed_in_the_document_it_belongs_to (self, monkeypatch: pytest.MonkeyPatch) -> None:
		"""The chart's printed page 1 is its second sheet, and the manual's is its first."""
		result = self.follow(monkeypatch, "The chart (chart p. 1) and the mode (manual p. 1).", True,
			sources = "manual: {sha256: aa}, chart: {sha256: bb, page_offset: 1}")

		assert not result.missing
		assert [document.pages for document in result.documents] == [[1], [2]]


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

		Only what is on no readable page is left as not checked, where a page of a scan is
		cited too.  The scan's page has to be cited: read by key, a scan nobody cites a page
		of excuses no number.
		"""
		scan = tmp_path / "scan.pdf"
		writer = pypdf.PdfWriter()
		writer.add_blank_page(width = 200, height = 200)
		writer.write(scan)
		digest = hashlib.sha256(scan.read_bytes()).hexdigest()

		result = followed(
			tmp_path, "band14_panpot: {nrpn: 605}, band15_panpot: {nrpn: 606}", self.ROW,
			extra = f", scan: {{sha256: {digest}, page_offset: 0}}",
			account = "The second table is a scan (scan p. 1).",
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

	def test_a_page_as_served_is_read_as_text_and_found_by_its_digest (self, tmp_path: pathlib.Path) -> None:
		"""Markup and all: a definition cites the served page where its visible text lacks the thing."""
		made = tmp_path / "page.html"
		made.write_text('<script>{"title":"Synthtribe App","version":"3.2.4"}</script>\n', encoding = "utf-8")

		assert '"version":"3.2.4"' in tool.whole_text(made)
		assert tool.library_index(tmp_path) == {hashlib.sha256(made.read_bytes()).hexdigest(): made}

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

		assert tool.ranges_holding(83, page)
		assert tool.ranges_holding(86, page)

	def test_an_endpoint_is_not_this_rule_s_business (self) -> None:
		"""It is on the page as itself, and is found by looking for it."""
		assert not tool.ranges_holding(80, "80...87")
		assert not tool.ranges_holding(87, "80...87")

	def test_a_wide_range_names_nothing (self) -> None:
		"""A note row reading 0-127 would otherwise answer for every controller in the file."""
		assert not tool.ranges_holding(74, "Note Number 0-127 0-127")
		assert not tool.ranges_holding(99, "0 - 127")

	def test_the_dashes_a_maker_actually_uses (self) -> None:
		"""One Korg page prints an ellipsis, a hyphen and an en dash on the same sheet."""
		for printed in ("102...109", "102-109", "102\u2013109", "102 \u2026 109"):
			assert tool.ranges_holding(105, printed), printed

	def test_a_fine_half_given_by_a_rule_is_found_inside_the_range_the_rule_prints (self, tmp_path: pathlib.Path) -> None:
		"""Moog's Theremini gives every controller below 32 a fine control "at locations 32 - 63".

		It prints no fine half's own number, so a definition that holds one for controller 9
		asks for a 41 that no row carries, and the page has named it in the only way a rule can.
		"""
		page = ("7 Master Volume\n9 Wavetable Scan Rate\n"
			"All implemented controller numbers 0 - 31 have corresponding LSB (fine) controls at locations 32 - 63.")
		result = followed(tmp_path, "scan_rate: {cc: 9, lsb: 41}", page)

		assert result.in_a_range == [("scan_rate", "lsb", 41)]
		assert result.range_forms == {"scan_rate.lsb": ["32 - 63"]}
		assert not result.missing and not result.also_across_a_gap

	def test_each_range_is_named_with_the_numbers_found_inside_it (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Which range it was is what there is to read, since one is matched wherever it stands."""
		result = followed(tmp_path, "knob_2: {cc: 81}, knob_3: {cc: 82}, vector: {cc: 17}",
			"Layer A Mod Knobs 1...8 80...87\nVector 16 - 19\n")

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "3 controller numbers found only inside a range the maker prints" in printed
		assert "inside 80...87: knob_2.cc = 81, knob_3.cc = 82\n" in printed
		assert "inside 16 - 19: vector.cc = 17\n" in printed

	def test_every_range_that_holds_a_number_is_named_and_not_the_first_alone (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The S-1's chart: the Basic Channel row stands above the Control Change row that means it."""
		page = "Basic Channel  Changed  1\u201316  1\u201316\nControl Change\n11\n12\u201331\n64, 65\n"

		assert list(tool.ranges_holding(14, page)) == ["1\u201316", "12\u201331"]
		assert list(tool.ranges_holding(17, page)) == ["12\u201331"]

		# One range printed twice, in whatever spacing, is named once and as it first stands.
		assert list(tool.ranges_holding(41, "at locations 32 - 63, and again 32-63")) == ["32 - 63"]

		# **And each is given with the line it stands on**, which is what tells a row of a chart
		# from a group of controls.
		assert tool.ranges_holding(14, page) == {
			"1\u201316": "Basic Channel Changed 1\u201316 1\u201316", "12\u201331": "12\u201331"}

		result = followed(tmp_path, "osc_range: {cc: 14}, osc_pulse_width: {cc: 15}, lfo: {cc: 17}", page)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "inside 1\u201316 and 12\u201331: osc_range.cc = 14, osc_pulse_width.cc = 15\n" in printed
		assert "inside 12\u201331: lfo.cc = 17\n" in printed

		# The line is said once, and not at all where the range is alone on it.
		assert printed.count("1\u201316 stands in: Basic Channel Changed 1\u201316 1\u201316\n") == 1
		assert "12\u201331 stands in" not in printed

	def test_a_range_two_groups_share_has_its_line_said_once (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The wavestate's chart row holds the numbers of two of its tables' rows."""
		result = followed(tmp_path, "a_2: {cc: 81}, b_2: {cc: 89}",
			"Layer A Mod Knobs 1...8 80...87\nLayer B Mod Knobs 1...8 88...95\n2-6, 8-9, 67-95, 102-119\n")

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "inside 80...87 and 67-95: a_2.cc = 81\n" in printed
		assert "inside 88...95 and 67-95: b_2.cc = 89\n" in printed
		assert printed.count("67-95 stands in: 2-6, 8-9, 67-95, 102-119\n") == 1

	def test_the_line_is_given_as_the_page_has_it_and_says_where_it_is_cut (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A marked hexadecimal form is no end of a range, and is still on the line it is on."""
		long = "status 0xB0 values 20 - 30, " + "and so on " * 12
		result = followed(tmp_path, "depth: {cc: 25}", long + "\n")

		assert result.range_lines == {"20 - 30": " ".join(long.split())}

		tool.render(result, verbose = False)

		assert f"20 - 30 stands in: {long[:93]}...\n" in capsys.readouterr().out

	def test_an_nrpn_is_not_looked_for_inside_a_range (self, tmp_path: pathlib.Path) -> None:
		"""A range of controller numbers names no parameter number."""
		result = followed(tmp_path, "knob: {nrpn: 83}", "Layer A Mod Knobs 1...8 80...87\n")

		assert result.missing == [("knob", "nrpn", 83)]
		assert not result.in_a_range

	def test_the_digits_of_a_marked_hexadecimal_form_end_no_range (self) -> None:
		"""`0x10 - 40` is sixteen to forty, and was read as ten to forty."""
		assert tool.ranges_holding(25, "values 0x10 - 40") == {}

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
		assert tool.hexadecimal_form(74, "Bn 4A xx \u2014 Filter Cutoff")

	def test_a_form_of_digits_alone_is_never_read_as_hexadecimal (self) -> None:
		"""A page that prints 40 is far likelier to mean forty than 64."""
		assert not tool.hexadecimal_form(64, "Bn 40 xx")
		assert not tool.hexadecimal_form(16, "Bn 10 xx")

	def test_it_must_stand_as_a_word_of_its_own (self) -> None:
		"""Part of a longer word is not the byte, whatever letters surround it."""
		for printed in ("B4A", "4A7", "4AH", "x4Ay", "0x4AB", "10x4A"):
			assert not tool.hexadecimal_form(74, printed), printed

	def test_a_form_the_maker_marks_as_hexadecimal_is_read_digits_or_not (self) -> None:
		"""Behringer's Neutron prints its modulation wheel's fine half as 0x21 and never as 33.

		A form of digits alone is refused because `21` is far likelier twenty-one.  With
		`0x` before it, it is 33 and nothing else.
		"""
		printed = "Modulation wheel or lever - MIDI CC 0x01 (MSB) & MIDI CC 0x21 (LSB)"

		assert tool.hexadecimal_form(33, printed)
		assert tool.hexadecimal_form(1, printed)
		assert tool.hexadecimal_form(33, printed) == "0x21"
		assert not tool.hexadecimal_form(33, "MIDI CC 21 (LSB)")
		assert not tool.hexadecimal_form(21, printed), "0x21 is not twenty-one"

	def test_a_marked_form_is_read_in_either_case (self) -> None:
		"""`0x2a` is written as often as `0x2A`, where a bare `2a` is a label."""
		assert tool.hexadecimal_form(42, "CC 0x2a") == "0x2a"
		assert tool.hexadecimal_form(74, "CC 0X4A") == "0X4A"
		assert tool.hexadecimal_form(74, "Bn 4A xx") == "4A"

	def test_a_marked_form_is_named_as_the_page_has_it (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Both halves, since the digits of neither are read as a decimal number."""
		result = followed(tmp_path, "modulation: {cc: 1, lsb: 33}",
			"Modulation wheel or lever - MIDI CC 0x01 (MSB) & MIDI CC 0x21 (LSB)\n")

		assert result.as_hex == [("modulation", "cc", 1), ("modulation", "lsb", 33)]
		assert not result.missing

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert "0 of 2 numbers found" in printed
		assert "modulation.cc = 1, printed as 0x01" in printed
		assert "modulation.lsb = 33, printed as 0x21" in printed

	def test_a_marked_form_is_read_at_any_width (self) -> None:
		"""`0x7` is 7, and `0x12C` is the 300 that no two digits hold."""
		assert tool.hexadecimal_form(7, "CC 0x7") == "0x7"
		assert tool.hexadecimal_form(10, "CC 0xA") == "0xA"
		assert tool.hexadecimal_form(33, "CC 0x0021") == "0x0021"
		assert tool.hexadecimal_form(300, "NRPN 0x12C") == "0x12C"
		assert tool.hexadecimal_form(300, "NRPN 0x012c") == "0x012c"

		for printed in ("0x210", "10x21", "0x21h", "CC0x21", "0 x21"):
			assert not tool.hexadecimal_form(33, printed), printed

	def test_a_marked_form_is_a_word_of_its_own (self) -> None:
		"""A screen of 1280x800 and a box of 12.0x8.5 inches hold no hexadecimal number."""
		assert tool.numbers_as_printed("1280x800 and 12.0x8.5 in") == {1280, 800, 12, 0, 8, 5}
		assert 21 in tool.numbers_as_printed("0x21h") and 4 in tool.numbers_as_printed("0x4AH")
		assert not tool.hexadecimal_form(8, "12.0x8.5 in") and not tool.hexadecimal_form(128, "1280x800")

		# A decimal point on one side alone is enough, whichever side.
		assert tool.numbers_as_printed("12.0x8 in") == {12, 0, 8} and not tool.hexadecimal_form(8, "12.0x8 in")
		assert tool.numbers_as_printed("0x8.5 in") == {0, 8, 5} and not tool.hexadecimal_form(8, "0x8.5 in")

		# The full stop that ends a sentence is not a decimal point.
		assert tool.hexadecimal_form(33, "It is CC 0x21.") == "0x21"
		assert tool.numbers_as_printed("It is CC 0x21.") == set()

	def test_a_marked_form_is_one_number_and_never_two_bytes (self, tmp_path: pathlib.Path) -> None:
		"""What this does not read, set down so that nobody takes it for more than it is."""
		assert tool.hexadecimal_form(1117, "NRPN 0x045D   Vocoder Band14 Panpot") == "0x045D"

		for number, page in enumerate(("NRPN 0x045D   Vocoder Band14 Panpot\n", "NRPN 0x04 0x5D   Vocoder Band14 Panpot\n")):
			library = tmp_path / str(number)
			library.mkdir()
			result = followed(library, "band14: {nrpn: 605}", page)

			assert result.missing == [("band14", "nrpn", 605)], page

	def test_the_marked_form_is_the_one_named_where_a_page_has_both (self) -> None:
		"""It is the form that can mean nothing else."""
		assert tool.hexadecimal_form(74, "Bn 4A xx, which is CC 0x4A") == "0x4A"

	def test_twenty_one_is_not_found_in_a_marked_thirty_three (self, tmp_path: pathlib.Path) -> None:
		"""It was found whole: the digits after `0x` were read as a decimal number."""
		result = followed(tmp_path, "wrong: {cc: 21}", "MIDI CC 0x01 (MSB) & MIDI CC 0x21 (LSB)\n")

		assert result.missing == [("wrong", "cc", 21)]

	def test_it_must_be_printed_in_capitals (self) -> None:
		"""Makers print bytes in capitals, and "4a" in running text is far likelier a label."""
		assert not tool.hexadecimal_form(74, "Bn 4a xx")

	def test_a_number_wider_than_a_byte_has_no_two_digit_form (self) -> None:
		"""An NRPN of 300 would be 12C, which is read only where the maker marks it."""
		assert not tool.hexadecimal_form(300, "12C 2C")

	def test_it_is_reported_as_weaker_and_never_counted_as_found (self, capsys: pytest.CaptureFixture[str]) -> None:
		"""A page that prints a byte has not printed the number in the base the definition holds."""
		result = tool.Result(name = "behringer/td_3_mo", documents = [])
		result.wanted = [("filter_cutoff", "cc", 74)]
		result.as_hex = list(result.wanted)

		tool.render(result, verbose = False)
		printed = capsys.readouterr().out

		assert result.sound
		assert "0 of 1 numbers found" in printed
		assert "1 numbers found only in hexadecimal, as the maker prints them" in printed

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


class TestTheNotesADefinitionOwesItsPages:

	"""Every note a voice answers to should be on a cited page, and so should every note sent for one."""

	def test_a_second_number_and_a_sent_number_are_both_wanted (self) -> None:
		definition = pymidiinstrumentdefs.parse(
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"voice: {addressing: voices, voices: {kick: [36, 35], snare: 38}, "
			"voices_sent: {b: {notes: {kick: 37}}}}\n", source = "x.yaml")

		assert tool.wanted_numbers(definition) == [
			("kick", "note", 36), ("kick", "note", 35), ("snare", "note", 38), ("b.kick", "sent", 37)]
