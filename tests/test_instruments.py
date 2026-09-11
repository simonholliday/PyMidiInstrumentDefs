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
		"""The four definitions that moved from PyMidiDefs 0.4.0, by their new names."""
		assert pymidiinstrumentdefs.available([CORPUS]) == [
			"moog/dfam",
			"moog/matriarch",
			"moog/minitaur",
			"vermona/drm1_mkiv",
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
		"""The README promises each one names its manual and its pages.

		"The manual" cannot be checked by anybody; "p.13" can. This keeps that
		promise true as the corpus grows, since a source line is the one part of
		a definition nothing else can verify for you.
		"""
		cites = re.compile(r"\bpp?\.\s*\d|\b\d+\s*pages?\b|\bevery page\b", re.I)

		for path in bundled():
			definition = pymidiinstrumentdefs.load_file(path)
			source = definition.source or ""

			assert "manual" in source.lower(), f"{path.name} does not name a document"
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

	def test_kind_may_be_stated_when_the_bands_are_not_known (self) -> None:
		"""Saying "this is a choice" without the numbers is honest, and useful.

		Three of the Matriarch's controls are named as three-state in the source
		with no value ranges given. The override records what they are without
		inventing where the bands fall.
		"""
		matriarch = pymidiinstrumentdefs.load("moog/matriarch", [CORPUS])
		arp_mode = matriarch.controls["arp_mode"]

		assert arp_mode.kind == pymidiinstrumentdefs.CHOICE
		assert arp_mode.values == {}


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
