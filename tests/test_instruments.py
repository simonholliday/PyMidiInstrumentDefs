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

	def test_the_bundled_names (self) -> None:
		"""Every bundled definition, by name, so adding or removing one shows here too."""
		assert pymidiinstrumentdefs.available([CORPUS]) == [
			"arturia/microfreak",
			"arturia/minifreak",
			"behringer/model_d",
			"elektron/digitakt",
			"elektron/digitone",
			"elektron/syntakt",
			"expressive_e/osmose",
			"korg/minilogue_xd",
			"korg/wavestate",
			"modal/carbon8m",
			"moog/dfam",
			"moog/grandmother",
			"moog/labyrinth",
			"moog/matriarch",
			"moog/minitaur",
			"moog/sub_37",
			"moog/subharmonicon",
			"moog/subsequent_37",
			"pwm/malevolent",
			"roland/tr8s",
			"sequential/take_5",
			"soma/pulsar_23",
			"vermona/drm1_mkiv",
			"voce/electric_piano",
			"waldorf/streichfett",
			"yamaha/dx7",
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

		Two and three-digit forms are left alone: `CC #39` is a controller, not an item.
		"""
		internal = re.compile(r"#[0-9]{3,}|\bSimon\b|\bSubroutine\b|/mnt/|/home/", re.IGNORECASE)

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

	def test_both_mpe_instruments_are_found_by_the_field_alone (self) -> None:
		"""The Carbon8M was corrected with the Osmose so the corpus answers one way.

		A consumer asking which instruments spread their voices across channels has to
		get both or neither; one flagged and one not is worse than none, because it
		reads as a settled answer and is wrong about the one it misses.
		"""
		flagged = sorted(name for name in pymidiinstrumentdefs.available([CORPUS])
			if pymidiinstrumentdefs.load(name, [CORPUS]).midi.per_voice_channels)

		assert flagged == ["expressive_e/osmose", "modal/carbon8m"]

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
