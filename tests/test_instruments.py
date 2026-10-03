"""Tests for pymidiinstrumentdefs — reading what a particular model does."""

import collections
import pathlib
import re

import pytest

import pymidiinstrumentdefs


CORPUS: pathlib.Path = pymidiinstrumentdefs.loading.BUNDLED


def bundled () -> list[pathlib.Path]:

	"""Every definition that ships, found where definitions are: in a maker's folder."""

	return sorted(CORPUS.glob("*/*.yaml"))


def write (directory: pathlib.Path, name: str, body: str) -> pathlib.Path:

	"""Put a definition on disk under its name, which is also its path, and return where it went."""

	path = directory / f"{name}.yaml"

	path.parent.mkdir(parents = True, exist_ok = True)
	path.write_text(body, encoding = "utf-8")

	return path


MINIMAL = """
definition: 1
model: {name: Test}
source: A test, written by hand.
"""


class TestBundledCorpus:

	def test_every_bundled_definition_loads (self) -> None:
		"""Nothing ships here that this package cannot read."""
		files = bundled()

		assert files, "the bundled corpus is empty"

		for path in files:
			pymidiinstrumentdefs.load_file(path)

	def test_every_group_a_bundled_definition_uses_has_a_label (self) -> None:
		"""A page heads each table with one, and an identifier is not a thing to show a reader.

		`mod_1` and `bd` are what the TR-8S and the Take 5 made this necessary for.
		"""
		unlabelled = {}

		for name in pymidiinstrumentdefs.available([CORPUS]):
			definition = pymidiinstrumentdefs.load(name, [CORPUS])
			missing = [group for group in definition.grouped_controls() if group and group not in definition.groups]

			if missing:
				unlabelled[name] = missing

		assert unlabelled == {}

	def test_a_label_can_differ_from_the_name_it_labels (self) -> None:
		"""Which is the whole point of having both, and two bundled files rest on it."""
		minifreak = pymidiinstrumentdefs.load("arturia/minifreak", [CORPUS])
		tr8s = pymidiinstrumentdefs.load("roland/tr8s", [CORPUS])

		# the chart's section word is MIDI, which would be a useless group name here
		assert minifreak.groups["controllers"] == "MIDI"

		# Roland expands none of its eleven, so the label is the maker's two letters
		assert tr8s.groups["bd"] == "BD"
		assert list(tr8s.grouped_controls())[0] == "global"

	def test_no_published_paragraph_prints_a_dash_the_site_will_not (self) -> None:
		"""Read as the loader returns it, because that is what a page prints.

		A folded paragraph joins its lines with a space, so a file ending a line
		with "--" shows a reader " -- " that no search of the file can find. Four
		definitions were doing exactly that, and one of them was released.
		"""
		printing = {}

		for name in pymidiinstrumentdefs.available([CORPUS]):
			paragraph = pymidiinstrumentdefs.load(name, [CORPUS]).source or ""
			found = [dash for dash in ("\u2014", " -- ") if dash in paragraph]

			if found:
				printing[name] = found

		assert printing == {}

	def test_the_readme_lists_every_bundled_definition (self) -> None:
		"""Its table says "The bundled definitions", so a missing row makes it untrue.

		Two were missing when this was written - both Moog 37s, added at v0.1.5 and never
		given a row - which nothing would have caught, because the table is prose to every
		other check here.
		"""
		readme = (pathlib.Path(__file__).parent.parent / "README.md").read_text(encoding = "utf-8")

		missing = [name for name in pymidiinstrumentdefs.available([CORPUS])
			if f"`{name}`" not in readme]

		assert missing == []

	def test_a_definition_with_nrpn_controls_says_so_about_the_instrument (self) -> None:
		"""An unset `midi.nrpn` means nobody looked, which is untrue of a file full of NRPNs.

		Three Elektron definitions carried NRPN numbers on most of their controls and left
		the field unset, which told a reader that the question had never been asked. Their
		manuals all answer it in the same sentence, about what the DATA ENTRY knobs send.
		"""
		silent = [name for name in pymidiinstrumentdefs.available([CORPUS])
			if pymidiinstrumentdefs.load(name, [CORPUS]).midi.nrpn is None
			and any(control.nrpn is not None
				for control in pymidiinstrumentdefs.load(name, [CORPUS]).controls.values())]

		assert silent == []

	def test_the_bundled_names (self) -> None:
		"""Every bundled definition, by name, so adding or removing one shows here too."""
		assert pymidiinstrumentdefs.available([CORPUS]) == [
			"akai/mpc_sample",
			"arturia/astrolab",
			"arturia/drumbrute_impact",
			"arturia/microfreak",
			"arturia/minifreak",
			"behringer/model_d",
			"behringer/td_3",
			"dreadbox/typhon",
			"elektron/analog_four",
			"elektron/analog_rytm_mkii",
			"elektron/digitakt",
			"elektron/digitakt_ii",
			"elektron/digitone",
			"elektron/digitone_ii",
			"elektron/model_cycles",
			"elektron/model_samples",
			"elektron/syntakt",
			"expressive_e/osmose",
			"korg/electribe",
			"korg/microkorg",
			"korg/minilogue_xd",
			"korg/modwave_mk_ii",
			"korg/multi_poly",
			"korg/opsix",
			"korg/volca_drum",
			"korg/wavestate",
			"modal/carbon8m",
			"moog/dfam",
			"moog/grandmother",
			"moog/labyrinth",
			"moog/matriarch",
			"moog/messenger",
			"moog/minitaur",
			"moog/mother_32",
			"moog/muse",
			"moog/sub_37",
			"moog/subharmonicon",
			"moog/subsequent_37",
			"novation/bass_station_ii",
			"novation/circuit_tracks",
			"novation/peak",
			"oberheim/teo_5",
			"pwm/malevolent",
			"roland/d_50",
			"roland/juno_106",
			"roland/mc_707",
			"roland/tr8s",
			"roland/tr_1000",
			"sequential/take_5",
			"soma/pulsar_23",
			"synthstrom_audible/deluge",
			"teenage_engineering/ep_133_ko_ii",
			"teenage_engineering/op_1",
			"teenage_engineering/op_xy",
			"vermona/drm1_mkiv",
			"voce/electric_piano",
			"waldorf/blofeld",
			"waldorf/iridium",
			"waldorf/streichfett",
			"yamaha/dx7",
		]

	def test_no_definition_writes_a_us_spelling_in_its_own_prose (self) -> None:
		"""The site this corpus feeds is written in British English and will not publish one.

		A quotation keeps its source's spelling, and so does a maker's own name for a thing -
		a control's label, a document's title - so only a definition's own account is swept.
		This exists because three definitions had to be corrected by hand before the site
		could take its spelling exception off, and nothing would have caught the fourth.
		"""
		patterns = [
			re.compile(r"\b[a-z]{3,}iz(e|es|ed|er|ers|ing|ation|ations)\b", re.IGNORECASE),
			re.compile(r"\b[a-z]{3,}yz(e|es|ed|ing)\b", re.IGNORECASE),
			re.compile(r"\b(favorite|favorites|color|colors|behavior|behaviors|honor|flavor)\b",
				re.IGNORECASE),
		]

		found = []

		for name in pymidiinstrumentdefs.available([CORPUS]):
			account = pymidiinstrumentdefs.load(name, [CORPUS]).source or ""

			# What is inside double quotation marks is somebody else's spelling to keep.
			outside = re.sub(r'"[^"]*"', " ", account)

			for pattern in patterns:
				found += [(name, hit.group(0)) for hit in pattern.finditer(outside)]

		assert found == []

	def test_nothing_bundled_sits_outside_a_makers_folder (self) -> None:
		"""A file directly in the corpus has no maker, so nothing could load it by name."""
		assert sorted(CORPUS.glob("*.yaml")) == []

	def test_every_bundled_definition_sits_in_its_makers_folder (self) -> None:
		"""The folder is half of the name, so it has to be the right maker.

		The folder is the short name ("moog") and the file says it the way the
		maker does ("Moog Music"), so the test is that one begins the other.
		"""
		for path in bundled():
			definition = pymidiinstrumentdefs.load_file(path)
			maker = re.sub(r"[^a-z0-9]+", "_", (definition.model.manufacturer or "").lower())

			assert maker.startswith(path.parent.name), (
				f"{path.parent.name}/{path.name} says it was made by {definition.model.manufacturer!r}"
			)

	def test_no_bundled_definition_carries_a_warning (self) -> None:
		"""Whatever the validator thinks worth saying about one of ours is fixed before it ships."""
		for path in bundled():
			definition = pymidiinstrumentdefs.load_file(path)

			assert definition.warnings == (), f"{path.parent.name}/{path.name}: {definition.warnings}"

	def test_every_maker_is_named_one_way_in_its_folder (self) -> None:
		"""One maker, one name, or a reader meets it twice under two headings.

		The Grandmother said "Moog" where the other six Moogs said "Moog Music", so a
		page listing the corpus by maker counted fifteen makers where there were
		fourteen, and called one model "Moog Grandmother" beside "Moog Music Minitaur".
		"""
		named: dict[str, dict[str, list[str]]] = {}

		for path in bundled():
			definition = pymidiinstrumentdefs.load_file(path)
			maker = definition.model.manufacturer or ""

			named.setdefault(path.parent.name, {}).setdefault(maker, []).append(path.name)

		for folder, makers in sorted(named.items()):
			assert len(makers) == 1, (
				f"{folder}/ names its maker {len(makers)} ways: "
				+ ", ".join(f"{maker!r} in {sorted(files)}" for maker, files in sorted(makers.items()))
			)

	def test_nothing_shipped_names_anything_internal (self) -> None:
		"""A definition and the guide beside it are read by strangers, so they name no tracker.

		These files go to PyPI and are rendered on a public site, where an item number, a
		colleague's name or a path on one machine means nothing to the reader and tells them
		about somebody's workshop instead of about their instrument. One tracker number had
		reached `elektron/syntakt` and nothing here caught it.

		**Four digits or more**, because that is what this workspace's numbers are and
		because a maker's own numbering reaches three. `CC #39` is a controller, and
		teenage engineering spells the OP-1's firmware `#246` on its own downloads page,
		which is the maker's word and belongs in a shipped file. The cost of the wider
		pattern was a false positive on a real instrument; the cost of this one is that a
		three-digit item number would not be caught, which has never happened.
		"""
		internal = re.compile(r"#[0-9]{4,}|\bSimon\b|\bSubroutine\b|/mnt/|/home/", re.IGNORECASE)

		shipped = list(bundled()) + sorted((CORPUS.parent.parent / "docs").glob("*.md"))
		found: dict[str, list[str]] = {}

		for path in shipped:
			for number, line in enumerate(path.read_text(encoding = "utf-8").splitlines(), start = 1):
				if internal.search(line):
					found.setdefault(f"{path.parent.name}/{path.name}", []).append(
						f"line {number}: {line.strip()[:70]}")

		assert found == {}, f"something internal reached a shipped file: {found}"

	def test_every_bundled_definition_states_its_provenance (self) -> None:
		"""A definition without a source is a rumour, so ours all have one."""
		for path in bundled():
			definition = pymidiinstrumentdefs.load_file(path)

			assert definition.source, f"{path.name} does not say where its facts came from"
			assert not definition.is_unverified, f"{path.name} ships unverified"

	def test_nothing_bundled_is_an_import (self) -> None:
		"""The README says none of these came from a .midnam, and it has to stay true.

		An import is a good way to start a definition and a poor place to stop.
		Shipping one would mean this package vouching for numbers nobody read out
		of a manual, which is the one thing its whole shape is arranged against.
		"""
		for path in bundled():
			definition = pymidiinstrumentdefs.load_file(path)
			source = (definition.source or "").lower()

			# "imported from" is what the importer writes, and is the whole test.
			# Merely naming a .midnam is not disqualifying and must not be treated
			# as such: moog/minitaur.yaml names one in order to record that it
			# disagrees, which is the opposite of having been derived from it.
			assert "imported from" not in source, f"{path.name} is an import: {source[:60]!r}"

	def test_every_bundled_definition_cites_a_locator (self) -> None:
		"""The README promises each one names its document and where in it to look.

		"The manual" cannot be checked by anybody; "p.13" can. This keeps that
		promise true as the corpus grows, since a source line is the one part of
		a definition nothing else can verify for you. The document is usually a
		user manual, and for one instrument a quick-start guide is all there is.

		**A page is not the only kind of locator**, because not every maker
		publishes pages. The OP-1's guide is a website of numbered sections and
		nothing else, so every one of its sources is `paginated: false` and it
		cites sections. A definition in that position is held to naming sections
		as firmly as the rest are held to naming pages.
		"""
		document = re.compile(r"\b(manual|guide|chart|addendum)\b", re.I)
		pages = re.compile(r"\bpp?\.\s*\d|\b\d+\s*pages?\b|\bevery page\b", re.I)
		sections = re.compile(r"\bsections?\b[^.]{0,40}?\d|\b\d+\s+numbered sections?\b", re.I)

		for path in bundled():
			definition = pymidiinstrumentdefs.load_file(path)
			source = definition.source or ""

			assert document.search(source), f"{path.name} does not name a document"

			paginated = [name for name, held in definition.sources.items() if held.paginated]
			wanted = pages if paginated else sections

			assert wanted.search(source), (
				f"{path.name} names no {'page' if paginated else 'section'}: {source[:80]!r}")

	def test_dfam_is_the_minimum_case (self) -> None:
		"""An instrument with no MIDI at all is a real definition, not an empty one.

		The DFAM's 44-page manual does not contain the word "MIDI". Recording
		that is what stops the next person reading it again.
		"""
		dfam = pymidiinstrumentdefs.load("moog/dfam", [CORPUS])

		assert dfam.model.name == "DFAM"
		assert dfam.midi.stated_none
		assert dfam.midi.refuses_control_change
		assert dfam.voice.addressing == "none"
		assert dfam.controls == {}

	def test_matriarch_control_surface (self) -> None:
		"""The Matriarch's own manual table, read back, plus the one its release notes add.

		36 come from the manual's MMA chart and the 37th, CC 106, from Moog's
		firmware v1.3.0 notes, which are the only place it is published.
		"""
		matriarch = pymidiinstrumentdefs.load("moog/matriarch", [CORPUS])

		assert len(matriarch.controls) == 37
		assert matriarch.controls["arp_seq_gate_length"].cc == 106
		assert sum(control.is_14_bit for control in matriarch.controls.values()) == 12
		assert matriarch.controls["osc_2_frequency"].range == (0, 16383)

	def test_matriarch_voicing_is_a_control_not_a_constant (self) -> None:
		"""Its voice count is switchable, and settable over MIDI at CC 94.

		So polyphony is unknown rather than wrong: the manual gives no power-on
		default, and a panel can move the instrument between one and four voices
		while it plays.
		"""
		matriarch = pymidiinstrumentdefs.load("moog/matriarch", [CORPUS])

		assert matriarch.voice.polyphony is None
		assert matriarch.voice.voicing_modes == (1, 2, 4)

		mode = matriarch.controls["paraphony_voice_mode"]

		assert mode.cc == 94
		assert mode.band("one_voice") == (0, 42)
		assert mode.band("two_voice") == (43, 84)
		assert mode.band("four_voice") == (85, 127)

	def test_the_matriarch_names_every_state_it_offers (self) -> None:
		"""A choice with no states draws a label and nothing to press.

		The three arp controls shipped that way until the table at p. 74 was read
		again.
		"""
		matriarch = pymidiinstrumentdefs.load("moog/matriarch", [CORPUS])
		empty = [
			control.name for control in matriarch.controls.values()
			if control.kind == pymidiinstrumentdefs.CHOICE and not control.values
		]

		assert empty == []
		assert matriarch.controls["arp_mode"].band("seq") == (43, 84)
		assert matriarch.controls["arp_pattern"].value_for("random") == 106
		assert matriarch.controls["arp_range"].name_for(0) == "one"


class TestAbsences:

	"""A checked absence and an unread page are different facts, and must not look alike."""

	def test_the_labyrinth_answers_to_notes_clock_and_transport_only (self) -> None:
		labyrinth = pymidiinstrumentdefs.load("moog/labyrinth", [CORPUS])

		assert labyrinth.midi.refuses_control_change
		assert labyrinth.midi.clock == "receives"
		assert labyrinth.midi.transport == "receives"
		assert labyrinth.controls == {}

	def test_the_labyrinth_does_not_guess_its_polyphony (self) -> None:
		"""Unknown is honest; a guessed 1 would be a fact nobody established."""
		labyrinth = pymidiinstrumentdefs.load("moog/labyrinth", [CORPUS])

		assert labyrinth.voice.polyphony is None

	def test_the_model_d_is_reached_only_by_sysex (self) -> None:
		model_d = pymidiinstrumentdefs.load("behringer/model_d", [CORPUS])

		assert model_d.midi.refuses_control_change
		assert model_d.midi.sysex is True
		assert model_d.voice.polyphony == 1
		assert model_d.controls == {}

	def test_the_malevolent_claims_no_absence_nobody_checked (self) -> None:
		"""Its only document is a quick-start guide, which lists no controllers.

		That is not the same as having none, so the file must not say it has
		none: silence here means "not in the guide", and says so in its source.
		"""
		malevolent = pymidiinstrumentdefs.load("pwm/malevolent", [CORPUS])

		assert not malevolent.midi.refuses_control_change
		assert malevolent.midi.control_change is None
		assert malevolent.voice.polyphony == 1
		assert "guide" in (malevolent.source or "").lower()

	def test_the_td_3_does_claim_an_absence_and_says_what_earns_it (self) -> None:
		"""The same shape of document as the Malevolent's, and the opposite answer.

		Both have nothing but a quick start guide and neither guide lists a
		controller.  The difference is that this one carries a table of MIDI
		messages, and that the same table in the sibling guide does carry a
		controller - so the absence here is informative rather than merely silent.
		The file has to say which, because the two instruments look alike.
		"""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])
		malevolent = pymidiinstrumentdefs.load("pwm/malevolent", [CORPUS])

		assert td3.midi.refuses_control_change
		assert not malevolent.midi.refuses_control_change
		assert td3.controls == malevolent.controls == {}

		account = " ".join((td3.source or "").split())

		assert "A QUICK START GUIDE THAT LISTS NO CONTROLLER IS" in account
		assert "Two documents are what turn a silence into a statement" in account

	def test_the_corpus_divides_its_empty_definitions_by_why (self) -> None:
		"""Eleven definitions carry no controls, for four different reasons.

		Pinned here because the count has gone stale in notes twice: a twelfth
		cannot be added without saying which kind it is.
		"""
		empty = {name for name in pymidiinstrumentdefs.available([CORPUS])
			if not pymidiinstrumentdefs.load(name, [CORPUS]).controls}

		assert len(empty) == 11

		kinds: dict[str | None, set[str]] = {}

		for name in empty:
			definition = pymidiinstrumentdefs.load(name, [CORPUS])
			key = "stated_none" if definition.midi.stated_none else definition.midi.control_change
			kinds.setdefault(key, set()).add(name)

		assert kinds["none"] == {"behringer/model_d", "behringer/td_3",
			"moog/labyrinth", "vermona/drm1_mkiv"}
		assert kinds["learned"] == {"arturia/drumbrute_impact", "roland/d_50",
			"synthstrom_audible/deluge", "teenage_engineering/op_1"}
		assert kinds["stated_none"] == {"moog/dfam"}

		# And the two that claim nothing, because nobody has established anything.
		assert kinds[None] == {"akai/mpc_sample", "pwm/malevolent"}


class TestCarbon8M:

	def test_the_whole_chart_arrives (self) -> None:
		"""111 assigned numbers, less the five channel mode messages PyMidiDefs owns."""
		carbon = pymidiinstrumentdefs.load("modal/carbon8m", [CORPUS])

		assert len(carbon.controls) == 106
		assert all(control.cc is not None and control.cc < 120 for control in carbon.controls.values())

	def test_no_number_is_used_twice (self) -> None:
		carbon = pymidiinstrumentdefs.load("modal/carbon8m", [CORPUS])
		numbers = [control.cc for control in carbon.controls.values()]

		assert len(numbers) == len(set(numbers))

	def test_the_numbers_the_chart_marks_unassigned_stay_unassigned (self) -> None:
		"""The chart prints "-" for 17 numbers, so their absence is a checked one."""
		carbon = pymidiinstrumentdefs.load("modal/carbon8m", [CORPUS])
		used = {control.cc for control in carbon.controls.values()}
		unassigned = {2, 4, 6, 8, 10, 38, 65, 66, 74, 76, 77, 97, 98, 99, 122, 126, 127}

		assert used & unassigned == set()

	def test_each_mod_slot_is_a_group_of_depth_source_and_destination (self) -> None:
		"""Three runs of eight numbers, paired by slot rather than by kind."""
		groups = pymidiinstrumentdefs.load("modal/carbon8m", [CORPUS]).grouped_controls()

		for slot in range(1, 9):
			members = [control.cc for control in groups[f"modslot_{slot}"]]

			assert members == [87 + slot, 99 + slot, 107 + slot]

	def test_the_joysticks_missing_axis_is_the_mod_wheel (self) -> None:
		"""The chart has X+, X- and Y- only, because Y+ sends CC 1."""
		carbon = pymidiinstrumentdefs.load("modal/carbon8m", [CORPUS])

		assert "joystick_y_plus" not in carbon.controls
		assert carbon.controls["mod_wheel"].cc == 1

	def test_voicing_is_a_mode_so_polyphony_is_not_a_constant (self) -> None:
		carbon = pymidiinstrumentdefs.load("modal/carbon8m", [CORPUS])

		assert carbon.voice.polyphony is None
		assert carbon.voice.voicing_modes == (1, 2, 4, 8)
		assert carbon.midi.program_change is not None
		assert carbon.midi.program_change.presets == 500


class TestTR8S:

	def test_the_two_auto_fill_controls_are_never_offered_for_sending (self) -> None:
		"""The chart marks them transmitted and not recognised, and a panel must respect that."""
		tr8s = pymidiinstrumentdefs.load("roland/tr8s", [CORPUS])
		unsendable = sorted(control.name for control in tr8s.controls.values() if not control.is_sendable)

		assert unsendable == ["auto_fill_in", "auto_fill_in_manual"]

	def test_every_voice_has_tune_decay_level_and_ctrl (self) -> None:
		groups = pymidiinstrumentdefs.load("roland/tr8s", [CORPUS]).grouped_controls()

		for voice in ("bd", "sd", "lt", "mt", "ht", "rs", "hc", "ch", "oh", "cc", "rc"):
			names = [control.name for control in groups[voice]]

			assert names == [f"{voice}_tune", f"{voice}_decay", f"{voice}_level", f"{voice}_ctrl"]

	def test_the_whole_chart_arrives (self) -> None:
		tr8s = pymidiinstrumentdefs.load("roland/tr8s", [CORPUS])

		assert len(tr8s.controls) == 55
		assert len(tr8s.voice.voices) == 11
		assert tr8s.voice.voices["bd"] == 36


class TestSubharmonicon:

	def test_notes_are_offsets_from_c4 (self) -> None:
		subharmonicon = pymidiinstrumentdefs.load("moog/subharmonicon", [CORPUS])

		assert subharmonicon.voice.addressing == "relative"
		assert subharmonicon.voice.reference_note == 60

	def test_a_sub_divider_names_its_divisor (self) -> None:
		"""The values rise while the divisor falls, and the names say which is which."""
		divider = pymidiinstrumentdefs.load("moog/subharmonicon", [CORPUS]).controls["vco_1_sub_1_frequency"]

		assert divider.band("divide_16") == (0, 7)
		assert divider.band("divide_1") == (120, 127)
		assert divider.name_for(64) == "divide_8"

	def test_six_fourteen_bit_pairs_each_obey_the_plus_32_rule (self) -> None:
		controls = pymidiinstrumentdefs.load("moog/subharmonicon", [CORPUS]).controls.values()
		pairs = [control for control in controls if control.is_14_bit]

		assert len(pairs) == 6
		assert all(control.cc is not None and control.lsb == control.cc + 32 for control in pairs)


class TestStreichfett:

	def test_an_enumeration_sends_the_number_the_manual_prints (self) -> None:
		"""Read as bands, 8va would have gone out as 64. The manual says 2."""
		streichfett = pymidiinstrumentdefs.load("waldorf/streichfett", [CORPUS])

		assert streichfett.controls["string_registration"].value_for("octave") == 2
		assert streichfett.controls["fx_type"].value_for("animate") == 2
		assert streichfett.controls["solo_sustain"].kind == pymidiinstrumentdefs.SWITCH

	def test_the_sustain_pedal_is_still_a_band (self) -> None:
		"""One table mixes both conventions, and each control keeps its own."""
		pedal = pymidiinstrumentdefs.load("waldorf/streichfett", [CORPUS]).controls["sustain_pedal"]

		assert pedal.band("on") == (64, 127)

	def test_each_section_counts_its_own_voices (self) -> None:
		"""128 for the strings and eight for the solo, from two engines that do not share.

		One figure for the instrument would be wrong for one section or the other,
		and a consumer capping notes per section would cap the wrong one.
		"""
		streichfett = pymidiinstrumentdefs.load("waldorf/streichfett", [CORPUS])

		assert streichfett.parts["strings"].polyphony == 128
		assert streichfett.parts["solo"].polyphony == 8
		assert streichfett.voice.polyphony is None
		assert streichfett.voice.polyphony_shared is False


class TestVoce:

	def test_the_whole_effects_table_arrives (self) -> None:
		"""Rate, depth and tremolo were thought undocumented; they are at pp. 8-9."""
		voce = pymidiinstrumentdefs.load("voce/electric_piano", [CORPUS])

		assert {control.cc for control in voce.controls.values()} == {1, 7, 80, 81, 82, 83, 91, 94}

	def test_channel_16_cannot_be_the_basic_channel (self) -> None:
		"""The switch's sixteenth position is omni, not channel 16."""
		voce = pymidiinstrumentdefs.load("voce/electric_piano", [CORPUS])

		assert voce.midi.channels == (1, 15)

	def test_polyphony_is_a_state_not_a_constant (self) -> None:
		"""Chorus takes two voices a note, and CC 80 switches it."""
		voce = pymidiinstrumentdefs.load("voce/electric_piano", [CORPUS])

		assert voce.voice.polyphony is None
		assert voce.voice.voicing_modes == (16, 32)


class TestTake5:

	def test_the_cutoff_is_four_times_finer_over_nrpn (self) -> None:
		"""One parameter, two addresses, two resolutions, and the file keeps both."""
		cutoff = pymidiinstrumentdefs.load("sequential/take_5", [CORPUS]).controls["filter_cutoff"]

		assert (cutoff.cc, cutoff.range) == (33, (0, 127))
		assert (cutoff.nrpn, cutoff.nrpn_range) == (29, (0, 1023))

	def test_the_whole_cc_table_arrives_less_the_nrpn_transport (self) -> None:
		"""CC 1-89, less Data Entry MSB and LSB, which carry NRPN values rather than parameters."""
		controls = pymidiinstrumentdefs.load("sequential/take_5", [CORPUS]).controls.values()
		numbers = [control.cc for control in controls if control.cc is not None]

		assert sorted(numbers) == sorted(set(range(1, 90)) - {6, 38})

	def test_no_nrpn_is_used_twice (self) -> None:
		controls = pymidiinstrumentdefs.load("sequential/take_5", [CORPUS]).controls.values()
		numbers = [control.nrpn for control in controls if control.nrpn is not None]

		assert len(numbers) == len(set(numbers))

	def test_the_fine_tunes_are_cc_only (self) -> None:
		"""Their NRPN range is printed as -700 to 700, with no word on how that is sent."""
		controls = pymidiinstrumentdefs.load("sequential/take_5", [CORPUS]).controls

		assert controls["osc_1_fine_freq"].nrpn is None
		assert controls["osc_2_fine_freq"].nrpn is None

	def test_nrpn_is_the_preferred_transport (self) -> None:
		take_5 = pymidiinstrumentdefs.load("sequential/take_5", [CORPUS])

		assert take_5.midi.nrpn == "preferred"
		assert take_5.voice.polyphony == 5


class TestPulsar23:

	def test_its_map_is_learned_and_says_so (self) -> None:
		"""Neither a checked absence nor an unread page: every assignment is the owner's."""
		pulsar = pymidiinstrumentdefs.load("soma/pulsar_23", [CORPUS])

		assert pulsar.midi.learns_control_change
		assert not pulsar.midi.refuses_control_change
		assert pulsar.voice.note_map == "learned"
		assert pulsar.voice.voices == {}

	def test_portamento_is_its_one_fixed_control (self) -> None:
		pulsar = pymidiinstrumentdefs.load("soma/pulsar_23", [CORPUS])

		assert list(pulsar.controls) == ["portamento"]
		assert pulsar.controls["portamento"].cc == 5


class TestSyntakt:

	def test_the_same_controller_number_means_two_things_on_two_parts (self) -> None:
		"""28 of its 71 controller numbers do, and only the channel tells them apart."""
		syntakt = pymidiinstrumentdefs.load("elektron/syntakt", [CORPUS])

		on_a_track = syntakt.controls["filter_attack_time"]
		on_the_fx_track = syntakt.controls["fx_filter_frequency"]

		assert on_a_track.cc == on_the_fx_track.cc == 70
		assert on_a_track.part == "track"
		assert on_the_fx_track.part == "fx"

		reused = [cc for cc in {control.cc for control in syntakt.controls.values()}
			if sum(1 for control in syntakt.controls.values() if control.cc == cc) > 1]

		assert len(reused) == 28

	def test_the_nrpn_does_not_resolve_what_the_cc_leaves_open (self) -> None:
		"""On other instruments it would, which is why this is pinned rather than assumed."""
		syntakt = pymidiinstrumentdefs.load("elektron/syntakt", [CORPUS])

		# the two filter tables share NRPN 1/20 for parameters their CCs number differently
		assert syntakt.controls["filter_frequency"].nrpn == 148
		assert syntakt.controls["fx_filter_frequency"].nrpn == 148
		assert syntakt.controls["filter_frequency"].cc != syntakt.controls["fx_filter_frequency"].cc

	def test_twelve_tracks_are_one_part_because_each_can_be_either_kind (self) -> None:
		"""A Digitakt has eight audio and eight MIDI tracks; this has twelve of either."""
		syntakt = pymidiinstrumentdefs.load("elektron/syntakt", [CORPUS])

		assert syntakt.parts["track"].count == 12
		assert syntakt.parts["track"].polyphony == 1
		assert syntakt.voice.polyphony_shared is False
		assert sorted(syntakt.parts) == ["fx", "track"]


class TestWavestate:

	def test_its_controller_numbers_are_defaults_a_player_can_move (self) -> None:
		"""41 of its 50 are, and a panel that calls them fixed will be wrong on any changed unit."""
		wavestate = pymidiinstrumentdefs.load("korg/wavestate", [CORPUS])

		assignable = {control.cc for control in wavestate.controls.values()
			if control.group and control.group.endswith("_mod") or control.group == "scale_select"}

		assert len(assignable) == 41
		assert wavestate.controls["layer_a_mod_1"].cc == 80
		assert wavestate.controls["perf_mod_1"].cc == 24

		# and the nine the chart fixes, which a player cannot reassign
		assert wavestate.controls["modulation"].cc == 1
		assert wavestate.controls["soft"].cc == 67

	def test_it_neither_sends_nor_follows_transport (self) -> None:
		"""Checked rather than unread: the chart marks Start, Stop and Continue X both ways."""
		wavestate = pymidiinstrumentdefs.load("korg/wavestate", [CORPUS])

		assert wavestate.midi.transport == "none"
		assert wavestate.midi.clock == "both"

	def test_four_layers_sit_on_the_global_channel_until_moved (self) -> None:
		"""Which is why each carries an offset of zero rather than a channel of its own."""
		wavestate = pymidiinstrumentdefs.load("korg/wavestate", [CORPUS])

		assert sorted(wavestate.parts) == ["layer_a", "layer_b", "layer_c", "layer_d"]

		for part in wavestate.parts.values():
			assert part.channel_offset == 0
			assert part.takes("notes")


class TestSubsequent37:

	def test_41_of_its_controls_can_be_reached_by_nrpn_alone (self) -> None:
		"""The maker says why: it has more parameters than there are controller numbers."""
		moog = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		nrpn_only = [control for control in moog.controls.values()
			if control.cc is None and control.nrpn is not None]

		assert len(nrpn_only) == 41
		assert all(control.nrpn is not None for control in moog.controls.values()
			if control.cc is None), "a control that can be addressed by nothing"

		# the arpeggiator's rate is the plainest case: a panel knob with no controller number
		assert moog.controls["arp_rate"].cc is None
		assert moog.controls["arp_rate"].nrpn == 403

	def test_57_controls_carry_both_numbers_for_one_parameter (self) -> None:
		"""The two charts name them differently and p. 51 is what joins the two names."""
		moog = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		both = [control for control in moog.controls.values()
			if control.cc is not None and control.nrpn is not None]

		assert len(both) == 57

		# "FILTER EG ATTACK TIME" on one page, "F EG ATTACK" on the next
		assert moog.controls["filter_eg_attack_time"].cc == 23
		assert moog.controls["filter_eg_attack_time"].nrpn == 505

	def test_the_amplifier_envelope_has_no_nrpn_at_all (self) -> None:
		"""Ten controller numbers and not one NRPN: the published chart stops before it."""
		moog = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		amp = [control for control in moog.controls.values() if control.group == "amp_envelope"]

		assert len(amp) == 10
		assert all(control.cc is not None for control in amp)
		assert all(control.nrpn is None for control in amp)

	def test_the_six_contradicted_value_counts_carry_no_nrpn_range (self) -> None:
		"""A count the same manual contradicts is not a range, so none is derived from it."""
		moog = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		contradicted = {486, 487, 488, 489, 490, 518}
		found = {control.nrpn: control for control in moog.controls.values()
			if control.nrpn in contradicted}

		assert set(found) == contradicted

		for control in found.values():
			assert control.nrpn_range is None, f"{control.name} claims a range from a bad count"

	def test_filter_resonance_is_the_one_named_row_with_no_value_range (self) -> None:
		"""Its neighbours both print 16384 and its own cell is empty on the page."""
		moog = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		assert moog.controls["filter_resonance"].nrpn == 500
		assert moog.controls["filter_resonance"].nrpn_range is None

		# the two either side of it in the chart do carry one
		assert moog.controls["filter_cutoff"].nrpn == 499
		assert moog.controls["filter_multidrive"].nrpn == 501

	def test_every_14_bit_pair_puts_its_fine_half_32_above (self) -> None:
		"""Which is the MMA's own pairing, so a sender that does not know this model gets it right."""
		moog = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		paired = [control for control in moog.controls.values() if control.is_14_bit]

		assert len(paired) == 28

		for control in paired:
			assert control.lsb == (control.cc or 0) + 32
			assert control.range == (0, 16383)

	def test_it_is_two_voice_only_when_duo_mode_is_on (self) -> None:
		"""So polyphony is unstated and the mode is a control, as on the Matriarch."""
		moog = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		assert moog.voice.polyphony is None
		assert moog.voice.paraphonic is True
		assert moog.voice.voicing_modes == (1, 2)
		assert moog.controls["osc_duo_mode_on_off"].cc == 110

	def test_it_carries_no_channel_mode_message_as_a_control (self) -> None:
		"""The chart prints two and both belong to the specification rather than here."""
		moog = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		numbers = {control.cc for control in moog.controls.values()}

		assert 122 not in numbers, "local control is a channel mode message"
		assert 123 not in numbers, "all notes off is a channel mode message"
		assert 0 not in numbers and 32 not in numbers, "bank select is the MMA's"


class TestTheTwoMoog37s:

	"""The Sub 37 and the Subsequent 37 are one MIDI implementation, established not assumed.

	Moog ships them one firmware image, byte for byte; their manuals' MIDI pages are
	identical character for character with the model name set aside; and their NRPN charts
	agree in all 123 rows. The only row that differs is a channel mode message, which is a
	control in neither.

	So the two definitions carry the same controls, and these tests are here to say so out
	loud: if somebody corrects one of them, the failure is the reminder to look at the other.
	**A real difference found in a document is a reason to change these tests**, not a reason
	to doubt them - but it should be a document that changes them.
	"""

	def test_they_carry_the_same_controls (self) -> None:
		"""Every name, number, band, range and group of all 114."""
		sub = pymidiinstrumentdefs.load("moog/sub_37", [CORPUS])
		subsequent = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		def surface (definition: pymidiinstrumentdefs.definition.Definition) -> dict[str, object]:
			return {
				name: (control.label, control.cc, control.lsb, control.nrpn,
					tuple(control.values.items()), control.range, control.nrpn_range,
					control.unit, control.direction, control.group)
				for name, control in definition.controls.items()
			}

		assert surface(sub) == surface(subsequent)
		assert len(sub.controls) == 114

	def test_they_describe_the_same_firmware (self) -> None:
		"""One image, which Moog names for the older instrument in both packages."""
		sub = pymidiinstrumentdefs.load("moog/sub_37", [CORPUS])
		subsequent = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		assert sub.model.firmware == "1.2.0"
		assert subsequent.model.firmware == "1.2.0"

	def test_they_agree_on_what_the_instrument_is (self) -> None:
		"""Their specifications pages are identical, so the definitions' facts are too."""
		sub = pymidiinstrumentdefs.load("moog/sub_37", [CORPUS])
		subsequent = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		for field in ("addressing", "paraphonic", "voicing_modes", "polyphony", "aftertouch"):
			assert getattr(sub.voice, field) == getattr(subsequent.voice, field), field

		assert sub.midi.channels == subsequent.midi.channels
		assert sub.midi.clock == subsequent.midi.clock
		assert sub.midi.transport == subsequent.midi.transport
		assert sub.midi.nrpn == subsequent.midi.nrpn
		assert sub.groups == subsequent.groups

	def test_each_is_named_as_its_own_manual_names_it (self) -> None:
		"""Moog calls the older one three things; its manual calls it one, in 62 pages."""
		sub = pymidiinstrumentdefs.load("moog/sub_37", [CORPUS])
		subsequent = pymidiinstrumentdefs.load("moog/subsequent_37", [CORPUS])

		assert sub.model.name == "Sub 37"
		assert subsequent.model.name == "Subsequent 37"
		assert sub.model.manufacturer == subsequent.model.manufacturer == "Moog Music"


class TestChoices:

	"""Exact values, for a manual that prints 0 = Base, 1 = Both, 2 = 8va and means them."""

	BODY = (
		"definition: 1\nmodel: {name: X}\nsource: hand\n"
		"controls: {registration: {cc: 70, choices: {base: 0, both: 1, octave: 2}}}\n"
	)

	def test_a_choice_sends_exactly_the_number_printed (self) -> None:
		"""Read as bands, the last of these would absorb 2-127 and send 64."""
		control = pymidiinstrumentdefs.parse(self.BODY, source = "x.yaml").controls["registration"]

		assert control.value_for("base") == 0
		assert control.value_for("octave") == 2
		assert control.band("octave") == (2, 2)
		assert control.kind == pymidiinstrumentdefs.CHOICE
		assert control.states == ["base", "both", "octave"]

	def test_a_number_between_choices_names_nothing (self) -> None:
		control = pymidiinstrumentdefs.parse(self.BODY, source = "x.yaml").controls["registration"]

		assert control.name_for(1) == "both"
		assert control.name_for(64) is None

	def test_two_choices_make_a_switch (self) -> None:
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"controls: {sustain: {cc: 79, choices: {no_sustain: 0, full_sustain: 1}}}\n"
		)
		control = pymidiinstrumentdefs.parse(body, source = "x.yaml").controls["sustain"]

		assert control.kind == pymidiinstrumentdefs.SWITCH
		assert control.value_for("full_sustain") == 1

	def test_values_and_choices_together_are_refused (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {a: {cc: 1, values: {p: 0, q: 64}, choices: {r: 0, s: 1}}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "both values and choices" in str(raised.value)

	def test_two_choices_cannot_share_a_number (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {a: {cc: 1, choices: {p: 1, q: 1}}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "controls.a.choices.q" in str(raised.value)


class TestDirection:

	def test_a_control_goes_both_ways_unless_it_says_otherwise (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nsource: hand\ncontrols: {a: {cc: 14}}"
		control = pymidiinstrumentdefs.parse(body, source = "x.yaml").controls["a"]

		assert control.direction == pymidiinstrumentdefs.definition.BOTH
		assert control.is_sendable

	def test_a_control_the_instrument_only_transmits_is_not_for_sending (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nsource: hand\ncontrols: {auto_fill: {cc: 14, direction: transmits}}"
		control = pymidiinstrumentdefs.parse(body, source = "x.yaml").controls["auto_fill"]

		assert not control.is_sendable

	def test_an_unknown_direction_is_refused (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {a: {cc: 14, direction: sideways}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "controls.a.direction" in str(raised.value)


class TestRelativeNotes:

	def test_a_relative_instrument_names_the_note_its_offsets_are_from (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nsource: hand\nvoice: {addressing: relative, reference_note: 60}\n"
		voice = pymidiinstrumentdefs.parse(body, source = "x.yaml").voice

		assert voice.addressing == "relative"
		assert voice.reference_note == 60

	def test_relative_without_a_reference_note_is_refused (self) -> None:
		"""An offset from nowhere cannot be drawn, so the file has to say which note."""
		body = "definition: 1\nmodel: {name: X}\nvoice: {addressing: relative}\n"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "voice.reference_note" in str(raised.value)

	def test_a_reference_note_means_nothing_to_a_pitched_instrument (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nvoice: {addressing: pitches, reference_note: 60}\n"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError):
			pymidiinstrumentdefs.parse(body, source = "x.yaml")


class TestLearnedMaps:

	def test_learned_controls_are_neither_absent_nor_unread (self) -> None:
		"""The third state: it answers to controllers, and nobody can publish which."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"midi: {control_change: learned}\nvoice: {addressing: voices, note_map: learned}\n"
		)
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert definition.midi.learns_control_change
		assert not definition.midi.refuses_control_change
		assert definition.voice.note_map == "learned"

	def test_the_drm1s_note_map_is_its_factory_default (self) -> None:
		drm1 = pymidiinstrumentdefs.load("vermona/drm1_mkiv", [CORPUS])

		assert drm1.voice.note_map == "learned"
		assert drm1.voice.voices["kick"] == 36

	def test_an_unknown_note_map_is_refused (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nvoice: {note_map: guessed}\n"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "voice.note_map" in str(raised.value)


class TestNrpnRange:

	def test_an_nrpn_can_be_finer_than_its_cc_twin (self) -> None:
		"""One control, two addresses, two resolutions: a consumer picks the finer."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"controls: {cutoff: {cc: 33, nrpn: 29, nrpn_range: [0, 1023]}}\n"
		)
		control = pymidiinstrumentdefs.parse(body, source = "x.yaml").controls["cutoff"]

		assert control.range == (0, 127)
		assert control.nrpn_range == (0, 1023)

	def test_an_nrpn_range_needs_an_nrpn (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {cutoff: {cc: 33, nrpn_range: [0, 1023]}}\n"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "controls.cutoff.nrpn_range" in str(raised.value)


class TestBands:

	def test_a_band_runs_to_the_next_one (self) -> None:
		"""Each entry names the lowest value of its band, as manuals print them."""
		control = pymidiinstrumentdefs.Control(
			name = "glide_type", label = "Glide Type", cc = 85,
			values = {"lcr": 0, "lct": 43, "exp": 85},
		)

		assert control.band("lcr") == (0, 42)
		assert control.band("lct") == (43, 84)
		assert control.band("exp") == (85, 127)

	def test_the_value_sent_is_the_middle_of_the_band (self) -> None:
		"""The middle, so a value that drifts by one is not a different setting."""
		control = pymidiinstrumentdefs.Control(
			name = "glide_type", label = "Glide Type", cc = 85,
			values = {"lcr": 0, "lct": 43, "exp": 85},
		)

		assert control.value_for("lcr") == 21
		assert control.value_for("exp") == 106

	def test_a_value_reads_back_as_its_band (self) -> None:
		control = pymidiinstrumentdefs.Control(
			name = "glide_type", label = "Glide Type", cc = 85,
			values = {"lcr": 0, "lct": 43, "exp": 85},
		)

		assert control.name_for(0) == "lcr"
		assert control.name_for(84) == "lct"
		assert control.name_for(127) == "exp"

	def test_kind_is_derived_from_how_many_values_there_are (self) -> None:
		bare = pymidiinstrumentdefs.Control(name = "cutoff", label = "Cutoff", cc = 19)
		two = pymidiinstrumentdefs.Control(
			name = "glide", label = "Glide", cc = 65, values = {"off": 0, "on": 64})
		three = pymidiinstrumentdefs.Control(
			name = "mode", label = "Mode", cc = 91, values = {"a": 0, "b": 43, "c": 85})

		assert bare.kind == pymidiinstrumentdefs.CONTINUOUS
		assert two.kind == pymidiinstrumentdefs.SWITCH
		assert three.kind == pymidiinstrumentdefs.CHOICE

	def test_a_choice_with_no_states_loads_and_says_what_is_wrong (self) -> None:
		"""A kind that promises states the file does not name gives a panel nothing to offer.

		The format allows the override, so the file still loads. But it is the one
		combination a consumer cannot do anything sensible with, so the validator
		says so rather than letting it ship quietly.
		"""
		body = "definition: 1\nmodel: {name: X}\nsource: hand\ncontrols: {division: {cc: 86, kind: choice}}"
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert definition.controls["division"].kind == pymidiinstrumentdefs.CHOICE
		assert any("no states" in warning for warning in definition.warnings)


class TestRefusals:

	def test_an_unknown_version_says_both_numbers (self) -> None:
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse("definition: 7\nmodel: {name: X}", source = "x.yaml")

		assert "version 7" in str(raised.value)
		assert "version 1" in str(raised.value)

	def test_a_definition_must_name_its_instrument (self) -> None:
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse("definition: 1\nmodel: {manufacturer: Moog}", source = "x.yaml")

		assert "model" in str(raised.value)

	def test_bands_must_ascend (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {a: {cc: 1, values: {hi: 10, lo: 5}}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "controls.a.values.lo" in str(raised.value)

	def test_two_bands_cannot_share_a_number (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {a: {cc: 1, values: {p: 5, q: 5}}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "already the start" in str(raised.value)

	def test_a_yaml_boolean_is_not_a_whole_number (self) -> None:
		"""True is an int in Python, and would arrive silently as 1."""
		body = "definition: 1\nmodel: {name: X}\ncontrols: {a: {cc: true}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "whole number" in str(raised.value)

	def test_a_bare_off_reads_as_a_boolean_and_the_error_says_so (self) -> None:
		"""YAML 1.1 turns `off` into False, so a band name stops being text.

		The file looks right and the fix is one pair of quotes, which is exactly
		when an error has to explain itself.
		"""
		body = "definition: 1\nmodel: {name: X}\ncontrols: {a: {cc: 1, values: {off: 0, on: 64}}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "Quote it" in str(raised.value)

	def test_numbers_out_of_range_are_refused (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {a: {cc: 200}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "0-127" in str(raised.value)

	@pytest.mark.parametrize("cc", range(120, 128))
	def test_a_channel_mode_message_is_not_a_control (self, cc: int) -> None:
		"""CC 120-127 mean the same everywhere, so they are PyMidiDefs' and not a definition's.

		Manufacturers' charts print them beside everything else, which is exactly
		how they would get copied into a definition by somebody transcribing one.
		"""
		body = f"definition: 1\nmodel: {{name: X}}\ncontrols: {{local: {{cc: {cc}}}}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "controls.local.cc" in str(raised.value)
		assert "pymididefs.cc." in str(raised.value)

	def test_the_refusal_names_the_constant_it_duplicates (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {local: {cc: 122}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "pymididefs.cc.LOCAL_CONTROL_ON_OFF" in str(raised.value)

	def test_a_name_must_be_addressable (self) -> None:
		body = "definition: 1\nmodel: {name: X}\ncontrols: {'Glide Type': {cc: 1}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "is not a name" in str(raised.value)

	def test_a_gate_must_name_a_real_control (self) -> None:
		"""velocity.gated_by explains a velocity lane that appears to do nothing.

		Pointing it at a control that does not exist explains nothing at all.
		"""
		body = (
			"definition: 1\nmodel: {name: X}\n"
			"voice: {velocity: {note_on: gated, gated_by: [nowhere]}}\n"
		)

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "nowhere" in str(raised.value)

	def test_every_message_names_the_file (self) -> None:
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse("definition: 1", source = "moog/thing.yaml")

		assert str(raised.value).startswith("moog/thing.yaml: ")


class TestWarnings:

	def test_missing_provenance_warns_and_still_loads (self) -> None:
		definition = pymidiinstrumentdefs.parse(
			"definition: 1\nmodel: {name: X}", source = "x.yaml")

		assert definition.model.name == "X"
		assert any("provenance" in warning for warning in definition.warnings)

	def test_an_unverified_import_says_so (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nsource: imported from X.midnam, unverified\n"
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert definition.is_unverified
		assert any("unverified" in warning for warning in definition.warnings)

	def test_a_control_that_cannot_be_addressed_warns (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nsource: hand\ncontrols: {a: {label: A}}"
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert any("neither cc nor nrpn" in warning for warning in definition.warnings)


class TestSources:

	def test_a_citation_keeps_the_landing_page_and_the_file_apart (self) -> None:
		"""They fail differently: the page outlives the file's address.

		A maker's file often sits on a content-hashed path that names no product
		and does not survive the next site change, while the page a person can
		navigate to stays put.
		"""
		body = (
			"definition: 1\nmodel: {name: X}\n"
			"sources:\n"
			"  midi_impl:\n"
			"    kind: midi_implementation\n"
			"    title: minilogue xd/MIDI Implimentation\n"
			"    edition: Revision 1.01\n"
			"    landing: https://example.test/support/product/811/\n"
			"    url: https://cdn.example.test/files/5227b0b2.txt\n"
			"    sha256: f34014c103b0127f\n"
		)
		document = pymidiinstrumentdefs.parse(body, source = "x.yaml").sources["midi_impl"]

		assert document.edition == "Revision 1.01"
		assert document.title == "minilogue xd/MIDI Implimentation"
		assert document.landing == "https://example.test/support/product/811/"
		assert document.url == "https://cdn.example.test/files/5227b0b2.txt"

	def test_a_bare_date_is_kept_as_it_prints (self) -> None:
		"""YAML hands `dated: 2020-02-10` over as a date rather than as text.

		It is the obvious way to write one, so a file that looks perfectly correct
		must not be refused for writing it that way.
		"""
		body = "definition: 1\nmodel: {name: X}\nsources: {m: {dated: 2020-02-10}}"
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert definition.sources["m"].dated == "2020-02-10"

	def test_a_printed_page_becomes_a_page_of_the_file (self) -> None:
		"""One manual here prints two pages to a sheet, so printed 21 is sheet 12.

		Its definition cites pp. 21-24 of a file with 19 pages, which is only not a
		contradiction once the sheet count is known.
		"""
		body = "definition: 1\nmodel: {name: X}\nsources: {m: {page_offset: 2, pages_per_sheet: 2}}"
		document = pymidiinstrumentdefs.parse(body, source = "x.yaml").sources["m"]

		assert [document.file_page(printed) for printed in (21, 22, 23, 24)] == [12, 12, 13, 13]

	def test_a_document_with_no_pages_says_so (self) -> None:
		"""A plain-text implementation chart runs to numbered sections, not pages."""
		body = "definition: 1\nmodel: {name: X}\nsources: {m: {paginated: false}}"

		assert pymidiinstrumentdefs.parse(body, source = "x.yaml").sources["m"].file_page(5) is None

	def test_no_sources_section_is_no_error (self) -> None:
		definition = pymidiinstrumentdefs.parse("definition: 1\nmodel: {name: X}", source = "x.yaml")

		assert definition.sources == {}

	def test_a_source_name_must_be_addressable (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nsources: {'Manual': {}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "is not a name" in str(raised.value)

	def test_a_malformed_offset_names_the_entry (self) -> None:
		body = "definition: 1\nmodel: {name: X}\nsources: {m: {page_offset: nine}}"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "sources.m.page_offset" in str(raised.value)


class TestParts:

	def make (self, body: str) -> pymidiinstrumentdefs.Definition:
		"""Parse a fragment that declares parts."""
		return pymidiinstrumentdefs.parse(f"definition: 1\nmodel: {{name: X}}\n{body}", source = "x.yaml")

	def test_a_part_may_be_given_a_channel_of_its_own (self) -> None:
		"""Each of the Digitone's four synth tracks is assigned a channel by the player.

		There is no offset to derive one from, so asking which channel it sits on
		is a question that does not apply, and it says so rather than guessing.
		"""
		part = self.make("parts: {synth: {channel: assigned, count: 4}}").parts["synth"]

		assert part.is_assigned is True
		assert part.channel_for(1) is None
		assert part.count == 4

	def test_a_part_may_derive_its_channel_instead (self) -> None:
		"""The Streichfett's solo section answers one channel above its strings.

		It cannot be set on its own, so the definition records the relationship
		rather than a number.
		"""
		part = self.make("parts: {solo: {channel_offset: 1}}").parts["solo"]

		assert part.is_assigned is False
		assert [part.channel_for(base) for base in (1, 7)] == [2, 8]

	def test_derived_channels_wrap_at_sixteen (self) -> None:
		"""A Voce on a base channel of 15 plays its three parts on 15, 16 and 1.

		The wrap is the manual's own behaviour, not arithmetic tidiness.
		"""
		part = self.make("parts: {voice: {channel_offset: 0, count: 3}}").parts["voice"]

		assert [part.channel_for(15, instance) for instance in (0, 1, 2)] == [15, 16, 1]

	def test_an_instance_the_part_does_not_have_has_no_channel (self) -> None:
		"""A plausible channel for a fourth of three parts would send to nothing at all."""
		part = self.make("parts: {voice: {channel_offset: 0, count: 3}}").parts["voice"]

		with pytest.raises(ValueError):
			part.channel_for(1, 3)

		with pytest.raises(ValueError):
			part.channel_for(1, -1)

	def test_a_base_channel_outside_the_sixteen_is_refused (self) -> None:
		part = self.make("parts: {solo: {channel_offset: 1}}").parts["solo"]

		for base in (0, 17):
			with pytest.raises(ValueError):
				part.channel_for(base)

	def test_a_part_says_which_messages_reach_it (self) -> None:
		"""The Voce's parts take notes and program change; its effects are global to all three.

		No single flag can say that, which is why this is a list.
		"""
		part = self.make("parts: {voice: {channel_offset: 0, receives: [notes, program_change]}}").parts["voice"]

		assert part.takes("notes") is True
		assert part.takes("program_change") is True
		assert part.takes("controls") is False

	def test_a_part_saying_nothing_about_messages_claims_nothing (self) -> None:
		"""Silence is nobody having recorded it, not a checked absence."""
		part = self.make("parts: {solo: {channel_offset: 1}}").parts["solo"]

		assert part.receives is None
		assert part.takes("notes") is False

	def test_a_part_recorded_as_receiving_nothing_is_not_unrecorded (self) -> None:
		"""One lets a consumer offer a note grid a musician can try; the other says not to draw one."""
		part = self.make("parts: {lane: {channel: assigned, receives: []}}").parts["lane"]

		assert part.receives == ()
		assert part.takes("notes") is False

	def test_a_part_nothing_can_address_is_not_assigned_a_channel (self) -> None:
		"""Otherwise a consumer would offer a channel picker for a part nobody said takes one."""
		definition = self.make("parts: {ghost: {label: Ghost}, synth: {channel: assigned}}")

		assert definition.parts["ghost"].is_assigned is False
		assert definition.parts["synth"].is_assigned is True

	def test_controls_are_collected_by_the_part_they_name (self) -> None:
		"""A control naming no part is on the base channel, which is a real case.

		The Streichfett's balance, effects and performance controls are all of
		that kind: its manual prints one generic control change and ties none of
		them to a channel.
		"""
		definition = self.make(
			"parts: {synth: {channel: assigned}, fx: {channel: assigned}}\n"
			"controls:\n"
			"  cutoff: {cc: 23, part: synth}\n"
			"  reverb_amount: {cc: 91, part: fx}\n"
			"  balance: {cc: 82}\n"
		)
		by_part = definition.controls_by_part()

		assert [control.name for control in by_part["synth"]] == ["cutoff"]
		assert [control.name for control in by_part["fx"]] == ["reverb_amount"]
		assert [control.name for control in by_part[""]] == ["balance"]

	def test_a_part_on_the_base_channel_answers_to_the_unparted_controls_too (self) -> None:
		"""A Streichfett's strings take every control, since their channel is the base channel.

		Its solo part, a channel above, takes notes and none of them.
		"""
		streichfett = pymidiinstrumentdefs.load("waldorf/streichfett", [CORPUS])

		assert len(streichfett.controls_reaching("strings")) == len(streichfett.controls) == 19
		assert streichfett.controls_reaching("solo") == []

	def test_a_part_taking_no_controls_is_not_handed_the_instruments_own (self) -> None:
		"""A Voce's parts start on the base channel, but its effects are global to all three."""
		voce = pymidiinstrumentdefs.load("voce/electric_piano", [CORPUS])

		assert [voce.controls_reaching("multi", instance) for instance in (0, 1, 2)] == [[], [], []]

	def test_only_the_instance_on_the_base_channel_takes_the_unparted_controls (self) -> None:
		"""An offset of -1 comes round to the base channel on the second instance, not the first."""
		definition = self.make(
			"parts: {layer: {channel_offset: -1, count: 3, receives: [notes, controls]}}\n"
			"controls:\n"
			"  cutoff: {cc: 23, part: layer}\n"
			"  volume: {cc: 7}\n"
		)
		reaching = [[control.name for control in definition.controls_reaching("layer", instance)] for instance in (0, 1, 2)]

		assert reaching == [["cutoff"], ["cutoff", "volume"], ["cutoff"]]

	def test_an_assigned_part_answers_only_to_its_own_controls (self) -> None:
		"""Whether a player puts it on the base channel is their project's business."""
		definition = self.make(
			"parts: {synth: {channel: assigned, count: 4, receives: [notes, controls]}}\n"
			"controls:\n"
			"  cutoff: {cc: 23, part: synth}\n"
			"  volume: {cc: 7}\n"
		)

		assert [control.name for control in definition.controls_reaching("synth", 3)] == ["cutoff"]

	def test_asking_for_an_instance_or_part_that_does_not_exist_is_refused (self) -> None:
		definition = self.make("parts: {synth: {channel: assigned, count: 4}}")

		with pytest.raises(ValueError):
			definition.controls_reaching("synth", 4)

		with pytest.raises(KeyError):
			definition.controls_reaching("fx")

	def test_the_same_number_means_different_things_in_different_parts (self) -> None:
		"""A Digitone's CC 70 is filter attack on a track and chorus high-pass on the FX channel.

		This is the whole reason parts exist, so it is worth a test of its own.
		"""
		definition = self.make(
			"parts: {synth: {channel: assigned}, fx: {channel: assigned}}\n"
			"controls:\n"
			"  filter_attack: {cc: 70, part: synth}\n"
			"  chorus_high_pass: {cc: 70, part: fx}\n"
		)

		assert definition.controls["filter_attack"].part == "synth"
		assert definition.controls["chorus_high_pass"].part == "fx"

	def test_a_control_naming_a_part_that_does_not_exist_is_refused (self) -> None:
		"""It would be addressed on a channel nothing declares, which fails silently on the wire."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make("parts: {synth: {channel: assigned}}\ncontrols: {cutoff: {cc: 23, part: fx}}")

		assert "controls.cutoff.part" in str(raised.value)

	def test_a_control_on_a_part_that_takes_no_controls_is_refused (self) -> None:
		"""A Streichfett's solo channel takes notes, and a control sent there does nothing.

		That took a measurement to establish on the instrument, so a file that
		says both things at once is refused rather than left to fail on the wire.
		"""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make(
				"parts: {solo: {channel_offset: 1, receives: [notes]}}\n"
				"controls: {solo_tone: {cc: 76, part: solo}}\n"
			)

		assert "controls.solo_tone.part" in str(raised.value)
		assert "receives no controls" in str(raised.value)

	def test_a_control_on_a_part_whose_receiving_is_unrecorded_still_loads (self) -> None:
		"""Nothing is contradicted when nobody recorded what the part receives."""
		definition = self.make(
			"parts: {synth: {channel: assigned}}\n"
			"controls: {cutoff: {cc: 23, part: synth}}\n"
		)

		assert definition.controls["cutoff"].part == "synth"

	def test_a_control_the_instrument_only_transmits_may_sit_on_any_part (self) -> None:
		"""What a part receives says nothing about what the instrument sends from it."""
		definition = self.make(
			"parts: {lane: {channel: assigned, receives: [notes]}}\n"
			"controls: {pressure_out: {cc: 2, part: lane, direction: transmits}}\n"
		)

		assert definition.controls["pressure_out"].part == "lane"

	def test_a_part_cannot_both_be_given_a_channel_and_derive_one (self) -> None:
		"""A reader could not tell which to believe."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make("parts: {synth: {channel: assigned, channel_offset: 1}}")

		assert "parts.synth" in str(raised.value)

	def test_a_part_nothing_can_address_warns (self) -> None:
		"""Declared, but with no way to reach it — the same shape as a control with no cc or nrpn."""
		definition = self.make("parts: {ghost: {label: Ghost}}")

		assert any("nothing can address it" in warning for warning in definition.warnings)

	def test_a_message_kind_nobody_knows_is_refused (self) -> None:
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make("parts: {synth: {channel: assigned, receives: [notes, aftertouch]}}")

		assert "parts.synth.receives" in str(raised.value)

	def test_a_repeated_message_kind_is_refused (self) -> None:
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make("parts: {synth: {channel: assigned, receives: [notes, notes]}}")

		assert "twice" in str(raised.value)

	def test_a_part_addresses_notes_the_way_the_instrument_does (self) -> None:
		"""`addressing` reuses the vocabulary `voice` already has, and is refused otherwise."""
		assert self.make("parts: {p: {channel_offset: 0, addressing: voices}}").parts["p"].addressing == "voices"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make("parts: {p: {channel_offset: 0, addressing: sideways}}")

		assert "parts.p.addressing" in str(raised.value)

	def test_a_part_name_must_be_addressable (self) -> None:
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make("parts: {'Synth Track': {channel: assigned}}")

		assert "is not a name" in str(raised.value)

	def test_no_parts_section_is_no_error (self) -> None:
		"""Fourteen definitions rely on this, and an instrument with no parts has one."""
		definition = pymidiinstrumentdefs.parse("definition: 1\nmodel: {name: X}", source = "x.yaml")

		assert definition.parts == {}


class TestPolyphonyAcrossParts:

	def make (self, body: str) -> pymidiinstrumentdefs.Definition:
		"""Parse a fragment that declares parts and says something about their voices."""
		return pymidiinstrumentdefs.parse(f"definition: 1\nmodel: {{name: X}}\nsource: hand\n{body}", source = "x.yaml")

	def test_parts_may_draw_on_one_pool (self) -> None:
		"""A Digitone's eight voices go to whichever of its four tracks plays next.

		So eight is a ceiling across all of them, not a figure each can count on.
		"""
		definition = self.make(
			"parts: {synth: {channel: assigned, count: 4}}\n"
			"voice: {polyphony: 8, polyphony_shared: true}\n"
		)

		assert definition.voice.polyphony == 8
		assert definition.voice.polyphony_shared is True
		assert definition.parts["synth"].polyphony is None
		assert definition.warnings == ()

	def test_a_part_may_have_voices_of_its_own (self) -> None:
		"""Counted per instance: three parts at eight voices is eight each."""
		definition = self.make(
			"parts: {voice: {channel_offset: 0, count: 3, polyphony: 8}}\n"
			"voice: {polyphony_shared: false}\n"
		)

		assert definition.parts["voice"].polyphony == 8
		assert definition.warnings == ()

	def test_saying_nothing_about_sharing_claims_nothing (self) -> None:
		"""Absent is nobody having recorded it, not a checked answer either way."""
		definition = self.make("parts: {synth: {channel: assigned}}")

		assert definition.voice.polyphony_shared is None
		assert definition.warnings == ()

	def test_sharing_between_parts_needs_parts (self) -> None:
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make("voice: {polyphony: 8, polyphony_shared: true}")

		assert "voice.polyphony_shared" in str(raised.value)

	def test_one_pool_and_a_part_with_its_own_is_refused (self) -> None:
		"""A consumer would be told two different things about how many notes that part holds."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make(
				"parts: {synth: {channel: assigned, polyphony: 4}}\n"
				"voice: {polyphony: 8, polyphony_shared: true}\n"
			)

		assert "parts.synth.polyphony" in str(raised.value)

	def test_one_figure_for_parts_that_do_not_share_is_refused (self) -> None:
		"""136 for a Streichfett is a number its maker never states and no section has."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make(
				"parts: {strings: {channel_offset: 0}, solo: {channel_offset: 1}}\n"
				"voice: {polyphony: 136, polyphony_shared: false}\n"
			)

		assert "voice.polyphony: gives one figure" in str(raised.value)
		assert "each part has voices of its own" in str(raised.value)

	def test_a_figure_for_the_instrument_and_for_a_part_is_refused (self) -> None:
		"""Even without saying whether they share, the two cannot both be the answer."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make(
				"parts: {solo: {channel_offset: 1, polyphony: 8}}\n"
				"voice: {polyphony: 8}\n"
			)

		assert "voice.polyphony: gives one figure" in str(raised.value)
		assert "parts.solo gives voices of its own" in str(raised.value)

	def test_a_part_with_its_own_voices_asks_for_sharing_to_be_said (self) -> None:
		"""Otherwise asking the instrument whether its parts share gets no answer."""
		definition = self.make("parts: {solo: {channel_offset: 1, polyphony: 8}}")

		assert any("polyphony_shared: false" in warning for warning in definition.warnings)

	def test_one_figure_for_an_instrument_with_parts_asks_what_it_covers (self) -> None:
		"""Eight across four tracks and eight on each are very different instruments."""
		definition = self.make(
			"parts: {synth: {channel: assigned, count: 4}}\n"
			"voice: {polyphony: 8}\n"
		)

		assert any("whether they share it" in warning for warning in definition.warnings)

	def test_an_instrument_with_no_parts_is_unchanged (self) -> None:
		"""Every definition written before parts still says polyphony the way it always did."""
		definition = self.make("voice: {polyphony: 5}")

		assert definition.voice.polyphony == 5
		assert definition.voice.polyphony_shared is None
		assert definition.warnings == ()


class TestSearchPath:

	def test_the_nearest_definition_wins (self, tmp_path: pathlib.Path) -> None:
		"""A file you drop beats one from a library, which beats one we shipped.

		That is the whole answer to adding your own synth.
		"""
		near = tmp_path / "near"
		far = tmp_path / "far"

		write(near, "moog/dfam", "definition: 1\nmodel: {name: Mine}\nsource: hand\n")
		write(far, "moog/dfam", "definition: 1\nmodel: {name: Theirs}\nsource: hand\n")

		found = pymidiinstrumentdefs.load("moog/dfam", [near, far])

		assert found.model.name == "Mine"

	def test_a_file_beside_the_project_overrides_a_bundled_one (
		self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
	) -> None:
		"""The default search path, as a project would use it, with nothing passed in."""
		monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "library"))
		monkeypatch.chdir(tmp_path)

		assert pymidiinstrumentdefs.load("moog/dfam").model.name == "DFAM"

		write(tmp_path / "instruments", "moog/dfam", "definition: 1\nmodel: {name: Mine}\nsource: hand\n")

		assert pymidiinstrumentdefs.load("moog/dfam").model.name == "Mine"

	def test_a_missing_definition_says_where_it_looked (self, tmp_path: pathlib.Path) -> None:
		"""And names the file it would have needed, so the fix is to put one there."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionNotFound) as raised:
			pymidiinstrumentdefs.load("moog/nothing_here", [tmp_path])

		assert str(tmp_path / "moog" / "nothing_here.yaml") in str(raised.value)

	def test_available_lists_each_name_once (self, tmp_path: pathlib.Path) -> None:
		near = tmp_path / "near"
		far = tmp_path / "far"

		write(near, "moog/dfam", MINIMAL)
		write(far, "moog/dfam", MINIMAL)
		write(far, "moog/minitaur", MINIMAL)

		assert pymidiinstrumentdefs.available([near, far]) == ["moog/dfam", "moog/minitaur"]

	def test_a_file_outside_a_makers_folder_has_no_name (self, tmp_path: pathlib.Path) -> None:
		"""The old flat layout: listed nowhere, and not found by its old name."""
		write(tmp_path, "moog_dfam", MINIMAL)

		assert pymidiinstrumentdefs.available([tmp_path]) == []

		with pytest.raises(pymidiinstrumentdefs.DefinitionError):
			pymidiinstrumentdefs.load("moog_dfam", [tmp_path])

	@pytest.mark.parametrize("name", [
		"moog_matriarch",
		"Moog/matriarch",
		"moog/Matriarch",
		"moog/",
		"/matriarch",
		"moog/matriarch/extra",
		"../moog/matriarch",
		"moog/../matriarch",
		"moog/matriarch.yaml",
	])
	def test_a_name_is_a_maker_and_a_model (self, name: str, tmp_path: pathlib.Path) -> None:
		"""Refused before any path is built, so a name can never reach outside a search directory."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.load(name, [tmp_path])

		assert "moog/matriarch" in str(raised.value)

	def test_a_file_name_must_be_addressable (self, tmp_path: pathlib.Path) -> None:
		path = write(tmp_path, "moog/Moog Matriarch", MINIMAL)

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.load_file(path)

		assert "moog/matriarch" in str(raised.value)


class TestFirmware:

	def make (self, body: str) -> pymidiinstrumentdefs.Definition:
		"""Parse a fragment whose model says something about firmware."""
		return pymidiinstrumentdefs.parse(f"definition: 1\nsource: hand\n{body}", source = "x.yaml")

	def test_a_definition_says_which_firmware_it_describes (self) -> None:
		"""What an instrument answers to changes when it is updated, so the version is a fact.

		A Minitaur before 2.1 ignores a note above its top octave; from 2.1 it
		sounds the equivalent pitch.
		"""
		minitaur = pymidiinstrumentdefs.load("moog/minitaur", [CORPUS])

		assert minitaur.model.firmware == "2.1"
		assert minitaur.model.states_no_firmware is False

	def test_an_instrument_with_no_firmware_can_say_so (self) -> None:
		"""An analogue instrument has none, which is established rather than assumed."""
		model = self.make("model: {name: X, firmware: none}").model

		assert model.states_no_firmware is True

	def test_saying_nothing_about_firmware_claims_nothing (self) -> None:
		"""Silence is nobody having looked, which is not the same as having none."""
		model = self.make("model: {name: X}").model

		assert model.firmware is None
		assert model.states_no_firmware is False

	def test_a_version_written_without_quotes_is_refused (self) -> None:
		"""YAML reads 1.10 as 1.1, and a maker shipping both would have one recorded as the other."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			self.make("model: {name: X, firmware: 1.10}")

		assert "model.firmware" in str(raised.value)
		assert "Quote it" in str(raised.value)

	def test_a_version_in_quotes_keeps_every_digit (self) -> None:
		assert self.make('model: {name: X, firmware: "1.10"}').model.firmware == "1.10"

	def test_a_hardware_revision_is_not_firmware (self) -> None:
		"""A Vermona DRM1 MkIV is not a MkIII, and that is a different kind of fact."""
		drm1 = pymidiinstrumentdefs.load("vermona/drm1_mkiv", [CORPUS])

		assert drm1.model.revision == "MkIV"
		assert drm1.model.firmware is None


class TestPublicSurface:

	def test_every_type_a_definition_hands_out_is_importable_from_the_package (self) -> None:
		"""So a consumer can annotate what it holds without reaching into a submodule."""
		assert pymidiinstrumentdefs.Part is pymidiinstrumentdefs.definition.Part
		assert pymidiinstrumentdefs.Source is pymidiinstrumentdefs.definition.Source
		assert {"Part", "Source"} <= set(pymidiinstrumentdefs.__all__)


class TestGrouping:

	def test_controls_collect_by_group_in_file_order (self) -> None:
		"""A flat list of forty controls is unreadable before it is unusable."""
		matriarch = pymidiinstrumentdefs.load("moog/matriarch", [CORPUS])
		groups = matriarch.grouped_controls()

		assert groups["oscillator"][0].name == "osc_2_frequency"
		assert len(groups["arpeggiator"]) == 9

	def test_panel_first_is_opt_in_and_stable (self) -> None:
		"""Nothing ranks by default: the flag is a strong hint and a poor rule."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"controls:\n"
			"  a: {cc: 1}\n"
			"  b: {cc: 2, panel_only: true}\n"
			"  c: {cc: 3}\n"
		)
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert list(definition.controls) == ["a", "b", "c"]
		assert [control.name for control in definition.panel_first()] == ["b", "a", "c"]

	def test_a_label_says_what_to_head_the_table_with (self) -> None:
		"""A group is an identifier, and `mod_1` is not what the maker calls it."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"groups:\n"
			"  mod_1: Mod Slot 1\n"
			"controls:\n"
			"  mod_1_source: {cc: 1, group: mod_1}\n"
		)
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert definition.groups == {"mod_1": "Mod Slot 1"}
		assert definition.groups["mod_1"] == "Mod Slot 1"

	def test_labels_set_the_order_the_groups_are_shown_in (self) -> None:
		"""A maker's panel does not always run in the order its controller numbers do."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"groups:\n"
			"  oscillator: Oscillators\n"
			"  filter: Filter\n"
			"controls:\n"
			"  cutoff: {cc: 74, group: filter}\n"
			"  tune:   {cc: 70, group: oscillator}\n"
		)
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert list(definition.controls) == ["cutoff", "tune"]
		assert list(definition.grouped_controls()) == ["oscillator", "filter"]

	def test_an_unlabelled_group_follows_the_labelled_ones_in_file_order (self) -> None:
		"""Labelling some groups and not others is a file part way through, not an error."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"groups:\n"
			"  envelope: Envelope\n"
			"controls:\n"
			"  cutoff: {cc: 74, group: filter}\n"
			"  attack: {cc: 73, group: envelope}\n"
			"  tune:   {cc: 70, group: oscillator}\n"
		)
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert list(definition.grouped_controls()) == ["envelope", "filter", "oscillator"]
		assert definition.warnings == ()

	def test_a_label_no_control_joined_warns_and_is_not_shown (self) -> None:
		"""A heading that never appears is a mistyped group name, or a section not yet read."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"groups:\n"
			"  filter: Filter\n"
			"  revreb: Reverb\n"
			"controls:\n"
			"  cutoff: {cc: 74, group: filter}\n"
		)
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert any("groups.revreb" in warning for warning in definition.warnings)
		assert list(definition.grouped_controls()) == ["filter"]

	def test_an_empty_label_is_refused (self) -> None:
		"""Nothing at all is worse than the group's own name, which is at least true."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"groups: {filter: ' '}\n"
			"controls: {cutoff: {cc: 74, group: filter}}\n"
		)

		with pytest.raises(pymidiinstrumentdefs.DefinitionError, match = "groups.filter"):
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

	def test_a_label_is_prose_and_the_group_is_a_name (self) -> None:
		"""The label is for a reader, so it takes the maker's spelling, spaces and all."""
		body = (
			"definition: 1\nmodel: {name: X}\nsource: hand\n"
			"groups: {arp_seq: 'ARP / SEQ'}\n"
			"controls: {rate: {cc: 1, group: arp_seq}}\n"
		)
		definition = pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert definition.groups["arp_seq"] == "ARP / SEQ"

		with pytest.raises(pymidiinstrumentdefs.DefinitionError, match = "is not a name"):
			pymidiinstrumentdefs.parse(
				body.replace("arp_seq: 'ARP / SEQ'", "'Arp Seq': 'ARP / SEQ'"), source = "x.yaml")


class TestOsmose:

	"""The first MPE instrument the format says is one, rather than only describing in prose."""

	def test_its_voices_take_a_channel_each_and_the_field_says_so (self) -> None:
		"""Grepping a comment is not a way to find out, so the flag answers it."""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		assert osmose.midi.per_voice_channels is True

		# Channel 1 is the master and 15 and 16 are the Haken Editor's, so the chart's
		# range stops at 14 rather than at 16.
		assert osmose.midi.channels == (1, 14)

	def test_every_mpe_instrument_is_found_by_the_field_alone (self) -> None:
		"""The Carbon8M was corrected with the Osmose so the corpus answers one way.

		A consumer asking which instruments spread their voices across channels has to
		get all of them or none; one flagged and one not is worse than none, because it
		reads as a settled answer and is wrong about the one it misses. There are four
		now, and the Deluge is the first that is a sequencer as much as a synthesizer -
		it reads a zone of channels as one instrument and writes one out too.
		"""
		flagged = sorted(name for name in pymidiinstrumentdefs.available([CORPUS])
			if pymidiinstrumentdefs.load(name, [CORPUS]).midi.per_voice_channels)

		assert flagged == ["expressive_e/osmose", "modal/carbon8m",
			"synthstrom_audible/deluge", "waldorf/iridium"]

	def test_velocity_is_ignored_though_every_key_is_velocity_sensitive (self) -> None:
		"""MPE+ carries a flow of pressure instead, and the chart answers No both ways."""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		assert osmose.voice.velocity is not None
		assert osmose.voice.velocity.note_on == "ignored"
		assert osmose.voice.velocity.note_off is False

	def test_it_takes_clock_and_sends_none_though_its_chart_claims_both (self) -> None:
		"""Two first-tier documents disagreed and the manual's plain sentence won.

		The chart marks clock, song position, start, continue and stop as transmitted;
		the manual says the instrument "is not capable of sending its own internal
		clock", and nothing in its settings offers a way to.
		"""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		assert osmose.midi.clock == "receives"
		assert osmose.midi.transport == "receives"

	def test_the_eq_has_two_numbers_and_neither_is_a_control (self) -> None:
		"""Its chart prints a range for both and marks both as answering to nothing.

		Making them controls would assert what no document states, so the file records
		the contradiction instead and declares no group for the eq at all.
		"""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		numbered = {control.cc for control in osmose.controls.values()}

		assert 83 not in numbered and 84 not in numbered
		assert "eq" not in osmose.groups

	def test_the_sustain_pedal_is_continuous_where_cc_64_is_usually_a_switch (self) -> None:
		"""On this instrument sustain fades and swells, so 0-127 is the point of it."""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		pedal = osmose.controls["pedal_1"]

		assert pedal.cc == 64
		assert pedal.range == (0, 127)
		assert pedal.kind == pymidiinstrumentdefs.CONTINUOUS

	def test_bank_select_is_the_one_control_it_only_receives (self) -> None:
		"""Every other control travels both ways, which is what its chart gives."""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		receives_only = [control.name for control in osmose.controls.values()
			if control.direction == "receives"]

		assert receives_only == ["bank_select"]
		assert osmose.controls["bank_select"].cc == 0

	def test_its_17_controls_are_the_chart_rows_that_answer_to_anything (self) -> None:
		"""126 rows, 34 named, and these are the ones marked Yes in either direction.

		The other 17 named rows are excluded for stated reasons: seven channel mode
		messages, four NRPN and RPN number controllers, two data entry rows, aftertouch,
		the two the eq test covers, and the controller that carries a pressure value's
		low seven bits rather than a parameter.
		"""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		assert len(osmose.controls) == 17
		assert {control.cc for control in osmose.controls.values()} == {
			0, 1, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 26, 64, 93}

		# None of the excluded numbers crept in: 74 and 87 are the two that name something
		# real and are still not parameters.
		for number in (6, 38, 74, 83, 84, 87, 98, 99, 100, 101, 120, 126):
			assert number not in {control.cc for control in osmose.controls.values()}

	def test_it_answers_to_no_nrpn_and_no_system_exclusive (self) -> None:
		"""Checked absences from the chart, not pages nobody read."""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		assert osmose.midi.nrpn == "none"
		assert osmose.midi.sysex is False

	def test_its_presets_are_counted_from_the_makers_own_list (self) -> None:
		"""529 factory and 80 expansion, where the product page says 580 and means neither."""
		osmose = pymidiinstrumentdefs.load("expressive_e/osmose", [CORPUS])

		assert osmose.midi.program_change is not None
		assert osmose.midi.program_change.presets == 609
		assert osmose.midi.program_change.receives is True
		assert osmose.midi.program_change.sends is False


class TestOP1:

	"""The first definition with no paginated source and no controller number to carry."""

	def test_its_controllers_are_the_players_and_it_has_no_controls (self) -> None:
		"""Four incoming control changes, routed per sound, and no factory map to publish."""
		op1 = pymidiinstrumentdefs.load("teenage_engineering/op_1", [CORPUS])

		assert op1.midi.learns_control_change
		assert op1.controls == {}
		assert op1.groups == {}

		# Which is not the same as answering to no controller at all, where somebody
		# checked and found none: that is the MODEL D, and it reads differently.
		assert not op1.midi.refuses_control_change

	def test_every_one_of_its_sources_has_no_pages (self) -> None:
		"""Its maker publishes a website, so the definition cites sections instead.

		This is the first definition in the corpus where that is true of every source,
		and `test_every_bundled_definition_cites_a_locator` holds it to naming sections
		as firmly as it holds the others to naming pages.
		"""
		op1 = pymidiinstrumentdefs.load("teenage_engineering/op_1", [CORPUS])

		assert len(op1.sources) == 8
		assert all(not source.paginated for source in op1.sources.values())
		assert all(source.file_page(1) is None for source in op1.sources.values())

	def test_its_firmware_is_spelled_the_way_its_maker_spells_it (self) -> None:
		"""A hash and no dots, which is teenage engineering's own numbering."""
		op1 = pymidiinstrumentdefs.load("teenage_engineering/op_1", [CORPUS])

		assert op1.model.firmware == "#246"
		assert not op1.model.states_no_firmware

	def test_it_sends_and_receives_clock_by_a_setting (self) -> None:
		"""Three named modes: one sends, one receives, and one does neither."""
		op1 = pymidiinstrumentdefs.load("teenage_engineering/op_1", [CORPUS])

		assert op1.midi.clock == "both"

		# Transport is left unrecorded, because the one sentence bearing on it will not
		# say whether a "play command" is a MIDI start or the unit's own key.
		assert op1.midi.transport is None

	def test_system_exclusive_comes_from_the_release_notes_alone (self) -> None:
		"""The guide never mentions it; a firmware note says the identity reply was fixed.

		Which is why the firmware above is part of that claim: before #243 the instrument
		answered an identity request with zeros.
		"""
		op1 = pymidiinstrumentdefs.load("teenage_engineering/op_1", [CORPUS])

		assert op1.midi.sysex is True
		assert "os_updates" in op1.sources
		assert op1.sources["os_updates"].kind == "release_notes"

	def test_what_is_left_unrecorded_is_left_out_rather_than_guessed (self) -> None:
		"""A default channel with no stated range is not a range, and 1-16 is not implied."""
		op1 = pymidiinstrumentdefs.load("teenage_engineering/op_1", [CORPUS])

		assert op1.midi.channels is None
		assert op1.midi.nrpn is None
		assert op1.midi.program_change is None
		assert op1.voice.polyphony is None
		assert op1.voice.note_range is None
		assert op1.voice.velocity is None


class TestOpXy:

	"""The first definition whose maker publishes one guide twice and disagrees with itself."""

	def test_it_carries_eleven_of_the_twelve_rows_its_table_prints (self) -> None:
		"""The twelfth row is the one the maker's two editions give different numbers for.

		One prints the track's parameters as CC 12-47 and the other as CC 46, so there is
		no honest value for a field that holds one number, and no control is written.
		"""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])

		numbers = [control.cc for control in op_xy.controls.values() if control.cc is not None]

		assert len(op_xy.controls) == 11
		assert sorted(numbers) == [7, 9, 10, 80, 81, 82, 83, 84, 85, 86, 90]

		# Neither of the two disputed numbers is anywhere in the file, and 46 in
		# particular must not creep in: it is one edition's reading of a range.
		assert 46 not in numbers

	def test_both_editions_of_the_guide_are_cited (self) -> None:
		"""A disagreement nobody kept both halves of is just an assertion.

		Seven of the eight sources have no pages, and one does: the printable guide,
		which is the only paginated document this maker has ever published here.
		"""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])

		paginated = [name for name, source in op_xy.sources.items() if source.paginated]

		assert len(op_xy.sources) == 8
		assert paginated == ["guide"]
		assert "midi_cc_table" in op_xy.sources

	def test_the_printable_guide_turns_its_pages_by_five (self) -> None:
		"""And is cited nowhere below printed page 53, where that stops being true.

		An unnumbered overflow page sits between printed 52 and 53, so the offset is 4
		before it and 5 after. The source records the run it is cited in.
		"""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])
		guide = op_xy.sources["guide"]

		assert guide.page_offset == 5
		assert guide.file_page(122) == 127
		assert guide.file_page(53) == 58

	def test_its_sixteen_tracks_are_one_part_on_channels_the_player_sets (self) -> None:
		"""Eight instrument tracks and eight auxiliary, and the table reaches all of them."""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])
		track = op_xy.parts["track"]

		assert len(op_xy.parts) == 1
		assert track.count == 16
		assert track.is_assigned
		assert track.takes("notes") and track.takes("controls")

		# Assigned, so there is no base channel to derive one from, and asking is told so.
		assert track.channel_for(1) is None

		# The four controls that name a track are the rows whose channel column reads 1-16.
		named = {name for name, control in op_xy.controls.items() if control.part == "track"}

		assert named == {"track_volume", "track_mute", "track_pan"}

	def test_twenty_four_voices_shared_across_those_tracks (self) -> None:
		"""A ceiling for all sixteen together, not a figure each track can count on."""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])

		assert op_xy.voice.polyphony == 24
		assert op_xy.voice.polyphony_shared is True

		# Three play modes are named - poly, mono and legato - and no count is given for
		# any of them, so the field that holds counts stays empty.
		assert op_xy.voice.voicing_modes == ()

	def test_what_the_guide_never_says_is_left_unrecorded (self) -> None:
		"""Including two things it mentions without ever specifying them.

		Aftertouch is received and routable, but neither edition says whether it is
		channel or polyphonic; the bend range is a setting, but how far it reaches is
		never printed.
		"""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])

		assert op_xy.voice.aftertouch is None
		assert op_xy.voice.note_range is None
		assert op_xy.midi.nrpn is None
		assert op_xy.midi.sysex is None

		assert op_xy.voice.pitch_bend is not None
		assert op_xy.voice.pitch_bend.programmable is True
		assert op_xy.voice.pitch_bend.semitones is None

	def test_transport_is_received_and_not_claimed_both_ways (self) -> None:
		"""One release note says incoming transport is relayed, and nothing says it sends.

		Clock is different: both editions describe it travelling each way, and over
		Bluetooth as well.
		"""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])

		assert op_xy.midi.transport == "receives"
		assert op_xy.midi.clock == "both"

	def test_it_sends_a_program_change_and_says_nothing_about_receiving_one (self) -> None:
		"""The external MIDI track selects a bank and a program on something else."""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])

		assert op_xy.midi.program_change is not None
		assert op_xy.midi.program_change.sends is True
		assert op_xy.midi.program_change.receives is None
		assert op_xy.midi.program_change.presets is None

	def test_its_firmware_is_the_one_its_guide_describes (self) -> None:
		"""Dotted, unlike the OP-1's hash, because this guide is numbered to a release.

		The maker publishes a later firmware than the guide covers, which is recorded in
		the file rather than quietly rounded up to the newest.
		"""
		op_xy = pymidiinstrumentdefs.load("teenage_engineering/op_xy", [CORPUS])

		assert op_xy.model.firmware == "1.1.15"
		assert op_xy.sources["guide"].edition == "1.1.15"
		assert op_xy.sources["os_updates"].edition == "1.1.33"


class TestMother32:

	"""Seven controllers, four of which reach a patch cable rather than a parameter."""

	def test_the_four_controllers_that_reach_no_parameter (self) -> None:
		"""CC 1, 2, 4 and 7 become a voltage at a jack, and only one at a time.

		They are controls because the instrument answers to them, and the file says what
		answering amounts to.
		"""
		mother = pymidiinstrumentdefs.load("moog/mother_32", [CORPUS])

		assignable = sorted(control.cc for control in mother.controls.values()
			if control.group == "assignable" and control.cc is not None)

		assert assignable == [1, 2, 4, 7]
		assert len(mother.controls) == 7

		# The three that do reach something: portamento twice and sustain.
		assert mother.controls["portamento_time"].cc == 5
		assert mother.controls["portamento_on_off"].cc == 65
		assert mother.controls["sustain"].cc == 64

	def test_every_note_does_something_so_the_range_is_the_whole_span (self) -> None:
		"""Notes 121 to 127 fold back onto 109 to 115 rather than falling silent."""
		mother = pymidiinstrumentdefs.load("moog/mother_32", [CORPUS])

		assert mother.voice.note_range == (0, 127)
		assert mother.voice.plays_note(127)
		assert mother.voice.polyphony == 1

	def test_aftertouch_is_channel_and_the_maker_says_so (self) -> None:
		"""Twice over, which is rarer in this corpus than it ought to be."""
		mother = pymidiinstrumentdefs.load("moog/mother_32", [CORPUS])

		assert mother.voice.aftertouch == "channel"

		assert mother.voice.pitch_bend is not None
		assert mother.voice.pitch_bend.semitones == 12
		assert mother.voice.pitch_bend.programmable is True

	def test_it_receives_and_does_not_send (self) -> None:
		"""One MIDI socket, and it is an input."""
		mother = pymidiinstrumentdefs.load("moog/mother_32", [CORPUS])

		assert mother.midi.clock == "receives"
		assert mother.midi.transport == "receives"
		assert mother.midi.channels == (1, 16)

		assert mother.midi.program_change is not None
		assert mother.midi.program_change.receives is True
		assert mother.midi.program_change.sends is None
		assert mother.midi.program_change.presets == 64

		# Neither system exclusive nor NRPN is described, so neither is claimed.
		assert mother.midi.sysex is None
		assert mother.midi.nrpn is None

	def test_its_firmware_comes_from_a_package_name (self) -> None:
		"""Which is the only place Moog ever states one."""
		mother = pymidiinstrumentdefs.load("moog/mother_32", [CORPUS])

		assert mother.model.firmware == "2.0.1"
		assert mother.sources["manual"].page_offset == 1
		assert not mother.sources["downloads"].paginated


class TestOpsix:

	"""A control map on one page whose text is enciphered, and a manual covering three models."""

	def test_the_five_controls_it_recognises_and_never_sends (self) -> None:
		"""The chart has two columns, and where they differ the control says so."""
		opsix = pymidiinstrumentdefs.load("korg/opsix", [CORPUS])

		receives = sorted(name for name, control in opsix.controls.items()
			if control.direction == "receives")

		assert receives == ["expression", "pan", "soft", "sostenuto", "volume"]

		# `receives` means the instrument answers to it and never sends it, so a panel may
		# still offer it: these are sendable, and nothing in this definition is not.
		assert all(control.is_sendable for control in opsix.controls.values())

		# Everything else travels both ways, which is the default and is not written out.
		assert len(opsix.controls) == 30
		assert sum(1 for control in opsix.controls.values() if control.direction == "both") == 25

	def test_the_two_runs_of_six_became_twelve_controls (self) -> None:
		"""The chart gives 102-107 and 108-113 as two entries naming six operators each."""
		opsix = pymidiinstrumentdefs.load("korg/opsix", [CORPUS])

		levels = [opsix.controls[f"op{n}_level"].cc for n in range(1, 7)]
		ratios = [opsix.controls[f"op{n}_ratio"].cc for n in range(1, 7)]

		assert levels == [102, 103, 104, 105, 106, 107]
		assert ratios == [108, 109, 110, 111, 112, 113]

		# The channel mode pair the chart also lists is not a control and must never become one.
		assert not {120, 121} & {control.cc for control in opsix.controls.values()}

	def test_the_chart_is_cited_through_a_rendering_of_itself (self) -> None:
		"""Its page cannot be searched, so the definition cites a decoded copy.

		Four sources, of which only the manual has pages: the chart's rendering, Korg's
		Property Exchange file and the download page have none.
		"""
		opsix = pymidiinstrumentdefs.load("korg/opsix", [CORPUS])

		paginated = [name for name, source in opsix.sources.items() if source.paginated]

		assert len(opsix.sources) == 4
		assert paginated == ["manual"]
		assert opsix.sources["manual"].page_offset == 0
		assert opsix.sources["chart"].sha256 != opsix.sources["manual"].sha256

	def test_it_is_the_opsix_and_not_the_two_models_beside_it (self) -> None:
		"""One manual, three instruments, and the voice counts are not the same."""
		opsix = pymidiinstrumentdefs.load("korg/opsix", [CORPUS])

		assert opsix.model.name == "opsix"
		assert opsix.voice.polyphony == 32

		# The chart's version is the instrument's, which the manual's own body settles by
		# naming the same number as a system version.
		assert opsix.model.firmware == "3.1.0"

	def test_release_velocity_both_ways_and_no_aftertouch_recorded (self) -> None:
		"""It answers to both kinds of aftertouch, which this field cannot say."""
		opsix = pymidiinstrumentdefs.load("korg/opsix", [CORPUS])

		assert opsix.voice.velocity is not None
		assert opsix.voice.velocity.note_on == "received"
		assert opsix.voice.velocity.note_off is True

		assert opsix.voice.aftertouch is None
		assert opsix.voice.note_range == (0, 127)

	def test_what_its_chart_marks_in_both_directions (self) -> None:
		"""Clock, transport, program change and system exclusive all travel each way."""
		opsix = pymidiinstrumentdefs.load("korg/opsix", [CORPUS])

		assert opsix.midi.clock == "both"
		assert opsix.midi.transport == "both"
		assert opsix.midi.sysex is True
		assert opsix.midi.mode == 3
		assert opsix.midi.nrpn is None

		assert opsix.midi.program_change is not None
		assert opsix.midi.program_change.receives is True
		assert opsix.midi.program_change.sends is True
		assert opsix.midi.program_change.presets == 100


class TestBassStationII:

	"""One guide for three products, and a number its own maker probably mistyped."""

	def test_the_mod_wheel_carries_the_number_the_guide_prints (self) -> None:
		"""Which is 0, where the specification puts the modulation wheel at 1.

		CC 0 is Bank Select MSB everywhere else in MIDI, so this is very hard to believe -
		and it is what the only document says, read at 900 dpi by two readers. The rule is
		that a definition carries what the maker published and doubts it in writing.
		"""
		synth = pymidiinstrumentdefs.load("novation/bass_station_ii", [CORPUS])

		assert synth.controls["other_mod"].cc == 0
		assert synth.controls["other_sustain"].cc == 64

	def test_the_mixer_pair_the_guide_mistyped_is_carried_as_the_sequence_requires (self) -> None:
		"""Printed `23.55` where its four neighbours are printed with a colon.

		20:52, 21:53, 22:54 and 24:56 leave `noise level` nothing else to be.
		"""
		synth = pymidiinstrumentdefs.load("novation/bass_station_ii", [CORPUS])
		mixer = synth.controls["mixer_noise_level"]

		assert (mixer.cc, mixer.lsb) == (23, 55)
		assert mixer.is_14_bit

		# Every pair in the guide is n and n+32, which is what makes 23 and 55 the only reading.
		paired = [control for control in synth.controls.values() if control.is_14_bit]

		assert len(paired) == 16
		assert all(control.lsb == control.cc + 32 for control in paired
			if control.cc is not None and control.lsb is not None)

	def test_the_two_nrpns_the_guide_publishes_twice (self) -> None:
		"""Under different names in different sections of the one table, so both are kept."""
		synth = pymidiinstrumentdefs.load("novation/bass_station_ii", [CORPUS])

		assert synth.controls["lfos_lfo_1_sync_value"].nrpn == 87
		assert synth.controls["lfo_speed_sync_lfo_1"].nrpn == 87
		assert synth.controls["lfos_lfo_2_sync_value"].nrpn == 91
		assert synth.controls["lfo_speed_sync_lfo_2"].nrpn == 91

		numbers = [control.nrpn for control in synth.controls.values() if control.nrpn is not None]

		assert len(numbers) == 31
		assert len(set(numbers)) == 29

	def test_it_is_monophonic_and_paraphonic_is_a_flag_not_a_count (self) -> None:
		"""Two oscillators on two keys still share one amplifier and one filter."""
		synth = pymidiinstrumentdefs.load("novation/bass_station_ii", [CORPUS])

		assert synth.voice.polyphony == 1
		assert synth.voice.paraphonic is True
		assert synth.voice.note_range is None

		# The guide gives three different pitch bend ranges, so no number is written.
		assert synth.voice.pitch_bend is not None
		assert synth.voice.pitch_bend.programmable is True
		assert synth.voice.pitch_bend.semitones is None

		# The keyboard has aftertouch and the guide never says which kind.
		assert synth.voice.aftertouch is None

	def test_what_the_guide_establishes_and_what_it_leaves_alone (self) -> None:
		"""Clock only one way, and transport not at all."""
		synth = pymidiinstrumentdefs.load("novation/bass_station_ii", [CORPUS])

		assert synth.midi.clock == "receives"
		assert synth.midi.transport is None
		assert synth.midi.sysex is True
		assert synth.midi.nrpn == "supported"
		assert synth.midi.channels == (1, 16)

		assert synth.midi.program_change is not None
		assert synth.midi.program_change.presets == 128

	def test_its_guide_needs_no_page_turning (self) -> None:
		"""Every page prints its own number and it is the file's own page index."""
		synth = pymidiinstrumentdefs.load("novation/bass_station_ii", [CORPUS])
		guide = synth.sources["guide"]

		assert guide.page_offset == 0
		assert guide.file_page(71) == 71
		assert len(synth.controls) == 94

		# Sixteen panel sections, one of them labelled a page before the rows it covers.
		assert len(synth.groups) == 16
		assert synth.groups["effects"] == "Effects"
		assert synth.controls["effects_distortion"].group == "effects"


class TestMicroKorg:

	"""Numbers that are a factory assignment rather than a fact, out of two documents."""

	def test_its_control_map_is_split_across_two_documents (self) -> None:
		"""The implementation gives the NRPNs and no controller number; the manual gives those.

		Neither half is in the other, which is why this is the first definition to cite a
		maker's implementation and its manual for different parts of one map.
		"""
		microkorg = pymidiinstrumentdefs.load("korg/microkorg", [CORPUS])

		changes = [control for control in microkorg.controls.values() if control.cc is not None]
		numbers = [control for control in microkorg.controls.values() if control.nrpn is not None]

		assert len(microkorg.controls) == 71
		assert len(changes) == 42
		assert len(numbers) == 29

		# No control carries both, because the two documents address different parameters.
		assert not [control for control in microkorg.controls.values()
			if control.cc is not None and control.nrpn is not None]

	def test_every_assignable_number_is_within_the_span_the_maker_states (self) -> None:
		"""The implementation allows CC 0 to 95, and the manual's defaults all fall inside it.

		CC 1 is the exception and is deliberate: it is fixed rather than assignable, and it
		comes from the implementation's receive table instead of the manual's.
		"""
		microkorg = pymidiinstrumentdefs.load("korg/microkorg", [CORPUS])

		assigned = [control.cc for control in microkorg.controls.values()
			if control.cc is not None and control.name != "pitch_modulation_depth"]

		assert len(assigned) == 41
		assert all(0 <= number <= 95 for number in assigned)
		assert len(set(assigned)) == 41

		assert microkorg.controls["pitch_modulation_depth"].cc == 1

	def test_it_has_no_parts_because_it_has_only_one_channel (self) -> None:
		"""Two timbres when layered, and the manual says outright they cannot be split."""
		microkorg = pymidiinstrumentdefs.load("korg/microkorg", [CORPUS])

		assert microkorg.parts == {}
		assert microkorg.midi.channels == (1, 16)

		# Which timbre a control reaches is a control change, not a channel.
		assert microkorg.controls["midi_timbre_select"].cc == 95

	def test_aftertouch_is_a_checked_absence_rather_than_silence (self) -> None:
		"""The keyboard has none and the recognised messages do not include it either."""
		microkorg = pymidiinstrumentdefs.load("korg/microkorg", [CORPUS])

		assert microkorg.voice.aftertouch == "none"

		assert microkorg.voice.velocity is not None
		assert microkorg.voice.velocity.note_on == "received"
		assert microkorg.voice.velocity.note_off is False

	def test_four_voices_and_a_settable_bend (self) -> None:
		"""Stated the same for synth programs and for vocoder programs."""
		microkorg = pymidiinstrumentdefs.load("korg/microkorg", [CORPUS])

		assert microkorg.voice.polyphony == 4
		assert microkorg.voice.note_range is None

		assert microkorg.voice.pitch_bend is not None
		assert microkorg.voice.pitch_bend.semitones == 12
		assert microkorg.voice.pitch_bend.programmable is True

	def test_its_manual_turns_its_pages_by_six (self) -> None:
		"""Eighty pages, whatever `file` says about it."""
		microkorg = pymidiinstrumentdefs.load("korg/microkorg", [CORPUS])
		manual = microkorg.sources["manual"]

		assert manual.paginated
		assert manual.file_page(56) == 62

		# The implementation is plain text and the download page is a page: neither has any.
		assert not microkorg.sources["implementation"].paginated
		assert not microkorg.sources["download_page"].paginated

	def test_program_change_both_ways_over_one_bank (self) -> None:
		"""128 programs and no bank select, which is what separates it from the microKORG S."""
		microkorg = pymidiinstrumentdefs.load("korg/microkorg", [CORPUS])

		assert microkorg.midi.program_change is not None
		assert microkorg.midi.program_change.receives is True
		assert microkorg.midi.program_change.sends is True
		assert microkorg.midi.program_change.presets == 128

		assert microkorg.midi.clock == "both"
		assert microkorg.midi.transport == "receives"
		assert microkorg.midi.sysex is True
		assert microkorg.midi.nrpn == "supported"


class TestJuno106:

	"""Two controller numbers in the whole instrument, read by eye from a 1984 scan."""

	def test_its_control_change_is_two_numbers_and_both_travel_both_ways (self) -> None:
		"""Not an absence and not a player's routing: a published map with two rows in it."""
		juno = pymidiinstrumentdefs.load("roland/juno_106", [CORPUS])

		assert sorted(control.cc for control in juno.controls.values() if control.cc) == [1, 64]
		assert all(control.direction == "both" for control in juno.controls.values())

		# Which is neither of the two shapes that also produce a short file: somebody
		# checked and found none, and a map the player writes with MIDI learn.
		assert not juno.midi.refuses_control_change
		assert not juno.midi.learns_control_change

	def test_hold_turns_on_at_one_because_that_is_what_the_maker_states (self) -> None:
		"""Everywhere else in this corpus a switch is off below 64; here the manual says 1."""
		juno = pymidiinstrumentdefs.load("roland/juno_106", [CORPUS])
		hold = juno.controls["hold"]

		assert hold.kind == "switch"
		assert hold.band("off") == (0, 0)
		assert hold.band("on") == (1, 127)

	def test_modulation_is_continuous_although_it_only_ever_sends_two_values (self) -> None:
		"""It answers to all 128; its own bender lever is a switch, so it sends 0 or 127."""
		juno = pymidiinstrumentdefs.load("roland/juno_106", [CORPUS])
		modulation = juno.controls["lfo_modulation"]

		assert modulation.kind == "continuous"
		assert modulation.range == (0, 127)
		assert modulation.states == []

	def test_the_mode_is_left_out_because_the_chart_gives_two (self) -> None:
		"""Default 3 transmitted and 1 recognized, and the field holds one number (#4179)."""
		juno = pymidiinstrumentdefs.load("roland/juno_106", [CORPUS])

		assert juno.midi.mode is None

	def test_its_note_range_is_what_it_accepts_not_what_it_sounds (self) -> None:
		"""A note outside the keyboard is transposed into it rather than dropped, so 0-127."""
		juno = pymidiinstrumentdefs.load("roland/juno_106", [CORPUS])

		assert juno.voice.note_range == (0, 127)
		assert juno.voice.plays_note(0) and juno.voice.plays_note(127)
		assert juno.voice.polyphony == 6

	def test_it_holds_a_scan_and_a_readable_page_at_once (self) -> None:
		"""The first definition to do so, which is what the quotation checker had to learn."""
		juno = pymidiinstrumentdefs.load("roland/juno_106", [CORPUS])

		assert juno.sources["manual"].paginated
		assert juno.sources["manual"].file_page(34) == 34
		assert not juno.sources["archive"].paginated
		assert juno.sources["archive"].file_page(34) is None

	def test_what_it_answers_to_with_no_sequencer_in_it (self) -> None:
		"""Crossed both ways on the chart, so neither clock nor transport, and no aftertouch."""
		juno = pymidiinstrumentdefs.load("roland/juno_106", [CORPUS])

		assert juno.midi.clock == "none"
		assert juno.midi.transport == "none"
		assert juno.midi.nrpn == "none"
		assert juno.voice.aftertouch == "none"

		assert juno.voice.velocity is not None
		assert juno.voice.velocity.note_on == "ignored"
		assert juno.voice.velocity.note_off is False

	def test_the_whole_of_its_remote_editing_is_system_exclusive (self) -> None:
		"""Eighteen parameters with no controller number, which no `controls` block can hold."""
		juno = pymidiinstrumentdefs.load("roland/juno_106", [CORPUS])

		assert juno.midi.sysex is True

		assert juno.midi.program_change is not None
		assert juno.midi.program_change.presets == 128
		assert juno.midi.program_change.receives is True
		assert juno.midi.program_change.sends is True


class TestAnalogRytmMkii:

	"""Ninety-nine of the 319 rows its appendix prints, and the reason is the other 220."""

	def test_the_machine_parameters_are_not_carried_and_the_slots_are (self) -> None:
		"""Eight generic slots stand for what 32 machines call the same eight numbers."""
		rytm = pymidiinstrumentdefs.load("elektron/analog_rytm_mkii", [CORPUS])

		assert len(rytm.controls) == 99

		slots = [name for name in rytm.controls if name.startswith("synth_parameter_")]

		assert len(slots) == 8
		assert [rytm.controls[name].cc for name in sorted(slots)] == [16, 17, 18, 19, 20, 21, 22, 23]

		# Nothing named for a machine reached the file. BD CLASSIC, SD FM and the rest would
		# each have claimed CC 16 again, with nothing in the format to choose between them.
		assert not [name for name in rytm.controls if name.startswith(("bd_", "sd_", "hh_", "cy_"))]

	def test_a_controller_number_means_different_things_on_different_parts (self) -> None:
		"""26 of them do, which is why every control names the part it belongs to."""
		rytm = pymidiinstrumentdefs.load("elektron/analog_rytm_mkii", [CORPUS])

		parts_using: dict[int, set[str | None]] = {}

		for control in rytm.controls.values():
			assert control.cc is not None
			parts_using.setdefault(control.cc, set()).add(control.part)

		shared = {cc for cc, parts in parts_using.items() if len(parts) > 1}

		assert len(shared) == 26
		assert rytm.controls["synth_parameter_1"].cc == rytm.controls["delay_time"].cc == 16
		assert rytm.controls["synth_parameter_1"].part == "track"
		assert rytm.controls["delay_time"].part == "fx"

	def test_the_nrpns_resolve_what_the_controller_numbers_do_not (self) -> None:
		"""Each bank is a part: 0 performance, 1 track, 2 FX, 3 trig. So an NRPN is unique."""
		rytm = pymidiinstrumentdefs.load("elektron/analog_rytm_mkii", [CORPUS])

		numbers = [control.nrpn for control in rytm.controls.values()]

		assert None not in numbers
		assert len(set(numbers)) == len(numbers) == 99

		# The manual prints an NRPN as a bank and a number; the format stores one integer.
		assert rytm.controls["synth_parameter_1"].nrpn == 1 * 128 + 0
		assert rytm.controls["delay_time"].nrpn == 2 * 128 + 0
		assert rytm.controls["trig_note"].nrpn == 3 * 128 + 0
		assert rytm.controls["performance_parameter_1"].nrpn == 0

	def test_one_control_in_the_whole_appendix_is_fourteen_bit (self) -> None:
		"""And the appendix says so itself, which its maker's other manual does not."""
		rytm = pymidiinstrumentdefs.load("elektron/analog_rytm_mkii", [CORPUS])

		fine = [name for name, control in rytm.controls.items() if control.is_14_bit]

		assert fine == ["lfo_depth"]
		assert rytm.controls["lfo_depth"].cc == 109
		assert rytm.controls["lfo_depth"].lsb == 118   # not 109 + 32, which the MMA would give

	def test_eight_voices_are_shared_across_twelve_tracks (self) -> None:
		"""Four tracks have a voice each and the other eight are paired two to a voice."""
		rytm = pymidiinstrumentdefs.load("elektron/analog_rytm_mkii", [CORPUS])

		assert rytm.voice.polyphony == 8
		assert rytm.voice.polyphony_shared is True
		assert rytm.parts["track"].count == 12
		assert rytm.parts["track"].polyphony is None

	def test_what_it_answers_to_beyond_its_controls (self) -> None:
		"""Clock and transport both ways, program change selecting a pattern, SysEx dumps."""
		rytm = pymidiinstrumentdefs.load("elektron/analog_rytm_mkii", [CORPUS])

		assert rytm.midi.clock == "both"
		assert rytm.midi.transport == "both"
		assert rytm.midi.nrpn == "supported"
		assert rytm.midi.sysex is True

		assert rytm.midi.program_change is not None
		assert rytm.midi.program_change.presets == 128

		# Notes 0-11 reach the twelve tracks and 12-59 the active one chromatically; above
		# that the manual says nothing, so nothing is claimed.
		assert rytm.voice.note_range == (0, 59)

	def test_the_part_that_only_sends_claims_nothing_about_receiving (self) -> None:
		"""One sentence names the performance channel and it names one direction only."""
		rytm = pymidiinstrumentdefs.load("elektron/analog_rytm_mkii", [CORPUS])

		assert rytm.parts["performance"].receives is None
		assert rytm.parts["fx"].receives == ("controls",)
		assert rytm.parts["track"].receives == ("notes", "controls")


class TestVolcaDrum:

	"""An instrument whose maker publishes two maps, and a definition that follows one of them."""

	def test_the_six_parts_sit_on_six_channels_with_nothing_to_set (self) -> None:
		"""The chart's whole addressing scheme is "Channel 1-6 = Parts 1-6"."""
		volca = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		part = volca.parts["part"]

		assert part.count == 6
		assert part.channel_offset == 0
		assert part.is_assigned is False

		# There is no basic channel to choose, so the six channels follow from the one base.
		assert volca.midi.channels == (1, 1)
		assert [part.channel_for(1, instance) for instance in range(6)] == [1, 2, 3, 4, 5, 6]

	def test_a_note_reaches_a_part_and_says_nothing_else (self) -> None:
		"""It answers to every note number, and the number picks nothing."""
		volca = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		assert volca.voice.addressing == "none"
		assert volca.parts["part"].addressing == "none"
		assert volca.parts["part"].takes("notes")

		assert volca.voice.note_range == (0, 127)
		assert volca.voice.plays_note(0)
		assert volca.voice.plays_note(127)

		# Nothing in either document says how many notes one part holds.
		assert volca.voice.polyphony is None

	def test_the_layer_suffix_is_a_third_control_and_not_a_range (self) -> None:
		"""SELECT1, SELECT2, SELECT1-2 against 14, 15, 16: three controls, not two."""
		volca = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		assert volca.controls["select_1"].cc == 14
		assert volca.controls["select_2"].cc == 15
		assert volca.controls["select_both"].cc == 16

		both = [name for name in volca.controls if name.endswith("_both")]

		assert len(both) == 7
		assert len(volca.controls) == 31

	def test_the_resonator_is_shared_so_four_controls_have_no_part (self) -> None:
		"""Its send belongs to a part and its own four do not."""
		volca = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		unparted = sorted(name for name, control in volca.controls.items() if control.part is None)

		assert unparted == [
			"waveguide_body", "waveguide_decay", "waveguide_model", "waveguide_tune"]
		assert volca.controls["waveguide_send"].part == "part"

	def test_it_answers_and_never_speaks (self) -> None:
		"""One MIDI socket, an input, so every row of the chart is received only."""
		volca = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		assert all(control.direction == "receives" for control in volca.controls.values())

		assert volca.midi.clock == "receives"
		assert volca.midi.transport == "receives"
		assert volca.midi.mode == 3

		assert volca.midi.program_change is not None
		assert volca.midi.program_change.receives is True
		assert volca.midi.program_change.sends is False
		assert volca.midi.program_change.presets is None

	def test_what_was_checked_and_found_absent (self) -> None:
		"""Three absences the documents state, kept apart from what nobody looked for."""
		volca = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		assert volca.midi.nrpn == "none"
		assert volca.midi.sysex is False
		assert volca.voice.aftertouch == "none"
		assert volca.voice.pitch_bend is None

		assert volca.voice.velocity is not None
		assert volca.voice.velocity.note_on == "received"
		assert volca.voice.velocity.note_off is False

	def test_the_other_chart_is_cited_and_nothing_is_taken_from_it (self) -> None:
		"""Both implementations are named, and the file describes the factory default."""
		volca = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		assert set(volca.sources) == {
			"chart", "manual", "alternate_chart", "download_page", "release_notes"}

		assert volca.sources["chart"].title == \
			"volca drum MIDI Implementation Chart (Split channel)"
		assert volca.sources["alternate_chart"].title == \
			"volca drum MIDI Implementation Chart (Single channel)"

		# Nobody established which system the charts describe, and the release notes say why.
		assert volca.model.firmware is None


class TestDigitaktII:

	"""Sixteen tracks that are each one thing or the other, and an appendix that miscounts itself."""

	def test_sixteen_tracks_are_one_part_and_not_two (self) -> None:
		"""A track is an audio track or a MIDI track, so the same channel reaches two maps."""
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		assert set(digitakt.parts) == {"track", "fx"}
		assert digitakt.parts["track"].count == 16
		assert digitakt.parts["track"].is_assigned
		assert digitakt.parts["track"].polyphony == 1
		assert digitakt.voice.polyphony_shared is False

		# The effects answer on a channel of their own and take no notes.
		assert digitakt.parts["fx"].receives == ("controls",)
		assert digitakt.parts["fx"].count == 1

	def test_the_same_number_means_two_things_on_one_track (self) -> None:
		"""CC 70 is the filter's attack on an audio track and VAL1 on a MIDI track."""
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		assert digitakt.controls["filter_attack_time"].cc == 70
		assert digitakt.controls["cc_val_val1"].cc == 70

		# Both are on the same part, because they are the same sixteen tracks.
		assert digitakt.controls["filter_attack_time"].part == "track"
		assert digitakt.controls["cc_val_val1"].part == "track"

		# Sixteen assignable CC values, which is what a MIDI track offers.
		assert sum(1 for control in digitakt.controls.values()
			if control.group == "cc_val") == 16

	def test_the_four_nrpns_the_appendix_gives_to_two_parameters_each (self) -> None:
		"""Carried as printed, because this maker has twice shipped a release to fix such a pair."""
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		# 1 * 128 + 23, the filter's envelope depth and its envelope delay.
		assert digitakt.controls["filter_env_depth"].nrpn == 151
		assert digitakt.controls["filter_env_delay"].nrpn == 151

		# 1:51 and 1:52, the filter's base and width against LFO 2.
		assert digitakt.controls["filter_base"].nrpn == 179
		assert digitakt.controls["lfo_2_multiplier"].nrpn == 179
		assert digitakt.controls["filter_width"].nrpn == 180
		assert digitakt.controls["lfo_2_fade_in_out"].nrpn == 180

		# 3:8, portamento against the Euclidean sequencer.
		assert digitakt.controls["trig_portamento_on_off"].nrpn == 392
		assert digitakt.controls["euclidean_pulse_generator_1"].nrpn == 392

	def test_the_external_inputs_are_printed_twice_because_a_setting_decides (self) -> None:
		"""DUAL MONO chooses whether CC 72 is one input's level or the pair's."""
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		assert digitakt.controls["external_in_dual_mono"].cc == 82
		assert digitakt.controls["external_in_input_l_level"].cc == 72
		assert digitakt.controls["external_in_input_l_r_level"].cc == 72
		assert digitakt.controls["external_in_input_l_pan"].cc == 74
		assert digitakt.controls["external_in_input_l_r_balance"].cc == 74

	def test_two_controls_come_from_the_body_and_not_the_appendix (self) -> None:
		"""A reader with only the appendix would take CC 1 and CC 2 for unassigned."""
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		assert digitakt.controls["modulation_wheel"].cc == 1
		assert digitakt.controls["breath_controller"].cc == 2

		# Neither carries an NRPN, because the appendix is where the NRPNs are.
		assert digitakt.controls["modulation_wheel"].nrpn is None
		assert digitakt.controls["breath_controller"].nrpn is None

		assert len(digitakt.controls) == 144

	def test_the_three_lfo_speeds_and_depths_are_fourteen_bit (self) -> None:
		"""The only six controls in the file with a CC LSB, and the appendix says so in words."""
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		paired = sorted(name for name, control in digitakt.controls.items()
			if control.lsb is not None)

		assert paired == [
			"lfo_1_depth", "lfo_1_speed",
			"lfo_2_depth", "lfo_2_speed",
			"lfo_3_depth", "lfo_3_speed",
		]
		assert digitakt.controls["lfo_1_speed"].cc == 102
		assert digitakt.controls["lfo_1_speed"].lsb == 58

	def test_what_it_answers_to_beyond_its_controls (self) -> None:
		"""Clock and transport both ways, program change selecting a pattern, SysEx dumps."""
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		assert digitakt.midi.clock == "both"
		assert digitakt.midi.transport == "both"
		assert digitakt.midi.nrpn == "supported"
		assert digitakt.midi.sysex is True
		assert digitakt.midi.channels == (1, 16)

		assert digitakt.midi.program_change is not None
		assert digitakt.midi.program_change.presets == 128

		# Notes 0-15 reach the sixteen tracks and 16-84 play the active one chromatically;
		# above that the manual says nothing, so nothing is claimed.
		assert digitakt.voice.note_range == (0, 84)

		# Aftertouch is received and never characterised, and the bend has no stated range.
		assert digitakt.voice.aftertouch is None
		assert digitakt.voice.pitch_bend is None


class TestMultiPoly:

	"""Two kinds of number on one instrument, and a chart page partly written in cipher."""

	def test_nine_numbers_are_fixed_and_twelve_are_defaults (self) -> None:
		"""The chart's rows are properties of the model; the CC Assign table's are not."""
		multi = pymidiinstrumentdefs.load("korg/multi_poly", [CORPUS])

		assert len(multi.controls) == 22

		fixed = sorted(control.cc for name, control in multi.controls.items()
			if control.group in ("controllers", "pedals")
			or name in ("kaoss_pad_x", "kaoss_pad_y", "kaoss_button")
			if control.cc is not None)

		assert fixed == [1, 7, 10, 11, 12, 18, 19, 64, 66, 67]

		defaults = sorted(control.cc for name, control in multi.controls.items()
			if control.cc not in fixed and control.cc is not None)

		assert defaults == [9, 20, 24, 25, 26, 27, 105, 106, 107, 108, 109, 110]

		# CC 12 is named with its number in the body and nowhere in the chart, which folds it
		# anonymously into its assignable run.
		assert multi.controls["kaoss_button"].cc == 12

	def test_every_default_falls_inside_the_assignable_range (self) -> None:
		"""The chart and the settings page agree, which is worth asserting rather than assuming."""
		multi = pymidiinstrumentdefs.load("korg/multi_poly", [CORPUS])

		# "2-6, 8-9, 12-31, 32-63, 65, 67-95, 102-119", as the chart prints it.
		assignable = (set(range(2, 7)) | {8, 9} | set(range(12, 64)) | {65}
			| set(range(67, 96)) | set(range(102, 120)))

		defaults = [control.cc for name, control in multi.controls.items()
			if control.group in ("scale_select", "mod_knobs")
			or name.startswith(("kaoss_finger", "kaoss_throw"))]

		assert defaults and all(number in assignable for number in defaults if number is not None)

	def test_five_controls_are_recognised_and_never_sent (self) -> None:
		"""Which is what the chart's two mark columns say, read by their position on the page."""
		multi = pymidiinstrumentdefs.load("korg/multi_poly", [CORPUS])

		receives = sorted(name for name, control in multi.controls.items()
			if control.direction == "receives")

		assert receives == ["expression", "pan", "soft", "sostenuto", "volume"]

		# `receives` means it answers and never sends, so a panel may still offer it.
		assert all(control.is_sendable for control in multi.controls.values())

	def test_four_layers_wait_on_the_global_channel (self) -> None:
		"""The wavestate's arrangement exactly, down to the setting that moves one."""
		multi = pymidiinstrumentdefs.load("korg/multi_poly", [CORPUS])

		assert sorted(multi.parts) == ["layer_a", "layer_b", "layer_c", "layer_d"]
		assert all(part.channel_offset == 0 for part in multi.parts.values())
		assert all(not part.is_assigned for part in multi.parts.values())

		# Sixty voices for the instrument, drawn on by whichever Layer plays next.
		assert multi.voice.polyphony == 60
		assert multi.voice.polyphony_shared is True

	def test_what_was_checked_and_found_absent (self) -> None:
		"""NRPN and transport are absences the documents state, not pages nobody read."""
		multi = pymidiinstrumentdefs.load("korg/multi_poly", [CORPUS])

		assert multi.midi.nrpn == "none"
		assert multi.midi.transport == "none"
		assert multi.midi.clock == "both"
		assert multi.midi.sysex is True

		assert multi.midi.program_change is not None
		assert multi.midi.program_change.presets == 64

		# Both kinds of aftertouch are received and a four-way setting picks between them, so
		# no one word is true; the bend has no stated range.
		assert multi.voice.aftertouch is None
		assert multi.voice.pitch_bend is None

	def test_the_chart_is_a_page_of_the_manual_and_the_offset_says_so (self) -> None:
		"""Korg publishes no chart of its own for this instrument, and one source is cited for that."""
		multi = pymidiinstrumentdefs.load("korg/multi_poly", [CORPUS])

		assert multi.sources["manual"].page_offset == 5
		assert not multi.sources["property_exchange"].paginated
		assert multi.model.firmware is None


class TestMessenger:

	"""The best-formed appendix here: two numbers and a value account for every row."""

	def test_every_fourteen_bit_pair_is_the_standard_one (self) -> None:
		"""Thirty of them here, and the fine half is always the coarse half plus 32.

		Worth asserting rather than assuming: the Digitakt II's are not, and a consumer
		applying the specification's rule to that instrument moves the wrong parameter.
		"""
		messenger = pymidiinstrumentdefs.load("moog/messenger", [CORPUS])

		paired = [control for control in messenger.controls.values() if control.lsb is not None]

		# The appendix has 31 and this file has 30: Data Entry on CC 6 with LSB 38 is the
		# specification's own pair and is excluded.
		assert len(paired) == 30
		assert all(control.lsb == control.cc + 32 for control in paired
			if control.cc is not None and control.lsb is not None)

		# And all of them run over the whole 14-bit range.
		assert all(control.range == (0, 16383) for control in paired)

		assert len(messenger.controls) == 56

	def test_no_number_is_used_twice_in_either_column (self) -> None:
		"""Eighty-six numbers across two columns, every one its own."""
		messenger = pymidiinstrumentdefs.load("moog/messenger", [CORPUS])

		every = [control.cc for control in messenger.controls.values()] + \
			[control.lsb for control in messenger.controls.values() if control.lsb is not None]

		assert len(every) == 86
		assert len(set(every)) == 86

	def test_the_bands_the_maker_names (self) -> None:
		"""Twenty-one stepped controls, and one more that gives exact values rather than bands."""
		messenger = pymidiinstrumentdefs.load("moog/messenger", [CORPUS])

		stepped = [control for control in messenger.controls.values() if control.values]
		exact = [control for control in messenger.controls.values() if control.choices]

		assert len(stepped) == 21
		assert len(exact) == 1

		# A band is recorded by its lowest value, which is how the manual prints it.
		assert messenger.controls["filter_mode"].values == {
			"four_p_lp": 0, "two_p_lp": 32, "bp": 64, "hp": 96}
		assert messenger.controls["lfo_1_destination"].choices == {
			"cutoff": 0, "osc_2_freq": 32, "osc_wave": 64, "sub_wave": 96}

		# Five octave bands, and the signs are what keep them five.
		assert messenger.controls["kb_octave"].values == {
			"minus_2_octaves": 0, "minus_1_octave": 26, "zero_octave": 51,
			"plus_1_octave": 76, "plus_2_octaves": 101}

	def test_it_answers_to_rpn_and_not_to_nrpn (self) -> None:
		"""A checked absence, and rare enough in this corpus to be worth a test."""
		messenger = pymidiinstrumentdefs.load("moog/messenger", [CORPUS])

		assert messenger.midi.nrpn == "none"
		assert messenger.midi.sysex is True
		assert messenger.midi.clock == "both"
		assert messenger.midi.transport == "both"

		assert messenger.midi.program_change is not None
		assert messenger.midi.program_change.presets == 256

	def test_a_monophonic_synthesizer_that_states_its_aftertouch (self) -> None:
		"""One direction each, which three instruments in a row could not manage."""
		messenger = pymidiinstrumentdefs.load("moog/messenger", [CORPUS])

		assert messenger.voice.polyphony == 1
		assert messenger.voice.aftertouch == "channel"

		assert messenger.voice.velocity is not None
		assert messenger.voice.velocity.note_on == "received"
		assert messenger.voice.velocity.note_off is False

		# The bend range is stated in the panel chapter and settable four ways.
		assert messenger.voice.pitch_bend is not None
		assert messenger.voice.pitch_bend.semitones == 7
		assert messenger.voice.pitch_bend.programmable is True

	def test_the_two_pedals_and_the_two_that_are_semitones (self) -> None:
		"""The only controls here carrying a unit, and the only two pedal inputs."""
		messenger = pymidiinstrumentdefs.load("moog/messenger", [CORPUS])

		assert messenger.controls["pitch_bend_up_amount"].cc == 107
		assert messenger.controls["pitch_bend_down_amount"].cc == 108
		assert messenger.controls["pitch_bend_up_amount"].range == (0, 24)
		assert messenger.controls["pitch_bend_up_amount"].unit == "semitones"

		pedals = sorted(name for name, control in messenger.controls.items()
			if control.group == "pedals")

		assert pedals == ["expression_pedal", "hold", "sustain_pedal"]


class TestMpcSample:

	"""A definition with no controls, because its maker publishes no controller number."""

	def test_it_carries_no_controls_and_no_groups (self) -> None:
		"""Which is the finding, not an omission: there is nothing published to transcribe."""
		mpc = pymidiinstrumentdefs.load("akai/mpc_sample", [CORPUS])

		assert mpc.controls == {}
		assert mpc.groups == {}
		assert mpc.parts == {}

		# And `midi` is not `none` either: this instrument has MIDI and plenty of it.
		assert mpc.midi.stated_none is False

	def test_what_the_one_menu_does_say (self) -> None:
		"""Nine settings, and three of them reach a field this format has."""
		mpc = pymidiinstrumentdefs.load("akai/mpc_sample", [CORPUS])

		assert mpc.midi.channels == (1, 16)
		assert mpc.midi.clock == "both"

		assert mpc.midi.program_change is not None
		assert mpc.midi.program_change.receives is True
		assert mpc.midi.program_change.presets == 128

	def test_silence_is_not_a_checked_absence (self) -> None:
		"""Nothing says the instrument ignores these, only that nobody is told."""
		mpc = pymidiinstrumentdefs.load("akai/mpc_sample", [CORPUS])

		assert mpc.midi.control_change is None
		assert mpc.midi.nrpn is None
		assert mpc.midi.sysex is None
		assert mpc.midi.transport is None

		assert mpc.midi.program_change is not None
		assert mpc.midi.program_change.sends is None

	def test_the_voice_block_is_empty_on_purpose (self) -> None:
		"""Notes reach the pads and which note reaches which pad is not published."""
		mpc = pymidiinstrumentdefs.load("akai/mpc_sample", [CORPUS])

		assert mpc.voice.addressing is None
		assert mpc.voice.note_range is None
		assert mpc.voice.velocity is None
		assert mpc.voice.aftertouch is None
		assert mpc.voice.voices == {}

		# The one thing the specification does state, which the blind reading found.
		assert mpc.voice.polyphony == 32

	def test_the_firmware_is_established_from_the_release_notes (self) -> None:
		"""The guide's version is its own; two of its features are what date it."""
		mpc = pymidiinstrumentdefs.load("akai/mpc_sample", [CORPUS])

		assert mpc.model.firmware == "1.3.0"
		assert mpc.model.manufacturer == "Akai Professional"
		assert set(mpc.sources) == {"guide", "release_notes"}


class TestTr1000:

	"""A real chart, nine firmware releases behind the instrument it describes."""

	def test_fifty_two_controls_belong_to_ten_instruments (self) -> None:
		"""Four large instruments have seven parameters and six small ones have four."""
		tr = pymidiinstrumentdefs.load("roland/tr_1000", [CORPUS])

		assert len(tr.controls) == 66

		counted = {name: sum(1 for control in tr.controls.values() if control.group == name)
			for name in ("bd", "sd", "lt", "ht", "rs", "hc", "ch", "oh", "cc", "rc")}

		assert counted == {"bd": 7, "sd": 7, "lt": 7, "ht": 7,
			"rs": 4, "hc": 4, "ch": 4, "oh": 4, "cc": 4, "rc": 4}

		assert sum(counted.values()) == 52

	def test_every_row_travels_both_ways (self) -> None:
		"""Sixty-six rows and not one direction among them."""
		tr = pymidiinstrumentdefs.load("roland/tr_1000", [CORPUS])

		assert all(control.direction == "both" for control in tr.controls.values())

		numbers = sorted(control.cc for control in tr.controls.values() if control.cc is not None)

		assert len(numbers) == 66
		assert len(set(numbers)) == 66
		assert numbers[0] == 9 and numbers[-1] == 117

	def test_eleven_instruments_have_notes_and_they_are_defaults (self) -> None:
		"""The chart's first note column, which the player can change in a menu."""
		tr = pymidiinstrumentdefs.load("roland/tr_1000", [CORPUS])

		assert tr.voice.addressing == "voices"
		assert tr.voice.voices == {
			"bd": 36, "sd": 38, "lt": 43, "ht": 50, "rs": 37, "hc": 39,
			"ch": 42, "oh": 46, "cc": 49, "rc": 51, "trg": 84}

		# TRG is the trigger output rather than an instrument, and it has no controls.
		assert not any(control.group == "trg" for control in tr.controls.values())

	def test_what_was_checked_and_found_absent (self) -> None:
		"""Three absences the chart states, and one silence it does not."""
		tr = pymidiinstrumentdefs.load("roland/tr_1000", [CORPUS])

		assert tr.midi.sysex is False
		assert tr.voice.aftertouch == "none"
		assert tr.voice.pitch_bend is None

		# The chart has no NRPN row at all, which is silence rather than an absence.
		assert tr.midi.nrpn is None

	def test_the_chart_is_older_than_the_firmware_it_is_cited_beside (self) -> None:
		"""Version 1.11 against a manual marked 1.20 and later, and a system program at 1.22."""
		tr = pymidiinstrumentdefs.load("roland/tr_1000", [CORPUS])

		assert tr.model.firmware == "1.20"
		assert tr.sources["chart"].edition == "Version 1.11"
		assert tr.sources["manual"].edition == "03"
		assert tr.sources["release_notes"].edition == "Ver.1.22"

	def test_it_sends_a_fixed_velocity_and_accepts_any (self) -> None:
		"""Which the TR-8S does too, and which the chart states in one row."""
		tr = pymidiinstrumentdefs.load("roland/tr_1000", [CORPUS])

		assert tr.voice.velocity is not None
		assert tr.voice.velocity.note_on == "received"

		assert tr.midi.clock == "both"
		assert tr.midi.transport == "both"
		assert tr.midi.channels == (1, 16)

		assert tr.midi.program_change is not None
		assert tr.midi.program_change.presets == 128


class TestD50:

	"""A 1987 instrument whose manual points at a chart that is not in it."""

	def test_it_carries_no_controls_because_the_player_chooses_them (self) -> None:
		"""Two pedals, each settable to any number in a range, and no factory map at all."""
		d50 = pymidiinstrumentdefs.load("roland/d_50", [CORPUS])

		assert d50.controls == {}
		assert d50.groups == {}

		# Not silence: the manual says what the mechanism is, so the field is answered.
		assert d50.midi.control_change == "learned"
		assert d50.midi.stated_none is False

	def test_two_tones_answer_on_two_channels (self) -> None:
		"""In one key mode the lower tone follows the basic channel and the upper its own."""
		d50 = pymidiinstrumentdefs.load("roland/d_50", [CORPUS])

		assert set(d50.parts) == {"lower", "upper"}

		assert d50.parts["lower"].channel_offset == 0
		assert d50.parts["lower"].channel is None

		assert d50.parts["upper"].channel == "assigned"
		assert d50.parts["upper"].channel_offset is None

		for part in d50.parts.values():
			assert part.addressing == "pitches"
			assert part.receives == ("notes",)

	def test_what_the_midi_chapter_does_state (self) -> None:
		"""Three things, each of them in words on a page rather than inferred."""
		d50 = pymidiinstrumentdefs.load("roland/d_50", [CORPUS])

		assert d50.midi.channels == (1, 16)
		assert d50.midi.sysex is True

		assert d50.midi.program_change is not None
		assert d50.midi.program_change.receives is True
		assert d50.midi.program_change.sends is True
		assert d50.midi.program_change.presets == 128

	def test_polyphony_is_not_recorded_although_the_manual_draws_it (self) -> None:
		"""There is no specifications page: the voice count appears only as rows of circles."""
		d50 = pymidiinstrumentdefs.load("roland/d_50", [CORPUS])

		assert d50.voice.polyphony is None
		assert d50.voice.note_range is None
		assert d50.voice.aftertouch is None
		assert d50.voice.velocity is None

		# What is recorded is how notes reach it, which the manual does say.
		assert d50.voice.addressing == "pitches"

	def test_clock_and_transport_are_silences_rather_than_absences (self) -> None:
		"""The MIDI chapter never mentions either, and nothing here says the instrument ignores
		them."""
		d50 = pymidiinstrumentdefs.load("roland/d_50", [CORPUS])

		assert d50.midi.clock is None
		assert d50.midi.transport is None
		assert d50.midi.nrpn is None

	def test_the_sources_are_a_scan_and_a_page_that_serves_nothing (self) -> None:
		"""One of the two is cited for what it does not contain."""
		d50 = pymidiinstrumentdefs.load("roland/d_50", [CORPUS])

		assert set(d50.sources) == {"manual", "support_page"}
		assert d50.sources["manual"].edition == "Advanced Course"
		assert d50.sources["manual"].page_offset == 0

		assert d50.sources["support_page"].kind == "download_page"
		assert d50.sources["support_page"].paginated is False

		# No firmware, because a 1987 manual names none and Roland publishes no history.
		assert d50.model.firmware is None
		assert d50.model.manufacturer == "Roland"


class TestTeo5:

	"""The largest definition here, off a document that names another synth as its subject."""

	def test_the_control_map_reaches_both_ways (self) -> None:
		"""Most parameters carry a controller number and an NRPN, which is one control each."""
		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		assert len(teo.controls) == 198
		assert len(teo.groups) == 33

		both = [c for c in teo.controls.values() if c.cc is not None and c.nrpn is not None]
		nrpn_alone = [c for c in teo.controls.values() if c.cc is None and c.nrpn is not None]

		assert len(both) == 98
		assert len(nrpn_alone) == 88

		assert teo.midi.nrpn == "preferred"

	def test_no_control_sits_on_a_channel_mode_message (self) -> None:
		"""The document lists CC 120 to 127, and those are MIDI's own, not this instrument's."""
		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		numbers = {c.cc for c in teo.controls.values() if c.cc is not None}

		assert not numbers & set(range(120, 128))

		# Nor on the machinery that carries an NRPN's value and selects its number.
		assert not numbers & {6, 38, 96, 97, 98, 99, 100, 101}

	def test_the_modulation_matrix_is_reachable_by_nrpn_only (self) -> None:
		"""Sixteen slots of source, amount and destination, and no controller number for any."""
		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		slots = [f"mod_{number}" for number in range(1, 17)]

		for slot in slots:
			assert slot in teo.groups

			inside = [c for c in teo.controls.values() if c.group == slot]

			assert len(inside) == 3, f"{slot} has {len(inside)} controls"
			assert all(c.cc is None and c.nrpn is not None for c in inside)

	def test_the_ranges_the_two_tables_disagree_about (self) -> None:
		"""Sixteen parameters, and three of them are a contradiction rather than finer NRPN."""
		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		differing = {name: control for name, control in teo.controls.items()
			if control.nrpn_range is not None}

		assert len(differing) == 16

		# Thirteen are NRPN being finer, which is the maker's reason for preferring it.
		assert differing["filter_cutoff"].range == (0, 127)
		assert differing["filter_cutoff"].nrpn_range == (0, 1024)

		# And three are not: a switch against a value, a narrower NRPN, and two tempo ranges
		# that do not reach the same top.
		assert differing["noise_type"].range == (0, 1)
		assert differing["noise_type"].nrpn_range == (0, 127)

		assert differing["scale"].range == (0, 65)
		assert differing["scale"].nrpn_range == (0, 64)

		assert differing["clock_bpm"].range == (15, 127)
		assert differing["clock_bpm"].nrpn_range == (30, 250)

	def test_the_globals_name_their_states (self) -> None:
		"""Which the sibling Take 5's document does not, so this records them where it cannot."""
		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		globals_here = [c for c in teo.controls.values() if c.group == "global"]

		assert len(globals_here) == 27
		assert all(c.nrpn is not None and 4096 <= c.nrpn <= 4122 for c in globals_here)

		clock = teo.controls["midi_clock_mode"]

		# Four states in the table, against six the prose two pages earlier names.
		assert clock.choices == {"off": 0, "out": 1, "in": 2, "in_thru": 3}

		# The maker's own spelling is kept, misprint and all.
		assert "apr_hold_moment" in teo.controls["sustain_mode"].choices

	def test_what_it_does_and_does_not_state_about_the_voice (self) -> None:
		"""Five voices and both kinds of pressure in, one kind out, and no note range at all."""
		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		assert teo.voice.polyphony == 5
		assert teo.voice.aftertouch == "poly"
		assert teo.voice.addressing == "pitches"

		assert teo.voice.velocity is not None
		assert teo.voice.velocity.note_on == "received"
		assert teo.voice.velocity.note_off is False

		assert teo.voice.pitch_bend is not None
		assert teo.voice.pitch_bend.programmable is True
		assert teo.voice.pitch_bend.semitones is None

		# No note range: the guide gives 44 keys in words and no number for either end.
		assert teo.voice.note_range is None

		# And no parts, although the keyboard splits: "The program is the same for both key
		# ranges", so a split is a control rather than a part.
		assert teo.parts == {}

	def test_the_firmware_is_not_recorded_because_nothing_states_one (self) -> None:
		"""Two documents, three sources, and no OS version named in any of them."""
		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		assert teo.model.firmware is None
		assert teo.model.manufacturer == "Oberheim"
		assert set(teo.sources) == {"midi_impl", "guide", "product_page"}

		assert teo.sources["midi_impl"].edition == "v2"
		assert teo.sources["guide"].edition == "Version 2.0"


class TestModelSamples:

	"""An appendix headed CC MSB that gives an LSB for one parameter out of twenty-nine."""

	def test_the_appendix_fits_on_one_page_and_this_is_all_of_it (self) -> None:
		"""Four tables, and the groups are the appendix's own headings."""
		ms = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		assert len(ms.controls) == 29
		assert set(ms.groups) == {"track", "playback", "lfo", "fx"}

		numbers = [c.cc for c in ms.controls.values()]

		assert all(number is not None and 0 <= number <= 127 for number in numbers)
		assert len(numbers) == len(set(numbers))

	def test_one_control_carries_an_lsb_and_the_rest_do_not (self) -> None:
		"""The column says MSB for all twenty-nine and Elektron prints the other half for one."""
		ms = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		with_lsb = {name: c.lsb for name, c in ms.controls.items() if c.lsb is not None}

		assert with_lsb == {"lfo_depth": 110}
		assert ms.controls["lfo_depth"].cc == 109

	def test_it_answers_to_nrpn_and_no_number_is_published (self) -> None:
		"""Which is the distinction three other Elektron definitions had to be corrected for."""
		ms = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		assert ms.midi.nrpn == "supported"
		assert all(c.nrpn is None for c in ms.controls.values())

	def test_six_tracks_and_the_two_effects_answer_on_their_own_channels (self) -> None:
		"""And no base channel, because every channel here is assigned."""
		ms = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		assert set(ms.parts) == {"track", "fx"}

		track = ms.parts["track"]

		assert track.count == 6
		assert track.channel == "assigned"
		assert track.channel_offset is None
		assert track.polyphony == 1
		assert track.receives == ("notes", "controls")

		fx = ms.parts["fx"]

		assert fx.count == 1
		assert fx.channel == "assigned"
		assert fx.receives == ("controls",)

		# The four effect parameters answer on the FX channel; the two sends stay with a track,
		# because they are a track's amount of an effect rather than the effect.
		on_fx = {name for name, c in ms.controls.items() if c.part == "fx"}

		assert on_fx == {"delay_time", "delay_feedback", "reverb_size", "reverb_tone"}
		assert ms.controls["delay_send"].part == "track"
		assert ms.controls["reverb_send"].part == "track"

	def test_a_program_change_picks_a_pattern_here (self) -> None:
		"""Six banks of sixteen, not a sound."""
		ms = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		assert ms.midi.program_change is not None
		assert ms.midi.program_change.presets == 96
		assert ms.midi.program_change.receives is True
		assert ms.midi.program_change.sends is True

	def test_the_note_range_and_what_is_left_unsaid (self) -> None:
		"""Two bands of notes, and three things the manual never mentions at all."""
		ms = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		assert ms.voice.note_range == (0, 60)
		assert ms.voice.polyphony_shared is False

		assert ms.voice.velocity is not None
		assert ms.voice.velocity.note_on == "received"

		# Silences rather than checked absences: no page says either way.
		assert ms.voice.aftertouch is None
		assert ms.voice.pitch_bend is None
		assert ms.midi.sysex is None

	def test_the_manual_is_newer_than_the_firmware_it_describes (self) -> None:
		"""OS 1.13 is of May 2021 and this manual of October 2024."""
		ms = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		assert ms.model.firmware == "1.13"
		assert ms.model.name == "Model:Samples"
		assert set(ms.sources) == {"manual", "downloads", "release_notes"}
		assert ms.sources["manual"].edition == "OS 1.13"


class TestModelCycles:

	"""The Model:Samples' manual with a synth in it, and four controls that change meaning."""

	def test_it_is_the_sibling_with_four_numbers_spent_differently (self) -> None:
		"""Which is what a host treating the two as one instrument would get wrong."""
		cycles = pymidiinstrumentdefs.load("elektron/model_cycles", [CORPUS])
		samples = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		assert len(cycles.controls) == 30
		assert len(samples.controls) == 29

		here = {c.cc: c.label for c in cycles.controls.values()}
		there = {c.cc: c.label for c in samples.controls.values()}

		# The four the two spend differently.
		for number, synth, sampler in (
				(16, "Color", "Pitch"), (17, "Shape", "Loop"),
				(18, "Sweep", "Reverse"), (19, "Contour", "Sample Start")):
			assert here[number] == synth, f"CC {number} is {here[number]!r} here"
			assert there[number] == sampler, f"CC {number} is {there[number]!r} on the sampler"

		# And the two this one has that the sampler has not.
		assert here[65] == "Pitch" and 65 not in there
		assert here[70] == "Machine Selection" and 70 not in there

	def test_the_two_appendices_agree_about_everything_else (self) -> None:
		"""Twenty-four numbers mean the same thing on both, which is why the four matter."""
		cycles = pymidiinstrumentdefs.load("elektron/model_cycles", [CORPUS])
		samples = pymidiinstrumentdefs.load("elektron/model_samples", [CORPUS])

		here = {c.cc: c.label for c in cycles.controls.values()}
		there = {c.cc: c.label for c in samples.controls.values()}

		shared = set(here) & set(there)
		differing = {number for number in shared if here[number] != there[number]}

		assert differing == {16, 17, 18, 19}

		# Both keep the same single LSB in the same place.
		assert cycles.controls["lfo_depth"].cc == 109
		assert cycles.controls["lfo_depth"].lsb == 110
		assert samples.controls["lfo_depth"].lsb == 110

	def test_the_machine_chooses_what_four_controls_do (self) -> None:
		"""Six machines, named once in the foreword and numbered nowhere."""
		cycles = pymidiinstrumentdefs.load("elektron/model_cycles", [CORPUS])

		machine = cycles.controls["machine_selection"]

		assert machine.cc == 70
		assert machine.part == "track"
		# No `choices`, because the manual gives no number for any machine.
		assert machine.choices == {}
		assert machine.values == {}

		for name in ("color", "shape", "sweep", "contour"):
			assert cycles.controls[name].part == "track"
			assert cycles.controls[name].group == "track"

	def test_it_answers_to_nrpn_and_no_number_is_published (self) -> None:
		"""As with the sibling, and the manual words the sentence slightly differently."""
		cycles = pymidiinstrumentdefs.load("elektron/model_cycles", [CORPUS])

		assert cycles.midi.nrpn == "supported"
		assert all(c.nrpn is None for c in cycles.controls.values())

		# And no range, for the reason the source account gives.
		assert all(c.range == (0, 127) for c in cycles.controls.values())

	def test_six_tracks_and_the_two_effects_as_on_the_sibling (self) -> None:
		"""Same parts, same assigned channels, and the sends still belong to a track."""
		cycles = pymidiinstrumentdefs.load("elektron/model_cycles", [CORPUS])

		assert set(cycles.parts) == {"track", "fx"}
		assert cycles.parts["track"].count == 6
		assert cycles.parts["track"].channel == "assigned"
		assert cycles.parts["track"].polyphony == 1
		assert cycles.parts["fx"].receives == ("controls",)

		on_fx = {name for name, c in cycles.controls.items() if c.part == "fx"}

		assert on_fx == {"delay_time", "delay_feedback", "reverb_size", "reverb_tone"}
		assert cycles.controls["delay_send"].part == "track"

	def test_what_it_shares_with_the_sibling_and_what_it_does_not_state (self) -> None:
		"""The same note bands, the same pattern count, the same three silences."""
		cycles = pymidiinstrumentdefs.load("elektron/model_cycles", [CORPUS])

		assert cycles.voice.note_range == (0, 60)
		assert cycles.voice.polyphony_shared is False
		assert cycles.midi.program_change is not None
		assert cycles.midi.program_change.presets == 96

		assert cycles.voice.aftertouch is None
		assert cycles.voice.pitch_bend is None
		assert cycles.midi.sysex is None

		assert cycles.model.firmware == "1.13"
		assert set(cycles.sources) == {"manual", "downloads", "release_notes"}


class TestElectribe:

	"""Sixteen parts on one MIDI channel, out of the one plain text source in this corpus."""

	def test_eighteen_controls_and_every_one_goes_both_ways (self) -> None:
		"""Korg's two tables name the same numbers, so none carries a direction."""
		et = pymidiinstrumentdefs.load("korg/electribe", [CORPUS])

		assert len(et.controls) == 18
		assert len(et.groups) == 7

		assert {c.cc for c in et.controls.values()} == {
			7, 10, 71, 72, 73, 74, 80, 81, 82, 83, 85, 86, 87, 102, 103, 104, 105, 106}

		assert all(c.direction == pymidiinstrumentdefs.definition.BOTH
			for c in et.controls.values())

	def test_a_switch_is_sent_as_nought_or_127_not_nought_or_one (self) -> None:
		"""The footnote gives "00,7F : Off,On", so a host sending 1 would be guessing."""
		et = pymidiinstrumentdefs.load("korg/electribe", [CORPUS])

		switches = {name: c.choices for name, c in et.controls.items() if c.choices}

		assert switches == {
			"insert_fx_on": {"off": 0, "on": 127},
			"mfx_send_on": {"off": 0, "on": 127},
			"master_fx_on": {"off": 0, "on": 127},
		}

		# Two named values make a switch rather than a choice, which the format derives.
		for name in switches:
			assert et.controls[name].kind == pymidiinstrumentdefs.SWITCH

	def test_a_bipolar_parameter_still_carries_the_wire_range (self) -> None:
		"""It reads -63 to +63 on the display and is sent as 0 to 127."""
		et = pymidiinstrumentdefs.load("korg/electribe", [CORPUS])

		for name in ("osc_pitch", "filter_eg_int", "amp_pan"):
			assert et.controls[name].range == (0, 127), f"{name} carries a display range"

	def test_sixteen_parts_and_no_part_is_addressable (self) -> None:
		"""One global channel, no per-part channel anywhere, and no stated note map."""
		et = pymidiinstrumentdefs.load("korg/electribe", [CORPUS])

		assert et.parts == {}
		assert et.midi.channels == (1, 16)

		# So no control belongs to a part either.
		assert all(c.part is None for c in et.controls.values())

	def test_aftertouch_is_a_checked_absence_and_pitch_bend_has_no_field (self) -> None:
		"""Both tables list every status byte, and there are four of them."""
		et = pymidiinstrumentdefs.load("korg/electribe", [CORPUS])

		assert et.voice.aftertouch == "none"
		assert et.voice.pitch_bend is None

		assert et.voice.velocity is not None
		assert et.voice.velocity.note_on == "both"
		assert et.voice.velocity.note_off is False

	def test_a_program_change_picks_one_of_250_patterns (self) -> None:
		"""And see the source account for why the published mapping reaches only 248."""
		et = pymidiinstrumentdefs.load("korg/electribe", [CORPUS])

		assert et.midi.program_change is not None
		assert et.midi.program_change.presets == 250
		assert et.midi.program_change.receives is True
		assert et.midi.program_change.sends is True

		assert et.voice.polyphony == 24
		assert et.voice.note_range == (0, 127)

	def test_the_implementation_has_no_pages_and_the_other_two_do (self) -> None:
		"""It is a text file, which is why nothing cites a page of it."""
		et = pymidiinstrumentdefs.load("korg/electribe", [CORPUS])

		assert set(et.sources) == {"midi_impl", "guide", "manual", "downloads"}
		assert et.sources["midi_impl"].paginated is False
		assert et.sources["midi_impl"].edition == "Revision 1.00"
		assert et.sources["downloads"].paginated is False

		# NOT RECORDED, because no document says which firmware it describes: the
		# implementation's "Revision 1.00" is the document's own, the chart's "Version: 1.02"
		# is the chart's, and Korg's two updaters are 2.02 and 1.19.
		assert et.model.firmware is None

		assert et.midi.sysex is True
		assert et.midi.nrpn is None

		# Only the owner's manual's chart gives a mode, and the implementation never does.
		assert et.midi.mode == 3


class TestPeak:

	"""The largest definition here, built from two documents that describe two firmwares."""

	def test_two_hundred_and_forty_six_controls_in_the_table_s_own_sections (self) -> None:
		"""230 rows of the manual and 19 of the addendum, less the three that are not controls."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		assert len(peak.controls) == 246
		assert len(peak.groups) == 10

		# The manual's own section headings, in the order it prints them, plus the two the
		# table gives no heading of its own.
		assert list(peak.groups) == [
			"voice", "oscillators", "mixer", "filter", "envelopes", "lfos", "effects",
			"arp", "mod_matrix", "settings"]

		# One setting governs the whole table, so no control carries a direction.
		assert all(c.direction == pymidiinstrumentdefs.definition.BOTH
			for c in peak.controls.values())

	def test_nrpn_is_the_main_road_and_the_high_half_is_the_mod_matrix_slot (self) -> None:
		"""`1:0` to `16:3` is sixteen slots of four, recorded as MSB x 128 + LSB."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		addressed = [c for c in peak.controls.values() if c.nrpn is not None and c.cc is None]

		assert len(addressed) == 172
		assert peak.midi.nrpn == "supported"

		# Slot 1 and slot 16, by the two halves the manual prints.
		assert peak.controls["mod_matrix_1_source1"].nrpn == 1 * 128 + 0
		assert peak.controls["mod_matrix_16_destination"].nrpn == 16 * 128 + 3

		slots = [c for c in peak.controls.values() if c.group == "mod_matrix"]

		# Sixteen slots of four, and the one selector that chooses between them.
		assert len(slots) == 16 * 4 + 1

	def test_every_control_change_pair_is_n_and_n_plus_32 (self) -> None:
		"""The check that separates a coarse-and-fine pair from an NRPN's two halves."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		pairs = [c for c in peak.controls.values() if c.lsb is not None]

		assert len(pairs) == 18

		# A pair always has both halves, which is what makes it a pair.
		assert all(c.cc is not None and c.lsb == c.cc + 32 for c in pairs)

		# And a fine half is never also a control change in its own right.
		coarse = {c.cc for c in peak.controls.values() if c.cc is not None}

		assert not coarse & {c.lsb for c in pairs}

		# Each such parameter runs past 127, which is why it has a fine half at all.
		assert all(c.range[1] > 127 for c in pairs)

	def test_thirty_three_controls_carry_no_default_because_the_documents_disagree (self) -> None:
		"""A default is recorded only where every statement the two documents make agrees."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		without = sorted(name for name, c in peak.controls.items() if c.default is None)

		assert len(without) == 33

		# Two are refused by the manual's own Init Patch table rather than by the arithmetic
		# of the MIDI list's two halves: it gives 2 where the list gives 0, and 127 where the
		# list gives 128.
		assert "amp_envelope_attack" in without
		assert "lfo_1_rate" in without

		# `0 (255)` cannot be read as a wire value and its own display on a 0-255 range.
		assert "filter_frequency" in without

		# The one row that prints a word where a number belongs.
		assert "arp_clock_sync_rate" in without

		# And four refused by a range the body states that the MIDI row's own bracket does
		# not: a pan that would start hard left, an arpeggiator that would start on two
		# octaves, and two effects whose three presets the body numbers 1 to 3.
		for name in ("pan_posn", "arp_clock_octave", "chorus_type", "reverb_type"):
			assert name in without, f"{name} carries a default the documents contradict"

		# The reverb is the one the manual disproves twice: its three presets set Reverb Size
		# to 0, 64 or 127 "respectively", and Reverb Size's own default is 64 - preset 2,
		# where a Reverb Type of 2 on a range of 0-2 would be preset 3.
		assert peak.controls["reverb_size"].default == 64

		# Where the documents do agree, the default stands: Arp/Clock Rhythm's 0 is Rhythm 1
		# on the body's range of 1 to 33, which is what the Init Patch table says.
		assert peak.controls["arp_clock_rhythm"].default == 0
		assert peak.controls["arp_clock_swing"].default == 50

	def test_the_summit_s_parameters_are_not_here (self) -> None:
		"""The addendum covers both synths and marks which features belong to which."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		numbers = {c.nrpn for c in peak.controls.values() if c.nrpn is not None}

		# `Atouch Scale`, NRPN 64:3, is in the shared MIDI parameters list and is under the
		# heading "Update Features Exclusive to Summit".
		assert 64 * 128 + 3 not in numbers

		# The three FM NRPNs named only in a bug-fix list, beside fixes for voices 9-16.
		assert not {25 * 128 + 13, 25 * 128 + 17, 25 * 128 + 21} & numbers

		# What the addendum does bring to the Peak, from the same list.
		assert peak.controls["patch_cue"].nrpn == 64 * 128 + 0
		assert peak.controls["select_tuning_table"].nrpn == 25 * 128 + 6

	def test_a_number_reserved_before_the_parameter_existed (self) -> None:
		"""The manual prints the NRPN and an empty range; the addendum fills it in."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		hpf = peak.controls["osc_common_noise_hpf"]

		assert hpf.nrpn == 12
		assert hpf.range == (0, 127)

		# Its sibling, which firmware 1.2 did have, for comparison.
		assert peak.controls["osc_common_noise_lpf"].nrpn == 11
		assert peak.controls["osc_common_noise_lpf"].default == 127

	def test_one_parameter_is_renamed_rather_than_added (self) -> None:
		"""NRPN 0:5 is Voice Unison Spread in the manual and Spread in the addendum."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		assert "voice_unison_spread" not in peak.controls
		assert peak.controls["spread"].nrpn == 5
		assert peak.controls["spread"].label == "Spread"

		# Nothing answers to a number twice.
		for field in ("cc", "nrpn"):
			used = [getattr(c, field) for c in peak.controls.values()
				if getattr(c, field) is not None]

			assert len(used) == len(set(used)), f"two controls share a {field}"

	def test_nothing_is_stepped_because_nothing_is_numbered (self) -> None:
		"""The manual names the states of its selectors in prose and numbers none of them."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		assert not any(c.choices or c.values for c in peak.controls.values())

		# The parameter that shows why: three settings over a range of 0-2, where the MIDI
		# list's default and the Init Patch table's disagree about which is first.
		assert peak.controls["lfo_1_range"].range == (0, 2)

		# And the two LFOs the manual calls identical are not addressed alike.
		assert peak.controls["lfo_1_range"].nrpn == 68
		assert peak.controls["lfo_1_range"].cc is None
		assert peak.controls["lfo_2_range"].cc == 83
		assert peak.controls["lfo_2_range"].nrpn is None

	def test_three_ranges_do_not_fit_the_lists_they_select_from (self) -> None:
		"""Carried as printed, because the range is what the row gives and the list has none."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		# 17 values for a table of 23 sources, where the 37 destinations do fit 0-36.
		for slot in (1, 8, 16):
			assert peak.controls[f"mod_matrix_{slot}_source1"].range == (0, 16)
			assert peak.controls[f"mod_matrix_{slot}_source2"].range == (0, 16)
			assert peak.controls[f"mod_matrix_{slot}_destination"].range == (0, 36)

		# 19 values for a table of 16 divisions - the arpeggiator's range, which has 19.
		assert peak.controls["delay_sync_time"].range == (0, 18)
		assert peak.controls["arp_clock_sync_rate"].range == (0, 18)

	def test_the_fx_modulation_matrix_reaches_no_number_at_all (self) -> None:
		"""Sixteen main matrix slots are numbered in full and the four FX slots are not."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		assert not [name for name in peak.controls if name.startswith("fx_mod")]

		# Nor does anything in the Settings menu, bar the tuning table's selection.
		for absent in ("midi_channel", "midichan", "local", "bank_patch", "transpose",
				"velshape", "arp_clock_source", "arp_midi"):
			assert absent not in peak.controls, f"{absent} is numbered nowhere in either document"

		assert peak.controls["select_tuning_table"].range == (0, 16)

	def test_the_tempo_is_the_one_row_no_message_reaches (self) -> None:
		"""`Arp/Clock Rate` is printed with a control number of NA:NA."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		assert "arp_clock_rate" not in peak.controls

		# Its neighbours in the same section are all addressable.
		assert peak.controls["arp_clock_gate"].cc == 116
		assert peak.controls["arp_clock_swing"].nrpn == 120

	def test_eight_voices_and_a_bend_range_per_oscillator (self) -> None:
		"""Three oscillators, three bend ranges, and no keyboard of its own."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		assert peak.voice.polyphony == 8
		assert peak.voice.aftertouch == "poly"

		# Voicing is a setting saved with the Patch: three mono modes and two poly ones.
		assert peak.voice.voicing_modes == (1, 8)
		assert peak.controls["voice_mode"].nrpn == 2
		assert peak.controls["voice_mode"].range == (0, 4)

		assert peak.voice.pitch_bend is not None
		assert peak.voice.pitch_bend.semitones == 12
		assert peak.voice.pitch_bend.programmable is True

		for which in (1, 2, 3):
			bend = peak.controls[f"oscillator_{which}_bend_range"]

			assert bend.range == (40, 88), f"oscillator {which} bends over the wrong range"
			assert bend.default == 76, f"oscillator {which} does not start at +12"

		# It has no keyboard, so velocity and aftertouch are received and never sent.
		assert peak.voice.velocity is not None
		assert peak.voice.velocity.note_on == "received"
		assert peak.voice.note_range is None

	def test_two_documents_two_firmwares_and_the_later_one_is_recorded (self) -> None:
		"""The manual is for v1.2 and the addendum for 2.0 and 2.1."""
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		assert peak.model.firmware == "2.1"
		assert set(peak.sources) == {"manual", "addendum", "download_page"}

		assert peak.sources["manual"].edition == "for firmware v1.2"
		assert peak.sources["addendum"].edition == "V1, for firmware updates 2.0 and 2.1"
		assert peak.sources["download_page"].paginated is False

		assert peak.midi.channels == (1, 16)
		assert peak.midi.clock == "receives"
		assert peak.midi.transport is None
		assert peak.midi.mode is None
		assert peak.midi.sysex is True

		assert peak.midi.program_change is not None
		assert peak.midi.program_change.presets == 512
		assert peak.midi.program_change.receives is True
		assert peak.midi.program_change.sends is True


class TestModwaveMkII:

	"""One document set for three products, and a chart whose columns had to be proved."""

	def test_fifteen_controls_off_three_tables (self) -> None:
		"""Nine from the chart, five from MIDI CC Assign, and one the chart never names."""
		mw = pymidiinstrumentdefs.load("korg/modwave_mk_ii", [CORPUS])

		assert len(mw.controls) == 15
		assert len(mw.groups) == 5

		# The chart's nine named controller numbers.
		for number in (1, 7, 10, 11, 18, 19, 64, 66, 67):
			assert number in {c.cc for c in mw.controls.values()}, f"cc {number} is missing"

		# The five the "MIDI CC Assign" table gives a default assignment for.
		assert mw.controls["scale_select"].cc == 9

		for which in (1, 2, 3, 4):
			assert mw.controls[f"mod_knob_{which}"].cc == 23 + which

		# And the KAOSS button, which the chart mentions only by folding 12 into "12-31".
		assert mw.controls["kaoss_button"].cc == 12

	def test_five_controls_are_received_and_never_sent (self) -> None:
		"""The chart marks them X transmitted and O recognized, and the prose agrees."""
		mw = pymidiinstrumentdefs.load("korg/modwave_mk_ii", [CORPUS])

		receiving = sorted(name for name, c in mw.controls.items()
			if c.direction == pymidiinstrumentdefs.definition.RECEIVES)

		assert receiving == ["expression", "pan", "soft", "sostenuto", "volume"]

		# Everything else goes both ways, including the Mod Knobs, which "send and receive".
		for name in ("modulation", "damper", "kaoss_pad_x", "kaoss_pad_y", "mod_knob_1"):
			assert mw.controls[name].direction == pymidiinstrumentdefs.definition.BOTH

	def test_no_nrpn_and_it_is_a_checked_absence (self) -> None:
		"""The chart's own numbers reach everything but 96 to 101, which is that block."""
		mw = pymidiinstrumentdefs.load("korg/modwave_mk_ii", [CORPUS])

		assert mw.midi.nrpn == "none"

		# No control carries one either, so the two statements cannot drift apart.
		assert all(c.nrpn is None for c in mw.controls.values())

	def test_transport_is_refused_rather_than_unstated (self) -> None:
		"""Song Position, Song Select and the real-time Commands are all X in both columns."""
		mw = pymidiinstrumentdefs.load("korg/modwave_mk_ii", [CORPUS])

		assert mw.midi.transport == "none"

		# Clock is the one real-time message it does answer to, and in both directions.
		assert mw.midi.clock == "both"
		assert mw.midi.mode == 3

	def test_two_layers_each_on_a_channel_of_its_own (self) -> None:
		"""A Performance has two, and program change is global by way of the Set List."""
		mw = pymidiinstrumentdefs.load("korg/modwave_mk_ii", [CORPUS])

		assert set(mw.parts) == {"layer"}

		layer = mw.parts["layer"]

		assert layer.count == 2
		assert layer.is_assigned is True
		assert layer.channel_offset is None

		# Notes and controllers reach a Layer; program change does not.
		assert layer.receives == ("notes", "controls")

		# Sixty voices are a ceiling across the pair, not a figure each can count on.
		assert mw.voice.polyphony == 60
		assert mw.voice.polyphony_shared is True
		assert mw.voice.voicing_modes == (1, 60)

	def test_the_voice_count_is_the_only_thing_that_is_the_mk_ii_s (self) -> None:
		"""One specification sentence covers three models and differs in one number."""
		mw = pymidiinstrumentdefs.load("korg/modwave_mk_ii", [CORPUS])

		assert mw.model.name == "modwave mk II"
		assert mw.model.firmware == "3.0"

		# Five documents, including the sibling's download page, fetched to prove the two
		# products are served one document set.
		assert set(mw.sources) == {
			"manual", "property_exchange", "about_mk_ii", "download_page",
			"download_page_modwave"}

		# The chart is printed five pages lower than its file page.
		assert mw.sources["manual"].page_offset == 5
		assert mw.sources["property_exchange"].paginated is False

	def test_release_velocity_is_sent_narrower_than_it_is_heard (self) -> None:
		"""O 8n V=1-64 transmitted against O 8n V=0-127 recognized."""
		mw = pymidiinstrumentdefs.load("korg/modwave_mk_ii", [CORPUS])

		assert mw.voice.velocity is not None
		assert mw.voice.velocity.note_on == "both"
		assert mw.voice.velocity.note_off is True

		# Received only, and both kinds, which the prose settles independently of the chart.
		assert mw.voice.aftertouch == "poly"

		# Settable in both directions with no published default.
		assert mw.voice.pitch_bend is not None
		assert mw.voice.pitch_bend.programmable is True
		assert mw.voice.pitch_bend.semitones is None

	def test_program_change_reaches_a_set_list_slot (self) -> None:
		"""Sixty-four of them, numbered from zero on the wire and from one on the panel."""
		mw = pymidiinstrumentdefs.load("korg/modwave_mk_ii", [CORPUS])

		assert mw.midi.program_change is not None
		assert mw.midi.program_change.presets == 64
		assert mw.midi.program_change.receives is True
		assert mw.midi.program_change.sends is True

		# No factory channel is published - the chart's Default cell holds the whole range.
		assert mw.midi.channels == (1, 16)


class TestMC707:

	"""Three editions of one chart, and an instrument two firmware releases ahead of it."""

	def test_twenty_seven_controls_and_only_three_are_sent (self) -> None:
		"""Every control change row is x transmitted but the three panel knobs."""
		mc = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		assert len(mc.controls) == 28
		assert len(mc.groups) == 7

		sending = sorted(c.cc for c in mc.controls.values()
			if c.direction == pymidiinstrumentdefs.definition.BOTH and c.cc is not None)

		assert sending == [80, 81, 82, 83]

		for name in ("filter_knob", "mod_knob", "fx_knob", "sound_knob"):
			assert mc.controls[name].direction == pymidiinstrumentdefs.definition.BOTH

		# The other twenty-four are recognised and never sent.
		assert len([c for c in mc.controls.values()
			if c.direction == pymidiinstrumentdefs.definition.RECEIVES]) == 24

	def test_the_footnoted_knob_is_kept (self) -> None:
		"""CC 83 is footnoted "for MC-101 compatibility" and is still this chart's own row."""
		mc = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		# The chart is headed "Model: MC-707" and marks the row o in both columns, and Ver.1.60
		# gave this instrument a virtual SOUND knob after all.
		assert mc.controls["sound_knob"].cc == 83
		assert mc.controls["sound_knob"].label == "SOUND Knob"

		# Nothing is left out of the chart: all 25 of its numbers are here.
		from_chart = {1, 5, 7, 10, 11, 64, 65, 66, 67, 68, 71, 72, 73, 74, 75, 76, 77, 78,
			80, 81, 82, 83, 84, 91, 92}

		assert from_chart <= {c.cc for c in mc.controls.values()}
		assert len(from_chart) == 25

	def test_three_numbers_come_from_the_update_notes (self) -> None:
		"""The chart is Version 1.60 and the firmware is 1.80, which named three more."""
		mc = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		for name, number in (("breath_control", 2), ("foot_control", 4),
				("delay_send", 93)):
			assert mc.controls[name].cc == number
			assert mc.controls[name].direction == pymidiinstrumentdefs.definition.RECEIVES

		assert mc.model.firmware == "1.80"
		assert mc.sources["chart"].edition == "Version 1.60"

	def test_two_numbers_are_published_for_chorus_send (self) -> None:
		"""The chart gives 92 and the Ver.1.80 notes give 93, and both are carried."""
		mc = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		assert mc.controls["chorus_send"].cc == 92
		assert mc.controls["delay_send"].cc == 93

		# Each under the name of the document that defines it as a parameter.
		assert mc.controls["chorus_send"].label == "General Purpose Effect 3 (Chorus Send Level)"
		assert mc.controls["delay_send"].label == "Delay Send Level"

		# And reverb send, which both documents agree about, is 91.
		assert mc.controls["reverb_send"].cc == 91

	def test_all_three_chart_editions_are_kept (self) -> None:
		"""What a maker added to a chart is evidence the current edition does not give."""
		mc = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		assert set(mc.sources) == {
			"chart", "chart_1_00", "chart_1_20", "reference", "update", "support_page"}

		assert mc.sources["chart_1_00"].edition == "Version 1.00"
		assert mc.sources["chart_1_20"].edition == "Version 1.20"

		# Each chart is one page and is cited as p. 1, so its quotations can be checked.
		for which in ("chart", "chart_1_00", "chart_1_20"):
			assert mc.sources[which].paginated is True
			assert mc.sources[which].page_offset == 0

	def test_eight_tracks_and_a_channel_that_makes_no_sound (self) -> None:
		"""Program change means a clip on a track channel and a scene on the control one."""
		mc = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		assert set(mc.parts) == {"track", "control"}

		track = mc.parts["track"]

		assert track.count == 8
		assert track.is_assigned is True
		assert track.receives == ("notes", "controls", "program_change")

		control = mc.parts["control"]

		assert control.count == 1
		assert control.is_assigned is True

		# It takes a program change and the Scatter Pad's notes, and no control change.
		assert control.receives == ("notes", "program_change")

		# The scenes a program change reaches on that channel.
		assert mc.midi.program_change is not None
		assert mc.midi.program_change.presets == 128

	def test_system_exclusive_is_not_recorded_because_the_documents_disagree (self) -> None:
		"""The chart marks it x in both columns; the reference manual has a Device ID for it."""
		mc = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		assert mc.midi.sysex is None

		# NRPN, by contrast, is a checked absence: the chart names its numbers one at a time.
		assert mc.midi.nrpn == "none"
		assert all(c.nrpn is None for c in mc.controls.values())

	def test_what_the_chart_settles_about_the_voice (self) -> None:
		"""Transport both ways with one asymmetry, and a voice count nobody publishes."""
		mc = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		assert mc.midi.channels == (1, 16)
		assert mc.midi.mode == 3
		assert mc.midi.clock == "both"
		assert mc.midi.transport == "both"

		# No document states a voice count; what is established is that the tracks share one.
		assert mc.voice.polyphony is None
		assert mc.voice.polyphony_shared is True

		assert mc.voice.velocity is not None
		assert mc.voice.velocity.note_on == "both"
		assert mc.voice.velocity.note_off is True

		assert mc.voice.aftertouch == "poly"
		assert mc.voice.pitch_bend is not None
		assert mc.voice.pitch_bend.programmable is True
		assert mc.voice.pitch_bend.semitones is None


class TestMuse:

	"""One appendix printed four times, wrong twice, and two timbres on two channels."""

	def test_a_hundred_and_two_rows_in_seventeen_panel_modules (self) -> None:
		"""Every row of the appendix is here, grouped by the module its name belongs to."""
		muse = pymidiinstrumentdefs.load("moog/muse", [CORPUS])

		assert len(muse.controls) == 102
		assert len(muse.groups) == 17

		numbers = sorted(c.cc for c in muse.controls.values() if c.cc is not None)

		assert len(numbers) == 102
		assert numbers[0] == 1
		assert numbers[-1] == 116

		# What the table leaves alone, which is why no NRPN is recorded: the data entry pair,
		# bank select LSB, and the whole of 96 to 101.
		missing = sorted(set(range(1, 117)) - set(numbers))

		assert missing == [2, 4, 6, 32, 38, 63, 74, 84, 96, 97, 98, 99, 100, 101]

		# Every row carries a group, and no row is left over.
		assert all(c.group in muse.groups for c in muse.controls.values())

	def test_the_two_misprints_are_corrected (self) -> None:
		"""`5-99` becomes 75 by arithmetic, and `ODR` becomes `ord` by the manual's own prose."""
		muse = pymidiinstrumentdefs.load("moog/muse", [CORPUS])

		# The modulation oscillator's bands are 25 apart, so the printed 5 can only be 75.
		waveform = muse.controls["modulation_oscillator_waveform"]

		assert waveform.cc == 28
		assert waveform.values == {"sine": 0, "sawtooth": 25, "ramp": 50, "square": 75,
			"noise": 100}

		# The arpeggiator's DIRECTION switch is ORD in two other places in the same manual.
		direction = muse.controls["arpeggiator_direction"]

		assert direction.cc == 114
		assert direction.values == {"ord": 0, "ptn": 43, "rnd": 85}

	def test_the_bands_a_name_cannot_hold_as_printed (self) -> None:
		"""Organ stops and a bare count, which the page prints as `16’` and as `1`."""
		muse = pymidiinstrumentdefs.load("moog/muse", [CORPUS])

		for name in ("oscillator_1_octave", "oscillator_2_octave"):
			assert muse.controls[name].values == {"ft_16": 0, "ft_8": 32, "ft_4": 64, "ft_2": 96}

		assert muse.controls["arpeggiator_octave_range"].values == \
			{"one": 0, "two": 32, "three": 64, "four": 96}

		# Twenty-seven of the rows are a plain switch, written `0-63 off/ 64-127 on`.
		switches = [c for c in muse.controls.values() if c.values == {"off": 0, "on": 64}]

		assert len(switches) == 27

		# And ten are a list of named bands, which with the switches is 37 of the 102.
		banded = [c for c in muse.controls.values() if c.values]

		assert len(banded) == 37

	def test_eighty_nine_rows_are_a_timbre_s_and_thirteen_are_not (self) -> None:
		"""The panel edits one timbre; the output, delay, sequencer and clock are global."""
		muse = pymidiinstrumentdefs.load("moog/muse", [CORPUS])

		assert set(muse.parts) == {"timbre"}

		timbre = muse.parts["timbre"]

		assert timbre.count == 2
		assert timbre.channel == "assigned"
		assert timbre.receives == ("notes", "controls")

		assert len([c for c in muse.controls.values() if c.part == "timbre"]) == 89

		global_groups = {"output", "delay", "sequencer", "clock"}
		elsewhere = [c for c in muse.controls.values() if c.part is None]

		assert len(elsewhere) == 13
		assert {c.group for c in elsewhere} == global_groups

		# The arpeggiator is per timbre where the sequencer is not, which the specification says.
		assert muse.controls["arpeggiator_clock_div"].part == "timbre"
		assert muse.controls["sequencer_clock_div"].part is None

	def test_eight_voices_shared_between_the_two_timbres (self) -> None:
		"""One pool of eight that the two voice counts always sum to."""
		muse = pymidiinstrumentdefs.load("moog/muse", [CORPUS])

		assert muse.voice.polyphony == 8
		assert muse.voice.polyphony_shared is True
		assert muse.voice.voicing_modes == (1, 8)

		# A shared pool and a part with voices of its own cannot both be true.
		assert muse.parts["timbre"].polyphony is None

		assert muse.voice.aftertouch == "channel"
		assert muse.voice.pitch_bend is not None
		assert muse.voice.pitch_bend.semitones == 7
		assert muse.voice.pitch_bend.programmable is True

		assert muse.voice.velocity is not None
		assert muse.voice.velocity.note_on == "both"
		assert muse.voice.velocity.note_off is None

		# The keybed is 61 keys, which is a panel and not a span of note numbers.
		assert muse.voice.note_range is None

	def test_what_the_settings_pages_settle (self) -> None:
		"""Clock and transport both ways, 256 patches, and no chart to give a mode."""
		muse = pymidiinstrumentdefs.load("moog/muse", [CORPUS])

		assert muse.midi.channels == (1, 16)
		assert muse.midi.clock == "both"
		assert muse.midi.transport == "both"

		assert muse.midi.program_change is not None
		assert muse.midi.program_change.receives is True
		assert muse.midi.program_change.sends is True
		assert muse.midi.program_change.presets == 256

		# Moog publishes no implementation chart for this instrument, so there is no mode row.
		assert muse.midi.mode is None

		# NRPN is a checked absence; system exclusive is a silence and is left unrecorded.
		assert muse.midi.nrpn == "none"
		assert muse.midi.sysex is None

		assert all(c.nrpn is None for c in muse.controls.values())

	def test_the_appendix_is_printed_in_four_documents (self) -> None:
		"""The manual and all three sets of release notes, which is why nothing rests on one."""
		muse = pymidiinstrumentdefs.load("moog/muse", [CORPUS])

		assert set(muse.sources) == {"manual", "release_notes", "release_notes_1_3_0",
			"release_notes_1_2_0", "quickstart"}

		assert muse.model.firmware == "1.4.0"
		assert muse.sources["manual"].edition == "1.4.0"

		for name in ("release_notes", "release_notes_1_3_0", "release_notes_1_2_0"):
			assert muse.sources[name].kind == "release_notes"

		# Every page of this manual prints its own number and it is the file's page index.
		assert all(source.page_offset == 0 for source in muse.sources.values())

	def test_the_whole_map_is_sent_and_none_of_it_answered_as_shipped (self) -> None:
		"""Both directions, which is what the instrument does rather than how it is set."""
		muse = pymidiinstrumentdefs.load("moog/muse", [CORPUS])

		# SEND CC defaults on and RECIEVE CC defaults off, but both are switches a player moves,
		# so no control carries a direction of its own.
		assert all(c.direction == pymidiinstrumentdefs.definition.BOTH
			for c in muse.controls.values())

		# The two rows whose direction prose states outright, for both pedals.
		assert muse.controls["sustain_pedal"].cc == 64
		assert muse.controls["expression"].cc == 11


class TestAstroLab:

	"""A Section column that cannot be carried down, and a row published as neither direction."""

	def test_thirty_six_of_thirty_seven_published_rows (self) -> None:
		"""The table gives 37; one is neither sent nor received and so is not a control."""
		astrolab = pymidiinstrumentdefs.load("arturia/astrolab", [CORPUS])

		assert len(astrolab.controls) == 36
		assert len(astrolab.groups) == 6

		numbers = sorted(c.cc for c in astrolab.controls.values() if c.cc is not None)

		assert numbers[0] == 1
		assert numbers[-1] == 115

		# CC 7, Master Volume, is published "Never" sending and "Never" receiving, which none of
		# the format's three directions can say.
		assert 7 not in numbers

		assert all(c.group in astrolab.groups for c in astrolab.controls.values())

	def test_the_groups_are_not_the_section_column (self) -> None:
		"""Carrying the table's Section label down would file Timbre under Pedals."""
		astrolab = pymidiinstrumentdefs.load("arturia/astrolab", [CORPUS])

		# The manual gives the Macro knobs as 74, 71, 76 and 77, which is what settles Timbre.
		macros = {c.cc for c in astrolab.controls.values() if c.group == "macros"}

		assert macros == {71, 74, 76, 77}

		# The three pedal inputs the Section column would put under "Master", and Sustain.
		pedals = {c.cc for c in astrolab.controls.values() if c.group == "pedals"}

		assert pedals == {11, 12, 13, 64}

		# "Effects" labels one row in the table and four belong to it.
		effects = {c.cc for c in astrolab.controls.values() if c.group == "effects"}

		assert effects == {16, 18, 19, 93}

	def test_the_four_direction_words_become_two (self) -> None:
		"""Always and Not linked travel both ways; Never and n/a are received only."""
		astrolab = pymidiinstrumentdefs.load("arturia/astrolab", [CORPUS])

		both = [c for c in astrolab.controls.values()
			if c.direction == pymidiinstrumentdefs.definition.BOTH]
		receives = [c for c in astrolab.controls.values()
			if c.direction == pymidiinstrumentdefs.definition.RECEIVES]

		assert len(both) == 13
		assert len(receives) == 23

		# Nothing is transmit-only: every row's Receiving cell but the excluded one says Always.
		assert not [c for c in astrolab.controls.values()
			if c.direction == pymidiinstrumentdefs.definition.TRANSMITS]

		# The Macros are "Not linked" sending, so they do travel out.
		for name in ("timbre", "brightness", "time", "movement"):
			assert astrolab.controls[name].direction == pymidiinstrumentdefs.definition.BOTH

		# The Faders are "n/a" sending - nothing on this panel sends them.
		assert all(c.direction == pymidiinstrumentdefs.definition.RECEIVES
			for c in astrolab.controls.values() if c.group == "faders")

	def test_nine_faders_the_manual_never_explains (self) -> None:
		"""Named only inside the table, and numbered out of step with their controllers."""
		astrolab = pymidiinstrumentdefs.load("arturia/astrolab", [CORPUS])

		faders = {c.label: c.cc for c in astrolab.controls.values() if c.group == "faders"}

		assert len(faders) == 9
		assert faders["Fader 4"] == 72
		assert faders["Fader 1"] == 73
		assert faders["Fader 9"] == 85

	def test_two_parts_that_do_not_share_their_voices (self) -> None:
		"""Voices are per part, and how many is the loaded engine's rather than the box's."""
		astrolab = pymidiinstrumentdefs.load("arturia/astrolab", [CORPUS])

		assert set(astrolab.parts) == {"part"}

		part = astrolab.parts["part"]

		assert part.count == 2
		assert part.channel == "assigned"
		assert part.receives == ("notes", "controls")

		assert astrolab.voice.polyphony_shared is False

		# No single figure exists: the manual prints a voice count per instrument engine.
		assert astrolab.voice.polyphony is None
		assert part.polyphony is None

		assert astrolab.voice.aftertouch == "channel"
		assert astrolab.voice.pitch_bend is not None
		assert astrolab.voice.pitch_bend.programmable is True
		assert astrolab.voice.pitch_bend.semitones is None

	def test_clock_and_transport_come_in_and_do_not_go_out (self) -> None:
		"""Sync is a received thing here; the MIDI Out Filter's widest setting is notes only."""
		astrolab = pymidiinstrumentdefs.load("arturia/astrolab", [CORPUS])

		assert astrolab.midi.clock == "receives"
		assert astrolab.midi.transport == "receives"
		assert astrolab.midi.channels == (1, 16)

		# No chart, so no mode; neither sysex nor NRPN is named in any document held.
		assert astrolab.midi.mode is None
		assert astrolab.midi.sysex is None
		assert astrolab.midi.nrpn is None

	def test_program_change_comes_from_the_release_notes (self) -> None:
		"""The manual never mentions it; the firmware history gives both directions."""
		astrolab = pymidiinstrumentdefs.load("arturia/astrolab", [CORPUS])

		assert astrolab.midi.program_change is not None
		assert astrolab.midi.program_change.receives is True
		assert astrolab.midi.program_change.sends is True

		# "Over 1,800" is not a count of addressable locations.
		assert astrolab.midi.program_change.presets is None

	def test_the_documents_and_what_each_is_for (self) -> None:
		"""One manual for two models, three sets of release notes, a page and a cheatsheet."""
		astrolab = pymidiinstrumentdefs.load("arturia/astrolab", [CORPUS])

		assert set(astrolab.sources) == {"manual", "release_notes", "release_notes_88",
			"release_notes_37", "resources_page", "cheatsheet"}

		# The firmware is two releases ahead of the manual that carries the map.
		assert astrolab.model.firmware == "1.7.0"
		assert astrolab.sources["manual"].edition == "1.5.1"

		# The folio is six lower than the file's page, which no other source here needs.
		assert astrolab.sources["manual"].page_offset == 6

		# The cheatsheet's version string reads newer than the manual's and is twenty months
		# older, which is why its date is recorded.
		assert astrolab.sources["cheatsheet"].edition == "1.6.0-cheatsheet"
		assert astrolab.sources["cheatsheet"].dated == "2024-04-08"


class TestIridium:

	"""An instrument with no control map, and two product pages serving one file."""

	def test_fifteen_numbers_the_maker_fixes_and_no_map (self) -> None:
		"""MIDI Learn reaches everything else, so the other 118 are the player's."""
		iridium = pymidiinstrumentdefs.load("waldorf/iridium", [CORPUS])

		assert len(iridium.controls) == 15
		assert len(iridium.groups) == 4

		assert iridium.midi.control_change == "learned"

		numbers = sorted(c.cc for c in iridium.controls.values() if c.cc is not None)

		assert numbers == [1, 2, 11, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 64, 74]

		# Every one is a modulation source, which is a thing received.
		assert all(c.direction == pymidiinstrumentdefs.definition.RECEIVES
			for c in iridium.controls.values())

	def test_the_ten_in_a_range_are_a_named_source (self) -> None:
		"""The maker prints one row for ten numbers, and they are fixed rather than assignable."""
		iridium = pymidiinstrumentdefs.load("waldorf/iridium", [CORPUS])

		block = sorted(c.cc for c in iridium.controls.values()
			if c.group == "modulation" and c.cc is not None)

		assert block == list(range(22, 32))

		for number in block:
			assert iridium.controls[f"cc_{number}"].label == f"CC {number}"

		# The four the table names one at a time, and the one from the MPE section.
		assert iridium.controls["wheel"].cc == 1
		assert iridium.controls["breath_control"].cc == 2
		assert iridium.controls["expression"].cc == 11
		assert iridium.controls["pedal"].cc == 64
		assert iridium.controls["mpe_y_axis"].cc == 74

	def test_it_sends_nrpn_and_ignores_incoming_nrpn (self) -> None:
		"""The only instrument here whose maker says so, and the field records the receiving half."""
		iridium = pymidiinstrumentdefs.load("waldorf/iridium", [CORPUS])

		assert iridium.midi.nrpn == "none"
		assert all(c.nrpn is None for c in iridium.controls.values())

		# That it transmits NRPN has no field; the source account carries it.
		assert "send out MIDI NRPN data" in (iridium.source or "")

	def test_mpe_with_two_layers_sharing_sixteen_voices (self) -> None:
		"""Per-note channels, and a voice pool the two Layers divide between them."""
		iridium = pymidiinstrumentdefs.load("waldorf/iridium", [CORPUS])

		assert iridium.midi.per_voice_channels is True

		assert iridium.voice.polyphony == 16
		assert iridium.voice.polyphony_shared is True

		assert set(iridium.parts) == {"layer"}

		layer = iridium.parts["layer"]

		assert layer.count == 2
		assert layer.channel == "assigned"
		assert layer.receives == ("notes", "controls")
		assert layer.polyphony is None

		assert iridium.voice.aftertouch == "poly"

	def test_no_note_range_because_the_one_sentence_is_not_about_one (self) -> None:
		"""The split-range limits bound a split point, and contradict the manual's own numbering."""
		iridium = pymidiinstrumentdefs.load("waldorf/iridium", [CORPUS])

		assert iridium.voice.note_range is None

		# Pitch bend is set per oscillator and all three default to twelve semitones.
		assert iridium.voice.pitch_bend is not None
		assert iridium.voice.pitch_bend.semitones == 12
		assert iridium.voice.pitch_bend.programmable is True

	def test_what_is_left_unrecorded_and_why (self) -> None:
		"""No chart, no channel range printed anywhere, and clock in one direction."""
		iridium = pymidiinstrumentdefs.load("waldorf/iridium", [CORPUS])

		# The manual says a channel is chosen per Layer and never says which are on offer.
		assert iridium.midi.channels is None
		assert iridium.midi.mode is None
		assert iridium.midi.sysex is None
		assert iridium.midi.transport is None

		assert iridium.midi.clock == "receives"

		# Program change is stated once, on the product page, under a title that denies it.
		assert iridium.midi.program_change is not None
		assert iridium.midi.program_change.receives is True

		# A Macro button sends one on demand, which is the only sending the manual describes.
		assert iridium.midi.program_change.sends is True
		assert iridium.midi.program_change.presets is None

	def test_one_manual_two_products_and_a_sibling_cited_twice (self) -> None:
		"""Four sources: the shared manual, both product pages, and the MK2's for two sentences."""
		iridium = pymidiinstrumentdefs.load("waldorf/iridium", [CORPUS])

		assert set(iridium.sources) == {"manual", "mk2_manual", "product_page", "keyboard_page"}

		assert iridium.sources["manual"].edition == "OS 3"
		assert iridium.sources["manual"].page_offset == 0

		# The two product pages are cited for the same file under two different share ids.
		assert iridium.sources["product_page"].paginated is False
		assert iridium.sources["keyboard_page"].paginated is False

		assert iridium.model.firmware == "3"


class TestCircuitTracks:

	"""The largest definition here, and a maker whose contents page misfiles a control table."""

	def test_the_largest_definition_here_and_where_its_rows_come_from (self) -> None:
		"""Four addressable things and a table the reference guide does not carry."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		assert len(tracks.controls) == 358
		assert len(tracks.groups) == 18

		# Bigger than the Peak, which held the record before it.
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		assert len(tracks.controls) > len(peak.controls)

		counted = collections.Counter(control.part for control in tracks.controls.values())

		assert counted["synth"] == 276
		assert counted["project"] == 38
		assert counted["drums"] == 28
		assert counted["midi_track"] == 8

		# The eight the guide gives no channel for carry no part at all.
		assert counted[None] == 8

	def test_the_audio_table_is_a_control_table_and_names_no_channel (self) -> None:
		"""The contents page files it with the value tables, and it holds eight controls."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		audio = [control for control in tracks.controls.values() if control.group == "audio"]

		assert len(audio) == 8
		assert sorted(control.cc for control in audio
			if control.cc is not None) == [13, 15, 31, 32, 33, 34, 35, 36]

		# No part, because no document says which channel reaches them.
		assert all(control.part is None for control in audio)

		# Nothing else in the definition uses these eight numbers on this instrument's own
		# channels without a part, so losing them would lose the audio inputs entirely.
		assert tracks.controls["audio_1_level"].default == 100
		assert tracks.controls["audio_2_pan"].cc == 36

	def test_eight_controls_come_from_the_user_guide_and_only_travel_out (self) -> None:
		"""A MIDI track drives external gear, so its Macro knobs send and nothing answers them."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		template = [control for control in tracks.controls.values()
			if control.group == "midi_template"]

		assert len(template) == 8
		assert sorted(control.cc for control in template
			if control.cc is not None) == [1, 2, 5, 11, 12, 13, 71, 74]

		assert all(control.direction == pymidiinstrumentdefs.definition.TRANSMITS
			for control in template)

		# They are the only ones here that do not go both ways.
		outward = [control.name for control in tracks.controls.values()
			if control.direction != pymidiinstrumentdefs.definition.BOTH]

		assert sorted(outward) == sorted(control.name for control in template)

	def test_an_nrpn_is_msb_times_128_plus_lsb_and_the_guide_proves_it (self) -> None:
		"""Two blocks of numbers come out as arithmetic sequences, which is the proof."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		# Twelve matrix slots at five-number intervals: 1:83 is 211 and 2:10 is 266.
		slots = [tracks.controls[f"mod_matrix_{slot}_source_1"].nrpn for slot in range(1, 13)]

		assert slots == list(range(211, 267, 5))

		# Eight macro knobs of sixteen parameters fill one MSB page exactly, 3:0 to 3:127.
		macros = sorted(control.nrpn for control in tracks.controls.values()
			if control.group == "macro_knobs" and control.nrpn is not None)

		assert macros == list(range(384, 512))

	def test_five_defaults_the_guide_contradicts_itself_about_are_not_recorded (self) -> None:
		"""The control map and the Synth Patch Format disagree, so neither figure is carried."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		contradicted = ["osc_1_wave_interpolate", "osc_1_pulse_width_index",
			"osc_2_wave_interpolate", "osc_2_pulse_width_index", "chorus_rate"]

		for name in contradicted:
			assert tracks.controls[name].default is None, name

		# Everything else that the guide gives a default for has one: only these five, and the
		# eight template macros, which are controller assignments and never had one.
		without = sorted(control.name for control in tracks.controls.values()
			if control.default is None)

		assert without == sorted(contradicted
			+ [f"midi_template_macro_{number}" for number in range(1, 9)])

		# The range is still recorded for all five - it is the default alone that is in doubt.
		assert tracks.controls["osc_1_pulse_width_index"].range == (0, 127)

	def test_the_twelfth_matrix_slot_breaks_the_stride_and_ships_as_printed (self) -> None:
		"""Eleven slots put depth and destination three and four above the first source; one does not."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		odd = []

		for slot in range(1, 13):
			base = tracks.controls[f"mod_matrix_{slot}_source_1"].nrpn
			offsets = [tracks.controls[f"mod_matrix_{slot}_{part}"].nrpn
				for part in ("source_1", "source_2", "depth", "destination")]

			assert base is not None

			if [number - base for number in offsets if number is not None] != [0, 1, 3, 4]:
				odd.append(slot)

		assert odd == [12]

		# As printed: 2:10, 2:11, 2:12, 2:13 where the stride says 2:13 and 2:14 for the last two.
		assert tracks.controls["mod_matrix_12_depth"].nrpn == 268
		assert tracks.controls["mod_matrix_12_destination"].nrpn == 269

	def test_eight_switches_share_one_controller_and_differ_by_value (self) -> None:
		"""NRPN 0:122 is one number carrying eight switches, each in a band of its own."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		shared = sorted(control.name for control in tracks.controls.values()
			if control.nrpn == 122)

		assert len(shared) == 8

		assert tracks.controls["lfo_1_one_shot"].range == (12, 13)
		assert tracks.controls["lfo_1_one_shot"].choices == {"off": 12, "on": 13}

		assert tracks.controls["lfo_2_delay_trigger"].range == (28, 29)
		assert tracks.controls["lfo_2_delay_trigger"].choices == {"off": 28, "on": 29}

		# A two-state control is a switch, which is derived rather than declared.
		assert tracks.controls["lfo_1_key_sync"].kind == pymidiinstrumentdefs.SWITCH

	def test_two_value_lists_under_one_heading_stay_apart (self) -> None:
		"""The Filter Table holds Drive Type and Type, both restarting at zero."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		drive = tracks.controls["drive_type"]
		kind = tracks.controls["type"]

		assert drive.range == (0, 6)
		assert drive.choices["diode"] == 0
		assert drive.choices["rate_reducer"] == 6

		assert kind.range == (0, 5)
		assert kind.choices["low_pass_12db"] == 0
		assert kind.choices["high_pass_24db"] == 5

		# Merged into one list, either would have had two entries numbered 0.
		assert set(drive.choices) & set(kind.choices) == set()

		# The sister table for the distortion differs from Drive Type by one word.
		assert tracks.controls["distortion_type"].choices["rectify"] == 4
		assert "rectifier" not in tracks.controls["distortion_type"].choices

	def test_the_modulation_sources_do_not_fill_their_range (self) -> None:
		"""Ten sources over a stated 0 to 12, with 1, 2 and 3 named nowhere."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		source = tracks.controls["mod_matrix_1_source_1"]

		assert source.range == (0, 12)
		assert len(source.choices) == 10

		assert sorted(source.choices.values()) == [0, 4, 5, 6, 7, 8, 9, 10, 11, 12]

		# Which is why they are choices and not bands: a band would make 1, 2 and 3 "direct".
		assert source.values == {}

		# The destinations do fill theirs.
		destination = tracks.controls["mod_matrix_1_destination"]

		assert destination.range == (0, 17)
		assert sorted(destination.choices.values()) == list(range(18))

	def test_four_parts_and_six_voices_on_each_synth (self) -> None:
		"""Six each rather than six shared, and four drums sharing one channel as one part."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		assert set(tracks.parts) == {"synth", "drums", "midi_track", "project"}

		assert tracks.parts["synth"].count == 2
		assert tracks.parts["synth"].polyphony == 6
		assert tracks.parts["synth"].addressing == "pitches"

		# Not shared, so the instrument carries no single figure.
		assert tracks.voice.polyphony_shared is False
		assert tracks.voice.polyphony is None

		# Four drum tracks on one channel are one part, and a note chooses between them.
		assert tracks.parts["drums"].count == 1
		assert tracks.parts["drums"].addressing == "voices"
		assert tracks.voice.voices == {"drum_1": 60, "drum_2": 62, "drum_3": 64, "drum_4": 65}

		# What reaches a MIDI track is not stated, which is different from nothing reaching it.
		assert tracks.parts["midi_track"].receives is None
		assert tracks.parts["project"].receives == ("controls", "program_change")

	def test_the_misprinted_number_ships_as_printed (self) -> None:
		"""One sidechain parameter is in the wrong NRPN block and the doubt is in the file."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		# 1:69 as printed, where the block it sits in says 2:69 would be 325.
		assert tracks.controls["sidechain_synth_2_depth"].nrpn == 197

		# Its four neighbours are all in the 2:xx block.
		assert tracks.controls["sidechain_synth_2_attack"].nrpn == 322
		assert tracks.controls["sidechain_synth_2_decay"].nrpn == 324

		assert "almost certainly a misprint" in (tracks.source or "").lower() \
			or "ALMOST CERTAINLY A MISPRINT" in (tracks.source or "")

	def test_what_is_left_unrecorded_and_why (self) -> None:
		"""Three fields are absent because 131 pages do not mention what they hold."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		# The word aftertouch appears in neither document.
		assert tracks.voice.aftertouch is None

		# Two engine parameters set a bend depth; no page says a bend message is answered.
		assert tracks.voice.pitch_bend is None
		assert tracks.controls["osc_1_pitchbend"].range == (52, 76)
		assert tracks.controls["osc_1_pitchbend"].default == 76

		# The pads' notes follow the chosen scale, and nothing bounds what arrives.
		assert tracks.voice.note_range is None

		# No implementation chart in either document.
		assert tracks.midi.mode is None

		# "Version 3" numbers both documents and neither names a firmware.
		assert tracks.model.firmware is None

		assert tracks.midi.clock == "both"
		assert tracks.midi.transport == "receives"
		assert tracks.midi.sysex is True
		assert tracks.midi.channels == (1, 16)

	def test_three_sources_and_a_landing_page_that_is_not_the_file_host (self) -> None:
		"""Novation serves its downloads from a different host than the page that lists them."""
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		assert set(tracks.sources) == {"guide", "user_guide", "download_page"}

		for name in ("guide", "user_guide"):
			source = tracks.sources[name]

			assert source.landing is not None
			assert "downloads.novationmusic.com" in source.landing
			assert source.url is not None
			assert "fael-downloads-prod.focusrite.com" in source.url
			assert source.page_offset == 0

		assert tracks.sources["download_page"].paginated is False

		# Both documents call themselves Version 3 and were made two months apart.
		assert tracks.sources["guide"].dated == "2022-10-19"
		assert tracks.sources["user_guide"].dated == "2022-08-25"


class TestDigitoneII:

	"""An Elektron whose sixteen tracks share sixteen voices, where its sibling's do not."""

	def test_sixteen_tracks_sharing_sixteen_voices (self) -> None:
		"""The figure sits on the instrument, which is the opposite of the Digitakt II."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		assert len(digitone.controls) == 164
		assert len(digitone.groups) == 20
		assert set(digitone.parts) == {"track", "fx"}

		assert digitone.parts["track"].count == 16
		assert digitone.parts["track"].addressing == "pitches"

		# A shared pool, so the instrument carries the figure and no part does.
		assert digitone.voice.polyphony == 16
		assert digitone.voice.polyphony_shared is True
		assert digitone.parts["track"].polyphony is None

		# Its sibling is the other way round, and the pair is worth keeping honest.
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		assert digitakt.voice.polyphony_shared is False
		assert digitakt.parts["track"].polyphony == 1

	def test_the_four_syn_pages_are_four_groups (self) -> None:
		"""Each prints the same eight names, so only the caption tells the thirty-two apart."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		pages = [f"syn_page_{number}" for number in range(1, 5)]

		for group in pages:
			knobs = [control for control in digitone.controls.values() if control.group == group]

			assert len(knobs) == 8, group

			# The label is as printed, which is the same eight on every page.
			assert sorted(control.label for control in knobs) == sorted(
				f"Data entry knob {letter} (machine dependent)" for letter in "ABCDEFGH")

		# Thirty-two distinct controls all the same, told apart by their group alone.
		assert digitone.controls["syn_page_1_data_entry_knob_a"].cc == 40
		assert digitone.controls["syn_page_4_data_entry_knob_h"].cc == 77

	def test_eleven_nrpns_mean_two_things_and_both_are_recorded (self) -> None:
		"""A track is an audio track or a MIDI track, so one number reaches two maps."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		# The filter's envelope on an audio track, VAL1 on a MIDI track, one NRPN.
		assert digitone.controls["filter_attack_time"].nrpn == 144
		assert digitone.controls["cc_val_val1"].nrpn == 144

		assert digitone.controls["filter_attack_time"].group == "filter"
		assert digitone.controls["cc_val_val1"].group == "cc_val"

		# Both are on the track part, because both are reached on a track's own channel.
		assert digitone.controls["filter_attack_time"].part == "track"
		assert digitone.controls["cc_val_val1"].part == "track"

		# Sixteen CC VAL controls, one per assignable controller on a MIDI track.
		assert len([c for c in digitone.controls.values() if c.group == "cc_val"]) == 16

	def test_the_euclidean_table_is_captioned_amp_and_grouped_by_its_section (self) -> None:
		"""The caption is the table above it carried down, so the section is what was used."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		assert digitone.groups["euclidean"] == "Euclidean Sequencer"

		euclidean = [c for c in digitone.controls.values() if c.group == "euclidean"]

		assert len(euclidean) == 7

		# Every one is reached by NRPN and by nothing else, which no other group here is.
		assert all(c.cc is None and c.nrpn is not None for c in euclidean)
		assert digitone.controls["euclidean_pulse_generator_1"].nrpn == 392

	def test_the_amp_table_prints_one_controller_twice (self) -> None:
		"""84, 85, 86, 86, 88 - and both rows carry 86, because nothing settles it."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		assert digitone.controls["amp_decay_time"].cc == 86
		assert digitone.controls["amp_sustain_level"].cc == 86

		# Their NRPNs are an unbroken run, which is what makes the CC look like the slip.
		assert digitone.controls["amp_decay_time"].nrpn == 160
		assert digitone.controls["amp_sustain_level"].nrpn == 161

		# And 87 is reached by nothing on this instrument.
		assert 87 not in [c.cc for c in digitone.controls.values()]

	def test_the_external_mixer_keeps_one_name_per_message (self) -> None:
		"""Five rows are a stereo-linked second name for a row already there."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		mixer = [c for c in digitone.controls.values() if c.group == "external_in"]

		assert len(mixer) == 11

		# The mono name is kept; the stereo name is not a control of its own.
		assert digitone.controls["external_in_input_l_level"].cc == 72
		assert "external_in_input_l_r_level" not in digitone.controls

		# The account says why, so a reader meeting the manual is not surprised.
		assert "Input L R Level" in (digitone.source or "")

	def test_two_controls_come_from_the_body_not_the_appendix (self) -> None:
		"""A reader with only the appendix would take CC 1 and CC 2 for unassigned."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		assert digitone.controls["modulation_wheel"].cc == 1
		assert digitone.controls["breath_controller"].cc == 2

		# Neither carries an NRPN, the body giving only a controller number for each.
		assert digitone.controls["modulation_wheel"].nrpn is None
		assert digitone.controls["breath_controller"].nrpn is None

		# The appendix uses neither number for anything else.
		assert [c.name for c in digitone.controls.values() if c.cc == 1] == ["modulation_wheel"]
		assert [c.name for c in digitone.controls.values() if c.cc == 2] == ["breath_controller"]

	def test_the_maker_prefers_nrpn_and_says_so (self) -> None:
		"""Control change cannot reach the high-resolution parameters on this instrument."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		assert digitone.midi.nrpn == "preferred"

		by_nrpn = [c for c in digitone.controls.values() if c.nrpn is not None]
		by_cc = [c for c in digitone.controls.values() if c.cc is not None]

		assert len(by_nrpn) == 160
		assert len(by_cc) == 149

		# Its sibling's appendix gives no such advice and records plain support.
		digitakt = pymidiinstrumentdefs.load("elektron/digitakt_ii", [CORPUS])

		assert digitakt.midi.nrpn == "supported"

	def test_what_is_left_unrecorded_and_why (self) -> None:
		"""Aftertouch reaches it and no page says which kind, so the field stays empty."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		assert digitone.voice.aftertouch is None
		assert digitone.voice.pitch_bend is None

		# What is established is recorded.
		assert digitone.voice.note_range == (0, 84)
		assert digitone.voice.velocity is not None
		assert digitone.voice.velocity.note_on == "received"

		assert digitone.midi.clock == "both"
		assert digitone.midi.transport == "both"
		assert digitone.midi.sysex is True
		assert digitone.midi.channels == (1, 16)

		assert digitone.midi.program_change is not None
		assert digitone.midi.program_change.presets == 128

	def test_three_sources_and_a_release_note_address_that_had_to_be_found (self) -> None:
		"""The sibling's release-notes URL pattern 404s for this product."""
		digitone = pymidiinstrumentdefs.load("elektron/digitone_ii", [CORPUS])

		assert set(digitone.sources) == {"manual", "support_page", "release_notes"}

		assert digitone.sources["manual"].edition == "OS 1.12"
		assert digitone.sources["manual"].page_offset == 0
		assert digitone.model.firmware == "1.12"

		notes = digitone.sources["release_notes"]

		assert notes.url == "https://www.elektron.se/release-notes/digitone-ii"
		assert notes.paginated is False


class TestBlofeld:

	"""A Waldorf whose chart has a row for all 128 controller numbers, and seventeen are not
	controls."""

	def test_the_chart_runs_0_to_127_and_111_of_them_are_controls (self) -> None:
		"""Every row is accounted for: each left out is left out for a reason."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert len(blofeld.controls) == 111
		assert len(blofeld.groups) == 21

		numbers = sorted(control.cc for control in blofeld.controls.values()
			if control.cc is not None)

		assert len(numbers) == 111, "every control here is reached by control change"

		# The twelve the maker marks `- not used -`, the four channel mode messages, and bank
		# select LSB. Nothing else is missing from 0 to 127.
		unused = {0, 3, 6, 8, 9, 11, 63, 119, 124, 125, 126, 127}
		mode = {120, 121, 122, 123}

		assert set(numbers) == set(range(128)) - unused - mode - {32}

	def test_no_channel_mode_message_is_a_control (self) -> None:
		"""CC 120 to 127 belong to the MIDI specification, and the validator refuses them."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		for control in blofeld.controls.values():
			assert control.cc is None or control.cc < 120, control.name

	def test_bank_select_is_left_out_and_its_banks_are_recorded_instead (self) -> None:
		"""The chart's value column for CC 32 is the only place the manual addresses them."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert all(control.cc != 32 for control in blofeld.controls.values())

		# Eight banks of 128, which is what the 1024 counts.
		assert blofeld.midi.program_change is not None
		assert blofeld.midi.program_change.presets == 1024
		assert blofeld.midi.program_change.receives is True

		# Whether it sends one is nowhere recorded, which is not the same as it not doing so.
		assert blofeld.midi.program_change.sends is None

	def test_the_three_oscillator_octaves_step_in_twelves (self) -> None:
		"""`16, 28, 40…112` is nine values and not ninety-seven, and the step is what says so."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		for number, name in ((27, "osc_1_octave"), (35, "osc_2_octave"), (42, "osc_3_octave")):
			octave = blofeld.controls[name]

			assert octave.cc == number
			assert octave.range == (16, 112)
			assert octave.step == 12

			# 128' to 1/2', which is nine octaves.
			assert len(range(octave.range[0], octave.range[1] + 1, octave.step)) == 9

	def test_nrpn_is_impossible_because_its_controllers_are_sound_parameters (self) -> None:
		"""Neither document mentions NRPN, and the chart gives away the numbers it would need."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert blofeld.midi.nrpn == "none"
		assert all(control.nrpn is None for control in blofeld.controls.values())

		# 98 and 99 are the NRPN pair and 100 and 101 the RPN pair, on every other instrument.
		by_number = {control.cc: control for control in blofeld.controls.values()}

		assert by_number[98].label == "FE Decay 2"
		assert by_number[99].label == "FE Sustain 2"
		assert by_number[100].label == "FE Release"
		assert by_number[101].label == "AE Attack"

		# And CC 38, the data entry LSB, is an oscillator's.
		assert by_number[38].label == "Osc 2 FM"

	def test_sixteen_parts_drawing_on_twenty_five_voices (self) -> None:
		"""A ceiling the patch lowers, held once for the instrument rather than per part."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert set(blofeld.parts) == {"part"}
		assert blofeld.parts["part"].count == 16
		assert blofeld.parts["part"].channel == "assigned"
		assert blofeld.parts["part"].receives == ("notes", "controls", "program_change")

		assert blofeld.voice.polyphony == 25
		assert blofeld.voice.polyphony_shared is True
		assert blofeld.parts["part"].polyphony is None

	def test_it_takes_clock_and_never_sends_it_and_has_no_transport (self) -> None:
		"""Internal or Auto is the whole of the choice, and no page names a transport message."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert blofeld.midi.clock == "receives"
		assert blofeld.midi.transport == "none"
		assert blofeld.midi.channels == (1, 16)
		assert blofeld.midi.sysex is True

	def test_velocity_is_received_rather_than_both_because_one_product_has_no_keys (self) -> None:
		"""The definition covers the Desktop and the Keyboard, and only one of them sends."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert blofeld.voice.velocity is not None
		assert blofeld.voice.velocity.note_on == "received"

		# Release velocity is a modulation source a patch can route, which is more than
		# receiving it.
		assert blofeld.voice.velocity.note_off is True

		assert blofeld.voice.aftertouch == "poly"
		assert blofeld.voice.pitch_bend is not None
		assert blofeld.voice.pitch_bend.programmable is True

		# Settable per oscillator, and no page says what any of the three starts at.
		assert blofeld.voice.pitch_bend.semitones is None

	def test_no_asterisk_reaches_a_label (self) -> None:
		"""It is the chart's footnote marker, not a character in the name of anything."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		for control in blofeld.controls.values():
			assert "*" not in control.label, control.name
			assert "*" not in control.name, control.name

		# The six marked ones that are controls here, by the chart's own spelling.
		by_number = {control.cc: control for control in blofeld.controls.values()}
		marked = {1: "Modulation Wheel", 2: "Breath Control", 4: "Foot Control",
			7: "Channel Volume", 10: "Pan", 64: "Sustain Pedal"}

		for number, label in marked.items():
			assert by_number[number].label == label

	def test_no_control_carries_a_default_or_a_state (self) -> None:
		"""The chart gives no defaults, and never says which value selects which state."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		for control in blofeld.controls.values():
			assert control.default is None, control.name
			assert control.values == {}, control.name
			assert control.choices == {}, control.name

	def test_the_manual_is_shared_with_the_keyboard_under_one_link (self) -> None:
		"""Where the Iridium needed two downloads to prove it, this pair needs none."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert set(blofeld.sources) == {"manual", "sysex", "product_page", "keyboard_page"}

		manual = blofeld.sources["manual"]

		assert manual.page_offset == 0
		assert manual.landing == "https://waldorfmusic.com/blofeld-en/"

		# The System Exclusive specification names no controller, so no number rests on it.
		assert blofeld.sources["sysex"].kind == "midi_implementation"

		# Both product pages are unpaginated text, cited by key rather than by page.
		assert blofeld.sources["product_page"].paginated is False
		assert blofeld.sources["keyboard_page"].paginated is False

	def test_the_account_records_what_the_keyboards_own_page_gets_wrong (self) -> None:
		"""A specification repeated between two product pages is one measurement, not two."""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert blofeld.source is not None

		account = " ".join(blofeld.source.split())

		assert "111 of those 128 rows are controls" in account
		assert "System Exclusive specification" in account

		# The two products and the socket that tells them apart are in the file's own comments,
		# which a package reader sees as the definition's header rather than in `source`.
		text = (CORPUS / "waldorf" / "blofeld.yaml").read_text()

		# A comment's own `#` is not part of the prose, and a sentence that runs over two lines
		# would otherwise have one in the middle of it.
		flowed = " ".join(line.lstrip().lstrip("#").strip()
			for line in text.splitlines()).replace("  ", " ")
		flowed = " ".join(flowed.split())

		assert "The Desktop has a MIDI In jack and no MIDI Out (manual p. 8)" in flowed
		assert "its English specification block is the Desktop's word for word" in flowed

	def test_the_note_range_is_left_out_because_the_sentence_is_about_a_filter (self) -> None:
		"""Low Key and High Key bound where a key window may be put, not what the engine sounds.

		The Iridium made this mistake with a split point and a second reader caught it; the
		same maker, the same shape, the same catch. It is recorded as a test so that a later
		reading which puts a range back has to argue with this.
		"""
		blofeld = pymidiinstrumentdefs.load("waldorf/blofeld", [CORPUS])

		assert blofeld.voice.note_range is None

		# With no range recorded, the loader treats every note as playable rather than guessing.
		assert blofeld.voice.plays_note(0) is True
		assert blofeld.voice.plays_note(127) is True


class TestDrumBruteImpact:

	"""An Arturia whose every MIDI number is inside a picture, and only one picture is a
	default."""

	def test_nineteen_notes_for_ten_instruments (self) -> None:
		"""Each has a plain note and a Color note, except the one with no Color effect."""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert len(impact.voice.voices) == 19
		assert impact.voice.addressing == "voices"

		plain = [name for name in impact.voice.voices if not name.startswith("colored_")]
		coloured = [name for name in impact.voice.voices if name.startswith("colored_")]

		assert len(plain) == 10
		assert len(coloured) == 9

		# The ten run unbroken from 36.
		assert sorted(impact.voice.voices[name] for name in plain) == list(range(36, 46))

	def test_every_colour_note_is_twelve_above_its_own (self) -> None:
		"""The relation is what checks a transcription made by eye, and 54 is the one gap."""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		voices = impact.voice.voices

		for name, note in voices.items():
			if name.startswith("colored_"):
				assert note == voices[name[len("colored_"):]] + 12, name

		# The Cowbell has no Color effect, so the one number missing from 48-57 is its.
		assert "colored_cowbell" not in voices
		assert voices["cowbell"] + 12 == 54
		assert 54 not in voices.values()

		coloured = sorted(note for name, note in voices.items() if name.startswith("colored_"))

		assert coloured == [48, 49, 50, 51, 52, 53, 55, 56, 57]

	def test_the_numbers_are_defaults_rather_than_fixed_facts (self) -> None:
		"""They are set in the maker's editor, so a machine in front of you may answer to
		anything."""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert impact.voice.note_map == "learned"

	def test_it_publishes_no_controller_number_at_all (self) -> None:
		"""Two things answer to control change and the player chooses both numbers."""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert impact.controls == {}
		assert impact.midi.control_change == "learned"
		assert impact.midi.nrpn == "none"

	def test_the_channel_range_is_not_recorded_because_it_is_never_stated (self) -> None:
		"""It exists only in a screenshot, and a screenshot of an editor is not a statement.

		This is the one that would be easiest to get wrong: 1 to 16 is what almost every
		instrument takes, and this manual never says so.
		"""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert impact.midi.channels is None

	def test_it_sends_transport_and_nothing_says_it_receives_any (self) -> None:
		"""The manual says 'receives' where it means it, and for transport it never does."""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert impact.midi.clock == "both"
		assert impact.midi.transport == "sends"

	def test_what_is_left_unset_is_left_unset (self) -> None:
		"""Program change and system exclusive are unestablished, which is not the same as
		absent.

		Something very like system exclusive exists - the editor reads the machine's settings
		over USB - and no document names its message type, so `sysex` says nothing rather
		than claiming false.
		"""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert impact.midi.sysex is None
		assert impact.midi.program_change is None

		# Nor is there a voice count: ten instruments are not ten voices, because the two
		# hats are one circuit.
		assert impact.voice.polyphony is None
		assert impact.voice.aftertouch is None
		assert impact.voice.pitch_bend is None

	def test_velocity_is_received_and_works_as_a_threshold (self) -> None:
		"""A note is accented or it is not, by one figure shared across all ten instruments."""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert impact.voice.velocity is not None
		assert impact.voice.velocity.note_on == "received"

		# Whether velocity leaves the instrument is nowhere stated.
		assert impact.voice.velocity.note_off is None

	def test_the_editors_manual_is_cited_for_an_absence (self) -> None:
		"""So that 'no document states them' is evidenced rather than asserted."""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert set(impact.sources) == {"manual", "release_notes", "mcc_manual", "resources_page"}

		# The largest page offset in the bundled set, and the reason front matter fills it.
		assert impact.sources["manual"].page_offset == 5
		assert impact.sources["mcc_manual"].page_offset == 0

		assert impact.sources["release_notes"].paginated is False
		assert impact.sources["resources_page"].paginated is False

	def test_the_account_records_the_values_the_format_cannot_hold (self) -> None:
		"""The touch strip's number is the player's and its values are the maker's."""
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert impact.source is not None

		account = " ".join(impact.source.split())

		assert "the MIDI CC values sent and recognized by the Touch strip are fixed" in account
		assert "1/32 sends 100 and answers to 100-127" in account

		# And that there is no chart at all, which is the fact rather than an omission.
		assert "THERE IS NO MIDI IMPLEMENTATION CHART AND NO CONTROLLER MAP" in account


class TestEP133KOII:

	"""A teenage engineering sampler whose chart says yes with a picture and no with a letter."""

	def test_four_controllers_and_the_guide_says_that_is_all (self) -> None:
		"""And the implementation chart adds two the list omits, which are not controls."""
		ep = pymidiinstrumentdefs.load("teenage_engineering/ep_133_ko_ii", [CORPUS])

		assert len(ep.controls) == 4
		assert sorted(control.cc for control in ep.controls.values()
			if control.cc is not None) == [1, 12, 13, 64]

		# Bank select is program change's business, not a control's - the Moog 37s' reading.
		assert all(control.cc not in (0, 32) for control in ep.controls.values())

		assert ep.midi.program_change is not None
		assert ep.midi.program_change.presets == 999

	def test_every_range_is_printed_one_to_127 (self) -> None:
		"""Recorded as printed, and doubted in the account rather than corrected."""
		ep = pymidiinstrumentdefs.load("teenage_engineering/ep_133_ko_ii", [CORPUS])

		for control in ep.controls.values():
			assert control.range == (1, 127), control.name

	def test_forty_eight_pads_on_four_groups_in_keypad_order (self) -> None:
		"""The lowest note of a group is the dot pad, and pad 1 is the fourth note."""
		ep = pymidiinstrumentdefs.load("teenage_engineering/ep_133_ko_ii", [CORPUS])

		voices = ep.voice.voices

		assert len(voices) == 48
		assert sorted(voices.values()) == list(range(36, 84))

		for index, group in enumerate("abcd"):
			pads = {name: note for name, note in voices.items() if name.startswith(f"{group}_")}

			assert len(pads) == 12, group
			assert sorted(pads.values()) == list(range(36 + index * 12, 48 + index * 12))

		# The keypad's own order, which is the trap: note 36 is the dot, not pad 1.
		assert voices["a_dot"] == 36
		assert voices["a_0"] == 37
		assert voices["a_enter"] == 38
		assert voices["a_1"] == 39

	def test_keys_mode_is_why_the_note_range_is_the_whole_of_it (self) -> None:
		"""Forty-eight pads ordinarily, and 0 to 127 chromatically for one chosen sound."""
		ep = pymidiinstrumentdefs.load("teenage_engineering/ep_133_ko_ii", [CORPUS])

		assert ep.voice.addressing == "voices"
		assert ep.voice.note_range == (0, 127)

		# Both of those are true at once, so a consumer must not read the voices as the limit.
		assert ep.voice.plays_note(0) is True
		assert ep.voice.plays_note(127) is True

	def test_the_first_definition_here_to_record_omni_on (self) -> None:
		"""Mode 1 with basic channel 1 is exactly the settings list's own code 110."""
		ep = pymidiinstrumentdefs.load("teenage_engineering/ep_133_ko_ii", [CORPUS])

		assert ep.midi.mode == 1
		assert ep.midi.channels == (1, 16)

		# Every other definition that records a mode records omni off.
		others = [pymidiinstrumentdefs.load(name, [CORPUS]).midi.mode
			for name in pymidiinstrumentdefs.available([CORPUS])
			if name != "teenage_engineering/ep_133_ko_ii"]

		assert 1 not in [mode for mode in others if mode is not None]

	def test_what_the_chart_marks_and_what_it_refuses_to (self) -> None:
		"""Aftertouch is a printed no; the true voice row is a dash, so no voice count."""
		ep = pymidiinstrumentdefs.load("teenage_engineering/ep_133_ko_ii", [CORPUS])

		assert ep.voice.aftertouch == "none"
		assert ep.voice.polyphony is None

		assert ep.midi.clock == "both"
		assert ep.midi.transport == "both"
		assert ep.midi.sysex is True
		assert ep.midi.nrpn == "none"

		assert ep.voice.velocity is not None
		assert ep.voice.velocity.note_on == "both"
		assert ep.voice.velocity.note_off is False

		# Received and not sent, which the format's pitch bend field cannot say - so it says
		# nothing rather than something wrong.
		assert ep.voice.pitch_bend is None

	def test_the_account_records_what_only_a_picture_says (self) -> None:
		"""A text reading of this chart loses every yes, and the file says so."""
		ep = pymidiinstrumentdefs.load("teenage_engineering/ep_133_ko_ii", [CORPUS])

		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "teenage_engineering" / "ep_133_ko_ii.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "THE AFFIRMATIVE MARK IN THIS INSTRUMENT'S MIDI CHART IS A PICTURE" in flowed
		assert "AND THE TABLES ARE NOT TABLES" in flowed

		assert ep.source is not None

		account = " ".join(ep.source.split())

		assert "14.5's claim to be a complete list is false by two" in account
		assert "THE GUIDE HAS NO CHAPTER 13" in account

	def test_its_sources_are_four_pages_of_one_web_guide (self) -> None:
		"""Published as a site rather than a document, so every source is unpaginated."""
		ep = pymidiinstrumentdefs.load("teenage_engineering/ep_133_ko_ii", [CORPUS])

		assert set(ep.sources) == {"system", "modes", "how_to", "downloads_page"}

		for name, source in ep.sources.items():
			assert source.paginated is False, name

		# The guide names no operating system; only the downloads page does.
		assert ep.model.firmware == "2.5"
		assert ep.sources["downloads_page"].kind == "download_page"


class TestDeluge:

	"""A Synthstrom whose maker reprinted somebody else's guide as its own last chapter."""

	def test_it_publishes_no_controller_and_no_note_number (self) -> None:
		"""Both directions are the player's to assign, which the chart says in as many words."""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.controls == {}
		assert deluge.midi.control_change == "learned"
		assert deluge.voice.note_map == "learned"
		assert deluge.voice.voices == {}

		# Pitches rather than voices: a synth clip is played across the grid by pitch, and a
		# kit's rows are learned one at a time rather than mapped from the factory.
		assert deluge.voice.addressing == "pitches"

	def test_it_sends_program_change_and_does_not_answer_one (self) -> None:
		"""The one row where this machine is plainly a sequencer rather than an instrument.

		Both bank select rows are the same way round, and a reading that took the chart's
		words in stream order would have had this backwards.
		"""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.midi.program_change is not None
		assert deluge.midi.program_change.sends is True
		assert deluge.midi.program_change.receives is False

		# 1-128 is the range of numbers it can be told to send at somebody else's synth, not a
		# count of its own presets, which are files on a card and are not addressed by number.
		assert deluge.midi.program_change.presets is None

	def test_release_velocity_is_left_unrecorded_because_the_guidebook_says_both (self) -> None:
		"""The chart says no and the chapter around it says yes, so neither is recorded.

		This is the field most likely to be filled in later by somebody who read only one of
		the two pages, so the absence is held in place by a test.
		"""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.voice.velocity is not None
		assert deluge.voice.velocity.note_on == "both"
		assert deluge.voice.velocity.note_off is None

	def test_the_chart_row_about_note_off_is_about_velocity (self) -> None:
		"""It is not a claim that the instrument fails to send note offs.

		A MIDI implementation chart's `Note off` row under a `Velocity` group is about release
		velocity, and the format agrees: `note_off` is a field of `Velocity` and not of
		`Voice`. Reading it the other way would make a sequencer that drives sixteen channels
		look like one that leaves every note hanging.
		"""
		velocity = pymidiinstrumentdefs.definition.Velocity

		assert "note_off" in velocity.__dataclass_fields__
		assert not hasattr(pymidiinstrumentdefs.definition.Voice, "note_off")

	def test_what_notes_it_sounds_is_not_recorded (self) -> None:
		"""Two printings of `0-127` are in the guidebook and neither is about the engine.

		One is a controller's value range and the other is the note number a kit row can be
		set to send. That is the Blofeld's trap in a third document.
		"""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.voice.note_range is None

	def test_polyphony_is_not_recorded_because_two_ceilings_are_published (self) -> None:
		"""64 synth voices and 90 sample voices, both CPU-bound, and one field."""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.voice.polyphony is None
		assert deluge.voice.voicing_modes == ()

	def test_it_takes_both_kinds_of_pressure_and_expression_per_channel (self) -> None:
		"""MPE in and out, with the zones MIDI's own and the dimensions patched rather than
		fixed."""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.voice.aftertouch == "poly"
		assert deluge.midi.per_voice_channels is True

		# Y is not CC 74 here: the guidebook patches it like any modulation source and names no
		# controller number for it, so none is invented.
		assert deluge.controls == {}

	def test_the_bend_range_recorded_is_the_global_default (self) -> None:
		"""Three bend ranges exist and this field holds the one a wheel gets."""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.voice.pitch_bend is not None
		assert deluge.voice.pitch_bend.semitones == 12
		assert deluge.voice.pitch_bend.programmable is True

	def test_the_abridged_chart_s_silences_are_not_recorded_as_noes (self) -> None:
		"""It prints no Basic Channel row, no Mode row and no NRPN row, so none is guessed at.

		System exclusive is different: the chart does print that row, and says no in both
		columns, so `false` is a reading rather than a silence.
		"""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.midi.mode is None
		assert deluge.midi.nrpn is None
		assert deluge.midi.sysex is False

	def test_it_answers_on_all_sixteen_and_follows_or_leads (self) -> None:
		"""Stated going both ways, unlike the DrumBrute Impact's unstated channel range."""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.midi.channels == (1, 16)
		assert deluge.midi.clock == "both"
		assert deluge.midi.transport == "both"

	def test_both_guidebooks_are_sources_and_the_community_guide_is_cited_not_read (self) -> None:
		"""The maker publishes one guidebook per display, and both were read and compared."""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert set(deluge.sources) == {
			"guidebook_oled", "guidebook_numeric", "community_guide",
			"product_page", "manual_page", "open_source_page", "news_page", "release_notes"}

		# Two editions of one book, same length, same offset, four months apart.
		for name in ("guidebook_oled", "guidebook_numeric"):
			assert deluge.sources[name].kind == "manual", name
			assert deluge.sources[name].page_offset == 6, name

		assert deluge.sources["guidebook_oled"].edition == "4.1.0"
		assert deluge.sources["guidebook_numeric"].edition == "4.0"

		# The firmware named is the guidebook's, not the newest build, because no document
		# covers the three releases in between.
		assert deluge.model.firmware == "4.1.0"

	def test_the_source_records_what_chapter_fifteen_turned_out_to_be (self) -> None:
		"""The finding that makes this instrument worth its space, held in place by a test."""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.source is not None

		account = " ".join(deluge.source.split())

		assert "THE OFFICIAL GUIDEBOOK'S LAST CHAPTER IS THE USER-WRITTEN COMMUNITY GUIDE" \
			in account
		assert "the one page that says who wrote it is the one page that did not survive" \
			in account

		# And that no number was taken from it.
		assert "No number in this file comes from printed pages 295 to 322" in account

		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "synthstrom_audible" / "deluge.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "THIS INSTRUMENT PUBLISHES NO CONTROLLER NUMBER AND NO NOTE NUMBER, BY DESIGN" \
			in flowed
		assert "ITS MAKER HAS BOUND SOMEBODY ELSE'S DOCUMENT INTO ITS OWN" in flowed

	def test_the_source_records_that_the_two_editions_were_compared (self) -> None:
		"""Agreement between editions is a measurement, so it is written down as one."""
		deluge = pymidiinstrumentdefs.load("synthstrom_audible/deluge", [CORPUS])

		assert deluge.source is not None

		account = " ".join(deluge.source.split())

		assert "identical, row for row, all 24 rows in all 9 groups" in account
		assert "THE SECOND READING FOUND A CELL THE FIRST HAD WRONG" in account
		assert "312 of them print a folio and all 312 are out by exactly six" in account


class TestTyphon:

	"""A Dreadbox whose controller list is the only place its numbers exist, in three columns."""

	def test_ninety_eight_controllers_in_fourteen_groups (self) -> None:
		"""One list, two pages, and every number in it accounted for."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert len(typhon.controls) == 98

		numbers = sorted(control.cc for control in typhon.controls.values()
			if control.cc is not None)

		assert len(numbers) == 98
		assert numbers[0] == 1
		assert numbers[-1] == 102

		groups = {control.group for control in typhon.controls.values() if control.group}

		assert len(groups) == 14

	def test_the_three_modulator_blocks_are_the_same_size (self) -> None:
		"""The relation that checks a three-column transcription better than a second look.

		The modulators carry identical parameters, so each owns a block of the same length -
		and a label sitting one row out cannot leave three equal blocks behind.
		"""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		for name in ("M1", "M2", "M3"):
			block = sorted(control.cc for control in typhon.controls.values()
				if control.label is not None and control.label.startswith(f"{name} ")
				and control.cc is not None)

			assert len(block) == 17, name

		# And each later block is pushed outwards by exactly the numbers MIDI had already
		# claimed: 32 is Bank Select LSB and 64 is the damper pedal.
		blocks = {}

		for name in ("M1", "M2", "M3"):
			block = sorted(control.cc for control in typhon.controls.values()
				if control.label is not None and control.label.startswith(f"{name} ")
				and control.cc is not None)
			blocks[name] = set(range(block[0], block[-1] + 1)) - set(block)

		assert blocks["M1"] == set()
		assert blocks["M2"] == {32}
		assert blocks["M3"] == {64}

	def test_nine_numbers_carry_the_meaning_midi_gives_them (self) -> None:
		"""The same check from the other direction, and a guard against a shifted reading."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		by_number = {control.cc: control.label for control in typhon.controls.values()}

		assert by_number[1] == "MOD WHEEL"            # MIDI's modulation wheel
		assert by_number[2] == "CC2"                  # MIDI's breath controller
		assert by_number[5] == "GLIDE"                # MIDI's portamento time
		assert by_number[7] == "PRESET VOLUME"        # MIDI's channel volume
		assert by_number[64] == "SUSTAIN PEDAL"       # MIDI's damper pedal
		assert by_number[72] == "VCA EG RELEASE"      # MIDI's release time
		assert by_number[73] == "VCA EG ATTACK"       # MIDI's attack time
		assert by_number[74] == "CUTOFF"              # MIDI's brightness

		# And one the maker almost certainly mislabelled, carried as printed: 71 is MIDI's
		# resonance and this instrument's panel calls the same thing a filter control.
		assert by_number[71] == "VCO RESONANCE"

	def test_the_gaps_in_the_list_are_what_the_manual_prints (self) -> None:
		"""Three of the four below 103 are numbers MIDI reserves; the fourth is unexplained."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		numbers = {control.cc for control in typhon.controls.values()}
		missing = sorted(set(range(1, 103)) - numbers)

		# 32 is Bank Select LSB, 66 is sostenuto, 69 is hold 2. MIDI leaves 3 undefined and so
		# does this manual.
		assert missing == [3, 32, 66, 69]

		# Nothing between 103 and 119 is in the list, and the manual does not mark those
		# absences at all - it simply jumps from 103 to 120.
		assert not numbers & set(range(103, 120))

	def test_the_channel_mode_messages_the_list_prints_are_not_controls (self) -> None:
		"""The list carries 120 and 123; the corpus refuses 120-127 as controls."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		numbers = {control.cc for control in typhon.controls.values()}

		assert not numbers & set(range(120, 128))

	def test_what_notes_it_sounds_is_not_recorded (self) -> None:
		"""It is stated in note names, and the manual uses two octave conventions.

		"A0 to C8" is the idiom for an 88-key piano's compass, which is notes 21 to 108; four
		lines above, the same paragraph calls middle C "C3", which puts the same two names at
		33 and 120. Twelve semitones apart, and the document supports both.
		"""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert typhon.voice.note_range is None

		# So every note is playable as far as this definition is concerned, which is the
		# loader's honest default rather than a claim.
		assert typhon.voice.plays_note(0)
		assert typhon.voice.plays_note(127)

	def test_three_more_fields_are_left_unset_and_each_for_its_own_reason (self) -> None:
		"""Polyphony is never stated, the aftertouch kind is never stated, and the bend
		default is never printed."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		# Two controls imply one voice - GLIDE MODE and LEGATO - and implication is not a
		# statement.
		assert typhon.voice.polyphony is None

		# MIDI has two aftertouch messages and no page of 24 says which this one answers to.
		assert typhon.voice.aftertouch is None

		# Settable 1 to 12, with none of the twelve marked as the one it arrives with.
		assert typhon.voice.pitch_bend is not None
		assert typhon.voice.pitch_bend.programmable is True
		assert typhon.voice.pitch_bend.semitones is None

	def test_velocity_arrives_and_does_nothing_until_it_is_routed (self) -> None:
		"""The Minitaur's case: a velocity lane can look dead on a correctly wired machine."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert typhon.voice.velocity is not None
		assert typhon.voice.velocity.note_on == "gated"

		# The gate is a menu setting rather than a control with a number, so there is nothing
		# for `gated_by` to name.
		assert typhon.voice.velocity.gated_by == ()

	def test_it_receives_transport_and_is_not_said_to_send_it (self) -> None:
		"""Clock has a Transmit switch in the menu and transport has none."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert typhon.midi.channels == (1, 16)
		assert typhon.midi.clock == "both"
		assert typhon.midi.transport == "receives"

	def test_it_changes_preset_both_ways_across_two_hundred_and_fifty_six (self) -> None:
		"""Stated three times, in two documents, and the three agree."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert typhon.midi.program_change is not None
		assert typhon.midi.program_change.receives is True
		assert typhon.midi.program_change.sends is True
		assert typhon.midi.program_change.presets == 256

	def test_a_published_map_leaves_control_change_unset (self) -> None:
		"""`learned` and `none` are for instruments without a map; this one has one.

		System exclusive is unset for the DrumBrute Impact's reason - a preset manager exists
		and no document names the message type it uses - and NRPN because the word appears
		nowhere in the manual.
		"""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert typhon.midi.control_change is None
		assert typhon.midi.sysex is None
		assert typhon.midi.nrpn is None
		assert typhon.midi.mode is None

	def test_its_sources_are_the_manual_and_three_pages (self) -> None:
		"""The manual is the whole of the map; the pages settle an absence and a firmware."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert set(typhon.sources) == {"manual", "release_notes", "support_page", "product_page"}
		assert typhon.sources["manual"].page_offset == 0
		assert typhon.sources["manual"].edition == "4.2"

		# The firmware named is the manual's, and the one release since it changed no number.
		assert typhon.model.firmware == "4.2"
		assert typhon.sources["release_notes"].edition == "4.2.1"

	def test_the_source_records_the_lookalike_chart_and_the_arithmetic (self) -> None:
		"""Two things a later reading must not undo."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert typhon.source is not None

		account = " ".join(typhon.source.split())

		assert "THERE IS NO MIDI IMPLEMENTATION CHART IN THE CONVENTIONAL SENSE" in account
		assert "17 numbers each" in account
		assert "WHAT NOTES IT SOUNDS IS STATED AND STILL NOT RECORDED" in account

		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "dreadbox" / "typhon.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "The Artemis's list must never be attributed to this instrument" in flowed
		assert "AND THE LIST IS SET IN THREE COLUMNS, SO A TEXT READING INTERLEAVES IT" in flowed


class TestTD3:

	"""A TB-303 recreation whose maker publishes a complete message table with no controller in it."""

	def test_no_controls_and_the_absence_is_a_checked_one (self) -> None:
		"""The distinction the whole format turns on, in its plainest form.

		Eleven knobs and twenty-eight switches, none of them addressable - and the
		file says so rather than saying nothing, because the maker's own MIDI message
		table enumerates what the instrument answers to and no controller is in it.
		"""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert len(td3.controls) == 0
		assert td3.midi.control_change == "none"
		assert td3.midi.refuses_control_change is True
		assert td3.midi.learns_control_change is False

		# And not the other kind of empty: this instrument has MIDI, unlike the DFAM.
		assert td3.midi.stated_none is False

	def test_everything_absent_rests_on_one_table_and_the_file_says_so (self) -> None:
		"""Three negatives from one reading, argued once instead of three times.

		The table lists `8n`, `9n`, `Bn 7B` and `En` under Channel Message, so program
		change and both kinds of aftertouch are missing from an enumeration that is
		otherwise complete.  A reader who disagrees with that reading knows from the
		file exactly which three conclusions to revisit.
		"""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert td3.midi.control_change == "none"
		assert td3.midi.program_change is not None
		assert td3.midi.program_change.receives is False
		assert td3.voice is not None
		assert td3.voice.aftertouch == "none"

		assert td3.source is not None

		account = " ".join(td3.source.split())

		assert "Everything recorded below as absent rests on that one" in account

	def test_clock_and_transport_are_received_and_not_claimed_to_be_sent (self) -> None:
		"""Because the specifications give the DIN socket as In and Thru only."""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert td3.midi.clock == "receives"
		assert td3.midi.transport == "receives"

	def test_monophonic_and_the_sixteen_voices_are_a_rig_not_an_instrument (self) -> None:
		"""Poly Chain combines units, which is a fact about several TD-3s and not about one."""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert td3.voice is not None
		assert td3.voice.polyphony == 1
		assert td3.voice.polyphony_shared is None

	def test_the_guide_prints_two_pages_to_a_sheet (self) -> None:
		"""So a citation to a printed page is half of a page of the file.

		Both guides are laid out this way, and getting it wrong would put every
		quotation on the wrong page - which is why the quotation gate is the check
		that matters here and this one only pins the arithmetic.
		"""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		guide = td3.sources["guide"]

		assert guide.pages_per_sheet == 2
		assert guide.page_offset == 1
		assert guide.file_page(94) == 48
		assert guide.file_page(95) == 48
		assert guide.file_page(103) == 52
		assert guide.file_page(1) == 1

		assert td3.sources["mo_guide"].pages_per_sheet == 2

	def test_the_firmware_is_not_recorded_and_the_file_says_why (self) -> None:
		"""An application's version is not an instrument's, and three pages give three."""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert td3.model.firmware is None

		# The guide's own V 5.0 is the document's edition, which is recorded where it
		# belongs rather than being mistaken for the instrument's.
		assert td3.sources["guide"].edition == "V 5.0"
		assert td3.sources["mo_guide"].edition == "V 3.0"

	def test_the_file_says_the_modded_out_sibling_is_not_this_instrument (self) -> None:
		"""One extra row in the same table, so one definition cannot serve both."""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert "mo_guide" in td3.sources

		assert td3.source is not None

		account = " ".join(td3.source.split())

		assert "THE TD-3-MO IS NOT THIS INSTRUMENT" in account
		assert "`Bn 4A xx` Filter Cutoff" in account

		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "behringer" / "td_3.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "ITS SIBLING IS A DIFFERENT INSTRUMENT AND DIFFERS BY EXACTLY ONE ROW" in flowed

	def test_nothing_is_claimed_about_what_leaves_the_din_socket (self) -> None:
		"""One document, two statements, and they contradict each other - so record neither."""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert td3.source is not None

		account = " ".join(td3.source.split())

		assert "ONE THING THIS DOCUMENT SAYS TWICE AND CONTRADICTS ITSELF ABOUT" in account
		assert "nothing below claims anything about what leaves the DIN socket" in account

	def test_sysex_is_unrecorded_rather_than_denied (self) -> None:
		"""The maker's own application configures it, so `false` would be the wrong answer."""
		td3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert td3.midi.sysex is None

		# And the channel, for a different reason the file gives in full.
		assert td3.midi.channels is None


class TestAnalogFour:

	"""An Elektron whose maker publishes the same appendix three times, in two typesettings."""

	def test_two_hundred_and_twenty_nine_controls_in_twenty_seven_groups (self) -> None:
		"""Every named row of a 255-row appendix, in one group per table that named it."""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		assert len(four.controls) == 229
		assert len(four.groups) == 27

		groups = {control.group for control in four.controls.values() if control.group}

		assert groups == set(four.groups)

	def test_every_control_is_addressable_one_way_or_the_other (self) -> None:
		"""The point of carrying a row at all, and the shape of this instrument's asymmetry.

		157 parameters have an NRPN address and no controller number and four have a
		controller number and no NRPN, so neither field alone would reach the
		instrument, and a reading that lost one column would leave controls with
		nothing behind them.

		The four divide two ways, which the appendix says by printing a dash in one
		case and leaving the cell empty in the other: Modwheel and Breath Controller
		have no NRPN, and the two PWM Speeds have an NRPN bank with no number under it.
		"""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		for name, control in four.controls.items():
			assert control.cc is not None or control.nrpn is not None, name

		with_cc = {name for name, control in four.controls.items() if control.cc is not None}
		with_nrpn = {name for name, control in four.controls.items() if control.nrpn is not None}

		assert len(with_cc) == 72
		assert len(with_nrpn) == 225
		assert len(with_cc & with_nrpn) == 68
		assert len(with_nrpn - with_cc) == 157
		assert with_cc - with_nrpn == {
			"modwheel", "breath_controller", "osc1_pwm_speed", "osc2_pwm_speed"}

	def test_the_nrpn_bank_is_the_part (self) -> None:
		"""The relation that makes this instrument unambiguous where its siblings are not.

		The appendix puts each section in a bank of its own - 0 for the performance
		macros, 1 for the synth tracks, 2 for the FX track, 3 for the CV track - so a
		sender using NRPN needs no part to know what a number does.  A row filed under
		the wrong table would show up here as a bank that does not match its part.
		"""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		banks = {"performance": 0, "track": 1, "fx": 2, "cv": 3}

		for name, control in four.controls.items():

			if control.nrpn is None:
				continue

			assert control.part is not None, name
			assert control.nrpn // 128 == banks[control.part], name

	def test_only_one_controller_number_is_printed_twice_and_it_agrees_with_itself (self) -> None:
		"""Unlike the Rytm's 26 and the Syntakt's 28, nothing here needs a part to disambiguate.

		The appendix prints Track Level in two tables with the same numbers, so the
		duplicate is dropped and every controller number below means one thing.
		"""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		numbers = [control.cc for control in four.controls.values() if control.cc is not None]

		assert len(numbers) == len(set(numbers))

		# And the row that was printed twice is carried once, with the numbers both
		# printings gave it: CC 95, NRPN 1/100.
		assert four.controls["track_level"].cc == 95
		assert four.controls["track_level"].nrpn == 1 * 128 + 100

	def test_the_fourteen_fine_pairs_use_the_mma_offset (self) -> None:
		"""Which this maker does not do on the Rytm, where the fine half of 109 is 118."""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		fine = {name: (control.cc, control.lsb) for name, control in four.controls.items()
			if control.lsb is not None}

		assert len(fine) == 14

		for name, (coarse, lsb) in fine.items():
			assert coarse is not None, name
			assert lsb == coarse + 32, name

	def test_pan_is_spelt_without_the_space_its_text_layer_puts_in_it (self) -> None:
		"""The one thing the two readings disagreed about, and the maker's page settled it."""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		assert four.controls["pan"].label == "Pan"

		labels = [control.label for control in four.controls.values() if control.label]

		for label in labels:
			assert not any(len(word) == 1 and word.isalpha() and word.islower()
				for word in label.split()), label

	def test_four_voices_shared_by_four_tracks (self) -> None:
		"""A ceiling across the tracks together, not a figure each track can count on."""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		assert four.voice is not None
		assert four.voice.polyphony == 4
		assert four.voice.polyphony_shared is True
		assert four.parts["track"].count == 4

		# No part claims voices of its own, because none owns any.
		for part in four.parts.values():
			assert part.polyphony is None

	def test_the_performance_channel_says_nothing_about_what_it_receives (self) -> None:
		"""Unrecorded is not empty, and this is the instrument that shows the difference.

		The manual names the performance channel's sending and names notes arriving on
		it for the multi map, and never says whether the ten macros can be driven on it.
		So the field is absent: naming either notes or controls would claim more than any
		sentence does, and naming one would deny the other.
		"""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		assert four.parts["performance"].receives is None
		assert four.parts["track"].receives == ("notes", "controls")
		assert four.parts["fx"].receives == ("controls",)
		assert four.parts["cv"].receives == ("controls",)

	def test_three_manuals_are_cited_and_one_of_them_is_a_different_product (self) -> None:
		"""The comparison this definition rests on is in the file, not only in a note."""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		assert set(four.sources) == {"manual", "release_notes", "mkii_manual", "keys_manual"}

		assert four.sources["manual"].sha256 != four.sources["mkii_manual"].sha256
		assert four.sources["manual"].edition == four.sources["keys_manual"].edition
		assert four.sources["manual"].dated == four.sources["keys_manual"].dated

		# One page of release notes serves both products, so it is not paginated and the
		# whole of it was read.
		assert four.sources["release_notes"].paginated is False

	def test_the_source_account_records_what_was_not_carried (self) -> None:
		"""26 rows left out, and the reason for each, because an absence has to be evidenced."""
		four = pymidiinstrumentdefs.load("elektron/analog_four", [CORPUS])

		assert four.source is not None

		account = " ".join(four.source.split())

		assert "THE APPENDIX PRINTS 255 ROWS IN 28 TABLES AND 229 ARE BELOW" in account
		assert "THE 26 ROWS NOT CARRIED ARE ROWS THE APPENDIX DOES NOT NAME" in account
		assert "the DELAY's knob C at NRPN 2/52" in account
		assert "EVERY NUMBER WAS READ TWICE, BY TWO METHODS" in account
		assert "SEVERAL RUNS OF NRPN NUMBERS SKIP VALUES" in account
		assert "THE FOUR WITH NO NRPN ARE TWO DIFFERENT FACTS" in account

	def test_the_file_says_the_keys_is_not_covered_by_it (self) -> None:
		"""A cover that names three products is not a definition for three products."""
		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "elektron" / "analog_four.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "THE ANALOG KEYS IS NOT COVERED BY THIS FILE" in flowed
		assert "a version number on a cover is not evidence that two documents were" in flowed
		assert "WHAT IS BELOW IS TRUE OF THE ANALOG FOUR MKII AS WELL" in flowed


class TestDeclaringAPicturedPage:

	"""A source can say which of its pages publish their numbers only as an image."""

	def test_only_the_drumbrute_impact_declares_one (self) -> None:
		"""It is the only instrument here whose numbers are published as a picture.

		Listed by name so that a second one has to be added here deliberately: the
		declaration switches off the strongest check this corpus has, for the pages it
		names, so it should never spread quietly.
		"""
		declared = {
			name: {key: source.pictured_pages
				for key, source in pymidiinstrumentdefs.load(name, [CORPUS]).sources.items()
				if source.pictured_pages}
			for name in pymidiinstrumentdefs.available([CORPUS])
		}

		assert {name: pages for name, pages in declared.items() if pages} == {
			"arturia/drumbrute_impact": {"manual": (99,)},
		}

	def test_a_page_declared_twice_is_refused (self) -> None:
		"""A page named twice is a typo rather than an emphasis."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(
				"definition: 1\nmodel: {name: X}\n"
				"sources: {m: {page_offset: 0, pictured_pages: [99, 99]}}",
				source = "x.yaml",
			)

		assert "more than once" in str(raised.value)

	def test_a_pictured_page_on_a_document_with_no_pages_is_refused (self) -> None:
		"""A printed page number is a claim about a document somebody can turn to."""
		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(
				"definition: 1\nmodel: {name: X}\n"
				"sources: {m: {paginated: false, pictured_pages: [99]}}",
				source = "x.yaml",
			)

		assert "says it has none" in str(raised.value)

	def test_declaring_nothing_is_the_default_and_changes_nothing (self) -> None:
		"""Every other definition reads exactly as it did before the field existed."""
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		assert typhon.sources["manual"].pictured_pages == ()
