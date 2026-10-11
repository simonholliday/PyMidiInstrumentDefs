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
import typing

import pytest


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

		# And a key-shaped word this definition has no source for is not one either.
		body = 'source: >-\n  It says "a long enough phrase here" (midi_impl).\n'

		assert tool.named_quotations(body, self.KEYS) == []

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
		of the whole guide while the correctly written `(guide p. 42)` beside it failed.
		"""
		for locator in ("guide, page 42", "guide, 42", "guide, section 4"):
			body = f'source: >-\n  It says "a long enough phrase here" ({locator}).\n'

			assert tool.placed_quotations(body, self.KEYS, paged = {"guide"}) == ([], []), locator
			assert tool.uncovered(body, self.KEYS, paged = {"guide"})[0] \
				== ["a long enough phrase here"], locator

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
			third: bool = False) -> tuple[typing.Any, str]:

		"""Write a definition citing two documents, and check it against those on disk.

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
			f"source: >-\n  {prose}\n\nsources:\n{sources}\n"
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
		assert "which is a weaker check than a page\n" in said

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
		assert "1 more are in no document that could be read, and 1 cited here could not be" in said

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

	def test_a_place_after_the_key_of_a_document_with_pages_is_left_unlocated (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""Not passed on a search of the whole document, and not failed: left where it is seen."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (guide, page 42).', paged = ("guide",))

		assert (tally.passed, tally.missing, tally.no_locator) == (0, 0, 1)
		assert tally.nothing_to_check == 1
		assert "with NO LOCATOR" in said

	def test_marks_that_do_not_pair_are_not_reported_as_nothing_to_check (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A place locator is found by pairing the marks, so with an odd one nobody looked."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (10.4) and then an unclosed " mark.')

		assert (tally.passed, tally.missing, tally.unpairable) == (0, 0, 1)
		assert tally.nothing_to_check == 0
		assert "ODD NUMBER OF QUOTE MARKS" in said
		assert "no locator that names a place and not a page was looked for" in said
		assert "so there is nothing to check" not in said

	def test_unpaired_marks_say_so_beside_a_quotation_that_was_checked (
			self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
		"""A bare key is found by a pattern and still checked; the place beside it is not."""
		tally, said = self.check(tmp_path, capsys,
			'It says "no sync is transmitted from the unit" (guide) and "the family of the'
			' product" (os_updates, #243), and then an unclosed " mark.')

		assert (tally.passed, tally.missing, tally.unpairable) == (1, 0, 1)
		assert "1 of 1 quotations that name a source are in it" in said
		assert "no locator that names a place and not a page was looked for" in said

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

	`arturia/polybrute_12` has 62 locators in its file and the gate reported 60. The two it
	passed over are `"5-octave"` and the edition `"3.1.0"`, both shorter than twelve
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

	`QUOTED` allowed only whitespace between the closing quote mark and the locator, so a
	quotation emphasised in this project's house style - with the markers closing before the
	parenthesis - did not match and was skipped without a word. Three definitions were in
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
		"""`BY_SOURCE` had the same gap and would have kept it."""
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
