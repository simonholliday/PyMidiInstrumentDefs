"""The parts of ``tools/check_quotations.py`` that can be checked without a manual.

The check itself is deliberately not a test, for the same reason the citation check is
not: it reads manufacturers' documents, which are copyrighted and are never committed
here, so in CI it could only ever skip.

What is tested here needs no document at all: reducing two readings of the same words to
the same string, and finding the quotations in a definition. Every rule below is here
because a **correct** quotation failed without it, and a tool that reports a correct
citation as wrong is worse than no tool, because its output stops being read.
"""

import hashlib
import importlib.util
import os
import pathlib
import types
import typing

import pytest
import yaml

import pymidiinstrumentdefs


def load_tool () -> typing.Any:

	"""Load the checker, which is a script beside the package rather than in it."""

	path = pathlib.Path(__file__).resolve().parent.parent / "tools" / "check_quotations.py"
	spec = importlib.util.spec_from_file_location("check_quotations", path)

	assert spec is not None and spec.loader is not None, f"{path} is not importable"

	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)

	return module


tool = load_tool()


class TestReducingTwoReadingsToOneString:

	def test_spaces_inside_a_word_do_not_matter (self) -> None:
		"""Moog's and Arturia's text layers both do this, differently in each file."""
		assert tool.squash("FI LTER SLOPES") == tool.squash("FILTER SLOPES")

	def test_case_does_not_matter (self) -> None:
		"""A manual sets a table heading in capitals; a definition quotes it in a sentence."""
		assert tool.squash("PROGRAM CHANGE") == tool.squash("Program change")

	def test_a_curly_apostrophe_is_a_straight_one (self) -> None:
		"""Thirteen correct quotations in one file failed on this alone."""
		assert tool.squash("the Subsequent 37’s clock") == tool.squash("the Subsequent 37's clock")

	def test_a_quote_mark_inside_a_quotation_does_not_matter (self) -> None:
		"""A definition quoting a sentence that quotes a word has to change the marks."""
		assert tool.squash("in “Play” mode") == tool.squash("in 'Play' mode")

	def test_an_en_dash_is_a_hyphen (self) -> None:
		assert tool.squash("0–127") == tool.squash("0-127")

	def test_the_makers_own_cross_reference_comes_out (self) -> None:
		"""One manual prints "a MIDI [p.112] Start command" in the middle of its sentence."""
		assert tool.squash("a MIDI [p.112] Start command") == tool.squash("a MIDI Start command")

	def test_two_different_sentences_are_still_different (self) -> None:
		"""The folding must not make everything match everything."""
		assert tool.squash("will select pattern 1-128") != tool.squash("selects pattern 1-128")


class TestSplittingAQuotationIntoWhatMustBeFound:

	def test_an_ellipsis_marks_something_left_out (self) -> None:
		"""Each side is looked for, since the middle is not being quoted."""
		assert tool.pieces("a note above C5 ... in its top octave") == \
			[tool.squash("a note above C5"), tool.squash("in its top octave")]

	def test_a_square_bracket_adapts_a_word_to_the_sentence (self) -> None:
		"""The page says "makes it possible"; the definition writes "make[s] it possible"."""
		found = tool.pieces("make[s] it possible to play")

		assert found == ["make", tool.squash("it possible to play")]
		assert all("[" not in part for part in found)

	def test_a_plain_quotation_is_one_piece (self) -> None:
		assert tool.pieces("Program change messages 0-127") == [tool.squash("Program change messages 0-127")]


class TestFindingTheQuotationsInADefinition:

	# A folded block scalar, which is what every definition's source line is: quote marks
	# inside it are the maker's own and are not escaped.
	BODY = (
		"definition: 1\n"
		"model: {name: X}\n"
		"source: >-\n"
		'  A manual (10pp): "the first thing" (p. 4) and "the second one here" (pp. 7-8).\n'
		"controls:\n"
		"  one:\n"
		'    # "a third thing" (p. 9), and "no page for this one".\n'
		"    cc: 70\n"
	)

	def test_every_quotation_with_a_page_is_found (self) -> None:
		"""Including one inside a comment, which is where most of them are."""
		found = tool.quotations(self.BODY)

		assert [q for q, _, _ in found] == ["the first thing", "the second one here", "a third thing"]

	def test_the_pages_are_read_off_each_one (self) -> None:
		"""A range gives both of its ends, since a citation does not say which page."""
		found = {quotation: pages for quotation, _, pages in tool.quotations(self.BODY)}

		assert found["the first thing"] == [4]
		assert found["the second one here"] == [7, 8]
		assert found["a third thing"] == [9]

	def test_a_phrase_too_short_to_identify_a_page_is_left_alone (self) -> None:
		"""A few words match half a manual, so a short quotation proves nothing either way."""
		body = 'source: >-\n  A manual: "the mode" (p. 4) and "a long enough phrase" (p. 5).\n'
		found = [q for q, _, _ in tool.quotations(body)]

		assert found == ["a long enough phrase"]

	def test_a_quotation_with_no_page_is_not_checked (self) -> None:
		"""There is nothing to check it against, so it is left alone rather than failed."""
		assert "no page for this one" not in [q for q, _, _ in tool.quotations(self.BODY)]

	def test_a_comment_folded_over_lines_is_still_one_quotation (self) -> None:
		"""Which is how a definition of any length writes them."""
		body = (
			"controls:\n"
			"  one:\n"
			'    # "a sentence that runs over\n'
			'    # two lines of comment" (p. 12).\n'
			"    cc: 70\n"
		)
		found = tool.quotations(body)

		assert len(found) == 1
		assert found[0][2] == [12]
		assert "runs over two lines" in found[0][0]


class TestAQuotationThatNamesItsSourceInsteadOfAPage:

	"""A document with no pages has no page to cite, so a definition names it instead.

	Nine quotations in the corpus were in that shape and the checker counted none of
	them - not as failures, which would have been noticed, but as nothing at all, so
	its summary read as though the file had been checked in full.
	"""

	BODY = (
		"definition: 1\n"
		"model: {name: X}\n"
		"source: >-\n"
		'  A page says "the engine has four voices" (product_page), and the manual\n'
		'  says "something on a page" (p. 4).\n'
		"controls:\n"
		"  one:\n"
		'    # "a note in a comment" (release_notes).\n'
		"    cc: 70\n"
	)

	KEYS = ("product_page", "release_notes", "manual")

	def test_a_quotation_naming_a_source_is_found (self) -> None:
		"""Including one in a comment, and with the comment markers folded away."""
		found = tool.named_quotations(self.BODY, self.KEYS)

		assert found == [
			("the engine has four voices", "product_page"),
			("a note in a comment", "release_notes"),
		]

	def test_a_page_citation_is_left_to_the_paged_check (self) -> None:
		"""The page is the more precise locator, so it is not also matched here."""
		assert "something on a page" not in [q for q, _ in tool.named_quotations(self.BODY, self.KEYS)]

	def test_a_parenthesis_that_is_not_a_source_key_is_not_a_locator (self) -> None:
		"""Otherwise any aside after a quotation would be read as naming a document."""
		body = 'source: >-\n  It says "a long enough phrase here" (our own words).\n'

		assert tool.named_quotations(body, self.KEYS) == []

		# And a key-shaped word this definition has no source for is not one either.  It is
		# a source the definition has not got, and is reported as that.
		body = 'source: >-\n  It says "a long enough phrase here" (midi_impl).\n'

		assert tool.named_quotations(body, self.KEYS) == []
		assert tool.misnamed_sources(body, self.KEYS, ("midi_impl",)) == [
			("a long enough phrase here", "midi_impl")]

	def test_both_shapes_of_locator_are_found_in_one_file (self) -> None:
		"""A definition citing an unpaginated source usually cites a paged one too."""
		paged = [q for q, _, _ in tool.quotations(self.BODY)]
		named = [q for q, _ in tool.named_quotations(self.BODY, self.KEYS)]

		assert paged == ["something on a page"]
		assert len(named) == 2
		assert not set(paged) & set(named), "a quotation was counted by both checks"


class TestALocatorThatNamesAPlaceAndNotAPage:

	"""A document with no pages still has places in it, and a definition cites them.

	`teenage_engineering/op_1` rests on a website of numbered sections and a list of release
	notes, so its locators are `(15.6)` and `(os_updates, #243)`. Neither is a page and
	neither is a bare key, so the checker read both as no locator and reported nothing to
	check for a file with twelve quotations in it.
	"""

	BODY = (
		"definition: 1\n"
		"model: {name: X}\n"
		"source: >-\n"
		'  The notes say "the identity reply now reflects the family" (os_updates, #243), the\n'
		'  guide says "no sync is transmitted from the unit" (10.4) and "in beat match it leads"\n'
		'  (section 10.5), a fix reads "messages were sometimes not sent" (1.55D), and one more\n'
		'  is "something printed on a real page" (os_updates p. 3).\n'
		"controls:\n"
		"  one:\n"
		'    # "a note in a comment about it" (os_updates, 1.1.0).\n'
		"    cc: 70\n"
	)

	KEYS = ("os_updates", "guide")

	def test_a_key_followed_by_a_place_names_that_source (self) -> None:
		"""What follows the key is the writer's note of where, and the source is still named."""
		in_source, _ = tool.placed_quotations(self.BODY, self.KEYS)

		assert in_source == [
			("the identity reply now reflects the family", "os_updates"),
			("a note in a comment about it", "os_updates"),
		]

	def test_a_section_number_alone_names_no_document (self) -> None:
		"""So it comes back with its locator, to be looked for in every document cited."""
		_, numbered = tool.placed_quotations(self.BODY, self.KEYS)

		assert numbered == [
			("no sync is transmitted from the unit", "10.4"),
			("in beat match it leads", "section 10.5"),
			("messages were sometimes not sent", "1.55D"),
		]

	def test_a_key_followed_by_a_page_is_left_to_the_paged_check (self) -> None:
		"""The page is the more precise locator, so the paged check keeps it."""
		in_source, numbered = tool.placed_quotations(self.BODY, self.KEYS)

		assert "something printed on a real page" not in [q for q, _ in in_source + numbered]
		assert [q for q, _, _ in tool.quotations(self.BODY)] == ["something printed on a real page"]

	def test_prose_in_brackets_is_still_not_a_locator (self) -> None:
		"""An aside, a description of a document, and a key this definition does not have."""
		for aside in ("our own words", "product page", "setting 0.10", "midi_impl, #4",
				"release notes, column 3 under the v1.0.6 heading"):
			body = f'source: >-\n  It says "a long enough phrase here" ({aside}).\n'

			assert tool.placed_quotations(body, self.KEYS) == ([], []), aside

		# No place to look in, which is all this asks.  The fourth is a misnamed source all
		# the same, and fails a run as one: `midi_impl` is a document's name elsewhere.
		body = 'source: >-\n  It says "a long enough phrase here" (midi_impl, #4).\n'

		assert tool.misnamed_sources(body, self.KEYS) == [("a long enough phrase here", "midi_impl")]

	def test_an_aside_that_begins_with_a_key_is_not_a_locator_without_its_comma (self) -> None:
		"""`manual` and `guide` are keys in most definitions and ordinary words in a sentence."""
		for aside in ("guide paraphrased", "guide and os_updates", "os_updates heading",
				"guide: 10.4"):
			body = f'source: >-\n  It says "a long enough phrase here" ({aside}).\n'

			assert tool.placed_quotations(body, self.KEYS) == ([], []), aside
			assert tool.uncovered(body, self.KEYS)[0] == ["a long enough phrase here"], aside

	def test_a_bare_number_is_not_a_section (self) -> None:
		"""A channel, a controller, a year and a voltage sit in brackets far oftener than a section.

		Each was read as a section by the first form of this, which then failed the run for a
		passage that quoted nothing, and counted `"Cutoff" (74)` as a quotation too short to
		check.
		"""
		for aside in ("16", "2", "74", "127", "2025", "5V", "2x", "section4"):
			body = f'source: >-\n  It says "a long enough phrase here" ({aside}), and "Cutoff" ({aside}).\n'

			assert tool.placed_quotations(body, self.KEYS) == ([], []), aside
			assert tool.uncovered(body, self.KEYS) == (["a long enough phrase here"], []), aside
			assert tool.misnamed_sources(body, self.KEYS) == [], aside

	def test_a_number_with_a_dot_or_a_word_for_section_is_read (self) -> None:
		"""A release's number as readily as a section's, which is why the report says number."""
		for place in ("15.6", "1.55D", "v1.0.6", "1.1.17", "section 4", "Section 10.5",
				"sec. 3", "§ 4", "§4"):
			body = f'source: >-\n  It says "a long enough phrase here" ({place}).\n'

			assert tool.placed_quotations(body, self.KEYS) == (
				[], [("a long enough phrase here", place)]), place
			assert tool.uncovered(body, self.KEYS) == ([], []), place

	def test_a_place_in_a_document_with_pages_is_not_read (self) -> None:
		"""A document with pages is cited by its page.

		`(guide, page 42)` is a page citation mistyped. Read as a place, it passed on a search
		of the whole guide while the correctly written `(guide p. 42)` beside it failed.  It
		is refused, as the bare key of such a document is, and so is no passage without a
		locator: it has one, and the wrong one.
		"""
		for locator in ("guide, page 42", "guide, 42", "guide, section 4", "guide"):
			body = f'source: >-\n  It says "a long enough phrase here" ({locator}).\n'

			if locator != "guide":
				assert tool.placed_quotations(body, self.KEYS, paged = {"guide"}) == ([], []), locator

			assert tool.sourced_quotations(body, self.KEYS, paged = {"guide"}) == [], locator
			assert tool.uncovered(body, self.KEYS, paged = {"guide"}) == ([], []), locator
			assert tool.unpaged_quotations(body, self.KEYS, {"guide"}) \
				== [("a long enough phrase here", "guide")], locator

			if locator == "guide":
				continue

			# And the same words after the key of a document with no pages are a place in it.
			assert tool.placed_quotations(body, self.KEYS) == (
				[("a long enough phrase here", "guide")], []), locator

	def test_a_quotation_that_begins_with_a_bracket_is_still_found (self) -> None:
		"""The marks are paired in order, so the bracket inside the passage is part of it."""
		body = (
			"source: >-\n"
			'  One says "the first thing it says" (os_updates) and then a range,\n'
			'  "(OFF, 1-127) is the range" (15.6).\n')

		assert tool.placed_quotations(body, self.KEYS) == (
			[], [("(OFF, 1-127) is the range", "15.6")])

	def test_prose_between_two_quotations_is_never_a_quotation (self) -> None:
		"""Even where the second one begins with a bracket that reads as a place.

		A pattern run over the whole text takes the words from one closing mark to the next
		opening one, sees `(10.4)` after them, and looks for prose in the maker's documents.
		That failed a run on a correct file, with nothing in it the writer could correct.
		"""
		for opening in ("(10.4) Sync and tempo", "(v2.1) adds a wrap setting",
				"(section 4) of the guide", "(os_updates, #243) reads"):
			body = (
				"source: >-\n"
				'  It says "no sync is transmitted from the unit" (guide) and then the heading\n'
				f'  "{opening}" comes next.\n')

			assert tool.placed_quotations(body, self.KEYS) == ([], []), opening
			assert tool.named_quotations(body, self.KEYS) == [
				("no sync is transmitted from the unit", "guide")], opening
			assert tool.uncovered(body, self.KEYS)[0] == [opening], opening

	def test_a_backticked_example_of_either_shape_is_code_and_is_passed_over (self) -> None:
		"""Which is what the backticks are for, and what the coverage figures already do."""
		body = (
			"source: >-\n"
			"  The form is `\"the maker's own sentence\" (guide, #243)` or, with a number alone,\n"
			"  `\"the maker's own sentence\" (15.6)`.\n")

		assert tool.placed_quotations(body, self.KEYS) == ([], [])
		assert tool.uncovered(body, self.KEYS) == ([], [])

	def test_a_quoted_yaml_value_is_not_a_quotation_whatever_follows_it (self) -> None:
		"""A title in quote marks is YAML's, and the comment under it may open with a bracket."""
		body = (
			"sources:\n"
			"  guide:\n"
			'    title: "OP-1 user guide, section 15"\n'
			"    # (15.6) is the section the whole definition turns on\n"
			'    url: "https://example.invalid/guide"\n'
			"    # (os_updates, #243) is where the other half is\n")

		assert tool.placed_quotations(body, self.KEYS) == ([], [])

	def test_a_code_span_inside_the_brackets_leaves_the_passage_unlocated_once (self) -> None:
		"""Read with the span in, it was checked in its source and reported as unlocated too."""
		body = 'source: >-\n  It says "no sync is transmitted from the unit" (guide, `10.4`).\n'

		assert tool.placed_quotations(body, self.KEYS) == ([], [])
		assert tool.uncovered(body, self.KEYS)[0] == ["no sync is transmitted from the unit"]

	def test_marks_that_do_not_pair_give_nothing_here_as_they_give_no_coverage_figure (self) -> None:
		"""Pairing an odd number of marks in order would pair every one after the stray wrongly."""
		body = (
			"source: >-\n"
			'  It says "words that are quoted from it" (10.4), and one unclosed " mark.\n')

		assert tool.odd_quote_marks(body)
		assert tool.placed_quotations(body, self.KEYS) == ([], [])

	def test_the_locator_can_be_folded_and_emphasised (self) -> None:
		"""A comment wraps where it wraps, and a quotation is emphasised in the house style."""
		body = (
			"controls:\n"
			"  one:\n"
			'    # **"a note in a comment about it"** (os_updates,\n'
			'    # 1.1.0), and "the next one in that comment"\n'
			"    # (section 10.5).\n"
			"    cc: 70\n")

		assert tool.placed_quotations(body, self.KEYS) == (
			[("a note in a comment about it", "os_updates")],
			[("the next one in that comment", "section 10.5")])

	def test_neither_is_reported_as_having_no_locator_any_more (self) -> None:
		"""They are checked now, so counting them as unlocated would count them twice."""
		unlocated, _ = tool.uncovered(self.BODY, self.KEYS)

		assert unlocated == []

		# And an aside after a quotation still leaves it unlocated.
		body = 'source: >-\n  It says "a long enough phrase here" (our own words).\n'

		assert tool.uncovered(body, self.KEYS)[0] == ["a long enough phrase here"]

	def test_every_passage_is_in_exactly_one_list (self) -> None:
		"""A page, a bare key, a key with a place, a number alone, and no locator at all.

		Five answers, and each quoted passage of twelve characters or more gets exactly one.
		"""
		body = self.BODY.replace('(10.4)', '(guide)').replace(
			"controls:", '  And "words of our own about it" (an aside).\ncontrols:')
		paged = [q for q, _, _ in tool.quotations(body)]
		named = [q for q, _ in tool.named_quotations(body, self.KEYS)]
		in_source, numbered = tool.placed_quotations(body, self.KEYS)
		unlocated, short = tool.uncovered(body, self.KEYS)

		assert named == ["no sync is transmitted from the unit"]
		assert unlocated == ["words of our own about it"]
		assert short == []

		everywhere = paged + named + [q for q, _ in in_source + numbered] + unlocated

		assert sorted(everywhere) == sorted(set(everywhere)), "a passage is in two lists"
		assert sorted(everywhere) == sorted([
			"the identity reply now reflects the family",
			"no sync is transmitted from the unit",
			"in beat match it leads",
			"messages were sometimes not sent",
			"something printed on a real page",
			"a note in a comment about it",
			"words of our own about it",
		])


class TestCheckingAPlaceAgainstDocumentsOnDisk:

	"""`check()` itself, on a definition and a library of text files written for the test.

	No maker's document is needed for these: a `.txt` is a document with no pages, which is
	the kind of document the two place locators are for. What is tested is what the report
	says and which figure a quotation lands in, because every defect found in this part of
	the tool was there and not in the patterns.
	"""

	GUIDE = "10.4 Sync\nIn this mode no sync is transmitted from the unit at all.\n"
	NOTES = "#243\nThe identity reply now reflects the family of the product.\n"

	def check (
			self,
			tmp_path: pathlib.Path,
			capsys: pytest.CaptureFixture[str],
			prose: str,
			absent: tuple[str, ...] = (),
			paged: tuple[str, ...] = (),
			suffix: str | dict[str, str] = ".txt",
			third: bool = False,
			folded: bool = True) -> tuple[typing.Any, str]:

		"""Write a definition citing two documents, and check it against those on disk.

		``folded`` false writes the account on its key's own line and not as a block scalar.
		``suffix`` is one for both, or one for each by key.  ``third`` adds a source, `manual`,
		whose document is never written, so that it is one that could not be read.
		"""

		library = tmp_path / "library"
		library.mkdir(parents = True)

		sources = ""
		documents = [("guide", self.GUIDE), ("os_updates", self.NOTES)]

		if third:
			documents.append(("manual", "A document nobody has put in the library.\n"))
			absent = absent + ("manual",)

		for key, text in documents:
			ending = suffix if isinstance(suffix, str) else suffix.get(key, ".txt")

			if key not in absent:
				(library / f"{key}{ending}").write_text(text, encoding = "utf-8")

			sources += (
				f"  {key}:\n"
				f"    kind: web_page\n"
				f"    title: The {key}\n"
				f'    url: "https://example.invalid/{key}"\n'
				f"    sha256: {hashlib.sha256(text.encode()).hexdigest()}\n"
				f"    retrieved: 2026-10-01\n"
				+ ("" if key in paged else "    paginated: false\n"))

		path = tmp_path / "x.yaml"
		path.write_text(
			"definition: 1\n\nmodel:\n  manufacturer: Zz\n  name: X\n\n"
			+ (f"source: >-\n  {prose}" if folded else f"source: {prose}")
			+ f"\n\nsources:\n{sources}\n"
			"midi: none\n\nvoice:\n  addressing: none\n  polyphony: 1\n",
			encoding = "utf-8")

		tally = tool.check("zz/x", path, tool.library_index(library))

		return tally, capsys.readouterr().out

	def test_a_number_alone_is_found_and_the_report_says_where (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (10.4).')

		assert (tally.passed, tally.missing, tally.unchecked) == (1, 0, 0)
		assert "1 of 1 quotations located by a section or version number alone" in said
		assert "(10.4) in guide: no sync is transmitted from the unit" in said

	def test_a_number_alone_in_no_document_fails_when_every_document_was_read (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, said = self.check(tmp_path, capsys,
			'It says "words that are in neither of them" (10.4).')

		assert (tally.passed, tally.missing, tally.unchecked) == (0, 1, 0)
		assert "IN NO DOCUMENT CITED, located (10.4): words that are in neither of them" in said

		# Nothing was found, so the line ends there and promises no list.
		assert "which is a weaker check than naming it\n" in said

	def test_a_number_alone_is_unchecked_when_a_document_could_not_be_read (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The passage may be in the one that was not read, and nothing names which it is in.

		It was called `IN NO DOCUMENT CITED` and failed the run, where the same quotation
		written `(guide p. 4)` was unchecked and did not.
		"""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (10.4).', absent = ("guide",))

		assert (tally.passed, tally.missing, tally.unchecked) == (0, 0, 1)
		assert "IN NO DOCUMENT CITED" not in said
		assert "1 more are in no document that could be read, and 1 cited here that have no pages" \
			" could not be" in said

	def test_a_number_alone_found_in_what_was_read_passes_whatever_was_not (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, _ = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (10.4).', absent = ("os_updates",))

		assert (tally.passed, tally.missing, tally.unchecked) == (1, 0, 0)

	def test_a_place_in_a_named_source_is_looked_for_in_that_source_alone (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The guide holds the second passage, and it is credited to the notes, so it fails."""
		tally, said = self.check(tmp_path, capsys,
			'It says "the identity reply now reflects the family" (os_updates, #243) and'
			' "no sync is transmitted from the unit" (os_updates, #244).')

		assert (tally.passed, tally.missing, tally.unchecked) == (1, 1, 0)
		assert "1 of 2 quotations that name a source are in it" in said
		assert "NOT IN os_updates: no sync is transmitted from the unit" in said

	def test_a_named_source_that_could_not_be_read_is_unchecked_and_not_wrong (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""With a place after the key or without one: nobody opened the document either way."""
		tally, said = self.check(tmp_path, capsys,
			'It says "the identity reply now reflects the family" (os_updates, #243) and'
			' "the family of the product" (os_updates), and "no sync is transmitted" (guide).',
			absent = ("os_updates",))

		assert (tally.passed, tally.missing, tally.unchecked) == (1, 0, 2)
		assert "NOT IN" not in said

		# The two that could not be looked for are not counted among those that were.
		assert "1 of 1 quotations that name a source are in it" in said
		assert "2 name a source that could not be read, so they are unchecked:" in said
		assert "(os_updates): the identity reply now reflects the family" in said
		assert "(os_updates): the family of the product" in said

	def test_a_place_after_the_key_of_a_document_with_pages_is_refused_as_the_bare_key_is (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Not passed on a search of the whole document: refused, and told its page.

		It was left among the passages with no locator, which does not fail a run, while the
		bare key beside it came to be refused.  The two are one case.
		"""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (guide, page 42).', paged = ("guide",))

		assert (tally.passed, tally.missing, tally.no_locator, tally.unpaged) == (0, 0, 0, 1)
		assert tally.nothing_to_check == 0
		assert "with NO LOCATOR" not in said
		assert "cite a document that has pages and give NO PAGE" in said
		assert "it is on: printed p. 1" in said
		assert tool.faults(tally) == 1

	def test_marks_that_do_not_pair_are_not_reported_as_nothing_to_check (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A place locator is found by pairing the marks, so with an odd one nobody looked."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (10.4) and then an unclosed " mark.')

		assert (tally.passed, tally.missing, tally.unpairable) == (0, 0, 1)
		assert tally.nothing_to_check == 0
		assert "ODD NUMBER OF QUOTE MARKS" in said
		assert "NOTHING IN IT WAS CHECKED" in said
		assert "so there is nothing to check" not in said
		assert tool.faults(tally) == 1, "a definition nobody could check must fail the run"

		# And it says where to look, which "an odd number" alone does not.  The account is
		# the eighth line of the definition this harness writes.
		assert "in the paragraph that begins at line 8 (quote marks)" in said

	def test_unpaired_marks_leave_nothing_checked_even_what_a_pattern_once_found (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A bare key was found by a pattern and still checked, and the file passed on that half.

		Every shape is found by pairing now, so there is no half that can still be seen, and
		a clean bill for it would be a silence about the rest.
		"""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (guide) and "the family of the'
			' product" (os_updates, #243), and then an unclosed " mark.')

		assert (tally.passed, tally.missing, tally.unpairable) == (0, 0, 1)
		assert "quotations that name a source are in it" not in said
		assert "NOTHING IN IT WAS CHECKED" in said

	def test_one_backtick_left_open_leaves_nothing_checked_either (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It turns every later code span inside out, and one definition was read that way."""
		tally, said = self.check(tmp_path, capsys,
			'The `Sync setting is on, and it says "no sync is transmitted from the unit" (guide).')

		assert (tally.passed, tally.missing, tally.unpairable) == (0, 0, 1)
		assert "A BACKTICK THAT NO OTHER CLOSES" in said
		assert "ODD NUMBER OF QUOTE MARKS" not in said
		assert "in the paragraph that begins at line 8 (backticks)" in said
		assert tool.faults(tally) == 1

	def test_a_bare_key_of_a_document_with_pages_is_refused_and_told_its_page (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A search of the whole document passed it without a page ever being turned to.

		Thirty-eight quotations in seven definitions were written so.  The report names the
		page the passage is on, so that it can be written in.
		"""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (guide).', paged = ("guide",))

		assert (tally.passed, tally.missing, tally.unpaged) == (0, 0, 1)
		assert tally.nothing_to_check == 0
		assert "cite a document that has pages and give NO PAGE" in said
		assert "(guide): no sync is transmitted from the unit" in said
		assert "it is on: printed p. 1" in said
		assert "say `paginated: false` on its source" in said
		assert tool.faults(tally) == 1

		# The same words with the page written in are checked, and pass.
		tally, said = self.check(tmp_path / "again", capsys,
			'It says "no sync is transmitted from the unit" (guide p. 1).', paged = ("guide",))

		assert (tally.passed, tally.missing, tally.unpaged) == (1, 0, 0)

		# A passage that is on no page of it is told so, and one in a document that is not
		# held is told nothing, since nobody looked.
		tally, said = self.check(tmp_path / "absent", capsys,
			'It says "words that are in neither of them" (guide).', paged = ("guide",))

		assert tally.unpaged == 1
		assert "it is on: no page of it as this tool reads it" in said

		tally, said = self.check(tmp_path / "unheld", capsys,
			'It says "no sync is transmitted from the unit" (guide).', paged = ("guide",),
			absent = ("guide",))

		assert tally.unpaged == 1
		assert "it is on" not in said

	def test_a_bare_key_with_spaces_inside_the_brackets_is_checked (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It was counted as located by the figures that pair, and matched by no pattern."""
		tally, _ = self.check(tmp_path, capsys,
			'It says "words that are in neither of them" ( guide ).')

		assert (tally.passed, tally.missing, tally.no_locator) == (0, 1, 0)

	def test_a_source_the_definition_has_not_got_is_reported_with_a_page_or_without (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""`(wrong_key p. 3)` failed the run; `(wrong_key)` and `(wrong_key, #243)` passed.

		And the first went unreported too wherever no document with pages could be read,
		which is the case here: the return for that came before the test for a wrong name.
		"""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (manual p. 3), "the identity reply'
			' now reflects the family" (chart, #243) and "the family of the product" (reference).')

		assert tally.misnamed == 3
		assert (tally.passed, tally.missing, tally.no_locator, tally.unchecked) == (0, 0, 0, 0)
		assert "NO SOURCE NAMED 'manual': no sync is transmitted from the unit" in said
		assert "NO SOURCE NAMED 'chart': the identity reply now reflects the family" in said
		assert "NO SOURCE NAMED 'reference': the family of the product" in said
		assert "this definition's sources are: guide, os_updates" in said
		assert tool.faults(tally) == 3

	def test_an_aside_after_a_quotation_does_not_fail_the_run (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It leaves the passage with no locator, which is reported and is not a fault."""
		tally, said = self.check(tmp_path, capsys,
			'The chart prints "Recieve channel is fixed" (sic), "Local Control Off" (default), "Filter'
			' Cutoff Frequency" (filter_cutoff), "Channel is set here" (MIDI) and "set by hand" (manually).')

		assert (tally.misnamed, tally.no_locator) == (0, 4)
		assert "NO SOURCE NAMED" not in said
		assert tool.faults(tally) == 0

	def test_a_page_cited_in_a_source_that_has_no_pages_is_named_and_fails (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It was counted as unchecked, and nothing said which quotation or why."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (guide p. 1) and "the family of'
			' the product" (os_updates p. 3).', paged = ("guide",))

		assert (tally.passed, tally.unchecked, tally.pageless) == (1, 0, 1)
		assert "cite a page WHERE NO SOURCE IT COULD BE IN HAS PAGES" in said
		assert "(os_updates): the family of the product" in said
		assert tool.faults(tally) == 1

	def test_a_page_cited_where_no_source_has_pages_fails_whether_or_not_one_is_named (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""`(p. 4)` was unchecked, as if a document with pages had not been read; none has pages."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (p. 4).')

		assert (tally.pageless, tally.unchecked) == (1, 0)
		assert "no document with pages could be read" not in said
		assert "(no source named, and none here has pages): no sync is transmitted" in said

		# Refused, so it is not a definition that quotes nothing with a locator.
		assert tally.nothing_to_check == 0
		assert "so there is nothing to check" not in said

		# Where one source does have pages and is not held, it is unchecked, as it was.
		tally, said = self.check(tmp_path / "unheld", capsys,
			'It says "no sync is transmitted from the unit" (p. 4).', paged = ("guide",),
			absent = ("guide",))

		assert (tally.pageless, tally.unchecked) == (0, 1)
		assert "no document with pages could be read" in said

	def test_a_number_alone_is_looked_for_only_where_there_are_no_pages (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The guide holds the passage and has pages, so the number does not find it there."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (10.4).', paged = ("guide",))

		assert "0 of 1 quotations located by a section or version number alone are in a document cited" \
			" here that has no pages" in said

		# **Not looked for there is not absent from it**, which is what this said of it, and
		# what it then counted it as while naming the page.  It gives no page, and fails as that.
		assert (tally.passed, tally.missing, tally.unpaged) == (0, 0, 1)
		assert "IN NO DOCUMENT CITED" not in said
		assert "1 quotation(s) located by a number alone are on a page of a document that has pages" in said
		assert "(10.4): no sync is transmitted from the unit\n            it is on: guide printed p. 1\n" in said
		assert tool.faults(tally) == 1

	def test_a_number_alone_found_nowhere_says_so_of_the_pages_too (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, said = self.check(tmp_path, capsys,
			'It says "words that are in neither of them" (10.4).', paged = ("guide",))

		assert (tally.missing, tally.unpaged) == (1, 0)
		assert "IN NO DOCUMENT CITED THAT HAS NO PAGES, located (10.4)" in said
		assert "and it is on no page of a document held either, as this tool reads it" in said

	def test_a_document_with_pages_that_could_not_be_read_does_not_excuse_a_number_alone (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It is looked for where there are no pages, and every such document was read."""
		tally, said = self.check(tmp_path, capsys,
			'It says "words that are in neither of them" (10.4).', paged = ("guide",), absent = ("guide",))

		assert (tally.missing, tally.unchecked) == (1, 0)

		# Where the one that could not be read has no pages, the passage may be in it.
		tally, said = self.check(tmp_path / "unpaged", capsys,
			'It says "words that are in neither of them" (10.4).', paged = ("guide",),
			absent = ("os_updates",))

		assert (tally.missing, tally.unchecked) == (0, 1)

	def test_a_number_alone_where_every_source_has_pages_is_refused (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It passed on a search of whole documents, which is what the bare key was refused for."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (10.4).', paged = ("guide", "os_updates"))

		assert (tally.passed, tally.missing, tally.unpaged) == (0, 0, 1)
		assert "cite a document that has pages and give NO PAGE" in said
		assert "by its key" not in said
		assert "(a number alone, 10.4, and every source here has pages): no sync is transmitted" in said
		assert "it is on: guide printed p. 1" in said
		assert tally.nothing_to_check == 0 and "so there is nothing to check" not in said
		assert tool.faults(tally) == 1

	def test_a_definition_with_no_sources_is_not_one_whose_sources_all_have_pages (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A number alone was refused for giving no page, and a page was told to mend a source."""
		path = tmp_path / "x.yaml"
		path.write_text(
			"definition: 1\n\nmodel:\n  manufacturer: Zz\n  name: X\n\n"
			'source: >-\n  It says "no sync is transmitted from the unit" (10.4) and "the family of'
			' the product" (p. 4).\n\n'
			"midi: none\n\nvoice:\n  addressing: none\n  polyphony: 1\n",
			encoding = "utf-8")
		tally = tool.check("zz/x", path, {})
		said = capsys.readouterr().out

		assert (tally.unpaged, tally.pageless, tally.unchecked, tally.missing) == (0, 1, 0, 1)
		assert "give NO PAGE" not in said
		assert "where the definition has no sources, give it the one the page is in" in said

		# The number alone is in no document, there being none, and was "unchecked" for want
		# of one that could be read.
		assert "IN NO DOCUMENT CITED, located (10.4): no sync is transmitted from the unit" in said
		assert "this definition has no sources, so there is none for it to be in" in said
		assert "none could be read" not in said

	def test_a_page_of_a_document_that_could_not_be_read_is_unchecked_and_named (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It was counted and never named, so the figure could not be squared with the file."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (guide p. 1) and "the family of'
			' the product" (os_updates p. 3).', paged = ("guide", "os_updates"), absent = ("os_updates",))

		assert (tally.passed, tally.unchecked, tally.missing) == (1, 1, 0)
		assert "1 cite a page of a document that could not be read, so they are unchecked:" in said
		assert "(os_updates p. 3): the family of the product" in said
		assert tool.faults(tally) == 0

	def test_two_backticks_each_side_are_a_code_span_and_what_it_hides_is_seen (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Read as two empty spans, the example between them was a quotation, looked for on a page."""
		tally, said = self.check(tmp_path, capsys,
			'The form is ``"words that are in neither of them" (guide)`` in the guide.')

		assert (tally.unpairable, tally.missing, tally.hidden) == (0, 0, 1)
		assert tool.faults(tally) == 1

		# With nothing in it that reads as a located quotation, it is passed over.
		tally, said = self.check(tmp_path / "plain", capsys,
			'A span may hold a backtick, ``the ` key``, and it says "no sync is transmitted from the'
			' unit" (guide).')

		assert (tally.unpairable, tally.hidden, tally.passed) == (0, 0, 1)
		assert tool.faults(tally) == 0

	def test_two_code_spans_back_to_back_are_sound (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Two backticks together there are one span closing and the next opening."""
		tally, said = self.check(tmp_path, capsys,
			'Bytes `F0``F7` frame it, and it says "no sync is transmitted from the unit" (guide).')

		assert (tally.unpairable, tally.passed) == (0, 1)
		assert tool.faults(tally) == 0

	def test_a_run_of_backticks_that_no_run_of_as_many_closes_names_its_paragraph (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, said = self.check(tmp_path, capsys,
			'The label is `` when unset, and it says "no sync is transmitted from the unit" (guide).')

		assert (tally.unpairable, tally.passed) == (1, 0)
		assert "A BACKTICK THAT NO OTHER CLOSES" in said
		assert "in the paragraph that begins at line 8 (backticks)" in said

	def test_a_quote_mark_inside_a_quotation_is_seen_and_fails (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It ends the quotation early, and the rest was looked for by its tail or not at all."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is "transmitted" from the unit" (guide).')

		assert tally.mispaired == 2
		assert "BEGIN OR END WITH A SPACE, ARE EMPTY, OR BEGIN BY CLOSING AN EMPHASIS BEFORE A LOCATOR" in said
		assert "'no sync is '" in said
		assert tool.faults(tally) >= 1

		# Written with a single mark inside, it is one quotation and is found.
		tally, said = self.check(tmp_path / "again", capsys,
			"It says \"no sync is 'transmitted' from the unit\" (guide).")

		assert (tally.passed, tally.mispaired) == (1, 0)
		assert tool.faults(tally) == 0

	def test_two_stray_marks_no_longer_hide_the_quotation_between_them (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The count is even, so nothing odd is seen, and every pair between them is inside out.

		A pattern found the quotation all the same and failed the run on it.  Pairing does
		not find it, and would pass the file, but for what the wrongly paired passages look
		like.
		"""
		tally, said = self.check(tmp_path, capsys,
			'The rear has a 1/4" jack. It says "words that are in neither of them" (guide).'
			' Beside it is a 1/8" jack.')

		assert tally.mispaired == 2
		assert tool.faults(tally) == 2
		assert "so there is nothing to check" not in said

	def test_a_stray_mark_before_an_emphasised_quotation_shows_as_a_passage_that_begins_with_a_locator (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Neither fragment has a space at its edge: one ends in the emphasis and one begins in it."""
		tally, said = self.check(tmp_path, capsys,
			'A 19"-wide unit. It says **"words that are in neither of them"** (guide).'
			' Its disk is 3.5".')

		assert tally.mispaired == 1
		assert tool.faults(tally) >= 1

	def test_a_quotation_that_begins_with_a_bracket_of_its_own_is_sound (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Ninety-one in the corpus begin so, and the bracket of one may read as a locator."""
		tally, said = self.check(tmp_path, capsys,
			'The heading is "(10.4) Sync" and under it "no sync is transmitted from the unit" (guide).')

		assert (tally.mispaired, tally.passed) == (0, 1)
		assert tool.faults(tally) == 0

	def test_a_quotation_with_a_code_span_at_its_edge_is_sound (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The span is taken out before a passage is looked for, and a span is not a space."""
		tally, said = self.check(tmp_path, capsys,
			'It says "`In this mode` no sync is transmitted from the unit `at all`" (guide), and'
			' the display reads "`OFF`" and nothing more.')

		assert (tally.mispaired, tally.passed) == (0, 1)
		assert tool.faults(tally) == 0

	def test_two_backticks_left_open_no_longer_hide_the_quotation_between_them (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""One long code span to this tool, with a quotation and its locator inside it."""
		tally, said = self.check(tmp_path, capsys,
			'The `Sync setting. It says "words that are in neither of them" (guide). Then the'
			' `Clock setting.')

		assert tally.hidden == 1
		assert "INSIDE BACKTICKS" in said
		assert "(guide): words that are in neither of them" in said
		assert tool.faults(tally) == 1

	def test_an_account_that_is_not_a_block_scalar_is_not_read_and_fails (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It loads all the same, and was reported as a definition with nothing to check."""
		tally, said = self.check(tmp_path, capsys,
			'The guide says "words that are in neither of them" (guide).', folded = False)

		assert (tally.accountless, tally.nothing_to_check, tally.missing) == (1, 0, 0)
		assert "its account does not begin `source: >-` or `source: |`" in said
		assert tool.faults(tally) == 1

	def test_a_literal_block_is_an_account_and_no_account_at_all_is_no_fault (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""`source: |` is read as `source: >-` is, and a definition that gives none has none to find."""
		path = tmp_path / "x.yaml"
		head = "definition: 1\n\nmodel:\n  manufacturer: Zz\n  name: X\n\n"
		tail = "midi: none\n\nvoice:\n  addressing: none\n  polyphony: 1\n"

		path.write_text(head + tail, encoding = "utf-8")

		assert tool.check("zz/x", path, {}).accountless == 0

		path.write_text(head + 'source: |\n  It says "a passage with no locator at all".\n\n' + tail,
			encoding = "utf-8")
		tally = tool.check("zz/x", path, {})

		assert (tally.accountless, tally.no_locator) == (0, 1)

	def test_the_faults_of_the_file_are_carried_whether_or_not_a_document_is_held (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Each return of the check carries them: nothing to look for, no document, and the end."""
		prose = ('It says "no sync is transmitted from the unit" (guide), "the family of the'
			' product" (user guide p. 4) and "the identity reply now reflects" (reference).')

		# Nothing to look for: the one readable locator is of a document that has pages.
		tally, _ = self.check(tmp_path / "nothing", capsys, prose, paged = ("guide",))

		assert (tally.unpaged, tally.unreadable, tally.misnamed) == (1, 1, 1)
		assert tally.nothing_to_check == 0

		# No document held.
		tally, said = self.check(tmp_path / "unheld", capsys, prose,
			absent = ("guide", "os_updates"))

		assert "none could be read" in said
		assert (tally.unchecked, tally.unreadable, tally.misnamed) == (1, 1, 1)

		# And at the end, with the document read.
		tally, _ = self.check(tmp_path / "held", capsys, prose)

		assert (tally.passed, tally.unreadable, tally.misnamed) == (1, 1, 1)
		assert tool.faults(tally) == 2

	def test_only_a_locator_nobody_can_read_is_not_nothing_to_check (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, said = self.check(tmp_path, capsys,
			'It says "the family of the product" (user guide p. 4).')

		assert (tally.unreadable, tally.nothing_to_check) == (1, 0)
		assert "so there is nothing to check" not in said

	def test_what_is_not_in_its_source_is_reported_in_the_order_of_the_file (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A key with a place and then a bare key: the two shapes were listed one after the other."""
		tally, said = self.check(tmp_path, capsys,
			'It says "first words that are in neither" (os_updates, #9), "second words that'
			' are in neither" (guide) and "third words that are in neither" (os_updates, #10).')

		assert tally.missing == 3
		assert said.index("NOT IN os_updates: first words") < said.index("NOT IN guide: second words") \
			< said.index("NOT IN os_updates: third words")

	def test_every_clause_on_the_page_is_its_own_figure (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""It was printed for its definition and counted neither as passed nor as missing."""
		tally, said = self.check(tmp_path, capsys,
			'It says "10.4 Sync: no sync is transmitted from the unit" (guide p. 1).',
			paged = ("guide",))

		assert (tally.passed, tally.missing, tally.partly) == (0, 0, 1)
		assert "1 more have every clause on the cited page" in said
		assert tool.faults(tally) == 0, "the weaker check is not a fault"

	def test_a_passage_in_curly_marks_with_a_locator_is_reported_and_not_passed_over (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Only straight marks are paired, so nothing would check it."""
		tally, said = self.check(tmp_path, capsys,
			'It says “no sync is transmitted from the unit” (guide).')

		assert (tally.passed, tally.curly, tally.nothing_to_check) == (0, 2, 0)
		assert "CURLY QUOTE MARK(S) stand outside every quotation" in said
		assert tool.faults(tally) == 2

	def test_a_text_file_has_no_second_reading (self, tmp_path: pathlib.Path) -> None:
		"""It is read as it is, so there is nothing for another extractor to disagree with."""
		path = tmp_path / "notes.txt"
		path.write_text(self.NOTES, encoding = "utf-8")

		assert tool.read_whole_again(path) is None

	def test_a_passage_only_the_second_reading_holds_passes_and_is_listed (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
			monkeypatch: pytest.MonkeyPatch) -> None:
		"""One extractor turns a hyphen into a letter, and the words are on the page all the same."""
		monkeypatch.setattr(tool, "read_whole_again",
			lambda path: self.GUIDE + "The non-registered parameters are read.\n"
				if path.name == "guide.txt" else None)

		tally, said = self.check(tmp_path, capsys,
			'It says "The non-registered parameters are read" (10.4) and'
			' "the non-registered parameters" (guide, 10.4).')

		assert (tally.passed, tally.missing, tally.disagreed) == (2, 0, 2)
		assert "2 of those located without a page were found only by the second extractor" in said
		assert "IN NO DOCUMENT CITED" not in said
		assert "NOT IN" not in said

	def test_an_absence_resting_on_one_reading_of_a_pdf_says_so (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
			monkeypatch: pytest.MonkeyPatch) -> None:
		"""Where the second extractor is not there to ask, the report must not sound as sure."""
		monkeypatch.setattr(tool, "pages_of",
			lambda path: [path.read_text(encoding = "utf-8")])
		monkeypatch.setattr(tool, "read_whole_again", lambda path: None)

		tally, said = self.check(tmp_path, capsys,
			'It says "words that are in neither of them" (10.4).', suffix = ".pdf")

		assert (tally.passed, tally.missing) == (0, 1)
		assert "IN NO DOCUMENT CITED, located (10.4)" in said
		assert "guide, os_updates read with pypdf" in said
		assert "that is one reading of a document rather than the document" in said

		# And nothing of the kind is said about text files, which have one reading by nature.
		tally, said = self.check(tmp_path / "again", capsys,
			'It says "words that are in neither of them" (10.4).')

		assert tally.missing == 1
		assert "read with pypdf" not in said

	def test_a_pdf_the_second_extractor_did_read_gets_no_caveat (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
			monkeypatch: pytest.MonkeyPatch) -> None:
		"""Two readings, and the passage in neither: that is an absence, said plainly."""
		monkeypatch.setattr(tool, "pages_of",
			lambda path: [path.read_text(encoding = "utf-8")])
		monkeypatch.setattr(tool, "read_whole_again",
			lambda path: path.read_text(encoding = "utf-8"))

		tally, said = self.check(tmp_path, capsys,
			'It says "words that are in neither of them" (10.4).', suffix = ".pdf")

		assert (tally.passed, tally.missing, tally.disagreed) == (0, 1, 0)
		assert "IN NO DOCUMENT CITED, located (10.4)" in said
		assert "read with pypdf" not in said

	def test_the_caveat_names_only_a_document_an_absence_was_looked_for_in (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
			monkeypatch: pytest.MonkeyPatch) -> None:
		"""A passage credited to one document is not made doubtful by the reading of another.

		Three sources, which is what it takes: the guide a PDF with one reading, the notes a
		text file, and a manual nobody could read.  The first passage names no document and is
		in neither that was read, so it is unchecked - and asking about it is what finds the
		guide has one reading.  The second is credited to the notes and is not in them.  That
		is an absence from a text file, and the guide's reading has nothing to do with it.
		"""
		monkeypatch.setattr(tool, "pages_of",
			lambda path: [path.read_text(encoding = "utf-8")])
		monkeypatch.setattr(tool, "read_whole_again", lambda path: None)

		tally, said = self.check(tmp_path, capsys,
			'It says "words that are in neither of them" (10.4) and "other words in neither"'
			' (os_updates, #9).', suffix = {"guide": ".pdf"}, third = True)

		assert (tally.passed, tally.missing, tally.unchecked) == (0, 1, 1)
		assert "NOT IN os_updates: other words in neither" in said
		assert "read with pypdf" not in said

		# And where the absence is from the PDF itself, the caveat is there and names it alone.
		tally, said = self.check(tmp_path / "again", capsys,
			'It says "words that are in neither of them" (guide, 10.4).',
			suffix = {"guide": ".pdf"})

		assert tally.missing == 1
		assert "NOT IN guide" in said
		assert "guide read with pypdf" in said
		assert "os_updates read with pypdf" not in said and "guide, os_updates" not in said

	def test_an_empty_second_reading_of_a_pdf_is_no_reading (
			self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
		"""An extractor that runs and returns no text has not read the document."""
		path = tmp_path / "guide.pdf"
		path.write_bytes(b"not a pdf at all")

		class Done:
			returncode = 0
			stdout = "  \n"

		monkeypatch.setattr(tool.subprocess, "run", lambda *args, **kwargs: Done())

		assert tool.read_whole_again(path) is None

		Done.stdout = "words on the page\n"

		assert tool.read_whole_again(path) == "words on the page\n"


class TestAPassageTheMakerPrintsInSquareBrackets:

	"""Korg prints a parameter's range in square brackets, and a definition quotes it so.

	A square bracket in a quotation was always read as the file adapting a word to its own
	sentence, and what is inside one is not looked for.  A quotation that is all bracket then
	has nothing to look for, and was found on every page of every document: five in the
	corpus were in that state.
	"""

	def test_a_quotation_that_is_all_bracket_is_looked_for_with_its_brackets (self) -> None:
		assert tool.pieces("[1 Note...12 Note]") == []
		assert tool.readings("[1 Note...12 Note]") == [["[1note", "12note]"]]

	def test_an_adaptation_is_still_read_as_one (self) -> None:
		"""Both readings are offered, and the page says which it was."""
		assert tool.readings("make[s] it possible to play") == [
			["make[s]itpossibletoplay"], ["make", "itpossibletoplay"]]

	def test_one_short_word_before_a_bracket_is_not_enough_to_look_for (self) -> None:
		"""`CLOCK [Internal, External, Auto]` was looked for by the word `clock` alone."""
		assert tool.readings("CLOCK [Internal, External, Auto]") == [["clock[internal,external,auto]"]]

	def test_a_quotation_with_no_bracket_has_one_reading (self) -> None:
		assert tool.readings("a note above C5 ... in its top octave") == [
			[tool.squash("a note above C5"), tool.squash("in its top octave")]]

	def test_a_page_carries_a_quotation_read_either_way (self) -> None:
		page = tool.squash("Bend Range + [ 1 Note...12 Note] If the Slider is set to PITCH BEND")

		assert tool.carried(page, tool.readings("[1 Note...12 Note]"))
		assert not tool.carried(page, tool.readings("[1 Note...24 Note]"))
		assert tool.carried(tool.squash("which makes it possible to play"),
			tool.readings("make[s] it possible to play"))

	def test_a_quotation_with_nothing_to_look_for_is_on_no_page (self) -> None:
		"""Not on every one, which is what an empty list of parts used to mean."""
		assert tool.readings("...") == []
		assert not tool.carried("anything at all", tool.readings("..."))


class TestSquareBracketsWhereTheCheckLooks:

	"""The two readings, asked of documents on disk through `check()` itself.

	Tested by calling `readings()` alone, each place the check looks for a passage could
	go back to the one reading and no test would say so.
	"""

	GUIDE = "Bend Range + [ 1 Note...12 Note] If the Slider is set to PITCH BEND it bends.\n"

	def check (
			self,
			tmp_path: pathlib.Path,
			capsys: pytest.CaptureFixture[str],
			prose: str,
			paged: tuple[str, ...] = ()) -> tuple[typing.Any, str]:

		"""The other class's definition and library, with a guide that prints a bracket."""

		harness = TestCheckingAPlaceAgainstDocumentsOnDisk()
		harness.GUIDE = self.GUIDE

		return harness.check(tmp_path, capsys, prose, paged = paged)

	def test_on_a_page (self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, said = self.check(tmp_path, capsys,
			'Its range is "[1 Note...12 Note]" (guide p. 1) and not "[1 Note...24 Note]" (guide p. 1).',
			paged = ("guide",))

		assert (tally.passed, tally.missing) == (1, 1)
		assert "NOT ON p. 1: [1 Note...24 Note]" in said
		assert "too little remains to look for" in said

	def test_in_a_named_source (self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, said = self.check(tmp_path, capsys,
			'Its range is "[1 Note...12 Note]" (guide) and not "[1 Note...24 Note]" (guide).')

		assert (tally.passed, tally.missing) == (1, 1)
		assert "NOT IN guide: [1 Note...24 Note]" in said

	def test_by_a_number_alone (self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		tally, said = self.check(tmp_path, capsys,
			'Its range is "[1 Note...12 Note]" (15.6) and not "[1 Note...24 Note]" (15.6).')

		assert (tally.passed, tally.missing) == (1, 1)
		assert "IN NO DOCUMENT CITED, located (15.6): [1 Note...24 Note]" in said

	def test_found_as_printed_in_one_document_it_is_not_called_adapted_for_another (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The guide prints the brackets, and the notes hold the passage only with them left out."""
		harness = TestCheckingAPlaceAgainstDocumentsOnDisk()
		harness.GUIDE = self.GUIDE
		harness.NOTES = "Bend Range + If the Slider is set to anything else it does not.\n"
		tally, said = harness.check(tmp_path, capsys,
			'It says "Bend Range + [1 Note...12 Note] If the Slider is set" (15.6).')

		assert (tally.passed, tally.adapted) == (1, 0)
		assert "(15.6) in guide, os_updates" in said

	def test_what_only_the_second_extractor_finds_on_a_page_is_called_adapted_too (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
		"""The first reading of the page has neither form, and the second has the adapted one."""
		monkeypatch.setattr(tool, "read_again", lambda path, page: "The slider makes it bend by a wider range.")
		tally, said = self.check(tmp_path, capsys,
			'It says "makes it bend[s] by a wider range" (guide p. 1).', paged = ("guide",))

		assert (tally.passed, tally.disagreed, tally.adapted) == (1, 1, 1)
		assert "guide p. 1: makes it bend[s] by a wider range" in said

	def test_a_passage_found_only_with_its_brackets_left_out_is_named (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Right for a word the file adapted, and no check at all of a bracket the maker prints."""
		tally, said = self.check(tmp_path / "paged", capsys,
			'It says "Bend Range + [1 Note...24 Note] If the Slider is set" (guide p. 1).',
			paged = ("guide",))

		assert (tally.passed, tally.missing, tally.adapted) == (1, 0, 1)
		assert "found only with what is in their square brackets left out" in said
		assert "guide p. 1: Bend Range + [1 Note...24 Note] If the Slider is set" in said
		assert tool.faults(tally) == 0, "the weaker check is not a fault"

		tally, said = self.check(tmp_path / "named", capsys,
			'It says "Bend Range + [1 Note...24 Note] If the Slider is set" (guide).')

		assert (tally.passed, tally.adapted) == (1, 1)

		tally, said = self.check(tmp_path / "numbered", capsys,
			'It says "Bend Range + [1 Note...24 Note] If the Slider is set" (15.6).')

		assert (tally.passed, tally.adapted) == (1, 1)
		assert "(15.6) in guide: Bend Range + [1 Note...24 Note] If the Slider is set" in said

	def test_the_line_about_brackets_is_said_only_of_a_pair_that_is_looked_for (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""The maker's own cross-reference is folded out first, and a bracket never closed is a character."""
		tally, said = self.check(tmp_path, capsys,
			'It says "sending the unit a MIDI [p.112] Start command now" (guide p. 1) and'
			' "the range is [1 Note and upward" (guide p. 1).', paged = ("guide",))

		assert tally.missing == 2
		assert "its square brackets were looked for" not in said


class TestEveryShapeIsFoundByPairingTheMarks:

	"""A page and a bare key were found by a pattern run over the whole file, and a place by pairing.

	So the four shapes disagreed about what a passage is.  The pattern stopped at a curly
	mark inside a passage, looked inside backticks, and took the prose between two
	quotations for a third.  All four read `paired()` now.
	"""

	KEYS = ("guide", "os_updates")

	def test_a_curly_mark_inside_a_passage_is_part_of_it (self) -> None:
		"""Twelve quotations in six definitions were counted as located and checked by nothing."""
		body = 'source: >-\n  It says "Works the same as “all notes off.”" (reference p. 60).\n'

		assert tool.quotations(body) == [("Works the same as “all notes off.”", "reference", [60])]
		assert tool.uncovered(body, self.KEYS) == ([], [])

		body = 'source: >-\n  It says "available in your “my waldorf” account" (guide).\n'

		assert tool.named_quotations(body, self.KEYS) == [
			("available in your “my waldorf” account", "guide")]

	def test_a_backticked_example_is_code_whatever_locator_it_shows (self) -> None:
		"""The guide says the checker reads past a backticked span, and two shapes did not."""
		body = (
			"source: >-\n"
			"  The form is `\"the maker's own sentence\" (p. 4)` or, for a page with no pages,\n"
			"  `\"the maker's own sentence\" (guide)`.\n")

		assert tool.quotations(body) == []
		assert tool.named_quotations(body, self.KEYS) == []
		assert tool.unreadable_locators(body) == []
		assert tool.uncovered(body, self.KEYS) == ([], [])

	def test_prose_between_two_quotations_is_not_a_quotation_for_a_page_or_a_key_either (self) -> None:
		"""The second passage begins with a bracket that reads as a locator for the prose before it."""
		for opening in ("(p. 4) is where it starts", "(guide) is what it is called"):
			body = (
				"source: >-\n"
				'  It says "no sync is transmitted from the unit" and then the heading\n'
				f'  "{opening}" comes next.\n')

			assert tool.quotations(body) == [], opening
			assert tool.named_quotations(body, self.KEYS) == [], opening
			assert tool.uncovered(body, self.KEYS)[0] == [
				"no sync is transmitted from the unit", opening], opening

	def test_spaces_inside_the_brackets_are_not_part_of_a_key (self) -> None:
		body = 'source: >-\n  It says "a long enough phrase here" ( guide ).\n'

		assert tool.named_quotations(body, self.KEYS) == [("a long enough phrase here", "guide")]

	def test_one_backtick_left_open_pairs_nothing (self) -> None:
		body = (
			"source: >-\n"
			'  The `Sync setting is on, and it says "a long enough phrase here" (p. 4) and\n'
			'  "another long enough phrase" (guide).\n')

		assert tool.odd_backticks(body)
		assert tool.paired(body) is None
		assert tool.quotations(body) == []
		assert tool.named_quotations(body, self.KEYS) == []

	def test_a_curly_mark_outside_every_passage_is_reported_whatever_follows_it (self) -> None:
		"""A locator, a misnamed key, a passage under the floor, a curly pair inside a curly pair.

		The first form of this looked for a curly passage with a locator it could read after
		it, and passed the other three.
		"""
		for words, marks in (
				("It says “a long enough phrase here” (p. 4).", 2),
				("It says “a long enough phrase here” (chart).", 2),
				("It says “Sync mode” (guide).", 2),
				("It says “no sync is “transmitted” from the unit” (guide).", 4),
				("It says “a long enough phrase here” and no more.", 2)):
			body = f"source: >-\n  {words}\n"

			assert tool.quotations(body) == [], words
			assert len(tool.curly_outside(body)) == marks, words

	def test_a_curly_mark_inside_a_passage_or_a_code_span_is_left_alone (self) -> None:
		for words in (
				'It says "the “a long enough phrase here” (guide) of it" (p. 4).',
				"The form `“a long enough phrase here” (p. 4)` is not read."):
			assert tool.curly_outside(f"source: >-\n  {words}\n") == [], words

	def test_a_curly_passage_is_not_given_the_locator_of_the_passage_after_it (self) -> None:
		"""The straight passage was blanked with spaces, and a locator is looked for across spaces."""
		body = 'source: >-\n  The heading “MIDI Implementation” "no sync is transmitted" (guide).\n'

		assert tool.named_quotations(body, self.KEYS) == [("no sync is transmitted", "guide")]
		assert len(tool.curly_outside(body)) == 2
		assert all("“MIDI Implementation”" in words for words in tool.curly_outside(body))

	def test_a_passage_that_looks_like_the_prose_between_two_quotations (self) -> None:
		"""It begins or ends with a space, or is empty: the marks around it do not belong together."""
		nested = 'source: >-\n  It says "set this to "ON" or "P-Dump"" (p. 55) and no more.\n'

		assert tool.mispaired(nested) == [("set this to ", None), (" or ", None), ("", "p. 55")]

		stray = ('source: >-\n  The rear has a 1/4" jack. It says "words that are quoted"'
			' (guide). Beside it is a 1/8" jack.\n')

		assert [passage for passage, _ in tool.mispaired(stray)] == [
			" jack. It says ", " (guide). Beside it is a 1/8"]

		sound = 'source: >-\n  It says "set this to \'ON\' or \'P-Dump\'" (p. 55) and no more.\n'

		assert tool.mispaired(sound) == []
		assert tool.quotations(sound) == [("set this to 'ON' or 'P-Dump'", None, [55])]

	def test_a_quotation_with_its_locator_inside_backticks_is_seen (self) -> None:
		"""Which is what two backticks left open make of a real one."""
		body = ('source: >-\n  The `Sync setting. It says "words that are quoted from it"'
			' (guide). Then the `Clock setting.\n')

		assert not tool.odd_backticks(body)
		assert tool.named_quotations(body, self.KEYS) == []
		assert tool.hidden(body, self.KEYS) == [("words that are quoted from it", "guide")]

		# A passage in backticks that quotes nothing has no locator, and is passed over.
		for words in ('The field is `"System Exclusive"` here.',
				'It shows `firmware: "#246"` (our reading).',
				'It shows `"Cutoff" (p. 4)`, which is under the floor.'):
			assert tool.hidden(f"source: >-\n  {words}\n", self.KEYS) == [], words

	def test_a_code_span_in_or_before_the_brackets (self) -> None:
		"""In a page citation it leaves a locator nobody can read; before the brackets it parts them."""
		body = 'source: >-\n  It says "a long enough phrase here" (`guide` p. 1).\n'

		assert tool.quotations(body) == []
		assert tool.unreadable_locators(body) == [("a long enough phrase here", "`...` p. 1")]

		body = 'source: >-\n  It says "a long enough phrase here" `SYNC` (guide).\n'

		assert tool.named_quotations(body, self.KEYS) == []
		assert tool.uncovered(body, self.KEYS)[0] == ["a long enough phrase here"]

	def test_where_the_marks_fail_to_pair_is_named_by_its_line (self) -> None:
		body = (
			"definition: 1\n"
			"source: >-\n"
			'  The first paragraph says "this is quoted here" (p. 4).\n'
			"\n"
			'  The second has a `stray tick and "another quotation" (p. 5).\n'
			"controls:\n"
			"  one:\n"
			'    # A comment with an unclosed " mark in it.\n'
			"    cc: 70\n")

		assert tool.odd_places(body) == [(5, "backticks"), (8, "quote marks")]

	def test_a_stray_mark_in_each_of_two_paragraphs_is_two_faults_and_not_none (self) -> None:
		"""Counted over the whole file they came to an even number, and paired with each other."""
		body = 'source: >-\n  A 19" rack unit, which says "this is quoted here" (p. 4).\n\n  And a 3.5" disk.\n'

		assert tool.odd_places(body) == [(2, "quote marks"), (4, "quote marks")]
		assert tool.odd_quote_marks(body) and not tool.odd_backticks(body)
		assert tool.paired(body) is None

		body = "source: >-\n  The `Sync setting is on.\n\n  And the `Clock one is off.\n"

		assert tool.odd_places(body) == [(2, "backticks"), (4, "backticks")]
		assert tool.odd_backticks(body) and tool.paired(body) is None

	def test_a_passage_that_begins_with_a_bracket_is_not_the_prose_after_a_quotation (self) -> None:
		"""Only the emphasis closing before the brackets is the sign, and these have none."""
		for passage in ("(10.4) Sync and tempo", "(v2.1) adds a wrap setting", "(section 4) of the guide",
				"(os_updates, #243) reads", "(p. 4) is where it starts", "(guide) is what it is called",
				"(1.00-128.00) in steps", "(channel) is fixed"):
			body = f'source: >-\n  The maker writes "{passage}" and no more.\n'

			assert tool.mispaired(body, self.KEYS) == [], passage

		body = 'source: >-\n  A 19"-wide unit. It says **"the maker\'s words"** (guide). Its disk is 3.5".\n'

		assert tool.mispaired(body, self.KEYS) == [("** (guide). Its disk is 3.5", None)]
		assert tool.mispaired(body.replace("(guide)", "(our reading)"), self.KEYS) == []

		# One asterisk or an underscore closes an emphasis as two asterisks do.
		for mark in ("*", "_", "__"):
			single = body.replace("**", mark)

			assert tool.mispaired(single, self.KEYS) == [(f"{mark} (guide). Its disk is 3.5", None)], mark

	# What other definitions call a document, for the tests below.  `zzdoc` is nobody's, so
	# that these do not pass by leaning on the corpus.
	ELSEWHERE = ("guide", "os_updates", "manual", "chart", "midi_impl", "reference", "addendum", "zzdoc")

	def test_a_word_that_is_a_key_in_another_definition_is_a_source_this_one_has_not_got (self) -> None:
		"""Alone, or before a comma, or before a page: the writer has the wrong document in mind."""
		for locator, word in (("chart", "chart"), ("midi_impl", "midi_impl"), ("reference, 2", "reference"),
				("addendum, as printed", "addendum"), ("manual p. 3", "manual"), ("zzdoc", "zzdoc"),
				("zzdoc, 2", "zzdoc")):
			body = f'source: >-\n  It says "a long enough phrase here" ({locator}).\n'

			assert tool.misnamed_sources(body, self.KEYS, self.ELSEWHERE) \
				== [("a long enough phrase here", word)], locator
			assert tool.uncovered(body, self.KEYS, vocabulary = self.ELSEWHERE) == ([], []), locator

	def test_before_a_page_any_name_that_is_not_the_definition_s_is_refused (self) -> None:
		"""A page is a locator whatever is before it, so there the name need be nobody's key."""
		body = 'source: >-\n  It says "a long enough phrase here" (handbook p. 3).\n'

		assert tool.misnamed_sources(body, self.KEYS, self.ELSEWHERE) == [
			("a long enough phrase here", "handbook")]

	def test_an_aside_is_nobodys_key (self) -> None:
		"""Not by its shape, and not by its likeness to a key: a tool that failed on it is not believed."""
		for aside in ("our own words", "sic, twice", "guide paraphrased", "16", "Chart", "MIDI",
				"release notes, 1.4.1", "notes, as printed", "sic", "default", "v2", "cc74",
				"emphasis", "section4", "filter_cutoff", "manually", "charted", "Handbook",
				"os_update, #243", "manaul"):
			body = f'source: >-\n  It says "a long enough phrase here" ({aside}).\n'

			assert tool.misnamed_sources(body, self.KEYS, self.ELSEWHERE) == [], aside
			assert tool.uncovered(body, self.KEYS, vocabulary = self.ELSEWHERE)[0] \
				== ["a long enough phrase here"], aside

	def test_the_words_a_caller_gives_are_the_words_asked_of (self) -> None:
		"""`zzdoc` is a document's name only where a caller says so, and `chart` only where one does not."""
		body = 'source: >-\n  It says "a long enough phrase here" (zzdoc).\n'

		assert tool.misnamed_sources(body, self.KEYS, ("zzdoc",)) == [("a long enough phrase here", "zzdoc")]
		assert tool.uncovered(body, self.KEYS, vocabulary = ("zzdoc",)) == ([], [])
		assert tool.misnamed_sources(body, self.KEYS) == []
		assert tool.uncovered(body, self.KEYS) == (["a long enough phrase here"], [])

		body = 'source: >-\n  It says "a long enough phrase here" (chart).\n'

		assert tool.misnamed_sources(body, self.KEYS, ("zzdoc",)) == []
		assert tool.uncovered(body, self.KEYS, vocabulary = ("zzdoc",)) == (["a long enough phrase here"], [])

	def test_one_of_its_own_keys_in_other_capitals_is_a_source_it_has_not_got (self) -> None:
		"""`(Guide)` passed as an aside, so a capital got round the rule that pages are cited."""
		for locator, word in (("Guide", "Guide"), ("GUIDE", "GUIDE"), ("Os_Updates, #243", "Os_Updates")):
			body = f'source: >-\n  It says "a long enough phrase here" ({locator}).\n'

			assert tool.misnamed_sources(body, self.KEYS) == [("a long enough phrase here", word)], locator
			assert tool.uncovered(body, self.KEYS) == ([], []), locator

	def test_a_key_that_is_an_ordinary_word_may_be_said_in_capitals (self) -> None:
		"""`(MIDI)` after a quotation is an aside, in the two definitions keyed `midi` as in any other."""
		keys = ("midi", "sysex", "usb", "manual")

		for aside in ("MIDI", "SysEx", "USB"):
			body = f'source: >-\n  The panel reads "Local Control Off" ({aside}) and nothing more.\n'

			assert tool.misnamed_sources(body, keys) == [], aside
			assert tool.uncovered(body, keys)[0] == ["Local Control Off"], aside

		body = 'source: >-\n  The panel reads "Local Control Off" (Manual) and nothing more.\n'

		assert tool.misnamed_sources(body, keys) == [("Local Control Off", "Manual")]

	def test_the_words_of_one_piece_are_the_nine_the_guide_gives (self) -> None:
		"""The list is the rule, so the guide gives the same words and says how many there are."""
		guide = pathlib.Path(__file__).parent.parent / "docs" / "adding-an-instrument.md"
		said = " ".join(guide.read_text(encoding = "utf-8").split())
		listed = said.split("one of nine words that name a document and little else: ")[1].split(". ")[0]
		words = listed.split("`")[1::2]

		assert len(words) == 9
		assert set(words) == tool.DOCUMENT_WORDS

	def test_the_keys_asked_of_are_the_bundled_definitions_own (self) -> None:
		"""Read from the corpus where a caller gives none: `chart` and `manual` are among them."""
		assert {"manual", "chart", "midi_impl", "release_notes"} <= tool.corpus_keys()
		assert "sic" not in tool.corpus_keys()

		# The key of a document with no pages is a document's name as much as a manual's is.
		assert {"downloads_page", "product_page"} <= tool.corpus_keys()

		# **The words of one piece are a list in the tool, and each is some definition's key**,
		# so that the list is not a guess at what a document is called.
		held = {key for name in pymidiinstrumentdefs.available()
			for key in pymidiinstrumentdefs.load(name).sources or {}}

		assert tool.DOCUMENT_WORDS <= held
		assert {key for key in held if "_" in key} | tool.DOCUMENT_WORDS == tool.corpus_keys()

		# One definition is enough for a key with an underscore in it, which is nobody's word.
		assert "chart_article" in tool.corpus_keys()

		# **And an ordinary word is not among them, however many definitions use it for a key.**
		for word in ("midi", "pdf", "system", "keyboard", "usb", "update", "updates", "support", "downloads"):
			assert word not in tool.corpus_keys(), word

			body = f'source: >-\n  The panel reads "Local Control Off" ({word}) and nothing more.\n'

			assert tool.misnamed_sources(body, self.KEYS) == [], word

		body = 'source: >-\n  It says "a long enough phrase here" (chart).\n'

		assert tool.misnamed_sources(body, self.KEYS) == [("a long enough phrase here", "chart")]

	def test_a_key_the_definition_has_is_not_a_stranger (self) -> None:
		body = (
			"source: >-\n"
			'  It says "a long enough phrase here" (guide), "and another of them" (guide p. 4)\n'
			'  and "a third long enough" (os_updates, #243).\n')

		assert tool.misnamed_sources(body, self.KEYS, self.ELSEWHERE) == []

	def test_a_page_after_a_key_and_a_comma_is_a_page_citation_and_not_refused (self) -> None:
		"""`(guide, p. 42)` cites a page with a comma the paged form allows."""
		body = 'source: >-\n  It says "a long enough phrase here" (guide, p. 42).\n'

		assert tool.unpaged_quotations(body, self.KEYS, {"guide"}) == []
		assert tool.quotations(body) == [("a long enough phrase here", "guide", [42])]

	def test_a_bracket_inside_backticks_that_is_no_locator_hides_nothing (self) -> None:
		body = 'source: >-\n  The field is `"System Exclusive message" (our reading)` here.\n'

		assert tool.hidden(body, self.KEYS) == []

	def test_a_quote_mark_inside_a_code_span_makes_no_paragraph_odd (self) -> None:
		body = 'source: >-\n  The rack is `19"` wide and says "this is quoted here" (p. 4).\n'

		assert tool.odd_places(body) == []
		assert not tool.odd_quote_marks(body)

	def test_a_stranger_after_a_short_passage_is_not_a_locator_the_floor_excluded (self) -> None:
		"""That figure is for a locator this tool would have read."""
		body = 'source: >-\n  It is called "Cutoff" (chart) here.\n'

		assert tool.uncovered(body, self.KEYS, vocabulary = self.ELSEWHERE) == ([], [])
		assert tool.misnamed_sources(body, self.KEYS, self.ELSEWHERE) == []


class TestWhereALinesCommentBegins:

	"""A `#` begins a comment only after white space and outside a value, and YAML says what a value is.

	Counting double quote marks before it was the whole rule, so a double mark inside a
	single-quoted value read as opening a string and lost the comment after it - and a `#`
	inside such a value read as a comment, and put the value's own mark into the prose.
	That lone mark made the count odd, which now fails a run.  Two scanners of this tool's
	own followed, and each read some YAML otherwise than YAML does.  PyYAML's is asked now.
	"""

	@staticmethod
	def comment (line: str) -> str | None:

		"""The comment of a file of one line, or nothing where it has none."""

		starts = tool.comment_starts(line)

		return line[starts[1]:] if 1 in starts else None

	def test_the_ordinary_comment (self) -> None:
		assert tool.comment_starts("    cc: 70  # the filter") == {1: 12}
		assert tool.comment_starts("# a whole line") == {1: 0}
		assert tool.comment_starts("    cc: 70") == {}
		assert tool.comment_starts("one: 1  # first\ntwo: 2\nthree: 3 # third\n") == {1: 8, 3: 9}

	def test_a_hash_inside_a_value_is_not_one (self) -> None:
		for line in ('    label: "Playback param #1"', "    label: CC#7", '    firmware: "#246"',
				"    title: 'Guide #2 for the 19\" rack'", "    title: 'Rock''n #1 hits'"):
			assert self.comment(line) is None, line

	def test_a_tab_before_it_is_white_space_too (self) -> None:
		assert self.comment("cc: 70\t# the filter") == "# the filter"

	def test_it_needs_no_white_space_where_yaml_asks_for_none (self) -> None:
		"""PyYAML takes a `#` straight after a closing quote mark or bracket for a comment."""
		assert self.comment('title: "The guide"# and its comment') == "# and its comment"
		assert self.comment("list: [1, 2]# and its comment") == "# and its comment"

		# Inside a plain value it is a character of the value, white space or none.
		assert self.comment("label: CC#7") is None

	def test_a_tag_or_an_anchor_before_a_value_moves_nothing (self) -> None:
		assert self.comment("title: &guide The guide   # the comment") == "# the comment"
		assert self.comment('title: !!str "The guide # second edition"   # the comment') == "# the comment"

	def test_a_comment_after_a_single_quoted_value_with_a_double_mark_in_it (self) -> None:
		line = "    title: 'The 19\" guide'   # \"words of the maker's\" (guide)"

		assert self.comment(line) == "# \"words of the maker's\" (guide)"

	def test_an_apostrophe_opens_nothing (self) -> None:
		line = "    label: Key's X  # the maker's own name"

		assert self.comment(line) == "# the maker's own name"

	def test_an_escaped_mark_inside_a_double_quoted_value (self) -> None:
		"""One escaped mark, so that the count of marks is odd and only the escape explains it."""
		line = '    label: "a \\"quoted word #1"  # and the comment'

		assert self.comment(line) == "# and the comment"

	def test_a_mark_inside_plain_text_opens_nothing (self) -> None:
		"""A quote mark opens a value only where a value begins, whichever kind it is."""
		for line in ("    title: Hits of the '80s, '90s and beyond   # the comment",
				'    title: The 19" rack guide   # the comment',
				"    - rock 'n' roll, 'til dawn   # the comment"):
			assert self.comment(line) == "# the comment", line

	def test_a_mark_that_begins_a_value_opens_it_wherever_a_value_can_begin (self) -> None:
		for line in ("    title: 'a #1 hit'", "    - 'a #1 hit'", "    - - \"a #1 hit\"",
				"    one: {label: 'a #1 hit', cc: 1}", "    list: ['a #1', \"b #2\"]",
				"'a #1 hit': first"):
			assert self.comment(line) is None, line

	def test_a_bracket_in_plain_text_opens_no_collection (self) -> None:
		line = "    label: Level [dB, 'peak   # the comment"

		assert self.comment(line) == "# the comment"

	def test_what_yaml_reads_as_one_value_holds_no_comment (self) -> None:
		"""A flow mapping with no space after its colon, and a tag before a quoted value."""
		for line in ('k: {"a":"b # c"}', 'title: !!str "The guide # second edition"'):
			assert self.comment(line) is None, line

		assert self.comment('k: {"a":"b # c"}  # and a real one') == "# and a real one"

	def test_a_quoted_value_carried_over_a_line_keeps_its_hash (self) -> None:
		"""Read a line at a time, the second line was a comment holding one quote mark."""
		body = (
			"sources:\n"
			"  guide:\n"
			'    title: "A guide to the unit and to\n'
			'      parameter #2 of it"\n'
			"    # and a real comment\n"
			"source: >-\n"
			'  It says "no sync is transmitted from the unit" (guide).')

		assert tool.prose_lines(body) == [
			(5, "# and a real comment"), (7, '  It says "no sync is transmitted from the unit" (guide).')]
		assert not tool.odd_quote_marks(body)

	def test_a_plain_value_carried_over_a_line_opens_nothing_with_its_apostrophe (self) -> None:
		"""It was taken for the opening of a quoted value, and every comment after it was lost."""
		body = (
			"sources:\n"
			"  guide:\n"
			"    title: Songs to play from dusk\n"
			"      'til dawn on the unit\n"
			'# The guide says "words that are in neither of them" (guide).\n'
			"midi: none  # and it's said here too\n")

		assert tool.prose_lines(body) == [
			(5, '# The guide says "words that are in neither of them" (guide).'),
			(6, "# and it's said here too")]

	def test_a_block_that_is_not_the_account_is_a_value_and_not_prose (self) -> None:
		"""Its `#` and its inch mark are the title's own, and the comment after it is found."""
		body = (
			"sources:\n"
			"  guide:\n"
			"    title: >-\n"
			'      The guide to param #1 and the 19" rack\n'
			"    # and a real comment\n"
			"    source: >-\n"
			'      Not the account either, for all its name, with a 3.5" disk # in it\n'
			"midi: none  # the last\n")

		assert tool.prose_lines(body) == [(5, "# and a real comment"), (8, "# the last")]
		assert not tool.odd_quote_marks(body)

	def test_a_line_break_that_only_yaml_counts_puts_no_later_comment_out_of_place (self) -> None:
		"""YAML ends a line at three characters this tool's split does not, and counts its lines so.

		Placed by line, every comment after one of them was judged against the line above,
		and one whose column fell inside a value there was lost.
		"""
		for odd in ("\u2028", "\u2029", "\u0085"):
			body = (
				"sources:\n"
				"  guide:\n"
				f'    title: "The guide{odd}for the unit"\n'
				'    # The guide says "words that are in neither of them" (guide).\n')

			assert tool.prose_lines(body) == [
				(4, '# The guide says "words that are in neither of them" (guide).')], repr(odd)

	def test_a_byte_order_mark_is_no_part_of_the_first_line (self) -> None:
		body = '\ufeff# The guide says "this is quoted here" (p. 4).\nmidi: none  # and a second\n'

		assert tool.comment_starts(body) == {1: 1, 2: 12}
		assert tool.prose_lines(body) == [
			(1, '# The guide says "this is quoted here" (p. 4).'), (2, "# and a second")]

	def test_a_byte_order_mark_is_taken_off_before_the_tokens_are_placed (self) -> None:
		"""PyYAML's two scanners count the mark differently, and a token one place out is a wrong edge.

		`ab#` is one plain value, whose last character is the `#`.  Placed one character
		early, the value ends before it and the `#` reads as a comment.
		"""
		assert yaml.safe_load("\ufeffkey: ab#\n") == {"key": "ab#"}
		assert tool.comment_starts("\ufeffkey: ab#\n") == {}
		assert tool.comment_starts("\ufeffkey: ab# # said\n") == {1: 10}

	def test_a_comment_after_a_block_s_indicator_is_a_comment (self) -> None:
		"""The block begins on the next line, and what follows the indicator is not in it."""
		for indicator in (">-", ">", "|", "|+"):
			body = (
				"sources:\n"
				"  guide:\n"
				f'    title: {indicator}  # The guide says "this is quoted here" (p. 4).\n'
				'      The guide to param #1\n'
				"    url: x\n")

			assert tool.prose_lines(body) == [
				(3, '# The guide says "this is quoted here" (p. 4).')], indicator

	def test_a_block_s_indicator_line_ends_where_yaml_ends_a_line (self) -> None:
		"""YAML ends a line at three characters a file's own lines do not, and a block begins after one."""
		for end in ("\u2028", "\u2029", "\x85"):
			body = f'title: |{end}  The guide to param #1 and a 19" rack\n'

			assert yaml.safe_load(body) == {"title": 'The guide to param #1 and a 19" rack\n'}, repr(end)
			assert tool.comment_starts(body) == {}, repr(end)

	def test_a_flow_collection_carried_over_a_line (self) -> None:
		body = "controls:\n  one: {label: 'a #1 hit',\n    note: 'b #2'}   # the comment\n"

		assert tool.prose_lines(body) == [(3, "# the comment")]

	def test_a_file_that_is_not_yaml_says_so (self) -> None:
		"""Nothing is guessed about one: the error is PyYAML's own."""
		with pytest.raises(yaml.YAMLError):
			tool.prose_lines("one: {label: 'never closed\n")

	def test_a_lone_mark_in_a_field_value_no_longer_fails_a_correct_file (self) -> None:
		body = (
			"sources:\n"
			"  guide:\n"
			"    title: 'Guide #2 for the 19\" rack'\n"
			"source: >-\n"
			'  It says "no sync is transmitted from the unit" (guide).\n')

		assert not tool.odd_quote_marks(body)
		assert tool.named_quotations(body, ("guide",)) == [("no sync is transmitted from the unit", "guide")]


class TestEveryPrintedPageADocumentHas:

	"""`where()` names the pages a passage is on, and walked one printed page for each sheet.

	A document whose first sheet is printed page 3 has printed pages past its number of
	sheets, so its last two were never reached and a passage on one was said to be on no
	page.  Four sources in the corpus are numbered so.
	"""

	def document (self, offset: int) -> typing.Any:
		source = types.SimpleNamespace(page_offset = offset, page_runs = (), pages_per_sheet = 1,
			paginated = True, file_page = lambda printed: printed + offset)

		return tool.Document("guide", pathlib.Path("guide.pdf"), source,
			["the first sheet", "the second sheet", "the last sheet"])

	def test_a_document_numbered_from_three (self) -> None:
		document = self.document(-2)

		assert document.where(tool.readings("the first sheet")) == [3]
		assert document.where(tool.readings("the last sheet")) == [5]

	def test_a_document_with_unnumbered_sheets_before_page_one (self) -> None:
		document = self.document(2)

		assert document.where(tool.readings("the last sheet")) == [1]
		assert document.where(tool.readings("the first sheet")) == []

	def test_two_printed_pages_to_a_sheet_are_both_named (self) -> None:
		source = types.SimpleNamespace(page_offset = 0, page_runs = (), pages_per_sheet = 2,
			paginated = True, file_page = lambda printed: (printed + 1) // 2)
		document = tool.Document("guide", pathlib.Path("guide.pdf"), source,
			["the first sheet", "the second sheet"])

		assert document.where(tool.readings("the second sheet")) == [3, 4]

	def test_a_run_whose_offset_falls_below_nought_reaches_the_last_sheet (self) -> None:
		"""The first run is level with the file and the second two behind it."""
		runs = (types.SimpleNamespace(from_printed = 1, offset = 0),
			types.SimpleNamespace(from_printed = 4, offset = -2))
		source = types.SimpleNamespace(page_offset = 0, page_runs = runs, pages_per_sheet = 1,
			paginated = True, file_page = lambda printed: printed - 2 if printed >= 4 else printed)
		document = tool.Document("guide", pathlib.Path("guide.pdf"), source,
			["the first sheet", "the second sheet", "the last sheet"])

		assert document.where(tool.readings("the last sheet")) == [3, 5]


class TestWhatARunComesTo:

	"""`summarise()`: what fails a run, and what the last lines say.

	What fails was decided inside `main()`, where no test reached it, so the status could
	go back to counting three faults of ten and every test would still pass.
	"""

	def test_each_fault_fails_the_run_alone (self, capsys: pytest.CaptureFixture[str]) -> None:
		for field in ("missing", "unreadable", "misnamed", "unpaged", "pageless", "curly",
				"mispaired", "hidden", "unpairable", "accountless"):
			assert tool.summarise(["zz/x"], [tool.Tally(**{field: 1})]) == 1, field
			assert "not clean: zz/x" in capsys.readouterr().out, field

	def test_a_fault_in_the_first_definition_fails_a_run_that_ends_clean (
			self, capsys: pytest.CaptureFixture[str]) -> None:
		assert tool.summarise(["zz/x", "zz/y"], [tool.Tally(missing = 1), tool.Tally(passed = 3)]) == 1
		assert "not clean: zz/x\n" in capsys.readouterr().out

	@pytest.mark.parametrize("field, said", [
		("misnamed", "1 quotations name a source their definition does not have: zz/x"),
		("unpaged", "1 quotations cite a document that has pages and give no page"),
		("pageless", "1 quotations cite a page where no source it could be in has pages"),
		("hidden", "1 quotations with a locator stand inside backticks"),
		("mispaired", "1 passage(s) begin or end with a space, are empty, or begin by closing an emphasis"),
		("curly", "1 curly quote mark(s) stand outside every quotation"),
		("unpairable", "1 definition(s) hold quote marks or backticks that do not pair"),
		("adapted", "1 of those that check out were found only with what is in their square brackets"),
		("accountless", "1 definition(s) write their account as something other than a block scalar"),
		("unreadable", "1 quotations across 1 definition(s) have a locator this tool cannot read"),
		("no_locator", "1 passage(s) of 12+ characters are in quotation marks with no locator at all"),
	])
	def test_each_figure_has_its_line_and_names_its_definition (
			self, field: str, said: str, capsys: pytest.CaptureFixture[str]) -> None:
		tool.summarise(["zz/x"], [tool.Tally(**{field: 1})])
		printed = capsys.readouterr().out

		assert said in printed
		assert [line for line in printed.split("\n") if said in line][0].endswith("zz/x")

	def test_the_two_coverage_figures_and_the_last_line_are_always_said (
			self, capsys: pytest.CaptureFixture[str]) -> None:
		"""Each is what lets a hand count be squared with the run, at nought as at any figure."""
		tool.summarise(["zz/x", "zz/y"], [tool.Tally(too_short = 2), tool.Tally(nothing_to_check = 1)])
		printed = capsys.readouterr().out

		assert "2 passage(s) carry a locator and are under 12 characters" in printed
		assert "0 passage(s) of 12+ characters are in quotation marks with no locator at all" in printed
		assert "1 definition(s) quote nothing with a locator" in printed

	def test_what_is_not_a_fault_does_not (self, capsys: pytest.CaptureFixture[str]) -> None:
		tally = tool.Tally(passed = 4, disagreed = 1, adapted = 1, unchecked = 3, partly = 2,
			no_locator = 5, too_short = 1, nothing_to_check = 1)

		assert tool.faults(tally) == 0
		assert tool.summarise(["zz/x"], [tally]) == 0

		said = capsys.readouterr().out

		assert "not clean" not in said
		assert "4 quotations check out across 1 definition(s); 0 are not on the page or in the" \
			" document they cite; 3 could not be checked" in said
		assert "2 more have every clause on the page they cite" in said
		assert "1 of those that check out were found only with what is in their square brackets" \
			" left out" in said
		assert "1 of those that check out were found only by the second extractor" in said

	def test_each_fault_is_named_with_the_definitions_it_is_in (
			self, capsys: pytest.CaptureFixture[str]) -> None:
		status = tool.summarise(["zz/x", "zz/y", "zz/z"],
			[tool.Tally(passed = 1), tool.Tally(unpaged = 2, hidden = 1), tool.Tally(unpaged = 1)])
		said = capsys.readouterr().out

		assert status == 1
		assert "3 quotations cite a document that has pages and give no page, so they were not" \
			" checked: zz/y, zz/z" in said
		assert "1 quotations with a locator stand inside backticks, so they were not checked: zz/y" in said
		assert "not clean: zz/y, zz/z" in said


class TestWhichDocumentsAPageCitationCouldBeFoundIn:

	"""The JUNO-106 is the first definition to hold a scan and a saved web page at once.

	Its manual is a photograph and the checker drops it, which is right; what was left was
	an unpaginated web page, and every "p. 34" in the file was then judged against a
	document with no pages and reported as being on the wrong page. Seven of a maker's own
	sentences came back as mistakes. The DX7 never showed it because a scan is its only
	source, so nothing readable was left and the tool said so.
	"""

	def paged (self, paginated: bool) -> typing.Any:
		"""A source with nothing in it but the one field this question turns on."""
		return tool.Document(
			name = "manual" if paginated else "product_page",
			path = pathlib.Path("/nowhere"),
			source = type("Source", (), {"paginated": paginated, "page_offset": 0, "pages_per_sheet": 1})(),
			pages = ["some text"],
		)

	def test_a_document_with_pages_is_somewhere_to_look (self) -> None:
		"""Which is the ordinary case, and the one every other definition is in."""
		held = [self.paged(True)]

		assert tool.with_pages(held) == held

	def test_a_document_with_no_pages_is_not (self) -> None:
		"""`paginated: false` means there is no page to turn to, so a page citation cannot be in it."""
		assert tool.with_pages([self.paged(False)]) == []

	def test_the_paged_one_is_kept_when_a_definition_holds_both (self) -> None:
		"""A page citation is still checkable, and is still checked, against the one that has pages."""
		paged, unpaged = self.paged(True), self.paged(False)

		assert tool.with_pages([unpaged, paged]) == [paged]

	def test_nothing_to_look_in_is_not_the_same_as_looking_and_failing (self) -> None:
		"""The whole point: with no paged document, the answer is unchecked rather than wrong."""
		assert tool.with_pages([self.paged(False)]) == []


class TestAWordBrokenAtTheEndOfALine:

	"""A typesetter's hyphen is not part of the word, and the text layer keeps it.

	The Analog Rytm MKII's page 21 prints "can be voiced simultaneously with the eight
	physical voices" and breaks the long word across the line, so the text layer gives back
	`simulta-\nneously`. A definition quoting the word the page prints was reported as citing
	the wrong page, which is the one failure that stops this tool's output being read.
	"""

	def test_a_word_broken_across_a_line_is_the_word (self) -> None:
		"""The case that found this, from the page it was found on."""
		page = "can be voiced simulta-\nneously with the eight physical voices"

		assert tool.squash("can be voiced simultaneously") in tool.squash(page)

	def test_a_hyphen_the_maker_meant_still_matches (self) -> None:
		"""Dropping the break on one side only would have broken this, so both sides drop it."""
		assert tool.squash("built-in") in tool.squash("the built-in reverb")
		assert tool.squash("built-in") in tool.squash("the built-\nin reverb")

	def test_a_spaced_hyphen_in_a_sentence_is_not_a_word_boundary (self) -> None:
		"""This corpus writes its own dashes as a spaced hyphen, and quotes manuals that do too."""
		assert tool.squash("one thing - and another") == tool.squash("one thing and another")

	def test_two_different_sentences_are_still_different (self) -> None:
		"""The point of folding anything is to find a quotation, not to find any quotation."""
		assert tool.squash("the instrument sends clock") != tool.squash("the instrument sends start")


class TestAQuotationThatNamesTheDocumentAndThePage:

	"""The locator a definition with several documents needs, and used to be ignored for."""

	# Four documents, which is when naming one starts to matter: "p. 110" alone says
	# nothing about which of them to turn to.
	BODY = (
		"definition: 1\n"
		"source: >-\n"
		'  "the plain form" (p. 4), "the named form" (manual p. 110),\n'
		'  "the named form with a comma" (guide, p. 6), and "a range of them" (manual pp. 7-8).\n'
	)

	def test_a_named_page_is_found_where_it_used_to_be_skipped (self) -> None:
		"""All four shapes are quotations with a page, and all four are checked."""
		found = [quotation for quotation, _, _ in tool.quotations(self.BODY)]

		assert found == [
			"the plain form", "the named form",
			"the named form with a comma", "a range of them"]

	def test_the_document_it_names_comes_back_with_it (self) -> None:
		"""Which is what lets the page be looked for in that document rather than any."""
		found = {quotation: source for quotation, source, _ in tool.quotations(self.BODY)}

		assert found["the plain form"] is None
		assert found["the named form"] == "manual"
		assert found["the named form with a comma"] == "guide"
		assert found["a range of them"] == "manual"

	def test_the_pages_are_read_the_same_either_way (self) -> None:
		"""Naming a document changes where to look, not what to look for."""
		found = {quotation: pages for quotation, _, pages in tool.quotations(self.BODY)}

		assert found["the plain form"] == [4]
		assert found["the named form"] == [110]
		assert found["a range of them"] == [7, 8]

	def test_a_name_alone_is_still_the_other_shape (self) -> None:
		"""A document with no pages is cited by its key and nothing else, which is unchanged."""
		body = 'source: >-\n  "no page to turn to here" (product_page).\n'

		assert tool.quotations(body) == []
		assert tool.named_quotations(body, ["product_page"]) == [
			("no page to turn to here", "product_page")]

	def test_an_ordinary_bracket_after_a_quotation_is_not_a_locator (self) -> None:
		"""The page is what makes it one, so prose in brackets does not become a document."""
		body = 'source: >-\n  "a thing the maker says" (and a remark about it).\n'

		assert tool.quotations(body) == []


class TestALocatorThisToolCannotRead:

	"""A locator that does not parse used to be indistinguishable from no locator at all.

	The rule for a quotation with no locator is to pass over it in silence, so a citation the
	pattern could not read was not checked, was not counted as unchecked, and nothing in the
	tool's output said it existed. **Forty-eight quotations across thirteen definitions were in
	that state**, and reading them where they stood turned up five that were not on the pages
	they cite, three of them quotations saying something the maker had not said.

	So the convention is `(p. N)` or `(key p. N)`, exactly one pair, and every shape below is
	one a writer actually reached for in this corpus. #4475.
	"""

	# The shapes that parsed all along, which must keep parsing.
	GOOD = {
		"p. 42": (None, [42]),
		"pp. 42-43": (None, [42, 43]),
		"p. 42, 44": (None, [42, 44]),
		"guide p. 6": ("guide", [6]),
		"manual, p. 110": ("manual", [110]),
		"user_guide p. 104": ("user_guide", [104]),
	}

	# Every shape that was silently skipped, taken from the definitions that held them.
	BAD = (
		"user guide p. 104",                            # a two-word document name
		"release notes 1.4.0 p. 8",                     # a name carrying a version
		"p. 89 of the guide",                           # the document named after the page
		"fw 5 manual, printed p. 11",                   # both at once
		"p. 35, mode 1",                                # the writer's aside after the page
		"p. 29 lists all six, pp. 29-36 describe them", # two citations and prose
		"notes' p. 4",                                  # an apostrophe in the name
		"p. 2 of the version 2.0 supplement",
		"manual p. 125, reference p. 29",               # two documents, one quotation
		"manual p. 307, p. 1",                          # two pages, and which document is which
	)

	def test_the_shapes_that_parsed_before_still_parse (self) -> None:
		"""The narrowing must not have cost a locator that was already being read."""
		for locator, expected in self.GOOD.items():
			assert tool.read_locator(locator) == expected, locator

	def test_every_shape_that_was_skipped_is_now_refused (self) -> None:
		"""Refused aloud, which is the whole point: it was accepted silently before."""
		for locator in self.BAD:
			assert tool.read_locator(locator) is None, locator

	def test_a_refused_locator_is_reported_against_its_quotation (self) -> None:
		"""Reporting the quotation is what makes the count actionable rather than a number."""
		body = 'source: >-\n  "a sentence worth checking" (user guide p. 104).\n'

		assert tool.unreadable_locators(body) == [
			("a sentence worth checking", "user guide p. 104")]

	def test_a_refused_locator_is_not_counted_as_checked (self) -> None:
		"""It must be in neither figure, or one of them is quietly wrong."""
		body = 'source: >-\n  "a sentence worth checking" (user guide p. 104).\n'

		assert tool.quotations(body) == []

	def test_a_bare_source_key_is_not_a_broken_page_citation (self) -> None:
		"""`(product_page)` cites no page, so it belongs to the other check and not to this one."""
		body = 'source: >-\n  "no page to turn to here" (product_page).\n'

		assert tool.unreadable_locators(body) == []

	def test_prose_in_brackets_is_not_a_broken_page_citation (self) -> None:
		"""Only something page-shaped counts, or every aside becomes a reported failure."""
		body = 'source: >-\n  "a thing the maker says" (and a remark about it).\n'

		assert tool.unreadable_locators(body) == []

	def test_a_locator_folded_over_two_lines_is_read_as_one (self) -> None:
		"""A sweep that forgot this invented a broken locator for every citation that wrapped."""
		body = (
			"controls:\n"
			"  one:\n"
			'    # "a sentence worth checking" (user_guide\n'
			"    # p. 104).\n"
			"    cc: 70\n"
		)

		assert tool.unreadable_locators(body) == []
		assert tool.quotations(body) == [("a sentence worth checking", "user_guide", [104])]


class TestAQuotationThatBeginsWithAParenthesis:

	"""A maker prints value ranges in brackets, so a quotation of one starts with `(`.

	`elektron/model_cycles` quotes "(OFF, 1-127)" and `korg/microkorg2` quotes
	"(NRPN 4, 32...37)". **This is the shape that punishes a pattern which matches any
	parenthesis after a quotation**: the prose in front ends at a closing quote, and twelve or
	more characters counted from *there* run to the quote that opens the real quotation - whose
	next character is the `(` the quotation itself begins with. The engine then pairs prose with
	a value range, finds nothing page-shaped in it, and skips it in silence, taking the real
	quotation with it.

	Two were being lost that way while the count looked complete, which is #4475's own defect
	arriving by a new route, in the fix for it.
	"""

	BODY = (
		"source: >-\n"
		'  The manual names "one thing and another" and both sends are "(OFF, 1-127)" (p. 37).\n'
	)

	def test_the_quotation_after_the_prose_is_still_found (self) -> None:
		"""It is the one the page citation belongs to, so losing it loses the check."""
		assert ("(OFF, 1-127)", None, [37]) in tool.quotations(self.BODY)

	def test_the_prose_before_it_is_not_mistaken_for_a_quotation (self) -> None:
		"""A value range is not a locator, so that pairing must not be made at all."""
		found = [quotation for quotation, _, _ in tool.quotations(self.BODY)]

		assert "both sends are" not in " ".join(found)

	def test_it_is_not_reported_as_an_unreadable_locator_either (self) -> None:
		"""Being refused aloud would be better than silence, and being read is better still."""
		assert tool.unreadable_locators(self.BODY) == []


class TestWhatTheToolDidNotLookAt:

	"""Counting the quotations with no locator, which is the figure that never existed.

	`korg/minilogue` read "5 of 5 quotations are on the page they cite" while holding thirty
	nobody had looked at, because a quotation with no locator is passed over in silence. The
	count is a coverage report rather than a list of faults - see `uncovered()` for why it
	must not fail the run - so these tests are about what it counts and what it must not.
	"""

	BODY = (
		"source: >-\n"
		'  The chart marks it "both ways on every channel" (p. 4), and the panel reads\n'
		'  "Local Control Off" with nowhere given for it.\n'
	)

	def test_the_located_quotation_is_not_in_the_figure (self) -> None:
		"""It was checked, so counting it here would double-count it."""
		unlocated, _ = tool.uncovered(self.BODY, [])

		assert "both ways on every channel" not in unlocated

	def test_the_unlocated_quotation_is (self) -> None:
		"""This is the whole of #4359: it was in no figure at all before."""
		unlocated, _ = tool.uncovered(self.BODY, [])

		assert unlocated == ["Local Control Off"]

	def test_the_prose_between_two_quotations_is_not_counted (self) -> None:
		"""**The mistake this has to avoid, and it has been made twice.**

		A `[^"]{12,}` between two quote characters matches the words between a closing mark
		and the next opening one as readily as a quotation, which gave 49 for a file holding
		35. Pairing in order is what stops it.
		"""
		unlocated, _ = tool.uncovered(self.BODY, [])

		assert not any("and the panel reads" in passage for passage in unlocated)


class TestAQuotedLabelIsNotAQuotation:

	"""A pair of quote marks outside prose is YAML syntax, and `elektron/octatrack` proves it.

	Ninety-nine of its controls carry a label in quote marks, not because the label is quoted
	from anywhere but because this maker writes parameter names with commas and brackets in
	them and a flow mapping cannot hold either bare. A sweep over the whole file reports 113
	unlocated quotations of which 99 are labels, and **a sweep that invents a hundred faults
	on a correct file is one nobody reads twice.**
	"""

	BODY = (
		"source: >-\n"
		'  The manual calls it "a performance macro" (p. 60).\n'
		"sources:\n"
		"  manual:\n"
		'    title: "Octatrack MKII User Manual"\n'
		'    sha256: "0f4e2a"\n'
		"controls:\n"
		'  track_mute: {label: "Track Mute [0]=Unmuted, [1-127]=Muted", cc: 49}\n'
	)

	def test_a_control_label_is_not_reported (self) -> None:
		"""It is a field value, and reporting it would bury the real answer."""
		unlocated, _ = tool.uncovered(self.BODY, [])

		assert not any("Track Mute" in passage for passage in unlocated)

	def test_a_title_and_a_digest_are_not_reported (self) -> None:
		"""Both are quoted because YAML needs them quoted, not because anybody cited them."""
		unlocated, _ = tool.uncovered(self.BODY, [])

		assert not any("Octatrack MKII" in passage for passage in unlocated)
		assert not any("0f4e2a" in passage for passage in unlocated)

	def test_the_account_is_still_read (self) -> None:
		"""Dropping the field values must not drop the prose with them."""
		assert ("a performance macro", None, [60]) in tool.quotations(self.BODY)

	def test_a_comment_inside_the_controls_block_is_still_read (self) -> None:
		"""A comment is prose wherever it sits, and some definitions put one there."""
		body = self.BODY + '  # The guide calls this "the mute behaviour" with no page.\n'
		unlocated, _ = tool.uncovered(body, [])

		assert "the mute behaviour" in unlocated


class TestBackticksAreTheRemedyAndMustWork:

	"""A quoted passage inside backticks is code, and the tool has to say so.

	This is not a nicety. The remedy the tool recommends for a passage that quotes nothing is
	to put it in backticks, so a sweep that went on reporting it afterwards would be telling
	people to do something that does not work. `elektron/octatrack`'s account explains the
	label trap by quoting a label as an example, inside backticks, and that one line was the
	only false positive left in the file once the YAML values were out.
	"""

	def test_a_code_span_is_not_a_quotation (self) -> None:
		"""Otherwise the advice the tool prints contradicts what the tool then does."""
		body = (
			"source: >-\n"
			'  Its controls carry a label in quote marks - `"Track Mute [0]=Unmuted"` - which\n'
			"  is syntax rather than a citation.\n"
		)

		unlocated, _ = tool.uncovered(body, [])

		assert unlocated == []

	def test_a_code_span_broken_across_two_comment_lines_is_still_code (self) -> None:
		"""A comment wraps, and a span can wrap with it exactly as a quotation can."""
		body = (
			"midi:\n"
			'  # The field is written `"a long label that wraps\n'
			'  # across two lines"` and is not quoted from anywhere.\n'
		)

		unlocated, _ = tool.uncovered(body, [])

		assert unlocated == []


class TestAQuotationUnderTheFloor:

	"""The floor is right and its effect was invisible, which stopped any count reconciling.

	`arturia/polybrute_12` had 62 locators in its file when the gate reported 60. The two it
	passed over were `"5-octave"` and the edition `"3.1.0"`, both shorter than twelve
	characters - **a second reason to skip, reported as nothing at all.** An audit that only
	looked for missing locators still would not have reconciled.
	"""

	BODY = (
		"source: >-\n"
		'  A "5-octave" (p. 3) keyboard, and the chart marks it "both ways here" (p. 4).\n'
	)

	def test_the_short_one_is_counted_apart (self) -> None:
		"""It carries a locator, so it is not a missing-locator fault."""
		unlocated, short = tool.uncovered(self.BODY, [])

		assert short == ["5-octave"]
		assert unlocated == []

	def test_the_long_one_is_checked_and_in_neither_figure (self) -> None:
		"""Both figures are about what was not looked at."""
		unlocated, short = tool.uncovered(self.BODY, [])

		assert "both ways here" not in unlocated + short
		assert ("both ways here", None, [4]) in tool.quotations(self.BODY)


class TestMarkupBetweenAQuotationAndItsLocator:

	"""The one silence a writer cannot find by reading their own file carefully.

	The pattern that found a page citation allowed only whitespace between the closing quote
	mark and the locator, so a quotation emphasised in this project's house style - with the
	markers closing before the parenthesis - did not match and was skipped without a word.
	Three definitions were in
	that state; their files were put right and the pattern was not, so the next writer to
	type it would have paid again.
	"""

	def test_bold_markers_before_the_locator_do_not_hide_it (self) -> None:
		"""`"..."** (p. 45)` looks located to a reader and was not."""
		body = 'source: >-\n  The guide reads **"the part parameters"** (p. 45) and nothing else.\n'

		assert ("the part parameters", None, [45]) in tool.quotations(body)

	def test_it_is_not_then_reported_as_having_no_locator (self) -> None:
		"""The two halves of this fix have to agree, or one invents what the other hides."""
		body = 'source: >-\n  The guide reads **"the part parameters"** (p. 45) and nothing else.\n'
		unlocated, _ = tool.uncovered(body, [])

		assert unlocated == []

	def test_a_named_source_is_found_past_the_markers_too (self) -> None:
		"""The pattern for a bare key had the same gap and would have kept it."""
		body = 'source: >-\n  It says **"up to twenty-four voices"** (product_page) plainly.\n'

		assert ("up to twenty-four voices", "product_page") in tool.named_quotations(
			body, ["product_page"])


class TestProseWithAnOddNumberOfQuoteMarks:

	"""Pairing is only sound where the marks pair, so an odd count is said out loud.

	Nought definitions in the corpus are in this state and every one holds an even number of
	straight double quotes, which is why pairing is safe at all. Saying so rather than
	mis-pairing in silence is the point: a silence being read as a clean bill is the fault
	this whole figure exists to close.
	"""

	BODY = 'source: >-\n  It reads "one thing and another (p. 4) with a mark missing.\n'

	def test_it_is_reported_rather_than_mis_paired (self) -> None:
		"""Whatever pairing produced here would be fiction."""
		assert tool.odd_quote_marks(self.BODY) is True

	def test_and_the_figures_say_nothing_for_it (self) -> None:
		"""Better to speak for nothing than to speak wrongly."""
		assert tool.uncovered(self.BODY, []) == ([], [])

	def test_an_even_file_is_not_reported (self) -> None:
		"""The ordinary case, and the corpus is entirely this case."""
		assert tool.odd_quote_marks(
			'source: >-\n  It reads "one thing and another" (p. 4) plainly.\n') is False


class TestATrailingCommentIsProseToo:

	"""**This was the coverage scan's own first bug, and the odd-mark guard is what found it.**

	Keeping only lines that are entirely a comment dropped the comment part of every line
	that also carries a field. `arturia/minifreak` writes
	``programmable: true   # "Bend Range: sets the range of pitch bend messages`` and runs the
	quotation on into the next line, so the opening mark went with the field and the closing
	one was kept — an odd count, which is the only reason anybody looked. A hundred and one
	lines in the corpus are that shape.

	The comment cannot be found by splitting on the first `#`, because a hundred and one of
	them sit inside a quoted value — `CC#7`, `"Playback param #1"`, ``firmware: "#246"``. The
	test is an even number of quote marks in front of it.
	"""

	def test_a_quotation_in_a_trailing_comment_is_read (self) -> None:
		"""Dropping it is the silence this whole figure exists to close."""
		body = (
			"voice:\n"
			'  pitch_bend: true   # "the range of pitch bend messages from MIDI" with no page\n'
		)

		unlocated, _ = tool.uncovered(body, [])

		assert unlocated == ["the range of pitch bend messages from MIDI"]

	def test_a_quotation_running_on_from_a_trailing_comment_pairs (self) -> None:
		"""The MiniFreak's own shape: the marks sit on two different lines."""
		body = (
			"voice:\n"
			'  pitch_bend: true     # "Bend Range: sets the range of pitch bend\n'
			'                       # messages from MIDI, in semitones" (p. 84)\n'
		)

		assert tool.odd_quote_marks(body) is False
		assert ("Bend Range: sets the range of pitch bend messages from MIDI, in semitones",
			None, [84]) in tool.quotations(body)

	def test_a_hash_inside_a_control_label_does_not_make_it_prose (self) -> None:
		"""Otherwise every one of the Octatrack's `param #1` labels comes back as a quotation."""
		body = 'controls:\n  lfo_param_1: {label: "LFO param #1 (Speed 1)", cc: 28}\n'

		unlocated, _ = tool.uncovered(body, [])

		assert unlocated == []

	def test_a_hash_inside_a_quotation_does_not_truncate_it (self) -> None:
		"""Makers write `CC#7`, and the comment starts before it rather than at it."""
		body = '  # The reference reads "Patch Volume reacts to MIDI CC#7 as well" with no page\n'

		unlocated, _ = tool.uncovered(body, [])

		assert unlocated == ["Patch Volume reacts to MIDI CC#7 as well"]

	def test_a_quoted_field_value_with_a_hash_is_not_prose (self) -> None:
		"""`firmware: "#246"` is teenage engineering's own version string, not a citation."""
		body = 'model:\n  firmware: "#246"\n'

		unlocated, short = tool.uncovered(body, [])

		assert unlocated == []
		assert short == []


class TestHowManyCoresTheSweepTakes:

	"""The whole-corpus sweep reads 413 manuals for text, which is why it is worth sharing out.

	Reading a PDF for text saturates a core, so a sweep over every definition would
	otherwise take the machine over for the length of it. These are the rules that decide
	how much of it to use, and the one that matters is the floor: a machine reporting one
	core, or a number asked for that makes no sense, must still check everything rather
	than refuse to start.
	"""

	def test_a_number_asked_for_is_what_is_used (self) -> None:
		"""Passing --jobs is how somebody sharing the machine dials it down."""
		assert tool.cores_to_use(3) == 3

	def test_one_is_allowed_because_it_is_the_reference_path (self) -> None:
		"""--jobs 1 is the single-process code every release so far has run."""
		assert tool.cores_to_use(1) == 1

	def test_zero_and_below_are_floored_rather_than_refused (self) -> None:
		"""A typo in a flag should slow the sweep down, never stop it checking."""
		assert tool.cores_to_use(0) == 1
		assert tool.cores_to_use(-4) == 1

	def test_the_default_leaves_room_to_work (self) -> None:
		"""Two cores are kept free, so a gate run does not take over the machine."""
		assert tool.cores_to_use(None) >= 1
		assert tool.cores_to_use(None) <= max(1, (os.cpu_count() or 1) - 2)
