"""Tests for pymidiinstrumentdefs — reading what a particular model does."""

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

	def test_the_bundled_names (self) -> None:
		"""Every bundled definition, by name, so adding or removing one shows here too."""
		assert pymidiinstrumentdefs.available([CORPUS]) == [
			"behringer/model_d",
			"modal/carbon8m",
			"moog/dfam",
			"moog/labyrinth",
			"moog/matriarch",
			"moog/minitaur",
			"moog/subharmonicon",
			"pwm/malevolent",
			"roland/tr8s",
			"sequential/take_5",
			"soma/pulsar_23",
			"vermona/drm1_mkiv",
			"voce/electric_piano",
			"waldorf/streichfett",
		]

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

	def test_every_bundled_definition_cites_pages (self) -> None:
		"""The README promises each one names its document and its pages.

		"The manual" cannot be checked by anybody; "p.13" can. This keeps that
		promise true as the corpus grows, since a source line is the one part of
		a definition nothing else can verify for you. The document is usually a
		user manual, and for one instrument a quick-start guide is all there is.
		"""
		document = re.compile(r"\b(manual|guide|chart|addendum)\b", re.I)
		cites = re.compile(r"\bpp?\.\s*\d|\b\d+\s*pages?\b|\bevery page\b", re.I)

		for path in bundled():
			definition = pymidiinstrumentdefs.load_file(path)
			source = definition.source or ""

			assert document.search(source), f"{path.name} does not name a document"
			assert cites.search(source), f"{path.name} names no page: {source[:80]!r}"

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
		"""The Matriarch's own manual table, read back."""
		matriarch = pymidiinstrumentdefs.load("moog/matriarch", [CORPUS])

		assert len(matriarch.controls) == 36
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

		assert part.receives == ()
		assert part.takes("notes") is False

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


class TestGrouping:

	def test_controls_collect_by_group_in_file_order (self) -> None:
		"""A flat list of forty controls is unreadable before it is unusable."""
		matriarch = pymidiinstrumentdefs.load("moog/matriarch", [CORPUS])
		groups = matriarch.grouped_controls()

		assert groups["oscillator"][0].name == "osc_2_frequency"
		assert len(groups["arpeggiator"]) == 8

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
