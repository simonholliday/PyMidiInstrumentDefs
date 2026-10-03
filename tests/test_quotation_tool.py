"""The parts of ``tools/check_quotations.py`` that can be checked without a manual.

The check itself is deliberately not a test, for the same reason the citation check is
not: it reads manufacturers' documents, which are copyrighted and are never committed
here, so in CI it could only ever skip.

What is tested here needs no document at all: reducing two readings of the same words to
the same string, and finding the quotations in a definition. Every rule below is here
because a **correct** quotation failed without it, and a tool that reports a correct
citation as wrong is worse than no tool, because its output stops being read.
"""

import importlib.util
import pathlib
import typing


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
