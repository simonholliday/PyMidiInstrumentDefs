"""Tests for pymidiinstrumentdefs.midnam — starting a definition from a MIDNAM."""

import pathlib

import pytest

import pymidiinstrumentdefs.midnam
import pymidiinstrumentdefs.validation


# Shaped after the real Moog_Minitaur.midnam rather than after the format's prose
# description: a value list written inline inside a control, a shared one referred
# to by name, 14-bit controls split into "(Coarse)" and "(Fine)" halves, notes
# nested inside a NoteGroup, and more than one note map. An earlier version of
# this fixture used a `Values ValueNameList="..."` attribute, which reads well and
# appears in no real file, so the tests passed against a shape that does not exist.
MINITAUR = """<?xml version="1.0" encoding="UTF-8"?>
<MIDINameDocument>
  <MasterDeviceNames>
    <Manufacturer>Moog Music</Manufacturer>
    <Model>Minitaur</Model>
    <ChannelNameSet Name="Names">
      <PatchBank Name="Presets">
        <PatchNameList>
          <Patch Number="1" Name="Bass" ProgramChange="0"/>
          <Patch Number="2" Name="Lead" ProgramChange="1"/>
        </PatchNameList>
      </PatchBank>
    </ChannelNameSet>
    <ValueNameList Name="Toggle">
      <Value Number="0" Name="Off"/>
      <Value Number="64" Name="On"/>
    </ValueNameList>
    <ControlNameList Name="Controls">
      <Control Type="7bit" Number="3" Name="LFO Rate (Coarse)"/>
      <Control Type="7bit" Number="35" Name="LFO Rate (Fine)"/>
      <Control Type="7bit" Number="20" Name="KB Track (Coarse)"/>
      <Control Type="7bit" Number="54" Name="KB Track (Fine)"/>
      <Control Type="7bit" Number="91" Name="Key Priority">
        <Values Min="0" Max="127">
          <ValueNameList>
            <Value Number="0" Name="Low"/>
            <Value Number="43" Name="High"/>
            <Value Number="85" Name="Last"/>
          </ValueNameList>
        </Values>
      </Control>
      <Control Type="7bit" Number="82" Name="LFO Key Trigger">
        <Values Min="0" Max="127">
          <UsesValueNameList Name="Toggle"/>
        </Values>
      </Control>
      <Control Type="14bit" Number="19" Name="Cutoff"/>
      <Control Type="7bit" Number="900" Name="Nonsense"/>
      <Control Type="7bit" Number="70" Name="16' Octave"/>
    </ControlNameList>
    <NoteNameList Name="Kit 00">
      <NoteGroup Name="Drums">
        <Note Number="36" Name="Kick"/>
      </NoteGroup>
      <Note Number="38" Name="Snare"/>
    </NoteNameList>
    <NoteNameList Name="Kit 01">
      <Note Number="60" Name="Something Else"/>
    </NoteNameList>
  </MasterDeviceNames>
</MIDINameDocument>
"""


class TestReading:

	def test_identity_comes_across (self) -> None:
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "Moog_Minitaur.midnam")

		assert definition.model.name == "Minitaur"
		assert definition.model.manufacturer == "Moog Music"
		assert pymidiinstrumentdefs.midnam.suggested_name(definition) == "moog_music/minitaur"

	def test_a_draft_with_no_maker_is_filed_under_unknown (self) -> None:
		"""A name needs a maker, and inventing one would be worse than saying so."""
		document = "<MIDINameDocument><MasterDeviceNames><Model>X-1</Model></MasterDeviceNames></MIDINameDocument>"
		definition = pymidiinstrumentdefs.midnam.read(document, source = "x.midnam")

		assert pymidiinstrumentdefs.midnam.suggested_name(definition) == "unknown/x_1"

	def test_an_import_is_marked_unverified (self) -> None:
		"""An import is an on-ramp, never an authority, and says so about itself."""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "Moog_Minitaur.midnam")

		assert definition.source == "imported from Moog_Minitaur.midnam, unverified"
		assert definition.is_unverified

	def test_a_value_list_written_inline_is_read (self) -> None:
		"""A MIDNAM Value Number is the low end of its band, as a definition wants.

		Note the 85: that is what the shared Minitaur file really says, and the
		manufacturer's own firmware addendum says 86. An import is an on-ramp.
		"""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")
		priority = definition.controls["key_priority"]

		assert priority.cc == 91
		assert priority.values == {"low": 0, "high": 43, "last": 85}
		assert priority.band("high") == (43, 84)

	def test_bands_listed_downwards_are_sorted (self) -> None:
		"""A real file counts a clock divider downwards, and a definition may not.

		A band is defined by its number, not by where it sits in the file, so
		sorting loses nothing -- and without it the import produces a definition
		this package would refuse to load.
		"""
		document = (
			"<MIDINameDocument><MasterDeviceNames><Model>X</Model>"
			'<Control Number="9" Name="Divider"><Values Min="0" Max="127"><ValueNameList>'
			'<Value Number="107" Name="Fast"/><Value Number="102" Name="Slow"/>'
			"</ValueNameList></Values></Control>"
			"</MasterDeviceNames></MIDINameDocument>"
		)
		definition = pymidiinstrumentdefs.midnam.read(document, source = "x.midnam")

		assert list(definition.controls["divider"].values.items()) == [("slow", 102), ("fast", 107)]

	def test_a_shared_value_list_is_resolved_by_name (self) -> None:
		"""Controls refer to a named list with UsesValueNameList, not an attribute."""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")

		assert definition.controls["lfo_key_trigger"].values == {"off": 0, "on": 64}

	def test_a_coarse_and_fine_pair_becomes_one_control (self) -> None:
		"""MIDNAM splits a 14-bit control in two and says so only in the names."""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")
		rate = definition.controls["lfo_rate"]

		assert rate.cc == 3
		assert rate.lsb == 35
		assert rate.is_14_bit
		assert "lfo_rate_fine" not in definition.controls

	def test_a_pair_whose_numbers_disagree_is_left_apart (self) -> None:
		"""Names pairing is not enough: the fine number must be the coarse one plus 32.

		This is a real disagreement in the real file -- KB Track is printed as
		20 and 54 -- and one of the two numbers is wrong. Guessing which would be
		inventing a number, so both halves stay and the conflict is reported.
		"""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")

		assert definition.controls["kb_track_coarse"].lsb is None
		assert definition.controls["kb_track_fine"].cc == 54
		assert any("not 20 + 32" in warning for warning in definition.warnings)

	def test_a_14_bit_control_with_no_partner_says_so (self) -> None:
		"""Marked 14bit with no fine half beside it: `lsb` has to be added by hand."""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")

		assert definition.controls["cutoff"].lsb is None
		assert any("14bit" in warning for warning in definition.warnings)

	def test_everything_a_midnam_cannot_carry_is_named (self) -> None:
		"""No polyphony, no note range, no velocity, no aftertouch — say so once."""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")

		assert any("added by hand" in warning for warning in definition.warnings)
		assert definition.voice.polyphony is None
		assert definition.voice.note_range is None

	def test_repeated_control_names_do_not_collapse (self) -> None:
		"""Two controls quietly becoming one is a loss nobody would notice."""
		document = (
			"<MIDINameDocument><MasterDeviceNames><Model>X</Model>"
			'<Control Number="5" Name="Rate"/><Control Number="3" Name="Rate"/>'
			"</MasterDeviceNames></MIDINameDocument>"
		)
		definition = pymidiinstrumentdefs.midnam.read(document, source = "x.midnam")

		assert definition.controls["rate"].cc == 5
		assert definition.controls["rate_2"].cc == 3

	def test_a_name_starting_with_a_digit_is_kept_not_dropped (self) -> None:
		"""16' Octave is a real control, and renaming beats losing it."""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")
		matching = [name for name in definition.controls if name.endswith("16_octave")]

		assert matching, f"the octave control was dropped: {list(definition.controls)}"

	def test_an_impossible_control_number_is_skipped_with_a_warning (self) -> None:
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")

		assert all(control.cc is not None and control.cc <= 127
			for control in definition.controls.values())
		assert any("not 0-127" in warning for warning in definition.warnings)

	def test_notes_become_voices_including_grouped_ones (self) -> None:
		"""A NoteGroup organises notes inside a map; they still belong to it."""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")

		assert definition.voice.addressing == "voices"
		assert definition.voice.voices == {"kick": 36, "snare": 38}

	def test_only_the_first_note_map_is_taken_and_the_rest_are_named (self) -> None:
		"""One measured file carries fifty kits; a definition describes one map.

		Flattening them together would invent an instrument that does not exist.
		"""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")

		assert 60 not in definition.voice.voices.values()
		assert any("note maps in this file" in warning for warning in definition.warnings)

	def test_patches_are_counted_as_presets (self) -> None:
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")

		assert definition.midi.program_change is not None
		assert definition.midi.program_change.presets == 2

	def test_a_namespaced_document_still_reads (self) -> None:
		"""Some MIDNAM files carry a namespace and most do not."""
		namespaced = MINITAUR.replace(
			"<MIDINameDocument>", '<MIDINameDocument xmlns="http://www.midi.org/dtds">')
		definition = pymidiinstrumentdefs.midnam.read(namespaced, source = "x.midnam")

		assert definition.model.name == "Minitaur"


class TestRefusals:

	def test_broken_xml_is_refused (self) -> None:
		with pytest.raises(pymidiinstrumentdefs.validation.DefinitionError) as raised:
			pymidiinstrumentdefs.midnam.read("<not xml", source = "x.midnam")

		assert "not valid XML" in str(raised.value)

	def test_a_document_with_no_model_is_refused (self) -> None:
		"""Without a model name there is nothing to file the result under."""
		with pytest.raises(pymidiinstrumentdefs.validation.DefinitionError) as raised:
			pymidiinstrumentdefs.midnam.read(
				"<MIDINameDocument><Manufacturer>X</Manufacturer></MIDINameDocument>",
				source = "x.midnam")

		assert "no <Model>" in str(raised.value)


class TestDraftFile:

	def test_the_draft_it_writes_loads_back (self, tmp_path: pathlib.Path) -> None:
		"""An importer that emits a file this package cannot read is worth nothing.

		Saved under the name it suggests and loaded back by that name, so the
		suggestion is proved to be one the loader accepts.
		"""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "Moog_Minitaur.midnam")
		name = pymidiinstrumentdefs.midnam.suggested_name(definition)
		path = tmp_path / f"{name}.yaml"

		path.parent.mkdir(parents = True)
		path.write_text(pymidiinstrumentdefs.midnam.to_yaml(definition), encoding = "utf-8")

		reloaded = pymidiinstrumentdefs.load(name, [tmp_path])

		assert reloaded.model.name == "Minitaur"
		assert reloaded.controls["key_priority"].values == {"low": 0, "high": 43, "last": 85}
		assert reloaded.controls["lfo_rate"].lsb == 35
		assert reloaded.is_unverified

	def test_off_and_on_are_quoted_on_the_way_out (self) -> None:
		"""Otherwise YAML reads them back as false and true, and the file will not load.

		Every switch in the world has bands called off and on, so an emitter that
		does not quote them writes files that cannot be read.
		"""
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")
		text = pymidiinstrumentdefs.midnam.to_yaml(definition)

		assert '"off": 0' in text
		assert '"on": 64' in text

	def test_the_draft_says_it_is_a_draft (self) -> None:
		definition = pymidiinstrumentdefs.midnam.read(MINITAUR, source = "x.midnam")
		text = pymidiinstrumentdefs.midnam.to_yaml(definition)

		assert text.startswith("# A DRAFT.")
		assert "unverified" in text
