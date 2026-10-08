"""Tests for pymidiinstrumentdefs — reading what a particular model does."""

import collections
import dataclasses
import pathlib
import re

import pytest
import yaml

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

	def test_the_readmes_table_is_in_the_order_the_loader_lists_them (self) -> None:
		"""A table of seventy-five rows is only findable if its order is the obvious one.

		Sixteen rows had drifted out of place by v0.1.12 - the Hydrasynth above the five
		Arturias, two Rolands above the two MC rows, two Waldorfs above the Vermona and
		the Voce - because a row is added where the eye lands rather than where it sorts.
		Nothing published reads the order, so this is for a reader of the table and for
		nobody else, which is reason enough: a list nobody can scan is a list nobody uses.
		"""
		readme = (pathlib.Path(__file__).parent.parent / "README.md").read_text(encoding = "utf-8")

		printed = re.findall(r"^\| `([^`]+)` \|", readme, re.MULTILINE)

		assert printed == sorted(printed), "the README's table rows are out of order"

		# And it is the loader's own listing, so the two cannot drift apart silently.
		assert printed == sorted(pymidiinstrumentdefs.available([CORPUS]))

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
			"ableton/move",
			"access/virus_ti",
			"akai/mpc_key_37",
			"akai/mpc_live",
			"akai/mpc_live_iii",
			"akai/mpc_sample",
			"akai/mpc_xl",
			"arturia/astrolab",
			"arturia/drumbrute",
			"arturia/drumbrute_impact",
			"arturia/microbrute",
			"arturia/microfreak",
			"arturia/minifreak",
			"arturia/polybrute",
			"arturia/polybrute_12",
			"asm/hydrasynth_explorer",
			"asm/leviasynth",
			"behringer/edge",
			"behringer/lm_drum",
			"behringer/model_d",
			"behringer/neutron",
			"behringer/pro_800",
			"behringer/rd_9",
			"behringer/td_3",
			"behringer/ub_xa",
			"dirtywave/m8",
			"dreadbox/artemis",
			"dreadbox/nymphes",
			"dreadbox/typhon",
			"elektron/analog_four",
			"elektron/analog_rytm_mkii",
			"elektron/digitakt",
			"elektron/digitakt_ii",
			"elektron/digitone",
			"elektron/digitone_ii",
			"elektron/machinedrum",
			"elektron/model_cycles",
			"elektron/model_samples",
			"elektron/octatrack",
			"elektron/syntakt",
			"elektron/tonverk",
			"erica_synths/hexdrums",
			"erica_synths/perkons_hd_01",
			"expressive_e/osmose",
			"groove_synthesis/third_wave",
			"intellijel/cascadia",
			"korg/drumlogue",
			"korg/electribe",
			"korg/kronos",
			"korg/m1",
			"korg/microkorg",
			"korg/microkorg2",
			"korg/minilogue",
			"korg/minilogue_xd",
			"korg/modwave_mk_ii",
			"korg/monologue",
			"korg/ms_20_mini",
			"korg/multi_poly",
			"korg/opsix",
			"korg/volca_bass",
			"korg/volca_beats",
			"korg/volca_drum",
			"korg/volca_fm",
			"korg/volca_keys",
			"korg/volca_sample",
			"korg/wavestate",
			"korg/wavestation",
			"make_noise/zero_coast",
			"modal/carbon8m",
			"moog/dfam",
			"moog/grandmother",
			"moog/labyrinth",
			"moog/matriarch",
			"moog/messenger",
			"moog/minimoog_model_d",
			"moog/minitaur",
			"moog/mother_32",
			"moog/muse",
			"moog/sub_37",
			"moog/subharmonicon",
			"moog/subsequent_37",
			"native_instruments/maschine_plus",
			"novation/bass_station_ii",
			"novation/circuit",
			"novation/circuit_rhythm",
			"novation/circuit_tracks",
			"novation/mininova",
			"novation/peak",
			"novation/summit",
			"oberheim/ob_x8",
			"oberheim/teo_5",
			"polyend/tracker",
			"pwm/malevolent",
			"roland/d_50",
			"roland/fantom_6_7_8",
			"roland/jd_08",
			"roland/jd_800",
			"roland/jd_xi",
			"roland/ju_06a",
			"roland/juno_106",
			"roland/jupiter_x",
			"roland/jx_08",
			"roland/jx_8p",
			"roland/mc_101",
			"roland/mc_707",
			"roland/p_6",
			"roland/s_1",
			"roland/sh_4d",
			"roland/sp_404mkii",
			"roland/tb_3",
			"roland/tr8s",
			"roland/tr_08",
			"roland/tr_1000",
			"roland/tr_6s",
			"roland/tr_8",
			"roland/tr_909",
			"sequential/fourm",
			"sequential/prophet_10",
			"sequential/prophet_5",
			"sequential/prophet_6",
			"sequential/take_5",
			"soma/pulsar_23",
			"synthstrom_audible/deluge",
			"teenage_engineering/ep_133_ko_ii",
			"teenage_engineering/op_1",
			"teenage_engineering/op_1_field",
			"teenage_engineering/op_xy",
			"teenage_engineering/op_z",
			"udo_audio/super_6",
			"vermona/drm1_mkiv",
			"voce/electric_piano",
			"waldorf/blofeld",
			"waldorf/iridium",
			"waldorf/protein",
			"waldorf/streichfett",
			"yamaha/dx7",
			"yamaha/montage_6_7_8",
			"yamaha/reface_cp",
			"yamaha/reface_cs",
			"yamaha/reface_dx",
			"yamaha/seqtrak",
		]

	def test_the_readme_qualifies_a_channel_that_could_be_read_two_ways (self) -> None:
		"""The site this corpus feeds publishes Subsample too, which has audio channels.

		Its house voice qualifies "channel" wherever a reader could take it more than one
		way, and its glossary check reports a bare one in this README without ever blocking
		(#4464).  Two of the four it finds are this project's own prose and are qualified
		here; **the other two are names and must not be "corrected"** - the MIDI
		specification's "channel mode", and Roland's own "a control channel".  Listed so
		that a later rewrite of either row does not quietly undo the first pair or
		over-correct the second.
		"""
		readme = (pathlib.Path(__file__).parent.parent / "README.md").read_text(encoding = "utf-8")

		rows = {match.group(1): match.group(0)
			for match in re.finditer(r"(?m)^\| `([^`]+)` \|.*$", readme)}

		assert "six parts on six MIDI channels" in rows["korg/volca_drum"]
		assert "a fifth MIDI channel that makes no sound" in rows["roland/mc_101"]

		# And the two the site accepts as names, which stay bare.
		assert "reserves for channel mode" in rows["asm/hydrasynth_explorer"]
		assert "a control channel that makes no sound" in rows["roland/mc_707"]


	def test_nothing_published_writes_a_us_spelling_in_its_own_prose (self) -> None:
		"""The site this corpus feeds is written in British English and will not publish one.

		A quotation keeps its source's spelling, and so does a maker's own name for a thing -
		a control's label, a document's title - so what is quoted is left alone and only the
		prose around it is swept. This exists because three definitions had to be corrected
		by hand before the site could take its spelling exception off, and nothing would
		have caught the fourth.

		**AND THE README IS SWEPT TOO, BECAUSE IT IS PUBLISHED AND WAS NOT.** The site
		prints it beneath its list of instruments, and "synthesizer mode" in the Polyend
		Tracker's row stopped the site publishing v0.1.12 - the exception had to be relaxed
		for that one word by hand. The sweep read each definition's account and nothing
		else, so a file that ships and is rendered was never looked at. **Sweep what is
		published, not what is convenient to load.**

		**AND "analog" IS SWEPT CASE-SENSITIVELY, BECAUSE TWO INSTRUMENTS ARE NAMED WITH IT.**
		The Behringer PRO-800's account wrote it twice and the site had to relax its check by
		hand for v0.1.13 (#4473). A pattern that ignored case would report Elektron's Analog
		Four and Analog Rytm on every run, so it would be turned off rather than obeyed.
		"""
		patterns = [
			re.compile(r"\b[a-z]{3,}iz(e|es|ed|er|ers|ing|ation|ations)\b", re.IGNORECASE),
			re.compile(r"\b[a-z]{3,}yz(e|es|ed|ing)\b", re.IGNORECASE),
			re.compile(r"\b(favorite|favorites|color|colors|behavior|behaviors|honor|flavor)\b",
				re.IGNORECASE),
			# **NOT case-insensitive, and that is deliberate.** Two instruments here are named
			# Analog Four and Analog Rytm, and the site reads past both as names; only the
			# lower-case word is this project's prose to correct. `analogue` and `analogy` keep
			# a word character after "analog", so neither matches. By #4473.
			re.compile(r"\banalogs?\b"),
		]

		def prose (text: str) -> str:
			"""One passage with everybody else's spelling taken out of it.

			Double quotation marks are a quotation and backticks are an identifier - a
			field name, a definition's name, a file - and neither is this project's
			prose to correct.
			"""
			return re.sub(r"`[^`]*`", " ", re.sub(r'"[^"]*"', " ", text))

		found = []

		for name in pymidiinstrumentdefs.available([CORPUS]):
			account = pymidiinstrumentdefs.load(name, [CORPUS]).source or ""

			for pattern in patterns:
				found += [(name, hit.group(0))
					for hit in pattern.finditer(prose(account))]

		# The README ships in the wheel and is rendered on the site, so it is prose too.
		readme = (CORPUS.parent.parent / "README.md").read_text(encoding = "utf-8")

		for number, line in enumerate(readme.splitlines(), start = 1):
			for pattern in patterns:
				found += [(f"README.md line {number}", hit.group(0))
					for hit in pattern.finditer(prose(line))]

		assert found == [], f"a US spelling is in prose that gets published: {found}"

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

	def test_no_definition_carries_a_source_key_the_format_does_not_have (self) -> None:
		"""Because a mistyped one is dropped in silence, with every gate still green.

		**Found by writing one.**  `roland/jupiter_x` was written with `version` on five
		of its sources where the field is `edition`, and nothing objected: the file
		loaded, the validator passed, both checkers passed, and the editions were
		simply not there.  It was caught only because a test read one of them back.

		So `dated` written as `date`, or `sha256` as `sha`, would ship a source with no
		date or no digest and look exactly like a source that has none - which is the
		distinction this corpus is most careful about everywhere else.  This test is
		the guard the loader does not provide.
		"""
		known = {field.name for field in dataclasses.fields(pymidiinstrumentdefs.Source)}
		stray: dict[str, list[str]] = {}

		for path in bundled():
			raw = yaml.safe_load(path.read_text(encoding = "utf-8")) or {}

			for name, block in (raw.get("sources") or {}).items():
				if not isinstance(block, dict):
					continue

				for key in block:
					if key not in known:
						stray.setdefault(key, []).append(
							f"{path.parent.name}/{path.stem}:{name}")

		assert stray == {}, f"source keys the format ignores: {stray}"


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
		"""Twenty-three definitions carry no controls, for five different reasons.

		Pinned here because the count has gone stale in notes twice: a twenty-fourth
		cannot be added without saying which kind it is. The twenty-third is
		`akai/mpc_xl`, `learned` from the MPC Live III's own book. The twenty-first was
		`arturia/drumbrute`, `learned` for the DrumBrute Impact's reason from its own
		manual, and the twenty-second is `behringer/rd_9`, `none` for the Model D's
		reason: a whole user manual searched, not a quick start guide.

		**The fifth reason arrived with the UB-Xa and the format has no word for it.**
		Its maker claims "comprehensive MIDI implementation" and publishes no part of
		one, which is neither ``none`` - that says the instrument answers to no
		controller, and the maker's own claim contradicts it - nor ``learned``, which
		says there is no factory map by design. So it shares ``None`` with the two
		definitions where nobody has established anything, and it is the opposite of
		those: a great deal was established, by two readers, and what they established
		is that the document does not exist.

		**The TR-909 joins ``none`` by a route none of the others took.**  Its maker
		did publish a MIDI page, numbered seven kinds of message on it in its own
		words, and put no controller among them - then sent the reader to a leaflet
		that came in the box and that Roland does not publish.  So the field is right
		for the usual reason, somebody looked and found none, and the looking was at
		an enumeration rather than at a chart's crossed box.

		**AND THE MS-20 MINI'S IS THE STRONGEST OF THE ESTABLISHED ONES.**  Korg wrote
		down what the socket accepts rather than what it refuses: *"The only MIDI
		messages that can be received at the MIDI IN connector are note messages
		(Velocity is disabled) on MIDI channel 1 (fixed)."*  A crossed box says a thing
		is not recognised; a sentence naming everything that is recognised says the
		same and settles two further fields while it is there.

		**BUT THE HEXDRUMS'S IS THE ONLY ONE OF THE EIGHT THAT RECORDS A DECISION
		RATHER THAN AN ABSENCE.**  Every other ``none`` here is something somebody
		established - a crossed box, an enumeration that numbered seven kinds of
		message and put no controller among them, a sentence naming everything the
		socket accepts.  Erica Synths instead say why there is nothing to find:
		*"There is no MIDI CC implementation for parameter control, however, since the
		parameters aren't digitally mapped.  This is intentional to allow for a more
		traditional drum machine workflow."*  That rules out the possibility every
		other member of this set leaves open - that a map exists and nobody has found
		it - so a consumer can act on it with more confidence than on any of them.
		"""
		empty = {name for name in pymidiinstrumentdefs.available([CORPUS])
			if not pymidiinstrumentdefs.load(name, [CORPUS]).controls}

		assert len(empty) == 23

		kinds: dict[str | None, set[str]] = {}

		for name in empty:
			definition = pymidiinstrumentdefs.load(name, [CORPUS])
			key = "stated_none" if definition.midi.stated_none else definition.midi.control_change
			kinds.setdefault(key, set()).add(name)

		assert kinds["none"] == {"ableton/move", "behringer/model_d", "behringer/rd_9", "behringer/td_3",
			"erica_synths/hexdrums", "korg/ms_20_mini", "moog/labyrinth", "roland/tr_909",
			"vermona/drm1_mkiv"}
		assert kinds["learned"] == {"akai/mpc_live", "akai/mpc_live_iii", "akai/mpc_xl", "arturia/drumbrute",
			"arturia/drumbrute_impact", "dirtywave/m8", "roland/d_50", "synthstrom_audible/deluge",
			"teenage_engineering/op_1"}
		assert kinds["stated_none"] == {"moog/dfam"}

		# And the four that record no word at all, for three different reasons now.
		assert kinds[None] == {"akai/mpc_sample", "pwm/malevolent", "behringer/ub_xa",
			"behringer/edge"}

		# **THE EDGE IS THE FOURTH AND IT IS THE MALEVOLENT'S REASON, NOT THE UB-Xa's.**
		# Everything its maker publishes for it is a quick start guide, and a quick start
		# guide that lists no controller is not an instrument that has none - which is the
		# ruling `pwm/malevolent` set and `behringer/td_3` had to earn its way out of.
		# **The same maker, the same kind of document, and the opposite answer**, which is
		# the pair worth asserting together: the TD-3's guide carries a table of MIDI
		# messages and its sibling's copy of that table carries a controller, so the
		# absence there is informative. The EDGE's guides have no such table at all.
		edge = " ".join((pymidiinstrumentdefs.load("behringer/edge", [CORPUS]).source or "").split())
		td_3 = " ".join((pymidiinstrumentdefs.load("behringer/td_3", [CORPUS]).source or "").split())

		assert "**FOUR DOCUMENTS AND ALL FOUR ARE THE SAME QUICK START GUIDE.**" in edge
		assert "A QUICK START GUIDE THAT LISTS NO CONTROLLER IS NOT THE SAME AS AN INSTRUMENT" \
			" THAT HAS NONE" in td_3

		assert pymidiinstrumentdefs.load("behringer/td_3", [CORPUS]).midi.control_change == "none"
		assert pymidiinstrumentdefs.load("behringer/edge", [CORPUS]).midi.control_change is None

		# **THE RD-9 TAKES THE MODEL D'S ROUTE, NOT THE EDGE'S.** Thirty-eight pages that set
		# channels, map notes, follow a start message and dump SysEx, and never name a controller:
		# a whole manual searched, which is what the Model D's `none` rests on. The EDGE stays
		# unset because quick start guides are all its maker publishes.
		rd_9 = " ".join((pymidiinstrumentdefs.load("behringer/rd_9", [CORPUS]).source or "").split())

		assert "WHICH IS THE MODEL D'S ROUTE TO `none`." in rd_9
		assert pymidiinstrumentdefs.load("behringer/rd_9", [CORPUS]).midi.control_change == "none"

		# **TWO OF THOSE CLAIM NOTHING BECAUSE NOBODY HAS ESTABLISHED ANYTHING. THE THIRD
		# CLAIMS NOTHING BECAUSE THERE IS NO WORD FOR WHAT WAS ESTABLISHED.** Only one of
		# them says so, and that is the difference a reader needs, so it is asserted rather
		# than left to the empty field they share.
		ub_xa = " ".join((pymidiinstrumentdefs.load("behringer/ub_xa", [CORPUS]).source or "").split())

		assert "THE MAKER CLAIMS A MIDI IMPLEMENTATION AND PUBLISHES NO PART OF IT" in ub_xa
		assert "Neither word this format has is true here" in ub_xa

		# **THE MOVE STATES THE ABSENCE IN THE PLAINEST WORDS OF THE FIVE**, and is the only
		# definition in this corpus built against its maker's manual rather than on it: that
		# manual is three years of releases out of date and says nothing about being so, which
		# is a thing a reader of the corpus needs told rather than left to find.
		move = " ".join((pymidiinstrumentdefs.load("ableton/move", [CORPUS]).source or "").split())

		assert "MIDI CC, and MIDI mapping are not supported" in move
		assert "THE MANUAL CANNOT BE USED FOR MIDI AND IT TOOK A SECOND READER TO SEE IT" in move

		# **THE M8 IS THE CLEAREST OF THE LEARNED SIX AND THE ONLY ONE WHERE THE MAKER
		# SAYS SO IN ITS OWN SPECIFICATIONS.** Everywhere else `learned` is a conclusion
		# drawn from a map's absence; here Dirtywave prints "user defined" on the
		# specification list, so the word is the maker's rather than the reader's.
		m8 = " ".join((pymidiinstrumentdefs.load("dirtywave/m8", [CORPUS]).source or "").split())

		assert "user defined" in m8
		assert "THERE IS NO CONTROL MAP AND THE MAKER SAYS SO IN ITS OWN SPECIFICATIONS" in m8

		for name in ("akai/mpc_sample", "pwm/malevolent"):
			account = " ".join((pymidiinstrumentdefs.load(name, [CORPUS]).source or "").split())

			assert "Neither word this format has is true here" not in account


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

	def test_system_exclusive_is_not_recorded_because_two_documents_disagree (self) -> None:
		"""And the TR-6S, which met the same conflict later, is recorded the same way.

		This file said `sysex: false` for a while, which was the chart read correctly. What
		changed it is what the claim does to a reader: a panel told an instrument has no
		system exclusive hides every sysex feature of a machine whose maker documents a
		device ID for matching sysex messages.
		"""
		tr8s = pymidiinstrumentdefs.load("roland/tr8s", [CORPUS])
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])

		assert tr8s.midi.sysex is None
		assert tr_6s.midi.sysex is None

		account = " ".join((tr8s.source or "").split())

		assert "CONTRADICT EACH OTHER ABOUT SYSTEM EXCLUSIVE" in account
		assert "the device ID numbers of both devices must match" in account
		assert "THIS FILE SAID `sysex: false` UNTIL THE TR-6S MET THE SAME CONFLICT" in account

		# The manual is cited twice over now, and the account no longer says otherwise.
		assert "CITED FOR TWO THINGS" in account
		assert "CITED FOR ONE THING" not in account


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


class TestTonverk:

	"""Sixteen tracks in four kinds, and an appendix that generates more numbers than it prints."""

	def test_its_sixteen_tracks_come_in_four_kinds (self) -> None:
		"""Eight audio, four bus, three send FX and one mix, each with a channel of its own."""
		tonverk = pymidiinstrumentdefs.load("elektron/tonverk", [CORPUS])

		assert list(tonverk.parts) == ["audio", "bus", "fx_send", "mix"]
		assert [part.count for part in tonverk.parts.values()] == [8, 4, 3, 1]
		assert sum(part.count for part in tonverk.parts.values()) == 16
		assert all(part.is_assigned for part in tonverk.parts.values())

		# **ONLY THE AUDIO TRACKS TAKE NOTES**, because a note plays the active track's preset
		# and only tracks 1 to 8 hold one.
		assert tonverk.parts["audio"].takes("notes")

		for key in ("bus", "fx_send", "mix"):
			assert not tonverk.parts[key].takes("notes")
			assert tonverk.parts[key].receives == ("controls",)

	def test_six_numbers_name_different_parameters_on_different_kinds (self) -> None:
		"""Which is a different thing from a number present on one kind and absent on another."""
		tonverk = pymidiinstrumentdefs.load("elektron/tonverk", [CORPUS])

		byte: dict[int, dict[str, str]] = {}

		for control in tonverk.controls.values():
			if control.cc is not None and control.part is not None:
				byte.setdefault(control.cc, {})[control.part] = control.label

		conflicting = sorted(number for number, kinds in byte.items()
			if len(set(kinds.values())) > 1)

		assert conflicting == [16, 17, 18, 20, 21, 22]

		# Each is a source machine's data entry knob on an audio track and an input setting on
		# the mix track, so a message on the wrong channel does something rather than nothing.
		assert byte[16]["audio"].startswith("SRC 1 Data entry knob A")
		assert byte[16]["mix"] == "In A level"

	def test_one_row_of_the_appendix_is_misprinted (self) -> None:
		"""CC 23 and CC 31 are printed with the same name, and only one of them can be right."""
		tonverk = pymidiinstrumentdefs.load("elektron/tonverk", [CORPUS])

		# The label ships as printed; only the key follows the sequence.
		assert tonverk.controls["audio_src_1_data_entry_knob_h"].cc == 23
		assert tonverk.controls["audio_src_2_data_entry_knob_h"].cc == 31

		assert tonverk.controls["audio_src_2_data_entry_knob_h"].label == \
			"SRC 1 Data entry knob H (machine dependent)"

		said = prose_of("elektron", "tonverk")

		assert "Two distinct numbers cannot both be SRC 1's knob H" in said

	def test_the_subtrack_numbers_it_does_not_print_are_not_here (self) -> None:
		"""49 rows against a `1-8` MSB is 392 numbers, and 343 of them are on no page."""
		tonverk = pymidiinstrumentdefs.load("elektron/tonverk", [CORPUS])

		subtracks = [key for key in tonverk.controls if key.startswith("subtrack_")]

		assert len(subtracks) == 49
		assert all(key.startswith("subtrack_1_") for key in subtracks)

		# Every one of them is the first subtrack's, which is the MSB the printed range opens
		# with - so each number is findable on the page the definition cites.
		for key in subtracks:
			control = tonverk.controls[key]

			assert control.nrpn is not None
			assert 128 <= control.nrpn < 256
			assert control.label.startswith("Subtrack 1 ")

		said = prose_of("elektron", "tonverk")

		assert "343 of them are printed nowhere" in said

	def test_every_direction_is_a_setting_and_all_of_them_are_two_way (self) -> None:
		"""Clock, transport and program change each have a switch per direction."""
		tonverk = pymidiinstrumentdefs.load("elektron/tonverk", [CORPUS])

		assert tonverk.midi.clock == "both"
		assert tonverk.midi.transport == "both"

		assert tonverk.midi.program_change is not None
		assert tonverk.midi.program_change.receives is True
		assert tonverk.midi.program_change.sends is True

		# Patterns, not presets: eight banks of sixteen.
		assert tonverk.midi.program_change.presets == 128

		# And the controls travel both ways, so none carries a direction of its own.
		assert all(control.direction == pymidiinstrumentdefs.definition.BOTH
			for control in tonverk.controls.values())

	def test_four_things_are_left_out_and_each_says_why (self) -> None:
		"""Two the manual half-states, one it states per machine, one it never mentions."""
		tonverk = pymidiinstrumentdefs.load("elektron/tonverk", [CORPUS])

		assert tonverk.voice.aftertouch is None
		assert tonverk.voice.pitch_bend is None
		assert tonverk.voice.polyphony is None
		assert tonverk.midi.sysex is None

		said = prose_of("elektron", "tonverk")

		# Aftertouch and pitch bend are received and their shapes are not stated.
		assert "assign up to four parameters to the MIDI aftertouch command" in said
		assert "Sets the amount of pitch bend data from external MIDI devices" in said
		assert "not mentioned in any spelling on any of the 130 pages" in said


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
		reads as a settled answer and is wrong about the one it misses. There are ten
		now. The Deluge is a sequencer as much as a synthesizer - it reads a zone of
		channels as one instrument and writes one out too - the Hydrasynth Explorer is
		the one whose maker says plainest what the flag means, that its voices break
		into individual channels so each note can have its own bend, timbre and
		pressure, and **the Prophet-6 is the first that receives MPE and never sends
		it**, which this field cannot say and its file does.

		**The PolyBrute 12 is the one whose sibling is in this corpus without the
		flag**, which is the case this list exists for: `arturia/polybrute` and
		`arturia/polybrute_12` publish the same controller chart, so a consumer that
		told them apart by their numbers would get one answer for both, and this field
		is where the difference is.

		**And the Super 6 is the one whose MPE is narrower than the instrument**, for a
		reason its maker gives: its analogue hardware can only give six notes different
		control voltages, so MPE mode runs at six voices where the synthesizer has
		twelve. A consumer that read `polyphony` and this flag together would get that
		wrong, and no field here can say it.

		**The OB-X8 is the one where MPE is a value of the MIDI channel setting**, not a
		mode beside it: "3. MIDI Channel... select MPE Enabled" is the whole of how it is
		turned on, so this flag and `channels` are two states of one global rather than
		two independent facts. It is also the one whose MPE changes the bend range out
		from under the program - "+/-48 semitones by default, regardless of the program's
		Bend Lever Amount setting" - where `voice.pitch_bend.semitones` says 12, which is
		the program's own maximum. Two numbers, one field, and its file says which.

		**And the Leviasynth is the one where turning MPE on takes other settings
		away.** Its manual says so in a heading - "enabling mpe will lock out, change or
		disable certain midi parameters" - and names them: all six of its transmit and
		receive channel assignments read `MPE Lock`, and so do its aftertouch transmit,
		its ribbon bend transmit, its transport messages and its overflow. So this flag
		and `channels` are not independent here either, and in a stronger sense than the
		OB-X8's: there the channel setting holds MPE as one of its values, here MPE
		makes the channel settings unreachable. No field says it and its file does.
		"""
		flagged = sorted(name for name in pymidiinstrumentdefs.available([CORPUS])
			if pymidiinstrumentdefs.load(name, [CORPUS]).midi.per_voice_channels)

		assert flagged == ["arturia/polybrute_12", "asm/hydrasynth_explorer",
			"asm/leviasynth", "dreadbox/nymphes", "expressive_e/osmose", "groove_synthesis/third_wave", "modal/carbon8m",
			"oberheim/ob_x8", "sequential/prophet_6", "synthstrom_audible/deluge",
			"udo_audio/super_6", "waldorf/iridium", "waldorf/protein"]

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


class TestOP1Field:

	"""The successor, whose guide exists twice and whose two forms each lack what the other has."""

	def test_the_two_forms_of_one_guide_are_cited_for_different_halves (self) -> None:
		"""The web page has the MIDI reference; the PDF has four controllers it omits."""
		field = pymidiinstrumentdefs.load("teenage_engineering/op_1_field", [CORPUS])

		assert set(field.sources) == {"guide", "pdf", "previous"}

		# The page has no pages to turn to and both PDFs do, which is why a locator against
		# this definition takes two different shapes.
		assert not field.sources["guide"].paginated
		assert field.sources["pdf"].paginated
		assert field.sources["previous"].paginated

		said = prose_of("teenage_engineering", "op_1_field")

		assert "THE MIDI REFERENCE IS ON THE PAGE AND IN NEITHER PDF" in said
		assert "AND THE FOUR CONTROLLERS THE MIDI LFO ANSWERS TO ARE IN THE PDF AND NOT IN" \
			" THE TABLE" in said

	def test_the_four_the_pdf_publishes_are_the_lowest_four_numbers (self) -> None:
		"""CC 1 to 4, which the web table skips entirely - it starts at 7."""
		field = pymidiinstrumentdefs.load("teenage_engineering/op_1_field", [CORPUS])

		for index in (1, 2, 3, 4):
			control = field.controls[f"midi_lfo_input_{index}"]

			assert control.cc == index
			assert control.group == "midi_lfo"

		# And the web table's own lowest number is 7, so the four cannot have come from it.
		from_the_table = [control.cc for key, control in field.controls.items()
			if not key.startswith("midi_lfo_input_") and control.cc is not None]

		assert min(from_the_table) == 7

	def test_every_control_is_received_because_both_tables_say_incoming (self) -> None:
		"""There is no outgoing table anywhere, so nothing claims a transmitting side."""
		field = pymidiinstrumentdefs.load("teenage_engineering/op_1_field", [CORPUS])

		assert len(field.controls) == 52
		assert all(control.direction == "receives" for control in field.controls.values())

		# Which is not the same as the instrument sending nothing: it has a controller mode,
		# and what that sends is published nowhere.
		said = prose_of("teenage_engineering", "op_1_field")

		assert "there is no outgoing table anywhere in either\n# document" in \
			(CORPUS / "teenage_engineering" / "op_1_field.yaml").read_text().lower()
		assert "a midi controller keyboard" in said

	def test_eight_controllers_mean_two_things_and_a_ninth_chooses (self) -> None:
		"""CC 46 to 53 carry both of the maker's functions, and CC 93 selects the mode."""
		field = pymidiinstrumentdefs.load("teenage_engineering/op_1_field", [CORPUS])

		paired = [control for control in field.controls.values()
			if " / " in control.label]

		assert len(paired) == 8
		assert sorted(control.cc for control in paired if control.cc is not None) == \
			list(range(46, 54))

		# Each label holds both of the maker's phrases, which is the standing answer to a
		# meaning that depends on a setting: carry one control and record both meanings.
		assert field.controls["synth_parameter_1"].label == \
			"synth: parameter 1 / drum: active key pitch"

		# And the control that picks between them names its two bands.
		assert field.controls["mode_select"].cc == 93
		assert field.controls["mode_select"].values == {"synth": 0, "drum": 64}

	def test_two_channel_schemes_over_the_same_sixteen_channels (self) -> None:
		"""Four tape tracks and eight sound slots, both starting at the base channel."""
		field = pymidiinstrumentdefs.load("teenage_engineering/op_1_field", [CORPUS])

		assert list(field.parts) == ["track", "sound_slot"]
		assert field.parts["track"].count == 4
		assert field.parts["sound_slot"].count == 8

		# **BOTH START AT THE SAME PLACE**, which is what the overlap means: channel 2 is
		# tape track 2 and sound slot 2 at once.
		assert field.parts["track"].channel_offset == 0
		assert field.parts["sound_slot"].channel_offset == 0

		# Neither takes notes - a note plays the active sound on any of the sixteen.
		for part in field.parts.values():
			assert part.receives == ("controls",)
			assert not part.takes("notes")

		# Three controllers are the tracks' and one is the slots'.
		parted = collections.Counter(control.part for control in field.controls.values())

		assert parted["track"] == 3
		assert parted["sound_slot"] == 1
		assert parted[None] == 48

	def test_the_tempo_controller_is_a_piecewise_map_recorded_as_bands (self) -> None:
		"""Three bands over one range, and what each spans is in its name."""
		field = pymidiinstrumentdefs.load("teenage_engineering/op_1_field", [CORPUS])

		assert field.controls["tempo"].values == {
			"bpm_40_to_50": 0, "bpm_52_to_166": 6, "bpm_168_to_180": 121}

	def test_all_notes_off_is_left_out_because_the_standard_says_it (self) -> None:
		"""The table's last row is CC 123, which a definition may not carry."""
		field = pymidiinstrumentdefs.load("teenage_engineering/op_1_field", [CORPUS])

		assert 123 not in {control.cc for control in field.controls.values()}

		said = prose_of("teenage_engineering", "op_1_field")

		assert "which is a channel mode message" in said

	def test_it_is_the_first_with_both_a_factory_map_and_assignable_controllers (self) -> None:
		"""Its sibling records `learned` and no controls; this one cannot say both."""
		field = pymidiinstrumentdefs.load("teenage_engineering/op_1_field", [CORPUS])
		op1 = pymidiinstrumentdefs.load("teenage_engineering/op_1", [CORPUS])

		assert op1.midi.learns_control_change
		assert op1.controls == {}

		# This one leaves the field unset rather than claiming the whole map is learned,
		# because 48 of its 52 controllers are the maker's and four are the player's.
		assert field.midi.control_change is None
		assert not field.midi.learns_control_change
		assert not field.midi.refuses_control_change

		said = prose_of("teenage_engineering", "op_1_field")

		assert "This is the first definition\n  here with both kinds at once" in \
			(CORPUS / "teenage_engineering" / "op_1_field.yaml").read_text()
		assert "it cannot say \"48 fixed and 4" in said


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
		assert opsix.midi.program_change.presets == 500


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


class TestTR909:

	"""Whose maker published one MIDI page, seven kinds of message, and not one number."""

	def test_it_carries_no_controls_and_says_somebody_looked (self) -> None:
		"""`control_change: none`, reached by an enumeration rather than a crossed box."""
		tr = pymidiinstrumentdefs.load("roland/tr_909", [CORPUS])

		assert tr.controls == {}
		assert tr.groups == {}
		assert tr.midi.refuses_control_change
		assert not tr.midi.learns_control_change
		assert not tr.midi.stated_none

		said = prose_of("roland", "tr_909")

		assert "Information which can be communicated are as follows." in said

	def test_the_absence_of_an_implementation_is_checked_against_the_makers_own_list (self) -> None:
		"""457 documents, 38 of them implementations, ten TRs and not one among them."""
		tr = pymidiinstrumentdefs.load("roland/tr_909", [CORPUS])

		assert set(tr.sources) == {"manual", "archive"}
		assert tr.sources["archive"].kind == "web_page"

		said = prose_of("roland", "tr_909")

		assert "TR-909 Owner's Manual" in said
		assert "D-50 MIDI Implementation" in said
		assert "every one of them an owner's manual and nothing else" in said

	def test_its_manual_is_a_scan_and_the_corpus_already_has_seven_more (self) -> None:
		"""So the quotations are read by eye and the checker reports them unchecked."""
		said = prose_of("roland", "tr_909")

		assert "THE MANUAL IS A SCAN AND HAS NO TEXT LAYER AT ALL." in said

		# Named because this is not a new liberty: four shipped definitions do it already.
		for sibling in ("roland/juno_106", "roland/d_50", "yamaha/dx7", "korg/m1"):
			assert sibling in said

	def test_the_page_offset_runs_the_other_way_from_most_of_the_corpus (self) -> None:
		"""A cover and a contents sheet carry no folio, so printed is one ahead of the sheet."""
		tr = pymidiinstrumentdefs.load("roland/tr_909", [CORPUS])

		assert tr.sources["manual"].page_offset == -1

		# The MIDI page is printed 38, which is the scan's 37th sheet.
		assert tr.sources["manual"].file_page(38) == 37

	def test_two_channels_whose_power_on_values_differ (self) -> None:
		"""Nought is omni on the receiving side and the transmitting side starts on 11."""
		tr = pymidiinstrumentdefs.load("roland/tr_909", [CORPUS])

		assert tr.midi.channels == (1, 16)

		said = prose_of("roland", "tr_909")

		assert "the receiving Channel is automatically set to 0, and the transmit Channel to 11." \
			in said
		assert "is Omni mode that receives all Channel information" in said

	def test_no_direction_is_recorded_for_any_message (self) -> None:
		"""Because the page says what can be communicated and never which way."""
		tr = pymidiinstrumentdefs.load("roland/tr_909", [CORPUS])

		assert tr.midi.clock is None
		assert tr.midi.transport is None
		assert tr.midi.program_change is None
		assert tr.midi.sysex is None
		assert tr.voice.addressing is None
		assert tr.voice.note_range is None
		assert tr.voice.velocity is None


class TestJU06A:

	"""A chart whose two pages are two whole maps, and only one of them is carried."""

	def test_only_the_sound_module_s_map_is_here (self) -> None:
		"""39 controls off page 1; page 2's 24 are in prose, because fifteen collide."""
		ju = pymidiinstrumentdefs.load("roland/ju_06a", [CORPUS])

		assert len(ju.controls) == 39

		said = prose_of("roland", "ju_06a")

		assert "Model: JU-06A (Control Surface Mode)" in said
		assert "FIFTEEN NUMBERS ARE IN BOTH AND ELEVEN OF THEM MEAN SOMETHING ELSE" in said

		# The six the comment tabulates are all page 1's meanings here, not page 2's.
		assert ju.controls["lfo_rate"].cc == 3
		assert ju.controls["vcf_freq"].cc == 74
		assert ju.controls["lfo_delay"].cc == 9
		assert ju.controls["vcf_res"].cc == 71

	def test_two_pairs_of_numbers_are_swapped_between_the_two_maps (self) -> None:
		"""Which is what catches a reader checking by name rather than by number."""
		said = prose_of("roland", "ju_06a")

		assert "`VCF FREQ` is cc 74 on page 1 and cc 3 on page 2 while `LFO RATE` is cc 3 on" \
			" page 1 and cc 29 on page 2" in said

	def test_three_controls_are_recognised_and_never_sent (self) -> None:
		"""The modulation wheel, the expression pedal and hold - and nothing the other way."""
		ju = pymidiinstrumentdefs.load("roland/ju_06a", [CORPUS])

		receiving = sorted(control.cc for control in ju.controls.values()
			if control.direction == "receives" and control.cc is not None)

		assert receiving == [1, 11, 64]

		# And nothing is transmitted without also being recognised, so the instrument never
		# sends a number it would not understand coming back.
		assert not [control for control in ju.controls.values()
			if control.direction == "transmits"]

	def test_two_documents_agree_about_the_patch_count_without_citing_each_other (self) -> None:
		"""The chart's program change range is 0-63 and the sound list names 64 patches."""
		ju = pymidiinstrumentdefs.load("roland/ju_06a", [CORPUS])

		assert ju.midi.program_change is not None
		assert ju.midi.program_change.presets == 64
		assert "sound_list" in ju.sources

	def test_four_voices_in_three_modes_and_a_bend_range_with_no_start (self) -> None:
		"""All from the manual, which is the only document that gives any of them."""
		ju = pymidiinstrumentdefs.load("roland/ju_06a", [CORPUS])

		assert ju.voice.polyphony == 4
		assert ju.voice.voicing_modes == (1, 4)
		assert ju.voice.aftertouch == "none"

		# The range is settable - it is `bend_range`, cc 87 - and no page says where it starts.
		assert ju.voice.pitch_bend is not None
		assert ju.voice.pitch_bend.programmable is True
		assert ju.voice.pitch_bend.semitones is None
		assert ju.controls["bend_range"].cc == 87

	def test_continue_is_answered_by_starting (self) -> None:
		"""A footnote the transport field has no room for."""
		ju = pymidiinstrumentdefs.load("roland/ju_06a", [CORPUS])

		assert ju.midi.transport == "both"

		said = prose_of("roland", "ju_06a")

		assert "*1 Same process as Start." in said


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


class TestSummit:

	"""The Peak's keyboard sibling, whose guide names sixty parameters it will not number."""

	def test_sixty_parameters_are_named_with_no_number_and_are_not_here (self) -> None:
		"""Slot 1 of the Modulation Matrix is numbered and slots 2 to 16 are blank.

		**The sibling's manual numbers all sixteen**, 1:0 to 16:3, and the two share an
		engine - so this is the one place in the corpus where the number a definition wants
		is published, and published in another instrument's document.
		"""
		summit = pymidiinstrumentdefs.load("novation/summit", [CORPUS])
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		# Slot 1 is here in full, as NRPN 1:0 to 1:3 recorded as MSB x 128 + LSB.
		for part, number in enumerate(("source1", "source2", "depth", "destination")):
			assert summit.controls[f"mod_matrix_1_{number}"].nrpn == 128 + part

		# And nothing from slot 2 upwards is here at all.
		for slot in range(2, 17):
			for number in ("source1", "source2", "depth", "destination"):
				assert f"mod_matrix_{slot}_{number}" not in summit.controls

				# The Peak has every one of them, which is what makes this an omission.
				assert peak.controls[f"mod_matrix_{slot}_{number}"].nrpn == \
					slot * 128 + ("source1", "source2", "depth", "destination").index(number)

	def test_one_hundred_and_eighty_nine_controls_in_the_table_s_own_sections (self) -> None:
		"""229 rows of the guide and 22 of the addendum, less the 62 that reach nothing."""
		summit = pymidiinstrumentdefs.load("novation/summit", [CORPUS])

		assert len(summit.controls) == 189
		assert len(summit.groups) == 11

		# The guide's own section headings, in the order it prints them, plus the two the
		# table gives no heading of its own.  `animate` is one the Peak's table does not have.
		assert list(summit.groups) == [
			"voice", "oscillators", "mixer", "filter", "envelopes", "lfos", "effects",
			"arp", "animate", "mod_matrix", "settings"]

		# One setting governs the whole table, so no control carries a direction of its own.
		assert all(c.direction == pymidiinstrumentdefs.definition.BOTH
			for c in summit.controls.values())

	def test_two_parts_with_eight_voices_each_out_of_sixteen (self) -> None:
		"""Sixteen voices in a Single Patch and a fixed eight per Part in a Multi."""
		summit = pymidiinstrumentdefs.load("novation/summit", [CORPUS])

		assert list(summit.parts) == ["part_a", "part_b"]

		for part in summit.parts.values():
			assert part.is_assigned
			assert part.polyphony == 8
			assert part.takes("notes")
			assert part.takes("controls")
			assert part.takes("program_change")

		# The allocation is fixed rather than drawn from a pool, so no figure is recorded for
		# the instrument and the voicing modes are the Single Patch's one or sixteen.
		assert summit.voice.polyphony_shared is False
		assert summit.voice.polyphony is None
		assert summit.voice.voicing_modes == (1, 16)

		# Every control is unparted: which channel reaches it is a mode, not a property of it.
		assert all(c.part is None for c in summit.controls.values())

	def test_velocity_arrives_and_does_nothing_until_a_patch_turns_it_up (self) -> None:
		"""Three envelope parameters start at zero, and the guide says what that means."""
		summit = pymidiinstrumentdefs.load("novation/summit", [CORPUS])

		assert summit.voice.velocity is not None
		assert summit.voice.velocity.note_on == "gated"
		assert summit.voice.velocity.gated_by == (
			"amp_envelope_velocity", "mod_envelope_1_velocity", "mod_envelope_2_velocity")

		# Each gate is a real control, and each starts in the middle of a signed range, which
		# is zero on the display - the value the guide says silences the touch response.  The
		# file omits the range because it is the whole of a controller's span, which the
		# loader fills back in, so writing it out would say nothing.
		for gate in summit.voice.velocity.gated_by:
			assert summit.controls[gate].default == 64
			assert summit.controls[gate].range == (0, 127)

		said = prose_of("novation", "summit")

		assert "If set to zero, the volume is the same regardless of how the keys are played" \
			in said

	def test_four_numbers_the_peak_left_out_on_this_instrument_s_evidence (self) -> None:
		"""The shared addendum marks what belongs to which, and these four are the Summit's."""
		summit = pymidiinstrumentdefs.load("novation/summit", [CORPUS])
		peak = pymidiinstrumentdefs.load("novation/peak", [CORPUS])

		# Aftertouch scaling, under "Update Features Exclusive to Summit".
		assert summit.controls["atouch_scale"].nrpn == 64 * 128 + 3
		assert summit.controls["atouch_scale"].range == (1, 10)
		assert "atouch_scale" not in peak.controls

		# And three FM NRPNs from a bug-fix list about voices 9 to 16.
		for msb, lsb, key in ((25, 13, "fm_osc3_1_manual_amount"),
				(25, 17, "fm_osc1_2_manual_amount"), (25, 21, "fm_osc2_3_manual_amount")):
			assert summit.controls[key].nrpn == msb * 128 + lsb
			assert key not in peak.controls

	def test_the_version_in_the_file_name_is_the_guide_s_edition_not_the_firmware (self) -> None:
		"""Which only another edition can show, because for the English one they agree."""
		summit = pymidiinstrumentdefs.load("novation/summit", [CORPUS])

		# The definition targets the addendum's firmware, not either guide edition.
		assert summit.model.firmware == "2.1"

		assert summit.sources["guide"].edition == "v1.1, for firmware v1.1"
		assert summit.sources["translation"].edition == "1.2"

		said = prose_of("novation", "summit")

		assert "the Italian is labelled version 1.2 and dated fourteen months later while" \
			" its own body sentence still gives the firmware as v1.1" in said

	def test_the_global_channel_s_default_is_stated_three_times_and_one_disagrees (self) -> None:
		"""So none is recorded, and the span is all the field holds anyway."""
		summit = pymidiinstrumentdefs.load("novation/summit", [CORPUS])

		assert summit.midi.channels == (1, 16)

		said = prose_of("novation", "summit")

		assert "Two witnesses say 1, one says 3" in said

	def test_the_sixty_blank_cells_were_checked_against_three_editions (self) -> None:
		"""Two languages over fourteen months, which is what makes it the maker's omission."""
		summit = pymidiinstrumentdefs.load("novation/summit", [CORPUS])

		# The two editions that are cited for an absence and quoted for nothing.
		assert set(summit.sources) == {
			"guide", "addendum", "translation", "second_edition", "download_page"}

		said = prose_of("novation", "summit")

		assert "no number of the form `2:0` to `16:3` occurs anywhere in any edition of this" \
			" guide that has a readable text layer" in said


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
		assert tracks.midi.transport == "both"
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

		# **IT WAS THE FIRST AND IS NO LONGER THE ONLY ONE.** The Korg Wavestation records mode 1
		# too, from its guide's own "When shipped, the Wavestation is set to MIDI Omni mode" - so
		# the claim this test made, that every other definition records omni off, became untrue
		# when the corpus grew, and it is narrowed to what is still true rather than dropped.
		omni_on = sorted(name for name in pymidiinstrumentdefs.available([CORPUS])
			if pymidiinstrumentdefs.load(name, [CORPUS]).midi.mode == 1)

		assert omni_on == ["korg/wavestation", "teenage_engineering/ep_133_ko_ii"]

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


class TestHydrasynthExplorer:

	"""An ASM whose maker prints its chart twice, and puts four parameters where it should not."""

	def test_one_hundred_and_ten_controls_in_twenty_nine_modules (self) -> None:
		"""Of 117 rows the chart prints: seven are set aside and the file says why."""
		explorer = pymidiinstrumentdefs.load("asm/hydrasynth_explorer", [CORPUS])

		assert len(explorer.controls) == 110
		assert len(explorer.groups) == 29

		numbers = [control.cc for control in explorer.controls.values() if control.cc is not None]

		assert len(numbers) == 110
		assert len(set(numbers)) == 110

	def test_four_parameters_sit_on_the_channel_mode_block_and_cannot_ship (self) -> None:
		"""The one real loss here, and the validator's own rule is what costs it.

		ASM puts ARP Octave on 120, ARP Length on 122, ENV4 Release on 124 and ENV4
		Sustain on 125 - All Sound Off, Local Control, Omni Off and Omni On.  The rule
		that keeps those out says they "mean the same on every instrument that has
		them", which this instrument makes untrue.
		"""
		explorer = pymidiinstrumentdefs.load("asm/hydrasynth_explorer", [CORPUS])

		numbers = {control.cc for control in explorer.controls.values()}

		for reserved in (120, 122, 123, 124, 125):
			assert reserved not in numbers, reserved

		account = " ".join((explorer.source or "").split())

		assert "FOUR PARAMETERS ARE PUT ON NUMBERS THE SPECIFICATION RESERVES" in account
		assert "moves its fourth envelope's release" in account

	def test_the_chart_is_printed_twice_and_that_is_what_checked_it (self) -> None:
		"""Same facts in two orders, by the maker - a free verification."""
		explorer = pymidiinstrumentdefs.load("asm/hydrasynth_explorer", [CORPUS])

		account = " ".join((explorer.source or "").split())

		assert "THE CHART IS PRINTED TWICE AND THAT IS WHAT VERIFIED IT" in account
		assert "AND THEY NAME NINETEEN PARAMETERS TWO WAYS" in account

		# The fuller printing's names are the ones shipped, and the pair that is
		# furthest apart is the one worth pinning.
		by_number = {control.cc: control for control in explorer.controls.values()}

		assert by_number[116].label == "Ring Mod FRate"
		assert by_number[74].label == "Filter 1 Cutoff"
		assert by_number[55].label == "Filter 2 Cutoff"

	def test_the_makers_own_spellings_are_kept (self) -> None:
		"""Including a label that ends in a full stop, which is the document's own."""
		explorer = pymidiinstrumentdefs.load("asm/hydrasynth_explorer", [CORPUS])

		by_number = {control.cc: control for control in explorer.controls.values()}

		assert by_number[1].label == "Modulation wheel."
		assert by_number[5].label == "GlidTime"
		assert by_number[117].label == "StWidth"

	def test_its_voices_take_a_channel_each (self) -> None:
		"""And this is the maker that says plainest what that means."""
		explorer = pymidiinstrumentdefs.load("asm/hydrasynth_explorer", [CORPUS])

		assert explorer.midi.per_voice_channels is True
		assert explorer.midi.channels == (1, 16)
		assert explorer.voice.polyphony == 8
		assert explorer.voice.aftertouch == "poly"

	def test_the_sibling_models_are_distinguished_from_a_chart_of_the_makers_own (self) -> None:
		"""Four Hydrasynths, three manuals, and one document that compares them."""
		explorer = pymidiinstrumentdefs.load("asm/hydrasynth_explorer", [CORPUS])

		assert set(explorer.sources) == {"manual", "comparison_chart"}
		assert explorer.sources["comparison_chart"].edition == "2.0.0"

		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "asm" / "hydrasynth_explorer.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "ASM MAKES FOUR HYDRASYNTHS AND THIS FILE DESCRIBES ONE" in flowed
		assert "MIDI In and Out where the other three have In, Out and Thru" in flowed

	def test_nrpn_is_offered_and_never_published (self) -> None:
		"""A setting makes it one of two formats, and no number is given for it."""
		explorer = pymidiinstrumentdefs.load("asm/hydrasynth_explorer", [CORPUS])

		assert explorer.midi.nrpn == "supported"

		for name, control in explorer.controls.items():
			assert control.nrpn is None, name

		account = " ".join((explorer.source or "").split())

		assert "NRPN IS OFFERED AND NOT PUBLISHED" in account


class TestFantom:

	"""A Roland workstation whose controller map is the MIDI specification's own."""

	def test_thirty_one_controls_and_every_one_a_standard_assignment (self) -> None:
		"""Roland invents none of these numbers, which is why the groups are the standard's.

		Modulation is 1, breath 2, foot 4, portamento time 5, volume 7, pan 10,
		expression 11 - the specification's assignments under the specification's names.
		"""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert len(fantom.controls) == 31
		assert len(fantom.groups) == 5

		by_number = {control.cc: control for control in fantom.controls.values()}

		assert by_number[1].label == "Modulation"
		assert by_number[7].label == "Volume"
		assert by_number[10].label == "Panpot"
		assert by_number[11].label == "Expression"
		assert by_number[64].label == "Hold 1"
		assert by_number[74].label == "Cutoff"

	def test_the_addressing_mechanisms_are_not_carried_as_controls (self) -> None:
		"""Bank select, data entry, the RPN selects and the velocity prefix address; they do not sound.

		The line is one step wider than the validator's own refusal of the channel mode
		messages, and the file draws it out loud rather than quietly.
		"""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		numbers = {control.cc for control in fantom.controls.values()}

		for mechanism in (0, 32, 6, 38, 88, 98, 99, 100, 101):
			assert mechanism not in numbers, mechanism

		for mode in range(120, 128):
			assert mode not in numbers, mode

		account = " ".join((fantom.source or "").split())

		assert "SIX NUMBERS ARE NOT CARRIED" in account

	def test_everything_travels_both_ways_and_the_document_says_why (self) -> None:
		"""Five are named only under reception, and that is not an asymmetry.

		Section 2 opens by saying the instrument can transmit any control change, and
		prints one numberless entry covering the range - so the five are covered, and
		nothing here is narrowed to `receives` on an omission.
		"""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		for name, control in fantom.controls.items():
			assert control.direction == "both", name

		account = " ".join((fantom.source or "").split())

		assert "can transmit any control change message" in account
		assert "SECTION 2 NAMES FIVE FEWER CONTROLLERS THAN SECTION 1" in account

	def test_the_one_line_that_contradicts_itself_is_recorded (self) -> None:
		"""`00H - 77H (0 - 31, 33 - 95)` - the hex is 0 to 119 and the gloss is 0 to 95."""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		account = " ".join((fantom.source or "").split())

		assert "CONTRADICTS ITSELF IN ONE CHARACTER" in account
		assert "is 0 to **119**, not 0 to" in account

	def test_the_chart_omits_a_controller_the_implementation_names (self) -> None:
		"""CC 17 is in the implementation twice and absent from the summary chart."""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		by_number = {control.cc: control for control in fantom.controls.values()}

		assert by_number[17].label == "General Purpose Controller 2"
		assert 16 in by_number and 18 in by_number

		account = " ".join((fantom.source or "").split())

		assert "DISAGREE ABOUT ONE CONTROLLER'S EXISTENCE" in account

	def test_sixteen_zones_each_of_which_may_sound_nothing (self) -> None:
		"""The same sixteen parts are the voices and the sixteen-channel MIDI output."""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert set(fantom.parts) == {"zone"}
		assert fantom.parts["zone"].count == 16
		assert fantom.parts["zone"].channel == "assigned"
		assert fantom.parts["zone"].receives == ("notes", "controls")

	def test_clock_and_transport_are_both_ways_by_two_different_sections (self) -> None:
		"""The sound generator receives clock; the sequencer sends it. Two charts, one instrument."""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert fantom.midi.clock == "both"
		assert fantom.midi.transport == "both"
		assert fantom.midi.mode == 3

		account = " ".join((fantom.source or "").split())
		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "roland" / "fantom_6_7_8.yaml").read_text().splitlines())

		assert "BOTH, BUT NOT BY THE SAME SECTION" in " ".join(flowed.split())
		assert account

	def test_nrpn_is_a_checked_absence_from_two_documents (self) -> None:
		"""No parameter named, no way to select one, and the chart marks 98 and 99 absent."""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert fantom.midi.nrpn == "none"
		assert fantom.midi.sysex is True

		account = " ".join((fantom.source or "").split())

		assert "NRPN IS A CHECKED ABSENCE, FROM BOTH DOCUMENTS AT ONCE" in account

	def test_both_pressures_are_received_and_the_field_holds_one_word (self) -> None:
		"""Poly is recorded, as the MC-707 does from the same maker, and channel is in the comment."""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert fantom.voice.aftertouch == "poly"
		assert fantom.voice.pitch_bend is not None
		assert fantom.voice.pitch_bend.programmable is True
		assert fantom.voice.pitch_bend.semitones is None
		assert fantom.voice.velocity is not None
		assert fantom.voice.velocity.note_off is True

	def test_the_firmware_is_the_newest_and_the_map_is_checked_across_all_seven (self) -> None:
		"""No document states a firmware, so seven supplements were read to establish it."""
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert fantom.model.firmware == "3.00"
		assert fantom.sources["implementation"].edition == "1.00"

		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "roland" / "fantom_6_7_8.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "all seven were fetched and read" in flowed.lower()
		assert "Not one adds, removes or renumbers a controller" in flowed

	def test_three_keyboards_one_definition_and_the_other_fantoms_are_not_it (self) -> None:
		"""Several generations share this name and only one of them is here."""
		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "roland" / "fantom_6_7_8.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "THREE KEYBOARDS, ONE DEFINITION" in flowed
		assert "the 2001 Fantom, the Fantom-S, -X and -G, and the FANTOM-0 are different" in flowed


class TestPolyBrute:

	"""An Arturia whose chart is eighteen tables three across, with columns that move."""

	def test_seventy_four_controls_in_eighteen_groups (self) -> None:
		"""One number per parameter, and every number distinct.

		Worth asserting for an instrument whose two parts divide a keyboard rather
		than a sound engine: nothing here needs a part to say what a number means,
		unlike the Rytm's 26 ambiguous numbers or the Syntakt's 28.
		"""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert len(poly.controls) == 74
		assert len(poly.groups) == 18

		numbers = [control.cc for control in poly.controls.values() if control.cc is not None]

		assert len(numbers) == 74
		assert len(set(numbers)) == 74

		for control in poly.controls.values():
			assert control.part is None

	def test_the_unused_numbers_are_mostly_the_ones_midi_reserves (self) -> None:
		"""Which is why a block of numbers that is not contiguous is worth asking about.

		The run 32 to 63 is absent entire, and it is the block the specification
		keeps for the fine halves of controllers 0 to 31 - so an instrument sending
		seven-bit values has no use for it.  That is an explanation, not a repair:
		the manual accounts for none of them and none is inferred.
		"""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		used = {control.cc for control in poly.controls.values() if control.cc is not None}
		missing = set(range(min(used), max(used) + 1)) - used

		assert set(range(32, 64)) <= missing
		assert missing - set(range(32, 64)) == {6, 20, 64, 74, 84, 88, 96, 97, 98, 99, 100, 101}

		# 64 sits next to that block and is absent for its own reason - it is the damper
		# pedal, and this instrument takes a sustain pedal on a jack rather than on a
		# controller. So the unbroken absence is 32 to 64 and it is two facts, not one.
		assert 64 in missing
		assert 65 not in missing

	def test_fourteen_names_need_their_table_to_tell_them_apart (self) -> None:
		"""`Rate` names four different things, so a key built from the name would collide."""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		labels: dict[str, int] = {}

		for control in poly.controls.values():

			if control.label is not None:
				labels[control.label] = labels.get(control.label, 0) + 1

		shared = {label for label, count in labels.items() if count > 1}

		assert len(shared) == 14
		assert labels["Rate"] == 4

		# And the four Rates are in four different groups, which is what makes them
		# four parameters rather than one read four times.
		rates = {control.group for control in poly.controls.values()
			if control.label == "Rate"}

		assert rates == {"lfo_1", "lfo_2", "lfo_3", "sequencer"}

	def test_the_two_parts_divide_a_keyboard_and_share_six_voices (self) -> None:
		"""They are parts because each has its own channels, not because the keyboard splits."""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert set(poly.parts) == {"upper", "lower"}

		for part in poly.parts.values():
			assert part.channel == "assigned"
			assert part.receives == ("notes", "controls")

		assert poly.voice.polyphony == 6
		assert poly.voice.polyphony_shared is True
		assert poly.voice.voicing_modes == (1, 6)

	def test_the_aftertouch_is_channel_pressure_whatever_duophonic_sounds_like (self) -> None:
		"""A setting that restricts which voices respond is not polyphonic pressure."""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert poly.voice.aftertouch == "channel"

		account = " ".join((poly.source or "").split())
		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "arturia" / "polybrute.yaml").read_text().splitlines())

		assert "duophonic option is NOT polyphonic pressure" in " ".join(flowed.split())
		assert account

	def test_the_firmware_is_unrecorded_and_the_manual_is_behind_the_instrument (self) -> None:
		"""The manual never says which firmware it covers, and a newer one is on offer."""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert poly.model.firmware is None
		assert poly.sources["manual"].edition == "3.0.1"
		assert poly.sources["manual"].dated == "2023-10-19"

		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "arturia" / "polybrute.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "THE MANUAL IS DEMONSTRABLY BEHIND THE INSTRUMENT" in flowed
		assert "ARTURIA SERVES DIFFERENT EDITIONS UNDER ONE HEADING" in flowed

	def test_the_sibling_is_not_covered_and_the_file_says_so (self) -> None:
		"""The PolyBrute 12 adds MPE per the survey, so one file cannot serve both."""
		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "arturia" / "polybrute.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "THE POLYBRUTE 12 IS NOT THIS INSTRUMENT" in flowed
		assert "The PolyBrute Noir is a finish and is covered" in flowed

	def test_the_source_account_says_how_the_chart_was_read (self) -> None:
		"""Because the next reader of a grid chart needs the trap, not the result."""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		account = " ".join((poly.source or "").split())

		assert "THE CHART IS A GRID OF EIGHTEEN SMALL TABLES, THREE ACROSS" in account
		assert "the column positions move from one block of rows to the next" in account
		assert "READING ACROSS ALSO MEANS THE RESULT HAS TO BE GATHERED" in account

	def test_four_numbers_mean_something_else_in_the_specification (self) -> None:
		"""A player meets this as a fault, so a panel should be able to warn about it.

		CC 7 is Channel Volume and here it is a filter level, so a sequencer sending a
		routine volume message moves the Steiner's output.
		"""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		by_number = {control.cc: control for control in poly.controls.values()}

		assert by_number[7].label == "Level"
		assert by_number[7].group == "steiner_filter"
		assert by_number[8].label == "Level"
		assert by_number[8].group == "ladder_filter"
		assert by_number[2].label == "Reverb Level"
		assert by_number[4].label == "Exp 2"

		# And four that do follow the specification, which is what makes the four above
		# look deliberate rather than careless.
		assert by_number[1].label == "Mod Wheel"
		assert by_number[5].label == "Glide"
		assert by_number[10].label == "Stereo"
		assert by_number[11].label == "Exp 1"

		account = " ".join((poly.source or "").split())

		assert "a sequencer sending a routine volume message will move a filter level" \
			in account.lower()

	def test_which_filter_is_vcf_one_is_settled_outside_the_chart (self) -> None:
		"""The chart heads its tables one way and routes its rows another, and cannot reconcile them."""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		by_number = {control.cc: control for control in poly.controls.values()}

		assert by_number[79].label == "VCO 2 > VCF 1"
		assert by_number[80].label == "Noise > VCF 2"
		assert by_number[79].group == by_number[80].group == "filter_fm"

		account = " ".join((poly.source or "").split())

		assert "THE CHART NAMES THE TWO FILTERS ONE WAY IN ITS HEADINGS" in account
		assert "CC 79 routes oscillator 2 into the **Steiner**" in account

	def test_the_survey_was_wrong_about_the_connectors_and_the_file_records_it (self) -> None:
		"""It said the manual does not name them; it names them twice and they agree."""
		poly = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		account = " ".join((poly.source or "").split())

		assert "names them twice" in account.lower()
		assert "MIDI In/Out/Thru" in account


class TestZeroCoast:

	"""A Make Noise whose maker publishes a control map and conditions most of it away."""

	def test_nineteen_controllers_in_the_order_the_manual_prints_them (self) -> None:
		"""Not ascending, which is the manual's own doing and is kept.

		Its table runs 117, 119, 118 and then 102 upward, so the two arpeggiator rows
		are split by the legato one.  Sorting them would be tidier and would stop a
		reader checking this file against the page it came from.
		"""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		assert len(coast.controls) == 19

		# Every one of them has a controller number, which is also what makes the list
		# below a complete reading of the page rather than a selection from it.
		printed = [control.cc for control in coast.controls.values() if control.cc is not None]

		assert len(printed) == 19
		assert printed == [5, 65, 117, 119, 118, 102, 103, 104, 105, 106, 107,
			108, 109, 110, 111, 112, 113, 114, 116]
		assert printed != sorted(printed)

	def test_one_hundred_and_fifteen_is_missing_and_is_not_filled_in (self) -> None:
		"""The block runs 102 to 119 with one hole, and the manual says nothing about it."""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		block = {control.cc for control in coast.controls.values()
			if control.cc is not None and control.cc >= 102}

		assert set(range(102, 120)) - block == {115}

	def test_nothing_is_sent_because_there_is_nothing_to_send_it_on (self) -> None:
		"""Sixty-one panel features and not one of them is a MIDI output."""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		for name, control in coast.controls.items():
			assert control.direction == "receives", name

		assert coast.midi.clock == "receives"

	def test_the_two_circuits_are_two_parts_and_only_one_sounds (self) -> None:
		"""MIDI B is a CV and gate pair for driving something else, on a channel of its own."""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		assert set(coast.parts) == {"midi_a", "midi_b"}

		for part in coast.parts.values():
			assert part.channel == "assigned"
			assert part.receives == ("notes", "controls")

		# Six controls belong to each, and seven to neither - the maker's own CH. A and
		# CH. B pairs, and the global settings that have no channel in their names.
		by_part: dict[str | None, int] = {}

		for control in coast.controls.values():
			by_part[control.part] = by_part.get(control.part, 0) + 1

		assert by_part == {None: 7, "midi_a": 6, "midi_b": 6}

	def test_one_voice_shared_rather_than_one_each (self) -> None:
		"""Using both parts at once gets you no more notes than using one."""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		assert coast.voice.polyphony == 1
		assert coast.voice.polyphony_shared is True

	def test_the_controls_with_no_program_page_are_marked (self) -> None:
		"""Nine of the nineteen can be reached by MIDI and by nothing else.

		The seven Program Pages offer a CV source and a gate source for MIDI B only, so
		the same two settings for MIDI A have no panel route at all, and neither have
		the six the maker calls additional nor the tempo divisor.
		"""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		only_over_midi = {control.cc for control in coast.controls.values()
			if control.panel_only}

		assert only_over_midi == {104, 106, 108, 109, 110, 111, 112, 113, 116}

	def test_pitch_bend_is_settable_and_aftertouch_is_unrecorded (self) -> None:
		"""Two fields, the same silence, and only one of them can hold it.

		CC 108 and 109 set the bend in semitones, which is what `programmable` says.
		CC 110 and 111 scale aftertouch in semitones, which says aftertouch arrives and
		not which kind - and the field names the kind, so it stays empty and the fact
		is in the source account.
		"""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		assert coast.voice.pitch_bend is not None
		assert coast.voice.pitch_bend.programmable is True
		assert coast.voice.pitch_bend.semitones is None
		assert coast.voice.aftertouch is None

		assert coast.voice.velocity is not None
		assert coast.voice.velocity.note_on == "received"

	def test_sysex_is_unrecorded_because_the_promised_section_is_empty (self) -> None:
		"""The manual names Sysex programming once and sends the reader to a page without any."""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		assert coast.midi.sysex is None

		account = " ".join((coast.source or "").split())

		assert "That section is p. 36 and it holds no system exclusive at all" in account

	def test_the_source_account_carries_the_condition_and_its_three_doubts (self) -> None:
		"""The whole difficulty of this instrument, which no field can hold."""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		account = " ".join((coast.source or "").split())

		assert "The 0-COAST will ignore these CC messages at all other times" in account
		assert "AND THE CONDITION CANNOT BE READ LITERALLY" in account
		assert "instructs a player to send a message it elsewhere says will be ignored" in account

	def test_the_row_that_is_not_text_is_recorded_as_such (self) -> None:
		"""Found only because the second reading rendered the page and looked at it."""
		coast = pymidiinstrumentdefs.load("make_noise/zero_coast", [CORPUS])

		account = " ".join((coast.source or "").split())

		assert "not in the text layer at all" in account
		assert "a maker's PDF can carry part of a table as artwork" in account

		flowed = " ".join(line.lstrip().lstrip("#").strip() for line
			in (CORPUS / "make_noise" / "zero_coast.yaml").read_text().splitlines())
		flowed = " ".join(flowed.split())

		assert "NEITHER THAT DESCRIPTION NOR THOSE VALUES ARE IN THE DOCUMENT'S TEXT LAYER" in flowed


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

	def test_four_instruments_declare_one_and_each_for_its_own_reason (self) -> None:
		"""Six pages in this corpus publish their numbers only as a picture, not one.

		Listed by name so that a fourth has to be added here deliberately: the declaration
		switches off the strongest check this corpus has, for the pages it names, so it
		should never spread quietly.

		**The three got there differently**, which is worth knowing before declaring a
		fourth.  The DrumBrute Impact's page 99 gives its drum map as a *screenshot of the
		maker's own editor*, in a manual of otherwise ordinary text.  The microKORG2's page
		133 is a MIDI Implementation Chart whose **type was converted to outlines** when the
		manual was made - 2,362 vector drawings and 79 characters where a reader sees a full
		page of numbers.  **The Nymphes's two are the plainest case and the largest**: its
		`8. CC List` is a PNG on each of two sheets, 13 characters of text between them, and
		82 controller numbers inside the images.

		A screenshot, a page of outlined type and a flat PNG look identical to a text search
		and need the same declaration.  **The Nymphes is also the first whose pictures are
		pinned by digest** - `Notes/4635_extract_nymphes.py` checks both images, so a redrawn
		table fails rather than letting a reading of the old one stand.  That is worth
		copying for any fourth.

		**And the fourth is the DrumBrute Impact's predecessor, with the same editor's
		screenshot in two editions of its manual.**  Version 1.2's page 73 is a crop of
		the whole window that version 1.0.0 prints on its page 70, so the two declarations
		name one picture twice - which is why both are declared, and why neither edition
		corroborates the other.  Its pictures are pinned by digest as the Nymphes's are.
		"""
		declared = {
			name: {key: source.pictured_pages
				for key, source in pymidiinstrumentdefs.load(name, [CORPUS]).sources.items()
				if source.pictured_pages}
			for name in pymidiinstrumentdefs.available([CORPUS])
		}

		assert {name: pages for name, pages in declared.items() if pages} == {
			"arturia/drumbrute": {"first_manual": (70,), "manual": (73,)},
			"arturia/drumbrute_impact": {"manual": (99,)},
			"dreadbox/nymphes": {"manual": (22, 23)},
			"korg/microkorg2": {"manual": (133,)},
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


class TestPresetCounts:

	"""What `presets` counts, which two definitions used to answer differently."""

	def test_presets_is_what_the_instrument_holds_not_what_one_message_reaches (self) -> None:
		"""An instrument that needs a bank select to reach the rest still records the rest.

		`midi.program_change.presets` is "how many it has".  Most instruments here that
		hold more than a program change can address record the whole number and explain
		the banks in a comment - the Carbon8M's 500 in five banks of a hundred, the
		MiniFreak's 512 in four banks of 128, the Sub 37's 256 in sixteen of sixteen.
		**Two Korgs recorded the hundred that one program change reaches instead**, so a
		consumer asking how many presets an instrument has got 500 from the Carbon8M and
		100 from the opsix for the same arrangement.  One answered one way and one the
		other is worse than neither, because it reads as settled and is wrong about one.

		The figures below are each the maker's own, from the specifications page of its
		own manual.
		"""
		holds = {
			"arturia/minifreak": 512,
			"korg/microkorg2": 256,
			"korg/minilogue": 200,
			"korg/minilogue_xd": 500,
			"korg/opsix": 500,
			"korg/wavestation": 150,
			"modal/carbon8m": 500,
			"moog/sub_37": 256,
			"moog/subsequent_37": 256,
			"sequential/prophet_10": 400,
			"sequential/prophet_5": 400,
			"sequential/prophet_6": 1000,
			"sequential/take_5": 256,
		}

		for name, expected in holds.items():
			definition = pymidiinstrumentdefs.load(name, [CORPUS])

			assert definition.midi.program_change is not None, name
			assert definition.midi.program_change.presets == expected, name

	def test_an_instrument_a_program_change_reaches_entirely_is_not_affected (self) -> None:
		"""The rule only bites where the instrument holds more than one message addresses.

		These three are right as they stand and must not be "corrected" to match the
		others: the modwave mk II's set list really is 64 slots, and the microKORG has
		no bank select at all.
		"""
		exact = {"korg/microkorg": 128, "korg/modwave_mk_ii": 64, "korg/wavestate": 64}

		for name, expected in exact.items():
			definition = pymidiinstrumentdefs.load(name, [CORPUS])

			assert definition.midi.program_change is not None, name
			assert definition.midi.program_change.presets == expected, name


def prose_of (maker: str, model: str) -> str:

	"""One definition's comments as running prose, with the # and the line breaks folded away.

	A comment wraps where the line runs out, so a sentence worth pinning is nearly always
	split across two lines and cannot be found in the file as it stands.
	"""

	text = (CORPUS / maker / f"{model}.yaml").read_text()

	return " ".join(line.lstrip("\t ").lstrip("#").strip() for line in text.splitlines())


class TestProphet6:

	"""A Sequential whose maker prints one appendix three times and agrees with itself nowhere."""

	def test_one_hundred_and_thirteen_controls_in_nineteen_panel_sections (self) -> None:
		"""Most parameters are reachable two ways, and seventy by NRPN alone."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		assert len(prophet.controls) == 113
		assert len(prophet.groups) == 19

		both = [control for control in prophet.controls.values()
			if control.cc is not None and control.nrpn is not None]
		cc_only = [control for control in prophet.controls.values()
			if control.cc is not None and control.nrpn is None]
		nrpn_only = [control for control in prophet.controls.values() if control.cc is None]

		assert (len(both), len(cc_only), len(nrpn_only)) == (38, 5, 70)

		# No number is used twice in either table.
		numbers = [control.cc for control in prophet.controls.values() if control.cc is not None]
		addresses = [control.nrpn for control in prophet.controls.values()
			if control.nrpn is not None]

		assert len(set(numbers)) == len(numbers)
		assert len(set(addresses)) == len(addresses)

	def test_the_five_controls_with_no_nrpn_are_the_ones_off_the_panel (self) -> None:
		"""A player's hands and feet: the maker's NRPN tables hold none of them."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		off_panel = sorted(control.cc for control in prophet.controls.values()
			if control.cc is not None and control.nrpn is None)

		assert off_panel == [1, 4, 7, 64, 74]

		for control in prophet.controls.values():

			if control.cc in off_panel:
				assert control.group == "performance"

	def test_the_two_numbers_the_document_gives_two_ranges_carry_none (self) -> None:
		"""The Global block is printed twice and disagrees with itself about two of its rows.

		MIDI Clock Mode is 0-3 on p. 78 and 0-4 on p. 80; MIDI Out Select is 0-3 and
		0-1.  Neither is recorded, because picking one would state a fact nobody has.
		Every other global carries the range both printings give it.
		"""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		disputed = {1027, 1033}

		for control in prophet.controls.values():

			if control.nrpn in disputed:
				assert control.range == (0, 127), control.label   # the format's own default

		by_address = {control.nrpn: control for control in prophet.controls.values()}

		assert by_address[1026].range == (0, 16)      # MIDI Channel, agreed
		assert by_address[1024].range == (0, 100)     # Master Fine Tune, agreed

		account = " ".join((prophet.source or "").split())

		assert "NEITHER RANGE IS RECORDED for those two" in account

	def test_the_maker_prints_this_appendix_three_times (self) -> None:
		"""Twice in the English manual and once more in the German, and that is the check."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		account = " ".join((prophet.source or "").split())

		assert "THE MAKER PRINTS THIS APPENDIX THREE TIMES AND NO TWO PRINTINGS AGREE" in account
		assert "WHAT THE GERMAN EDITION CAUGHT, AND WHAT IT HAS WRONG ITSELF" in account

		# The German edition is cited, which is what makes the comparison checkable.
		assert "handbuch" in prophet.sources
		assert prophet.sources["handbuch"].title == "Prophet-6 Handbuch"

	def test_the_control_nrpn_table_contradicts_the_program_table (self) -> None:
		"""Three of its four rows are program parameters with the same numbers and ranges.

		Only NRPN 1088, Seq Play/Stop, is taken from it; 1, 2 and 3 are recorded as
		the program parameters that two of the three printings say they are.
		"""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		by_address = {control.nrpn: control for control in prophet.controls.values()}

		assert by_address[1088].label == "Seq Play/Stop"
		assert by_address[1088].group == "sequencer"

		assert by_address[1].label == "Osc 1 Sync"
		assert by_address[2].label == "Osc 1 Level"
		assert by_address[3].label == "Osc 1 Shape"

		account = " ".join((prophet.source or "").split())

		assert "THE CONTROL NRPN TABLE CONTRADICTS ITSELF" in account

	def test_mpe_is_received_and_never_sent (self) -> None:
		"""The sixth instrument here with per-voice channels, and the first one way only."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		assert prophet.midi.per_voice_channels is True
		assert prophet.voice.polyphony == 6

		# Six voices on six channels, which is what the addendum says the flag means here.
		# The detail is in the file's comments, because a boolean cannot carry it.
		said = prose_of("sequential", "prophet_6")

		assert "doesn't output MPE from its own keyboard" in said
		assert "correspond to MIDI channels 2-7" in said

		flagged = sorted(name for name in pymidiinstrumentdefs.available([CORPUS])
			if pymidiinstrumentdefs.load(name, [CORPUS]).midi.per_voice_channels)

		assert "sequential/prophet_6" in flagged

		# The OB-X8 joined them at #4477: MPE is a value of its MIDI Channel global.
		assert "oberheim/ob_x8" in flagged

		# And the Leviasynth, whose MPE takes the channel settings away rather than
		# sitting beside them. The Osmose's test above carries what each of the eleven is.
		assert "asm/leviasynth" in flagged

		# **The Protein is the eleventh, and the only one whose channel count for MPE is the
		# player's to set**: "Here you can determine the number of used channels for MPE
		# purposes." So this boolean covers an instrument that takes some channels and one
		# that takes as many as somebody says.
		assert "waldorf/protein" in flagged

		# The twelfth, whose MPE is a state of its channel menu rather than a setting beside it.
		assert "dreadbox/nymphes" in flagged
		# The thirteenth, whose MPE is a global setting and which, like this one, answers to MPE
		# and sends none: "the 3rd Wave doesn't output MPE from its own keyboard".
		assert "groove_synthesis/third_wave" in flagged
		assert len(flagged) == 13

	def test_nrpn_is_preferred_as_it_is_on_the_other_sequential (self) -> None:
		"""Word for word the same sentence in both implementations, so it is the maker's."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])
		take_5 = pymidiinstrumentdefs.load("sequential/take_5", [CORPUS])

		assert prophet.midi.nrpn == "preferred"
		assert take_5.midi.nrpn == "preferred"

		# Six definitions say `preferred`, and five of them are this one company -
		# Sequential, and the Oberheim it builds - which is what makes it a house position
		# rather than one instrument's. The Prophet-5's implementation puts it in a callout
		# rather than in the body, and the words are the same again. The Fourm, four years
		# later than the Prophet-6, still says it in the user guide rather than the
		# implementation, and says it about the same two things: the range NRPN covers and
		# the 128 a controller is limited to.
		preferred = sorted(name for name in pymidiinstrumentdefs.available([CORPUS])
			if pymidiinstrumentdefs.load(name, [CORPUS]).midi.nrpn == "preferred")

		assert preferred == ["elektron/digitone_ii", "groove_synthesis/third_wave", "oberheim/ob_x8", "oberheim/teo_5",
			"sequential/fourm", "sequential/prophet_10", "sequential/prophet_5",
			"sequential/prophet_6", "sequential/take_5"]

	def test_one_file_covers_the_keyboard_and_the_module (self) -> None:
		"""The maker treats them as one instrument, and says so on its own download page."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		assert prophet.model.name == "Prophet-6"

		said = prose_of("sequential", "prophet_6")

		assert "ONE DEFINITION, TWO INSTRUMENTS" in said
		assert "the Prophet-6 keyboard and desktop module" in said

	def test_a_thousand_programs_in_ten_banks_half_of_them_permanent (self) -> None:
		"""Five user banks and five factory banks, a hundred programs each."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		assert prophet.midi.program_change is not None
		assert prophet.midi.program_change.receives is True
		assert prophet.midi.program_change.sends is True
		assert prophet.midi.program_change.presets == 1000

	def test_transport_is_received_and_the_file_says_how_that_was_settled (self) -> None:
		"""The maker never says it outright; one clock mode says what it does not do."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_6", [CORPUS])

		assert prophet.midi.clock == "both"
		assert prophet.midi.transport == "receives"

		said = prose_of("sequential", "prophet_6")

		assert "does not respond to MIDI Start or Stop command" in said
		assert "RECEIVES ONLY, and said by implication rather than outright" in said


class TestMinilogue:

	"""A Korg whose implementation is a text file, and whose maker prints it twice five years apart."""

	def test_thirty_nine_controls_in_ten_panel_sections (self) -> None:
		"""Of 44 rows the receiving table prints: five are set aside and the file says why."""
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])

		assert len(minilogue.controls) == 39
		assert len(minilogue.groups) == 10

		numbers = sorted(control.cc for control in minilogue.controls.values()
			if control.cc is not None)

		assert len(numbers) == 39
		assert len(set(numbers)) == 39
		assert numbers[0] == 16 and numbers[-1] == 88

		# Bank select and the three channel mode messages are the five left out.
		for set_aside in (0, 32, 120, 122, 123):
			assert set_aside not in numbers, set_aside

	def test_it_is_not_the_minilogue_xd (self) -> None:
		"""Two instruments, one name, and the corpus has both - so each says which it is."""
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])
		xd = pymidiinstrumentdefs.load("korg/minilogue_xd", [CORPUS])

		assert minilogue.model.name == "minilogue"
		assert xd.model.name == "minilogue xd"

		# They are different instruments and the numbers say so: the xd has NRPN and this
		# has none, the xd holds 500 programs and this 200.
		assert minilogue.midi.nrpn == "none"
		assert xd.midi.nrpn == "supported"

		assert minilogue.midi.program_change is not None
		assert minilogue.midi.program_change.presets == 200

		said = prose_of("korg", "minilogue")

		assert "NOT THE minilogue xd, WHICH IS A DIFFERENT INSTRUMENT" in said

	def test_every_value_it_sends_lands_in_the_band_it_reads (self) -> None:
		"""The implementation describes a switch twice, and the two were checked against each other.

		Sending, it gives the exact values; receiving, the bands.  They are not the same
		arithmetic - the four-way switches band in quarters and are sent as 0, 42, 84, 127,
		and the three-way ones band in thirds and are sent as 0, 64, 127 - so 42 and 84 look
		like thirds boundaries and are read against quarters.
		"""
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])

		stepped = [control for control in minilogue.controls.values() if control.values]

		assert len(stepped) == 13

		by_number = {control.cc: control for control in minilogue.controls.values()}

		assert by_number[48].values == {"ft_16": 0, "ft_8": 32, "ft_4": 64, "ft_2": 96}
		assert by_number[50].values == {"sqr": 0, "tri": 43, "saw": 86}
		assert by_number[84].values == {"pole_2": 0, "pole_4": 64}

		# Every band starts where the one before it ends, with nothing uncovered.
		for control in stepped:
			starts = sorted(control.values.values())

			assert starts[0] == 0, control.label
			assert starts == list(control.values.values()), control.label

	def test_the_implementations_names_are_the_ones_shipped (self) -> None:
		"""The manual's chart abbreviates seven, and two of its abbreviations mislead."""
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])

		by_number = {control.cc: control for control in minilogue.controls.values()}

		assert by_number[82].label == "CUTOFF VELOCITY"
		assert by_number[83].label == "CUTOFF KEYBOARD TRACK"
		assert by_number[84].label == "CUTOFF TYPE"
		assert by_number[27].label == "VOICE MODE DEPTH"

		said = prose_of("korg", "minilogue")

		assert "THE TWO PRINTINGS AGREE ON EVERY NUMBER" in said
		assert "The names are not confirmed twice" in said

	def test_the_older_document_is_stale_about_its_own_switches (self) -> None:
		"""Right about every number and wrong about the conditions, which is the lesson."""
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])

		said = prose_of("korg", "minilogue")

		assert "OUT OF DATE ABOUT HOW ITS OWN MESSAGES ARE SWITCHED ON" in said
		assert "No such setting exists on this instrument" in said

		# Both documents are cited, because the claim rests on the pair of them.
		assert set(minilogue.sources) == {"midi_impl", "manual", "downloads"}
		assert minilogue.sources["midi_impl"].paginated is False

	def test_two_checked_absences_the_successor_does_not_have (self) -> None:
		"""No NRPN and no aftertouch, both from the maker's own rows rather than from silence."""
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])

		assert minilogue.midi.nrpn == "none"
		assert minilogue.voice.aftertouch == "none"

		assert minilogue.midi.clock == "both"
		assert minilogue.midi.transport == "both"
		assert minilogue.midi.mode == 3

	def test_portamento_is_on_the_panel_and_has_no_controller (self) -> None:
		"""The slider reaches it and MIDI does not, which the successor changed."""
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])
		xd = pymidiinstrumentdefs.load("korg/minilogue_xd", [CORPUS])

		assert 5 not in {control.cc for control in minilogue.controls.values()}
		assert 5 in {control.cc for control in xd.controls.values()}

		said = prose_of("korg", "minilogue")

		assert "PORTAMENTO has no controller number at all" in said

	def test_four_voices_and_three_note_counts_the_maker_states (self) -> None:
		"""Eight voice modes, and only four of them described as a number of notes."""
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])

		assert minilogue.voice.polyphony == 4
		assert minilogue.voice.voicing_modes == (1, 2, 4)
		assert minilogue.voice.note_range == (0, 127)


class TestMC101:

	"""A Roland whose chart is published in editions, one of which is missing."""

	def test_twenty_eight_controls_from_two_documents (self) -> None:
		"""Twenty-five on the chart and three the chart has never carried."""
		mc_101 = pymidiinstrumentdefs.load("roland/mc_101", [CORPUS])

		assert len(mc_101.controls) == 28
		assert len(mc_101.groups) == 7

		numbers = sorted(control.cc for control in mc_101.controls.values()
			if control.cc is not None)

		assert len(numbers) == 28
		assert len(set(numbers)) == 28

		# The three the update notes name and the chart does not.
		for added in (2, 4, 93):
			assert added in numbers, added

	def test_it_publishes_the_same_numbers_as_its_bigger_sibling (self) -> None:
		"""Four tracks against eight, and one control map between them - bar one name.

		The two instruments publish the same twenty-eight controller numbers, and
		twenty-seven of them carry the same name.  **CC 93 is the exception, and it is
		the one number neither chart prints**: the MC-707's reference manual names it
		outright, "Delay Send Level (CC#93)", and the MC-101's reference gives no number
		for any send at all, so the only name this instrument has for it is the update
		notes' own setting, `Rx ChoDlySend`.  Each is labelled from the document that
		defines it, which is why they differ.
		"""
		mc_101 = pymidiinstrumentdefs.load("roland/mc_101", [CORPUS])
		mc_707 = pymidiinstrumentdefs.load("roland/mc_707", [CORPUS])

		here = {control.cc: control.label for control in mc_101.controls.values()
			if control.cc is not None}
		there = {control.cc: control.label for control in mc_707.controls.values()
			if control.cc is not None}

		assert sorted(here) == sorted(there)

		differ = {number for number in here if here[number] != there[number]}

		assert differ == {93}
		assert here[93] == "Rx ChoDlySend"
		assert there[93] == "Delay Send Level"

		assert mc_101.parts["track"].count == 4
		assert mc_707.parts["track"].count == 8

	def test_only_the_four_knob_numbers_are_transmitted (self) -> None:
		"""Everything else is received and never sent, by the chart's own columns."""
		mc_101 = pymidiinstrumentdefs.load("roland/mc_101", [CORPUS])

		sent = [control.cc for control in mc_101.controls.values()
			if control.cc is not None and control.direction != "receives"]

		assert sorted(sent) == [80, 81, 82, 83]

	def test_the_control_channel_takes_no_control_change (self) -> None:
		"""A channel that makes no sound: scenes by program change, the Scatter Pad by note."""
		mc_101 = pymidiinstrumentdefs.load("roland/mc_101", [CORPUS])

		assert set(mc_101.parts) == {"track", "control"}

		control = mc_101.parts["control"]

		assert control.count == 1
		assert control.channel == "assigned"
		assert sorted(control.receives or ()) == ["notes", "program_change"]

		track = mc_101.parts["track"]

		assert sorted(track.receives or ()) == ["controls", "notes", "program_change"]

	def test_the_missing_chart_edition_is_recorded (self) -> None:
		"""eng01 and eng03 exist and eng02 does not, so one firmware step is unprinted."""
		mc_101 = pymidiinstrumentdefs.load("roland/mc_101", [CORPUS])

		assert "chart" in mc_101.sources
		assert "chart_1_00" in mc_101.sources
		assert mc_101.sources["chart"].edition == "eng03"
		assert mc_101.sources["chart_1_00"].edition == "eng01"

		account = " ".join((mc_101.source or "").split())

		assert "TWO EDITIONS OF THE CHART EXIST AND THE MIDDLE ONE DOES NOT" in account
		assert "THE CHART SHOWS IN ONE STEP WHAT THE INSTRUMENT DID IN TWO" in account

	def test_two_checked_absences_and_one_refusal (self) -> None:
		"""No NRPN anywhere in five documents; system exclusive left unrecorded."""
		mc_101 = pymidiinstrumentdefs.load("roland/mc_101", [CORPUS])

		assert mc_101.midi.nrpn == "none"
		assert mc_101.midi.sysex is None

		said = prose_of("roland", "mc_101")

		assert "nowhere in any of this instrument's five documents" in said
		assert "NOT RECORDED, BECAUSE TWO DOCUMENTS CONTRADICT EACH OTHER" in said

	def test_it_cites_another_instruments_chart_for_one_sentence (self) -> None:
		"""The MC-707's footnote is the maker saying where CC 83 comes from."""
		mc_101 = pymidiinstrumentdefs.load("roland/mc_101", [CORPUS])

		assert "sibling_chart" in mc_101.sources
		assert mc_101.sources["sibling_chart"].title == "MC-707 MIDI Implementation Chart"

		said = prose_of("roland", "mc_101")

		assert "for MC-101 compatibility." in said


class TestPolyendTracker:

	"""A tracker with two received maps, live in different modes, and one controller in neither."""

	def test_eighty_controls_in_two_maps (self) -> None:
		"""Thirty-two for performance and the mixer, forty-eight for the instrument."""
		tracker = pymidiinstrumentdefs.load("polyend/tracker", [CORPUS])

		assert len(tracker.controls) == 80
		assert len(tracker.groups) == 9

		numbers = [control.cc for control in tracker.controls.values() if control.cc is not None]

		assert len(numbers) == 80
		assert len(set(numbers)) == 80

	def test_the_two_maps_share_no_number (self) -> None:
		"""Which map is live depends on a mode, so an overlap would be unsayable.

		`performance_effects` and `master` answer whenever CC In is on; everything else
		answers only in MIDI Synthesizer mode with the sequencer stopped.  This format
		has no field for that, and the only reason it can list both at once is that no
		controller number is in both.
		"""
		tracker = pymidiinstrumentdefs.load("polyend/tracker", [CORPUS])

		always = {control.cc for control in tracker.controls.values()
			if control.group in ("performance_effects", "master")}
		synth = {control.cc for control in tracker.controls.values()
			if control.group not in ("performance_effects", "master")}

		assert len(always) == 32
		assert len(synth) == 48
		assert not (always & synth)

		said = prose_of("polyend", "tracker")

		assert "TWO MAPS, AND WHICH ONE IS LIVE DEPENDS ON A MODE RATHER THAN ON A CHANNEL" in said

	def test_the_controller_that_is_in_neither_table (self) -> None:
		"""Panning is on the instrument's own screen and not in the manual's table."""
		tracker = pymidiinstrumentdefs.load("polyend/tracker", [CORPUS])

		by_number = {control.cc: control for control in tracker.controls.values()}

		assert by_number[10].label == "Panning"
		assert by_number[10].group == "instrument"

		# The whole panning envelope is there, which is what makes the gap visible.
		for envelope in range(26, 32):
			assert by_number[envelope].group == "panning"

		said = prose_of("polyend", "tracker")

		assert "THE ONE CONTROLLER THAT IS NOT IN EITHER TABLE" in said
		assert "Panning = 10" in said

	def test_nothing_is_transmitted (self) -> None:
		"""The outgoing side is six slots the player fills, so it is a setting not a map."""
		tracker = pymidiinstrumentdefs.load("polyend/tracker", [CORPUS])

		for control in tracker.controls.values():
			assert control.direction == "receives", control.label

		said = prose_of("polyend", "tracker")

		assert "NOTHING BELOW IS TRANSMITTED" in said

	def test_the_maker_did_not_write_this_manual (self) -> None:
		"""A third party's book that Polyend publishes as the official reference.

		**The ellipsis in the quotation is not decoration.** The colophon sets the typesetter's
		web address below the name, and the page's text layer returns it *between* "by" and
		"Synthdawg" - so the words a reader takes in at one glance are not one string in the
		file, and quoting them unbroken failed the quotation gate the moment the locator became
		readable at all. Both extractors agree on that ordering, so it is the page and not a
		bad reading of it.
		"""
		tracker = pymidiinstrumentdefs.load("polyend/tracker", [CORPUS])

		said = prose_of("polyend", "tracker")

		assert "THIS MANUAL IS NOT WRITTEN BY POLYEND" in said
		assert "Manual Produced in the United Kingdom by ... Synthdawg" in said
		assert "the ellipsis is the typesetter's web address" in said

	def test_pitch_bend_is_a_checked_absence (self) -> None:
		"""The words do not occur in 308 pages, and nor does MPE."""
		tracker = pymidiinstrumentdefs.load("polyend/tracker", [CORPUS])

		assert tracker.voice.pitch_bend is None
		assert tracker.midi.per_voice_channels is None
		assert tracker.midi.nrpn == "none"

		said = prose_of("polyend", "tracker")

		assert "PITCH BEND IS A CHECKED ABSENCE" in said

	def test_what_it_sends_and_will_not_say_on_what_number (self) -> None:
		"""Program change goes out as a step effect, and two pages give it two numbers."""
		tracker = pymidiinstrumentdefs.load("polyend/tracker", [CORPUS])

		assert tracker.midi.program_change is not None
		assert tracker.midi.program_change.sends is True
		assert tracker.midi.program_change.receives is None

		said = prose_of("polyend", "tracker")

		assert "AND THE MANUAL CONTRADICTS ITSELF ABOUT WHICH NUMBER PROGRAM CHANGE IS" in said

	def test_the_order_is_the_makers_and_not_numeric (self) -> None:
		"""The synthesizer map follows the instrument's own screen, which is the evidence."""
		tracker = pymidiinstrumentdefs.load("polyend/tracker", [CORPUS])

		run = [control.cc for control in tracker.controls.values()
			if control.group == "instrument"]

		assert run == [5, 3, 7, 10, 9, 1, 11, 12, 13, 14, 15, 16, 17]


class TestCircuit:

	"""A Novation whose guide prints seventy-four rows twice and leaves thirty-nine out."""

	def test_two_hundred_and_ninety_nine_controls_in_three_parts (self) -> None:
		"""233 for a synth, 28 for the drums, 38 for the session."""
		circuit = pymidiinstrumentdefs.load("novation/circuit", [CORPUS])

		assert len(circuit.controls) == 299
		assert len(circuit.groups) == 15
		assert set(circuit.parts) == {"synth", "drums", "session"}

		per = collections.Counter(control.part for control in circuit.controls.values())

		assert per == {"synth": 233, "drums": 28, "session": 38}

	def test_it_is_not_the_circuit_tracks (self) -> None:
		"""Two instruments, one family, and the corpus has both."""
		circuit = pymidiinstrumentdefs.load("novation/circuit", [CORPUS])
		tracks = pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS])

		assert circuit.model.name == "Circuit"
		assert tracks.model.name == "Circuit Tracks"

		# The Tracks adds two MIDI tracks this has not, and more controls with them.
		assert set(tracks.parts) - set(circuit.parts) == {"midi_track", "project"}
		assert len(tracks.controls) > len(circuit.controls)

		said = prose_of("novation", "circuit")

		assert "NOT THE CIRCUIT TRACKS, WHICH IS A DIFFERENT INSTRUMENT" in said

	def test_the_guide_prints_seventy_four_rows_twice (self) -> None:
		"""Every repeat identical, so nothing is lost but the counting."""
		circuit = pymidiinstrumentdefs.load("novation/circuit", [CORPUS])

		said = prose_of("novation", "circuit")

		assert "THE GUIDE PRINTS SEVENTY-FOUR OF ITS 307 SYNTH ROWS MORE THAN ONCE" in said
		assert "Every repeat is identical in every cell" in said

		# No parameter is listed twice under one part AND one section.  Six names do repeat
		# within the session, and that is the guide's doing rather than a reprint: the six
		# send levels are printed once under Reverb and again under Delay, on different
		# numbers.  The section is what tells those apart, which is why it is in the key.
		labels = [(control.part, control.group, control.label)
			for control in circuit.controls.values()]

		assert len(set(labels)) == len(labels)

		repeated = [control.label for control in circuit.controls.values()
			if control.group == "delay" and "send level" in control.label]

		assert len(repeated) == 6

	def test_thirty_nine_rows_the_guide_leaves_out (self) -> None:
		"""The reprint replaced content rather than adding it, and nothing is invented.

		Macro knobs 1 and 2 are absent, macro knob 3 begins four rows in, and mod matrix
		11 has no destination.  The missing numbers are predictable from the pattern -
		the macro positions run CC 83 to 87 for knobs 4 to 8 - and predicting a
		controller number is not reading one, so none is recorded.
		"""
		circuit = pymidiinstrumentdefs.load("novation/circuit", [CORPUS])

		macros = sorted(control.label for control in circuit.controls.values()
			if control.label.lower().startswith("macro knob"))

		assert not [name for name in macros if name.startswith(("macro knob 1", "macro knob 2"))]
		assert "macro knob 3 depth A" in macros
		assert "macro knob 3 position" not in macros
		assert "macro knob 4 position" in macros

		destinations = {control.label for control in circuit.controls.values()}

		assert "mod matrix 10 destination" in destinations
		assert "mod matrix 11 destination" not in destinations

		said = prose_of("novation", "circuit")

		assert "AND THE REPRINT DID NOT ADD CONTENT, IT REPLACED IT" in said

	def test_two_nrpn_addresses_carry_ten_parameters (self) -> None:
		"""The value says which switch, and each control's range is what tells them apart."""
		circuit = pymidiinstrumentdefs.load("novation/circuit", [CORPUS])

		shared = collections.defaultdict(list)

		for control in circuit.controls.values():

			if control.nrpn is not None and control.part == "synth":
				shared[control.nrpn].append(control)

		twice = {number: held for number, held in shared.items() if len(held) > 1}

		assert sorted(twice) == [122, 123]
		assert len(twice[122]) == 8
		assert len(twice[123]) == 2

		# Every one of the ten has a range of its own, and none of them overlap.
		for number, held in twice.items():
			spans = sorted(control.range for control in held)

			for before, after in zip(spans, spans[1:]):
				assert before[1] < after[0], (number, before, after)

	def test_the_session_is_on_a_channel_a_player_cannot_move (self) -> None:
		"""Tracks take 1 to 15 and the session keeps 16."""
		circuit = pymidiinstrumentdefs.load("novation/circuit", [CORPUS])

		assert circuit.midi.channels == (1, 15)

		said = prose_of("novation", "circuit")

		assert "Channel 16 is reserved for the session" in said
		assert circuit.parts["session"].receives == ("controls", "program_change")
		assert circuit.parts["synth"].polyphony == 6

	def test_the_guide_is_stale_about_its_own_channels (self) -> None:
		"""It is the newer document and it describes the older instrument."""
		circuit = pymidiinstrumentdefs.load("novation/circuit", [CORPUS])

		said = prose_of("novation", "circuit")

		assert "THE GUIDE IS OUT OF DATE ABOUT ITS OWN CHANNELS, AND IT IS THE NEWER DOCUMENT" \
			in said
		assert "update_1_8" in circuit.sources
		assert circuit.sources["guide"].edition == "1.3"

	def test_it_cites_two_uploads_of_one_guide (self) -> None:
		"""The same version served twice, listed once, and identical in text."""
		circuit = pymidiinstrumentdefs.load("novation/circuit", [CORPUS])

		assert "guide_other_upload" in circuit.sources
		assert circuit.sources["guide"].edition == circuit.sources["guide_other_upload"].edition
		assert circuit.sources["guide"].sha256 != circuit.sources["guide_other_upload"].sha256

		said = prose_of("novation", "circuit")

		assert "NOVATION SERVES THIS GUIDE TWICE AT ONE NAME" in said


class TestPerkonsHD01:

	"""An Erica Synths drum machine whose map a player can rewrite on the SD card."""

	def test_forty_four_controls_in_four_voices (self) -> None:
		"""Eleven each, on an unbroken run of controller numbers."""
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		assert len(perkons.controls) == 44
		assert len(perkons.groups) == 4
		assert not perkons.parts

		per = collections.Counter(control.group for control in perkons.controls.values())

		assert per == {"voice_1": 11, "voice_2": 11, "voice_3": 11, "voice_4": 11}

		numbers = sorted(control.cc for control in perkons.controls.values()
			if control.cc is not None)

		assert numbers == list(range(70, 114))

	def test_each_voice_holds_one_block_of_eleven (self) -> None:
		"""The page is read down its columns, so a voice's numbers are consecutive."""
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		blocks = {"voice_1": (70, 80), "voice_2": (81, 91),
			"voice_3": (92, 102), "voice_4": (103, 113)}

		for group, (low, high) in blocks.items():

			mine = sorted(control.cc for control in perkons.controls.values()
				if control.group == group and control.cc is not None)

			assert mine == list(range(low, high + 1))

	def test_the_map_is_a_factory_assignment_the_player_can_rewrite (self) -> None:
		"""A file on the SD card, not MIDI learn, and the file says so on its face."""
		said = prose_of("erica_synths", "perkons_hd_01")

		assert "THE NUMBERS ARE A FACTORY ASSIGNMENT AND THE PLAYER CAN REWRITE THEM" in said
		assert "single-midi-cc.json" in said

		# `learned` would be wrong here: there is a published map, and it is this one.
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		assert perkons.midi.control_change is None
		assert not perkons.midi.learns_control_change

	def test_the_other_channel_mode_is_recorded_in_words (self) -> None:
		"""Four voices on four channels, answering to voice 1's eleven numbers."""
		said = prose_of("erica_synths", "perkons_hd_01")

		assert "TWO MAPS AGAIN, AND THIS TIME ONE IS THE OTHER'S FIRST QUARTER" in said
		assert "THIS FORMAT HAS NO FIELD FOR A MAP THAT IS LIVE IN ONE MODE ONLY" in said

	def test_the_note_numbers_are_not_in_print (self) -> None:
		"""Four note names and no octave, so there is nothing to record."""
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		assert perkons.voice is not None
		assert perkons.voice.addressing == "voices"
		assert perkons.voice.voices == {}
		assert perkons.voice.note_range is None

		said = prose_of("erica_synths", "perkons_hd_01")

		assert "THE FOUR NOTE NUMBERS ARE NOT IN PRINT" in said

	def test_the_switches_have_no_states_because_none_are_printed (self) -> None:
		"""Three positions each, all named, and no value given for any of them."""
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		switches = [control for control in perkons.controls.values()
			if control.name.endswith(("_algo_switch", "_mode_switch", "_filter_switch"))]

		assert len(switches) == 12

		for switch in switches:
			assert switch.states == []
			assert switch.kind == pymidiinstrumentdefs.CONTINUOUS

	def test_velocity_arrives_but_a_setting_gates_it (self) -> None:
		"""Nothing to name as the gate, because the gate is not a control."""
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		assert perkons.voice is not None
		assert perkons.voice.velocity is not None
		assert perkons.voice.velocity.note_on == "gated"
		assert perkons.voice.velocity.gated_by == ()

	def test_it_holds_presets_and_no_program_change_reaches_them (self) -> None:
		"""Sixty-four banks of sixty-four, and no way in from outside."""
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		assert perkons.midi.program_change is None

		said = prose_of("erica_synths", "perkons_hd_01")

		assert "no preset count is recorded here at all" in said

	def test_the_firmware_is_named_and_the_absence_of_a_later_one_is_evidenced (self) -> None:
		"""A news run of seventy-five posts is what lets this file name 1.2."""
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		assert perkons.model.firmware == "1.2"
		assert "news_listing" in perkons.sources
		assert set(perkons.sources) == {"manual", "firmware_1_2", "firmware_1_1",
			"firmware_1_0", "news_listing"}

		said = prose_of("erica_synths", "perkons_hd_01")

		assert "AND 1.2 IS STILL THE NEWEST" in said

	def test_it_was_the_first_erica_synths_instrument_here_and_taught_nothing_reusable (self) \
			-> None:
		"""No habits of this maker were known before it - and the next one broke them."""
		perkons = pymidiinstrumentdefs.load("erica_synths/perkons_hd_01", [CORPUS])

		assert perkons.model.manufacturer == "Erica Synths"
		assert perkons.model.name == "PĒRKONS HD-01"

		erica = sorted(path.stem for path in (CORPUS / "erica_synths").glob("*.yaml"))

		assert erica == ["hexdrums", "perkons_hd_01"]

		# **THIS MAKER CHANGED HOW IT PUBLISHES BETWEEN THE TWO**, which is the whole value of
		# having learned its habits here: the PĒRKONS's manual sits at a direct address naming
		# the file, and the HexDrums's arrives from a download controller that takes a product
		# id and a file id and names the file only in a header. So the lesson a reader should
		# take from either definition is about that instrument, not about Erica Synths.
		hexdrums = pymidiinstrumentdefs.load("erica_synths/hexdrums", [CORPUS])

		assert "erp.ericasynths.lv/media/PERKONS" in (perkons.sources["manual"].url or "")
		assert "/service/file/download/" in (hexdrums.sources["manual"].url or "")


class TestMiniNova:

	"""A Novation whose implementation guide has no controller number in it."""

	def test_five_hundred_and_fifty_seven_controls_in_eighty_five_groups (self) -> None:
		"""The chart's own Category column, every one of its values."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		assert len(mininova.controls) == 557
		assert len(mininova.groups) == 85
		assert not mininova.parts

	def test_the_controllers_and_the_nrpns_are_two_different_sets (self) -> None:
		"""Not one map addressed twice, which is the usual arrangement and not this one."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		by_cc = [control for control in mininova.controls.values() if control.cc is not None]
		by_nrpn = [control for control in mininova.controls.values() if control.nrpn is not None]
		both = [control for control in mininova.controls.values()
			if control.cc is not None and control.nrpn is not None]

		assert len(by_cc) == 105
		assert len(by_nrpn) == 452
		assert both == []

		said = prose_of("novation", "mininova")

		assert "THE CONTROL CHANGES AND THE NRPNS ARE TWO DIFFERENT SETS OF PARAMETERS" in said

	def test_the_three_channel_mode_rows_are_left_out (self) -> None:
		"""The chart lists them and they belong to the specification, not to one synthesiser."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		numbers = {control.cc for control in mininova.controls.values()}

		assert not numbers & {120, 122, 123}

		said = prose_of("novation", "mininova")

		assert "THREE OF THE CHART'S ROWS ARE NOT CONTROLS AND ARE LEFT OUT" in said

		# The unusual values the chart gives Local Off/On survive in the prose, because a player
		# who sent 0 or 127 would get nothing.
		assert "99=On" in said and "33=Off" in said

	def test_two_nrpn_addresses_carry_thirty_six_parameters (self) -> None:
		"""The value says which switch, and each control's range is what tells them apart."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		shared = collections.defaultdict(list)

		for control in mininova.controls.values():

			if control.nrpn is not None:
				shared[control.nrpn].append(control)

		twice = {number: held for number, held in shared.items() if len(held) > 1}

		assert sorted(twice) == [122, 251]
		assert len(twice[122]) == 30
		assert len(twice[251]) == 6

		# On 122 no two bands overlap, which is the arrangement working.
		bands = sorted(control.range for control in twice[122])

		for earlier, later in zip(bands, bands[1:]):
			assert earlier[1] < later[0]

	def test_the_one_row_whose_own_columns_disagree_keeps_no_names (self) -> None:
		"""Its named values fall outside its own range, so neither reading is recorded."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		insert = mininova.controls["vocaltune_insert"]

		assert insert.range == (25, 27)
		assert insert.choices == {}
		assert insert.values == {}

		said = prose_of("novation", "mininova")

		assert "AND NRPN 251 IS THE ONE PLACE THIS CHART CONTRADICTS ITSELF" in said

	def test_a_borrowed_set_of_names_moves_onto_its_own_range (self) -> None:
		"""A pointer lends names and not numbers."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		first = mininova.controls["lfo_1_oneshot"]
		third = mininova.controls["lfo_3_oneshot"]

		assert first.choices == {"normal": 12, "oneshot": 13}
		assert third.choices == {"normal": 32, "oneshot": 33}
		assert third.range == (32, 33)

	def test_three_rows_are_a_family_rather_than_a_parameter (self) -> None:
		"""Their NRPN LSB column holds a range, and the row says what each number in it addresses."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		gator = [name for name in mininova.controls if name.startswith("gator_step_")]
		spectra = [name for name in mininova.controls if name.startswith("vocoder_spectrum_")]
		keys = [name for name in mininova.controls if name.startswith("chorder_key_")]

		assert len(gator) == 32
		assert len(spectra) == 32
		assert len(keys) == 9

		# Consecutive addresses, which is what the chart says they are.
		for family in (gator, spectra, keys):

			numbers = sorted(mininova.controls[name].nrpn or 0 for name in family)

			assert numbers == list(range(numbers[0], numbers[0] + len(numbers)))

		# The chorder's first key is Key 2, because Key 1 is the root and is not addressed.
		assert "chorder_key_1" not in mininova.controls
		assert "chorder_key_2" in mininova.controls

	def test_the_keyboard_octave_wraps_rather_than_spanning (self) -> None:
		"""Printed `(124 - 4)`, which is not a range, so the control keeps the whole of one."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		octave = mininova.controls["voice_keyboardoctave"]

		assert octave.range == (0, 127)
		assert octave.choices["minus_4_octaves"] == 124
		assert octave.choices["plus_4_octaves"] == 4
		assert len(octave.choices) == 9

	def test_it_holds_three_banks_of_a_hundred_and_twenty_eight (self) -> None:
		"""What the instrument holds, not what one program change reaches."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		assert mininova.midi.program_change is not None
		assert mininova.midi.program_change.presets == 384
		assert mininova.voice is not None
		assert mininova.voice.polyphony == 18
		assert mininova.voice.aftertouch == "channel"

	def test_no_firmware_is_recorded_and_none_is_published (self) -> None:
		"""Three version numbers in the sources and not one of them is the instrument's."""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		assert mininova.model.firmware is None
		assert mininova.sources["chart"].edition == "0002"
		assert mininova.sources["midi_impl"].edition == "0001"
		assert mininova.sources["manual"].edition == "1.01"
		assert "downloads" in mininova.sources

		said = prose_of("novation", "mininova")

		assert "None of them\n  # is a firmware number." in \
			(CORPUS / "novation" / "mininova.yaml").read_text()

	def test_it_is_none_of_the_other_novations (self) -> None:
		"""Seven of them now, and the UltraNova is an eighth this does not describe.

		**Three of the seven are Circuits**, and the oldest name is a prefix of the other
		two, so the listing is by name rather than by anything that could match a substring.
		The Summit and the Peak share an engine and are two definitions, which is the maker's
		own division: one is a keyboard with two of the other's synth core in it.
		"""
		mininova = pymidiinstrumentdefs.load("novation/mininova", [CORPUS])

		assert mininova.model.name == "MiniNova"

		novations = sorted(path.stem for path in (CORPUS / "novation").glob("*.yaml"))

		assert novations == ["bass_station_ii", "circuit", "circuit_rhythm", "circuit_tracks",
			"mininova", "peak", "summit"]

		said = prose_of("novation", "mininova")

		assert "The UltraNova is the larger synthesiser this one is derived from" in said


class TestVolcaBeats:

	"""A Korg whose chart draws its marks and leaves three of its ten parts out of a footnote."""

	def test_twenty_controls_in_an_unbroken_run (self) -> None:
		"""Forty to fifty-nine, and every one of them only receives."""
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])

		assert len(beats.controls) == 20

		numbers = sorted(control.cc for control in beats.controls.values()
			if control.cc is not None)

		assert numbers == list(range(40, 60))

		for control in beats.controls.values():
			assert control.direction == "receives"

	def test_the_groups_are_the_makers_prefixes_and_one_control_has_none (self) -> None:
		"""Inventing a group for a single control would invent a grouping the maker has not."""
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])

		assert set(beats.groups) == {"part_level", "pcm_speed", "stutter", "decay"}

		per = collections.Counter(control.group for control in beats.controls.values())

		assert per == {"part_level": 10, "pcm_speed": 4, "decay": 3, "stutter": 2, None: 1}
		assert beats.controls["hat_grain"].group is None

	def test_the_ten_parts_have_notes_and_the_charts_footnote_has_seven (self) -> None:
		"""The text file has all ten; a reader of the chart alone could not play three of them."""
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])

		assert beats.voice is not None
		assert beats.voice.addressing == "voices"
		assert beats.voice.voices == {"kick": 36, "snare": 38, "clap": 39, "cl_hat": 42,
			"lo_tom": 43, "op_hat": 46, "crash": 49, "hi_tom": 50, "agogo": 67, "claves": 75}

		# Every part with a level has a note and the other way round, which is the cross-check
		# that found the footnote short.
		levelled = {control.label.split("(")[1].rstrip(")").replace(" ", "_")
			for control in beats.controls.values() if control.group == "part_level"}

		assert levelled == set(beats.voice.voices)

		said = prose_of("korg", "volca_beats")

		assert "AND THE CHART IS SHORT BY THREE PARTS WHERE THE TEXT FILE IS NOT" in said

	def test_the_note_range_is_the_true_voice_row (self) -> None:
		"""Recognised is 0 to 127 and only ten numbers inside 36 to 75 do anything."""
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])

		assert beats.voice is not None
		assert beats.voice.note_range == (36, 75)
		assert beats.voice.plays_note(36) and beats.voice.plays_note(75)
		assert not beats.voice.plays_note(35) and not beats.voice.plays_note(76)

	def test_velocity_comes_from_the_text_file_because_the_charts_cell_cannot_be_read (self) -> None:
		"""A cross and a value together in one cell, and the other document settles it."""
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])

		assert beats.voice is not None
		assert beats.voice.velocity is not None
		assert beats.voice.velocity.note_on == "received"
		assert beats.voice.velocity.note_off is False

		said = prose_of("korg", "volca_beats")

		assert "a cross and a value" in said

	def test_it_sends_nothing_at_all (self) -> None:
		"""Which is a fact about the sockets rather than about the implementation."""
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])

		assert beats.midi.clock == "receives"
		assert beats.midi.transport == "receives"
		assert beats.midi.program_change is not None
		assert beats.midi.program_change.sends is False
		assert beats.midi.program_change.receives is False
		assert beats.midi.program_change.presets is None

		said = prose_of("korg", "volca_beats")

		assert "not equipped with a MIDI Out jack" in said

	def test_the_checked_absences (self) -> None:
		"""Each one a cross in both of the chart's columns, or a word searched for and not found."""
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])

		assert beats.midi.sysex is False
		assert beats.midi.nrpn == "none"
		assert beats.voice is not None
		assert beats.voice.aftertouch == "none"
		assert beats.voice.pitch_bend is None
		assert beats.voice.polyphony is None

	def test_no_firmware_is_recorded_because_a_system_update_changed_what_is_charted (self) -> None:
		"""The volca drum's reasoning over again, and the same maker."""
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])
		drum = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		assert beats.model.firmware is None
		assert drum.model.firmware is None
		assert "updater" in beats.sources
		assert beats.sources["updater"].edition == "1.04"

		said = prose_of("korg", "volca_beats")

		assert "Fixes MIDI Song Position Pointer." in said

	def test_the_charts_marks_are_drawings (self) -> None:
		"""Which is why both readings of it were made by eye."""
		said = prose_of("korg", "volca_beats")

		assert "THE PLAIN TEXT FILE IS THE BETTER DOCUMENT" in said
		assert "not in its text layer at all" in said


class TestVolcaBass:

	"""An instrument with no MIDI Out jack, whose maker says so rather than leaving a blank."""

	def test_every_control_only_arrives (self) -> None:
		"""Twelve of them, and the implementation gives the reason in its second line."""
		bass = pymidiinstrumentdefs.load("korg/volca_bass", [CORPUS])

		assert len(bass.controls) == 12
		assert all(control.direction == "receives" for control in bass.controls.values())

		said = prose_of("korg", "volca_bass")

		assert "No message is transmitted." in said
		assert "The volca bass is not equipped with a MIDI Out jack." in said

		# Which is a checked absence in both documents: one says it in a sentence and the
		# other by thirty identical marks.
		assert "thirty crosses in the Transmitted column and not one circle" in said

	def test_three_controls_reach_what_the_panel_cannot (self) -> None:
		"""The chart's `*3`, and the manual never prints two of the three names."""
		bass = pymidiinstrumentdefs.load("korg/volca_bass", [CORPUS])

		for key, number in (("slide_time", 5), ("expression", 11), ("gate_time", 49)):
			assert bass.controls[key].cc == number
			assert bass.controls[key].group == "performance"

		said = prose_of("korg", "volca_bass")

		assert "Cannot be changed with machine operations; can only be changed with MIDI." in said

		# **AND THE FORMAT HAS NO WORD FOR IT.** `panel_only` says the opposite, so none of
		# the three carries it and the prose has to.
		assert not any(control.panel_only for control in bass.controls.values())
		assert "there is no field for a control a message reaches that the panel" in said

	def test_the_octave_bands_are_the_only_value_map_either_document_gives (self) -> None:
		"""Six bands over the whole span, from the implementation's own `*2` table."""
		bass = pymidiinstrumentdefs.load("korg/volca_bass", [CORPUS])

		assert bass.controls["octave"].values == {
			"oct_1": 0, "oct_2": 22, "oct_3": 44, "oct_4": 66, "oct_5": 88, "oct_6": 110}

		# And nothing else here names a value at all.
		assert [key for key, control in bass.controls.items() if control.values] == ["octave"]
		assert not any(control.choices for control in bass.controls.values())

	def test_what_the_chart_settles_as_a_checked_absence (self) -> None:
		"""Four crosses in both columns, which is different from four silences."""
		bass = pymidiinstrumentdefs.load("korg/volca_bass", [CORPUS])

		assert bass.midi.sysex is False
		assert bass.midi.nrpn == "none"
		assert bass.voice.aftertouch == "none"

		assert bass.midi.program_change is not None
		assert bass.midi.program_change.receives is False
		assert bass.midi.program_change.sends is False

		# And what it settles positively.
		assert bass.midi.channels == (1, 16)
		assert bass.midi.mode == 3
		assert bass.midi.clock == "receives"
		assert bass.midi.transport == "receives"

	def test_polyphony_is_not_recorded_although_there_are_three_oscillators (self) -> None:
		"""The grouping the manual describes is a property of sequences, not of MIDI notes."""
		bass = pymidiinstrumentdefs.load("korg/volca_bass", [CORPUS])

		assert bass.voice.polyphony is None
		assert bass.voice.voicing_modes == ()

		# The three oscillators are three controls, which is as far as the documents go.
		for index in (1, 2, 3):
			assert bass.controls[f"vco_pitch_{index}"].group == "oscillators"

		said = prose_of("korg", "volca_bass")

		assert "VCOs grouped together are activated by the same sequence data" in said
		assert "No page of any of the three documents says how many" in said

	def test_the_two_documents_disagree_about_one_footnote (self) -> None:
		"""Recorded and not resolved, because nothing in the file turns on it."""
		bass = pymidiinstrumentdefs.load("korg/volca_bass", [CORPUS])

		said = prose_of("korg", "volca_bass")

		assert "carries no footnote at all" in said

		# Pitch bend has no block here at all, which is why the disagreement costs nothing.
		assert bass.voice.pitch_bend is None


class TestMonologue:

	"""A Korg whose map is printed twice, one way round each, and the two are not the same."""

	def test_twenty_four_controls_in_the_makers_panel_sections (self) -> None:
		"""Seven groups, from its own specification's list of synthesis parameters."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])

		assert len(monologue.controls) == 24
		assert list(monologue.groups) == ["master", "vco_1", "vco_2", "mixer", "filter", "eg", "lfo"]

		numbers = sorted(control.cc for control in monologue.controls.values()
			if control.cc is not None)

		assert numbers == [16, 17, 24, 25, 26, 28, 34, 35, 36, 37, 39, 40,
			43, 44, 48, 49, 50, 51, 56, 58, 59, 60, 61, 62]

	def test_two_controls_are_received_only_because_the_panel_cannot_send_them (self) -> None:
		"""VCO 2 has a pitch and an octave control and VCO 1 has neither."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])

		receives = sorted(name for name, control in monologue.controls.items()
			if control.direction == "receives")

		assert receives == ["vco_1_octave", "vco_1_pitch"]

		# Their VCO 2 counterparts go both ways.
		assert monologue.controls["vco_2_pitch"].direction == "both"
		assert monologue.controls["vco_2_octave"].direction == "both"

		said = prose_of("korg", "monologue")

		assert "none for VCO 1" in said

	def test_the_named_values_are_the_bands_it_answers_to (self) -> None:
		"""It sends three exact numbers and answers to three bands, and the bands are recorded."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])

		assert monologue.controls["vco_1_wave"].values == {"sqr": 0, "tri": 43, "saw": 86}
		assert monologue.controls["vco_2_wave"].values == {"noise": 0, "tri": 43, "saw": 86}
		assert monologue.controls["vco_2_octave"].values == {"n16": 0, "n8": 32, "n4": 64, "n2": 96}

		# Every number it sends falls inside the band it would be read back in.
		assert monologue.controls["vco_1_wave"].values["tri"] <= 64 <= 85

	def test_one_control_carries_choices_because_its_footnote_is_unprinted (self) -> None:
		"""The document refers to *5-6 and never prints it, so its bands are not invented."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])

		mode = monologue.controls["lfo_mode"]

		assert mode.cc == 59
		assert mode.values == {}
		assert mode.choices == {"n1_shot": 0, "slow": 64, "fast": 127}

		# It is the only one in the file shaped that way.
		assert [name for name, control in monologue.controls.items() if control.choices] \
			== ["lfo_mode"]

		said = prose_of("korg", "monologue")

		assert "WHOSE BANDS THE MAKER REFERS TO AND DOES NOT PRINT" in said

	def test_the_newer_of_its_two_midi_documents_is_inside_the_manual (self) -> None:
		"""Korg publishes no chart for this one, and the manual has one on p. 58."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])

		assert set(monologue.sources) == {"midi_impl", "manual", "downloads", "updater"}
		assert monologue.sources["midi_impl"].edition == "1.00"
		assert monologue.sources["manual"].edition == "E 3"

		said = prose_of("korg", "monologue")

		assert "THE NEWER ONE IS INSIDE THE MANUAL" in said

	def test_a_firmware_is_named_and_three_documents_were_needed_to_do_it (self) -> None:
		"""Where the two volcas could not, this one could."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])
		beats = pymidiinstrumentdefs.load("korg/volca_beats", [CORPUS])
		drum = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])

		assert monologue.model.firmware == "2.00"
		assert beats.model.firmware is None
		assert drum.model.firmware is None
		assert monologue.sources["updater"].edition == "2.00"

		said = prose_of("korg", "monologue")

		assert "support for MIDI set position messages" in said

	def test_it_is_monophonic_and_holds_a_hundred_programs (self) -> None:
		"""One voice, and a program change reaches every one of them."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])

		assert monologue.voice is not None
		assert monologue.voice.polyphony == 1
		assert monologue.midi.program_change is not None
		assert monologue.midi.program_change.presets == 100
		assert monologue.midi.program_change.receives is True
		assert monologue.midi.program_change.sends is True

	def test_what_it_sends_and_answers_to_are_not_symmetrical (self) -> None:
		"""It answers to a continue it will never send."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])

		assert monologue.midi.clock == "both"
		assert monologue.midi.transport == "both"

		said = prose_of("korg", "monologue")

		assert "it answers to a continue it will never send" in said

	def test_the_checked_absences_and_the_settable_bend (self) -> None:
		"""Each from the chart's own rows, and a bend range set separately in each direction."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])

		assert monologue.midi.nrpn == "none"
		assert monologue.midi.sysex is True
		assert monologue.voice is not None
		assert monologue.voice.aftertouch == "none"
		assert monologue.voice.pitch_bend is not None
		assert monologue.voice.pitch_bend.programmable is True
		assert monologue.voice.pitch_bend.semitones is None

	def test_it_is_not_the_minilogue (self) -> None:
		"""Two instruments, one family, and the corpus has three of them."""
		monologue = pymidiinstrumentdefs.load("korg/monologue", [CORPUS])
		minilogue = pymidiinstrumentdefs.load("korg/minilogue", [CORPUS])

		assert monologue.model.name == "monologue"
		assert minilogue.model.name == "minilogue"

		assert monologue.voice is not None and minilogue.voice is not None
		assert monologue.voice.polyphony == 1
		assert minilogue.voice.polyphony == 4

		# And they do not answer to the same numbers.
		mine = {control.cc for control in monologue.controls.values()}
		theirs = {control.cc for control in minilogue.controls.values()}

		assert mine != theirs


class TestS1:

	"""A Roland whose chart gives ranges with no names and whose list gives names with no direction."""

	def test_fifty_four_controls_from_two_tables (self) -> None:
		"""The chart's thirteen ranges expand to exactly the list's fifty-four numbers."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert len(s1.controls) == 54
		assert len(s1.groups) == 9

		numbers = sorted(control.cc for control in s1.controls.values() if control.cc is not None)

		assert numbers[0] == 1 and numbers[-1] == 107
		assert len(numbers) == len(set(numbers))

		said = prose_of("roland", "s_1")

		assert "TWO TABLES, AND NEITHER WOULD DO ON ITS OWN" in said

	def test_six_controls_are_received_and_never_sent (self) -> None:
		"""Six of the chart's thirteen Control Change rows are x transmitted and o received."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		receives = sorted(control.cc for control in s1.controls.values()
			if control.direction == "receives" and control.cc is not None)

		assert receives == [1, 10, 11, 64, 65, 77]

	def test_two_controls_are_told_apart_by_a_drawing (self) -> None:
		"""Both read OSC LEVEL and the waveform between the brackets is the only difference."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert s1.controls["osc_level_19"].cc == 19
		assert s1.controls["osc_level_20"].cc == 20
		assert s1.controls["osc_level_19"].label == s1.controls["osc_level_20"].label

		said = prose_of("roland", "s_1")

		assert "TWO CONTROLS HAVE THE SAME NAME AND THE MAKER TELLS THEM APART WITH A DRAWING" in said
		assert "19's is a pulse wave and 20's is a sawtooth" in said

	def test_it_answers_on_two_channels_at_once (self) -> None:
		"""One for the synth, one for the program changes that change patterns."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert set(s1.parts) == {"synth", "pattern"}
		assert s1.parts["synth"].channel == "assigned"
		assert s1.parts["pattern"].channel == "assigned"
		assert s1.parts["synth"].receives == ("notes", "controls")
		assert s1.parts["pattern"].receives == ("program_change",)
		assert s1.midi.channels == (1, 16)

	def test_the_voices_are_the_synths_and_are_stated_there (self) -> None:
		"""Only one of the two parts sounds, so the figure is said once where it is true."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert s1.voice is not None
		assert s1.voice.polyphony is None
		assert s1.voice.polyphony_shared is False
		assert s1.parts["synth"].polyphony == 4
		assert s1.parts["pattern"].polyphony is None

	def test_it_answers_to_a_transport_it_cannot_be_told_to_resume (self) -> None:
		"""Start and stop are o in both columns and continue is x in both."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert s1.midi.transport == "both"
		assert s1.midi.clock == "both"

		said = prose_of("roland", "s_1")

		assert "it answers to a transport it cannot be told to resume" in said

	def test_the_checked_absences (self) -> None:
		"""Each from the chart's own rows, or a word searched for across seventy-five pages."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert s1.midi.sysex is False
		assert s1.midi.nrpn == "none"
		assert s1.midi.mode == 3
		assert s1.voice is not None
		assert s1.voice.aftertouch == "none"
		assert s1.voice.pitch_bend is None
		assert s1.voice.velocity is not None
		assert s1.voice.velocity.note_off is False

	def test_it_holds_sixty_four_patterns_and_the_chart_agrees (self) -> None:
		"""Four banks of sixteen, and a True Number of 0 to 63."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert s1.midi.program_change is not None
		assert s1.midi.program_change.presets == 64
		assert s1.midi.program_change.receives is True
		assert s1.midi.program_change.sends is True

	def test_it_cites_two_uploads_of_one_manual (self) -> None:
		"""The same version served twice, listed once, and identical in text."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert "manual_other_upload" in s1.sources
		assert s1.sources["manual"].edition == s1.sources["manual_other_upload"].edition
		assert s1.sources["manual"].sha256 != s1.sources["manual_other_upload"].sha256

		said = prose_of("roland", "s_1")

		assert "TRYING THE NUMBERS FOUND AN UNLISTED EDITION, AND IT IS THE SAME DOCUMENT" in said

	def test_no_firmware_is_recorded_and_none_is_published (self) -> None:
		"""A manual version is not a firmware number, and Roland publishes neither for this one."""
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert s1.model.firmware is None
		assert s1.sources["manual"].edition == "1.02"

		said = prose_of("roland", "s_1")

		assert "No firmware number appears anywhere in it" in said


class TestP6:

	"""A Roland whose chart names no controller number and whose list names forty."""

	# The forty numbers the control change list prints a parameter for, in the list's order.
	LIST = [3, 7, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 28, 29, 30,
		68, 71, 72, 73, 74, 75, 76, 77, 78, 79, 84, 85, 86, 87, 88, 89, 90, 91, 92]

	def test_forty_controls_from_the_list_and_none_from_the_chart (self) -> None:
		"""The chart's one Control Change row points at the list, which is the only place a number is."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		assert len(p6.controls) == 40
		assert sorted(control.cc for control in p6.controls.values() if control.cc is not None) == self.LIST
		assert {control.direction for control in p6.controls.values()} == {"both"}

		said = prose_of("roland", "p_6")

		assert "THE CHART POINTS AT THE LIST AND NAMES NOTHING ITSELF" in said
		assert "every control below is `both` on the strength of that one row" in said

	def test_the_dashes_and_the_elisions_are_not_carried (self) -> None:
		"""Four rows print a dash for their parameter and seven print a colon for numbers left out."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		numbers = {control.cc for control in p6.controls.values()}

		assert not numbers & {0, 11, 22, 27}

		said = prose_of("roland", "p_6")

		assert "four that print a dash in place of one - 0, 11, 22 and 27" in said

	def test_the_groups_are_the_sections_each_entry_cites (self) -> None:
		"""Every list entry cites the page its parameter is set on, and the page's section is the group."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		assert p6.groups == {"voice": "VOICE", "filter": "FILTER", "mixer": "MIXER",
			"lo_fi": "Lo-Fi", "delay_reverb": "DELAY/REVERB"}

		counts = collections.Counter(control.group for control in p6.controls.values())

		assert counts == {"voice": 21, "filter": 6, "mixer": 7, "lo_fi": 2, "delay_reverb": 4}

		# The one name its own page does not print: p. 12 calls it the [LO-Fi] button.
		assert p6.controls["lo_fi_switch"].label == "Lo-Fi Switch"
		assert "That page never calls it a switch." in prose_of("roland", "p_6")

	def test_four_channels_each_settable (self) -> None:
		"""Granular sampler, sample pads, auto and pattern, with the chart's four defaults."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		assert list(p6.parts) == ["granular", "sample_pads", "auto", "pattern"]
		assert all(part.channel == "assigned" for part in p6.parts.values())
		assert p6.parts["granular"].receives == ("notes", "controls")
		assert p6.parts["sample_pads"].receives == ("notes",)
		assert p6.parts["auto"].receives == ("notes", "controls")
		assert p6.parts["pattern"].receives == ("program_change",)
		assert p6.midi.channels == (1, 16)

	def test_the_controllers_moved_channel_in_the_firmware_it_describes (self) -> None:
		"""1.01 took them on the auto channel alone; 1.02 on the granular sampler's as well."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		assert p6.model.firmware == "1.02"
		assert p6.sources["release_notes"].edition == "Ver.1.02"
		assert {control.part for control in p6.controls.values()} == {"granular"}
		assert p6.parts["auto"].takes("controls")

		said = prose_of("roland", "p_6")

		assert "For ver. 1.01, this data is received only when the receive channel is set to 15 (auto)." in said
		assert "Changed the MIDI CC so that it can be received by both Auto Channel and Granular Ch." in said

	def test_a_note_picks_a_pad_on_one_channel_and_a_pitch_on_another (self) -> None:
		"""The sample pads read a note as a pad, the auto channel as a pitch, and nothing says how the granular one reads it."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		assert p6.parts["sample_pads"].addressing == "voices"
		assert p6.parts["auto"].addressing == "pitches"
		assert p6.parts["granular"].addressing is None

		# Only the two ends of the pads' span are printed, so no pad is given a note.
		assert p6.voice is not None
		assert p6.voice.voices == {}
		assert p6.voice.note_range is None

		said = prose_of("roland", "p_6")

		assert "Which note reaches which pad between those two ends is not printed anywhere" in said

	def test_each_part_that_sounds_has_voices_of_its_own (self) -> None:
		"""Sixteen for the sample pads and four for the granular sampler, stated where each is true."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		assert p6.voice is not None
		assert p6.voice.polyphony is None
		assert p6.voice.polyphony_shared is False
		assert p6.parts["sample_pads"].polyphony == 16
		assert p6.parts["granular"].polyphony == 4
		assert p6.parts["auto"].polyphony is None
		assert p6.parts["pattern"].polyphony is None

	def test_nine_stepped_parameters_stay_continuous (self) -> None:
		"""Each chooses between named settings on the instrument, and no value is tied to any of them."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		stepped = ["sample", "filter_type", "auto_pan", "grain_shape", "start_mode",
			"t_env_mode", "amp_switch", "output_bus_select", "lo_fi_switch"]

		for name in stepped:
			control = p6.controls[name]

			assert control.kind == "continuous", name
			assert control.range == (0, 127), name

		assert all(not control.values and not control.choices for control in p6.controls.values())

	def test_the_checked_absences (self) -> None:
		"""From the chart's own rows, and a sweep of 152 pages squashed to letters and digits."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])

		assert p6.midi.sysex is False
		assert p6.midi.nrpn == "none"
		assert p6.midi.mode == 3
		assert p6.midi.clock == "both"
		assert p6.midi.transport == "both"
		assert p6.voice is not None
		assert p6.voice.aftertouch == "none"
		assert p6.voice.pitch_bend is None
		assert p6.voice.velocity is not None
		assert p6.voice.velocity.note_on == "received"
		assert p6.voice.velocity.note_off is False

	def test_continue_is_received_and_does_what_start_does (self) -> None:
		"""The chart prints that inside the received column's cell, under its o, and not among the remarks."""
		said = prose_of("roland", "p_6")

		assert "under the `o`, inside the column headed `Recognized`" in said

	def test_sixty_four_patterns_and_a_channel_of_their_own (self) -> None:
		"""The S-1 gives its program changes a channel of their own too, and the same sixty-four."""
		p6 = pymidiinstrumentdefs.load("roland/p_6", [CORPUS])
		s1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert p6.midi.program_change is not None
		assert p6.midi.program_change.presets == 64
		assert p6.midi.program_change.receives is True
		assert p6.midi.program_change.sends is True

		assert s1.midi.program_change is not None
		assert s1.midi.program_change.presets == p6.midi.program_change.presets
		assert s1.parts["pattern"].receives == p6.parts["pattern"].receives == ("program_change",)


class TestPolyBrute12:

	"""The sibling of an instrument already here, whose chart turns out to be the same chart."""

	def test_its_chart_is_the_polybrutes_chart_number_for_number (self) -> None:
		"""The one thing worth asserting about two definitions of two products.

		This is the test the instrument exists for. Arturia publishes a manual for each
		product and the two charts agree completely, so **a consumer must get the same
		answer from either file** about any number either carries - and if a later
		edition of one manual changes a row, this is where that shows up rather than in
		somebody's reading of a diff.
		"""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])
		six = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		charted = {name: control for name, control in twelve.controls.items()
			if control.group != "mpe"}

		assert set(charted) == set(six.controls)

		for name, control in charted.items():
			assert control.cc == six.controls[name].cc, name
			assert control.label == six.controls[name].label, name
			assert control.group == six.controls[name].group, name

		# And the group labels with them, because a number under a different heading
		# would be a difference in the chart even with the number unchanged.
		assert {key: label for key, label in twelve.groups.items() if key != "mpe"} \
			== six.groups

	def test_the_one_control_the_chart_does_not_carry (self) -> None:
		"""Controller 74 is the MPE third dimension, and the chart has no reason to list it."""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])
		six = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		slide = twelve.controls["slide"]

		assert slide.cc == 74
		assert slide.label == "Slide"
		assert slide.group == "mpe"

		# Both ways, which is the format's default and so is what the file leaves unsaid.
		assert slide.direction == "both"

		# **THE SENSE IN WHICH ONE MAP IS A SUPERSET OF THE OTHER**: exactly one number.
		ours = {control.cc for control in twelve.controls.values()}
		theirs = {control.cc for control in six.controls.values()}

		assert ours - theirs == {74}
		assert theirs - ours == set()

		assert len(twelve.controls) == 75
		assert len(six.controls) == 74

	def test_it_has_double_the_voices_and_the_count_is_said_four_ways (self) -> None:
		"""Twelve against six, which is the product name and the first real difference."""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])
		six = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert twelve.voice.polyphony == 12
		assert six.voice.polyphony == 6

		# Two zones out of one pool on both, and one layering mode costs half of it.
		assert twelve.voice.polyphony_shared is True

		# **THE UNISON COUNT IS PRINTED IN THIS MANUAL AND NOT IN THE POLYBRUTE'S**, so
		# this list is five long where the sibling's is two. That is the document being
		# better rather than the instrument being different.
		assert twelve.voice.voicing_modes == (1, 2, 3, 6, 12)
		assert six.voice.voicing_modes == (1, 6)

		said = prose_of("arturia", "polybrute_12")

		assert "Please note that only 6 voices can be played" in said

	def test_the_aftertouch_is_poly_although_one_specification_line_says_channel (self) -> None:
		"""Two statements of one fact on one page, settled by the body of the manual.

		The rule this corpus follows is that a document contradicting itself about a
		thing records neither. **What takes this out of that rule is a third statement**,
		four pages of aftertouch modes that describe polyphonic pressure as what the
		keybed produces - so the narrower specification line is incomplete rather than in
		conflict, and the file sets out all of it.
		"""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])
		six = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert twelve.voice.aftertouch == "poly"
		assert six.voice.aftertouch == "channel"

		said = prose_of("arturia", "polybrute_12")

		assert "Two statements of one fact that do not meet" in said
		assert "WHAT SETTLES IT IS THE BODY OF THE MANUAL, NOT EITHER LINE" in said
		assert "Aftertouch (pressure sensitivity), channel or polyphonic" in said

	def test_mpe_is_the_difference_the_field_can_carry (self) -> None:
		"""One boolean for the thing the whole instrument is named around."""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])
		six = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert twelve.midi.per_voice_channels is True
		assert six.midi.per_voice_channels is None

		assert twelve.midi.channels == (1, 16)

		said = prose_of("arturia", "polybrute_12")

		# What the boolean cannot say, in the file instead: the two zones cross over.
		assert "AND IN SPLIT MODE THE TWO ZONES CROSS OVER" in said
		assert "An instrument's own upper half is MPE's lower zone" in said

	def test_the_bend_range_is_recorded_where_the_siblings_is_not (self) -> None:
		"""The pitch wheel's own reach, and not MPE's, which is set separately."""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])
		six = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert twelve.voice.pitch_bend is not None
		assert twelve.voice.pitch_bend.semitones == 24
		assert twelve.voice.pitch_bend.programmable is True

		# The PolyBrute's manual states no figure, so its file holds none.
		assert six.voice.pitch_bend is None

		said = prose_of("arturia", "polybrute_12")

		assert "MPE BENDS BY A DIFFERENT AND SEPARATELY SET RANGE" in said

	def test_the_transport_difference_is_the_manuals_and_not_the_instruments (self) -> None:
		"""Two separate menu entries here; the sibling's manual gives only the send switch."""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])
		six = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert twelve.midi.transport == "both"
		assert six.midi.transport is None

		assert twelve.midi.clock == "both"
		assert six.midi.clock == "both"

		said = prose_of("arturia", "polybrute_12")

		assert "Whether the PolyBrute gained the setting or only the sentence is not" in said

	def test_the_file_says_which_product_it_covers (self) -> None:
		"""Two manuals under one family's version numbers, so the name is not enough."""
		said = prose_of("arturia", "polybrute_12")

		assert "THE SAME MAP ON A DIFFERENT INSTRUMENT" in said
		assert "THE POLYBRUTE NOIR IS A FINISH" in said

		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])

		account = " ".join((twelve.source or "").split())

		# The document identifies itself, which is what was checked rather than assumed.
		assert "User Manual PolyBrute 12" in account
		assert "polybrute-12__3.1.0__20251010__en" in account

	def test_no_firmware_and_the_image_is_the_siblings_own_file (self) -> None:
		"""One firmware runs both products, which a version number would hide."""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])

		assert twelve.model.firmware is None
		assert twelve.sources["manual"].edition == "3.1.0"
		assert twelve.sources["manual"].dated == "2025-10-15"
		assert twelve.sources["manual"].page_offset == 9

		said = prose_of("arturia", "polybrute_12")

		assert "AND THE FIRMWARE THE PAGE SERVES IS THE POLYBRUTE'S OWN FILE" in said
		assert "One firmware image runs both products" in said

	def test_the_survey_was_wrong_about_the_socket_and_the_file_says_so (self) -> None:
		"""USB-C per the survey, USB type B per the manual, three times and agreeing."""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])

		account = " ".join((twelve.source or "").split())

		assert "THE SURVEY SAID THIS INSTRUMENT HAS A USB-C SOCKET AND THE MANUAL SAYS " \
			"USB TYPE B" in account
		assert "the connector difference the survey reported between the two products is " \
			"not there" in account

	def test_the_source_account_keeps_the_trap_and_the_render_warning (self) -> None:
		"""Because the next reader of a grid chart needs the trap, not the result."""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])

		account = " ".join((twelve.source or "").split())

		assert "THE CHART IS A GRID OF EIGHTEEN SMALL TABLES, THREE ACROSS" in account
		assert "the column positions move from one block of rows to the next" in account

		# **AND THE WARNING THAT COST THE SECOND READER NOTHING AND COULD HAVE COST A LOT**:
		# this typeface's zero reads as a capital O in a render, so an eye-reading of an
		# image is the less reliable of the two methods here.
		assert "THE RENDERING WAS THE LESS RELIABLE OF THE TWO" in account
		assert "all read as 7O, 8O, 9O, 1O and 1O2" in account

	def test_sysex_and_nrpn_are_left_unset_for_a_stated_reason (self) -> None:
		"""A checked absence, and a document whose form is not strong enough to settle it.

		The S-1 records `nrpn: none` off the same kind of word search, and the difference
		is the document: an implementation chart undertakes to list what an instrument
		does not do, so its silence is an answer. A list of controller assignments does
		not, so this manual's silence is only silence - and both Arturias agree.
		"""
		twelve = pymidiinstrumentdefs.load("arturia/polybrute_12", [CORPUS])
		six = pymidiinstrumentdefs.load("arturia/polybrute", [CORPUS])

		assert twelve.midi.nrpn is None
		assert twelve.midi.sysex is None
		assert six.midi.nrpn is None
		assert six.midi.sysex is None

		assert pymidiinstrumentdefs.load("roland/s_1", [CORPUS]).midi.nrpn == "none"

		account = " ".join((twelve.source or "").split())

		assert "its silence is only silence" in account


class TestPro800:

	"""A table whose columns say what each number is, and 34 controls paired by name alone."""

	def test_the_column_a_name_sits_in_is_half_of_what_the_table_says (self) -> None:
		"""112 rows become 70 controls, and the arithmetic has to be visible.

		34 coarse rows each absorb a fine row as their `lsb`; 30 stepped rows and 6 of the 14
		protocol rows become controls of their own; and 8 protocol rows are left out. So
		112 - 34 - 8 = 70, and this is where that is written down.
		"""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		assert len(pro.controls) == 70

		fourteen = [control for control in pro.controls.values() if control.lsb is not None]

		assert len(fourteen) == 34

		account = " ".join((pro.source or "").split())

		assert "34 coarse, 34 fine, 30 stepped and 14 the protocol's own" in account

	def test_the_fine_half_is_not_where_the_specification_puts_it (self) -> None:
		"""Three offsets, none of them 32, so no rule gets you from one half to the other.

		**This is the finding.** The MIDI specification pairs controller N with N+32. This
		maker pairs 8 with 80, 24 with 100 and 39 with 114 - and a consumer that assumed the
		convention would send OSC A Freq's fine value to controller 40, which on this
		instrument is the VCF Aftertouch amount.
		"""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		offsets = {control.lsb - control.cc for control in pro.controls.values()
			if control.lsb is not None and control.cc is not None}

		assert offsets == {72, 75, 76}
		assert 32 not in offsets

		# The one that would bite, named so the test says why it matters.
		by_number = {control.cc: control for control in pro.controls.values()}

		assert by_number[8].label == "OSC A Freq"
		assert by_number[8].lsb == 80
		assert by_number[40].label == "VCF Aftertouch"

	def test_no_fine_controller_is_also_a_control_of_its_own (self) -> None:
		"""A fine half is an `lsb` and nothing else, or a consumer would see it twice."""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		fine = {control.lsb for control in pro.controls.values() if control.lsb is not None}
		coarse = {control.cc for control in pro.controls.values()}

		assert fine & coarse == set()
		assert len(fine) == 34

	def test_the_protocols_own_controllers_are_left_out (self) -> None:
		"""Six NRPN controllers and two channel mode messages are not this instrument.

		The guide beside this corpus draws the line: channel mode messages are refused
		outright, and Data Entry is left out where it is only how an NRPN's value travels.
		This table says that is exactly what it is - it calls CC 6 and 38 `NRPN Data MSB`
		and `NRPN Data LSB` - and the same argument covers CC 96 to 99.
		"""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		numbers = {control.cc for control in pro.controls.values()}

		for number in (6, 38, 96, 97, 98, 99, 120, 123):
			assert number not in numbers, f"controller {number} should not be a control"

		# Bank Select is kept, as two other definitions in this corpus keep theirs.
		assert 0 in numbers

		for other in ("korg/opsix", "oberheim/teo_5"):
			theirs = pymidiinstrumentdefs.load(other, [CORPUS])
			assert any(control.cc == 0 for control in theirs.controls.values()), other

	def test_nrpn_is_supported_and_no_nrpn_number_is_published (self) -> None:
		"""The transport is documented and the addresses are not, which is a real state.

		Six controllers are the NRPN mechanism and the maker names them as such, so
		`supported` is said by the document. But no page of 123 names an NRPN parameter
		number, so **no control carries one** - and the two facts together are what the
		file has to convey.
		"""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		assert pro.midi.nrpn == "supported"

		assert [control.name for control in pro.controls.values()
			if control.nrpn is not None] == []

		said = prose_of("behringer", "pro_800")

		assert "NRPN IS REAL AND NOT ONE NRPN NUMBER IS PUBLISHED" in said

	def test_the_three_faults_in_the_table_are_recorded_and_not_mended (self) -> None:
		"""A duplicated name, a wrong hexadecimal cell and two halves named differently."""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		# The duplicate is carried as printed, told apart by number and not by invention.
		assert pro.controls["osc_a_saw_48"].label == "OSC A Saw"
		assert pro.controls["osc_a_saw_49"].label == "OSC A Saw"
		assert pro.controls["osc_a_saw_48"].cc == 48
		assert pro.controls["osc_a_saw_49"].cc == 49

		# And the maker's own misspelling of its own oscillator is kept, twice.
		labels = {control.label for control in pro.controls.values()}

		assert "OSB B Tri" in labels
		assert "OSB B Square" in labels

		account = " ".join((pro.source or "").split())

		assert "Controllers 48 and 49 are both printed `OSC A Saw`" in account
		assert "Controller 79's `Hex` cell reads `AF`" in account
		assert "The two halves of one parameter are not named alike" in account

	def test_the_one_pair_joined_on_four_grounds_rather_than_on_its_name (self) -> None:
		"""Controller 41 and controller 116 are one parameter spelled two ways.

		Every other coarse half pairs with a fine half of the same name. This one does not,
		and it is joined anyway - which is a judgement, so the file sets out all four
		reasons rather than leaving a reader to wonder.
		"""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		joined = next(control for control in pro.controls.values() if control.cc == 41)

		assert joined.label == "LFO Aftertouch amount"
		assert joined.lsb == 116

		# +75, exactly as its three neighbours sit.
		for number in (39, 40, 42):
			other = next(c for c in pro.controls.values() if c.cc == number)
			assert other.lsb is not None and other.lsb - number == 75

		account = " ".join((pro.source or "").split())

		assert "it is the only unpaired name on either side" in account
		assert 'the instrument\'s own menu calls the parameter "LFO Aftertouch Amount"' in account

	def test_two_printed_pages_to_a_sheet_as_on_the_other_behringer (self) -> None:
		"""A spread holds two pages, so a citation to p. 107 is one half of a sheet."""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])
		td_3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert pro.sources["guide"].pages_per_sheet == 2
		assert pro.sources["guide"].page_offset == 1

		# The same shape on the same maker's other guide, which is why it is worth a test -
		# and the same source key, so a reader comparing the two meets one name for one
		# kind of document.
		assert td_3.sources["guide"].pages_per_sheet == 2

		account = " ".join((pro.source or "").split())

		assert "TWO PRINTED PAGES ARE SET TO A SHEET" in account
		assert "The citation checker cannot tell the two halves apart" in account

	def test_the_preset_count_is_four_hundred_and_the_guide_cannot_count (self) -> None:
		"""Four banks of a hundred, settled by the guide against the guide.

		"program numbers 0-100" over "four banks" is 404. What settles it is the guide
		itself two pages later, telling you to press a two-digit location - a hundred per
		bank - and the product page twice saying 400.
		"""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		assert pro.midi.program_change is not None
		assert pro.midi.program_change.presets == 400

		said = prose_of("behringer", "pro_800")

		assert "THE GUIDE'S OWN ARITHMETIC DOES NOT WORK AND IS NOT WHAT IS RECORDED" in said
		assert "Two digits is a hundred locations" in said

	def test_what_is_absent_is_absent_for_a_stated_reason (self) -> None:
		"""Transport, the note range and the kind of aftertouch, each with its own sentence."""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		assert pro.midi.transport is None
		assert pro.voice.note_range is None

		# It plainly answers to pressure and no page says which kind, so the field is unset.
		assert pro.voice.aftertouch is None

		labels = {control.label for control in pro.controls.values()}

		assert "VCA Aftertouch" in labels
		assert "VCF Aftertouch" in labels

		said = prose_of("behringer", "pro_800")

		assert "NOT RECORDED, AND IT PLAINLY ANSWERS TO ONE" in said

		assert "the menu's \"Sync In Start/Stop On / Off\"" in said

	def test_the_maker_publishes_a_feature_claim_it_cannot_be_quoted_on (self) -> None:
		"""A script-built feature list is in the markup and not in the text that is cited."""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		account = " ".join((pro.source or "").split())

		assert "THE PRODUCT PAGE'S FEATURE LIST IS NOT CITABLE AND ITS PROSE IS" in account
		assert "inside a JSON payload in a `script` element" in account

	def test_its_groups_are_the_makers_panel_sections_and_fifteen_have_none (self) -> None:
		"""A flat table has no headings, so the grouping comes from the specifications."""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		assert list(pro.groups) == ["oscillator", "poly_mod", "noise", "lfo_mod",
			"glide", "filter", "amplifier", "output"]

		bare = [control.name for control in pro.controls.values() if not control.group]

		assert len(bare) == 15

		said = prose_of("behringer", "pro_800")

		assert "FIFTEEN CONTROLS GET NO GROUP AT ALL" in said

	def test_no_firmware_although_the_parameter_set_demonstrably_moves (self) -> None:
		"""The third Behringer here with no firmware number, and the one where it matters."""
		pro = pymidiinstrumentdefs.load("behringer/pro_800", [CORPUS])

		assert pro.model.firmware is None
		assert pro.sources["guide"].edition == "V 4.0"

		for other in ("behringer/td_3", "behringer/model_d"):
			assert pymidiinstrumentdefs.load(other, [CORPUS]).model.firmware is None

		said = prose_of("behringer", "pro_800")

		assert "THE FIRMWARE THIS DESCRIBES IS NOT ESTABLISHED AND THE DOCUMENT PROVES THE " \
			"PARAMETER SET HAS MOVED" in said
		assert "are now controllable in three modes" in said


class TestOctatrack:

	"""Two controller maps, one file for two products, and sixteen rows the format refuses."""

	def test_one_file_covers_two_products_because_the_appendices_agree (self) -> None:
		"""The question the rank posed, and the answer is in the file's own account.

		Elektron publishes a manual per product, four years and two OS revisions apart. Both
		appendices were read by the same code and compared on four questions - the numbers,
		the names, the direction marks and the hexadecimal cells - and all 115 rows agree.
		Both are in `sources`, and the older one is cited for nothing: it is there because
		reading it is what establishes this.
		"""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		assert set(octa.sources) >= {"manual", "mki_manual"}
		assert octa.sources["manual"].edition == "1.40C"
		assert octa.sources["mki_manual"].edition == "1.40A"

		said = prose_of("elektron", "octatrack")

		assert "THIS ONE FILE COVERS THE MKI AND THE MKII, AND THAT WAS ESTABLISHED RATHER " \
			"THAN ASSUMED" in said

		account = " ".join((octa.source or "").split())

		assert "THE TWO MANUALS' APPENDICES AGREE ON ALL 115 ROWS" in account

	def test_the_same_number_means_different_things_in_the_two_maps (self) -> None:
		"""51 numbers are in both maps, which is the whole reason for the parts.

		**This is the test worth having.** A consumer that ignored `part` would get one of the
		two meanings for every one of those numbers, and would be wrong half the time.
		"""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		audio = {control.cc for control in octa.controls.values()
			if control.part == "audio" and control.cc is not None}
		midi = {control.cc for control in octa.controls.values()
			if control.part == "midi" and control.cc is not None}

		# 51 numbers overlap in the appendix; 8 of those are on refused numbers, so 43 of the
		# overlap survives into the controls.
		assert len(audio & midi) == 43

		# And the overlapping numbers really do mean different things.
		def named (part: str, number: int) -> str:
			"""One map's label for a controller number."""
			return next(control.label for control in octa.controls.values()
				if control.part == part and control.cc == number)

		assert named("audio", 22) == "Amp param #1 (Attack)"
		assert named("midi", 22) == "Amp param #1 (Transpose)"
		assert named("audio", 34) == "FX1 param #1"
		assert named("midi", 34) == "Pitch bend"

	def test_the_appendix_reuses_a_page_name_for_a_different_page (self) -> None:
		"""So the grouping is keyed on the map as well as the name, and here is why.

		`Amp param` is the AMP page in the audio map and the ARPEGGIATOR page in the MIDI map.
		The bracketed glosses are the evidence: Transpose, Legato, Mode, Speed, Octave Range
		and Arp Note Length are what sections 15.4.3 and 15.4.4 put on the arpeggiator pages.
		**A reader grouping on the prefix alone files the arpeggiator under the amplifier.**
		"""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		amp = sorted(control.cc for control in octa.controls.values()
			if control.group == "amp" and control.cc is not None)
		arp = sorted(control.cc for control in octa.controls.values()
			if control.group == "arpeggiator" and control.cc is not None)

		assert amp == [22, 23, 24, 25, 26, 27]
		assert arp == [22, 23, 24, 25, 26, 27]

		# The same numbers, in different maps, under different pages.
		assert {control.part for control in octa.controls.values()
			if control.group == "amp"} == {"audio"}
		assert {control.part for control in octa.controls.values()
			if control.group == "arpeggiator"} == {"midi"}

		account = " ".join((octa.source or "").split())

		assert "APPENDIX C'S OWN NAMES FOR THE MIDI MAP'S PAGES ARE THE AUDIO MAP'S NAMES" \
			in account

	def test_sixteen_rows_are_refused_because_the_maker_used_channel_mode (self) -> None:
		"""Controllers 120 to 127 carry MIDI track solos, and this format will not hold them.

		The second instrument here to lose published numbers this way, after the Hydrasynth
		Explorer - and the loss is recorded in the file rather than worked around.
		"""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		numbers = {control.cc for control in octa.controls.values()}

		for number in range(120, 128):
			assert number not in numbers, f"controller {number} is a channel mode message"

		# But 112 to 119 are undefined in the specification and are carried.
		for number in range(112, 120):
			assert number in numbers, f"controller {number} should be a control"

		assert len(octa.controls) == 99

		account = " ".join((octa.source or "").split())

		assert "SIXTEEN OF THE 115 ROWS CANNOT BE CONTROLS, AND THE MAKER IS THE REASON" \
			in account
		assert "a sequencer sending All Sound Off to it solos a MIDI track" in account

		# The Hydrasynth Explorer is the precedent and says the same thing its own way.
		explorer = " ".join((pymidiinstrumentdefs.load(
			"asm/hydrasynth_explorer", [CORPUS]).source or "").split())

		assert "numbers the specification reserves for channel mode" in explorer.lower()

	def test_the_midi_map_is_receive_only_by_its_own_introduction (self) -> None:
		"""Every row of C.8 is marked in REC and none in TRN, which the section states.

		It reads at first like the manual contradicting itself: the sixteen MIDI track mutes
		and solos are identical rows in both maps, marked both ways in one and received only
		in the other. **The section's own first sentence settles it** - the auto channel
		"responds to" these messages - so C.8 is a receive-only table by construction.
		"""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		midi = [control for control in octa.controls.values() if control.part == "midi"]

		assert midi
		assert all(control.direction == "receives" for control in midi)

		# The audio map is mostly both ways, with seven received only.
		audio = [control for control in octa.controls.values() if control.part == "audio"]
		one_way = [control.cc for control in audio
			if control.direction == "receives" and control.cc is not None]

		assert sorted(one_way) == [7, 8, 57, 58, 59, 60, 61]

		account = " ".join((octa.source or "").split())

		assert "the whole of C.8 is a receive-only table by construction" in account

	def test_the_parts_are_the_tracks_and_not_the_makers_own_word (self) -> None:
		"""An Octatrack bank holds four "parts" and they are not these."""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		assert set(octa.parts) == {"audio", "midi"}
		assert octa.parts["audio"].count == 8
		assert octa.parts["midi"].count == 8

		# The MIDI tracks do not sound, so they take controls and not notes.
		assert "notes" not in (octa.parts["midi"].receives or ())
		assert "notes" in (octa.parts["audio"].receives or ())

		said = prose_of("elektron", "octatrack")

		assert "THE MAKER'S WORD `PART` IS NOT THIS FORMAT'S" in said

	def test_no_polyphony_because_the_word_voices_is_nowhere_in_the_manual (self) -> None:
		"""A count of tracks is not a count of voices, and this manual gives only tracks."""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		assert octa.voice.polyphony is None
		assert octa.voice.note_range is None

		said = prose_of("elektron", "octatrack")

		assert "The word `voices` appears nowhere in these 148 pages" in said
		assert "A count of tracks is not a count of voices" in said

	def test_one_firmware_image_serves_both_products (self) -> None:
		"""Both support pages link the same release notes, so a version tells them apart."""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		assert octa.model.firmware == "1.40C"
		assert octa.sources["release_notes"].edition == "1.40C"

		said = prose_of("elektron", "octatrack")

		assert "BOTH SUPPORT PAGES SERVE THE SAME IMAGE" in said
		assert "THE SAME FILE IS LINKED FROM BOTH PRODUCTS' PAGES" in said

	def test_the_support_pages_printed_date_contradicts_the_file_it_serves (self) -> None:
		"""Three signals against one, so the page is stale rather than the file mislabelled."""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		assert octa.sources["manual"].dated == "2026-08-27"

		account = " ".join((octa.source or "").split())

		assert "THE MKII'S SUPPORT PAGE PRINTS A DATE THAT CONTRADICTS THE FILE IT SERVES" \
			in account
		assert "Three independent signals against one" in account

	def test_sysex_is_true_for_one_purpose_unlike_the_other_elektrons (self) -> None:
		"""Nine Elektrons here record it for a dump menu; this one has none.

		The only thing this instrument does with system exclusive is take its own operating
		system, over the five-pin ports and not over USB. The field is the same and what it
		covers is not, so the file says which.
		"""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		assert octa.midi.sysex is True

		said = prose_of("elektron", "octatrack")

		assert "TRUE, AND FOR ONE PURPOSE ONLY, WHICH IS DIFFERENT FROM EVERY OTHER " \
			"ELEKTRON HERE" in said
		assert "The upgrade can not be sent over the Octatrack's USB port" in said

	def test_nrpn_is_unset_and_the_reasoning_is_in_the_file (self) -> None:
		"""The closest call here: suggestive, and not a statement.

		The words appear nowhere in 148 pages, and this maker's newer manuals publish NRPN
		beside CC in the same appendix form. That is a difference worth noticing and still
		not something the document says, so the field is unset and the evidence is written
		down - which is the honest state rather than a guess in either direction.
		"""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		assert octa.midi.nrpn is None
		assert [control.name for control in octa.controls.values()
			if control.nrpn is not None] == []

		# The comparison the file makes: this maker's other appendices do give NRPNs.
		digitone = pymidiinstrumentdefs.load("elektron/digitone", [CORPUS])

		assert digitone.midi.nrpn is not None
		assert any(control.nrpn is not None for control in digitone.controls.values())

		said = prose_of("elektron", "octatrack")

		assert "NOT RECORDED, AND THIS IS THE CLOSEST CALL IN THE FILE" in said
		assert "It is still not a statement" in said

	def test_ten_of_the_midi_maps_controllers_have_owner_chosen_destinations (self) -> None:
		"""The numbers are fixed and published; what they reach is a setting."""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		assignable = sorted(control.cc for control in octa.controls.values()
			if (control.label or "").startswith("CC #") and control.cc is not None)

		assert assignable == [36, 37, 38, 39, 40, 41, 42, 43, 44, 45]

		# Four on the CTRL 1 page and six on CTRL 2, which is the maker's own division.
		assert sorted(control.cc for control in octa.controls.values()
			if control.group == "ctrl_1" and control.cc is not None) \
			== [34, 35, 36, 37, 38, 39]
		assert sorted(control.cc for control in octa.controls.values()
			if control.group == "ctrl_2" and control.cc is not None) \
			== [40, 41, 42, 43, 44, 45]

		account = " ".join((octa.source or "").split())

		assert "the ten numbers are fixed and published and the ten destinations are not" \
			in account

	def test_one_parameter_name_is_at_two_numbers_with_two_directions (self) -> None:
		"""Track level is controller 7, received only, and 46, both ways."""
		octa = pymidiinstrumentdefs.load("elektron/octatrack", [CORPUS])

		seven = octa.controls["audio_track_level_7"]
		forty_six = octa.controls["audio_track_level_46"]

		assert seven.label == forty_six.label == "Track level"
		assert seven.cc == 7 and seven.direction == "receives"
		assert forty_six.cc == 46 and forty_six.direction == "both"

		account = " ".join((octa.source or "").split())

		assert "ONE PARAMETER NAME IS AT TWO NUMBERS IN THE AUDIO MAP" in account


class TestMaschinePlus:

	"""Two controller numbers in 243 pages, and an absence established by enumeration."""

	def test_two_controls_and_both_are_the_specifications_own_numbers (self) -> None:
		"""The whole published map, and neither number is this maker's choice.

		Controller 1 the manual itself calls reserved for the modulation wheel; controller 64
		is the damper pedal, and what it reaches here is an envelope's sustain level - a
		continuous parameter on a number the specification defines as a switch.
		"""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		assert len(maschine.controls) == 2

		assert maschine.controls["modulation"].cc == 1
		assert maschine.controls["sustain"].cc == 64

		# The second is received only; no page says the instrument sends it.
		assert maschine.controls["modulation"].direction == "both"
		assert maschine.controls["sustain"].direction == "receives"

		account = " ".join((maschine.source or "").split())

		assert "BOTH NUMBERS ARE ONES THE MIDI SPECIFICATION HAD ALREADY SPOKEN FOR" in account
		assert "a continuous parameter on a number the specification defines as a switch" \
			in account

	def test_the_absence_is_an_enumeration_and_not_a_silence (self) -> None:
		"""The point of this definition: a machine found every number, and there were two.

		The corpus has eleven definitions with no controls and they rest on evidence of
		different strengths. This one is a third kind - a manual that names two numbers in
		passing - and the only honest way to say so is to show the list is two long.
		"""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		said = prose_of("native_instruments", "maschine_plus")

		assert "THAT ABSENCE IS AN ENUMERATION AND NOT A SILENCE" in said

		account = " ".join((maschine.source or "").split())

		assert "SO THE WORK ON THIS INSTRUMENT WAS TO ESTABLISH AN ABSENCE, AND A MACHINE " \
			"ESTABLISHED IT" in account

		# And both editions were searched, so the absence is not an artefact of which was read.
		assert set(maschine.sources) >= {"manual", "older_manual"}
		assert maschine.sources["manual"].dated == "2022-05-13"
		assert maschine.sources["older_manual"].dated == "2020-10-01"

		assert "the 2020 edition names the same two" in account

	def test_every_other_controller_number_belongs_to_the_owner (self) -> None:
		"""`learned`, and the two numbers above are the exceptions somebody else fixed.

		The Iridium and the Pulsar-23 are the other definitions here that are `learned` and
		still carry a few numbers, so the combination is established rather than invented.
		"""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		assert maschine.midi.control_change == "learned"

		for other in ("waldorf/iridium", "soma/pulsar_23"):
			theirs = pymidiinstrumentdefs.load(other, [CORPUS])
			assert theirs.midi.control_change == "learned", other
			assert theirs.controls, other

		said = prose_of("native_instruments", "maschine_plus")

		assert "EVERY CONTROLLER NUMBER BUT TWO BELONGS TO THE PLAYER" in said

	def test_the_document_that_would_hold_the_map_is_not_published (self) -> None:
		"""It ships inside an application, so this corpus cannot cite it.

		**That is the sharpest limit on this instrument** and it is a limit of publication
		rather than of reading, so the file says so rather than leaving a reader to wonder
		why a controller map is missing.
		"""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		account = " ".join((maschine.source or "").split())

		assert "AND THE MANUAL FOR THAT APPLICATION IS NOT ON THE WEB" in account
		assert "available as a PDF file via the Help menu of Controller Editor" in account

		said = prose_of("native_instruments", "maschine_plus")

		assert "It ships inside an application" in said

		# And the downloads page is saved for what it does not contain.
		assert "downloads_page" in maschine.sources
		assert maschine.sources["downloads_page"].paginated is False

	def test_the_first_native_instruments_product_here (self) -> None:
		"""A new maker, so no habits were established and the folder is new too."""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		assert maschine.model.manufacturer == "Native Instruments"

		theirs = [name for name in pymidiinstrumentdefs.available([CORPUS])
			if name.startswith("native_instruments/")]

		assert theirs == ["native_instruments/maschine_plus"]

		said = prose_of("native_instruments", "maschine_plus")

		assert "THE FIRST NATIVE INSTRUMENTS PRODUCT HERE" in said

	def test_no_firmware_because_this_maker_dates_rather_than_numbers (self) -> None:
		"""Both editions are identified by a date in a file name and nothing else."""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		assert maschine.model.firmware is None
		assert maschine.sources["manual"].edition is None
		assert maschine.sources["older_manual"].edition is None

		said = prose_of("native_instruments", "maschine_plus")

		assert "it is dated rather than numbered, which is this maker's habit" in said

	def test_the_clock_does_each_direction_and_not_both_at_once (self) -> None:
		"""A three-way setting, which the field cannot say and the file does."""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		assert maschine.midi.clock == "both"

		said = prose_of("native_instruments", "maschine_plus")

		assert "BOTH, AND THE SETTING IS EXCLUSIVE" in said
		assert "So it does each and not both at once" in said

	def test_program_change_is_received_and_sending_is_not_claimed (self) -> None:
		"""What arrives selects a Scene; what leaves is a message the owner assigned."""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		assert maschine.midi.program_change is not None
		assert maschine.midi.program_change.receives is True
		assert maschine.midi.program_change.sends is None
		assert maschine.midi.program_change.presets is None

		said = prose_of("native_instruments", "maschine_plus")

		assert "That is the instrument sending a message the owner chose, not reporting" in said

	def test_its_parts_default_to_a_focus_rather_than_a_channel (self) -> None:
		"""Unlike every other part in this corpus, and the file says so."""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		assert set(maschine.parts) == {"sound", "group"}
		assert maschine.parts["sound"].channel == "assigned"
		assert maschine.parts["group"].channel == "assigned"

		# A Group takes notes and not controllers: the MIDI output page is for Sounds only.
		assert "controls" in (maschine.parts["sound"].receives or ())
		assert "controls" not in (maschine.parts["group"].receives or ())

		said = prose_of("native_instruments", "maschine_plus")

		assert "SO THE DEFAULT IS NOT A CHANNEL BUT A FOCUS" in said

	def test_in_and_out_and_no_thru (self) -> None:
		"""Worth stating because this maker's competitors mostly have three sockets."""
		maschine = pymidiinstrumentdefs.load("native_instruments/maschine_plus", [CORPUS])

		account = " ".join((maschine.source or "").split())

		assert "THE CONNECTORS ARE IN AND OUT AND THERE IS NO THRU" in account

		# The Octatrack is the contrast, from the same kind of instrument.
		octa = " ".join((pymidiinstrumentdefs.load(
			"elektron/octatrack", [CORPUS]).source or "").split())

		assert "MIDI In/Out/Thru" in octa


class TestSuper6:

	"""The most complete implementation a new maker has brought here, and an NRPN rule."""

	def test_the_nrpn_is_the_controller_number_plus_1024 (self) -> None:
		"""The finding, and it is measured over every pair rather than assumed.

		NRPN 1027 is controller 3, both named Tempo; 1031 is controller 7, both VCA
		Envelope Level. **A consumer can derive one from the other**, which is rare enough
		to be worth a test of its own - and if a later edition breaks the rule, this is
		where it shows.
		"""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		paired = [control for control in super_6.controls.values()
			if control.cc is not None and control.nrpn is not None]

		assert len(paired) == 41

		# **AND NO BANDED CONTROL HAS ONE.** The NRPN block mirrors the continuous
		# parameters only, which is a sharper statement than the arithmetic gives: a
		# switched parameter has nothing to gain from fourteen bits.
		assert all(not control.values for control in paired)

		for control in paired:
			assert control.cc is not None and control.nrpn is not None
			assert control.nrpn == control.cc + 1024, control.name

		# And every one of them carries the wider range the NRPN table gives.
		for control in paired:
			assert control.nrpn_range == (0, 16383), control.name
			assert control.range == (0, 127), control.name

	def test_the_protocols_own_rows_are_listed_and_left_out (self) -> None:
		"""This maker lists them, which is the opposite of the rank before it.

		The Octatrack put its own MIDI track solos on 120 to 127 and the format had to
		refuse them. **This maker lists 120 to 127 as what the specification says they
		are** - All Sound Off, Reset All Controllers, Local Control, All Notes Off, the
		four mode messages - so leaving them out loses nothing of this instrument.
		"""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		numbers = {control.cc for control in super_6.controls.values()}

		# **38 IS IN THIS LIST BECAUSE THE SECOND READER PUT IT THERE.** It is
		# `LSB for Control 6 (Data Entry)`, so keeping it was keeping half of a pair.
		for number in list(range(120, 128)) + [6, 38, 96, 97, 98, 99, 100, 101]:
			assert number not in numbers, f"controller {number} should not be a control"

		# Bank Select is kept, as two other definitions here keep theirs.
		assert 0 in numbers

		account = " ".join((super_6.source or "").split())

		assert "this table is unusual in listing them at all" in account
		assert "which is the opposite of the instrument one rank earlier" in account

	def test_every_number_from_0_to_127_gets_a_row (self) -> None:
		"""What makes the table complete rather than selective, and a blank row is the maker.

		97 of its 128 rows name a parameter and 31 are blank. **A blank row is the maker
		saying nothing rather than the reading losing something**, which is the distinction
		that lets this definition's absences be trusted.
		"""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		account = " ".join((super_6.source or "").split())

		assert "THE CONTROLLER TABLE GIVES EVERY NUMBER FROM 0 TO 127 A ROW" in account
		assert "97 of its 128 rows name a parameter and 31 are blank" in account

		# 97 named less 16 of the protocol's own is 81, plus 5 NRPN-only global settings.
		assert len(super_6.controls) == 86

		nrpn_only = [control for control in super_6.controls.values()
			if control.cc is None and control.nrpn is not None]

		assert len(nrpn_only) == 5
		assert all(control.group == "global" for control in nrpn_only)

	def test_forty_controls_have_their_value_bands_named (self) -> None:
		"""The Value Range column is real, which most are not."""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		banded = [control for control in super_6.controls.values() if control.values]

		assert len(banded) == 40

		# A band is recorded by its lowest value, which is what `values` means.
		waveform = next(control for control in super_6.controls.values()
			if control.cc == 16)

		assert waveform.values == {"triangle": 0, "square": 21, "random": 43,
			"saw": 64, "hf": 85, "hf_trk": 107}

	def test_it_receives_mpe_and_never_sends_it_at_six_of_its_twelve_voices (self) -> None:
		"""Two facts the flag cannot carry, and the maker gives a reason for the second.

		**The six-voice limit is a hardware fact stated plainly**, which is rarer than the
		limit: the analogue hardware can only give six notes different control voltages. A
		consumer reading `polyphony` and `per_voice_channels` together would get it wrong.
		"""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		assert super_6.midi.per_voice_channels is True
		assert super_6.voice.polyphony == 12

		said = prose_of("udo_audio", "super_6")

		assert "the Super 6 will respond to incoming MIDI messages sent from an MPE " \
			"controller via an individual MIDI channel per note" in said
		assert "so MPE mode is limited to six voices" in said
		assert "which puts this instrument beside the Prophet-6 rather than beside the " \
			"Osmose" in said

		# And the MPE timbre axis is one of the controls below, not a separate route.
		cutoff = next(control for control in super_6.controls.values() if control.cc == 74)

		assert cutoff.label == "VCF Cutoff Frequency"

	def test_the_resolution_is_a_choice_about_sending_and_never_about_receiving (self) -> None:
		"""Unusual enough to be the second thing the file says."""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		assert super_6.midi.nrpn == "supported"

		said = prose_of("udo_audio", "super_6")

		assert "the Super 6 will always respond to both parameter changes sent in 7 and " \
			"14 bit resolution" in said
		assert "So a sender chooses the resolution and a listener never has to" in said

	def test_one_manual_covers_both_models (self) -> None:
		"""Which answers in one document what the two ranks before it needed work for."""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		assert list(super_6.sources) == ["manual", "support_page"]

		said = prose_of("udo_audio", "super_6")

		assert "ONE MANUAL COVERS THE KEYBOARD AND THE DESKTOP MODELS" in said
		assert "MIDI In, Out and Thru Ports: Standard 5-pin MIDI DIN connectors" in said

	def test_no_firmware_because_the_maker_masks_its_own_version (self) -> None:
		"""Three numbers exist and none of them is the firmware."""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		assert super_6.model.firmware is None

		# The edition is the document's version, which is the only place it appears.
		assert super_6.sources["manual"].edition == "1.4"

		said = prose_of("udo_audio", "super_6")

		assert "THE MAKER MASKS THE NUMBER IN ITS OWN INSTRUCTIONS" in said
		assert "the manual is two minor versions behind the firmware on offer" in said

	def test_the_front_matter_is_numbered_in_roman_numerals (self) -> None:
		"""A trap the citation gate cannot catch, so the file names it.

		Sheets 1 to 13 print roman numerals and the body prints arabic equal to the sheet.
		**A citation to "p. 12" would pass the gate while being wrong**, because the
		arithmetic lands on sheet 12 and the text is there, under a folio the document
		calls xii. The clearest statement of the voice count is on that sheet and is
		deliberately not cited.
		"""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		assert super_6.sources["manual"].page_offset == 0

		account = " ".join((super_6.source or "").split())

		assert "THE FRONT MATTER IS NUMBERED IN ROMAN NUMERALS AND THE BODY IN ARABIC" \
			in account
		assert "a citation to `p. 12` would pass the gate while being wrong" in account

		# So the voice count is cited from two other pages instead.
		said = prose_of("udo_audio", "super_6")

		assert "its 12 voices are twinned to form six stereo" in said
		assert "In 12-voice non-binaural mode" in said

	def test_the_message_tables_give_a_direction_for_every_row (self) -> None:
		"""Including one that is received and never sent, and one that is simply absent."""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		# Polyphonic Key Pressure is No transmitted and Yes received.
		assert super_6.voice.aftertouch == "poly"

		assert super_6.voice.velocity is not None
		assert super_6.voice.velocity.note_on == "both"
		assert super_6.voice.velocity.note_off is True

		account = " ".join((super_6.source or "").split())

		assert "Polyphonic Key Pressure is No transmitted and Yes received" in account

		# **AND CONTINUE IS NOT IN THE TABLE AT ALL**, which is an absence and not a No -
		# the distinction the S-1 is the contrast for.
		assert "CONTINUE IS NOT IN THE TABLE AT ALL" in account

		s_1 = pymidiinstrumentdefs.load("roland/s_1", [CORPUS])

		assert s_1.midi.transport == "both"
		assert "it answers to a transport it cannot be told to resume" in prose_of("roland", "s_1")

	def test_the_bend_range_is_stated_twice_from_two_directions (self) -> None:
		"""A sentence and a registered parameter's data entry value, agreeing."""
		super_6 = pymidiinstrumentdefs.load("udo_audio/super_6", [CORPUS])

		assert super_6.voice.pitch_bend is not None
		assert super_6.voice.pitch_bend.semitones == 12
		assert super_6.voice.pitch_bend.programmable is True

		said = prose_of("udo_audio", "super_6")

		assert "The maximum pitch-bend range is one octave" in said
		assert "MSB = +/- 12 semitones" in said


class TestTR6S:

	"""The smaller of two drum machines whose maker wrote one document by editing the other's.

	**EVERY CLAIM HERE ABOUT WHAT THE TWO SHARE IS CHECKED AGAINST THE COMMITTED `roland/tr8s`
	RATHER THAN ASSERTED**, because that is the whole lesson of this instrument: Roland's TR-6S
	Parameter Guide says "the TR-8S" twice, so the documents cannot be told apart by reading them.
	The numbers can.
	"""

	def test_the_whole_chart_arrives (self) -> None:
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])

		assert len(tr_6s.controls) == 34
		assert len(tr_6s.voice.voices) == 6
		assert tr_6s.voice.voices["bd"] == 36

	def test_every_instrument_has_tune_decay_level_and_ctrl (self) -> None:
		groups = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS]).grouped_controls()

		for voice in ("bd", "sd", "lt", "hc", "ch", "oh"):
			names = [control.name for control in groups[voice]]

			assert names == [f"{voice}_tune", f"{voice}_decay", f"{voice}_level", f"{voice}_ctrl"]

	def test_the_two_transmit_only_controls_are_never_offered_for_sending (self) -> None:
		"""And they are not the same case, which the file says and this pins.

		The fill-in trigger is sent in one mode only and the chart footnotes it. BEAT is sent
		always and footnoted nowhere - it is the one control here whose name is all that is known.
		"""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])
		unsendable = sorted(control.name for control in tr_6s.controls.values()
			if not control.is_sendable)

		assert unsendable == ["beat", "fill_in_trig"]

		account = " ".join((tr_6s.source or "").split())

		assert "Transmitted when the UTILITY:SOUND:LocalSw is SURFACE" in account
		assert "with no footnote at all: sent always, and never heard" in account
		assert "AND NOTHING SAYS WHAT BEAT IS" in account

	def test_thirty_three_of_its_thirty_four_numbers_are_the_tr_8s_s (self) -> None:
		"""The two-product question, settled by the numbers rather than by the names."""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])
		tr8s = pymidiinstrumentdefs.load("roland/tr8s", [CORPUS])

		mine = {control.cc for control in tr_6s.controls.values()}
		theirs = {control.cc for control in tr8s.controls.values()}

		assert len(mine & theirs) == 33

		# **AND THE ONE THE SIBLING HAS NOT IS BEAT.** A consumer that reached for the TR-8S's
		# map would miss it, and would offer twenty-two numbers this instrument ignores.
		assert mine - theirs == {2}
		assert len(theirs - mine) == 22

	def test_the_six_shared_instruments_answer_to_the_same_notes (self) -> None:
		"""Both maps, not only the one the format holds."""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])
		tr8s = pymidiinstrumentdefs.load("roland/tr8s", [CORPUS])

		for voice, note in tr_6s.voice.voices.items():
			assert tr8s.voice.voices[voice] == note

		# The alternate map is in each file's prose, because the format holds one map.
		assert "BD 35, SD 40, LT 41, HC 54, CH 44 and OH 55" in " ".join(
			(tr_6s.source or "").split())
		assert "bd 35, sd 40, lt 41, mt 45, ht 48, rs 56, hc 54, ch 44, oh 55" in prose_of(
			"roland", "tr8s")

	def test_two_chart_editions_disagree_about_one_note_and_both_claim_version_1_00 (self) -> None:
		"""So the number recorded is the one a third document agrees with, not the newer one."""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])
		account = " ".join((tr_6s.source or "").split())

		assert "The earlier file prints OH's alternate as 58 and the later prints 55" in account
		assert "neither the printed version nor the printed date changed" in account

		# The earlier edition is held and cited for nothing, so a reader can turn to it.
		assert "chart_eng01" in tr_6s.sources
		assert tr_6s.sources["chart_eng01"].edition == "eng01"

	def test_system_exclusive_is_not_recorded_because_two_documents_disagree (self) -> None:
		"""The chart marks it absent and the Parameter Guide gives a device ID for it."""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])

		assert tr_6s.midi.sysex is None

		account = " ".join((tr_6s.source or "").split())

		assert "CONTRADICT EACH OTHER ABOUT SYSTEM EXCLUSIVE" in account
		assert "the device ID numbers of both devices must match" in account

	def test_the_labels_are_the_charts_own_capitals (self) -> None:
		"""Because its remark column is the only name this maker gives these numbers."""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])

		assert tr_6s.controls["bd_tune"].label == "BD TUNE"
		assert tr_6s.controls["master_fx_ctrl"].label == "MASTER FX CTRL"

		# And the sibling's are in title case, which is not an inconsistency: it had a second
		# source to follow and this instrument has none.
		assert pymidiinstrumentdefs.load("roland/tr8s", [CORPUS]).controls["bd_tune"].label \
			== "BD Tune"

	def test_the_chart_is_three_releases_behind_the_firmware (self) -> None:
		"""And the history is what says the gap does not matter."""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])

		assert tr_6s.model.firmware == "2.00"
		assert tr_6s.sources["chart"].dated == "2020-04-22"

		said = prose_of("roland", "tr_6s")

		assert "MIDI sometimes becomes unsynchronized when a pattern is changed" in said
		assert "No release adds, removes or renumbers anything below" in said

	def test_two_channels_share_one_recorded_range (self) -> None:
		"""Notes and controls on one, kit changes on the other, and the format holds one span."""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])

		assert tr_6s.midi.channels == (1, 16)
		assert tr_6s.midi.program_change is not None
		assert tr_6s.midi.program_change.presets == 128

		account = " ".join((tr_6s.source or "").split())

		assert "Specifies the MIDI transmit/receive channel of the pattern sequencer" in account
		assert "channel for program change messages that switch kits" in account
		assert "no document gives the kit channel's default" in account

	def test_the_numbering_holes_are_the_charts_own (self) -> None:
		"""Two readings reached the same explanation from opposite ends, which is why it is here."""
		tr_6s = pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS])

		numbers = sorted(control.cc for control in tr_6s.controls.values() if control.cc)

		for missing in (21, 22, 26, 27, 98, 99, 100, 101, 103, 104, 105):
			assert missing not in numbers

		account = " ".join((tr_6s.source or "").split())

		assert "THE NUMBERING HAS HOLES AND THEY ARE THE CHART'S" in account
		assert "nobody should ever close them up" in account

	def test_the_local_switch_is_reachable_from_the_panel_and_nowhere_else (self) -> None:
		"""Which is what makes the fill-in trigger unreachable too."""
		account = " ".join(
			(pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS]).source or "").split())

		assert "AND NOTHING OVER MIDI CAN PUT IT THERE" in account
		assert "reachable from the panel and from nowhere else" in account

	def test_neither_unnumbered_cover_is_cited (self) -> None:
		"""The Super 6's lesson, one instrument later: a page number a document does not print.

		Both of these documents number every sheet but the first, so `p. 1` would land on the
		right sheet while naming a page that does not exist. What the covers say is in the file
		without a locator, because there is no locator to give.
		"""
		account = " ".join(
			(pymidiinstrumentdefs.load("roland/tr_6s", [CORPUS]).source or "").split())

		assert "NEITHER COVER IS CITED, AND THAT IS DELIBERATE" in account
		assert "because there is no locator to give" in account


class TestMpcLive:

	"""One user guide, ten machines, and the work was deciding which sentences are this one's.

	**EVERY CLAIM HERE ABOUT SCOPE IS CHECKED AGAINST THE DOCUMENT'S OWN CONVENTION**, which it
	announces in its introduction and then marks two different ways - one easy to enumerate and
	one that is a section's opening sentence and marks nothing under it.
	"""

	def test_it_carries_no_controls_and_the_file_says_why (self) -> None:
		"""The second Akai to reach that answer, and for a different reason from the first."""
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])

		assert not live.controls
		assert live.midi.control_change == "learned"

		account = " ".join((live.source or "").split())

		assert "assign external MIDI controllers to various parameters in your specific MPC project" \
			in account
		assert "These assignments will be saved with your MPC project" in account

		# The MPC Sample has no controls either, and nobody has established what it would do with
		# one. **That is a different answer**, and the corpus keeps them apart.
		sample = pymidiinstrumentdefs.load("akai/mpc_sample", [CORPUS])

		assert not sample.controls
		assert sample.midi.control_change is None

	def test_the_guide_names_the_ten_machines_it_covers_and_two_it_does_not (self) -> None:
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert ("MPC X, MPC X Special Edition, MPC Live, MPC Live II, MPC One, MPC One+, "
			"MPC One G2, MPC Key 61, MPC Key 37, and MPC Key 37 G2") in account

		assert "MPC Live III and MPC XL, which have a separate User Guide" in account

	def test_a_sections_opening_sentence_scopes_everything_under_it (self) -> None:
		"""The mechanism that marks nothing, and the one that would have cost two wrong fields."""
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])
		account = " ".join((live.source or "").split())

		assert "The keyboard control screen allows you to edit the functions of the keybed on " \
			"MPC Key 61, Key 37, and Key 37 G2" in account

		# Which is why neither of that screen's two MIDI settings is recorded here - and the
		# file says that is the reason, rather than that nothing is said.
		assert live.voice.aftertouch is None
		assert "The one page that configures a received one is the keyboard screen" in account

	def test_the_machine_itself_offers_controls_it_does_not_have (self) -> None:
		"""The third place the ten machines must be told apart, and the only unverifiable one."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "will show many more hardware controls than are actually available on your MPC " \
			"hardware" in account
		assert "the only one a document cannot be checked against" in account

	def test_the_pads_send_aftertouch_three_ways_and_the_field_holds_one (self) -> None:
		"""The second reader caught this: it is stated, and the earlier draft said it was not.

		`voice.aftertouch` records what an instrument answers to. What this document states is
		what the pads **send**, per pad, at the owner's choice of none, channel or poly - so the
		field is unset because no single value is right, not because the page is silent.
		"""
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])
		account = " ".join((live.source or "").split())

		assert live.voice.aftertouch is None

		assert "Off: The pad will not send any aftertouch messages" in account
		assert "the aftertouch message each pad sends will be independent from the others" in account
		assert "AND NOT BECAUSE NOTHING IS SAID" in account

		# And velocity is the same shape: what the pads send, not what it answers to.
		assert live.voice.velocity is None
		assert "pressing the pad will send a note at full-level (127) always" in account

	def test_three_times_it_says_a_fixed_map_exists_and_declines_to_print_it (self) -> None:
		"""Which is a sharper absence than silence, and is why control_change says learned."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "the Q-Links are fixed to a selection of MIDI performance controls" in account
		assert "Standard MIDI control change assignments" in account
		assert "Classic MPC (the default MIDI note map of classic MPCs)" in account

	def test_it_states_its_own_coverage_three_times_and_once_differently (self) -> None:
		"""Ten, then eight, then ten - and the eight is the one that defines the term used."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "This chapter explains the features and functions of each MPC v3.9-supported " \
			"model" in account
		assert "dropping the MPC X and the MPC X Special Edition" in account

		# And it inherits between two pairs of machines, but not this one and its successor.
		assert "also apply to the MPC X Special Edition unless otherwise noted" in account
		assert "There is no such rule for this machine and the MPC Live II" in account

	def test_the_absence_is_recorded_with_its_two_limits (self) -> None:
		"""A text search cannot see a screenshot, and 43 pages are missing from the contents."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "Every MIDI screen in this guide is an image" in account
		assert "FORTY-THREE PAGES ARE MISSING FROM THE TABLE OF CONTENTS" in account

		# And the one place an incoming controller message has a documented effect.
		assert "the one place in 530 pages where an incoming controller message is given a " \
			"documented effect" in account

	def test_an_omission_from_the_spec_table_is_binding_and_unsearchable (self) -> None:
		"""No CV, no thru-port, no footswitch - so three unqualified chapters are not this one's."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "An absence from a table is as binding as a parenthetical and cannot be searched " \
			"for" in account

	def test_the_model_names_are_prefixes_of_each_other (self) -> None:
		"""A substring test over-includes, silently, and always by claiming more than was said."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "This instrument's name is the whole of the next one's: MPC Live, MPC Live II" \
			in account
		assert "always by claiming more than the maker said" in account

	def test_the_one_list_of_controller_numbers_is_not_a_control_map (self) -> None:
		"""And four of its numbers are not control changes at all."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "Check these boxes to allow the listed MIDI Control Change messages to pass " \
			"through the track" in account
		assert "not what this instrument does when it receives one" in account

		# 128 to 131 are above the 127 a control change can carry.
		assert "CC128 Pitchbend, CC129 Channel Pressure, CC130 Program Change and CC131 " \
			"Aftertouch" in account

	def test_the_note_map_is_the_owners_and_its_presets_are_named_twice (self) -> None:
		"""One document, one list of three, two spellings of the second - recorded, not resolved."""
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])

		assert not live.voice.voices

		account = " ".join((live.source or "").split())

		assert "lets you assign specific MIDI notes to your MPC hardware pads" in account

		# The two spellings, each quoted from its own page, and the file resolving neither.
		assert "Chromatic C-2 (an ascending" in account
		assert "Chromatic C1, Chromatic C2, or Classic MPC" in account
		assert "two spellings of the second of them, and nothing here chooses between them" \
			in account

	def test_the_clock_setting_has_four_positions_and_the_field_holds_two (self) -> None:
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])

		assert live.midi.clock == "both"

		account = " ".join((live.source or "").split())

		assert "communication from Ableton Link (Ableton Link), or none of these (Off)" in account
		assert "MIDI Time Code and Ableton Link are the other choices and no field here " \
			"records them" in account

		# And MIDI Machine Control, which no field here records either.
		assert "will be able to receive MIDI Machine Control (MMC) information" in account

	def test_program_change_goes_both_ways_and_reaches_no_recorded_count (self) -> None:
		"""Because what it selects is a setting with two positions and neither count is given."""
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])

		assert live.midi.program_change is not None
		assert live.midi.program_change.receives is True
		assert live.midi.program_change.sends is True
		assert live.midi.program_change.presets is None

		account = " ".join((live.source or "").split())

		assert "an incoming MIDI program change message will change: a Sequence or Track" in account
		assert "one number would be wrong for one of them" in account

	def test_a_glossary_reads_like_a_specification_and_is_not_one (self) -> None:
		"""Three of the terms a control map would be written in appear only there."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "the MIDI specification being explained and not this instrument being described" \
			in account
		assert "can range from 0 to 127" in account

	def test_nothing_is_recorded_that_no_document_states (self) -> None:
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])

		assert live.midi.sysex is None
		assert live.midi.nrpn is None
		assert live.voice.polyphony is None
		assert live.voice.velocity is None

		# Pitch bend is settable and its range is not published.
		assert live.voice.pitch_bend is not None
		assert live.voice.pitch_bend.programmable is True
		assert live.voice.pitch_bend.semitones is None

	def test_two_midi_inputs_and_two_outputs_which_no_field_here_records (self) -> None:
		"""The first instrument in this corpus with more than one port of each."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).source or "").split())

		assert "(2) 5-pin MIDI inputs" in account
		assert "(2) 5-pin MIDI outputs" in account
		assert "a channel number in this definition does not say which socket it arrives on" \
			in account

	def test_the_firmware_is_the_operating_systems_and_the_guide_is_a_patch_behind (self) -> None:
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])

		assert live.model.firmware == "3.9.1"
		assert live.sources["guide"].edition == "v3.9"

		said = prose_of("akai", "mpc_live")

		assert "Internal improvements and maintenance updates" in said


class TestProphet5:

	"""The 2020 instrument, whose implementation is also the Prophet-10's and is older than it.

	**THE NAME ALONE IDENTIFIES NOTHING HERE**: Sequential's Prophet-5 of 2020 is a MIDI
	instrument, the Prophet-5 of 1978 is not, and the Rev 3.3 of the 1980s had a MIDI of its own
	that nothing in this corpus describes.
	"""

	def test_the_whole_implementation_arrives (self) -> None:
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert len(prophet.controls) == 64
		assert len(prophet.groups) == 10

		# 59 are the parameter table's and five are performance controllers from the message
		# tables, which is why the performance group is the one that mixes the two.
		assert prophet.controls["osc_a_frequency"].cc == 3
		assert prophet.controls["mod_wheel"].cc == 1

	def test_the_makers_typo_is_kept_because_it_is_printed_twice (self) -> None:
		"""ON/FF for ON/OFF, in the controller table and in the NRPN table both."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert prophet.controls["osc_a_saw_on_ff"].label == "OSC A SAW ON/FF"
		assert prophet.controls["osc_a_saw_on_ff"].cc == 15

		assert "it is printed that way in the NRPN table as well" in " ".join(
			(prophet.source or "").split())

	def test_only_the_breath_controller_is_one_way (self) -> None:
		"""Measured over two lists, received and transmitted, rather than asserted."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		one_way = sorted(control.name for control in prophet.controls.values()
			if control.direction != "both")

		assert one_way == ["breath_controller"]
		assert prophet.controls["breath_controller"].direction == "transmits"

	def test_two_mode_messages_and_one_contradiction_are_left_out_by_name (self) -> None:
		account = " ".join(
			(pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS]).source or "").split())
		numbers = {control.cc for control in
			pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS]).controls.values()}

		for refused in (121, 123, 13):
			assert refused not in numbers

		assert "All Notes Off: Clear all MIDI notes" in account
		assert "Expression is controller 11" in account
		assert "There is no third statement anywhere to settle which the maker meant" in account

	def test_nrpn_is_the_preferred_method_and_the_numbers_are_not_recorded (self) -> None:
		"""The maker says preferred in as many words, and the two tables do not line up."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert prophet.midi.nrpn == "preferred"
		assert not any(control.nrpn for control in prophet.controls.values())

		account = " ".join((prophet.source or "").split())

		assert "NRPNs are the preferred method of parameter transmission" in account
		assert "no arithmetic relates one number to the other" in account

	def test_it_receives_poly_pressure_and_its_keyboard_sends_channel (self) -> None:
		"""The Super 6's shape from the other side, and the one field cannot say it twice."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert prophet.voice.aftertouch == "poly"

		account = " ".join((prophet.source or "").split())

		assert "the transmitted table has \"Channel Pressure\" (p. 3) and no polyphonic row at " \
			"all" in account
		assert "The Prophet-5 provides monophonic (or \"channel\") aftertouch" in account

	def test_the_bend_range_is_per_program_and_counted_two_ways (self) -> None:
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert prophet.voice.pitch_bend is not None
		assert prophet.voice.pitch_bend.semitones == 12
		assert prophet.voice.pitch_bend.programmable is True

		# And the controller counts the same twelve values from zero.
		assert prophet.controls["pitch_wheel_range"].range == (0, 11)

		assert "A setting of 12 equals an octave" in " ".join((prophet.source or "").split())

	def test_four_hundred_programs_and_a_program_change_reaches_forty (self) -> None:
		"""And the row that says so contradicts itself, which the file quotes rather than fixes."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert prophet.midi.program_change is not None
		assert prophet.midi.program_change.presets == 400

		account = " ".join((prophet.source or "").split())

		assert "The Prophet-5 contains a total of 400 programs" in account
		assert "AND THAT PROGRAM CHANGE ROW CONTRADICTS ITSELF" in account
		assert "Nothing here resolves it" in account

	def test_the_implementation_is_also_the_prophet_10s (self) -> None:
		"""Settled by the documents, three ways, and not by reasoning from the names."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		# The sibling's guide is held and cited for exactly one thing.
		assert "sibling_guide" in prophet.sources
		assert prophet.sources["sibling_guide"].title == "Prophet-10 User's Guide"

		said = prose_of("sequential", "prophet_5")

		assert "Cited for one thing and nothing else" in said
		assert "identical but for the model name and where the lines wrap" in said
		assert "Prophet-5/10" in " ".join((prophet.source or "").split())

	def test_the_implementation_is_older_than_two_operating_systems (self) -> None:
		"""So the published tables are known to be incomplete, and the file says so."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert prophet.model.firmware == "2.1.0"
		assert prophet.sources["implementation"].edition == "1.4"
		assert prophet.sources["implementation"].dated == "2021-03-11"

		account = " ".join((prophet.source or "").split())

		assert "Neither addendum mentions MIDI and neither gives a number for anything it adds" \
			in account
		assert "known to be incomplete for the instrument as it ships" in account

	def test_the_guides_front_matter_is_numbered_in_roman_numerals (self) -> None:
		"""The Super 6's trap at rank 64, met again three ranks later and measured."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert prophet.sources["guide"].page_offset == 11
		assert prophet.sources["implementation"].page_offset == 0

		assert "sheets 8 to 11 print viii, ix, x and xi" in prose_of("sequential", "prophet_5")

	def test_a_parameter_change_is_cc_or_nrpn_and_never_both (self) -> None:
		"""Each global takes one of three values, so a panel offering both describes no machine."""
		account = " ".join(
			(pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS]).source or "").split())

		assert "They are transmitted when Param Xmit is set to CC, and recognized/received when " \
			"Param Rcv is set to CC" in account
		assert "A panel that offered both at once would be describing a machine that cannot " \
			"exist" in account

	def test_the_two_maps_agree_about_every_range_they_share (self) -> None:
		"""Fifty names in both tables and not one range differs - measured, by two readings."""
		account = " ".join(
			(pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS]).source or "").split())

		assert "Measured over the 50 parameter names printed in both: **not one range differs.**" \
			in account
		assert "disagree about numbering and never about scaling" in account

	def test_six_more_defects_are_recorded_and_none_resolved (self) -> None:
		"""Including the one a reader would be hurt by: two system exclusive identities."""
		account = " ".join(
			(pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS]).source or "").split())

		assert "VELOCTIY > FILTER" in account
		assert "This instrument's system exclusive identity is given two ways" in account
		assert "51 against 49, and nothing in the document says which" in account
		assert "the RPN reset message is given the wrong controller numbers" in account
		assert "nothing in the document says how to save the edit buffer" in account
		assert "a program is addressed three incompatible ways" in account

	def test_the_maker_names_the_revision_on_a_page_it_does_not_number (self) -> None:
		"""The implementation says nothing; the guide says it in unnumbered front matter."""
		said = prose_of("sequential", "prophet_5")

		assert "AND THE MAKER NAMES IT ON A PAGE IT DOES NOT NUMBER" in said
		assert "Or as we call it around here, the Prophet-5 Rev4" in said
		assert "because there is no locator to give" in said

	def test_the_implementation_never_mentions_the_prophet_10 (self) -> None:
		"""So the sibling question is settled by three other documents, not by this one."""
		said = prose_of("sequential", "prophet_5")

		assert "THE IMPLEMENTATION ITSELF NEVER MENTIONS THE PROPHET-10, not once in thirteen" \
			in said

	def test_the_clock_and_the_transport_are_absent_rather_than_denied (self) -> None:
		prophet = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])

		assert prophet.midi.clock is None
		assert prophet.midi.transport is None
		assert prophet.midi.sysex is True

		assert "not as a no, as nothing at all" in " ".join((prophet.source or "").split())


class TestProphet10:

	"""The 2020 instrument, which answers to the Prophet-5's implementation and has ten voices.

	**THE NAME ALONE IDENTIFIES NOTHING HERE EITHER**: the Prophet-10 of the early 1980s is not
	this instrument, and nothing in this corpus describes it.
	"""

	def test_ten_voices_and_nine_with_a_plug_in_the_gate_in_jack (self) -> None:
		prophet = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert prophet.voice.polyphony == 10

		account = " ".join((prophet.source or "").split())

		assert "The Prophet-10 is a ten-voice, polyphonic analog synthesizer" in account
		assert "its keyboard polyphony is reduced to 9 voices" in account

	def test_the_implementation_never_names_it_and_three_things_say_it_is_its (self) -> None:
		"""A documentation page, the instrument's own guide, and one operating system for both."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert prophet.sources["implementation"].title == "Prophet-5 MIDI Implementation"

		account = " ".join((prophet.source or "").split())

		assert "THE IMPLEMENTATION NEVER NAMES THE PROPHET-10" in account
		assert "For a list of Prophet-10 CCs and NRPNs, see the Prophet-10 Support page at " \
			"Sequential.com" in account
		assert "the latest operating system for the Prophet-5 and Prophet-10 keyboards and " \
			"desktop modules" in account

	def test_its_guide_is_the_prophet_5s_edited_and_four_sentences_were_not (self) -> None:
		"""The sibling's guide is held and cited for what the two say differently."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert prophet.sources["sibling_guide"].title == "Prophet-5 User's Guide"

		account = " ".join((prophet.source or "").split())

		assert "the two differ in twenty-one places" in prose_of("sequential", "prophet_10")
		assert "The envelopes of the fifth voice are triggered by the gate in signal" in account
		assert "may cause the Prophet-5 to respond unpredictably" in account
		assert "(now you can stack 1-5 voices)" in account

	def test_it_is_bi_timbral_and_no_part_is_recorded (self) -> None:
		"""OS 2.0 gave it two layers and no published word says how a sender reaches the second."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert not prophet.parts

		account = " ".join((prophet.source or "").split())

		assert "becomes bi-timbral and allows you to play two different sounds/programs at " \
			"once" in account
		assert "nothing published says how" in account

	def test_the_nrpns_are_left_out_to_keep_it_the_prophet_5s (self) -> None:
		"""Two definitions of one document should never disagree about it."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert prophet.midi.nrpn == "preferred"
		assert not any(control.nrpn for control in prophet.controls.values())

		account = " ".join((prophet.source or "").split())

		assert "THE NRPN TABLE IS NOT RECORDED, AND THAT IS TO KEEP THIS FILE THE PROPHET-5'S" \
			in account
		assert "a question for both files at once" in account

	def test_the_firmware_is_on_the_makers_operating_system_page (self) -> None:
		"""Saved as text, which is a source with no pages to turn to."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert prophet.model.firmware == "2.1.0"
		assert prophet.sources["os"].paginated is False
		assert "The current version of the OS is Main 2.1.0" in prose_of("sequential", "prophet_10")

	def test_two_ranges_the_guide_gives_differently_are_carried_as_the_implementation_prints (
		self) -> None:
		"""Unison detune and resonance: recorded, and neither resolved."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert prophet.controls["unison_detune"].range == (0, 7)
		assert prophet.controls["resonance"].range == (0, 120)

		account = " ".join((prophet.source or "").split())

		assert "A setting of 0 is minimum detuning. A setting of 8 is maximum detuning" in account
		assert "the resonance parameter has an internal value range of 0 to 127" in account

	def test_bank_select_names_four_factory_banks_where_the_guide_has_five_groups (self) -> None:
		account = " ".join(
			(pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS]).source or "").split())

		assert "AND BANK SELECT NAMES FIVE USER BANKS AND ONLY FOUR FACTORY ONES" in account
		assert "6 - 9 select factory banks 1 - 4" in account

	def test_the_unison_rows_count_to_ten (self) -> None:
		"""On a document named for a five-voice instrument, and nothing says what each value means."""
		prophet = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert prophet.controls["unison_voice_count"].range == (0, 10)
		assert "AND THE IMPLEMENTATION'S UNISON ROWS COUNT TO TEN" in " ".join(
			(prophet.source or "").split())


class TestTheTwoProphets:

	"""The Prophet-5 and the Prophet-10 are one MIDI implementation, established not assumed.

	Sequential offers one file under both instruments, byte for byte; the Prophet-10's guide
	sends its reader to it; and the two guides differ in twenty-one places with the model names
	masked, every one of them the voice count or the front matter.

	So the two definitions carry the same controls, and these tests say so out loud: if somebody
	corrects one of them, the failure is the reminder to look at the other. **A difference found
	in a document is a reason to change these tests**, not a reason to doubt them - but it should
	be a document that changes them.
	"""

	def test_they_carry_the_same_controls (self) -> None:
		"""Every name, number, range, direction and group of all 64."""
		five = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])
		ten = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		def surface (definition: pymidiinstrumentdefs.definition.Definition) -> dict[str, object]:
			return {
				name: (control.label, control.cc, control.lsb, control.nrpn,
					tuple(control.values.items()), control.range, control.nrpn_range,
					control.unit, control.direction, control.group)
				for name, control in definition.controls.items()
			}

		assert surface(five) == surface(ten)
		assert len(ten.controls) == 64
		assert five.groups == ten.groups

	def test_they_cite_one_implementation_and_describe_one_firmware (self) -> None:
		five = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])
		ten = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert five.sources["implementation"].sha256 == ten.sources["implementation"].sha256
		assert five.model.firmware == ten.model.firmware == "2.1.0"

	def test_they_agree_on_everything_but_the_voice_count (self) -> None:
		"""Which is the one thing the two guides are edited to say differently."""
		five = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])
		ten = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		for field in ("aftertouch", "velocity", "pitch_bend"):
			assert getattr(five.voice, field) == getattr(ten.voice, field), field

		assert five.midi == ten.midi

		assert five.voice.polyphony == 5
		assert ten.voice.polyphony == 10

	def test_each_is_named_as_its_own_guide_names_it (self) -> None:
		five = pymidiinstrumentdefs.load("sequential/prophet_5", [CORPUS])
		ten = pymidiinstrumentdefs.load("sequential/prophet_10", [CORPUS])

		assert five.model.name == "Prophet-5"
		assert ten.model.name == "Prophet-10"
		assert five.model.manufacturer == ten.model.manufacturer == "Sequential"


class TestMicroKORG2:

	"""The instrument whose maker publishes the same map three times, and the three agree.

	**IT IS NOT `korg/microkorg`**, which is also in this corpus and whose numbers are the
	player's to assign where this one's are fixed.  The names are prefixes of each other in
	both directions, which is why nothing here was matched by substring.
	"""

	def test_the_whole_map_arrives (self) -> None:
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		assert len(microkorg2.controls) == 181
		assert len(microkorg2.groups) == 23

		by_control_change = [c for c in microkorg2.controls.values() if c.cc is not None]
		by_nrpn = [c for c in microkorg2.controls.values() if c.nrpn is not None]

		# 71 from the implementation's panel table, plus the modulation wheel and the damper
		# pedal, which it keeps in its channel-message tables instead.
		assert len(by_control_change) == 73

		# Every one of the implementation's NRPN rows, including the eight whose address it
		# garbles and the manual supplies.
		assert len(by_nrpn) == 108

		addresses = [control.nrpn for control in by_nrpn]
		assert len(set(addresses)) == len(addresses), "two NRPNs share an address"

		assert microkorg2.controls["filter_cutoff"].cc == 74
		assert microkorg2.controls["vocoder_band1_level"].nrpn == 0x05 * 128 + 0x10

	def test_the_three_statements_of_the_map_agree (self) -> None:
		"""The implementation's table, the chart's list and the manual's own annotations."""
		account = " ".join(
			(pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS]).source or "").split())

		assert "the remaining 71 are the implementation's table exactly" in account
		assert "**70 controller numbers**, which are 69 of the" in account
		assert "**77 NRPN addresses**" in account

	def test_the_manual_puts_eight_nrpn_addresses_right (self) -> None:
		"""The implementation gives six parameters one address and numbers two others twice.

		**This is not choosing between a maker's two columns**, which #2522 forbids.  The
		manual's own parameter pages carry a second numbering scheme, `(NRPN m, n)`, which
		is coherent where the implementation is not and agrees with it everywhere it is.
		"""
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		# The implementation prints 04/20 for all six; the manual annotates 4, 32...37.
		destinations = [microkorg2.controls[f"patch{n}_destination"].nrpn for n in range(1, 7)]
		assert destinations == [4 * 128 + lsb for lsb in range(32, 38)]

		# And 6, 1 / 6, 2 / 6, 3, where the implementation's hexadecimal column reads
		# 01 / 01 / 02 and would put Speed on top of Intensity.
		hard_tune = [microkorg2.controls[name].nrpn
			for name in ("hardtune_intensity", "hardtune_speed", "hardtune_formant")]
		assert hard_tune == [6 * 128 + lsb for lsb in (1, 2, 3)]

		account = " ".join((microkorg2.source or "").split())

		assert "Hardtune Speed is printed as \"06 | 01 ( 2)\"" in account
		assert "ALL SIX `Patch N Destination` ROWS CARRY THE SAME ADDRESS" in account
		assert "THE MANUAL SETTLES BOTH, ON ITS OWN PAGES AND IN ITS OWN SCHEME" in account
		assert "not a choice between two columns with nothing to settle it" in account

	def test_four_absences_were_checked_rather_than_assumed (self) -> None:
		"""Each one is a thing a reader would otherwise go looking for."""
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])
		account = " ".join((microkorg2.source or "").split())

		assert "does not have a half-damper function" in account
		assert "Controller 50 is the one gap inside the OSC 3 run" in account
		assert "there is no global dump" in account
		assert "the manual never writes \"bank select\", anywhere in its 134 pages" in account

		# The pitch bend range is one of them: a program parameter no number reaches.
		assert not any(control.label.startswith("Pitch Bend")
			for control in microkorg2.controls.values())

	def test_two_timbres_on_two_channels_and_no_control_names_either (self) -> None:
		"""The same numbers reach whichever timbre's channel they arrive on."""
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		assert set(microkorg2.parts) == {"timbre_1", "timbre_2"}

		# Timbre 1 is the global channel itself; Timbre 2 is set on its own.
		assert microkorg2.parts["timbre_1"].channel_offset == 0
		assert microkorg2.parts["timbre_2"].is_assigned

		# A program change selects a program, which contains both, so there is nothing a
		# second channel could select on its own.
		assert "program_change" in (microkorg2.parts["timbre_1"].receives or ())
		assert "program_change" not in (microkorg2.parts["timbre_2"].receives or ())

		assert not any(control.part for control in microkorg2.controls.values())

	def test_the_firmware_is_behind_the_release_notes_on_purpose (self) -> None:
		"""Which is what `docs/adding-an-instrument.md` says to do, and why this flags itself."""
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		assert microkorg2.model.firmware == "1.02"
		assert microkorg2.sources["release_notes"].edition == "2.0.2"

		said = prose_of("korg", "microkorg2")

		assert "THE NEWEST SYSTEM THESE DOCUMENTS STILL DESCRIBE" in said
		assert "return nothing at all in 1,784 lines" in said

	def test_the_chart_is_a_picture_and_says_so (self) -> None:
		"""Printed page 133 carries 2,362 drawings and 79 characters, so it was read by eye."""
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		assert microkorg2.sources["manual"].pictured_pages == (133,)

		account = " ".join((microkorg2.source or "").split())

		assert "THE CHART'S PAGE CANNOT BE READ AS TEXT" in account
		assert "2,362 vector drawings and 79 characters" in account

	def test_the_implementation_has_no_pages_at_all (self) -> None:
		"""Korg's plain-text shape, as the microKORG's and the wavestate's are."""
		implementation = pymidiinstrumentdefs.load(
			"korg/microkorg2", [CORPUS]).sources["implementation"]

		assert implementation.paginated is False
		assert implementation.file_page(1) is None

	def test_the_maker_spells_its_own_instrument_two_ways (self) -> None:
		"""microKORG2 on the pages and in the manual, microKORG 2 in the two map documents."""
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		assert microkorg2.model.name == "microKORG2"

		said = prose_of("korg", "microkorg2")

		assert "AND KORG SPELLS THE NAME TWO WAYS IN ITS OWN DOCUMENTS" in said
		assert "the other is recorded rather than tidied away" in said

	def test_it_is_not_the_microkorg_and_the_difference_is_the_numbers (self) -> None:
		"""The older one's numbers are defaults; this one's are the maker's and fixed."""
		microkorg = pymidiinstrumentdefs.load("korg/microkorg", [CORPUS])
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		assert microkorg.model.firmware is None
		assert microkorg2.model.firmware == "1.02"

		account = " ".join((microkorg2.source or "").split())

		assert "THAT IS THE DIFFERENCE FROM THE microKORG" in account
		assert "mentions microKORG 2 three times and no other microKORG at all" in account

	def test_what_the_chart_settles_that_the_implementation_does_not (self) -> None:
		"""Mode, after touch, release velocity and the transport, all read off one page."""
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		assert microkorg2.midi.mode == 3
		assert microkorg2.voice.aftertouch == "none"

		assert microkorg2.voice.velocity is not None
		assert microkorg2.voice.velocity.note_on == "received"
		assert microkorg2.voice.velocity.note_off is False

		# A checked absence rather than a silence: the chart's Commands row is X both ways.
		assert microkorg2.midi.transport == "none"
		assert microkorg2.midi.clock == "both"

	def test_the_two_documents_disagree_about_two_things_and_it_is_recorded (self) -> None:
		"""Local control and what is sent as all-notes-off. Neither is publishable anyway."""
		account = " ".join(
			(pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS]).source or "").split())

		assert "AND THE TWO DOCUMENTS DISAGREE ABOUT TWO THINGS" in account
		assert "says X in both columns" in account

	def test_the_colour_variants_are_settled_three_ways (self) -> None:
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])
		account = " ".join((microkorg2.source or "").split())

		assert "two limited edition color models" in account
		assert "MK-2: 2.2 kg/4.85 lb, MK-2 MBK/MWH: 2.1 kg/4.63 lb" in account
		assert "One system, one manual, one map" in account

	def test_two_published_lists_are_short_for_the_current_system (self) -> None:
		"""Right for 1.02, which is what this file says it describes, and said out loud."""
		microkorg2 = pymidiinstrumentdefs.load("korg/microkorg2", [CORPUS])

		assert microkorg2.controls["patch1_source1"].nrpn_range == (0, 17)
		assert "one_shot" in microkorg2.controls["osc1_wave"].values
		assert "user" not in microkorg2.controls["osc1_wave"].values

		account = " ".join((microkorg2.source or "").split())

		assert "ARE RIGHT FOR SYSTEM 1.02 AND SHORT FOR 2.0.2" in account


class TestCircuitRhythm:

	"""The third Circuit here, and the first family of three this corpus can compare.

	**The headline is the comparison, not the count**: 64 of this machine's 74 addresses are
	also used by `novation/circuit`, and only nine of them mean the same thing.
	"""

	def test_the_whole_reference_arrives (self) -> None:
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])

		assert len(rhythm.controls) == 74
		assert len(rhythm.groups) == 17

		by_cc = [c for c in rhythm.controls.values() if c.cc is not None]
		by_nrpn = [c for c in rhythm.controls.values() if c.nrpn is not None]

		assert len(by_cc) == 50
		assert len(by_nrpn) == 24

		# The NRPNs are printed MSB:LSB, so 1:18 is 146.
		assert rhythm.controls["reverb_type"].nrpn == 1 * 128 + 18
		assert rhythm.controls["sampler_pitch"].cc == 21

	def test_eleven_addresses_mean_one_thing_across_the_family (self) -> None:
		"""Ten effect NRPNs, and the one control change that survives the instrument.

		A first pass said nine and a looser one said twelve, so the eleven are listed by
		address here as they are in `Notes/4468_compare_with_the_siblings.py`, rather than
		matched by folding labels - which is what got it wrong both times.
		"""
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])
		siblings = [pymidiinstrumentdefs.load(name, [CORPUS])
			for name in ("novation/circuit", "novation/circuit_tracks")]

		one_meaning = [("cc", 71)] + [("nrpn", n) for n in
			(134, 135, 136, 137, 138, 139, 146, 147, 148, 149)]

		assert len(one_meaning) == 11

		for kind, number in one_meaning:
			assert any(getattr(c, kind) == number for c in rhythm.controls.values()), \
				f"the Rhythm no longer uses {kind} {number}"

			for sibling in siblings:
				assert any(getattr(c, kind) == number for c in sibling.controls.values()), \
					f"{sibling.model.name} no longer uses {kind} {number}"

		# And controller 21 is on both machines and is a different parameter on each.
		assert rhythm.controls["sampler_pitch"].cc == 21

		theirs_at_21 = [control.label for control in siblings[0].controls.values()
			if control.cc == 21]

		assert theirs_at_21, "the Circuit no longer uses controller 21, so this has nothing to say"
		assert "pitch" not in theirs_at_21[0].lower()

		said = " ".join(prose_of("novation", "circuit_rhythm").split())

		assert "ONLY ELEVEN OF THEM MEAN THE SAME THING" in said
		assert "the eleventh is the one control change" in said

	def test_the_master_filters_frequency_moved_and_its_resonance_did_not (self) -> None:
		"""The most dangerous line in the family, and the reason the comparison was run."""
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])

		assert rhythm.controls["lp_hp_filter_frequency"].cc == 79
		assert rhythm.controls["lp_hp_filter_resonance"].cc == 71

		# And this machine uses 74 for nothing, where both siblings put the filter there.
		assert not any(control.cc == 74 for control in rhythm.controls.values())

		for name in ("novation/circuit", "novation/circuit_tracks"):
			sibling = pymidiinstrumentdefs.load(name, [CORPUS])

			assert any(control.cc == 74 and "frequency" in control.label
				for control in sibling.controls.values()), name

		said = " ".join(prose_of("novation", "circuit_rhythm").split())

		assert "AND THE MASTER FILTER'S FREQUENCY MOVED" in said
		assert "this machine uses 74 for nothing at all" in said

	def test_five_rows_the_maker_prints_and_says_are_not_supported (self) -> None:
		"""A stated absence, named rather than dropped."""
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])

		for absent in ("master_volume", "click_on_off", "click_volume", "click_rate"):
			assert absent not in rhythm.controls

		assert "master" not in rhythm.groups
		assert "click" not in rhythm.groups

		account = " ".join((rhythm.source or "").split())

		assert "marked NOT SUPPORTED: Master Volume, and the Click's On/Off, Volume, Rate and" \
			in account

	def test_three_defaults_are_on_the_parameters_own_scale_and_are_not_published (self) -> None:
		"""Which the format's own validator caught, by refusing one outside its range."""
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])

		for scaled in ("sampler_pitch", "sampler_slope", "mixer_pan"):
			assert rhythm.controls[scaled].default is None, scaled

		# The fourth of the same shape keeps its default, because 64 is outside the signed
		# scale the maker prints and so can only be a byte.
		assert rhythm.controls["lp_hp_filter_frequency"].default == 64

		account = " ".join((rhythm.source or "").split())

		assert "it is nought semitones, which is byte 64" in account

	def test_eight_sample_tracks_and_a_project_on_sixteen_channels (self) -> None:
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])

		assert set(rhythm.parts) == {"sample_track", "project"}
		assert rhythm.parts["sample_track"].count == 8
		assert rhythm.parts["sample_track"].is_assigned

		# The tracks take parameters on their own channels; the notes arrive on the
		# Project's channel instead, which is why the two parts receive different things.
		assert rhythm.parts["sample_track"].receives == ("controls",)
		assert rhythm.parts["project"].receives == ("notes", "program_change")

		assert rhythm.voice.voices == {
			"sample_track_1": 36, "sample_track_2": 38, "sample_track_3": 40,
			"sample_track_4": 41, "sample_track_5": 43, "sample_track_6": 45,
			"sample_track_7": 47, "sample_track_8": 48,
		}

	def test_only_the_sampler_parts_name_a_part_because_only_they_are_given_one (self) -> None:
		"""The reference names a channel for one of its four tables."""
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])

		parted = {c.name for c in rhythm.controls.values() if c.part}

		assert len(parted) == 25
		assert all(rhythm.controls[name].part == "sample_track" for name in parted)

		account = " ".join((rhythm.source or "").split())

		assert "the Effects and Global Control Data tables name no channel at all" in account

	def test_system_exclusive_is_left_out_rather_than_taken_from_the_family (self) -> None:
		"""Both siblings record it as true; this one's documents never mention it."""
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])

		assert rhythm.midi.sysex is None
		assert pymidiinstrumentdefs.load("novation/circuit", [CORPUS]).midi.sysex is True
		assert pymidiinstrumentdefs.load("novation/circuit_tracks", [CORPUS]).midi.sysex is True

		account = " ".join((rhythm.source or "").split())

		assert "112 sheets" in account
		assert "an enumerated silence and not a denial" in account

	def test_the_three_circuits_agree_about_the_transport (self) -> None:
		"""One maker's one sentence, printed three times, and now read one way.

		All three Programmer's Reference Guides head the list "Supported Realtime Messages"
		and none of them says which direction any of start, stop, continue or the timing
		clock goes. The switch is the evidence all three documents carry: Rx and Tx are
		separate settings over a MIDI Clock category that is on both ways by default.
		"""
		for name in ("novation/circuit", "novation/circuit_rhythm", "novation/circuit_tracks"):
			assert pymidiinstrumentdefs.load(name, [CORPUS]).midi.transport == "both", name

		# The file that changed says it changed, and why its old reading could not settle three.
		tracks = " ".join(prose_of("novation", "circuit_tracks").split())

		assert "THIS FILE RECORDED `receives` UNTIL THE THIRD CIRCUIT ARRIVED" in tracks
		assert "holds for neither sibling's" in tracks

		# And this one no longer calls the disagreement open.
		rhythm = " ".join(prose_of("novation", "circuit_rhythm").split())

		assert "BOTH, AND ALL THREE CIRCUITS AGREE ABOUT IT" in rhythm
		assert "THE FAMILY DID NOT ALWAYS AGREE" in rhythm

		# And no file still describes the Circuit Tracks as recording receives.
		assert "records receives" not in rhythm
		assert "raised rather than settled here" not in rhythm

	def test_the_firmware_is_the_only_one_named_and_the_reference_names_none (self) -> None:
		"""And the by-name test is reported as the weak evidence it is on this document."""
		rhythm = pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS])

		assert rhythm.model.firmware == "2.0"
		assert rhythm.sources["addendum"].edition == "V1 English"

		account = " ".join((rhythm.source or "").split())

		assert "MENTIONS MIDI NOT ONCE in eleven sheets" in account
		assert "THAT TEST PROVES MUCH LESS HERE THAN IT DID ON THE LAST INSTRUMENT" in account

		# What does tie the two documents together is a redundancy, and it is the figure
		# worth asserting rather than the argument.
		assert "fourteen of those defaults are" in account
		assert "All fourteen agree" in account

	def test_four_leftovers_from_a_siblings_document_are_recorded (self) -> None:
		"""None changes a number; all four would mislead somebody reading quickly."""
		account = " ".join(
			(pymidiinstrumentdefs.load("novation/circuit_rhythm", [CORPUS]).source or "").split())

		assert "Triggering Drums" in account
		assert "there is no Drum Control table in these six sheets" in account
		assert "which are the Circuit Tracks' eight tracks, not this machine's eight sample" \
			in account


class TestOBX8:

	"""Rank 70, and the first instrument here whose implementation is inside its user manual.

	**The headline is how much the document contradicts itself**, not the count: one page
	number printed twice, one control change printed twice, one NRPN name printed twice, six
	ranges that disagree between its own two tables, ten more that break a limit the same
	document states, and six mutually exclusive accounts of how many programs there are.
	Every one was found twice, by two readers working from different libraries.
	"""

	def test_the_whole_implementation_arrives (self) -> None:
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		assert len(ob_x8.controls) == 147
		assert len(ob_x8.groups) == 24
		assert set(ob_x8.parts) == {"lower", "upper"}

		# 121 control change rows and 135 NRPN addresses, merged into 163 parameters, of which
		# sixteen control changes are held back and two NRPN addresses are not published.
		by_cc = [c for c in ob_x8.controls.values() if c.cc is not None]
		by_nrpn = [c for c in ob_x8.controls.values() if c.nrpn is not None]

		assert len(by_cc) == 105
		assert len(by_nrpn) == 133

	def test_sixteen_control_changes_are_held_back_as_the_sibling_holds_them (self) -> None:
		"""Data entry, the NRPN transport and the channel mode messages - the TEO-5's list."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])
		numbers = {c.cc for c in ob_x8.controls.values() if c.cc is not None}

		for held in (6, 38, 96, 97, 98, 99, 100, 101, 120, 121, 122, 123, 124, 125, 126, 127):
			assert held not in numbers, f"control change {held} should not publish"

		# Bank Select does publish, as it does for `oberheim/teo_5`.
		assert 0 in numbers and 32 in numbers

		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])
		theirs = {c.cc for c in teo.controls.values() if c.cc is not None}

		assert 0 in theirs and 32 in theirs
		assert 6 not in theirs and 120 not in theirs

	def test_control_change_12_is_printed_twice_and_ships_twice (self) -> None:
		"""Two parameters at one number, which the file carries rather than correcting."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])
		at_12 = sorted(c.name for c in ob_x8.controls.values() if c.cc == 12)

		assert at_12 == ["osc_1_filter_env_mod", "osc_1_xmod"]

		# And the NRPN table gives them 9 and 12, which is the argument that the second row's
		# "12" is its NRPN number repeated into the control change column.
		assert ob_x8.controls["osc_1_xmod"].nrpn == 9
		assert ob_x8.controls["osc_1_filter_env_mod"].nrpn == 12

		account = " ".join((ob_x8.source or "").split())

		assert "CONTROL CHANGE 12 IS PRINTED TWICE" in account

	def test_two_nrpn_addresses_are_not_published_and_the_file_says_why (self) -> None:
		"""The maker prints one name on two addresses, so neither is attached to a control.

		This is the strongest refusal in the file. Pairing control change 78 with whichever of
		56 and 57 came first would be arbitrary, and publishing both would invent a parameter.
		"""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])
		addresses = {c.nrpn for c in ob_x8.controls.values() if c.nrpn is not None}

		assert 56 not in addresses
		assert 57 not in addresses

		# The two control changes they belong to publish, without an NRPN.
		for name in ("mod_box_lfo_2_dest_osc_1", "mod_box_lfo_2_dest_osc_2"):
			assert ob_x8.controls[name].nrpn is None, name

		assert ob_x8.controls["mod_box_lfo_2_dest_osc_1"].cc == 77
		assert ob_x8.controls["mod_box_lfo_2_dest_osc_2"].cc == 78

		account = " ".join((ob_x8.source or "").split())

		assert "TWO NRPN ADDRESSES ARE NOT PUBLISHED AT ALL" in account
		assert "correcting a maker's printed name is not this project's to do" in account

	def test_the_six_ranges_that_disagree_carry_both_figures (self) -> None:
		"""`nrpn_range` holds the NRPN table's where the two tables differ, and only there.

		Both readers found the same six out of 91 pairs. Three read as a mistyping of 0-127;
		two are genuinely two-sided and the prose supports a different table in each; one is
		only the maker's leading zero.
		"""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		differing = {c.name: (c.range, c.nrpn_range)
			for c in ob_x8.controls.values() if c.nrpn_range is not None}

		assert differing == {
			"page_2_lfo_1_mod_2_ramp_up": ((0, 127), (0, 27)),
			"mod_box_arp_speed": ((0, 127), (0, 27)),
			"page_2_chord_key_limit": ((0, 127), (0, 1207)),
			"mod_box_lfo2_bend_amount": ((0, 255), (0, 12)),
			"env_type": ((0, 1), (0, 2)),
		}

		# Filter Frequency is the sixth, and is not recorded as a disagreement because the two
		# figures are the same number: the control change table prints "00-175".
		assert ob_x8.controls["filter_frequency"].range == (0, 175)
		assert ob_x8.controls["filter_frequency"].nrpn_range is None

		account = " ".join((ob_x8.source or "").split())

		assert "SIX RANGES DISAGREE BETWEEN THE TWO TABLES" in account
		assert "from ¼ to 12 semitones" in account

	def test_ten_ranges_break_a_limit_the_same_document_states (self) -> None:
		"""Printed as printed, because no page says how a value that wide is scaled.

		The maker says a control change is limited to 128 values and then prints a wider range
		ten times in its own control change column. Writing 127 into `range` would put a number
		in the corpus that no document prints.
		"""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		wide = sorted((c.cc, c.range[1]) for c in ob_x8.controls.values()
			if c.cc is not None and c.range[1] > 127)

		assert wide == [(1, 255), (33, 175), (39, 255), (40, 255), (42, 255), (45, 255),
			(46, 255), (48, 255), (73, 255), (74, 175)]

		account = " ".join((ob_x8.source or "").split())

		assert "while CCs are limited to a range of 128" in account
		assert "would be this file's invention rather than the maker's statement" in account

	def test_the_program_count_is_not_recorded_because_six_accounts_disagree (self) -> None:
		"""Program change travels both ways, which every account agrees about, and that is all."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		assert ob_x8.midi.program_change is not None
		assert ob_x8.midi.program_change.receives is True
		assert ob_x8.midi.program_change.sends is True
		assert ob_x8.midi.program_change.presets is None

		account = " ".join((ob_x8.source or "").split())

		assert "SIX ACCOUNTS OF HOW MANY PROGRAMS THERE ARE AND NO TWO AGREE" in account
		assert "768 user-programmable presets" in account
		assert "the entire 640 program sound set" in account

	def test_the_split_puts_the_upper_one_channel_above_the_lower (self) -> None:
		"""Which is OS 2.0's headline, and the reason this instrument has parts at all."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		assert ob_x8.parts["lower"].channel_offset == 0
		assert ob_x8.parts["upper"].channel_offset == 1
		assert ob_x8.parts["lower"].polyphony == 4
		assert ob_x8.parts["upper"].polyphony == 4

		# The four is stated against the parts and not against the instrument, because the
		# validator refuses both and the parts do not share a pool.
		assert ob_x8.voice.polyphony is None
		assert ob_x8.voice.polyphony_shared is False

		said = prose_of("oberheim", "ob_x8")

		assert "The Upper MIDI channel is automatically assigned as Lower channel +1" in said
		assert "THIS FORMAT CANNOT SAY SO WHILE ALSO DESCRIBING THE SPLIT" in said

	def test_the_two_split_parameters_with_two_addresses_each (self) -> None:
		"""The maker prints both numbers in one ruled cell and marks the name (UPPER/LOWER).

		Which number is which is settled by the rows either side rather than by the document:
		SPLIT UPPER TRANSPOSE is 1125 and SPLIT LOWER TRANSPOSE is 1093, so the 112x run is
		the Upper's. The second reader reached the same ordering from a different library.
		"""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		assert ob_x8.controls["split_params_upper_level_upper"].nrpn == 1122
		assert ob_x8.controls["split_params_upper_level_lower"].nrpn == 1090
		assert ob_x8.controls["split_params_split_point_upper"].nrpn == 1123
		assert ob_x8.controls["split_params_split_point_lower"].nrpn == 1092

		for name, part in (("split_params_upper_level_upper", "upper"),
				("split_params_upper_level_lower", "lower"),
				("split_upper_transpose", "upper"), ("split_lower_transpose", "lower")):
			assert ob_x8.controls[name].part == part, name

		# The maker's own label is kept on both halves; the part is what tells them apart.
		assert ob_x8.controls["split_params_upper_level_upper"].label \
			== ob_x8.controls["split_params_upper_level_lower"].label

	def test_the_pages_are_file_pages_because_one_number_is_printed_twice (self) -> None:
		"""Sheet 121 ends Appendix E on 112 and sheet 122 begins the MIDI section on 112."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		assert ob_x8.sources["manual"].page_offset == 0
		assert ob_x8.sources["addendum"].page_offset == 0

		account = " ".join((ob_x8.source or "").split())

		assert "PAGES ARE CITED AS FILE PAGES, BECAUSE THE PRINTED NUMBERING IS BROKEN" in account
		assert "two different sheets both print 112" in account

	def test_the_guide_was_built_from_a_sequential_document_and_the_body_is_clean (self) -> None:
		"""Which explains the sibling: the TEO-5's map says in its own words it is the Pro 3's."""
		said = prose_of("oberheim", "ob_x8")

		assert "Pro 3 User's Guide" in said
		assert "Mark Wilcox/Sequential" in said
		assert "THIS DOCUMENT'S BODY IS CLEAN" in said

		# And the sibling, which is where the same lineage shows on the page rather than in
		# the metadata.
		assert "Pro 3" in prose_of("oberheim", "teo_5")

	def test_os_2_0_adds_five_parameters_with_no_published_address (self) -> None:
		"""So the control map is the guide's, and the absence is enumerated rather than assumed."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		assert ob_x8.model.firmware == "2.0"

		labels = {c.label for c in ob_x8.controls.values()}

		for absent in ("AFTERTOUCH TO VOL", "MIDI #74 TO OSC 2", "MIDI #74 TO FILTER",
				"LFO VOLUME DEST", "AFTERTOUCH AMOUNT"):
			assert absent not in labels, absent

		said = prose_of("oberheim", "ob_x8")

		assert "five Page 2 parameters with no published MIDI address at all" in said

	def test_the_labels_keep_the_makers_typos_and_the_field_names_do_not (self) -> None:
		"""A label is the maker's word for the parameter; a field name is this project's."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		assert ob_x8.controls["osc_2_freq"].label == "0SC 2 FREQ"
		assert ob_x8.controls["expresion_pedal"].label == "EXPRESION PEDAL"
		assert ob_x8.controls["page_2_panwidth"].label == "PAGE 2 PANWIDTH"
		assert ob_x8.controls["mod_box_lfo2_bend_amount"].label == "MOD BOX LFO2 BEND AMOUNT"

		# The maker prints in capitals throughout, so the labels do too - as `roland/tr_6s`
		# does, and unlike `oberheim/teo_5`, whose own document prints title case.
		assert all(c.label == c.label.upper() for c in ob_x8.controls.values())

		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		assert not all(c.label == c.label.upper() for c in teo.controls.values())

	def test_four_things_that_look_like_misprints_and_are_not (self) -> None:
		"""Each reconciled against the prose, so that nobody later "corrects" them."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		# Three non-bend modes plus 64 half-semitone bend steps is 67 values.
		assert ob_x8.controls["page_2_portamento_mode"].range == (0, 66)

		# "5-octave+minor third range (0-+63 semitones.)"
		assert ob_x8.controls["osc_1_freq"].range == (0, 63)

		# 88 printable characters, consistent across all twenty name positions.
		assert ob_x8.controls["program_name_char_0"].range == (0, 87)

		account = " ".join((ob_x8.source or "").split())

		assert "FOUR THINGS THAT LOOK LIKE MISPRINTS AND ARE NOT" in account
		assert "in 0.5 semitone increments" in account

	def test_it_is_not_the_teo_5 (self) -> None:
		"""Two Oberheims, one document family, and almost nothing shared on the wire."""
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])
		teo = pymidiinstrumentdefs.load("oberheim/teo_5", [CORPUS])

		assert ob_x8.model.name == "OB-X8"
		assert teo.model.name == "TEO-5"

		# The TEO-5's document prints every control change from 0 to 127; this one leaves
		# eight numbers unmentioned and prints one of them twice.
		theirs = {c.cc for c in teo.controls.values() if c.cc is not None}
		ours = {c.cc for c in ob_x8.controls.values() if c.cc is not None}

		assert len(ours) == 104
		assert ours != theirs

		# Both prefer NRPN, in the maker's own words, which is what makes it a house position.
		assert ob_x8.midi.nrpn == "preferred"
		assert teo.midi.nrpn == "preferred"


class TestM1:

	"""Rank 71, and the first definition here read entirely out of a document with no text in it.

	**Four controls**, because everything else about this 1988 workstation is reached by system
	exclusive. The chart lists ten control change numbers and six of them are how a registered
	parameter travels.
	"""

	def test_four_controls_and_six_numbers_held_back (self) -> None:
		"""Ten numbers in the chart's Control Change block, four of them parameters."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])

		assert len(m1.controls) == 4
		assert sorted(c.cc for c in m1.controls.values() if c.cc is not None) == [1, 2, 7, 64]

		# The maker's own names for them, out of the chart's Remarks column.
		assert [m1.controls[n].label for n in
			("pitch_mg", "vdf_modulation", "volume", "sustain")] \
			== ["Pitch MG", "VDF modulation", "Volume", "Sustain"]

		account = " ".join((m1.source or "").split())

		assert "TEN CONTROL CHANGE NUMBERS ARE LISTED AND FOUR ARE PARAMETERS" in account
		assert "Six of those ten are how a registered parameter" in account

	def test_the_eleventh_row_is_the_sequencer_and_not_a_control (self) -> None:
		"""`0-101` against "Sending and receiving Seq. Data only" would be 102 phantom controls."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])
		numbers = {c.cc for c in m1.controls.values()}

		# Nothing between 3 and 63 is a control, which is what that row would have made it.
		assert not any(n in numbers for n in range(3, 64) if n != 7)

		account = " ".join((m1.source or "").split())

		assert "AN ELEVENTH ROW IS NOT A CONTROL AT ALL" in account
		assert "Sending and receiving Seq. Data only" in account

	def test_everything_else_is_system_exclusive (self) -> None:
		"""Which is the finding, and the same state `behringer/model_d` is in by another road."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])

		assert m1.midi.sysex is True

		# The chart has no NRPN row; what it has is an RPN, so NRPN is a checked absence.
		assert m1.midi.nrpn is None

		account = " ".join((m1.source or "").split())

		assert "Parameter change by system exclusive is used to edit Programs" in account
		assert "THE CHART HAS NO NRPN ROW" in account.upper()

		# The other definition here whose remote surface is system exclusive.
		assert len(pymidiinstrumentdefs.load("behringer/model_d", [CORPUS]).controls) == 0

	def test_eight_timbres_each_with_its_own_receive_channel (self) -> None:
		"""And a global channel that is none of them, which is what the keyboard plays on."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])

		assert len(m1.parts) == 8
		assert list(m1.parts) == [f"timbre_{n}" for n in range(1, 9)]

		for part in m1.parts.values():
			assert part.channel == "assigned"
			assert part.receives == ("notes", "controls", "program_change")
			# The voices are shared, so no timbre carries a count of its own.
			assert part.polyphony is None

		assert m1.voice.polyphony == 16
		assert m1.voice.polyphony_shared is True

		said = prose_of("korg", "m1")

		assert "Dynamic Voice Allocation" in said
		assert "only the Timbres which are set to the same channel as the MIDI Global channel" \
			in said

	def test_sixteen_voices_or_eight_depending_on_the_program (self) -> None:
		"""Single mode and Double mode, which is what `voicing_modes` is for."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])

		assert m1.voice.voicing_modes == (8, 16)
		assert m1.voice.polyphony == 16

		said = prose_of("korg", "m1")

		assert "16 voice, 16 oscillator (Single mode)" in said
		assert "8 voice, 16 oscillator (Double mode)" in said

	def test_the_source_is_a_scan_and_the_file_says_what_that_costs (self) -> None:
		"""No gate can check a number here, so the file says so rather than appearing checked.

		This is the distinction the whole corpus turns on: a figure nobody could verify by
		machine is not the same as a figure nobody looked at, and only the file can say which.
		"""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])
		account = " ".join((m1.source or "").split())

		assert "EVERY NUMBER BELOW WAS READ BY EYE AND NO GATE CAN CHECK ONE OF THEM" in account
		assert "The manual is a pure scan" in account

		# The other two definitions whose numbers came off an image.
		assert "yamaha/dx7" in account
		assert "roland/juno_106" in account

		said = prose_of("korg", "m1")

		assert "**`file(1)` SAYS THIS DOCUMENT HAS 13 PAGES. IT HAS 138.**" in said

	def test_the_clock_and_transport_are_one_way_at_a_time (self) -> None:
		"""Both, where `both` records a pair of settings rather than a simultaneous capability."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])

		assert m1.midi.clock == "both"
		assert m1.midi.transport == "both"

		said = prose_of("korg", "m1")

		assert "When Clock is Internal, it transmits but does not receive" in said
		assert "only when this function is set to EXT" in said

	def test_four_global_switches_can_turn_any_of_it_off (self) -> None:
		"""A condition the format cannot carry, which the chart states four times over."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])
		account = " ".join((m1.source or "").split())

		assert "FOUR GLOBAL SWITCHES DECIDE WHETHER ANY OF IT ARRIVES" in account
		assert "When set to DIS, the selected MIDI data is not received or sent" in account
		assert "every field below is what the instrument does with its switches on" in account

	def test_the_preset_count_is_one_of_two_the_player_chooses (self) -> None:
		"""100 is recorded because the chart agrees with it; the other setting gives fifty."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])

		assert m1.midi.program_change is not None
		assert m1.midi.program_change.presets == 100

		account = " ".join((m1.source or "").split())

		assert "Memory allocation can be changed to 50 Programs and 50 Combinations" in account
		assert "a reader whose instrument is set the other way has fifty" in account

	def test_aftertouch_is_refused_polyphonically_rather_than_unstated (self) -> None:
		"""Keys x / x is a denial; it is the one row in this chart that refuses both ways."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])

		assert m1.voice.aftertouch == "channel"
		assert m1.voice.velocity is not None
		assert m1.voice.velocity.note_on == "received"
		assert m1.voice.velocity.note_off is False

		# No bend range is printed anywhere, so the field is absent rather than guessed.
		assert m1.voice.pitch_bend is None

		said = prose_of("korg", "m1")

		assert "After Touch Keys x / x" in said

	def test_the_drum_kits_have_no_factory_note_map (self) -> None:
		"""The player assigns each sound to a key, so there is nothing fixed to publish."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])

		assert m1.voice.voices == {}
		assert m1.voice.addressing == "pitches"

		account = " ".join((m1.source or "").split())

		assert "Key sets the key (C0 to G8) to which the sound is assigned" in account
		assert "soma/pulsar_23" in account

	def test_the_ten_numbers_are_split_between_two_global_switches (self) -> None:
		"""Which is the thing a definition of this instrument is most likely to get wrong.

		The four published are under the CONTROL filter and so is pitch bend; the six held
		back are under EXCLUSIVE, because on this instrument they are the machinery of
		parameter editing rather than performance control. The first reading of this manual
		had it as "all ten under CONTROL" and the second reading corrected it.
		"""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])
		account = " ".join((m1.source or "").split())

		assert "THEY DO NOT DIVIDE THE WAY A READER WOULD GUESS" in account
		assert "the ten control change numbers are split between two different switches" in account
		assert "names the wrong switch for six of them" in account

	def test_six_controller_numbers_exist_and_never_cross_the_cable (self) -> None:
		"""102 to 107 are the sequencer's own, and the manual says so forty pages away."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])
		numbers = {c.cc for c in m1.controls.values()}

		for inside_only in range(102, 108):
			assert inside_only not in numbers, f"{inside_only} does not leave the instrument"

		account = " ".join((m1.source or "").split())

		assert "MIDI does not input or output 102 to 107" in account
		assert "a number the instrument cannot hear" in account

	def test_the_one_rpn_reaches_one_parameter_and_is_received_only (self) -> None:
		"""RPN 0,1 - the specification's own Master Fine Tuning - and nothing else."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])
		account = " ".join((m1.source or "").split())

		assert "controllers 98 and 99 appear nowhere in the document" in account
		assert "That is RPN 0,1, which is the MIDI specification's own Master Fine Tuning" \
			in account
		assert "answers to it and never sends it" in account

	def test_the_document_disagrees_with_itself_about_the_aftertouch_switch (self) -> None:
		"""Chart says the AFTER TOUCH filter; the exclusive section says the CONTROL one."""
		m1 = pymidiinstrumentdefs.load("korg/m1", [CORPUS])
		account = " ".join((m1.source or "").split())

		assert "CONTRADICTS ITSELF ABOUT WHICH SWITCH GOVERNS AFTERTOUCH" in account
		assert "Both readers checked the letter at full resolution and it is a C" in account

		# The field still records the kind, which is not what the two statements disagree about.
		assert m1.voice.aftertouch == "channel"


class TestMachinedrum:

	"""Rank 72, and the definition that publishes what the maker prints rather than what it means.

	The appendix abbreviates fifteen of its sixteen per-track blocks. Expanding them would
	give 416 controls and would assert three things the page does not: the intermediate
	parameter names, the direction marks for the rows it elides, and that the eight-number
	gap at 64 to 71 is deliberate. **71 is what is printed with a number and a name.**
	"""

	def test_only_what_the_maker_prints_is_published (self) -> None:
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])

		assert len(machinedrum.controls) == 71
		assert len(machinedrum.parts) == 16
		assert len(machinedrum.groups) == 4

		# One track is printed in full and the other fifteen give a level, a mute and the
		# first of their twenty-four.
		per_part = collections.Counter(c.part for c in machinedrum.controls.values())

		assert per_part["track_1"] == 26
		assert all(per_part[f"track_{n}"] == 3 for n in range(2, 17))

		said = " ".join(prose_of("elektron", "machinedrum").split())

		assert "THIS FILE DOES NOT EXPAND IT" in said
		assert "the maker prints 71 of them with both a number and a name" in said

	def test_the_three_things_an_expansion_would_assert (self) -> None:
		"""Named one by one, because the expansion is nearly certain and still not printed."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])
		said = " ".join(prose_of("elektron", "machinedrum").split())

		assert "THE EXPANSION IS NEARLY CERTAIN AND IS STILL NOT WHAT THE PAGE SAYS" in said
		assert "the twenty-two intermediate names in every abbreviated block" in said
		assert "only the opening row is marked" in said
		assert "If that gap were instead a misprint, half the map would move" in said

		# And the rule is written down, so a consumer can apply it knowingly.
		assert "THE RULE, FOR ANYBODY WHO WANTS TO APPLY IT KNOWINGLY" in said

	def test_the_makers_own_count_agrees_with_neither (self) -> None:
		"""384 in the specifications, 416 by the appendix, and this file publishes 71."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])
		said = " ".join(prose_of("elektron", "machinedrum").split())

		assert "384 MIDI controllable (MIDI CC) parameters" in said
		assert "384 is not quoted as a figure anywhere in this file" in said

	def test_sixteen_tracks_over_four_channels (self) -> None:
		"""`channel_offset` holds which of the four, because the base itself is the player's."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])

		offsets = [machinedrum.parts[f"track_{n}"].channel_offset for n in range(1, 17)]

		assert offsets == [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]

		# And the base channel's own range is not recorded, because no page prints it.
		assert machinedrum.midi.channels is None

		account = " ".join((machinedrum.source or "").split())

		assert "The manual never prints the range the base channel can take" in account
		assert "this is the seventh manual that does not print one" in account

	def test_the_mutes_are_received_and_never_sent (self) -> None:
		"""The one direction in the appendix that is not both ways, and it is sixteen rows."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])

		receives_only = [c for c in machinedrum.controls.values() if c.direction == "receives"]

		assert len(receives_only) == 16
		assert all(c.label == "Mute (>0 mutes trk)" for c in receives_only)
		assert sorted(c.cc for c in receives_only if c.cc is not None) \
			== sorted([12, 13, 14, 15] * 4)

	def test_nrpn_is_refused_by_design_and_the_maker_says_why (self) -> None:
		"""Four channels exist so that NRPN need not, which is rarer than a silence."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])

		assert machinedrum.midi.nrpn == "none"

		said = " ".join(prose_of("elektron", "machinedrum").split())

		assert "The reason for using four channels is to allow for easy access of control " \
			"change messages to all parameters" in said
		assert "which are usually hard to make good use of from keyboards" in said

	def test_the_labels_are_only_true_of_a_track_holding_a_drum_machine (self) -> None:
		"""A MIDI machine on a track gives the same numbers different meanings, and two unknown."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])
		account = " ".join((machinedrum.source or "").split())

		assert "ONLY TRUE OF A TRACK HOLDING A DRUM MACHINE" in account
		assert "two of the eight are undetermined, and the manual does not say which" in account

		# And the master effects have no controllers at all, despite the appendix's claim.
		assert "THE STEREO MASTER EFFECTS HAVE NO CONTROL CHANGE NUMBERS" in account

	def test_the_note_map_is_a_default_and_carries_numbers_not_names (self) -> None:
		"""Three octave conventions in one manual, and the numbers agree in all three."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])

		assert machinedrum.voice.addressing == "voices"
		assert len(machinedrum.voice.voices) == 16
		assert machinedrum.voice.voices["bd"] == 36
		assert machinedrum.voice.voices["m4"] == 62

		account = " ".join((machinedrum.source or "").split())

		assert "THE MANUAL NAMES NOTES THREE INCOMPATIBLE WAYS AND NUMBERS THEM ONE WAY" in account
		assert "This mapping can be changed in the MIDI map editor" in account

	def test_one_definition_covers_five_machines (self) -> None:
		"""Two axes - sampling or not, MKI or MKII - and none of it reaches the appendix."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])
		said = prose_of("elektron", "machinedrum")

		assert "SPS-1; SPS-1UW; SPS-1 MKII; SPS-1UW MKII; SPS-1UW+ MKII" in said
		assert "OS compatible with all Machinedrum versions" in said

		account = " ".join((machinedrum.source or "").split())

		assert "None of them is a control change number" in account

	def test_the_same_manual_is_served_from_two_urls (self) -> None:
		"""Byte for byte, which is what settles that the two products share one document."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])

		assert set(machinedrum.sources) == {"manual", "support_page", "uw_support_page"}

		said = prose_of("elektron", "machinedrum")

		assert "THE SAME BYTES ARE SERVED FROM TWO URLS" in said
		assert "identical, byte for byte, uploaded thirteen minutes apart" in said

	def test_the_hyphen_fault_is_the_font_and_the_appendix_escapes_it (self) -> None:
		"""Which is why two quotations here are cut rather than adapted."""
		said = prose_of("elektron", "machinedrum")

		assert "nonxregistered" in said
		assert "PyMuPDF reads 3,764 of them and `pypdf` reads 2,816" in said
		assert "Appendix B and Appendix C are set in Courier New and are unaffected" in said

	def test_the_edition_is_the_manuals_own_and_not_the_download_pages_date (self) -> None:
		"""The page dates this very file four years after the file says it was made."""
		machinedrum = pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS])

		assert machinedrum.sources["manual"].edition == "rev M"
		assert machinedrum.sources["manual"].dated == "2012-01-03"
		assert machinedrum.model.firmware == "1.63"

		said = prose_of("elektron", "machinedrum")

		assert "THE DOWNLOAD PAGE DATES THIS OS TO 23 MAY 2016 AND THAT DATE IS NOT TO BE USED" \
			in said
		assert "A catalogue of unrelated files all dated 23 May is a site migration" in said


class TestVirusTI:

	"""Rank 73, and the definition whose finding is an absence the maker created.

	**Access publishes no control change map for this instrument.** The 2006 manual says the
	list of all parameters is on its website; that address now redirects to a site whose
	downloads page never uses the word. The 2013 reference deletes even that sentence.
	"""

	def test_four_controls_and_they_are_not_the_control_map (self) -> None:
		virus = pymidiinstrumentdefs.load("access/virus_ti", [CORPUS])

		assert len(virus.controls) == 4
		assert sorted(c.cc for c in virus.controls.values() if c.cc is not None) == [7, 10, 11, 64]

		said = " ".join(prose_of("access", "virus_ti").split())

		assert "THE MAKER PUBLISHES NO CONTROL CHANGE MAP FOR THIS INSTRUMENT" in said
		assert "THIS IS NOT THE INSTRUMENT'S CONTROL MAP" in said
		assert "Four is what is published, not what exists" in said

	def test_the_pointer_still_resolves_and_what_it_pointed_at_is_gone (self) -> None:
		"""The maker's sentence, the redirect, and the page it lands on, all three recorded."""
		said = " ".join(prose_of("access", "virus_ti").split())

		assert "Further information, including a list of all parameters, is available at " \
			"www.access-music.de" in said
		assert "302 to `http://virus.info/`" in said
		assert 'the words "parameter", "MIDI" and "SysEx" appear nowhere on it' in said

		# And the later document removed the sentence.
		assert "AND THE LATER DOCUMENT DELETED THE POINTER" in said

	def test_the_manual_promises_a_chart_it_does_not_contain (self) -> None:
		"""Which is the maker's own evidence that one was meant to exist."""
		said = " ".join(prose_of("access", "virus_ti").split())

		assert "Appendices: Legal matters, charts, diagrams, glossary" in said
		assert "There is no chart appendix and no diagram appendix" in said

	def test_the_absence_was_checked_eight_ways_before_being_written_down (self) -> None:
		"""Because "the maker publishes nothing" is the strongest claim a definition can make."""
		said = " ".join(prose_of("access", "virus_ti").split())

		assert "CHECKED EIGHT WAYS BEFORE BEING WRITTEN DOWN" in said
		assert "the second reader was asked to break it rather than confirm it" in said
		assert "43 tables of which every one is a value-and-meaning table" in said

	def test_the_traps_that_would_put_wrong_numbers_in_this_corpus (self) -> None:
		"""A designer's initials, a third party's controller, and the specification's own list."""
		said = " ".join(prose_of("access", "virus_ti").split())

		assert "one designer's initials are **CC**" in said
		assert "128 false controller rows from one bank alone" in said
		assert "a definition recording 70 as a cutoff would be describing somebody else's " \
			"instrument" in said

	def test_the_program_count_is_not_recorded_because_four_accounts_disagree (self) -> None:
		virus = pymidiinstrumentdefs.load("access/virus_ti", [CORPUS])

		assert virus.midi.program_change is not None
		assert virus.midi.program_change.receives is True
		assert virus.midi.program_change.presets is None

		said = " ".join(prose_of("access", "virus_ti").split())

		assert "THE PROGRAM COUNT IS STATED FOUR WAYS AND NO TWO AGREE" in said
		assert "bank select is undocumented in both documents" in said

	def test_polyphony_is_not_a_number_and_the_maker_says_why (self) -> None:
		"""An average, a maximum and a caveat in one sentence."""
		virus = pymidiinstrumentdefs.load("access/virus_ti", [CORPUS])

		assert virus.voice.polyphony is None

		said = " ".join(prose_of("access", "virus_ti").split())

		assert "quoted at about 80, with a maximum of more than 100" in said
		assert "is not a voice count" in said

	def test_sixteen_parts_each_with_a_channel_the_player_sets (self) -> None:
		"""And a second mode where the channel is fixed to the part number."""
		virus = pymidiinstrumentdefs.load("access/virus_ti", [CORPUS])

		assert len(virus.parts) == 16
		assert all(part.channel == "assigned" for part in virus.parts.values())

		said = " ".join(prose_of("access", "virus_ti").split())

		assert "the MIDI channel is always equal to the PART number" in said

	def test_what_is_absent_is_absent_for_stated_reasons (self) -> None:
		"""Transport, NRPN and a bend range, each with the search behind it."""
		virus = pymidiinstrumentdefs.load("access/virus_ti", [CORPUS])

		assert virus.midi.transport is None
		assert virus.midi.nrpn is None
		assert virus.voice.pitch_bend is not None
		assert virus.voice.pitch_bend.semitones is None
		assert virus.voice.pitch_bend.programmable is True

		said = " ".join(prose_of("access", "virus_ti").split())

		assert "No page of either document mentions MIDI start, stop, continue or song position" \
			in said
		assert "only allows for a resolution of 128 values per parameter" in said
		assert "there is no single number that is the bend range" in said

	def test_three_machines_and_one_midi_difference_between_them (self) -> None:
		"""The desktop has no Keyboard pages, so it chooses no transmit controller numbers."""
		said = " ".join(prose_of("access", "virus_ti").split())

		assert "ACCESS VIRUS TI DESKTOP" in said
		assert "The 'Keyboard' pages are only available in keyboard versions of the Virus" in said
		assert "a desktop has no local control setting and chooses no transmit controller " \
			"numbers" in said.replace("**", "")

	def test_neither_document_contains_the_other (self) -> None:
		"""The 2013 reference adds a later OS and drops whole categories of MIDI material."""
		virus = pymidiinstrumentdefs.load("access/virus_ti", [CORPUS])

		assert set(virus.sources) == {"manual", "reference", "manuals_page", "downloads_page"}
		assert virus.sources["manual"].edition == "Virus TI1 Series"
		assert virus.sources["reference"].edition == "Virus TI2 Series"

		said = " ".join(prose_of("access", "virus_ti").split())

		assert "THE TWO DOCUMENTS ARE NOT ONE SUPERSEDING THE OTHER" in said
		assert "Neither contains the other" in said

	def test_it_is_the_other_kind_of_empty_definition (self) -> None:
		"""`behringer/model_d` has no controls by design; this one has them and no document."""
		virus = pymidiinstrumentdefs.load("access/virus_ti", [CORPUS])
		model_d = pymidiinstrumentdefs.load("behringer/model_d", [CORPUS])

		assert len(model_d.controls) == 0
		assert len(virus.controls) == 4

		said = " ".join(prose_of("access", "virus_ti").split())

		assert "IT IS AN INSTRUMENT WHOSE MAP IS NOT" in said
		assert "A third-party map exists; it is not evidence and nothing from it is here" in said


class TestKRONOS:

	"""The first instrument here whose maker publishes an implementation and no chart.

	Which costs this corpus the chart's `Mode` row and gains it two separate lists of
	messages, one for each direction, read against each other instead.
	"""

	def test_every_control_travels_both_ways (self) -> None:
		"""Seventy-two of them, and not one needs a direction - which is unusual."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		assert len(kronos.controls) == 72
		assert all(control.direction == "both" for control in kronos.controls.values())

		said = prose_of("korg", "kronos")

		assert "Nothing this instrument sends is something it will not answer to." in said

		# The fourteen numbers that are in one table only are exactly the addressing
		# machinery and the channel mode messages, which is why none of them is here.
		carried = {control.cc for control in kronos.controls.values()}

		assert not carried & {0, 32, 6, 38, 96, 97, 100, 101}
		assert not carried & set(range(120, 128))

	def test_its_chart_is_in_the_appendices_of_another_document (self) -> None:
		"""And two of this definition's fields are rows nothing else here carries.

		The MIDI archive's four pages are prose tables with no Basic Channel, Mode or True
		Voice row, and the Parameter Guide reprints those same four pages. The chart is
		printed p. 296 of the Operation Guide, after the specifications.
		"""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		assert kronos.midi is not None
		assert kronos.voice is not None

		# **Both of these were written up as unrecorded before that page was found.**
		assert kronos.midi.mode == 3
		assert kronos.voice.note_range == (0, 127)

		said = prose_of("korg", "kronos")
		flat = " ".join(said.split())

		assert "printed p. 296 of the Operation Guide" in flat
		assert "Mode 3: OMNI OFF, POLY" in said
		assert "A claim that a maker published no chart has to be checked against every page" \
			" of every document, not against the documents about MIDI." in flat

		# And the mode still cannot be changed over MIDI, which the chart does not say and
		# the implementation does: the four mode messages arrive and drop the notes.
		assert "THE MODE CANNOT BE CHANGED OVER MIDI" in flat
		assert "as All Notes Off" in said

	def test_its_nrpn_absence_is_about_parameters_not_controllers (self) -> None:
		"""The chart carries 98 and 99; nothing in five documents says what they select."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		assert kronos.midi is not None
		assert kronos.midi.nrpn == "none"

		flat = " ".join(prose_of("korg", "kronos").split())

		# They are the only numbers the chart has that the implementation does not.
		assert "they are the only numbers the chart carries that the prose tables do not" in flat
		assert "THERE IS NOTHING FOR THEM TO SELECT" in flat

		# And the registered three are received, which is a different thing.
		assert "r = 0 : Pitch Bend Sensitivity ( Bend Range )" in flat
		assert kronos.voice is not None
		assert kronos.voice.pitch_bend is not None
		assert kronos.voice.pitch_bend.programmable is True

	def test_the_chart_leaves_eight_more_numbers_assignable (self) -> None:
		"""Which the implementation prints, so both are carried and the difference is said."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		carried = {control.cc for control in kronos.controls.values()}

		assert {17, 19, 20, 21, 85, 86, 87, 88} <= carried

		flat = " ".join(prose_of("korg", "kronos").split())

		assert "Realtime Knobs 5-8 VJS Assign" in flat
		assert "the implementation says where those eight sit and the chart says they go" \
			" anywhere" in flat

	def test_twenty_eight_of_its_numbers_are_off_on_a_new_instrument (self) -> None:
		"""The KARMA controls, the pads and the Vector Joystick - a loadable default.

		The sharpest case in this corpus of a maker printing controller numbers that are
		not in effect until somebody turns them on.
		"""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		settable = set(range(22, 32)) | set(range(102, 120)) | {14}

		assert settable <= {control.cc for control in kronos.controls.values()}
		assert len(settable) == 29

		said = prose_of("korg", "kronos")

		assert "As shipped from the factory, for simplicity, all KARMA and Pad" \
			" assignments are set to Off." in said
		assert "a set of recommended CC assignments which can be loaded in a single step" in said

		# And the two tables disagree about exactly one of them, which the guide settles.
		assert "CC 14 carries that" in said
		assert "the transmitted table" in said and "missing a mark" in said

	def test_its_polyphony_is_a_property_of_the_program (self) -> None:
		"""Nine engines, nine figures from 40 to 200, and a processor they share."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		assert kronos.voice is not None
		assert kronos.voice.polyphony is None

		# **But the pool being shared is recorded even though the pool has no size**, which
		# is a thing worth saying about sixteen parts.
		assert kronos.voice.polyphony_shared is True

		said = prose_of("korg", "kronos")

		assert "KRONOS dynamically allocates the voice processing power between the" \
			" engines as necessary." in said
		assert "the first instrument here whose polyphony is a property of the program" \
			" rather than of the model" in " ".join(said.split()).lower()

	def test_its_aftertouch_asymmetry_is_stated_in_words (self) -> None:
		"""The keyboard sends one kind; the instrument answers to both."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		assert kronos.voice is not None
		assert kronos.voice.aftertouch == "poly"

		said = prose_of("korg", "kronos")

		assert "keyboard transmits only channel after touch" in said
		assert "it can receive polyphonic after touch to control individual notes" in said

		# And one of the four keyboards generates none at all, which is about that model's
		# hardware rather than about what any of them answers to.
		assert "KRONOS2-88LS keyboard does not generate aftertouch" in said

	def test_its_sixteen_parts_are_one_set_under_two_names (self) -> None:
		"""Timbres in Combination mode, Tracks in Sequencer mode, sixteen either way."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		assert list(kronos.parts) == ["timbre"]

		timbre = kronos.parts["timbre"]

		assert timbre.count == 16
		assert timbre.channel == "assigned"
		assert timbre.receives == ("notes", "controls", "program_change")

		said = prose_of("korg", "kronos")

		assert "each of the 16 Timbres or Tracks in Combi and Sequence modes" in said
		assert "Combination Number of Timbres 16 Maximum" in said

	def test_one_map_covers_every_kronos_and_that_is_checked (self) -> None:
		"""Seven products, three generations, and a 2025 archive compared against this one."""
		said = prose_of("korg", "kronos")

		assert "KRONOS 61/73/88 KRONOS X 61/73/88 KRONOS 2 61/73/88/PLATINUM/LS/GOLD" in said
		assert "six of them offer the identical implementation archive" in said

		flat = " ".join(said.split())

		assert "the same 88 controller numbers with the same status bytes" in flat

		# And nothing moved across the firmware, which is checked as an absence rather
		# than inferred from a changelog that reads harmless.
		assert "do not appear in it once" in flat

	def test_three_of_its_numbers_reach_one_channel_only (self) -> None:
		"""Which this format cannot say, so the definition says it in prose instead."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		for key, number in (("all_insert_fx", 92), ("master_fx", 94), ("total_fx", 95)):
			assert kronos.controls[key].cc == number
			assert kronos.controls[key].group == "effects"
			# **They carry no part, because the part they belong to is the instrument.**
			assert kronos.controls[key].part is None

		said = prose_of("korg", "kronos")

		assert "g : Always Global Channel No. (0 - 15)" in said
		assert "there is no part for the instrument itself" in said

		# Their received cells are malformed, so no band was invented for them.
		assert all(not kronos.controls[key].values
			for key in ("all_insert_fx", "master_fx", "total_fx"))
		assert "inventing the threshold would put a number in this corpus that no page" \
			" carries" in " ".join(said.split())

	def test_it_records_three_faults_in_the_makers_own_tables (self) -> None:
		"""Crossed effect sends, a typo, and three cells that did not typeset."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		# The lower number is the second send and the higher is the first.
		assert kronos.controls["send_2_level"].cc == 91
		assert kronos.controls["send_1_level"].cc == 93

		# And the label spells the word the received table gets wrong.
		assert kronos.controls["filter_eg_intensity"].label == "Filter EG Intensity"

		said = prose_of("korg", "kronos")

		assert "The effect sends are crossed" in said
		assert "Filter EG Intencity" in said

	def test_its_implementation_arrives_as_an_archive (self) -> None:
		"""A first for this library, and the digest recorded is the document inside it."""
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		said = prose_of("korg", "kronos")

		assert "the first archive this library has had to open to reach a controller" \
			" number" in " ".join(said.split())

		# The archive's own digest is recorded in the source's comment, so the extracted
		# copy cannot quietly become a different file from the download.
		archive = kronos.sources["implementation"].url

		assert archive is not None and archive.endswith(".zip")


class TestNeutron:

	"""Two controllers, counted by the maker, with everything else system exclusive.

	And the first instrument here that **clamps** a note outside its stated range rather
	than ignoring it, which is why it records no range at all.
	"""

	def test_the_maker_counts_its_two_controllers (self) -> None:
		"""Which is what makes two the whole map rather than two somebody noticed."""
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		assert len(neutron.controls) == 2
		assert neutron.controls["modulation"].cc == 1
		assert neutron.controls["sustain"].cc == 64

		said = prose_of("behringer", "neutron")

		assert "There are 2 MIDI CC functions that the Neutron supports" in said

		# And no other controller number is written anywhere in the manual, which is the
		# second of the three kinds of evidence the account sets out.
		flat = " ".join(said.split())

		assert "No other controller number is written anywhere in 34 pages" in flat

	def test_its_modulation_control_is_fourteen_bit (self) -> None:
		"""The maker prints both halves, as hex, on one line."""
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		modulation = neutron.controls["modulation"]

		assert modulation.cc == 1
		assert modulation.lsb == 33
		assert modulation.is_14_bit is True

		said = prose_of("behringer", "neutron")

		assert "Modulation wheel or lever - MIDI CC 0x01 (MSB) & MIDI CC 0x21 (LSB)" in said

	def test_it_records_no_note_range_because_it_clamps (self) -> None:
		"""A note outside 24 to 96 plays the nearest end, where this field means silence."""
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		assert neutron.voice is not None
		assert neutron.voice.note_range is None

		# So every note is playable, which is what the maker describes.
		assert all(neutron.voice.plays_note(note) for note in (0, 23, 24, 96, 97, 127))

		said = prose_of("behringer", "neutron")

		assert "The supported MIDI note range is 24 (C1) to 96 (C7) inclusive." in said
		assert "MIDI notes 0-23 will trigger note 24 (C1) note." in said

		flat = " ".join(said.split())

		assert "The first instrument in this corpus that clamps." in flat

	def test_its_absences_are_checked_against_every_document (self) -> None:
		"""Which is the rule the KRONOS cost at rank 89, applied rather than restated."""
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		assert neutron.midi is not None
		assert neutron.midi.mode is None
		assert neutron.midi.program_change is None

		flat = " ".join(prose_of("behringer", "neutron").split())

		assert "Behringer publishes six documents for this instrument and all six were" \
			" fetched and read" in flat
		assert "112 sheets" in flat

		# And the product page is what makes six the whole of it.
		assert "cited for the count being six" in flat

	def test_it_distinguishes_an_absence_with_evidence_from_one_without (self) -> None:
		"""`nrpn: none` has a positive behind it; the transport has nothing, so it is empty."""
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		assert neutron.midi is not None
		assert neutron.midi.nrpn == "none"
		assert neutron.midi.transport is None

		flat = " ".join(prose_of("behringer", "neutron").split())

		assert "this is deliberately not `none`" in flat
		assert "An absence with nothing positive behind it is left empty." in flat

		# What stands behind `nrpn: none` is a complete alternative mechanism.
		assert "the system exclusive table **is** this instrument's parameter mechanism and" \
			" it is exhaustive" in flat

	def test_velocity_and_aftertouch_reach_a_socket (self) -> None:
		"""Neither has a fixed destination here, which is what a semi-modular can do."""
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		assert neutron.voice is not None
		assert neutron.voice.velocity is not None
		assert neutron.voice.velocity.note_on == "received"

		# **The aftertouch kind is unrecorded although aftertouch plainly arrives**, because
		# no page says which kind it is.
		assert neutron.voice.aftertouch is None

		flat = " ".join(prose_of("behringer", "neutron").split())

		assert "this instrument's answer to a velocity is a voltage on a socket" in flat
		assert "Channel is the likely reading for a monophonic instrument and a reading is" \
			" not a statement." in flat

	def test_it_is_monophonic_until_told_otherwise (self) -> None:
		"""Paraphonic is a system exclusive setting, and it handles two notes."""
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		assert neutron.voice is not None
		assert neutron.voice.polyphony == 1
		assert neutron.voice.paraphonic is True
		assert neutron.voice.voicing_modes == (1, 2)

		said = prose_of("behringer", "neutron")

		assert "Note that a Neutron in Paraphonic mode will handle 2 notes." in said

		# And its pitch bend depth is published, which is unusual enough to check.
		assert neutron.voice.pitch_bend is not None
		assert neutron.voice.pitch_bend.semitones == 2
		assert neutron.voice.pitch_bend.programmable is True


class TestRefaceCS:

	"""The third reface here, out of a Data List that covers all four of them.

	Four sections, four charts, and **no two of the charts are the same chart** - which is
	why this definition reads all four rather than trusting a sibling's reading.
	"""

	def test_it_reuses_the_documents_its_siblings_saved (self) -> None:
		"""One file, one digest, three definitions citing it."""
		cs = pymidiinstrumentdefs.load("yamaha/reface_cs", [CORPUS])
		dx = pymidiinstrumentdefs.load("yamaha/reface_dx", [CORPUS])
		cp = pymidiinstrumentdefs.load("yamaha/reface_cp", [CORPUS])

		# **The same three files at the same three digests**, saved once under the DX.
		for key in ("dl", "supplement", "reference"):
			assert cs.sources[key].sha256 == dx.sources[key].sha256
			assert cs.sources[key].sha256 == cp.sources[key].sha256

		flat = " ".join(prose_of("yamaha", "reface_cs").split())

		assert "ALL THREE DOCUMENTS WERE ALREADY IN THIS LIBRARY AND NONE WAS FETCHED AGAIN." \
			in flat

		# And the document's shape is what makes reading one model's part of it safe.
		assert "no sheet names two models" in flat

	def test_seventeen_of_its_controls_answer_only_while_a_setting_is_on (self) -> None:
		"""And four work whatever it is set to, which the chart gives cell by cell."""
		cs = pymidiinstrumentdefs.load("yamaha/reface_cs", [CORPUS])

		assert len(cs.controls) == 21

		always = {1, 7, 11, 64}
		carried = {control.cc for control in cs.controls.values()}

		assert always <= carried
		assert len(carried - always) == 17

		said = prose_of("yamaha", "reface_cs")

		assert "Transmitted and recognized Control Change Number and Value, when MIDI" \
			" control is on." in said
		assert "MIDI Control off, ON" in said

		# Two of the four are received and never sent, stated twice in two ways.
		assert [key for key, control in cs.controls.items()
			if control.direction == "receives"] == ["modulation", "volume"]

	def test_its_pedal_sends_one_of_two_things_and_never_both (self) -> None:
		"""One socket, one setting, and the factory value picks expression."""
		cs = pymidiinstrumentdefs.load("yamaha/reface_cs", [CORPUS])

		assert cs.controls["expression"].cc == 11
		assert cs.controls["sustain_switch"].cc == 64

		# Both travel both ways, because that is what the chart says of each.
		assert cs.controls["expression"].direction == "both"
		assert cs.controls["sustain_switch"].direction == "both"

		said = prose_of("yamaha", "reface_cs")

		assert "*3 Transmitted if Foot Volume / Sustain switch is Foot Volume." in said
		assert "*4 Transmitted if Foot Volume / Sustain switch is Sustain." in said
		assert "Factory default setting: Foot Volume" in said

		# **And it can transmit a half-damper value it cannot use**, which is the detail
		# worth keeping.
		assert "Half-damper playing has no effect on the sound of the reface CS." in said

	def test_it_does_clock_where_two_of_its_siblings_do_not (self) -> None:
		"""And the reason is a block in its system overview that they lack."""
		cs = pymidiinstrumentdefs.load("yamaha/reface_cs", [CORPUS])
		cp = pymidiinstrumentdefs.load("yamaha/reface_cp", [CORPUS])

		assert cs.midi is not None and cp.midi is not None
		assert (cs.midi.clock, cs.midi.transport) == ("both", "both")
		assert (cp.midi.clock, cp.midi.transport) == ("none", "none")

		said = prose_of("yamaha", "reface_cs")

		assert "Looper Play/Rec (LPR PLAY/REC)" in said
		assert "so it has an internal clock to switch back to" in \
			" ".join(said.split()).lower()

	def test_its_mode_is_unrecorded_for_the_familys_reason (self) -> None:
		"""The chart gives two different defaults, and this field holds one number."""
		cs = pymidiinstrumentdefs.load("yamaha/reface_cs", [CORPUS])

		assert cs.midi is not None
		assert cs.midi.mode is None

		flat = " ".join(prose_of("yamaha", "reface_cs").split())

		assert "two different defaults" in flat

		# And the row under it is where the family divides, which is the kind of thing
		# somebody carries across by mistake.
		assert '*2 "m" is always treated as "1" regardless of its actual value.' in flat
		assert "Four charts in one document, and no two of them are the same chart." in flat

	def test_it_does_no_program_change_where_the_dx_does (self) -> None:
		"""The warning its sibling left, which applies equally here."""
		cs = pymidiinstrumentdefs.load("yamaha/reface_cs", [CORPUS])
		dx = pymidiinstrumentdefs.load("yamaha/reface_dx", [CORPUS])

		assert cs.midi is not None and cs.midi.program_change is not None
		assert cs.midi.program_change.receives is False
		assert cs.midi.program_change.sends is False

		# The DX is the one of the four that does.
		assert dx.midi is not None and dx.midi.program_change is not None
		assert dx.midi.program_change.receives is True

	def test_its_pitch_bend_is_settable_where_the_cps_is_not (self) -> None:
		"""The same system address, reserved on one instrument and used on the other."""
		cs = pymidiinstrumentdefs.load("yamaha/reface_cs", [CORPUS])
		cp = pymidiinstrumentdefs.load("yamaha/reface_cp", [CORPUS])

		assert cs.voice is not None and cs.voice.pitch_bend is not None
		assert cs.voice.pitch_bend.programmable is True
		assert cs.voice.pitch_bend.semitones == 12

		assert cp.voice is not None and cp.voice.pitch_bend is not None
		assert cp.voice.pitch_bend.programmable is False

		said = prose_of("yamaha", "reface_cs")

		assert "Pitch Bend Range -24 - +24 (semitones)" in said
		assert "Factory default setting: 12 semitones (one octave)" in said

	def test_it_records_neither_polyphony_nor_voicing_modes (self) -> None:
		"""Because one of the pair is known and that is not enough to list them."""
		cs = pymidiinstrumentdefs.load("yamaha/reface_cs", [CORPUS])

		assert cs.voice is not None
		assert cs.voice.polyphony is None
		assert cs.voice.voicing_modes == ()

		said = prose_of("yamaha", "reface_cs")

		# The portamento control is what shows it has both modes.
		assert cs.controls["portamento"].values == {"poly": 0, "mono": 1}
		assert "Mono with Portamento Time 1 - 127" in said

		flat = " ".join(said.split())

		assert "no document in the family states n" in flat


class TestMS20Mini:

	"""No controls, and the strongest form of that claim this corpus has.

	The maker has written down what the socket accepts, and a control change is not among
	it - which is a different thing from a chart's crossed box and from an unread page.
	"""

	def test_one_sentence_settles_three_of_its_fields (self) -> None:
		"""What arrives, that velocity does nothing, and that the channel is fixed."""
		mini = pymidiinstrumentdefs.load("korg/ms_20_mini", [CORPUS])

		assert len(mini.controls) == 0
		assert mini.midi is not None
		assert mini.midi.control_change == "none"
		assert mini.midi.channels == (1, 1)

		assert mini.voice is not None and mini.voice.velocity is not None
		assert mini.voice.velocity.note_on == "ignored"

		said = prose_of("korg", "ms_20_mini")

		assert "The only MIDI messages that can be received at the MIDI IN connector are note" \
			" messages (Velocity is disabled) on MIDI channel 1 (fixed)." in said

		# Which is the strongest form of this field: not a crossed box, not an unread page.
		assert "THE STRONGEST FORM OF THAT FIELD THIS CORPUS HAS" in said

	def test_its_channel_is_fixed_and_three_documents_say_so (self) -> None:
		"""A span of one, which a consumer offering a channel chooser should know."""
		mini = pymidiinstrumentdefs.load("korg/ms_20_mini", [CORPUS])

		assert mini.midi is not None
		assert mini.midi.channels == (1, 1)

		said = prose_of("korg", "ms_20_mini")

		# The sentence, the chart's crossed Changed row, and the hard-coded status bytes.
		assert "(fixed)" in said
		assert "crosses its Changed row" in said
		assert "`80`, `90` and `B0` rather than `8n`, `9n` and `Bn`" in said

	def test_its_keyboard_sends_one_velocity_for_every_note (self) -> None:
		"""Crossed in both velocity rows, with the constant printed beside the cross."""
		mini = pymidiinstrumentdefs.load("korg/ms_20_mini", [CORPUS])

		assert mini.voice is not None and mini.voice.velocity is not None
		assert mini.voice.velocity.note_on == "ignored"
		assert mini.voice.velocity.note_off is False

		flat = " ".join(prose_of("korg", "ms_20_mini").split())

		assert "`9n, v=64` and `8n, v=64`" in flat
		assert "this keyboard sends the same velocity for every note it has ever played" in flat

	def test_its_note_range_is_right_where_the_neutrons_had_to_be_empty (self) -> None:
		"""Because an out-of-range note here sounds nothing, and on the NEUTRON it sounds."""
		mini = pymidiinstrumentdefs.load("korg/ms_20_mini", [CORPUS])
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		assert mini.voice is not None and neutron.voice is not None

		# **The same field, two instruments, and the difference is what happens outside.**
		assert mini.voice.note_range == (12, 91)
		assert neutron.voice.note_range is None

		assert [mini.voice.plays_note(note) for note in (11, 12, 91, 92)] \
			== [False, True, True, False]

		said = prose_of("korg", "ms_20_mini")

		assert "If a Note On message with a note number of 92 or more is received, the message" \
			" will become invalid, and the sound being produced will stop." in said

		flat = " ".join(said.split())

		assert "The field turns on whether an out-of-range note sounds something, not on" \
			" whether the maker printed a range." in flat

	def test_its_chart_is_in_the_owners_manual_not_the_implementation (self) -> None:
		"""The second time in four instruments that the chart has moved."""
		mini = pymidiinstrumentdefs.load("korg/ms_20_mini", [CORPUS])

		assert mini.midi is not None
		assert mini.midi.mode == 3

		flat = " ".join(prose_of("korg", "ms_20_mini").split())

		assert "THE CHART IS NOT IN THE DOCUMENT CALLED AN IMPLEMENTATION" in flat
		assert "the second time in four instruments that the chart has been somewhere other" \
			" than the document named for it" in flat

	def test_three_of_its_five_documents_are_a_1978_instruments (self) -> None:
		"""And Korg's own list of differences is what says they cannot carry MIDI."""
		flat = " ".join(prose_of("korg", "ms_20_mini").split())

		assert "Equipped with MIDI IN connector and USB port" in flat
		assert "so **the original has neither**" in flat

		# **And the limit on the search is stated rather than hidden.**
		assert "two of the three are scans with no text layer at all" in flat
		assert "for those two a text search proves nothing" in flat

	def test_it_cannot_be_configured_over_midi_in_any_way (self) -> None:
		"""No sysex, no program change, no clock, no transport, and nothing to configure."""
		mini = pymidiinstrumentdefs.load("korg/ms_20_mini", [CORPUS])

		assert mini.midi is not None
		assert mini.midi.sysex is False
		assert mini.midi.clock == "none"
		assert mini.midi.transport == "none"
		assert mini.midi.nrpn == "none"
		assert mini.midi.program_change is not None
		assert mini.midi.program_change.receives is False
		assert mini.midi.program_change.sends is False

		assert mini.voice is not None
		assert mini.voice.aftertouch == "none"
		assert mini.voice.pitch_bend is None

		flat = " ".join(prose_of("korg", "ms_20_mini").split())

		assert "no memory, no firmware, and a channel that cannot be changed" in flat


class TestDrumlogue:

	"""Two complete implementation charts for two modes, on facing pages.

	**And 65 of the 67 controller numbers they share mean different things**, so the two
	cannot be merged and the factory default is the one carried.
	"""

	def test_it_carries_the_first_of_two_whole_charts (self) -> None:
		"""Which its maker calls the factory default, in those words."""
		drumlogue = pymidiinstrumentdefs.load("korg/drumlogue", [CORPUS])

		assert len(drumlogue.controls) == 66
		assert len(drumlogue.groups) == 14

		said = prose_of("korg", "drumlogue")

		assert "This is the factory default implementation." in said
		assert "This is an alternate implementation selectable via MIDI Global settings." in said

		flat = " ".join(said.split())

		# **Counted rather than described**, which is the point of reading both.
		assert "share **67** controller numbers, **65** of those name a different parameter" \
			" in each" in flat
		assert "the alternate gives **46** of its numbers more than one meaning" in flat

		# And the reason they cannot be merged is that 46 would need two meanings at once.
		assert "the alternate cannot be merged" in flat

	def test_its_chart_is_in_the_manual_as_the_pattern_now_predicts (self) -> None:
		"""The third Korg in four ranks whose chart is not where its name would put it."""
		flat = " ".join(prose_of("korg", "drumlogue").split())

		assert "THERE IS NO SEPARATE MIDI IMPLEMENTATION, AND THAT IS NOW THE EXPECTED CASE" \
			" FOR THIS MAKER." in flat
		assert "the third Korg in four ranks whose chart is not where its name would put it" \
			in flat

		# Which the two it follows are named in, so the pattern is traceable.
		assert "`korg/kronos`" in flat and "`korg/ms_20_mini`" in flat

	def test_every_one_of_its_controls_is_gated_by_a_global_switch (self) -> None:
		"""In each direction separately, and the format has no field for it."""
		drumlogue = pymidiinstrumentdefs.load("korg/drumlogue", [CORPUS])

		said = prose_of("korg", "drumlogue")

		assert "When the GLOBAL setting MIDI RX CC is ON, the drumlogue will receive signals;" \
			" and when the GLOBAL setting MIDI TX CC is ON, the drumlogue will transmit" \
			" signals." in said

		flat = " ".join(said.split())

		assert "The format has no field for a condition on a whole map" in flat
		assert "will find all 66 of them silent" in flat

	def test_its_notes_name_drums_and_carry_no_pitch (self) -> None:
		"""Eleven voices over a span of twenty, nine of which do nothing."""
		drumlogue = pymidiinstrumentdefs.load("korg/drumlogue", [CORPUS])

		assert drumlogue.voice is not None
		assert drumlogue.voice.addressing == "voices"
		assert drumlogue.voice.note_range == (36, 55)
		assert len(drumlogue.voice.voices) == 11
		assert drumlogue.voice.voices["bd"] == 36
		assert drumlogue.voice.voices["multi"] == 55

		said = prose_of("korg", "drumlogue")

		assert "Pitch is unaffected by the note number." in said

		# **The span is twenty and only eleven of it sounds.**
		assert sorted(drumlogue.voice.voices.values()) == [36, 37, 39, 40, 42, 45, 46, 50,
			52, 53, 55]

	def test_its_master_volume_is_its_one_fourteen_bit_control (self) -> None:
		"""And it is why the control count differs from the chart's assignment count."""
		drumlogue = pymidiinstrumentdefs.load("korg/drumlogue", [CORPUS])

		volume = drumlogue.controls["master_volume"]

		assert volume.cc == 7
		assert volume.lsb == 39
		assert volume.is_14_bit is True

		assert [key for key, control in drumlogue.controls.items() if control.is_14_bit] \
			== ["master_volume"]

	def test_it_receives_a_velocity_and_sends_a_constant (self) -> None:
		"""Because it has buttons rather than pads, so there is nothing to strike harder."""
		drumlogue = pymidiinstrumentdefs.load("korg/drumlogue", [CORPUS])

		assert drumlogue.voice is not None and drumlogue.voice.velocity is not None
		assert drumlogue.voice.velocity.note_on == "received"
		assert drumlogue.voice.velocity.note_off is False

		flat = " ".join(prose_of("korg", "drumlogue").split())

		assert "RECEIVED AS A REAL FIGURE AND SENT AS A CONSTANT." in flat
		assert "there being no pads on this instrument to strike" in flat

	def test_its_firmware_changed_nothing_in_the_map (self) -> None:
		"""Five new features in 1.1.0 and all of them panel operations."""
		drumlogue = pymidiinstrumentdefs.load("korg/drumlogue", [CORPUS])

		assert "release_note" in drumlogue.sources
		assert drumlogue.sources["release_note"].edition == "1.1.0"

		flat = " ".join(prose_of("korg", "drumlogue").split())

		assert "all panel operations" in flat
		assert "the word `MIDI` appears in it only inside a link to the downloads page" in flat

	def test_its_program_change_count_is_stated_rather_than_implied (self) -> None:
		"""The chart's True Number row is the row for exactly that."""
		drumlogue = pymidiinstrumentdefs.load("korg/drumlogue", [CORPUS])

		assert drumlogue.midi is not None and drumlogue.midi.program_change is not None
		assert drumlogue.midi.program_change.presets == 128
		assert drumlogue.midi.program_change.receives is True
		assert drumlogue.midi.program_change.sends is True

		flat = " ".join(prose_of("korg", "drumlogue").split())

		assert "the True Number row is the row for exactly this and it reads 0-127" in flat


class TestJDXi:

	"""Four parts on four fixed channels, and the first Roland here with real NRPNs.

	The same controller means different things on different channels, which is what the
	``part`` field is for and what this instrument needs more than most.
	"""

	def test_its_four_parts_sit_on_fixed_channels (self) -> None:
		"""Stated by the owner's manual and settable nowhere in 97 sheets."""
		jd_xi = pymidiinstrumentdefs.load("roland/jd_xi", [CORPUS])

		assert list(jd_xi.parts) == ["digital_synth", "analog_synth", "drum"]
		assert jd_xi.parts["digital_synth"].count == 2
		assert jd_xi.parts["digital_synth"].channel_offset == 0
		assert jd_xi.parts["analog_synth"].channel_offset == 2
		assert jd_xi.parts["drum"].channel_offset == 9

		said = prose_of("roland", "jd_xi")

		assert "The MIDI transmit/receive channels are channel 1 for the Digital Synth 1 part," \
			" channel 2 for the Digital Synth 2 part, channel 10 for the Drum part, and" \
			" channel 3 for the Analog Synth part." in said

		# **And the format cannot say they are absolute rather than derived**, which the
		# definition records rather than glossing.
		flat = " ".join(said.split())

		assert "the first half is a fiction, there being no base to derive from because the" \
			" base never moves" in flat

	def test_the_same_controller_means_two_things_on_two_channels (self) -> None:
		"""Which is what the part field is for, and eight Elektrons here already do."""
		jd_xi = pymidiinstrumentdefs.load("roland/jd_xi", [CORPUS])

		assert jd_xi.controls["partial_1_cutoff"].cc == 102
		assert jd_xi.controls["partial_1_cutoff"].part == "digital_synth"
		assert jd_xi.controls["analog_cutoff"].cc == 102
		assert jd_xi.controls["analog_cutoff"].part == "analog_synth"

		flat = " ".join(prose_of("roland", "jd_xi").split())

		assert "Controller 102 is the first partial's cutoff on channels 1 and 2, the whole" \
			" analog tone's cutoff on channel 3, and nothing at all on channel 10." in flat

	def test_it_is_the_first_roland_here_with_real_nrpns (self) -> None:
		"""Twenty-one of its 57 controls are addressed that way."""
		jd_xi = pymidiinstrumentdefs.load("roland/jd_xi", [CORPUS])
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert jd_xi.midi is not None and fantom.midi is not None
		assert jd_xi.midi.nrpn == "supported"
		assert fantom.midi.nrpn == "none"

		by_nrpn = [key for key, control in jd_xi.controls.items() if control.nrpn is not None]

		assert len(by_nrpn) == 21
		assert len(jd_xi.controls) == 57

		# Every one has a most significant byte of nought, so the address is the printed LSB.
		addresses = [jd_xi.controls[key].nrpn for key in by_nrpn]

		assert all(address is not None and address < 128 for address in addresses)

	def test_its_drum_parameters_are_a_rule_and_are_not_carried (self) -> None:
		"""148 addresses stated as four rules, which is rank 86's lesson applied."""
		jd_xi = pymidiinstrumentdefs.load("roland/jd_xi", [CORPUS])

		assert jd_xi.parts["drum"].addressing == "voices"

		# **Nothing carries the drum part**, because what it would carry is arithmetic.
		assert not [key for key, control in jd_xi.controls.items() if control.part == "drum"]

		said = prose_of("roland", "jd_xi")

		assert "Cutoff | 36 - 72 | NRPN MSB:89, LSB:Note" in said

		flat = " ".join(said.split())

		assert "148 addresses stated as four rules" in flat
		assert "`elektron/tonverk`'s lesson at rank 86" in flat

	def test_it_says_which_of_its_numbers_rest_on_arithmetic (self) -> None:
		"""Nine of 57, which the citation checker reports and the definition repeats."""
		flat = " ".join(prose_of("roland", "jd_xi").split())

		assert "AND NINE OF THE FIFTY-SEVEN NUMBERS ARE NOT PRINTED AS NUMBERS ANYWHERE." in flat
		assert "48 of the 57 are found as numbers and nine are found inside a span" in flat

		# And it distinguishes that from generating numbers, which is the line it did not cross.
		assert "That is reading a table rather than generating numbers" in flat

	def test_the_list_the_chart_points_at_is_where_it_says (self) -> None:
		"""And a first reading of that page's opening concluded otherwise."""
		flat = " ".join(prose_of("roland", "jd_xi").split())

		assert "Refer to Control Change Message List (p. 14) about function of each controller" \
			" number." in flat
		assert "6,138 characters into a page that opens with the tail of a system exclusive" \
			" address map" in flat

		# **The lesson, stated so the next reader does not repeat it.**
		assert "A page is not a page's first screen." in flat

	def test_its_two_charts_are_two_sections_not_two_maps (self) -> None:
		"""Unlike the drumlogue's, which were the same instrument twice over."""
		jd_xi = pymidiinstrumentdefs.load("roland/jd_xi", [CORPUS])

		assert jd_xi.midi is not None
		assert jd_xi.midi.clock == "both"
		assert jd_xi.midi.transport == "both"

		flat = " ".join(prose_of("roland", "jd_xi").split())

		assert "`roland/fantom_6_7_8`'s arrangement and not `korg/drumlogue`'s" in flat

		# And the clock is both because the two charts divide it between them.
		assert "The JD-Xi can transmit and receive MIDI clock (F8) messages to synchronize its" \
			" tempo." in prose_of("roland", "jd_xi")

	def test_its_chart_misspells_three_of_its_own_names (self) -> None:
		"""And the labels take the spelling the reception section uses."""
		jd_xi = pymidiinstrumentdefs.load("roland/jd_xi", [CORPUS])

		for key, label in (("vibrato_rate", "Vibrato Rate"),
				("vibrato_depth", "Vibrato Depth"), ("vibrato_delay", "Vibrato Delay")):
			assert jd_xi.controls[key].label == label

		flat = " ".join(prose_of("roland", "jd_xi").split())

		assert "`Vibrate rate`, `Vibrate depth` and `Vibrate delay`" in flat

	def test_its_parameter_guide_carries_no_number_and_was_checked (self) -> None:
		"""Because on this maker's other instruments a Parameter Guide is where they are."""
		jd_xi = pymidiinstrumentdefs.load("roland/jd_xi", [CORPUS])

		assert "parameter_guide" in jd_xi.sources

		flat = " ".join(prose_of("roland", "jd_xi").split())

		assert "CITED FOR AN ABSENCE AND QUOTED FOR NOTHING, AND ITS NAME IS WHY IT WAS" \
			" CHECKED." in flat
		assert "51 sheets, 31,811 words, and **not one controller number**" in flat


class TestHexdrums:

	"""No controllers, and the one maker here that says it chose not to have any.

	Every other ``control_change: none`` in this corpus is an absence somebody
	established.  This one is a decision somebody explains, which is a stronger claim
	and the reason this definition is worth having at all.
	"""

	def test_its_maker_says_why_there_are_no_controllers (self) -> None:
		"""Which no other definition in this corpus can say."""
		hexdrums = pymidiinstrumentdefs.load("erica_synths/hexdrums", [CORPUS])

		assert not hexdrums.controls
		assert hexdrums.midi.control_change == "none"
		assert not hexdrums.midi.stated_none

		said = prose_of("erica_synths", "hexdrums")

		assert "There is no MIDI CC implementation for parameter control, however, since the" \
			" parameters aren't digitally mapped. This is intentional to allow for a more" \
			" traditional drum machine workflow." in said

		# **THE DISTINCTION THE DEFINITION DRAWS IS THE POINT OF IT**, so it is asserted
		# rather than left to a reader to notice that this `none` is unlike the other seven.
		flat = " ".join(said.split())

		assert "Eight definitions in this corpus carry that field and in the other seven it" \
			" records **an absence somebody established**" in flat
		assert "This one records **a decision somebody explains**" in flat

	def test_ten_voices_over_ten_consecutive_notes (self) -> None:
		"""So every note in its range sounds something, which drum machines rarely manage."""
		hexdrums = pymidiinstrumentdefs.load("erica_synths/hexdrums", [CORPUS])

		assert hexdrums.voice is not None
		assert hexdrums.voice.addressing == "voices"
		assert hexdrums.voice.note_range == (36, 45)

		assert hexdrums.voice.voices == {"bd1": 36, "bd2": 37, "machine": 38, "snare": 39,
			"clap": 40, "rimshot": 41, "oh": 42, "ch": 43, "crash": 44, "ride": 45}

		# Ten voices over ten numbers, with nothing in between - which is the claim, so it
		# is checked rather than read off the dictionary above.
		notes = sorted(hexdrums.voice.voices.values())

		assert notes == list(range(36, 46))
		assert len(set(notes)) == len(notes)

		for note in notes:
			assert hexdrums.voice.plays_note(note)

		assert not hexdrums.voice.plays_note(35)
		assert not hexdrums.voice.plays_note(46)

	def test_its_manual_asks_for_a_chart_it_does_not_contain (self) -> None:
		"""And the definition says so rather than recording a mode it never found."""
		hexdrums = pymidiinstrumentdefs.load("erica_synths/hexdrums", [CORPUS])

		assert hexdrums.midi.mode is None

		said = prose_of("erica_synths", "hexdrums")

		assert "The DIN5 MIDI in receives trigger note messages and MIDI clock. Please refer" \
			" to the MIDI implementation chart in the manual." in said

		flat = " ".join(said.split())

		assert "**THE MANUAL ASKS FOR A CHART IT DOES NOT CONTAIN.**" in flat
		assert "and there is no chart: no Basic Channel row, no True Voice row, no `o` and" \
			" `x`." in flat

	def test_the_japanese_edition_has_none_of_it_and_the_reason_is_marked_an_inference (self) \
			-> None:
		"""The obvious reading is that a maker dropped a section, and the dates say otherwise."""
		flat = " ".join(prose_of("erica_synths", "hexdrums").split())

		assert "**AND THE JAPANESE EDITION HAS NONE OF IT, BECAUSE IT IS FOUR WEEKS OLDER.**" \
			in flat
		assert "`MIDI IMPLEMENTATION` is on none of the Japanese edition's pages and not one" \
			" of the numbers 36 to 45 is anywhere in it" in flat

		# **THE HEADING IS WHAT DECIDES IT**, so it is asserted rather than left in a list of
		# evidence: a dropped section leaves its heading behind.
		assert "**its sheet 27 is headed for the sample upload alone**" in flat
		assert "A translator who drops a section leaves the heading behind; a translator" \
			" working from a manual that has no such section has no heading to translate." \
			in flat

		# **AND THE DEFINITION DOES NOT STATE THE INFERENCE AS A FACT**, which is the whole
		# discipline here - this is the second instrument in two ranks where one more reading
		# stopped the corpus accusing a maker of something.
		assert "**Neither document says so, so that is an inference and is marked as one**" \
			in flat
		assert "the earlier English edition it would have been made from is not published, so" \
			" nobody can settle it" in flat

		# What is *not* an inference, and is the part a reader of that edition is owed.
		assert "**WHAT A JAPANESE READER FINDS IS NOTHING EITHER WAY, AND THAT PART IS NOT AN" \
			" INFERENCE.**" in flat

		# **CITED FOR AN ABSENCE AND DELIBERATELY NOT KEPT**, which a reader needs told,
		# because every other document this corpus rests on is in the library.
		assert "28.8 MB for a remark about what a translation does not contain is not worth" \
			" the library's weight" in flat

	def test_what_it_leaves_empty_and_why_that_is_not_the_same_as_none (self) -> None:
		"""The word for velocity appears nowhere in 28 sheets, so the field says nothing."""
		hexdrums = pymidiinstrumentdefs.load("erica_synths/hexdrums", [CORPUS])

		assert hexdrums.voice is not None
		assert hexdrums.voice.velocity is None
		assert hexdrums.voice.polyphony is None
		assert hexdrums.midi.program_change is None
		assert hexdrums.midi.sysex is None
		assert hexdrums.midi.transport is None

		# And the one thing it does settle in both directions, each by its own setting.
		assert hexdrums.midi.clock == "both"
		assert hexdrums.midi.channels == (1, 16)

		flat = " ".join(prose_of("erica_synths", "hexdrums").split())

		assert "**not declared absent**, so the fields are empty rather than `none`" in flat

	def test_its_documents_are_addressed_by_a_file_id_rather_than_a_name (self) -> None:
		"""So the address says nothing about what comes back, which is worth recording."""
		hexdrums = pymidiinstrumentdefs.load("erica_synths/hexdrums", [CORPUS])

		manual = hexdrums.sources["manual"].url or ""

		assert "/service/file/download/product_id/1009/file_id/608/" in manual
		assert not manual.endswith(".pdf")

		flat = " ".join(prose_of("erica_synths", "hexdrums").split())

		assert "**the file name arrives only in a `content-disposition` header**" in flat
		assert "the firmware and the manual are told apart only by what comes back" in flat


class TestJupiterX:

	"""The Roland whose implementation holds none of its tone parameters.

	Eight Rolands had established that a document named an implementation is where
	this maker's numbers are.  This one divides the work the other way round, and
	the same number means different things depending on which model a part holds -
	a setting rather than a channel, which no field in this format can say.
	"""

	def test_its_implementation_holds_only_the_performance_controls (self) -> None:
		"""22 of the 35 numbers it names, the rest being machinery or channel mode."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])

		assert len(jupiter.controls) == 22
		assert len(jupiter.groups) == 4

		# Every one answers to a controller number, so the list below is the whole map.
		assert all(control.cc is not None for control in jupiter.controls.values())

		assert sorted(control.cc for control in jupiter.controls.values()
				if control.cc is not None) == [
			1, 4, 5, 7, 10, 11, 64, 65, 66, 67, 68, 71, 72, 73, 74, 75, 76, 77, 78, 84, 91, 93]

		# **THE FANTOM RULING, STILL HOLDING NINE RANKS ON.** None of the addressing machinery
		# the implementation also names is here, and nor is a channel mode message.
		numbers = {control.cc for control in jupiter.controls.values()}

		assert not numbers & {0, 32, 6, 38, 98, 99, 100, 101}
		assert not numbers & set(range(120, 128))

	def test_the_tone_map_is_in_the_parameter_guide_and_is_not_carried (self) -> None:
		"""Which inverts what the JD-Xi one rank earlier established about this maker."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])
		flat = " ".join(prose_of("roland", "jupiter_x").split())

		assert "**THE DOCUMENT NAMED FOR THIS INSTRUMENT'S MIDI IS NOT WHERE ITS CONTROLLERS" \
			" ARE, AND EIGHT ROLANDS HAD TAUGHT THE OPPOSITE.**" in flat
		assert "the Parameter Guide carries a `CC#` column on nine of its 75 sheets, one table" \
			" per model**, holding 156 more rows over 46 distinct numbers" in flat

		# **AND THE JD-XI'S LESSON IS CORRECTED RATHER THAN LEFT TO CONTRADICT THIS ONE.**
		assert "So rank 94's lesson was about the JD-Xi and not about Roland" in flat

		# The reason those 156 rows are not below: the meaning turns on a setting.
		assert "21 of the 46 numbers name more than one parameter across those tables" in flat
		assert "That is **not** the collision the `part` field exists for." in flat
		assert "so the meaning turns on what somebody loaded, not on where the message arrived" \
			in flat

		# And it is cited for that, so a reader can go and look.
		assert "parameter_guide" in jupiter.sources
		assert "jd_800" in jupiter.sources

	def test_one_control_is_transmitted_and_never_received (self) -> None:
		"""Because this maker prints two prose halves rather than a chart's two columns."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])

		directions = collections.Counter(
			control.direction for control in jupiter.controls.values())

		assert directions == {"receives": 15, "both": 6, "transmits": 1}

		assert jupiter.controls["foot_type"].cc == 4
		assert jupiter.controls["foot_type"].direction == "transmits"

		# **AND THE SIBLING WITH THE SAME LIST RECORDS NO DIRECTION AT ALL**, which is the
		# comparison worth pinning: the difference is in the reading, not in the instruments.
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert all(control.direction == "both" for control in fantom.controls.values())

		flat = " ".join(prose_of("roland", "jupiter_x").split())

		assert "**One control is transmitted and never received**" in flat

	def test_its_clock_rests_entirely_on_a_document_about_parameters (self) -> None:
		"""The 90-sheet implementation never mentions a timing clock byte."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])

		assert jupiter.midi.clock == "both"
		assert jupiter.midi.transport is None

		said = prose_of("roland", "jupiter_x")

		assert "Sync Mode AUTO, INT, MIDI, USB COM, USB MEM" in said
		assert "Specifies the connector from which MIDI clock messages etc. are output." in said

		flat = " ".join(said.split())

		assert "`F8H` appears on none of the implementation's 90 sheets." in flat
		assert "**So this field rests entirely on a document whose title is about parameters**" \
			in flat

	def test_nrpn_is_empty_because_the_document_disagrees_with_itself (self) -> None:
		"""Three sentences say it exists and the enumeration gives no way to select one."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])

		assert jupiter.midi.nrpn is None

		# Not `none`, which would say somebody established that it answers to no NRPN.
		assert jupiter.midi.nrpn != "none"

		flat = " ".join(prose_of("roland", "jupiter_x").split())

		assert "**THE IMPLEMENTATION CONTRADICTS ITSELF ABOUT NRPN, SO `nrpn` IS LEFT EMPTY" \
			" RATHER THAN SET TO `none`.**" in flat
		assert "the enumeration that gives every controller number it receives gives no 98 and" \
			" no 99" in flat

		# **THE RULE IS BORROWED RATHER THAN INVENTED**, and the definition says whose it is.
		assert "which is the rule `novation/peak` and `novation/circuit_tracks` established" \
			" for `default` and which has not been applied to this field before" in flat

	def test_its_two_documents_complete_each_other_about_aftertouch (self) -> None:
		"""Which is the opposite of the NRPN case, and the definition distinguishes them."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])

		assert jupiter.voice is not None
		assert jupiter.voice.aftertouch == "poly"

		said = prose_of("roland", "jupiter_x")

		assert "Rx Poly Pres OFF, ON Specifies whether polyphonic aftertouch is received (ON)" \
			" or not received (OFF)." in said

		flat = " ".join(said.split())

		assert "**The implementation's silence is not a denial**" in flat
		assert "so the two documents complete each other here rather than disagreeing, which" \
			" is the opposite of the NRPN case above" in flat

		# Following the chain of three Rolands that chose the stronger word.
		for name in ("roland/mc_707", "roland/fantom_6_7_8", "roland/jd_xi"):
			assert pymidiinstrumentdefs.load(name, [CORPUS]).voice.aftertouch == "poly"

	def test_five_parts_in_two_kinds_and_a_polyphony_the_maker_will_not_give (self) -> None:
		"""Four take any model, the fifth takes only a drum kit."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])

		assert list(jupiter.parts) == ["part", "drum"]
		assert jupiter.parts["part"].count == 4
		assert jupiter.parts["part"].channel == "assigned"
		assert jupiter.parts["part"].addressing == "pitches"
		assert jupiter.parts["drum"].count == 1
		assert jupiter.parts["drum"].addressing == "voices"

		assert jupiter.voice is not None
		assert jupiter.voice.polyphony is None
		assert jupiter.voice.polyphony_shared is True

		said = prose_of("roland", "jupiter_x")

		assert "It differs depending on the type and combination of models. As an example, if" \
			" the JUPITER-8 is assigned to all four parts, the maximum simultaneous polyphony" \
			" will be 32 voices (up to eight voices per part)." in said
		assert "No, a drum kit can be used only with PART R. It cannot be used with parts 1-4." \
			in said

		# **A SHARED POOL IS A FACT WHERE THE FIGURE IS NOT**, which is the KRONOS's pairing.
		kronos = pymidiinstrumentdefs.load("korg/kronos", [CORPUS])

		assert kronos.voice.polyphony is None
		assert kronos.voice.polyphony_shared is True

	def test_no_chart_in_any_of_its_eleven_documents (self) -> None:
		"""Which is why the mode is unrecorded rather than guessed."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])

		assert jupiter.midi.mode is None

		flat = " ".join(prose_of("roland", "jupiter_x").split())

		assert "**AND THERE IS NO CHART IN ANY OF THE ELEVEN DOCUMENTS.**" in flat
		assert "no Basic Channel row, no True Voice row, on any of the 377 sheets" in flat

	def test_the_model_id_is_printed_two_ways_in_one_document (self) -> None:
		"""Three statements say 65H and two say 52H, and the definition counts them."""
		flat = " ".join(prose_of("roland", "jupiter_x").split())

		assert "**Three statements say 65H and two say 52H**" in flat

		# Said because of what it costs a reader, not as a complaint about the maker.
		assert "a sysex implementer reading sheet 5 alone would address a device that is not" \
			" there" in flat

	def test_the_owners_manual_names_the_wrong_product_once (self) -> None:
		"""On 25 sheets it is the X's; in one explanation it is the Xm's."""
		flat = " ".join(prose_of("roland", "jupiter_x").split())

		assert "**IT NAMES THE JUPITER-X ON 25 OF ITS 31 SHEETS AND THE JUPITER-Xm ON EXACTLY" \
			" ONE**" in flat
		assert "the setting is this instrument's, and the Parameter Guide, which is titled for" \
			" both, prints the same words" in flat

	def test_every_translation_of_its_manual_is_two_releases_behind (self) -> None:
		"""Which a reader of one would have no way to tell from inside it."""
		flat = " ".join(prose_of("roland", "jupiter_x").split())

		assert "**each of them `Ver. 1.5 and later` against the English one's `Ver. 3.0 and" \
			" later`**" in flat

	def test_the_firmware_floor_is_not_the_implementations_own_version (self) -> None:
		"""One is a claim about the instrument and the other about the document."""
		jupiter = pymidiinstrumentdefs.load("roland/jupiter_x", [CORPUS])

		assert jupiter.model.firmware == "3.0"
		assert jupiter.sources["implementation"].edition == "1.06"

		flat = " ".join(prose_of("roland", "jupiter_x").split())

		assert "**The implementation's own version is a different number**" in flat


class TestProtein:

	"""The Waldorf whose MIDI chapter is a glossary of what MIDI is.

	Most of the MIDI words in its manual are in a six-sheet glossary of general
	terms, and three of the numbers there look exactly like this instrument's
	own.  So the channel range, the note range and the controller range are all
	left unrecorded, and the definition says which sentence each would have come
	from.
	"""

	def test_the_channel_range_is_unrecorded_because_only_a_glossary_gives_one (self) -> None:
		"""A sentence about MIDI is not a sentence about this instrument."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert protein.midi.channels is None
		assert protein.midi.mode is None
		assert protein.voice is not None
		assert protein.voice.note_range is None

		said = prose_of("waldorf", "protein")

		assert "MIDI Channels 1 through 16 are available for this purpose." in said
		assert "Program numbers 1 through 128 can be changed via program change messages." in said
		assert "can be between 0 and 120." in said

		flat = " ".join(said.split())

		assert "**SEVENTY-ONE SHEETS, A SIX-SHEET MIDI GLOSSARY, AND NO IMPLEMENTATION.**" in flat
		assert "**THE CHANNEL RANGE IS LEFT UNRECORDED BELOW FOR EXACTLY THAT REASON**" in flat.upper()

		# **AND THE LESSON IS NAMED AS THE THIRD IN A ROW**, which is the point of keeping it.
		assert "a glossary is not an implementation" in flat

	def test_five_numbers_carried_and_ten_recorded_rather_than_listed (self) -> None:
		"""Because the maker printed two ends and a rule, not ten numbers."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert len(protein.controls) == 5
		assert sorted(control.cc for control in protein.controls.values()
			if control.cc is not None) == [1, 2, 11, 64, 74]

		flat = " ".join(prose_of("waldorf", "protein").split())

		assert "**AND TEN MORE NUMBERS ARE NOT BELOW, BECAUSE THE MAKER PRINTED A RANGE AND NOT" \
			" A LIST.**" in flat
		assert "**Only 22 and 31 are printed.**" in flat
		assert "found 24, 28 and 30 on no page" in flat

		# The gate that decided it, named so the next reader does not argue it again.
		assert "which is `elektron/tonverk`'s gate at rank 88" in flat

		# And none of the five names a parameter - every one is a modulation source.
		assert {control.group for control in protein.controls.values()} == {"modulation"}

	def test_control_change_is_empty_because_it_is_both_things_the_field_names (self) -> None:
		"""Fixed sources in the matrix, and MIDI learn for everything else."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert protein.midi.control_change is None
		assert not protein.midi.refuses_control_change

		said = prose_of("waldorf", "protein")

		assert "Protein allows you to map its parameters to incoming MIDI control change data." \
			in said
		assert "If no MIDI CC mapping was made, Nothing Mapped is displayed." in said

		flat = " ".join(said.split())

		assert "**`control_change` IS LEFT EMPTY BECAUSE IT HOLDS ONE WORD AND THIS INSTRUMENT" \
			" IS BOTH THINGS.**" in flat

		# The six that do use `learned` all carry nothing, which is why writing it here would
		# have said the five above are defaults somebody can change.
		for name in ("akai/mpc_live", "arturia/drumbrute_impact", "dirtywave/m8",
				"roland/d_50", "synthstrom_audible/deluge", "teenage_engineering/op_1"):
			other = pymidiinstrumentdefs.load(name, [CORPUS])

			assert other.midi.control_change == "learned"
			assert not other.controls

	def test_its_four_layers_take_channels_in_one_mode_of_four (self) -> None:
		"""So a consumer trusting the channels without the mode addresses nothing."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert list(protein.parts) == ["layer"]
		assert protein.parts["layer"].count == 4
		assert protein.parts["layer"].channel_offset == 0
		assert protein.parts["layer"].channel is None

		said = prose_of("waldorf", "protein")

		assert "Based on the determined MIDI Receive Channel in the Settings, the select MIDI" \
			" Channel triggers Layer A, the next MIDI channel Layer B and so on." in said

		flat = " ".join(said.split())

		assert "**THESE PARTS EXIST IN ONE MODE OF FOUR, WHICH IS AN OPEN QUESTION ON THE" \
			" FORMAT FROM THE OTHER SIDE.**" in flat
		assert "**IN THE OTHER THREE MODES ALL FOUR ANSWER ON THE ONE CHANNEL.**" in flat

	def test_eight_voices_shared_which_the_ob_x8_could_not_say (self) -> None:
		"""One figure is true here and would have been false there."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert protein.voice is not None
		assert protein.voice.polyphony == 8
		assert protein.voice.polyphony_shared is True
		assert protein.voice.voicing_modes == (1, 8)

		said = prose_of("waldorf", "protein")

		assert "Keep in mind that all 4 layers share the maximum of 8 voices." in said

		# **THE CONTRAST THAT MAKES THE FIGURE WORTH HAVING**, asserted against the sibling.
		ob_x8 = pymidiinstrumentdefs.load("oberheim/ob_x8", [CORPUS])

		assert ob_x8.voice.polyphony is None
		assert all(part.polyphony == 4 for part in ob_x8.parts.values())

		flat = " ".join(said.split())

		assert "**That sentence is why this definition can carry a figure where" \
			" `oberheim/ob_x8` could not**" in flat

	def test_the_specification_is_stale_and_the_changelog_dates_it (self) -> None:
		"""One statement superseded, which is not two contradicting each other."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert protein.midi.program_change is not None
		assert protein.midi.program_change.presets == 360
		assert protein.midi.program_change.receives is None

		said = prose_of("waldorf", "protein")

		assert "Capacity of 250 patch memory slots" in said
		assert "Increased preset storage from 250 to 360" in said
		assert "Recognizing MIDI Bank Select (LSB aka CC32) messages to choose from all 360" \
			" slots" in said

		flat = " ".join(said.split())

		assert "**That is not two statements contradicting each other**" in flat
		assert "**it is one statement superseded by a dated one**" in flat

		# **AND THE MESSAGE THAT IS NAMED IS NOT A PROGRAM CHANGE**, so that field stays empty.
		assert "**AND THE ONLY STATEMENT ABOUT CHOOSING A PRESET OVER MIDI NAMES BANK SELECT" \
			" RATHER THAN PROGRAM CHANGE**" in flat
		assert "**An inference is not a citation**" in flat

	def test_the_document_that_settles_most_is_the_one_the_page_does_not_name (self) -> None:
		"""A bare address in the body of an answer about something else."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert "changelog" in protein.sources
		assert protein.model.firmware == "1.02"

		said = prose_of("waldorf", "protein")

		assert "Changelog - Protein Firmware 1.02 (January 2026)" in said
		assert "New OS versions are available in your “my waldorf” account under Hardware & OS" \
			" Updates. Here is the changelog:" in said

		flat = " ".join(said.split())

		assert "**AND THE DOCUMENT THAT SETTLES THE MOST IS THE ONE THE DOWNLOADS PAGE DOES NOT" \
			" NAME.**" in flat

	def test_its_text_layer_loses_the_f_ligature_and_the_checker_folds_it_back (self) -> None:
		"""So the words a reader sees on the page are the words a definition can quote."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])
		flat = " ".join(prose_of("waldorf", "protein").split())

		assert "**ITS TEXT LAYER PUTS A LOW LINE WHERE THE PAGE PRINTS AN `f` LIGATURE**, 226" \
			" times" in flat
		assert "`tools/check_quotations.py` now reads a low line back as an `f`" in flat

		# And the quotations that only work because of it are in the file, so a change to the
		# fold fails here as well as in the checker.
		said = prose_of("waldorf", "protein")

		assert "Legato: Same as Mono, but when you play legato, only the first note that was" \
			" played triggers the envelopes." in said
		assert "You can also use Select to define the Vel Amnt (Velocity Amount), so that the" \
			" volume will be affected by keyboard velocity." in said

	def test_the_german_edition_is_a_revision_behind_and_omits_nothing (self) -> None:
		"""Which is what rank 95's instrument needed comparing with."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert "german_manual" in protein.sources
		assert protein.sources["german_manual"].edition == "1"
		assert protein.sources["manual"].edition == "2"

		flat = " ".join(prose_of("waldorf", "protein").split())

		assert "**CITED FOR A COMPARISON RATHER THAN FOR A FACT, AND IT IS THE REASSURING" \
			" ONE.**" in flat
		assert "**every MIDI fact the English edition has**" in flat

		# The instrument it is being compared with, and what it did instead.
		hexdrums = " ".join((pymidiinstrumentdefs.load(
			"erica_synths/hexdrums", [CORPUS]).source or "").split())

		assert "THE JAPANESE EDITION IS CITED FOR AN ABSENCE" in hexdrums

	def test_it_sends_no_clock_although_it_has_a_sequencer (self) -> None:
		"""An absence a consumer may be surprised by rather than a silence."""
		protein = pymidiinstrumentdefs.load("waldorf/protein", [CORPUS])

		assert protein.midi.clock == "receives"
		assert protein.midi.transport is None

		said = prose_of("waldorf", "protein")

		assert "Determines how Protein reacts to incoming MIDI Clock messages." in said

		flat = " ".join(said.split())

		assert "**Nothing in any document says it sends one**" in flat


class TestEdge:

	"""No controls, and the one definition that says so from a list rather than a search.

	Everything this maker publishes for this instrument is a quick start guide, and
	the product page embeds its own list of what that is: six items, four of them
	the same guide.  So the absence of a manual is a fact read off a page rather
	than a failure to find one.
	"""

	def test_it_does_not_say_none_and_the_sibling_does (self) -> None:
		"""Same maker, same kind of document, opposite answer - and the reason is exact."""
		edge = pymidiinstrumentdefs.load("behringer/edge", [CORPUS])
		td_3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert not edge.controls
		assert edge.midi.control_change is None
		assert not edge.midi.refuses_control_change

		assert not td_3.controls
		assert td_3.midi.control_change == "none"
		assert td_3.midi.refuses_control_change

		flat = " ".join(prose_of("behringer", "edge").split())

		assert "**NO CONTROLS, AND THIS FILE DELIBERATELY DOES NOT SAY `none`.**" in flat
		assert "**The EDGE's guides have no table of MIDI messages at all**, in either edition," \
			" so there is nothing for a controller to be missing from." in flat

	def test_there_is_no_manual_and_that_is_read_off_a_list (self) -> None:
		"""The page carries its own download list, so this is a count rather than a search."""
		edge = pymidiinstrumentdefs.load("behringer/edge", [CORPUS])

		assert list(edge.sources) == ["guide", "older_guide", "product_page"]

		flat = " ".join(prose_of("behringer", "edge").split())

		assert "it has six items: four quick start guides and two builds of an application" \
			in flat

		# **THE SIBLING THAT PROVES THE MAKER WOULD HAVE PUBLISHED ONE**, one letter away in
		# the product code, with its two controllers coming out of exactly that document.
		neutron = pymidiinstrumentdefs.load("behringer/neutron", [CORPUS])

		assert "manual" in neutron.sources
		assert neutron.sources["manual"].title == "NEUTRON User Manual"
		assert len(neutron.controls) == 2

		assert "**So this maker does publish a manual when there is one to publish, and for" \
			" this instrument it has not.**" in flat

	def test_two_of_the_six_are_the_same_guide_four_years_apart (self) -> None:
		"""And only the newer one is labelled as the one to take."""
		edge = pymidiinstrumentdefs.load("behringer/edge", [CORPUS])

		assert edge.sources["guide"].edition == "V 2.0"
		assert edge.sources["older_guide"].edition == "V 1.0"
		assert str(edge.sources["guide"].dated) == "2025-01-22"
		assert str(edge.sources["older_guide"].dated) == "2021-11-15"

		flat = " ".join(prose_of("behringer", "edge").split())

		assert "A reader clicking the third item gets the 2021 edition." in flat
		assert "**No MIDI was added or removed between the two editions.**" in flat

	def test_the_two_covers_describe_different_instruments (self) -> None:
		"""And the page that serves the newer one still advertises what it dropped."""
		flat = " ".join(prose_of("behringer", "edge").split())

		assert "**`Semi-Modular` and `16-Voice Poly Chain` are gone from the newer one**" in flat
		assert "So the page and the document it offers do not agree about what this instrument" \
			" is." in flat

	def test_the_poly_chain_is_documented_nowhere_but_a_picture (self) -> None:
		"""Which is why a monophonic instrument's polyphony reads one."""
		edge = pymidiinstrumentdefs.load("behringer/edge", [CORPUS])

		assert edge.voice is not None
		assert edge.voice.polyphony == 1

		said = prose_of("behringer", "edge")

		assert "Number of voices Monophonic" in said
		assert "Turns red if poly mode is activated." in said

		flat = " ".join(said.split())

		assert "**There is no prose about it anywhere in either edition**" in flat
		assert "A consumer cannot be told from these documents how to do the thing the page" \
			" sells." in flat

		# **AND THE POLY CHAIN IS NOT THIS INSTRUMENT'S POLYPHONY**, which the field would
		# otherwise be read as saying.
		assert "the poly chain is sixteen monophonic EDGEs passing MIDI along a THRU, each" \
			" playing a note" in flat

	def test_the_spanish_label_on_that_diagram_is_a_plastics_term (self) -> None:
		"""In both editions, four years apart."""
		flat = " ".join(prose_of("behringer", "edge").split())

		assert "**AND THE SPANISH LABEL ON THAT DIAGRAM READS `Sistema de cadena de" \
			" polietileno`**" in flat
		assert "a Spanish reader looking for the poly chain section is looking for a plastics" \
			" term" in flat

	def test_its_channel_has_two_mechanisms_and_no_word_on_which_wins (self) -> None:
		"""Dip switches on the rear panel, and an application this corpus does not run."""
		edge = pymidiinstrumentdefs.load("behringer/edge", [CORPUS])

		assert edge.midi.channels == (1, 16)
		assert edge.midi.mode is None

		said = prose_of("behringer", "edge")

		assert "A MIDI channel from 1 to 16 is selectable using the dip switches." in said
		assert "The SYNTHTRIBE application allows you to select the MIDI channel number and to" \
			" set and adjust various parameters of the EDGE to suit your preferences." in said

		flat = " ".join(said.split())

		assert "**Two mechanisms for one setting and no word on which wins.**" in flat

		# **AND THE APPLICATION IS WHERE THE CONTROLLERS WOULD BE, AND IT WAS NOT RUN.**
		assert "vendor software is not installed to read a specification" in flat

	def test_it_takes_a_clock_it_will_not_follow_above_300_bpm (self) -> None:
		"""Which no field here holds, so the definition says it."""
		edge = pymidiinstrumentdefs.load("behringer/edge", [CORPUS])

		assert edge.midi.clock == "receives"
		assert edge.midi.transport is None

		said = prose_of("behringer", "edge")

		assert "TEMPO – Tempo can be set from 10 to 10,000 when set to internal (INT). Via MIDI" \
			" and USB the range is 10- 300 BPM." in said

		flat = " ".join(said.split())

		assert "**So a clock above 300 BPM is something this instrument will not follow**" in flat

		# And nothing says what its output socket sends, so nothing records transmission.
		assert "MIDI OUT / THRU – MIDI DIN can be used as an output or a thru." in said
		assert "**What it puts out is never stated**" in flat

	def test_the_word_velocity_is_in_it_seven_times_and_never_about_midi (self) -> None:
		"""Which is why that field is empty on an instrument whose panel says VELOCITY."""
		edge = pymidiinstrumentdefs.load("behringer/edge", [CORPUS])

		assert edge.voice is not None
		assert edge.voice.velocity is None
		assert edge.voice.aftertouch is None
		assert edge.voice.pitch_bend is None
		assert edge.voice.note_range is None

		said = prose_of("behringer", "edge")

		assert "VEL – These 8 controls adjust the velocity of each." in said
		assert "Velocity 0 V to 5 V" in said

		flat = " ".join(said.split())

		assert "**So the word appears seven times in this document and never once about a MIDI" \
			" message.**" in flat

	def test_its_guide_prints_two_pages_to_a_sheet_as_the_siblings_does (self) -> None:
		"""So a locator is arithmetic rather than a page turn, and the format holds it."""
		edge = pymidiinstrumentdefs.load("behringer/edge", [CORPUS])

		assert edge.sources["guide"].pages_per_sheet == 2
		assert edge.sources["guide"].page_offset == 1

		td_3 = pymidiinstrumentdefs.load("behringer/td_3", [CORPUS])

		assert td_3.sources["guide"].pages_per_sheet == 2
		assert td_3.sources["guide"].page_offset == 1

		# **AND THE OLDER EDITION NUMBERS ONLY SOME OF ITS SHEETS**, so it has no page to
		# turn to at all and is cited by name.
		assert edge.sources["older_guide"].paginated is False

		flat = " ".join(prose_of("behringer", "edge").split())

		assert "**IT NUMBERS SOME OF ITS SHEETS AND NOT OTHERS**" in flat


class TestNymphes:

	"""82 controls read off two pages that are pictures, and all of them start switched off.

	Its maker publishes the controller list as an image, so the text layer of
	those two sheets holds thirteen characters between them - and a factory reset
	leaves control change reception off, which no field in this format can say.
	"""

	def test_its_controller_list_is_a_picture_and_the_file_says_so (self) -> None:
		"""So the citation checker reports plainly that it cannot look for 68 numbers."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		assert len(nymphes.controls) == 82
		assert len(nymphes.groups) == 7
		assert nymphes.sources["manual"].pictured_pages == (22, 23)

		flat = " ".join(prose_of("dreadbox", "nymphes").split())

		assert "**AND THE LIST ITSELF IS A PICTURE.**" in flat
		assert "the table is an image, so a search of this manual for `LPF Cutoff` or `Reverb" \
			" Mix` finds nothing" in flat

		# **THE ONLY OTHER DEFINITION THAT DECLARES PICTURED PAGES**, so the pair is worth
		# asserting together: a reader comparing them sees what the field is for.
		declared = sorted(name for name in pymidiinstrumentdefs.available([CORPUS])
			for source in pymidiinstrumentdefs.load(name, [CORPUS]).sources.values()
			if source.pictured_pages)

		assert "dreadbox/nymphes" in declared

	def test_every_control_is_off_until_somebody_turns_it_on (self) -> None:
		"""Which is the first thing a reader of this definition needs to know."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		assert nymphes.controls
		assert nymphes.midi.control_change is None

		said = prose_of("dreadbox", "nymphes")

		assert "CC : In = OFF, out=OFF" in said

		flat = " ".join(said.split())

		assert "**EIGHTY-TWO CONTROLS, AND EVERY ONE OF THEM IS OFF WHEN THE INSTRUMENT LEAVES" \
			" THE FACTORY.**" in flat
		assert "**No field in this format says that**" in flat

	def test_four_numbers_are_out_of_sequence_and_the_maker_prints_them_in_bold (self) -> None:
		"""Because 64 and 68 were already the standard's, which the maker kept."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		for name, number in (("mod_source_reverb_size_depth", 86),
				("mod_source_reverb_decay_depth", 87),
				("mod_source_reverb_filter_depth", 88),
				("mod_source_reverb_mix_depth", 89)):
			assert nymphes.controls[name].cc == number
			assert nymphes.controls[name].group == "modulation"

		# The two it kept at the standard's numbers, which is why the four had to move.
		assert nymphes.controls["sustain_pedal"].cc == 64
		assert nymphes.controls["legato"].cc == 68

		flat = " ".join(prose_of("dreadbox", "nymphes").split())

		assert "**FOUR OF ITS NUMBERS ARE SET OUT OF SEQUENCE AND THE MAKER PRINTS THEM IN" \
			" BOLD.**" in flat

	def test_the_seven_numbers_it_skips_are_mostly_ones_this_corpus_refuses (self) -> None:
		"""Six of the seven, and the seventh is the one place the maker crossed the standard."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		used = {control.cc for control in nymphes.controls.values()}
		skipped = [n for n in range(1, 90) if n not in used]

		assert skipped == [2, 6, 38, 65, 66, 67, 69]

		# **AND THE ONE IT DID CROSS**, which a consumer sending bank select would meet.
		assert nymphes.controls["mod_source_osc_level_depth"].cc == 32

		flat = " ".join(prose_of("dreadbox", "nymphes").split())

		assert "CC 32 is `Mod Source OSC Level Depth` here and bank select LSB in the standard," \
			" so a controller sending bank select to a Nymphes moves a modulation depth." in flat

	def test_its_manual_cannot_count_its_own_pages (self) -> None:
		"""So a locator here is the file's sheet, which is what eighteen of them print anyway."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		assert nymphes.sources["manual"].page_offset == 0
		assert nymphes.sources["manual"].paginated is not False

		flat = " ".join(prose_of("dreadbox", "nymphes").split())

		assert "**THE MANUAL CANNOT COUNT ITS OWN PAGES.**" in flat
		assert "two sheets claim page 10, no sheet claims page 1, and the last three run one" \
			" behind" in flat

	def test_the_two_documents_that_settle_most_are_inside_a_firmware_archive (self) -> None:
		"""And the support page that offers it does not say what is in it."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		assert "v2_notes" in nymphes.sources
		assert "v2_1_notes" in nymphes.sources
		for key in ("v2_notes", "v2_1_notes"):
			url = nymphes.sources[key].url

			assert url is not None and url.endswith(".zip")

		said = prose_of("dreadbox", "nymphes")

		assert "Polyphonic Aftertouch is implemented, so that Nymphes can respond to a keyboard/" \
			" controller that allows this feature." in said
		assert "Pitch wheel : +/-3 semitones" in said

		flat = " ".join(said.split())

		assert "**The support page offers the archive and does not say what is in it.**" in flat

	def test_the_makers_pages_refused_and_the_shared_copy_is_cited (self) -> None:
		"""Three times, spaced apart, nothing varied - while its uploads served fine."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])
		typhon = pymidiinstrumentdefs.load("dreadbox/typhon", [CORPUS])

		# **ONE DOCUMENT, TWO CITERS, AND THE SAME DIGEST** - which is what makes this honest
		# rather than a shortcut.
		assert nymphes.sources["support_page"].sha256 == typhon.sources["support_page"].sha256
		assert str(nymphes.sources["support_page"].retrieved) == "2026-10-03"
		assert str(nymphes.sources["manual"].retrieved) == "2026-10-06"

		flat = " ".join(prose_of("dreadbox", "nymphes").split())

		assert "**AND THE MAKER'S OWN PAGES REFUSED THIS MACHINE.**" in flat
		assert "three times, spaced apart, with nothing varied between attempts" in flat
		assert "**Every file it names was fetched fresh and answered 200**" in flat

	def test_its_channel_can_be_set_further_by_midi_than_by_its_own_knob (self) -> None:
		"""A player with no MIDI source to hand reaches only channels 1 to 7."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		assert nymphes.midi.channels == (1, 16)
		assert nymphes.midi.per_voice_channels is True

		said = prose_of("dreadbox", "nymphes")

		assert "Send any MIDI message (channel 1 to 16) or use the rotary to select from channel" \
			" 1 to 7." in said
		assert "Nymphes can now be set to any MIDI channel (except of 1 to 7) with the use of" \
			" MIDI learn." in said

		flat = " ".join(said.split())

		assert "**So a player with no MIDI source to hand can only reach channels 1 to 7**" in flat

	def test_six_voices_spent_four_ways_and_an_aftertouch_that_is_both (self) -> None:
		"""Polyphonic for sixteen destinations and monophonic for the rest."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		assert nymphes.voice is not None
		assert nymphes.voice.polyphony == 6
		assert nymphes.voice.voicing_modes == (1, 2, 3, 6)
		assert nymphes.voice.aftertouch == "poly"
		assert nymphes.voice.pitch_bend is not None
		assert nymphes.voice.pitch_bend.semitones == 3
		assert nymphes.voice.pitch_bend.programmable is True

		flat = " ".join(prose_of("dreadbox", "nymphes").split())

		assert "**this instrument's aftertouch is polyphonic for some destinations and" \
			" monophonic for the rest.**" in flat

		# **AND THE FACTORY BEND DEPTH IS ONLY IN THE RELEASE NOTES**, which is why they are cited.
		assert "**A FACTORY DEPTH THAT ONLY THE RELEASE NOTES GIVE.**" in flat

	def test_its_documents_disagree_about_which_way_its_socket_points (self) -> None:
		"""And the definition carries neither, because no field records that."""
		flat = " ".join(prose_of("dreadbox", "nymphes").split())

		assert "WHAT ITS OWN DOCUMENTS DISAGREE ABOUT, WHICH IS WHICH WAY ITS SOCKET POINTS." \
			in flat
		assert "the connection diagram on the same document's sheet 4 labels the hardware jack" \
			" `MIDI IN`**" in flat
		assert "a reader buying the included DIN5 adapter should know the document says both" \
			" things" in flat

	def test_the_clock_was_recorded_as_absent_until_the_sweep_caught_it (self) -> None:
		"""An absence is a claim about every page, so it is swept for rather than noticed."""
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])

		assert nymphes.midi.clock == "receives"
		assert nymphes.midi.transport is None

		said = prose_of("dreadbox", "nymphes")

		# The sentence that was missed, eleven sheets before anything else about MIDI.
		assert "BPM (where the rate can sync to midi clock)" in said
		assert "When the Rate is set to BPM , but no clock is send, it automatically works on" \
			" low rate mode." in said

		flat = " ".join(said.split())

		assert "**A first reading of this definition recorded the clock as unmentioned**" in flat
		assert "**An absence is a claim about every page, so it is the one kind of statement" \
			" that has to be swept for rather than noticed.**" in flat


class TestMpcKey37:

	"""The third definition out of one guide, and the first of the three to find anything.

	Akai's MPC Standalone OS guide runs to 530 sheets and describes fourteen
	machines.  `akai/mpc_live` and `akai/mpc_sample` both read it and carried no
	controls at all.  This machine has a keybed, and the guide has two sheets
	about keybeds that neither of them had any reason to read.
	"""

	def test_one_control_and_it_is_a_factory_default (self) -> None:
		"""Which is exactly what `control_change: learned` means beside a control."""
		key_37 = pymidiinstrumentdefs.load("akai/mpc_key_37", [CORPUS])

		assert len(key_37.controls) == 1
		assert key_37.controls["modulation"].cc == 1
		assert key_37.controls["modulation"].direction == "transmits"
		assert key_37.midi.control_change == "learned"

		said = prose_of("akai", "mpc_key_37")

		assert "Mod Wheel: Use this field to select the MIDI function for the keyboard" \
			" modulation wheel. Select Disable, Default - CC 001: Modulation, or CC 000-126." \
			in said

		flat = " ".join(said.split())

		assert "**ONE CONTROL, AND IT IS A FACTORY ASSIGNMENT THE PLAYER CAN CHANGE TO ANY OTHER" \
			" NUMBER.**" in flat

		# **THE TWO BEFORE IT CARRY NOTHING**, which is what makes one number worth a definition.
		for name in ("akai/mpc_live", "akai/mpc_sample"):
			assert not pymidiinstrumentdefs.load(name, [CORPUS]).controls

	def test_three_definitions_cite_one_document_with_one_digest (self) -> None:
		"""A mismatch would mean one of them is reading a different file."""
		key_37 = pymidiinstrumentdefs.load("akai/mpc_key_37", [CORPUS])
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])

		assert key_37.sources["guide"].sha256 == live.sources["guide"].sha256
		assert key_37.sources["guide"].edition == "v3.9"
		assert str(key_37.sources["guide"].retrieved) == "2026-10-04"

		flat = " ".join(prose_of("akai", "mpc_key_37").split())

		assert "one document, three citers, one digest" in flat

		# And the definition sends a reader to the sibling's scoping account rather than
		# repeating it, which is the thing that makes any statement here trustworthy.
		assert "**That account is not repeated here**" in flat

	def test_the_keybed_sheets_are_what_this_definition_adds (self) -> None:
		"""Scoped by their own first sentence, which names this machine."""
		key_37 = pymidiinstrumentdefs.load("akai/mpc_key_37", [CORPUS])

		said = prose_of("akai", "mpc_key_37")

		assert "The keyboard control screen allows you to edit the functions of the keybed on" \
			" MPC Key 61, Key 37, and Key 37 G2." in said

		# The three fields that sentence makes statements about this box rather than about MPCs.
		assert key_37.midi.channels == (1, 16)
		assert key_37.voice is not None
		assert key_37.voice.aftertouch == "channel"
		assert key_37.voice.velocity is not None
		assert key_37.voice.velocity.note_on == "received"

		# **AND THE SIBLING RECORDS NONE OF THEM**, because its machine has no keys.
		live = pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS])

		assert live.voice is not None
		assert live.voice.aftertouch is None
		assert live.voice.velocity is None

	def test_the_maker_names_the_kind_of_aftertouch_in_a_bracket (self) -> None:
		"""Which is the whole reason that field can be filled at all."""
		key_37 = pymidiinstrumentdefs.load("akai/mpc_key_37", [CORPUS])

		assert key_37.voice is not None
		assert key_37.voice.aftertouch == "channel"

		said = prose_of("akai", "mpc_key_37")

		assert "Aftertouch (Channel Pressure): This determines whether aftertouch is enabled (As" \
			" Played) or not (Disable)." in said
		assert "37 synth-action keys with aftertouch" in said

		flat = " ".join(said.split())

		assert "That bracket is the whole reason this field can be filled" in flat

	def test_the_machine_it_is_not_is_named_on_the_same_sheets (self) -> None:
		"""There is an MPC Key 37 and an MPC Key 37 G2, and they differ in MIDI."""
		key_37 = pymidiinstrumentdefs.load("akai/mpc_key_37", [CORPUS])

		assert key_37.model.name == "MPC Key 37"

		flat = " ".join(prose_of("akai", "mpc_key_37").split())

		assert "**AND THE MACHINE IT IS NOT IS NAMED ON THE SAME SHEETS.**" in flat
		assert "**The two differ in MIDI**: the G2 has `Ableton Live Control Mode` and a USB-C" \
			" port that can act as a host for MIDI controllers, and this machine has neither." \
			in flat

	def test_the_guide_contradicts_itself_about_this_machines_keybed (self) -> None:
		"""Recorded because the fields below come from the same neighbourhood."""
		said = prose_of("akai", "mpc_key_37")

		assert "37-key semi-weighted, velocity-sensitive" in said
		assert "37 synth-action keys with aftertouch" in said

		flat = " ".join(said.split())

		assert "Semi-weighted and synth-action are different things, and a reader cannot tell" \
			" from this document which this instrument has." in flat

	def test_fifteen_fixed_velocities_or_the_one_that_was_played (self) -> None:
		"""A thing the velocity field cannot say, so the definition says it."""
		key_37 = pymidiinstrumentdefs.load("akai/mpc_key_37", [CORPUS])

		assert key_37.voice is not None
		assert key_37.voice.velocity is not None
		assert key_37.voice.velocity.note_on == "received"

		said = prose_of("akai", "mpc_key_37")

		assert "Alternatively, you can set a fixed velocity for all note on messages, at 12%," \
			" 18%, 25%, 31%, 37%, 43%, Half, 56%, 62%, 68%, 75%, 81%, 87%, 93% or Full" \
			" velocity." in said

		flat = " ".join(said.split())

		assert "**So fifteen fixed values or the one that was played**" in flat

	def test_it_cannot_send_one_of_the_128_program_numbers (self) -> None:
		"""A fact about the field rather than about the format, so the account holds it."""
		key_37 = pymidiinstrumentdefs.load("akai/mpc_key_37", [CORPUS])

		assert key_37.midi.program_change is not None
		assert key_37.midi.program_change.sends is True
		assert key_37.midi.program_change.presets is None

		said = prose_of("akai", "mpc_key_37")

		assert "a value from 1-127" in said

		flat = " ".join(said.split())

		assert "**this machine cannot send one of the 128 numbers a program change can carry**" \
			in flat

	def test_two_of_its_four_clock_choices_are_not_midi_clock (self) -> None:
		"""Which no field here holds, so the definition names them."""
		key_37 = pymidiinstrumentdefs.load("akai/mpc_key_37", [CORPUS])

		assert key_37.midi.clock == "both"

		said = prose_of("akai", "mpc_key_37")

		assert "receives MIDI Clock information (MIDI Clock), MIDI Time Code information (MTC)," \
			" communication from Ableton Link, or none of these (Off)" in said

		flat = " ".join(said.split())

		assert "**Two of the four choices either way are not MIDI clock at all**" in flat


class TestTR8:

	"""A complete chart five firmware releases old, and an update that carries on from it.

	The chart prints the version it describes on its own face - 1.11 - and the
	update document on the same page carries this instrument to 1.60.  So the
	chart is where the fifty controller numbers are and it is not where this
	instrument's MIDI ends.
	"""

	def test_fifty_controls_and_three_it_obeys_without_reporting (self) -> None:
		"""The scatter controls are crossed transmitted and marked recognized."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		assert len(tr_8.controls) == 50
		assert len(tr_8.groups) == 5

		directions = collections.Counter(
			control.direction for control in tr_8.controls.values())

		assert directions == {"both": 47, "receives": 3}

		for name, number in (("scatter_type", 68), ("scatter_depth", 69), ("scatter_sw", 70)):
			assert tr_8.controls[name].cc == number
			assert tr_8.controls[name].direction == "receives"
			assert tr_8.controls[name].group == "scatter"

		flat = " ".join(prose_of("roland", "tr_8").split())

		assert "so a TR-8 can be told to scatter and will never tell anybody that it is" in flat

	def test_the_chart_is_five_firmware_releases_old (self) -> None:
		"""And the update document's last sheet is a MIDI section it has no row for."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		assert tr_8.model.firmware == "1.60"
		assert str(tr_8.sources["chart"].dated) == "2014-11-18"

		said = prose_of("roland", "tr_8")

		assert "Model: TR-8 Date: Nov. 18, 2014 Version: 1.11" in said

		flat = " ".join(said.split())

		assert "**A COMPLETE IMPLEMENTATION CHART ON ONE SHEET, AND IT IS FIVE FIRMWARE RELEASES" \
			" OLD.**" in flat
		assert "**So the chart is where the 50 controller numbers come from and it is not where" \
			" this instrument's MIDI ends**" in flat

		# **AND THE MIDI SECTION IS NEXT TO THE OLDEST RELEASE**, which is the trap.
		assert "**the oldest release is the one next to the MIDI section**, and a reader who" \
			" stops at sheet 1 misses it" in flat

	def test_eight_notes_that_are_not_drums_and_are_not_carried (self) -> None:
		"""Given as names, never as numbers, with no octave convention stated."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		assert tr_8.voice is not None
		assert set(tr_8.voice.voices.values()) == {36, 37, 38, 39, 42, 43, 46, 47, 49, 50, 51}

		said = prose_of("roland", "tr_8")

		assert "C0 ACCENT PATTERN ALL ON/OFF" in said

		flat = " ".join(said.split())

		assert "**THAT SECTION ADDS EIGHT NOTES THAT ARE NOT DRUMS**" in flat
		assert "**They are given as note names and never as numbers**" in flat
		assert "`C0` is 12 under one common convention and 24 under another, and a definition" \
			" that picked one would be inventing the difference" in flat

	def test_eleven_instruments_over_seventeen_notes_with_no_gap (self) -> None:
		"""Because five of the eleven answer to two numbers each."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		assert tr_8.voice is not None
		assert tr_8.voice.note_range == (35, 51)
		assert len(tr_8.voice.voices) == 11

		# Eleven voices named, seventeen notes in the range, and every one of them sounds.
		for note in range(35, 52):
			assert tr_8.voice.plays_note(note)

		assert not tr_8.voice.plays_note(34)
		assert not tr_8.voice.plays_note(52)

		flat = " ".join(prose_of("roland", "tr_8").split())

		assert "**ELEVEN INSTRUMENTS, SEVENTEEN NOTES, AND NOT A GAP BETWEEN THEM.**" in flat
		assert "so **every number from 35 to 51 sounds something**" in flat

	def test_an_expansion_board_changes_the_map_and_the_stock_one_is_carried (self) -> None:
		"""Which is the ruling the JU-06A set and the drumlogue followed."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		# The four numbers the expansion takes over are not voices here.
		assert 35 not in tr_8.voice.voices.values()
		assert 40 not in tr_8.voice.voices.values()
		assert 54 not in tr_8.voice.voices.values()
		assert 56 not in tr_8.voice.voices.values()

		flat = " ".join(prose_of("roland", "tr_8").split())

		assert "**AND FITTING THAT BOARD CHANGES THE MAP.**" in flat
		assert "**This definition carries the instrument as sold**" in flat

		# The two rulings it follows, both in this corpus.
		assert "`roland/ju_06a` set at rank 87 and `korg/drumlogue` followed at 93" in flat

	def test_the_chart_names_its_drums_after_a_machine_this_one_cannot_be (self) -> None:
		"""Its own footnote says the names depend on the selected instrument set."""
		said = prose_of("roland", "tr_8")

		assert "The instrument names are for the 707. These names will differ depending on the" \
			" instrument set that's selected." in said

		flat = " ".join(said.split())

		assert "**AND THE CHART NAMES ITS INSTRUMENTS AFTER A MACHINE THE STOCK TR-8 CANNOT" \
			" BE.**" in flat

	def test_a_discontinued_rolands_page_is_not_always_an_empty_shell (self) -> None:
		"""Which the TR-909 needed the US manual archive for, and this one does not."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		assert len(tr_8.sources) == 5

		flat = " ".join(prose_of("roland", "tr_8").split())

		assert "**So that habit is not a rule**, and the next discontinued Roland is worth" \
			" checking before assuming." in flat

		# The sibling that needed the archive, so the pair is assertable rather than asserted.
		tr_909 = " ".join((pymidiinstrumentdefs.load("roland/tr_909", [CORPUS]).source or "").split())

		assert "archive" in tr_909.lower()

	def test_what_the_chart_crosses_in_every_box (self) -> None:
		"""A checked absence rather than a silence, which is what a chart is for."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		assert tr_8.voice is not None
		assert tr_8.voice.aftertouch == "none"
		assert tr_8.voice.pitch_bend is None
		assert tr_8.midi.sysex is False
		assert tr_8.midi.nrpn is None

		assert tr_8.midi.mode == 4
		assert tr_8.midi.program_change is not None
		assert tr_8.midi.program_change.receives is True
		assert tr_8.midi.program_change.sends is False
		assert tr_8.midi.program_change.presets == 15

		flat = " ".join(prose_of("roland", "tr_8").split())

		assert "**FOUR, WHICH IS OMNI OFF AND MONO**" in flat
		assert "An odd row for an eleven-voice drum machine, and it is what the chart says." \
			in flat

	def test_an_omni_tr_8_still_transmits_on_channel_ten (self) -> None:
		"""Which no field here holds, so the account carries it."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		assert tr_8.midi.channels == (1, 16)

		said = prose_of("roland", "tr_8")

		assert "ONn (OMNI) MIDI messages of all channels are received. The MIDI transmit channel" \
			" will be 10." in said

		flat = " ".join(said.split())

		assert "**So an omni TR-8 still transmits on 10**, which no field here holds." in flat

	def test_its_manual_is_one_a3_sheet (self) -> None:
		"""This maker's fold-out poster format, so it is cited by name rather than by page."""
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		assert tr_8.sources["manual"].paginated is False
		assert tr_8.sources["chart"].paginated is False

		flat = " ".join(prose_of("roland", "tr_8").split())

		assert "**ONE A3 SHEET, 1,191 BY 842 POINTS, CARRYING 17,395 CHARACTERS**" in flat
		assert "**It carries no controller number at all**" in flat


class TestVolcaFM:

	"""Eleven controls that only travel inwards, and a value table that disagrees with itself.

	Its maker says why nothing leaves in one line - there is no MIDI Out jack -
	and its implementation is the first in this corpus that is a plain text file.
	"""

	def test_nothing_leaves_and_the_maker_says_why (self) -> None:
		"""So every control is receive-only and the chart's whole column is crossed."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		assert len(volca.controls) == 11
		assert all(control.direction == "receives" for control in volca.controls.values())
		assert volca.midi.clock == "receives"
		assert volca.midi.transport == "receives"

		said = prose_of("korg", "volca_fm")

		assert "No message is transmitted. (The volca fm is not equipped with a MIDI Out jack.)" \
			in said

		flat = " ".join(said.split())

		assert "**NOTHING LEAVES THIS INSTRUMENT, AND ITS MAKER SAYS WHY IN ONE LINE.**" in flat
		assert "a consumer can stop wondering what this instrument reports: it has nowhere to" \
			" report to" in flat

	def test_its_implementation_is_the_first_text_file_in_the_corpus (self) -> None:
		"""Which is why there is no extraction, no ligature and no coordinate reading here."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])
		url = volca.sources["implementation"].url

		assert url is not None and url.endswith(".txt")

		# **AND IT IS STILL THE FIRST**, which is the claim its account makes. It was the only
		# one until rank 107, when `korg/volca_keys` arrived with the same arrangement from the
		# same maker - so the list is asserted whole rather than as a count, and a third will
		# show up here rather than passing unnoticed.
		elsewhere = [name for name in pymidiinstrumentdefs.available([CORPUS])
			for source in pymidiinstrumentdefs.load(name, [CORPUS]).sources.values()
			if source.kind == "implementation" and (source.url or "").endswith(".txt")]

		assert elsewhere == ["korg/volca_fm", "korg/volca_keys"]

		# **`First` here means first into this corpus, not first published** - and the two run
		# opposite ways, which is why it is worth saying. The volca keys' implementation is from
		# 2013 and this one from 2016; the volca fm was written at rank 102 and the keys at 107.
		keys = pymidiinstrumentdefs.load("korg/volca_keys", [CORPUS])

		assert str(keys.sources["implementation"].dated) < str(volca.sources["implementation"].dated)

		flat = " ".join(prose_of("korg", "volca_fm").split())

		assert "**ITS IMPLEMENTATION IS A TEXT FILE, WHICH IS THE FIRST IN THIS CORPUS.**" in flat

	def test_one_value_table_is_carried_and_one_is_not (self) -> None:
		"""Because one column is coherent and the other table has neither."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		# ARP DIV's decimals partition 0 to 127 exactly, so they are carried.
		bands = volca.controls["arp_div"].values

		assert bands == {"one_twelfth": 0, "one_eighth": 12, "one_quarter": 24, "one_third": 36,
			"one_half": 47, "two_thirds": 59, "one": 70, "three_halves": 82, "two": 94,
			"three": 105, "four": 117}

		# **AND ARP TYPE CARRIES NOTHING**, because no reading of its table is a partition.
		assert not volca.controls["arp_type"].values
		assert not volca.controls["arp_type"].choices

		flat = " ".join(prose_of("korg", "volca_fm").split())

		assert "**ARP DIV's decimal column is coherent and its hexadecimal has two typos.**" in flat
		assert "**ARP TYPE's columns are both incoherent, so neither is carried.**" in flat
		assert "**the decimal column overlaps itself**: the ninth row ends at 115 and the tenth" \
			" begins at 104" in flat

		# The ten names are recorded even though the numbers are not.
		assert "`OFF`, `RISE1`, `RISE2`, `RISE3`, `FALL1`, `FALL2`, `FALL3`, `RAND1`, `RAND2`," \
			" `RAND3`" in flat

	def test_one_number_means_two_things_and_the_documents_disagree (self) -> None:
		"""So the label is the chart's single row and the rest is written down."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		assert volca.controls["transpose"].cc == 40
		assert volca.controls["transpose"].label == "TRANSPOSE"

		flat = " ".join(prose_of("korg", "volca_fm").split())

		assert "**ONE NUMBER MEANS TWO THINGS AND THE TWO DOCUMENTS DISAGREE ABOUT WHICH IS" \
			" WHICH.**" in flat
		assert "**The manual says the switch turns the slider to semitone units when it is on;" \
			" the implementation gives the on state the narrower span.**" in flat

	def test_its_global_switch_is_on_where_the_nymphes_is_off (self) -> None:
		"""The same kind of switch, set the other way, two ranks apart."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		said = prose_of("korg", "volca_fm")

		assert "Received when global parameter MIDI RX ShortMessage is set to ON." in said

		flat = " ".join(said.split())

		assert "**Which is the opposite of `dreadbox/nymphes` at rank 99**" in flat

		# The sibling that is set the other way, so the pair is assertable.
		assert "CC : In = OFF, out=OFF" in prose_of("dreadbox", "nymphes")

	def test_a_korg_that_accepts_a_yamaha_dump (self) -> None:
		"""And publishes the other maker's format to go with it."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		assert volca.midi.sysex is True

		said = prose_of("korg", "volca_fm")

		assert "Received only YAMAHA DX7 bulk data." in said

		flat = " ".join(said.split())

		assert "**ITS SYSTEM EXCLUSIVE IS ANOTHER MAKER'S.**" in flat
		assert "which is the only instrument here to do so" in flat

	def test_three_voices_and_a_velocity_it_does_not_use (self) -> None:
		"""With a controller for velocity instead of the byte it ignores."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		assert volca.voice is not None
		assert volca.voice.polyphony == 3
		assert volca.voice.voicing_modes == (1, 3)
		assert volca.voice.velocity is not None
		assert volca.voice.velocity.note_on == "ignored"
		assert volca.voice.aftertouch == "none"
		assert volca.voice.pitch_bend is None

		said = prose_of("korg", "volca_fm")

		assert "Velocity is not used." in said
		assert "This digital synthesizer uses a 3-voice, 6-operator FM (Frequency Modulation)" \
			" sound engine." in said

		flat = " ".join(said.split())

		assert "**And there is a controller for velocity instead**: number 41" in flat

	def test_what_its_firmware_changed_is_not_published (self) -> None:
		"""Instructions, not notes - and the MIDI documents are three years older."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		assert volca.model.firmware == "1.07"
		assert str(volca.sources["implementation"].dated) == "2016-04-07"
		assert str(volca.sources["firmware_update"].dated) == "2019-08-20"

		flat = " ".join(prose_of("korg", "volca_fm").split())

		assert "**1.07, AND WHAT IT CHANGED IS NOT PUBLISHED.**" in flat
		assert "so whether three years changed anything below is a thing nobody has said" in flat
		assert "**The firmware arrives as two WAV files played into the SYNC IN jack**" in flat

	def test_the_parameter_list_is_a_picture_and_carries_no_number (self) -> None:
		"""Opened because its name is where two Rolands put opposite things."""
		volca = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		assert "parameter_list" in volca.sources
		assert volca.sources["parameter_list"].pictured_pages == ()

		flat = " ".join(prose_of("korg", "volca_fm").split())

		assert "**no text layer at all** - 1,888 and 615 vector drawings between them" in flat
		assert "**not one controller number**" in flat

		# The two that made it worth opening, both in this corpus.
		assert "`roland/jd_xi` at rank 94 found nothing and `roland/jupiter_x` at 96 found a" \
			" whole second map" in flat


class TestTB3:

	"""The first definition here whose controller numbers a second document confirms.

	Roland publishes three documents for the TB-3 and two of them are about MIDI
	and nothing else.  The chart gives all thirteen controller numbers.  The
	six-sheet MIDI Implementation is a system-exclusive document with no
	controller table at all - and its ``Controller`` address block names seven of
	those same numbers beside the addresses that reach the same parameters.

	**All seven agree**, which is why this class asserts them one by one: the
	usual trouble with a number published twice is that the two disagree, and
	#4243's rule would then make this definition carry neither.
	"""

	def test_thirteen_controls_and_the_bank_select_row_is_not_one (self) -> None:
		"""Fourteen rows on the chart, and the first is addressing machinery."""
		tb_3 = pymidiinstrumentdefs.load("roland/tb_3", [CORPUS])
		numbers = sorted(control.cc for control in tb_3.controls.values()
			if control.cc is not None)

		assert len(tb_3.controls) == 13
		assert numbers == [1, 11, 12, 13, 16, 17, 68, 69, 71, 74, 102, 103, 104]

		# The row the Fantom ruling sets aside: `0, 32` against "CC#0: Bank Number, CC#32: 0".
		assert 0 not in numbers and 32 not in numbers

	def test_seven_numbers_are_confirmed_by_the_system_exclusive_document (self) -> None:
		"""The second document reaches the same parameters and prints their numbers."""
		tb_3 = pymidiinstrumentdefs.load("roland/tb_3", [CORPUS])
		by_number = {control.cc: control for control in tb_3.controls.values()}

		confirmed = {74: "CUTOFF", 71: "RESONANCE", 16: "ACCENT", 17: "EFFECT",
			12: "(ENV MOD) PAD X", 13: "(ENV MOD) PAD Y", 104: "TUNING"}

		for cc, label in confirmed.items():
			assert by_number[cc].label == label

		# And the account says so, naming each as the second document prints it.
		flat = " ".join((tb_3.source or "").split())

		for quoted in ("CUTOFF (CC# 74)", "RESONANCE (CC# 71)", "ACCENT (CC# 16)",
				"EFFECT (CC# 17)", "ENV MOD X (CC# 12)", "ENV MOD Y (CC# 13)",
				"TUNING (CC# 104)"):
			assert quoted in flat

	def test_the_two_scatter_controls_are_received_and_never_sent (self) -> None:
		"""The same two numbers the TR-8 refuses to transmit, for the same two parameters."""
		tb_3 = pymidiinstrumentdefs.load("roland/tb_3", [CORPUS])
		receives = sorted(control.cc for control in tb_3.controls.values()
			if control.direction == "receives" and control.cc is not None)

		assert receives == [68, 69]

		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])
		tr_8_receives = sorted(control.cc for control in tr_8.controls.values()
			if control.direction == "receives" and control.cc is not None)

		# **THE TR-8 REFUSES A THIRD, WHICH THE TB-3 HAS NO ROW FOR**, so this is the same
		# habit and not the same list.
		assert tr_8_receives == [68, 69, 70]

	def test_the_pad_leaves_by_three_different_routes (self) -> None:
		"""X as pitch bend, Y as a controller, and pressure as another controller."""
		tb_3 = pymidiinstrumentdefs.load("roland/tb_3", [CORPUS])

		assert tb_3.controls["pad_z"].cc == 1
		assert tb_3.controls["xy_play_pad_y"].cc == 11

		# **AND THAT IS WHY AFTERTOUCH IS NONE WHILE THE MANUAL NAMES AFTERTOUCH.** The
		# chart crosses both kinds in both directions; the manual has a "Pad Aftertouch
		# Sensitivity" setting. Pad pressure travels as controller 1, so both are true.
		assert tb_3.voice.aftertouch == "none"
		assert "pad pressure leaves this instrument as controller 1" in \
			" ".join((tb_3.source or "").split()).lower()

	def test_it_answers_to_two_more_octaves_than_it_plays (self) -> None:
		"""The one row on this chart where the two columns differ by more than a mark."""
		tb_3 = pymidiinstrumentdefs.load("roland/tb_3", [CORPUS])

		assert tb_3.voice.note_range == (12, 108)

		flat = " ".join((tb_3.source or "").split())

		assert "IT ANSWERS TO TWO MORE OCTAVES THAN IT PLAYS" in flat
		assert "`12-84` transmitted against `12-108` in the `Recognized` column" in flat

	def test_it_ships_on_channel_two_and_says_so_twice (self) -> None:
		"""Both documents give the default, and an omni TB-3 still transmits on it."""
		tb_3 = pymidiinstrumentdefs.load("roland/tb_3", [CORPUS])

		assert tb_3.midi.channels == (1, 16)
		assert tb_3.midi.mode == 4
		assert tb_3.midi.sysex is True
		assert tb_3.midi.program_change is not None
		assert tb_3.midi.program_change.receives is True
		assert tb_3.midi.program_change.sends is False

	def test_the_pitch_bend_block_is_left_out_although_it_has_pitch_bend (self) -> None:
		"""Marked in both columns, with no depth published - so neither field can be filled."""
		tb_3 = pymidiinstrumentdefs.load("roland/tb_3", [CORPUS])

		assert tb_3.voice.pitch_bend is None

		# `roland/tr_8` leaves the same block out for the opposite reason, and this file says so.
		flat = " ".join((tb_3.source or "").split())

		assert "the `pitch_bend` block is left out entirely" in flat
		assert "`roland/tr_8` leaves it out for the opposite reason" in flat


class TestSH4D:

	"""Three whole implementation charts, and only one of them has any control change.

	`roland/ju_06a` at rank 87 and `korg/drumlogue` at 93 each met a maker
	printing two maps where only one is in force at a time, and the ruling was
	to carry the default.  **This instrument needs the opposite treatment**: its
	three charts describe three kinds of destination inside one machine - four
	tone parts, one rhythm part, and the control channel - and all three hold at
	once.

	So the thirty-two controls are the tone parts' controls, and that is a fact
	a single-chart definition could not have stated.
	"""

	def test_thirty_two_controls_and_four_of_them_cannot_be_sent (self) -> None:
		"""The four crossed transmitted are the four with no panel control."""
		sh_4d = pymidiinstrumentdefs.load("roland/sh_4d", [CORPUS])
		numbers = sorted(control.cc for control in sh_4d.controls.values()
			if control.cc is not None)

		assert len(sh_4d.controls) == 32
		assert numbers == [1, 7, 10, 16, 18, 19, 20, 21, 28, 29, 31, 64, 65, 66, 71, 72, 73,
			74, 75, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 90]

		receives = sorted(control.cc for control in sh_4d.controls.values()
			if control.direction == "receives" and control.cc is not None)

		assert receives == [64, 65, 66, 84]

		# All four are standard MIDI assignments rather than this maker's parameters.
		assert sh_4d.controls["hold_pedal"].label == "Hold Pedal"
		assert sh_4d.controls["sostenuto"].label == "Sostenuto"
		assert sh_4d.controls["portamento_control"].label == "Portamento Control"

	def test_twelve_rows_carry_the_number_the_standard_gives_them (self) -> None:
		"""The cheapest check that the chart's rows were paired with the right names.

		The chart gives numbers in one column and names in another, so an off-by-one
		pairing is the error to fear.  Twelve of the thirty-two are numbers the MIDI
		standard itself assigns, and all twelve carry a name that matches - which no
		shifted reading could manage.
		"""
		sh_4d = pymidiinstrumentdefs.load("roland/sh_4d", [CORPUS])
		by_number = {control.cc: control.label for control in sh_4d.controls.values()}

		standard = {1: "Modulation", 7: "LEVEL", 10: "PAN", 64: "Hold", 65: "Porta",
			66: "Sostenuto", 71: "RESONANCE", 72: "RELEASE", 73: "ATTACK", 74: "CUTOFF",
			75: "DECAY", 84: "Portamento"}

		for cc, word in standard.items():
			assert word.lower() in by_number[cc].lower()

	def test_five_parts_each_on_a_channel_of_its_own_choosing (self) -> None:
		"""Four tone parts and one rhythm part, which is what the specification counts."""
		sh_4d = pymidiinstrumentdefs.load("roland/sh_4d", [CORPUS])

		assert sorted(sh_4d.parts) == ["rhythm", "tone"]
		assert sh_4d.parts["tone"].count == 4
		assert sh_4d.parts["rhythm"].count == 1
		assert sh_4d.parts["tone"].channel == "assigned"
		assert sh_4d.parts["rhythm"].channel == "assigned"

		# Sixty voices, shared, with a per-part reserve.
		assert sh_4d.voice.polyphony == 60
		assert sh_4d.voice.polyphony_shared is True

	def test_the_account_says_only_one_of_three_charts_has_control_change (self) -> None:
		"""Because every control here belongs to a tone part and the rhythm part has none."""
		flat = " ".join(
			(pymidiinstrumentdefs.load("roland/sh_4d", [CORPUS]).source or "").split())

		assert "THREE WHOLE CHARTS, IN FORCE AT THE SAME TIME" in flat
		assert "Only the first has any control change" in flat

		# And each chart is cited at the sheet it begins on.
		for quoted in ('"MIDI implementation chart (Tone)" (manual p. 240)',
				'"MIDI implementation chart (Rhythm)" (manual p. 241)',
				'"MIDI implementation chart (SYSTEM)" (manual p. 242)'):
			assert quoted in flat

	def test_this_makers_mode_divides_by_what_the_instrument_is (self) -> None:
		"""Mode 3 for the polyphonic Rolands, Mode 4 for the drum machines.

		Asserted because the first reading of this file claimed the SH-4d was the
		first Roland here to say Mode 3, and it is the seventh.  The real pattern is
		more useful than the wrong claim was: **of the Rolands that declare a mode,
		the polyphonic and multitimbral ones say 3 and the drum machines say 4** -
		and `roland/tb_3` sits with the drum machines while being a monophonic bass
		line, which is the one that does not follow from the instrument.

		**And `roland/tr_08` broke it from the other side**: a drum machine, a
		Boutique, whose chart says Mode 3 in both columns. So the pattern is the
		TR-8's, the TR-8S's and the TR-6S's rather than drum machines', and the
		next Roland is worth reading before assuming either.

		The JD-800 of 1991 is the oldest Roland here to declare one, and it says Mode 3
		as a polyphonic synthesizer, with Mode 4 recognised for its solo key.
		Its Boutique recreation, the JD-08, says Mode 3 on both of its charts, and so
		does the JX-08 - though the JX-8P it recreates gives two defaults, Mode 1 and
		3, so `roland/jx_8p` records none.
		"""
		modes = {}

		for name in pymidiinstrumentdefs.available([CORPUS]):
			if name.startswith("roland/"):
				modes[name] = pymidiinstrumentdefs.load(name, [CORPUS]).midi.mode

		assert modes["roland/sh_4d"] == 3

		three = sorted(name for name, mode in modes.items() if mode == 3)
		four = sorted(name for name, mode in modes.items() if mode == 4)

		assert three == ["roland/fantom_6_7_8", "roland/jd_08", "roland/jd_800", "roland/jd_xi",
			"roland/ju_06a", "roland/jx_08", "roland/mc_101", "roland/mc_707", "roland/p_6", "roland/s_1",
			"roland/sh_4d", "roland/tr_08"]
		assert four == ["roland/tb_3", "roland/tr8s", "roland/tr_6s", "roland/tr_8"]

		# Three of the four are drum machines; the TB-3 is the exception worth knowing.
		assert pymidiinstrumentdefs.load("roland/sh_4d", [CORPUS]).midi.sysex is False

	def test_the_bend_range_was_nearly_recorded_as_absent (self) -> None:
		"""This maker writes `BendRange` as one word, so an exact search finds nothing.

		The absence sweep squashes the text to letters and digits, and that is what
		found it.  Had it not, this definition would have shipped saying the
		instrument publishes no bend range, which is false.
		"""
		sh_4d = pymidiinstrumentdefs.load("roland/sh_4d", [CORPUS])

		assert sh_4d.voice.pitch_bend is not None
		assert sh_4d.voice.pitch_bend.programmable is True

		# No figure is carried, because 0-48 is the setting's range and not a value in force.
		assert sh_4d.voice.pitch_bend.semitones is None

		flat = " ".join((sh_4d.source or "").split())

		assert "BECAUSE THIS MAKER WRITES IT AS ONE WORD" in flat
		assert "an absence has to be swept for with the text squashed" in flat

	def test_the_sound_list_its_footnotes_name_is_not_published (self) -> None:
		"""The bank numbers are published and what they select is not."""
		flat = " ".join(
			(pymidiinstrumentdefs.load("roland/sh_4d", [CORPUS]).source or "").split())

		assert "THE BANK NUMBERS ARE PUBLISHED AND WHAT THEY SELECT IS NOT." in flat
		assert '"*3 See Sound List" (manual p. 241)' in flat

		# The same shape as the TR-909's unpublished leaflet, and this file says so.
		assert "roland/tr_909" in flat


class TestVolcaSample:

	"""A chart whose ticks and crosses are drawings, so the text layer loses the directions.

	`dreadbox/nymphes` met pages that were entirely pictures and declared them
	with ``pictured_pages``.  This is narrower and worse: the page extracts
	perfectly - row labels, controller numbers, remarks - and is silently missing
	the only column that says which way anything travels.

	The marks were read as shapes against the chart's own printed key, and then
	the table was rendered and looked at.
	"""

	def test_eleven_controls_and_every_one_of_them_only_receives (self) -> None:
		"""29 crosses stand in the Transmitted column of that chart and not one circle."""
		volca = pymidiinstrumentdefs.load("korg/volca_sample", [CORPUS])
		numbers = sorted(control.cc for control in volca.controls.values()
			if control.cc is not None)

		assert len(volca.controls) == 11
		assert numbers == [7, 10, 40, 41, 42, 43, 44, 45, 46, 47, 48]
		assert {control.direction for control in volca.controls.values()} == {"receives"}

	def test_ten_parts_on_ten_channels_with_no_note_map (self) -> None:
		"""One part with ten instances, which is how the volca drum records its six."""
		volca = pymidiinstrumentdefs.load("korg/volca_sample", [CORPUS])

		assert list(volca.parts) == ["part"]
		assert volca.parts["part"].count == 10
		assert volca.parts["part"].channel_offset == 0
		assert volca.parts["part"].addressing == "none"
		assert volca.voice.addressing == "none"

		# Ten parts over eight notes, so they cannot all sound at once.
		assert volca.voice.polyphony == 8
		assert volca.voice.polyphony_shared is True

	def test_the_velocity_cross_is_readable_because_its_siblings_differ (self) -> None:
		"""The same chart row is a circle on one sibling and a cross on another.

		That is what makes the cross readable as a statement rather than as
		decoration, and it is settled out of this maker's own charts rather than
		borrowed from a sibling's reading.
		"""
		volca = pymidiinstrumentdefs.load("korg/volca_sample", [CORPUS])
		drum = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])
		fm = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		assert volca.voice.velocity is not None
		assert volca.voice.velocity.note_on == "ignored"
		assert fm.voice.velocity is not None
		assert fm.voice.velocity.note_on == "ignored"

		# **AND THE ONE THAT DIFFERS**, which is the whole argument.
		assert drum.voice.velocity is not None
		assert drum.voice.velocity.note_on == "received"

	def test_the_three_volcas_do_not_answer_alike (self) -> None:
		"""Checked rather than inherited, because this maker's habits have not held.

		Rank 102 found Korg's arrangements differing across the volcas, and the
		standing rule is that two instruments by one maker are not a habit.  These
		three disagree about velocity, about program change and about pitch bend.
		"""
		volca = pymidiinstrumentdefs.load("korg/volca_sample", [CORPUS])
		drum = pymidiinstrumentdefs.load("korg/volca_drum", [CORPUS])
		fm = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		# Program change: the drum answers to one, this does not.
		assert volca.midi.program_change is not None
		assert volca.midi.program_change.receives is False
		assert drum.midi.program_change is not None
		assert drum.midi.program_change.receives is True

		# Pitch bend: the fm is marked as answering to it, this one is crossed.
		assert volca.voice.pitch_bend is None
		assert drum.voice.pitch_bend is None

		# What all three share: nothing leaves them.
		for one in (volca, drum, fm):
			directions = {control.direction for control in one.controls.values()}

			assert directions == {"receives"}

	def test_the_chart_is_older_than_the_firmware_and_one_row_is_doubted (self) -> None:
		"""A 2019 release note fixes a message the 2014 chart crosses in both columns."""
		volca = pymidiinstrumentdefs.load("korg/volca_sample", [CORPUS])
		flat = " ".join((volca.source or "").split())

		assert volca.model.firmware == "1.42"
		assert '"Fixed MIDI Song Position Pointer." (updater)' in flat
		assert "enough to doubt a row and not enough" in flat

		# The chart's own edition is recorded as what it is, five years earlier.
		assert volca.sources["chart"].edition == "1.00"
		assert volca.sources["updater"].edition == "1.42"

	def test_the_survey_pointed_at_the_other_machine (self) -> None:
		"""Product 867 is the volca sample2; this instrument is product 370."""
		volca = pymidiinstrumentdefs.load("korg/volca_sample", [CORPUS])

		for source in volca.sources.values():
			assert "/867/" not in (source.landing or "")
			assert "/867/" not in (source.url or "")

		assert any("/370/" in (source.landing or "") for source in volca.sources.values())


class TestMicroBrute:

	"""The controller table is in a document the maker does not publish.

	Fifty sheets of user manual print no controller number at all.  All
	thirteen are on one sheet of the *MicroBrute Connection* manual, which is
	not on the downloads page: it ships inside the Connection software archive,
	and the only reason to look there is a sentence on the manual's sheet 48.

	The archive's executable was not run.  Reading a document out of an archive
	is not installing a maker's software.
	"""

	def test_thirteen_controls_none_of_which_is_a_knob (self) -> None:
		"""102 to 114, every one of them a setting of the editor rather than a panel control."""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])
		numbers = sorted(control.cc for control in brute.controls.values()
			if control.cc is not None)

		assert len(brute.controls) == 13
		assert numbers == [102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]

		# Nothing leaves by the socket, because there is only one and it is an input.
		assert {control.direction for control in brute.controls.values()} == {"receives"}

		# **And not one of them is the front panel.** An analogue monosynth's knobs answer to
		# nothing, so a consumer looking for a cutoff here will not find one.
		labels = " ".join(control.label.lower() for control in brute.controls.values())

		for knob in ("cutoff", "resonance", "attack", "decay", "sustain", "release",
				"glide", "metalizer", "ultrasaw"):
			assert knob not in labels

	def test_the_two_rows_of_that_table_that_are_not_controls (self) -> None:
		"""Fifteen rows, thirteen controls: an RPN and a channel mode message.

		The pitch bend range is reached by ``RPN 06`` and so belongs under
		``voice.pitch_bend``; ``Local ON/OFF`` is controller 122, which this
		library's validator refuses by the ruling `roland/fantom_6_7_8` set.
		"""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])

		assert brute.voice.pitch_bend is not None
		assert brute.voice.pitch_bend.semitones == 2
		assert brute.voice.pitch_bend.programmable is True

		assert 122 not in {control.cc for control in brute.controls.values()}

		# **Refused by name, not merely left out.** Adding it back is an error.
		body = ("definition: 1\nmodel: {name: X}\n"
			"controls: {local: {label: Local ON/OFF, cc: 122}}\n")

		with pytest.raises(pymidiinstrumentdefs.DefinitionError) as raised:
			pymidiinstrumentdefs.parse(body, source = "x.yaml")

		assert "channel mode message" in str(raised.value)

	def test_velocity_is_sent_and_not_received_which_the_format_cannot_say (self) -> None:
		"""``note_on`` has four values and this instrument is none of them.

		It transmits velocity over USB and does not recognise it.  ``ignored`` is
		the true half; the half with no field is written into the account, so the
		fact is not lost even though nothing can switch on it.
		"""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])
		flat = " ".join((brute.source or "").split())

		assert brute.voice.velocity is not None
		assert brute.voice.velocity.note_on == "ignored"

		# Two documents say it, and the account quotes the plainer one.
		assert ("The MicroBrute does not receive or respond to velocity but it does send it."
			in flat)
		assert "it transmits and does not recognise" in flat

		# **And it carries a parameter governing something it will never hear**: the curve of
		# the velocity it sends.
		assert brute.controls["velocity_curve"].cc == 112

	def test_monophonic_although_one_sentence_says_fully_polyphonic (self) -> None:
		"""The polyphonic sentence is about the keyboard sending chords elsewhere.

		"The keyboard can also be used as a fully polyphonic MIDI controller for
		other devices via the rear panel USB jack."  What the instrument *sounds*
		is settled by the note-priority paragraph instead: one of two notes.
		"""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])
		flat = " ".join((brute.source or "").split())

		assert brute.voice.polyphony == 1
		assert "fully polyphonic MIDI controller" in flat
		assert "One of two notes is one note." in flat

		# The behaviour it rests on is a control as well as a sentence.
		assert brute.controls["note_priority"].cc == 111
		assert set(brute.controls["note_priority"].values) == {"last", "low", "high"}

	def test_every_absence_is_absent_rather_than_guessed (self) -> None:
		"""Six fields are unset because sixty-five sheets never raise them.

		An unset field says nobody has established it, which is a different
		claim from ``none`` and from ``false``.  `korg/volca_sample` could say
		``program_change: {receives: false}`` because a chart crossed the box;
		nothing here crosses anything.
		"""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])

		assert brute.midi.mode is None
		assert brute.midi.transport is None
		assert brute.midi.program_change is None
		assert brute.midi.sysex is None
		assert brute.voice.aftertouch is None
		assert brute.voice.note_range is None

		# What *is* established, over either socket.
		assert brute.midi.clock == "receives"
		assert brute.midi.channels == (1, 16)

	def test_the_transport_absence_is_the_one_a_counting_sweep_gets_wrong (self) -> None:
		"""`Start` occurs twenty-nine times across the two documents and never as a message.

		"Quick Start", "start playing notes", "restart", "the LFO will start on
		power up".  A sweep that counted hits would have reported transport as
		documented, which is why the account says the hits were read.
		"""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])
		flat = " ".join((brute.source or "").split())

		assert brute.midi.transport is None
		assert "not once as a MIDI message" in flat
		assert "would have reported transport and bank select as documented here" in flat
		assert "all that is published is that it follows a clock" in flat

	def test_the_channel_settings_are_exact_and_the_rest_are_banded (self) -> None:
		"""Two shapes in one table, because the maker prints two kinds of value.

		``1 to 16, 17=All`` means those numbers exactly; ``0 to 41 = Reset``
		means a band whose low end is what this format records.
		"""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])

		receive = brute.controls["receive_channel"]
		assert receive.choices["channel_1"] == 1
		assert receive.choices["all"] == 17
		assert receive.range == (1, 17)
		assert not receive.values

		# Send Channel has no omni setting, which is the asymmetry the table shows.
		send = brute.controls["send_channel"]
		assert "all" not in send.choices
		assert send.range == (1, 16)

		# The other eleven are bands.
		for name, control in brute.controls.items():
			if name in ("receive_channel", "send_channel"):
				continue

			assert control.values, f"{name} should be banded"
			assert not control.choices, f"{name} should not be exact"

		assert brute.controls["seq_retrig"].values == {"reset": 0, "legato": 42, "none": 84}

	def test_a_document_on_an_instruments_page_is_not_about_that_instrument (self) -> None:
		"""The MIDI Control Center manual sits on this page and never names this instrument.

		`arturia/drumbrute_impact` cites it legitimately.  This definition cannot,
		and the reason is in the library beside the file rather than only here.
		"""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		assert "mcc_manual" in impact.sources
		assert not any("mcc" in key for key in brute.sources)

		# This instrument's editor document is the 2013 one, and its address is an archive.
		assert (brute.sources["connection"].url or "").endswith("MicroBrute_1_0_3_2_win.zip")
		assert brute.sources["connection"].edition == "1.0.3"

	def test_the_seven_arturias_do_not_answer_alike (self) -> None:
		"""The largest single-maker group here, and the standing rule still holds.

		Two instruments by one maker are not a habit.  These seven disagree about
		how many controls they have, about velocity, and about whether the panel
		is addressable at all.
		"""
		names = ["arturia/astrolab", "arturia/drumbrute_impact", "arturia/microbrute",
			"arturia/microfreak", "arturia/minifreak", "arturia/polybrute",
			"arturia/polybrute_12"]
		loaded = {name: pymidiinstrumentdefs.load(name, [CORPUS]) for name in names}

		counts = {name: len(one.controls) for name, one in loaded.items()}

		# **No two of the seven carry the same number of controls.**
		assert counts == {
			"arturia/astrolab": 36,
			"arturia/drumbrute_impact": 0,
			"arturia/microbrute": 13,
			"arturia/microfreak": 21,
			"arturia/minifreak": 42,
			"arturia/polybrute": 74,
			"arturia/polybrute_12": 75,
		}

		# And none of the others omits a mode either, which is this maker's one constant.
		assert all(one.midi.mode is None for one in loaded.values())

	def test_the_firmware_is_four_versions_past_the_documented_one (self) -> None:
		"""The controller table describes 1.0.3.2 and Arturia serves 1.0.4.114.

		The only release note this instrument has is the first one, and it says
		nothing about MIDI.  So the span between them is undocumented, which the
		account states rather than papering over.
		"""
		brute = pymidiinstrumentdefs.load("arturia/microbrute", [CORPUS])

		assert brute.model.firmware == "1.0.4.114"
		assert brute.sources["connection"].edition == "1.0.3"
		assert brute.sources["release_note"].dated == "2013-11-08"

		# The span nobody has spoken for is stated in the account, which ships.
		flat = " ".join((brute.source or "").split())

		assert brute.sources["connection"].dated == "2013-11-12"
		assert "publishes no release notes at all" in flat
		assert "whether those four years changed any of these numbers is a thing nobody has said" \
			in flat


class TestVolcaKeys:

	"""A second chart whose marks are artwork, and a row a sibling could not settle.

	`korg/volca_sample` met a release note reading "Fixed MIDI Song Position
	Pointer." against a chart that crossed song position in both columns, and
	could only record the doubt.  This instrument has the same release note,
	dated the same day - and here the chart circles the row and the
	implementation lays the message out.
	"""

	def test_sixteen_controls_and_every_one_of_them_only_receives (self) -> None:
		"""34 crosses stand in the chart's Transmitted column and not one circle."""
		volca = pymidiinstrumentdefs.load("korg/volca_keys", [CORPUS])
		numbers = sorted(control.cc for control in volca.controls.values()
			if control.cc is not None)

		assert len(volca.controls) == 16
		assert numbers == [5, 11, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53]
		assert {control.direction for control in volca.controls.values()} == {"receives"}

	def test_the_song_position_row_this_definition_can_settle (self) -> None:
		"""Three documents agree where the volca sample's two could not.

		Both instruments took the same firmware fix on the same day.  The
		difference is what their charts say: this one circles the row.
		"""
		keys = pymidiinstrumentdefs.load("korg/volca_keys", [CORPUS])
		sample = pymidiinstrumentdefs.load("korg/volca_sample", [CORPUS])
		flat = " ".join((keys.source or "").split())

		assert keys.midi.transport == "receives"
		assert '"pppp : 0~15 = STEP 1 ~ STEP 16" (implementation)' in flat
		assert "recorded the doubt rather than resolving it" in flat

		# The sibling it corrects is still carrying its own doubt, deliberately.
		assert "enough to doubt a row and not enough" in " ".join((sample.source or "").split())

	def test_the_two_documents_disagree_about_two_footnotes_so_neither_gate_is_kept (self) -> None:
		"""The chart gates pitch bend and song position; the implementation gates neither.

		They agree the messages are answered to, so nothing is in doubt - but a
		gate that two documents describe differently is a gate this corpus does
		not record.
		"""
		volca = pymidiinstrumentdefs.load("korg/volca_keys", [CORPUS])
		flat = " ".join((volca.source or "").split())

		assert "Both say the messages are answered to and they cannot both be right about when" \
			in flat
		assert "neither account is carried" in flat

		# Pitch bend is answered to and no range is published, so the block is absent.
		assert volca.voice.pitch_bend is None
		assert "it is answered to and cannot say how far" in flat

	def test_the_controller_with_no_knob_is_in_no_group (self) -> None:
		"""Expression exists only as a message, so it belongs to no panel section.

		"Cannot be changed with machine operations; can only be changed with
		MIDI." is the chart's own footnote on it.
		"""
		volca = pymidiinstrumentdefs.load("korg/volca_keys", [CORPUS])

		assert volca.controls["expression"].cc == 11
		assert volca.controls["expression"].group is None

		# And it is the only one, the other fifteen sitting in the manual's five sections.
		ungrouped = [name for name, control in volca.controls.items() if control.group is None]
		assert ungrouped == ["expression"]
		assert sorted(volca.groups) == ["delay", "eg", "lfo", "vcf", "vco"]

	def test_the_five_volcas_still_do_not_answer_alike (self) -> None:
		"""Five now, and the maker rule has never held across them.

		Checked rather than inherited, which is the standing rule: these five
		disagree about velocity, about system exclusive, about program change,
		about the channel span and about polyphony.
		"""
		names = ["korg/volca_bass", "korg/volca_drum", "korg/volca_fm", "korg/volca_keys",
			"korg/volca_sample"]
		loaded = {name: pymidiinstrumentdefs.load(name, [CORPUS]) for name in names}

		# Velocity: three answers across five instruments.
		velocities = {name: one.voice.velocity.note_on if one.voice.velocity else None
			for name, one in loaded.items()}
		assert velocities == {
			"korg/volca_bass": "received",
			"korg/volca_drum": "received",
			"korg/volca_fm": "ignored",
			"korg/volca_keys": "received",
			"korg/volca_sample": "ignored",
		}

		# System exclusive: the two with a text implementation disagree about it.
		assert loaded["korg/volca_fm"].midi.sysex is True
		assert loaded["korg/volca_keys"].midi.sysex is False

		# What all five share: nothing leaves any of them.
		for one in loaded.values():
			assert {control.direction for control in one.controls.values()} == {"receives"}

	def test_both_gates_are_open_when_the_instrument_arrives (self) -> None:
		"""Two global parameters stand between MIDI and this instrument, and both default on.

		Which is the opposite of `dreadbox/nymphes`, whose controls are off until
		somebody turns them on - the same kind of switch, set the other way.
		"""
		volca = pymidiinstrumentdefs.load("korg/volca_keys", [CORPUS])
		nymphes = pymidiinstrumentdefs.load("dreadbox/nymphes", [CORPUS])
		flat = " ".join((volca.source or "").split())

		assert "MIDI RX ShortMessage is set to ON" in flat
		assert "marks the factory setting with an asterisk: `*On`" in flat
		assert "opposite of `dreadbox/nymphes`" in flat

		assert len(nymphes.controls) == 82

	def test_six_voice_modes_over_two_counts (self) -> None:
		"""One controller's bands are the whole voicing story, as on the volca fm."""
		volca = pymidiinstrumentdefs.load("korg/volca_keys", [CORPUS])
		fm = pymidiinstrumentdefs.load("korg/volca_fm", [CORPUS])

		assert list(volca.controls["voice_mode"].values) == ["poly", "unison", "octave",
			"fifth", "unison_ring", "poly_ring"]
		assert volca.voice.polyphony == 3
		assert volca.voice.voicing_modes == (1, 3)

		# The same pair, reached from a different document.
		assert fm.voice.voicing_modes == (1, 3)
		assert fm.voice.polyphony == 3

	def test_the_manual_contradicts_itself_about_its_own_table (self) -> None:
		"""Firmware 1.03 added an eighth global parameter and only the table was updated.

		The release note asked for the manuals to be downloaded again, and they
		were changed - in one of the two places that needed it.
		"""
		volca = pymidiinstrumentdefs.load("korg/volca_keys", [CORPUS])
		flat = " ".join((volca.source or "").split())

		assert volca.model.firmware == "1.03"
		assert ("\"Press a keyboard button 1-7 to specify the setting for the global parameter.\" (manual" in flat)
		assert "the table is right and the sentence above it is not" in flat


class TestArtemis:

	"""The survey named the wrong document, and the right one is a chapter of the manual.

	#2507 points at `CC List v1.1.0`, a standalone PDF.  The user's manual at
	v1.2.0 carries the same list as its chapter 017 - with one controller the
	standalone list has not got and four rows it disagrees about.  The firmware
	is 1.2.0, so the named document is the superseded one.
	"""

	def test_eighty_four_controls_and_every_one_of_them_only_receives (self) -> None:
		"""The instrument has a MIDI out and every MIDI switch it offers receives."""
		artemis = pymidiinstrumentdefs.load("dreadbox/artemis", [CORPUS])
		numbers = sorted(control.cc for control in artemis.controls.values()
			if control.cc is not None)

		assert len(artemis.controls) == 84
		assert numbers[0] == 1 and numbers[-1] == 96
		assert {control.direction for control in artemis.controls.values()} == {"receives"}

		# The three rows of the maker's list that are not controls.
		assert 0 not in numbers, "bank select is addressing machinery"
		assert 120 not in numbers and 123 not in numbers, "120 and 123 are channel mode"

	def test_the_survey_named_the_superseded_document (self) -> None:
		"""Both lists are cited, and the account says which one the numbers came from."""
		artemis = pymidiinstrumentdefs.load("dreadbox/artemis", [CORPUS])
		flat = " ".join((artemis.source or "").split())

		assert artemis.sources["manual"].edition == "v1.2.0"
		assert artemis.sources["cc_list"].edition == "v1.1.0"
		assert artemis.model.firmware == "1.2.0"

		# The one controller the standalone list has not got.
		assert artemis.controls["vco_1_tune"].cc == 77
		assert "adds controller 77, `VCO 1 TUNE`, which the standalone list does not have" in flat

		# **And the maker's own badges agree with the diff**, which is why five is five.
		assert "Dreadbox badges exactly those five rows `new`" in flat

	def test_controller_31_changes_what_every_other_controller_means (self) -> None:
		"""A consumer that does not know where 31 stands does not know what it is setting.

		Nothing in this format can express a control that re-points the rest, so
		the account has to - and it is the first of its kind in this corpus.
		"""
		artemis = pymidiinstrumentdefs.load("dreadbox/artemis", [CORPUS])
		flat = " ".join((artemis.source or "").split())

		assert artemis.controls["selector"].cc == 31
		assert artemis.controls["selector"].group == "mod_matrix"

		assert ("\"Use CC 31 (Selector) to choose whether subsequent CC messages adjust a "
			"parameter's base value or its corresponding modulation amount.\" (manual p. 74)"
			in flat)
		assert "you may be setting the cutoff or setting how far an envelope moves it" in flat

		# And the remapping, which makes the same number mean a signed amount.
		assert '"0 → –100", "64 → 0", "127 → +100" (manual p. 74)' in flat

	def test_only_the_switches_carry_values (self) -> None:
		"""No band boundary is printed for anything with three or more states.

		The maker says only that the states are "split in the whole CC range of
		0-127", which is a rule and not a table: thirds can be 0/42/84 or
		0/43/85.  So the thirteen multi-state controls carry no numbers -
		`novation/peak`'s rule, as `korg/volca_fm` applied it.
		"""
		artemis = pymidiinstrumentdefs.load("dreadbox/artemis", [CORPUS])
		banded = {name for name, control in artemis.controls.items() if control.values}

		assert len(banded) == 7
		assert all(len(artemis.controls[name].values) == 2 for name in banded)
		assert artemis.controls["sustain"].values == {"off": 0, "on": 64}

		flat = " ".join((artemis.source or "").split())

		assert "`novation/peak`'s rule as `korg/volca_fm` applied it" in flat
		assert "38 `DISTORTIONS TYPE` (15)" in flat

	def test_receives_is_read_off_the_settings_not_quoted (self) -> None:
		"""It has a MIDI out, and every MIDI switch it offers is a receive switch.

		That is weaker ground than a sentence, so the account says so - and
		`receives` is the safer of the two errors a reader could make.
		"""
		artemis = pymidiinstrumentdefs.load("dreadbox/artemis", [CORPUS])
		flat = " ".join((artemis.source or "").split())

		assert ("\"MIDI IN/OUT MIDI DIN connector for receiving / transmitting MIDI messages "
			"from/to an external MIDI device.\" (manual p. 9)" in flat)
		assert "every MIDI switch it offers is a receive switch" in flat
		assert "the safer of the two errors" in flat

	def test_the_three_dreadboxes_do_not_answer_alike (self) -> None:
		"""Checked rather than inherited, and the direction is where they part.

		Both siblings mark every control `both`; this one marks every control
		`receives`, on the strength of its own global parameters.
		"""
		names = ["dreadbox/artemis", "dreadbox/nymphes", "dreadbox/typhon"]
		loaded = {name: pymidiinstrumentdefs.load(name, [CORPUS]) for name in names}

		assert {c.direction for c in loaded["dreadbox/artemis"].controls.values()} == {"receives"}
		assert {c.direction for c in loaded["dreadbox/nymphes"].controls.values()} == {"both"}
		assert {c.direction for c in loaded["dreadbox/typhon"].controls.values()} == {"both"}

		# And no two carry the same number of controls.
		counts = sorted(len(one.controls) for one in loaded.values())
		assert counts == [82, 84, 98]
		assert len(set(counts)) == 3

	def test_the_manual_contradicts_itself_about_the_mpe_bend_range (self) -> None:
		"""Given twice with two answers, so neither is carried.

		Which is also why `pitch_bend.semitones` is absent: the ordinary wheel is
		settable and nothing says where it starts.
		"""
		artemis = pymidiinstrumentdefs.load("dreadbox/artemis", [CORPUS])
		flat = " ".join((artemis.source or "").split())

		assert artemis.voice.pitch_bend is not None
		assert artemis.voice.pitch_bend.programmable is True
		assert artemis.voice.pitch_bend.semitones is None

		assert "`MPE PITCH WHEEL 0 to 96 semitones` in the global parameter table" in flat
		assert '"Adjusts the range of the Pitch Wheel from 0 to 48 semitones for MPE control."' \
			in flat
		assert "Both cannot be right, so neither is carried" in flat

	def test_five_hundred_and_twelve_presets_stated_and_audited (self) -> None:
		"""The count is printed once and the export arithmetic gives it a second time."""
		artemis = pymidiinstrumentdefs.load("dreadbox/artemis", [CORPUS])
		flat = " ".join((artemis.source or "").split())

		assert artemis.midi.program_change is not None
		assert artemis.midi.program_change.presets == 512
		assert artemis.midi.program_change.receives is True

		# An in-switch and no out-switch, so what it sends is unestablished.
		assert artemis.midi.program_change.sends is None

		assert '"Active preset export will send 2 messages and Bank export will send 65 messages."' \
			in flat
		assert "one identifier and sixty-four presets" in flat

	def test_its_system_exclusive_does_not_travel_down_its_own_din (self) -> None:
		"""Presets and firmware both go by USB only, which the manual says twice."""
		artemis = pymidiinstrumentdefs.load("dreadbox/artemis", [CORPUS])
		flat = " ".join((artemis.source or "").split())

		assert artemis.midi.sysex is True
		assert '"Mind that this only works from the USB connection, not the MIDI DIN."' in flat
		assert "ITS SYSTEM EXCLUSIVE DOES NOT TRAVEL DOWN ITS OWN DIN SOCKET" in flat
		assert "true of one of this instrument's two MIDI connections and not the other" in flat


class TestThirdWave:

	"""A synthesizer with two maps a setting chooses between, from a specification covering three models."""

	# The rows the NRPN table prints and this definition leaves out, each for a reason its own row
	# gives: the part-select bitmap, six deprecated, three wavetable selectors and 24 song steps
	# that pack two numbers into one, three unused, eleven of sequence data, five the desktop's,
	# the one not settable, and two the 8M's.
	NRPN_LEFT_OUT = sorted([0, 48, 51, 52, 53, 54, 75, 102, 103, 104, 345, 346, 347,
		*range(354, 365), *range(371, 395), 424, 425, 426, 427, 428, 444, 458, 459])

	def test_two_maps_and_neither_control_carries_both (self) -> None:
		"""101 by controller from the keyboard's table and 413 by NRPN, never paired."""
		wave = pymidiinstrumentdefs.load("groove_synthesis/third_wave", [CORPUS])

		by_cc = [control for control in wave.controls.values() if control.cc is not None]
		by_nrpn = [control for control in wave.controls.values() if control.nrpn is not None]

		assert len(wave.controls) == 514
		assert len(by_cc) == 101 and len(by_nrpn) == 413
		assert not [control for control in wave.controls.values() if control.cc is not None and control.nrpn is not None]
		assert wave.midi.nrpn == "preferred"

		said = prose_of("groove_synthesis", "third_wave")

		assert "TWO MAPS FOR ONE INSTRUMENT, AND A SETTING CHOOSES WHICH IS LIVE" in said

	def test_every_row_of_both_tables_is_accounted_for (self) -> None:
		"""Four controller rows and 56 NRPN rows left out, each for a reason; nothing else."""
		wave = pymidiinstrumentdefs.load("groove_synthesis/third_wave", [CORPUS])

		numbers = {control.cc for control in wave.controls.values() if control.cc is not None}
		nrpns = {control.nrpn for control in wave.controls.values() if control.nrpn is not None}

		# Bank select, and the three filter controllers 1.9a moved to 9, 37 and 39.
		assert not numbers & {32, 65, 66, 67}
		assert {2, 9, 37, 39} <= numbers

		assert len(self.NRPN_LEFT_OUT) == 56
		assert nrpns == set(range(0, 469)) - set(self.NRPN_LEFT_OUT)

		# The row filed under `Mutli` is carried with the others of its kind.
		assert 253 in nrpns
		assert next(control for control in wave.controls.values() if control.nrpn == 253).group == "multi"

	def test_the_groups_are_the_makers_own (self) -> None:
		"""The controller table's column heading, and the NRPN table's categories."""
		wave = pymidiinstrumentdefs.load("groove_synthesis/third_wave", [CORPUS])

		assert wave.groups == {"panel": "3rd Wave Control", "single": "Single", "multi": "Multi", "global": "Global"}

		counts = collections.Counter(control.group for control in wave.controls.values())

		assert counts == {"panel": 101, "single": 129, "multi": 269, "global": 15}

	def test_a_button_is_pressed_from_64 (self) -> None:
		"""">= 64 is pressed, <= 63 is off" on every button the controller table names."""
		wave = pymidiinstrumentdefs.load("groove_synthesis/third_wave", [CORPUS])

		buttons = [control for control in wave.controls.values() if control.values]

		assert len(buttons) == 29
		assert all(control.values == {"off": 0, "pressed": 64} for control in buttons)
		assert wave.controls["sustain_pedal"].values == {"off": 0, "pressed": 64}

	def test_the_two_tables_disagree_about_effect_2 (self) -> None:
		"""Fourteen types with the shimmer reverb by controller, thirteen without it by NRPN."""
		wave = pymidiinstrumentdefs.load("groove_synthesis/third_wave", [CORPUS])

		by_cc = next(control for control in wave.controls.values() if control.cc == 110)
		by_nrpn = next(control for control in wave.controls.values() if control.nrpn == 231)

		assert by_cc.range == (0, 13) and "shimmer_reverb" in by_cc.choices
		assert by_nrpn.range == (0, 12) and "shimmer_reverb" not in by_nrpn.choices

	def test_the_firmware_is_the_newest_and_was_found_by_search (self) -> None:
		"""2.0c, whose one change is editor system exclusive; 2.0a's three are in the specification."""
		wave = pymidiinstrumentdefs.load("groove_synthesis/third_wave", [CORPUS])

		assert wave.model.firmware == "2.0c"
		assert wave.sources["release_notes"].edition == "2.0c"
		assert wave.sources["spec"].edition == "v2.0"
		assert wave.sources["manual"].edition == "1.9"

	def test_four_parts_in_a_mode_and_none_declared (self) -> None:
		"""Multitimbral mode is a setting with no stated default, so the file describes one channel."""
		wave = pymidiinstrumentdefs.load("groove_synthesis/third_wave", [CORPUS])

		assert wave.parts == {}
		assert wave.voice is not None and wave.voice.polyphony == 24
		assert wave.midi.per_voice_channels is True

		said = prose_of("groove_synthesis", "third_wave")

		assert "The 3rd Wave is 4-part multitimbral" in said
		assert "multi-parts 1-2 on a given program" in said

	def test_what_is_not_recorded (self) -> None:
		"""Velocity, aftertouch, receiving program change, the presets, the mode and the bend depth."""
		wave = pymidiinstrumentdefs.load("groove_synthesis/third_wave", [CORPUS])

		assert wave.voice is not None
		assert wave.voice.velocity is None
		assert wave.voice.aftertouch is None
		assert wave.voice.pitch_bend is not None
		assert wave.voice.pitch_bend.programmable is True
		assert wave.voice.pitch_bend.semitones is None
		assert wave.midi.program_change is not None
		assert wave.midi.program_change.sends is True
		assert wave.midi.program_change.receives is None
		assert wave.midi.program_change.presets is None
		assert wave.midi.mode is None
		assert wave.midi.sysex is True
		assert wave.midi.transport == "receives"

	def test_the_first_groove_synthesis_and_the_thirty_second_maker (self) -> None:
		"""Counted rather than claimed, and the current count lives here until a newer maker arrives."""
		names = [name for name in pymidiinstrumentdefs.available([CORPUS]) if name.startswith("groove_synthesis/")]

		assert names == ["groove_synthesis/third_wave"]

		makers = {name.split("/")[0] for name in pymidiinstrumentdefs.available([CORPUS])}

		assert len(makers) == 32
		assert "GROOVE SYNTHESIS IS THE THIRTY-SECOND MAKER HERE" in prose_of("groove_synthesis", "third_wave")


class TestCascadia:

	"""Four controllers, and four is the whole of what this maker publishes.

	Every other definition here with a handful of controls has a handful because
	somebody could only find a handful.  This one has four because MIDI arrives,
	becomes a voltage at one of eight jacks, and which controller drives two of
	those jacks is whatever its owner last taught it.
	"""

	def test_four_controls_and_every_one_of_them_only_receives (self) -> None:
		"""One sentence settles the direction of all four: the output jack carries a clock."""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])
		numbers = sorted(control.cc for control in cascadia.controls.values()
			if control.cc is not None)

		assert len(cascadia.controls) == 4
		assert numbers == [1, 2, 5, 65]
		assert {control.direction for control in cascadia.controls.values()} == {"receives"}

		# **`learned` alongside published controls**, which is the arrangement the Iridium
		# established with fifteen of them and the MPC Key 37 with one.
		assert cascadia.midi.learns_control_change is True

		flat = " ".join((cascadia.source or "").split())

		assert "**FOUR CONTROLLER NUMBERS ARE PUBLISHED FOR THIS INSTRUMENT AND NO MORE.**" in flat
		assert "**This one rests on a sentence.**" in flat

	def test_two_are_fixed_and_two_are_only_what_the_factory_chose (self) -> None:
		"""A consumer that offers all four as fixtures is wrong about half of them."""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])
		flat = " ".join((cascadia.source or "").split())

		# The portamento pair cannot be reassigned.
		assert cascadia.controls["portamento"].cc == 65
		assert cascadia.controls["portamento_time"].cc == 5
		assert "**Neither is learnable and neither can be reassigned**" in flat

		# The other two are the default source for a jack, over the full range.
		assert cascadia.controls["midi_mod_output"].cc == 1
		assert cascadia.controls["midi_cc_output"].cc == 2
		assert "what a Cascadia answers to **as it leaves the factory**" in flat

	def test_the_portamento_switch_carries_choices_because_a_band_would_invent_a_boundary (self) -> None:
		"""The maker gives 127 and 0 and says nothing about anything between them."""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])
		portamento = cascadia.controls["portamento"]

		assert portamento.choices == {"off": 0, "on": 127}
		assert portamento.values == {}
		assert portamento.kind == pymidiinstrumentdefs.SWITCH

		# A choice is one exact value, so neither state claims any ground around itself.
		assert portamento.band("off") == (0, 0)
		assert portamento.band("on") == (127, 127)

		# **And `off` is a string here, not a boolean.** YAML would have read it either way.
		assert set(portamento.choices) == {"off", "on"}

	def test_a_controller_sent_to_a_new_cascadia_reaches_a_jack_patched_to_nothing (self) -> None:
		"""Four of the eight MIDI outputs are patched at the factory and these two are not.

		Which makes this the sharpest thing in the definition for anybody writing a
		panel: the two controls are real, published and audible only after somebody
		puts a cable in.
		"""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])
		flat = " ".join((cascadia.source or "").split())

		assert "**SENDING EITHER OF THEM TO A NEW CASCADIA MOVES A VOLTAGE THAT IS CONNECTED " \
			"TO NOTHING.**" in flat
		assert "**So controller 1 and controller 2 are audible only after somebody patches a " \
			"cable**" in flat

		# And in Dual Mono mode they stop being controller destinations at all.
		assert cascadia.voice.voicing_modes == (1, 2)
		assert "the two controllers below and the second voice are alternatives, not additions" \
			in flat

	def test_the_manual_documents_a_firmware_three_releases_behind_the_instrument (self) -> None:
		"""And the gap was checked rather than assumed harmless."""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])

		assert cascadia.model.firmware == "1.4.4.0"
		assert cascadia.sources["manual"].edition == "v1.4, for firmware 1.4.1"

		flat = " ".join((cascadia.source or "").split())

		assert "**not one of them touches anything recorded here**" in flat

	def test_the_bend_range_contradiction_is_settled_and_the_clock_one_is_not (self) -> None:
		"""Two self-contradictions in one manual, resolved two different ways.

		The bend range is decided by the maker's changelog, which carries the manual's
		unheaded block word for word under a version heading.  The clock is not decided
		at all, because all four editions carry both halves.
		"""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])
		flat = " ".join((cascadia.source or "").split())

		# Settled: the table is stale, and the typo is what proves the match.
		assert "**So the maximum is 96 and the table is out of date**" in flat
		assert "including its misspelling of `Ableton` as `Albeton`" in flat

		# But the shipped value is nowhere printed, so only the settability is recorded.
		assert cascadia.voice.pitch_bend is not None
		assert cascadia.voice.pitch_bend.programmable is True
		assert cascadia.voice.pitch_bend.semitones is None

		# Not settled, and the field rests on the other port instead.
		assert cascadia.midi.clock == "both"
		assert "there is no moment at which one replaced the other" in flat
		assert "**`clock: both` does not rest on either**" in flat

	def test_all_four_editions_of_the_manual_are_cited_and_each_does_a_job (self) -> None:
		"""Reading the earlier three is what told the two contradictions apart.

		It is also what caught a wrong answer: the first pass concluded that the
		current edition had introduced the clock clash, on a search window that
		stopped four words short of the sentence saying otherwise.
		"""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])
		editions = sorted(key for key in cascadia.sources if key.startswith("manual"))

		assert editions == ["manual", "manual_1_1", "manual_1_2", "manual_1_3"]
		assert sorted(cascadia.sources) == ["changelog", "firmware_index", "manual",
			"manual_1_1", "manual_1_2", "manual_1_3", "product_page"]

		# Oldest first, and the first edition names no firmware on its cover at all.
		dates = [str(cascadia.sources[key].dated) for key in
			("manual_1_1", "manual_1_2", "manual_1_3", "manual")]

		assert dates == sorted(dates)
		assert "the first, which names no firmware on its cover" in \
			(cascadia.sources["manual_1_1"].edition or "")

		assert " ".join(prose_of("intellijel", "cascadia").split()).count(
			"**A few words either side of a match is not the sentence**") == 1

	def test_velocity_is_gated_by_a_switch_that_has_no_controller_number (self) -> None:
		"""The manual itself describes the silence this value exists to explain."""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])

		assert cascadia.voice.velocity is not None
		assert cascadia.voice.velocity.note_on == "gated"
		assert cascadia.voice.velocity.note_off is False

		# **Empty, because the thing doing the gating is a panel switch.** The Perkons
		# HD-01 is the precedent for recording `gated` with nothing to name.
		assert cascadia.voice.velocity.gated_by == ()

		flat = " ".join((cascadia.source or "").split())

		assert "**No edition prints which position that switch ships in**" in flat
		assert "the maker's own missing letter" in flat

	def test_per_voice_channels_is_unrecorded_on_a_monophonic_mpe_instrument (self) -> None:
		"""The first instrument here where answering to MPE and spreading voices come apart.

		In this corpus the field means the voices are spread across channels, one note
		to each.  One voice cannot be spread, so both answers would mislead - and the
		Messenger left the same field unrecorded on the same kind of machine.
		"""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])

		assert cascadia.midi.per_voice_channels is None
		assert cascadia.voice.polyphony == 1

		flat = " ".join((cascadia.source or "").split())

		assert "`true` would misdescribe the instrument and `false` would hide the feature" in flat

		# **AND NOT ONE INSTRUMENT THAT SETS THE FLAG IS MONOPHONIC**, which is the whole
		# distinction: thirteen set it, and none of the thirteen records one voice. So this
		# would have been the first, and the field's meaning here cannot stretch to it.
		setters = {}

		for name in pymidiinstrumentdefs.available([CORPUS]):
			other = pymidiinstrumentdefs.load(name, [CORPUS])

			if other.midi is not None and other.midi.per_voice_channels is True:
				setters[name] = other

		assert len(setters) == 13
		assert "modal/carbon8m" in setters and "waldorf/iridium" in setters
		assert [name for name, other in setters.items() if other.voice.polyphony == 1] == []

		# And the monophonic one that also leaves it alone, for a weaker reason: nothing
		# in its manual said either way.
		messenger = pymidiinstrumentdefs.load("moog/messenger", [CORPUS])

		assert messenger.midi.per_voice_channels is None
		assert messenger.voice.polyphony == 1

	def test_what_this_maker_calls_a_midi_mode_is_not_what_midi_calls_one (self) -> None:
		"""Which is why no mode is recorded, and not for want of looking."""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])

		assert cascadia.midi.mode is None

		flat = " ".join((cascadia.source or "").split())

		assert "**WHAT THIS MAKER CALLS A MIDI MODE IS NOT WHAT MIDI CALLS ONE**" in flat
		assert "no sheet of the four editions names one or uses the word `omni`" in flat

	def test_the_transport_absence_could_not_have_been_established_by_counting (self) -> None:
		"""Eight hits, every one of them ordinary English, in a manual with no transport."""
		cascadia = pymidiinstrumentdefs.load("intellijel/cascadia", [CORPUS])
		flat = " ".join((cascadia.source or "").split())

		assert cascadia.midi.transport == "none"
		assert "**A count would have reported eight transport mentions in a manual that has " \
			"none**" in flat

		# The other checked absences, each with what was swept for it.
		assert cascadia.midi.sysex is False
		assert cascadia.midi.nrpn == "none"
		assert cascadia.midi.program_change is not None
		assert cascadia.midi.program_change.receives is False
		assert cascadia.midi.program_change.sends is False

		# No note range, because a note above the top of the pitch output is not silent.
		assert cascadia.voice.note_range is None
		assert "NOT RECORDED: the note range." in flat

	def test_the_first_intellijel_so_the_maker_rule_has_nothing_to_rest_on (self) -> None:
		"""Eleven times the standing rule has been tested; here there is not even one sibling."""
		names = [name for name in pymidiinstrumentdefs.available([CORPUS])
			if name.startswith("intellijel/")]

		assert names == ["intellijel/cascadia"]

		comments = " ".join(prose_of("intellijel", "cascadia").split())

		assert "Intellijel is the thirty-first maker here and its first instrument." in comments

		# Thirty-one makers when it arrived. **The current count is asserted with the newest
		# maker** - `TestThirdWave` - so this claim was narrowed when the corpus grew rather than
		# deleted: Intellijel is still one maker of the thirty-one that came before Groove Synthesis.
		makers = {name.split("/")[0] for name in pymidiinstrumentdefs.available([CORPUS])}

		assert len(makers - {"groove_synthesis"}) == 31


class TestMontage:

	"""Ten Data List rows, and two of them serve one file.

	So a label on Yamaha's download page cannot identify an edition and neither can a
	filename - both rows end `montage_en_dl_c0.pdf`.  What identifies one is the code
	Yamaha prints in the document's own colophon, and the map turns out not to have
	moved in four and a half years anyway.
	"""

	def test_twenty_nine_controls_and_half_of_them_are_only_the_factory_choice (self) -> None:
		"""The chart gives 1 to 95 as assignable, and a footnote gives the shipped numbers."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		numbers = sorted(control.cc for control in montage.controls.values()
			if control.cc is not None)

		assert len(montage.controls) == 29
		assert numbers == [1, 2, 5, 7, 10, 11, 16, 17, 18, 19, 20, 21, 22, 23, 24,
			64, 65, 66, 71, 72, 73, 74, 75, 86, 87, 88, 89, 91, 94]

		# **Fourteen of the twenty-nine are a default rather than a fixture**, and they are
		# in a group of their own so a consumer can read them as one.
		assignable = [name for name, control in montage.controls.items()
			if control.group == "assignable"]

		assert len(assignable) == 14
		assert montage.midi.learns_control_change is True
		assert montage.groups["assignable"] == "Assignable Cntrl"

		# Six numbers the chart names are addressing machinery and are not here.
		for machinery in (0, 32, 6, 38, 96, 97, 100, 101):
			assert machinery not in numbers, machinery

	def test_three_are_received_and_never_transmitted (self) -> None:
		"""The maker prints two lists and the transmitted one is a subset."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		receives = sorted(control.cc for control in montage.controls.values()
			if control.direction == "receives" and control.cc is not None)

		assert receives == [11, 65, 66]
		assert montage.controls["expression"].cc == 11
		assert montage.controls["portamento_switch"].cc == 65
		assert montage.controls["sostenuto"].cc == 66

		# The other twenty-six travel both ways, which is this format's default.
		assert {control.direction for control in montage.controls.values()} == {"both", "receives"}

	def test_two_controllers_are_named_differently_depending_on_direction (self) -> None:
		"""Same number, same sheet, two names - and the label is the received one."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		flat = " ".join((montage.source or "").split())

		assert montage.controls["harmonic_content"].cc == 71
		assert montage.controls["brightness"].cc == 74

		assert '"FILTER RESONANCE"' in flat and '"HARMONIC CONTENT"' in flat
		assert '"FILTER CUTOFF FREQ"' in flat and '"BRIGHTNESS"' in flat
		assert "**Same controller, same sheet, two names**" in flat

	def test_two_rows_of_the_download_page_serve_one_file (self) -> None:
		"""Proved by hash rather than by inference, which is the Iridium's test inverted."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		comments = " ".join(prose_of("yamaha", "montage_6_7_8").split())

		assert "two of the rows serve the same file" in comments.lower()
		assert "same 5,088,645 bytes, same SHA-256" in comments

		# **The edition is identified by the code inside the document**, not by the row.
		for key, code in (("data_list", "MW-J0"), ("data_list_3_00", "MW-I0"),
				("data_list_first", "MW-C0")):
			assert (montage.sources[key].edition or "").startswith(code), key

	def test_the_map_is_unchanged_across_every_edition_read (self) -> None:
		"""Three editions spanning 2016 to 2020, compared cell for cell."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		comments = " ".join(prose_of("yamaha", "montage_6_7_8").split())

		assert "**cell for cell**" in comments
		assert "Every cell agrees" in comments

		# And the chart's own version is not the instrument's, which is the trap.
		assert "`Version : 1.0`" in comments
		assert montage.model.firmware == "3.51"

		dates = [str(montage.sources[key].dated) for key in
			("data_list_first", "data_list_3_00", "data_list")]

		assert dates == sorted(dates)
		assert dates[0].startswith("2016") and dates[-1].startswith("2020")

	def test_the_two_charts_disagree_and_the_definition_follows_the_sounding_one (self) -> None:
		"""Polyphonic pressure is recorded by the sequencer and never reaches the engine.

		Which is `roland/fantom_6_7_8`'s situation with the answer the other way about,
		because there both kinds reached the engine and `poly` was the stronger word.
		"""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		flat = " ".join((montage.source or "").split())

		assert montage.voice.aftertouch == "channel"
		assert "**never reaches the tone generator**" in flat
		assert "the one field here where the two halves of the instrument give different " \
			"answers and the stronger one is not the right one" in flat

		# The Fantom took the other answer on its own evidence.
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert fantom.voice.aftertouch == "poly"

		# And the split is why two fields say `both` where one chart alone would not.
		assert montage.midi.clock == "both"
		assert montage.midi.transport == "both"

	def test_the_polyphony_is_given_twice_and_never_totalled (self) -> None:
		"""Two engines, two ceilings of 128, and no sum in 86 sheets."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		flat = " ".join((montage.source or "").split())

		assert montage.voice.polyphony is None
		assert montage.voice.polyphony_shared is True
		assert '"Polyphony AWM2: 128 (max.; stereo/mono waveforms) FM-X: 128 (max.)"' in flat
		assert "no sum in 86 sheets" in flat

		# The Fantom is the precedent for leaving it out.
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert fantom.voice.polyphony is None

	def test_sixteen_parts_each_on_its_own_channel (self) -> None:
		"""Part N answers on channel N, which the data format states outright."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		part = montage.parts["part"]

		assert part.count == 16
		assert part.is_assigned is True
		assert part.takes("notes") and part.takes("controls") and part.takes("program_change")
		assert part.addressing == "pitches"

		flat = " ".join((montage.source or "").split())

		assert '"[SW1] Complies with Part Receive Switch. The MIDI Receive Channel complies ' \
			'with the Part number."' in flat

	def test_mode_three_is_named_which_the_four_older_yamahas_do_not (self) -> None:
		"""Four Yamahas were already here and not one of them names a reception mode.

		**This test was called `..._which_no_other_yamaha_here_does` and that stopped being
		true at rank 110**, when `yamaha/seqtrak` arrived naming mode 3 outright and the
		assertion failed.  It is renamed rather than relaxed: the claim worth keeping is
		about the four that came before, which is the maker-rule point, and the fact that
		two of six now name a mode is asserted in `TestSeqtrak`.
		"""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])

		assert montage.midi.mode == 3

		older = ["yamaha/dx7", "yamaha/reface_cp", "yamaha/reface_cs", "yamaha/reface_dx"]

		for name in older:
			assert pymidiinstrumentdefs.load(name, [CORPUS]).midi.mode is None, name

		# The one thing every Yamaha here shares, which the maker rule says proves nothing.
		for name in pymidiinstrumentdefs.available([CORPUS]):
			if name.startswith("yamaha/"):
				assert pymidiinstrumentdefs.load(name, [CORPUS]).midi.sysex is True, name

	def test_every_received_message_sits_behind_a_switch_with_no_printed_default (self) -> None:
		"""The chart's footnote names a switch and never says which way it points."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])
		flat = " ".join((montage.source or "").split())

		assert '"*1 receive/transmit if switch is on."' in flat
		assert "**Not one of the 187 sheets marks a factory position for any of them.**" in flat

		# The two switches that are bands rather than exact values, as the maker prints them.
		for name in ("portamento_switch", "sostenuto"):
			control = montage.controls[name]

			assert control.values == {"off": 0, "on": 64}
			assert control.band("off") == (0, 63) and control.band("on") == (64, 127)

	def test_the_presets_are_an_approximation_so_no_count_is_recorded (self) -> None:
		"""An approximation is not a count."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])

		assert montage.midi.program_change is not None
		assert montage.midi.program_change.receives is True
		assert montage.midi.program_change.sends is True
		assert montage.midi.program_change.presets is None

		flat = " ".join((montage.source or "").split())

		assert '"Performances Approx. 1,900"' in flat
		assert "**An approximation is not a count**" in flat

		# NRPN is a checked absence, against four registered-parameter controllers.
		assert montage.midi.nrpn == "none"
		assert "controllers 98 and 99 appear in no list" in flat

	def test_one_definition_for_three_keybeds_on_the_fantoms_precedent (self) -> None:
		"""And the specification is the evidence, not the precedent alone."""
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])

		assert montage.model.name == "MONTAGE6/7/8"

		flat = " ".join((montage.source or "").split())

		assert "**THE THREE MODELS DIFFER IN THEIR KEYBED AND IN NOTHING ELSE**" in flat
		assert '"MONTAGE8: 88 keys, Balanced Hammer Effect Keyboard (Initial Touch/Aftertouch)"' in flat

		# The precedent it follows, and the two names are spelled the maker's way in each.
		fantom = pymidiinstrumentdefs.load("roland/fantom_6_7_8", [CORPUS])

		assert fantom.model.name == "FANTOM-6/7/8"
		assert "roland/fantom_6_7_8" in flat


class TestSeqtrak:

	"""The numbers are in one document and the names are in another.

	Yamaha's Data List carries the implementation chart, which lists sixteen cells of
	controller numbers and names three of them only as model-specific, with a footnote
	pointing at "the manual".  The User Guide's section 18.3 names thirty-seven
	controllers and says nothing about which way any of them travels.  Neither document
	is sufficient, and the Data List's own MIDI Data Table - which is where rank 109
	taught us to look - is a system exclusive address map with no controller names in it.
	"""

	def test_forty_controls_reconciled_from_two_documents (self) -> None:
		"""37 named in the User Guide, plus 3 the chart carries and no table names."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])
		numbers = sorted(control.cc for control in seqtrak.controls.values()
			if control.cc is not None)

		assert len(seqtrak.controls) == 40
		assert numbers == [5, 7, 10, 11, 20, 21, 23, 24, 25, 26, 27, 28, 29,
			64, 65, 66, 71, 73, 74, 75, 91, 94,
			102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
			116, 117, 118, 119]

		# **The three the chart has and 18.3 has not**: standard controllers the instrument
		# answers to with no model-specific parameter published behind them.
		for standard in (11, 64, 66):
			assert standard in numbers, standard

		# Ten numbers the chart names are addressing machinery or channel mode, and the
		# ruling at rank 77 and the Fantom's keep them out.
		for machinery in (0, 32, 6, 38, 96, 97, 100, 101, 126, 127):
			assert machinery not in numbers, machinery

		# 72 is absent because the chart writes `71,73-75` rather than `71-75`.
		assert 72 not in numbers

	def test_five_are_received_only_and_two_of_them_on_two_documents_word (self) -> None:
		"""The chart crosses their transmitted column; the guide says so in prose for two."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])
		receives = sorted(control.cc for control in seqtrak.controls.values()
			if control.direction == "receives" and control.cc is not None)

		assert receives == [11, 23, 24, 64, 66]

		# MUTE and SOLO are the pair the User Guide also states, which is the account's point.
		assert seqtrak.controls["mute"].cc == 23
		assert seqtrak.controls["solo"].cc == 24
		assert "receive only" in (seqtrak.source or "")

		both = [control for control in seqtrak.controls.values() if control.direction == "both"]

		assert len(both) == 35

	def test_the_two_switches_take_different_conventions (self) -> None:
		"""One is given exact values and the other halves of the range, two sheets apart."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])

		# Exact values: 0 is off and 1 is on, and nothing says what 2 to 127 do.
		assert seqtrak.controls["portamento_switch"].choices == {"off": 0, "on": 1}
		assert seqtrak.controls["portamento_switch"].values == {}

		# Bands: 0 to 63 off, 64 to 127 on.
		assert seqtrak.controls["mute"].values == {"off": 0, "on": 64}
		assert seqtrak.controls["mute"].choices == {}

	def test_eleven_tracks_on_eleven_channels_that_cannot_be_moved (self) -> None:
		"""Four groups, because that is how both documents group the eleven."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])

		assert seqtrak.midi.channels == (1, 11)
		assert sorted(seqtrak.parts) == ["drum", "dx", "sampler", "synth"]

		# The counts sum to the eleven channels, and the offsets lay them out in order.
		assert [(part.count, part.channel_offset) for name, part in
			sorted(seqtrak.parts.items(), key = lambda pair: pair[1].channel_offset or 0)] == \
			[(7, 0), (2, 7), (1, 9), (1, 10)]

		assert sum(part.count for part in seqtrak.parts.values()) == 11

	def test_the_part_specific_controls_name_their_part (self) -> None:
		"""Where a control reaches one group only, the control says which."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])

		assert seqtrak.controls["drum_pitch"].part == "drum"

		fm = [name for name, control in seqtrak.controls.items() if control.part == "dx"]

		assert sorted(fm) == ["fm_algorithm", "fm_modulation_amount",
			"fm_modulator_feedback", "fm_modulator_frequency"]

		# **The arpeggio and portamento controls reach two groups**, synth and DX, which a
		# single `part` field cannot say - so they name none and the account says it instead.
		for spanning in ("arp_type", "arp_gate", "arp_speed", "portamento_time"):
			assert seqtrak.controls[spanning].part is None, spanning

	def test_aftertouch_is_none_without_needing_a_judgement (self) -> None:
		"""One chart, crossed in all four boxes - where its sibling had two that disagreed."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])

		assert seqtrak.voice.aftertouch == "none"

		# The MONTAGE is the contrast: two charts, and `channel` chosen between them.
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])

		assert montage.voice.aftertouch == "channel"

	def test_polyphony_is_unrecorded_because_two_engines_have_no_sum (self) -> None:
		"""128 voices and 8, and no third number anywhere - rank 109's situation exactly."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])
		montage = pymidiinstrumentdefs.load("yamaha/montage_6_7_8", [CORPUS])

		assert seqtrak.voice.polyphony is None
		assert montage.voice.polyphony is None

		# The reason is in the account rather than left as a silence.
		assert "no sum" in (seqtrak.source or "")

	def test_bend_is_programmable_and_ships_at_two_semitones (self) -> None:
		"""Its maker publishes a default where `roland/jd_xi`'s publishes none."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])

		assert seqtrak.voice.pitch_bend is not None
		assert seqtrak.voice.pitch_bend.semitones == 2
		assert seqtrak.voice.pitch_bend.programmable is True

		jd_xi = pymidiinstrumentdefs.load("roland/jd_xi", [CORPUS])

		assert jd_xi.voice.pitch_bend is not None
		assert jd_xi.voice.pitch_bend.semitones is None
		assert jd_xi.voice.pitch_bend.programmable is True

	def test_nrpn_is_a_checked_absence_and_sysex_is_not (self) -> None:
		"""Not one occurrence in 272 sheets, swept with the whitespace taken out."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])

		assert seqtrak.midi.nrpn == "none"
		assert seqtrak.midi.sysex is True
		assert seqtrak.midi.mode == 3
		assert seqtrak.midi.clock == "both"
		assert seqtrak.midi.transport == "both"

	def test_the_sixth_yamaha_and_the_maker_rule_held_again (self) -> None:
		"""All six say sysex, and this one is the second to name a mode or carry parts."""
		names = [name for name in pymidiinstrumentdefs.available([CORPUS])
			if name.startswith("yamaha/")]

		assert len(names) == 6

		loaded = {name: pymidiinstrumentdefs.load(name, [CORPUS]) for name in names}

		# The one thing all six agree on.
		assert all(one.midi.sysex is True for one in loaded.values())

		# **Only two of the six name a reception mode, and only two have parts** - this one
		# and the MONTAGE. A Yamaha Data List is not one shape.
		with_mode = sorted(name for name, one in loaded.items() if one.midi.mode is not None)
		with_parts = sorted(name for name, one in loaded.items() if one.parts)

		assert with_mode == ["yamaha/montage_6_7_8", "yamaha/seqtrak"]
		assert with_parts == ["yamaha/montage_6_7_8", "yamaha/seqtrak"]

	def test_the_firmware_comes_from_inside_both_documents (self) -> None:
		"""Where rank 109's Data List named no version at all, this one names it twice."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])

		assert seqtrak.model.firmware == "2.00"
		assert seqtrak.model.revision == "D0"
		assert sorted(seqtrak.sources) == ["data_list", "downloads_page", "user_guide"]

	def test_the_drumkit_disagreement_is_carried_rather_than_reduced (self) -> None:
		"""The specification names five track types; both MIDI tables name four."""
		seqtrak = pymidiinstrumentdefs.load("yamaha/seqtrak", [CORPUS])

		assert "DRUMKIT" in (seqtrak.source or "")
		assert len(seqtrak.parts) == 4


class TestWavestation:

	"""The 1990 keyboard, read by eye from three scans, and not the 2020 wavestate.

	**NO GATE CAN CHECK A NUMBER IN THIS FILE**: every document Korg serves for it is a scan with
	no text layer, so these tests pin what two readers agreed the scans say.
	"""

	def test_it_was_read_by_eye_and_says_so (self) -> None:
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		assert set(wavestation.sources) == {"player", "reference", "addendum", "listing"}
		assert "EVERY FIGURE HERE WAS READ BY EYE" in " ".join((wavestation.source or "").split())

	def test_eight_controls_from_two_lists_that_differ_by_one (self) -> None:
		"""The chart has no row for controller 7; both appendices and three other pages do."""
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		assert {control.cc for control in wavestation.controls.values()} == {0, 1, 4, 7, 16, 17, 32, 64}
		assert wavestation.controls["volume"].direction == "both"

		account = " ".join((wavestation.source or "").split())

		assert "This parameter has always responded to MIDI Volume (Controller #7); now, MIDI " \
			"Volume may be transmitted as well" in account
		assert "VOLUME allows the pedal to control the Part volume level as well as transmit MIDI " \
			"Controller 7" in account

	def test_the_registered_parameter_machinery_is_left_out_by_name (self) -> None:
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		assert not {6, 38, 100, 101} & {control.cc for control in wavestation.controls.values()}
		assert "Pitch bend range, Master fine tune" in " ".join((wavestation.source or "").split())

	def test_bank_select_is_received_in_one_half_and_sent_in_both (self) -> None:
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		lsb = wavestation.controls["bank_select_lsb"]
		msb = wavestation.controls["bank_select_msb"]

		assert (lsb.cc, lsb.direction, dict(lsb.values)) == (32, "both", {"ram1_ram2": 0, "rom_card": 1})
		assert (msb.cc, msb.direction, msb.range) == (0, "transmits", (0, 0))

	def test_the_assignable_controllers_are_not_recorded (self) -> None:
		"""Two modulation sources set to any of 1 to 95, and no page names their factory setting."""
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		assert 2 not in {control.cc for control in wavestation.controls.values()}
		assert "no page says those are the factory settings" in " ".join(
			(wavestation.source or "").split())

	def test_it_ships_in_omni_and_multi_mode_has_sixteen_channels (self) -> None:
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		assert wavestation.midi.mode == 1

		multiset = wavestation.parts["multiset"]

		assert (multiset.count, multiset.channel_offset) == (16, 0)
		assert multiset.receives == ("notes", "controls", "program_change")
		assert wavestation.parts["fx_control"].receives == ("controls",)

	def test_thirty_two_voices_spent_one_two_or_four_a_note (self) -> None:
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		assert wavestation.voice.polyphony == 32
		assert wavestation.voice.voicing_modes == (8, 16, 32)
		assert wavestation.voice.polyphony_shared is True

	def test_it_answers_to_both_aftertouches_and_takes_clock_for_one_thing (self) -> None:
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		assert wavestation.voice.aftertouch == "poly"
		assert wavestation.midi.clock == "receives"
		assert wavestation.midi.transport == "none"
		assert "Used for Wave Sequence Sync function" in " ".join(
			(wavestation.source or "").split())

	def test_it_describes_software_3_0_from_the_addendum (self) -> None:
		"""The newest version any Korg document names; Korg publishes no operating system for it."""
		wavestation = pymidiinstrumentdefs.load("korg/wavestation", [CORPUS])

		assert wavestation.model.firmware == "3.0"
		assert wavestation.sources["addendum"].title == "Wavestation Version 3 Addendum"
		assert "Wavestation software version 3.0" in prose_of("korg", "wavestation")


class TestTR08:

	"""The Boutique TR-808, off a one-sheet chart.

	Roland lists it last among ten documents. It gives thirty-eight controllers, all of them
	numbers the TR-8 uses, eleven of them under another name.
	"""

	def test_thirty_eight_controls_all_both_ways (self) -> None:
		"""Four ranges on the chart, and the list names every number in them."""
		tr_08 = pymidiinstrumentdefs.load("roland/tr_08", [CORPUS])

		numbers = sorted(control.cc for control in tr_08.controls.values() if control.cc is not None)

		assert numbers == list(range(20, 30)) + list(range(46, 64)) + [71] + list(range(80, 89))
		assert {control.direction for control in tr_08.controls.values()} == {"both"}

		account = " ".join((tr_08.source or "").split())

		assert "THIRTY-EIGHT CONTROLLERS, ALL OF THEM BOTH WAYS." in account

	def test_the_groups_are_the_select_switch_spelled_out (self) -> None:
		"""Twelve groups, each the manual's own expansion of a two-letter code."""
		tr_08 = pymidiinstrumentdefs.load("roland/tr_08", [CORPUS])

		assert len(tr_08.groups) == 12
		assert tr_08.groups["ch"] == "CLS’D HIHAT"
		assert tr_08.groups["accent"] == "ACCENT"

		for name, control in tr_08.controls.items():
			assert control.group == ("accent" if name == "accent" else name.split("_")[0]), name

	def test_the_numbers_are_the_tr_8s_and_eleven_carry_another_name (self) -> None:
		"""Every number is the TR-8's; 86 to 88 are its `RC` and this machine's cowbell."""
		tr_08 = pymidiinstrumentdefs.load("roland/tr_08", [CORPUS])
		tr_8 = pymidiinstrumentdefs.load("roland/tr_8", [CORPUS])

		here = {control.cc: control.label
			for control in tr_08.controls.values() if control.cc is not None}
		there = {control.cc: control.label
			for control in tr_8.controls.values() if control.cc is not None}

		assert set(here) <= set(there)
		assert sorted(set(there) - set(here)) == [9, 12, 13, 16, 17, 18, 68, 69, 70, 89, 90, 91]

		renamed = {cc: (there[cc], here[cc]) for cc in here if here[cc] != there[cc]}

		assert sorted(renamed) == [21, 25, 58, 59, 60, 83, 84, 85, 86, 87, 88]
		assert renamed[86] == ("RC TUNE", "CB TUNE")
		assert renamed[21] == ("BD ATTACK", "BD TONE")

		flat = " ".join(prose_of("roland", "tr_08").split())

		assert "**THE CONTROLLER NUMBERS ARE THE TR-8's, AND ELEVEN OF THEM CARRY ANOTHER NAME.**" in flat

	def test_two_note_tables_and_the_sent_one_is_carried (self) -> None:
		"""Sixteen instruments; seven answer to a second number; no single range covers them."""
		tr_08 = pymidiinstrumentdefs.load("roland/tr_08", [CORPUS])

		assert tr_08.voice is not None
		assert tr_08.voice.addressing == "voices"
		assert len(tr_08.voice.voices) == 16
		assert tr_08.voice.voices["snare_drum"] == 38
		assert tr_08.voice.voices["cow_bell"] == 56
		assert tr_08.voice.note_range is None

		account = " ".join((tr_08.source or "").split())

		assert "**Seven answer to two numbers and send one**" in account
		assert "**So no note range is recorded**, because 35 to 75 would claim eighteen numbers" \
			" the table does not have." in account

	def test_mode_3_on_one_channel_and_the_mode_messages_change_nothing (self) -> None:
		tr_08 = pymidiinstrumentdefs.load("roland/tr_08", [CORPUS])

		assert tr_08.midi.mode == 3
		assert tr_08.midi.channels == (1, 16)
		assert "*2 The same processing will be carried out as when All Notes Off is received." \
			in " ".join((tr_08.source or "").split())

	def test_clock_and_transport_both_and_no_program_change (self) -> None:
		"""256 patterns and none of them reachable over MIDI."""
		tr_08 = pymidiinstrumentdefs.load("roland/tr_08", [CORPUS])

		assert tr_08.midi.clock == "both"
		assert tr_08.midi.transport == "both"
		assert tr_08.midi.program_change is not None
		assert (tr_08.midi.program_change.receives, tr_08.midi.program_change.sends) == (False, False)
		assert tr_08.midi.program_change.presets is None
		assert tr_08.midi.sysex is False

	def test_the_footnote_marks_each_do_two_jobs (self) -> None:
		account = " ".join((prose_of("roland", "tr_08")).split())

		assert "THE CHART'S FOOTNOTE MARKS EACH DO TWO JOBS, AND ONE OF THEM IS EXPLAINED NOWHERE." \
			in account

	def test_it_describes_1_08_through_the_manual_for_1_07 (self) -> None:
		"""Edition 04 adds exactly what 1.07 added; 1.08 changed only its number."""
		tr_08 = pymidiinstrumentdefs.load("roland/tr_08", [CORPUS])

		assert tr_08.model.firmware == "1.08"
		assert tr_08.sources["manual"].edition == "eng04"
		assert tr_08.sources["manual_eng03"].edition == "eng03"
		assert tr_08.sources["chart"].page_offset == 0

		said = " ".join(prose_of("roland", "tr_08").split())

		assert "USB and MIDI have been added as MIDI clock sources." in said
		assert "Product specifications are unaffected." in said
		assert "So edition 04 is the manual for 1.07's MIDI settings" in said

	def test_velocity_both_ways_and_neither_bend_nor_aftertouch (self) -> None:
		tr_08 = pymidiinstrumentdefs.load("roland/tr_08", [CORPUS])

		assert tr_08.voice is not None and tr_08.voice.velocity is not None
		assert (tr_08.voice.velocity.note_on, tr_08.voice.velocity.note_off) == ("both", True)
		assert tr_08.voice.aftertouch == "none"
		assert tr_08.voice.pitch_bend is None
		assert tr_08.voice.polyphony is None


class TestMpcLiveIII:

	"""The first MPC Live's answer again, read from a different book that covers two machines.

	**NOTHING HERE IS TAKEN FROM `akai/mpc_live`**: that file was read from the Standalone OS guide,
	which covers ten other machines and sends this one to a guide of its own, read here.
	"""

	def test_it_carries_no_controls_and_the_numbers_are_the_owners_both_ways (self) -> None:
		"""MIDI Learn inward, MIDI Control Mode outward, and both saved with the project."""
		live = pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS])

		assert not live.controls
		assert live.midi.control_change == "learned"

		account = " ".join((live.source or "").split())

		assert "These assignments will be saved with your MPC project." in account
		assert "The edits you make in MIDI Control Mode will be retained with the current MPC " \
			"project." in account

	def test_the_guide_covers_two_machines_and_the_scoping_was_enumerated (self) -> None:
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS]).source or "").split())

		assert "on the second-generation standalone MPC Live III and MPC XL" in account
		assert "THE SCOPING WAS ENUMERATED, NOT SAMPLED." in account

		# The one MIDI-related input the guide withholds from this machine.
		assert "Footswitch 1 & Footswitch 2 (MPC XL only)" in account

	def test_one_unscoped_passage_is_written_for_the_other_machine (self) -> None:
		"""The MMC appendix names sockets and a field this machine's pages do not have."""
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS]).source or "").split())

		assert "connect your MPC’s MIDI Out A to the MIDI input of your external device." in account
		assert "AND ONE UNSCOPED PROCEDURE FITS NEITHER MACHINE AS THE GUIDE DESCRIBES THEM." in account

	def test_three_times_it_says_a_fixed_map_exists_and_four_pages_name_1_and_11 (self) -> None:
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS]).source or "").split())

		assert "the Q-Links are fixed to a selection of MIDI performance controls" in account
		assert "Standard MIDI control change assignments" in account
		assert "Classic MPC (the default MIDI note map of classic MPCs)" in account

		# And the two fixed numbers it does name, 1 and 11, recorded and not carried.
		assert "to control the MIDI CC1 modulation control" in account
		assert "enable Expression messages (MIDI CC #11) from external MIDI controllers" in account
		assert "**So this instrument does answer to two fixed numbers**" in account
		assert "that is a choice rather than a finding" in account

	def test_the_one_list_of_numbers_is_a_filter_and_four_are_not_control_changes (self) -> None:
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS]).source or "").split())

		assert "CC128 Pitchbend CC130 Program Change CC129 Channel Pressure CC131 Aftertouch" \
			in account
		assert "It says which messages a track forwards, not what this instrument does with one." \
			in account

	def test_program_change_both_ways_and_two_ranges_neither_the_protocols (self) -> None:
		live = pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS])

		assert live.midi.program_change is not None
		assert (live.midi.program_change.receives, live.midi.program_change.sends) == (True, True)
		assert live.midi.program_change.presets is None

		account = " ".join((live.source or "").split())

		assert "enter a value from 1–127" in account
		assert "Programs 1–128 can be changed via program change messages." in account

	def test_clock_both_ways_and_aftertouch_and_velocity_left_unset_on_purpose (self) -> None:
		live = pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS])

		assert live.midi.clock == "both"
		assert live.midi.channels == (1, 16)
		assert live.midi.sysex is None and live.midi.nrpn is None
		assert live.voice.polyphony is None
		assert live.voice.aftertouch is None and live.voice.velocity is None
		assert "AFTERTOUCH AND VELOCITY ARE LEFT UNSET, AND NOT BECAUSE NOTHING IS SAID." in " ".join(
			(live.source or "").split())
		assert not live.voice.voices

		assert live.voice.pitch_bend is not None
		assert live.voice.pitch_bend.programmable is True
		assert live.voice.pitch_bend.semitones is None

	def test_two_midi_ports_each_way_and_cv_which_the_first_mpc_live_has_not (self) -> None:
		account = " ".join(
			(pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS]).source or "").split())

		assert "(2) 5-pin MIDI inputs" in account
		assert "(2) 5-pin MIDI outputs" in account
		assert "CV/Gate outputs" in account
		assert "**The CV outputs are a difference from the first MPC Live**" in account

	def test_it_describes_3_9_1_through_the_v3_9_guide (self) -> None:
		live = pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS])

		assert live.model.firmware == "3.9.1"
		assert live.sources["guide"].edition == "v3.9"
		assert live.sources["release_notes"].sha256 == \
			pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).sources["release_notes"].sha256


class TestDrumBrute:

	"""The first DrumBrute: its drum notes are one picture, and its program change is in the
	release notes and in no manual."""

	def test_seventeen_notes_run_unbroken_from_36 (self) -> None:
		"""The run is what checks a transcription made by eye: one note for each of the
		seventeen instruments the manual counts, with no gap and no repeat."""
		drumbrute = pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS])

		assert drumbrute.voice.addressing == "voices"
		assert len(drumbrute.voice.voices) == 17
		assert sorted(drumbrute.voice.voices.values()) == list(range(36, 53))

		# The editor's own order, left to right and top to bottom, is the note order.
		assert list(drumbrute.voice.voices)[:3] == ["kick1", "kick2", "snare"]
		assert list(drumbrute.voice.voices)[-1] == "zap"

		account = " ".join((drumbrute.source or "").split())

		assert "there are actually 17 separate instruments available from the 12 pads" in account

	def test_the_numbers_are_defaults_and_the_drum_map_is_one_picture (self) -> None:
		"""Both editions print it, and version 1.2's is a crop of version 1.0.0's, so the two
		do not corroborate each other."""
		drumbrute = pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS])

		assert drumbrute.voice.note_map == "learned"
		assert drumbrute.sources["manual"].pictured_pages == (73,)
		assert drumbrute.sources["first_manual"].pictured_pages == (70,)

		account = " ".join((drumbrute.source or "").split())

		assert "The settings shown are the default MIDI note number values for each instrument, " \
			"but you can set them to any note number between 0-127." in account
		assert "the two editions do not corroborate each other" in account

	def test_it_publishes_no_controller_number_at_all (self) -> None:
		"""The touch strip and the three transport buttons answer to numbers the player sets."""
		drumbrute = pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS])

		assert drumbrute.controls == {}
		assert drumbrute.midi.control_change == "learned"
		assert drumbrute.midi.nrpn == "none"

		account = " ".join((drumbrute.source or "").split())

		assert "No controller map: DrumBrute, MatrixBrute" in account
		assert "MIDI CC allows you to change Control Change number." in account

	def test_the_transport_numbers_in_the_pictures_are_one_units_settings (self) -> None:
		"""Version 1.0.0 prints the whole window, on firmware older than any Arturia lists.

		**The template the window's title names does not cover them**, which the first
		draft of this definition got wrong and the second reader caught: the manual says a
		template holds no Device Settings, and the transport, the channel and the drum map
		are all Device Settings.
		"""
		account = " ".join(
			(pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS]).source or "").split())

		assert "firmware `0.9.8.0`, older than any version Arturia lists" in account
		assert "\"A Template does not contain the Device Settings.\" (manual p. 56)" in account
		assert "a saved template" not in account.lower()

	def test_program_change_is_received_and_only_the_release_notes_say_so (self) -> None:
		"""Firmware 1.1.0.0 added it, and neither edition of the manual mentions it."""
		drumbrute = pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS])

		assert drumbrute.midi.program_change is not None
		assert drumbrute.midi.program_change.receives is True
		assert drumbrute.midi.program_change.sends is None
		assert drumbrute.midi.program_change.presets == 64

		account = " ".join((drumbrute.source or "").split())

		assert "Use Program Change to switch patterns, and Bank MSB to switch Bank" in account
		assert "Neither edition of the manual names program change, bank select or song select" \
			in account

	def test_clock_both_ways_and_transport_only_out (self) -> None:
		drumbrute = pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS])

		assert drumbrute.midi.clock == "both"
		assert drumbrute.midi.transport == "sends"

	def test_what_no_page_states_is_left_unset (self) -> None:
		"""The channel range is a picture, and no page says what received velocity does."""
		drumbrute = pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS])

		assert drumbrute.midi.channels is None
		assert drumbrute.midi.mode is None
		assert drumbrute.midi.sysex is None
		assert drumbrute.voice.velocity is None
		assert drumbrute.voice.polyphony is None
		assert drumbrute.voice.aftertouch is None
		assert drumbrute.voice.pitch_bend is None

	def test_the_impacts_map_cannot_stand_in_for_this_one (self) -> None:
		"""A different machine: five instruments share a name and none shares a note."""
		drumbrute = pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS])
		impact = pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS])

		shared = set(drumbrute.voice.voices) & set(impact.voice.voices)

		assert shared == {"cl_hat", "op_hat", "tom_h", "tom_l", "cymbal"}
		assert all(drumbrute.voice.voices[name] != impact.voice.voices[name] for name in shared)

		# What the two do share is the shape of the answer.
		assert (drumbrute.midi.control_change, drumbrute.midi.transport, drumbrute.voice.note_map) \
			== (impact.midi.control_change, impact.midi.transport, impact.voice.note_map)

	def test_it_describes_1_2_1_0_through_manual_1_2 (self) -> None:
		drumbrute = pymidiinstrumentdefs.load("arturia/drumbrute", [CORPUS])

		assert drumbrute.model.firmware == "1.2.1.0"
		assert drumbrute.sources["manual"].edition == "1.2"
		assert drumbrute.sources["first_manual"].edition == "1.0.0"

		assert drumbrute.sources["manual"].page_offset == 5
		assert drumbrute.sources["first_manual"].page_offset == 0
		assert drumbrute.sources["mcc_manual"].page_offset == 4
		assert drumbrute.sources["release_notes"].paginated is False
		assert drumbrute.sources["downloads_page"].paginated is False

		# The editor's manual is the very file the DrumBrute Impact holds.
		assert drumbrute.sources["mcc_manual"].sha256 == \
			pymidiinstrumentdefs.load("arturia/drumbrute_impact", [CORPUS]).sources["mcc_manual"].sha256


class TestJD800:

	"""A 1991 Roland read by eye from two scans: three charts, and the one row where they differ."""

	def test_seven_controls_with_the_charts_names_and_directions (self) -> None:
		"""Seven are recognised and four are sent; breath, portamento time and portamento only arrive."""
		jd = pymidiinstrumentdefs.load("roland/jd_800", [CORPUS])

		numbers = {control.cc: control for control in jd.controls.values() if control.cc is not None}

		assert sorted(numbers) == [1, 2, 5, 7, 10, 64, 65]
		assert {cc for cc, control in numbers.items() if control.direction == "receives"} == {2, 5, 65}
		assert {cc for cc, control in numbers.items() if control.direction == "both"} == {1, 7, 10, 64}
		assert numbers[64].label == "Hold 1" and numbers[5].label == "Portamento time"

		# The registered parameters' carriers and the mode messages are not carried.
		assert not {6, 38, 100, 101, 121} & set(numbers)

	def test_pan_is_the_one_row_where_the_single_and_parts_charts_differ (self) -> None:
		"""Only Multi mode's five synth parts receive it, and the prose says why.

		The special part's chart differs from theirs in more than pan, which the first draft
		of this file missed and the second reader caught.
		"""
		account = " ".join((pymidiinstrumentdefs.load("roland/jd_800", [CORPUS]).source or "").split())

		assert "PAN IS THE ONE PLACE THE SINGLE AND PARTS CHARTS DIFFER, AND THE PROSE SAYS WHY." in account
		assert "\"In SINGLE mode, this message is ignored.\" (reference p. 285)" in account
		assert "\"It is not possible to specify overall pan for the Special Part.\" (reference p. 170)" \
			in account

	def test_the_special_parts_chart_is_misprinted_and_read_by_its_remarks (self) -> None:
		account = " ".join((pymidiinstrumentdefs.load("roland/jd_800", [CORPUS]).source or "").split())

		assert "`1, 2, 7, 10, 64, 100, 101, 38, 6, 121`" in account
		assert "the numbers 5 and 65 are not printed" in account

	def test_a_program_change_reaches_128_patches_half_on_a_card (self) -> None:
		jd = pymidiinstrumentdefs.load("roland/jd_800", [CORPUS])

		assert jd.midi.program_change is not None
		assert (jd.midi.program_change.receives, jd.midi.program_change.sends) == (True, True)
		assert jd.midi.program_change.presets == 128

		# And the Reference's own table of the mapping is misprinted where the guide's is not.
		account = " ".join((jd.source or "").split())

		assert "it prints BANK across the top and NUMBER down the side (reference p. 211)" in account
		assert "its sixth row reads `42 42 43` where the guide's reads `41 42 43`" in account

	def test_twenty_four_tones_shared_by_every_part (self) -> None:
		"""A voice is a tone, so a four-tone patch plays six notes."""
		jd = pymidiinstrumentdefs.load("roland/jd_800", [CORPUS])

		assert jd.voice.polyphony == 24
		assert jd.voice.voicing_modes == (6, 8, 12, 24)
		assert jd.voice.polyphony_shared is True
		account = " ".join((jd.source or "").split())

		assert "\"24 (Tones) divided by 4 (Tones per note) equals 6 (notes).\" (guide p. 124)" in account
		assert "\"By turning unneeded Parts off, you can conserve notes for those Parts which are " \
			"sounding.\" (guide p. 137)" in account

	def test_five_synth_parts_and_a_special_part (self) -> None:
		jd = pymidiinstrumentdefs.load("roland/jd_800", [CORPUS])

		assert set(jd.parts) == {"part", "special"}
		assert jd.parts["part"].count == 5 and jd.parts["part"].channel == "assigned"
		assert jd.parts["part"].addressing == "pitches"

		# A tone on each key, chosen by the player, so the special part's addressing is unrecorded.
		assert jd.parts["special"].count == 1 and jd.parts["special"].addressing is None

	def test_the_rest_of_the_chart (self) -> None:
		jd = pymidiinstrumentdefs.load("roland/jd_800", [CORPUS])

		assert jd.midi.channels == (1, 16) and jd.midi.mode == 3
		assert (jd.midi.clock, jd.midi.transport) == ("none", "none")
		assert jd.midi.nrpn == "none" and jd.midi.sysex is True

		assert jd.voice.note_range == (0, 127)
		assert jd.voice.velocity is not None
		assert (jd.voice.velocity.note_on, jd.voice.velocity.note_off) == ("both", True)
		assert jd.voice.aftertouch == "channel"
		assert jd.voice.pitch_bend is not None and jd.voice.pitch_bend.programmable is True
		assert jd.voice.pitch_bend.semitones is None

	def test_both_documents_are_scans_cited_by_sheet (self) -> None:
		"""Chapter folios such as V-53 fit no locator, so every locator is a sheet of the file."""
		jd = pymidiinstrumentdefs.load("roland/jd_800", [CORPUS])

		assert set(jd.sources) == {"reference", "guide", "archive"}
		assert jd.sources["reference"].page_offset == jd.sources["guide"].page_offset == 0
		assert jd.sources["archive"].paginated is False
		assert jd.model.firmware is None

		# The archive the TR-909 and the JUNO-106 cite.
		assert jd.sources["archive"].url == \
			pymidiinstrumentdefs.load("roland/tr_909", [CORPUS]).sources["archive"].url


class TestLMDrum:

	"""A drum machine whose two documents number six controllers differently, and the later one is carried."""

	def test_seventeen_controls_all_received (self) -> None:
		"""The filter cutoff on 74 and a tuning for every drum on 75 to 90, the manual's names."""
		lm = pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS])

		numbers = {control.cc: control for control in lm.controls.values() if control.cc is not None}

		assert sorted(numbers) == list(range(74, 91))
		assert {control.direction for control in numbers.values()} == {"receives"}
		assert numbers[74].label == "Filter Cutoff" and numbers[74].group == "analog_filter"
		assert numbers[75].label == "Bass Drum Tuning" and numbers[90].label == "Claps Tuning"
		assert {numbers[cc].group for cc in range(75, 91)} == {"tune"}

	def test_the_guide_gives_six_of_the_numbers_to_other_drums (self) -> None:
		"""The guide's 75 is the snare and the manual's the bass drum; the account says which wins and why."""
		account = " ".join((pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS]).source or "").split())

		assert "the guide's 75 is \"Snare Tuning\" (guide p. 18)" in account
		assert "\"Enhanced Mode (on (default)/off) – allows tuning on all samples regardless of whether " \
			"they have a dedicated tuning control.\" (manual p. 24)" in account
		# And the sentence in the manual that still describes the old list.
		assert "\"These controls are used to tune the snares, toms and congas and set the hi-hat decay." in account

	def test_sixteen_drum_notes_are_defaults_used_both_ways (self) -> None:
		lm = pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS])

		assert lm.voice.addressing == "voices"
		assert len(lm.voice.voices) == 16
		assert (lm.voice.voices["bass_drum"], lm.voice.voices["snare_drum"], lm.voice.voices["cabasa"]) == (36, 40, 69)

		# Changed in the instrument's own menu, which `roland/tr8s` and `elektron/machinedrum` leave unflagged.
		assert lm.voice.note_map is None
		assert pymidiinstrumentdefs.load("roland/tr8s", [CORPUS]).voice.note_map is None
		assert pymidiinstrumentdefs.load("elektron/machinedrum", [CORPUS]).voice.note_map is None
		account = " ".join((lm.source or "").split())

		assert "Note that the same note is used both for TX and Rx." in account

	def test_each_drum_plays_at_pitch_on_a_channel_of_its_own (self) -> None:
		"""With Chromatic MIDI In on, sixteen parts on channels the player can change."""
		lm = pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS])

		assert set(lm.parts) == {"chromatic"}
		chromatic = lm.parts["chromatic"]

		assert (chromatic.count, chromatic.channel, chromatic.addressing) == (16, "assigned", "pitches")
		assert chromatic.receives == ("notes",)

	def test_the_rest_of_the_midi (self) -> None:
		lm = pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS])

		assert lm.midi.channels == (1, 16)
		assert (lm.midi.clock, lm.midi.transport, lm.midi.program_change) == ("receives", None, None)
		assert lm.midi.sysex is True and lm.midi.nrpn is None and lm.midi.mode is None

		assert lm.voice.velocity is not None and lm.voice.velocity.note_on == "received"
		assert (lm.voice.aftertouch, lm.voice.pitch_bend, lm.voice.polyphony) == (None, None, None)

	def test_the_voice_count_is_given_twice_and_carried_neither_way (self) -> None:
		account = " ".join((pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS]).source or "").split())

		assert "\"Number of voices 15\" (guide p. 68)" in account
		assert "\"With 16-voice architecture\" (product_page)" in account

	def test_the_firmware_is_the_manuals_and_not_the_newest (self) -> None:
		lm = pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS])

		assert lm.model.firmware == "1.1.5"
		assert lm.sources["manual"].edition == "V1.1" and lm.sources["guide"].edition == "V 0.0"
		account = " ".join((lm.source or "").split())

		assert "names `LM DRUM Release Notes 1.1.7`" in account

	def test_the_guide_is_two_pages_to_a_sheet (self) -> None:
		lm = pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS])

		assert set(lm.sources) == {"manual", "guide", "product_page"}
		assert (lm.sources["manual"].page_offset, lm.sources["manual"].pages_per_sheet) == (0, 1)
		assert (lm.sources["guide"].page_offset, lm.sources["guide"].pages_per_sheet) == (1, 2)
		assert lm.sources["guide"].file_page(18) == lm.sources["guide"].file_page(19) == 10
		assert lm.sources["product_page"].paginated is False


class TestRD9:

	"""Eleven drums, ten at once, a start message and a SysEx dump - and no controller named anywhere."""

	def test_eleven_drums_on_eleven_default_notes (self) -> None:
		rd9 = pymidiinstrumentdefs.load("behringer/rd_9", [CORPUS])

		assert rd9.voice.addressing == "voices"
		assert list(rd9.voice.voices.values()) == [36, 38, 45, 47, 50, 37, 39, 49, 51, 46, 42]
		assert rd9.voice.voices["rim_shot"] == 37 and rd9.voice.voices["closed_hat"] == 42

		# Changed on the instrument's own MAP page, as the LM DRUM's are, so unflagged like it.
		assert rd9.voice.note_map is None
		assert pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS]).voice.note_map is None

	def test_ten_sound_at_once (self) -> None:
		"""A count of what sounds at once, stated alike in both documents."""
		rd9 = pymidiinstrumentdefs.load("behringer/rd_9", [CORPUS])

		assert rd9.voice.polyphony == 10
		assert len(rd9.voice.voices) == 11
		account = " ".join((rd9.source or "").split())

		assert "\"Number of simultaneous voices 10\" (manual p. 33)" in account
		# Not a contradiction like the LM DRUM's, which leaves its polyphony out.
		assert pymidiinstrumentdefs.load("behringer/lm_drum", [CORPUS]).voice.polyphony is None

	def test_a_whole_manual_names_no_controller (self) -> None:
		"""A search of every page, the Model D's route to `none` rather than the EDGE's unset field."""
		rd9 = pymidiinstrumentdefs.load("behringer/rd_9", [CORPUS])

		assert rd9.controls == {}
		assert rd9.midi.control_change == "none" and rd9.midi.refuses_control_change
		assert pymidiinstrumentdefs.load("behringer/model_d", [CORPUS]).midi.control_change == "none"
		assert (rd9.midi.program_change, rd9.midi.nrpn) == (None, None)

	def test_clock_and_a_start_message_are_received (self) -> None:
		rd9 = pymidiinstrumentdefs.load("behringer/rd_9", [CORPUS])

		assert (rd9.midi.clock, rd9.midi.transport) == ("receives", "receives")
		assert rd9.midi.channels == (1, 16) and rd9.midi.sysex is True
		assert rd9.voice.velocity is not None and rd9.voice.velocity.note_on == "received"
		account = " ".join((rd9.source or "").split())

		assert "A MIDI start message is required in order for playback to start.\" (manual p. 19)" in account
		# The manual claims to send clock and names no port; the page's copy of that paragraph
		# names the RD-8 once.
		assert "\"The RD-9 can also send and receive clock information with highly accurate timing to sync " \
			"it to the outside world.\" (manual p. 6)" in account
		assert "\"the RD-8 lets you control external synths\" (product_page)" in account

	def test_the_settings_table_slips_a_row (self) -> None:
		account = " ".join((pymidiinstrumentdefs.load("behringer/rd_9", [CORPUS]).source or "").split())

		assert "THE SETTINGS TABLE ON P. 21 SLIPS A ROW." in account
		assert "`USB TX Channel` beside \"Set the USB MIDI receive channel.\" (manual p. 21)" in account

	def test_no_firmware_is_named_and_the_guide_is_two_pages_to_a_sheet (self) -> None:
		rd9 = pymidiinstrumentdefs.load("behringer/rd_9", [CORPUS])

		assert rd9.model.firmware is None
		assert set(rd9.sources) == {"manual", "guide", "product_page"}
		assert (rd9.sources["manual"].page_offset, rd9.sources["manual"].pages_per_sheet) == (0, 1)
		assert (rd9.sources["guide"].page_offset, rd9.sources["guide"].pages_per_sheet) == (1, 2)
		assert rd9.sources["guide"].file_page(51) == 26
		assert rd9.sources["product_page"].paginated is False


class TestMpcXl:

	"""The MPC Live III's book read for the other machine it covers: the same answers, another panel."""

	def test_every_field_is_its_siblings_because_the_book_is_the_same (self) -> None:
		"""One guide, one firmware, one ruling on 1 and 11 - so one set of fields."""
		xl = pymidiinstrumentdefs.load("akai/mpc_xl", [CORPUS])
		live = pymidiinstrumentdefs.load("akai/mpc_live_iii", [CORPUS])

		assert not xl.controls and xl.midi.control_change == "learned"
		assert xl.midi == live.midi
		assert xl.voice == live.voice
		assert xl.model.firmware == live.model.firmware == "3.9.1"
		assert {key: source.sha256 for key, source in xl.sources.items()} == \
			{key: source.sha256 for key, source in live.sources.items()}

	def test_the_one_machine_only_setting_is_its_footswitches (self) -> None:
		account = " ".join((pymidiinstrumentdefs.load("akai/mpc_xl", [CORPUS]).source or "").split())

		assert "THE SCOPING WAS ENUMERATED, NOT SAMPLED." in account
		assert "\"Footswitch 1 & Footswitch 2 (MPC XL only): These determine how connected footswitches " \
			"will work.\" (guide p. 65)" in account

	def test_its_own_ports_four_midi_outputs_and_eight_cv (self) -> None:
		account = " ".join((pymidiinstrumentdefs.load("akai/mpc_xl", [CORPUS]).source or "").split())

		assert "\"(4) 5-pin MIDI outputs\" (guide p. 543)" in account
		assert "\"(2) 5-pin MIDI inputs\" (guide p. 543)" in account
		assert "\"(8) Stereo 1/8” (3.5 mm) CV/Gate outputs\" (guide p. 543)" in account
		assert "This connection allows MPC XL to send and receive MIDI and audio data to and from your " \
			"computer." in account

	def test_the_mmc_appendix_names_its_outputs_and_not_its_inputs (self) -> None:
		"""MIDI Out A fits this machine's A-D; MIDI In A does not fit its 1/2."""
		account = " ".join((pymidiinstrumentdefs.load("akai/mpc_xl", [CORPUS]).source or "").split())

		assert "connect your MPC’s MIDI Out A to the MIDI input of your external device." in account
		assert "connect your MPC’s MIDI In A to the MIDI output of your external device." in account
		assert "where this machine's inputs are `MIDI In 1/2` (guide p. 396)" in account

	def test_1_and_11_are_recorded_and_not_carried_as_in_both_siblings (self) -> None:
		xl = pymidiinstrumentdefs.load("akai/mpc_xl", [CORPUS])
		account = " ".join((xl.source or "").split())

		assert "to control the MIDI CC1 modulation control" in account
		assert "enable Expression messages (MIDI CC #11) from external MIDI controllers" in account
		assert not pymidiinstrumentdefs.load("akai/mpc_live", [CORPUS]).controls
		assert xl.voice.aftertouch is None and xl.voice.velocity is None


class TestJX8P:

	"""A 1985 Roland read by eye from a scan: five controllers behind four function switches."""

	def test_five_controls_with_the_charts_names_and_directions (self) -> None:
		"""Four travel both ways; volume only arrives."""
		jx = pymidiinstrumentdefs.load("roland/jx_8p", [CORPUS])

		numbers = {control.cc: control for control in jx.controls.values() if control.cc is not None}

		assert sorted(numbers) == [1, 5, 7, 64, 65]
		assert {cc for cc, control in numbers.items() if control.direction == "receives"} == {7}
		assert numbers[65].label == "Portamento Switch" and numbers[5].label == "Portamento Time"

		# Hold and portamento switch on at 1, as the implementation prints them, not at 64.
		assert numbers[64].values == numbers[65].values == {"off": 0, "on": 1}

		# No page ties a control to a controller number; the account says which are evident.
		account = " ".join((jx.source or "").split())

		assert "NO PAGE SAYS WHICH CONTROL SENDS WHICH CONTROLLER." in account

	def test_every_controller_is_behind_a_function_switch_that_ships_on (self) -> None:
		account = " ".join((pymidiinstrumentdefs.load("roland/jx_8p", [CORPUS]).source or "").split())

		assert "\"*1 Transmitted if the corresponding function switch is ON.\" (manual p. 28)" in account
		assert "\"*3 Received if the corresponding function switch is ON.\" (manual p. 28)" in account
		assert "Every one is ON from the factory, as are rows 12 to 14 for program change, aftertouch " \
			"and pitch bend (manual p. 25)" in account

		# Four rows for five controllers: the one portamento row would govern both 5 and 65.
		assert "FIVE CONTROLLERS, BEHIND FOUR SWITCHES." in account
		assert "the manual never pairs a row with a message" in account

		# And the table's own footnote says only half of it.
		assert "\"ON = Sent, OFF = Not Sent\" (manual p. 25)" in account

	def test_a_program_change_reaches_128_with_the_last_range_misprinted (self) -> None:
		jx = pymidiinstrumentdefs.load("roland/jx_8p", [CORPUS])

		assert jx.midi.program_change is not None
		assert (jx.midi.program_change.receives, jx.midi.program_change.sends) == (True, True)
		assert jx.midi.program_change.presets == 128

		account = " ".join((jx.source or "").split())

		assert "\"95 - 127 : Preset #2\" (manual p. 28)" in account

	def test_six_voices_and_three_key_modes (self) -> None:
		jx = pymidiinstrumentdefs.load("roland/jx_8p", [CORPUS])

		assert jx.voice.polyphony == 6 and jx.voice.voicing_modes == (1, 3, 6)
		account = " ".join((jx.source or "").split())

		assert "\"6 Voice Synthesizer with Dynamics, After Touch\" (manual p. 27)" in account
		assert "\"the JX-8P becomes 3 voice synthesizer\" (manual p. 9)" in account

	def test_no_mode_because_the_chart_gives_two_and_a_switch_does_not_say (self) -> None:
		"""Mode 1, 3 and memorised; ON from the factory, and no page says which mode ON is."""
		jx = pymidiinstrumentdefs.load("roland/jx_8p", [CORPUS])

		assert jx.midi.mode is None
		account = " ".join((jx.source or "").split())

		assert "\"This sets the JX-8P's mode.\" (manual p. 25)" in account

	def test_the_rest_of_the_chart (self) -> None:
		jx = pymidiinstrumentdefs.load("roland/jx_8p", [CORPUS])

		assert jx.midi.channels == (1, 16)
		assert (jx.midi.clock, jx.midi.transport) == ("none", "none")
		assert jx.midi.nrpn == "none" and jx.midi.sysex is True

		assert jx.voice.note_range == (0, 127)
		assert jx.voice.velocity is not None
		assert (jx.voice.velocity.note_on, jx.voice.velocity.note_off) == ("both", False)
		assert jx.voice.aftertouch == "channel"
		assert jx.voice.pitch_bend is not None and jx.voice.pitch_bend.programmable is True
		assert jx.voice.pitch_bend.semitones is None

	def test_a_scan_cited_by_sheet_from_the_archive (self) -> None:
		"""From sheet 5 to 27 the printed page is the sheet; the implementation prints none."""
		jx = pymidiinstrumentdefs.load("roland/jx_8p", [CORPUS])

		assert set(jx.sources) == {"manual", "archive"}
		assert jx.sources["manual"].page_offset == 0
		assert jx.sources["archive"].paginated is False
		assert jx.model.firmware is None

		# The archive the JD-800, the TR-909 and the JUNO-106 cite.
		assert jx.sources["archive"].url == \
			pymidiinstrumentdefs.load("roland/jd_800", [CORPUS]).sources["archive"].url


class TestJD08:

	"""A Boutique JD-800 whose 85 controllers are in a chart inside its Reference Manual."""

	def test_eighty_five_controls_off_the_part_chart (self) -> None:
		"""63 both ways, 18 received only, and the four palette sliders sent only."""
		jd = pymidiinstrumentdefs.load("roland/jd_08", [CORPUS])

		numbers = {control.cc: control for control in jd.controls.values() if control.cc is not None}

		assert len(numbers) == 85
		directions = [control.direction for control in numbers.values()]
		assert (directions.count("both"), directions.count("receives"), directions.count("transmits")) == \
			(63, 18, 4)
		assert {cc for cc, control in numbers.items() if control.direction == "transmits"} == {68, 69, 70, 71}

		# The chart's own spelling is the label, and 72 is the one controller with a range printed.
		assert numbers[9].label == "TVF RESONANSE"
		assert numbers[72].range == (0, 108)
		assert all(control.range == (0, 127) for cc, control in numbers.items() if cc != 72)

		# No parameter numbers travel, and bank select is the program change's, not a control.
		assert not {0, 6, 32, 38, 98, 99, 100, 101} & set(numbers)

		# Effect B's seven are on the chart for both parts, and can be heard on Part A only.
		account = " ".join((jd.source or "").split())

		assert "\"Effect B is only enabled for PART A.\" (reference p. 36)" in account

	def test_two_parts_and_a_system_channel (self) -> None:
		jd = pymidiinstrumentdefs.load("roland/jd_08", [CORPUS])

		assert set(jd.parts) == {"part", "system"}
		assert jd.parts["part"].count == 2 and jd.parts["part"].channel == "assigned"
		assert jd.parts["part"].receives == ("notes", "controls", "program_change")
		assert jd.parts["system"].receives == ("notes", "program_change")

		account = " ".join((jd.source or "").split())

		assert "\"Selects the step sequencer pattern.\" (reference p. 62)" in account
		assert "\"Transmits/receives between the selected part and the system.\" (reference p. 62)" in account

	def test_program_change_reaches_256_patches_by_bank (self) -> None:
		jd = pymidiinstrumentdefs.load("roland/jd_08", [CORPUS])

		assert jd.midi.program_change is not None
		assert (jd.midi.program_change.receives, jd.midi.program_change.sends) == (True, True)
		assert jd.midi.program_change.presets == 256

		account = " ".join((jd.source or "").split())

		assert "\"letting you save a total of 4 x 8 x 8 = 256 patches.\" (reference p. 15)" in account
		assert "no page maps a number to a group, bank and patch" in account

	def test_the_rest_of_the_chart (self) -> None:
		jd = pymidiinstrumentdefs.load("roland/jd_08", [CORPUS])

		assert jd.midi.channels == (1, 16) and jd.midi.mode == 3
		assert (jd.midi.clock, jd.midi.transport) == ("both", "both")
		assert jd.midi.nrpn == "none" and jd.midi.sysex is False

		assert jd.voice.note_range == (0, 127)
		assert jd.voice.velocity is not None
		assert (jd.voice.velocity.note_on, jd.voice.velocity.note_off) == ("both", False)
		assert jd.voice.aftertouch == "poly"
		assert jd.voice.pitch_bend is not None and jd.voice.pitch_bend.programmable is True
		assert jd.voice.pitch_bend.semitones is None

	def test_what_no_page_says (self) -> None:
		"""No polyphony, no factory channel, and no word on which layer a controller reaches."""
		jd = pymidiinstrumentdefs.load("roland/jd_08", [CORPUS])

		assert jd.voice.polyphony is None and jd.voice.voicing_modes == ()
		account = " ".join((jd.source or "").split())

		assert "NO PAGE SAYS WHICH LAYER A RECEIVED CONTROLLER CHANGES." in account
		assert "No page gives a factory channel for any of the three" in account
		assert "ONE CONTROLLER HAS A RANGE PRINTED IN THE CHART, AND IT DOES NOT FIT ITS LIST." in account

	def test_firmware_and_sources (self) -> None:
		"""1.03 changed nothing but its number, as the TR-08's 1.08 did."""
		jd = pymidiinstrumentdefs.load("roland/jd_08", [CORPUS])

		assert jd.model.firmware == "1.03"
		assert set(jd.sources) == {"reference", "chart_html", "quick_start", "manuals_page", "updates",
			"release_notes"}
		assert jd.sources["reference"].page_offset == 0
		assert jd.sources["chart_html"].paginated is False


class TestJX08:

	"""A Boutique JX-8P whose 49 controllers are in a chart inside its Reference Manual."""

	def test_forty_nine_controls_off_the_part_chart (self) -> None:
		"""42 both ways and 7 received only; nothing is sent only."""
		jx = pymidiinstrumentdefs.load("roland/jx_08", [CORPUS])

		numbers = {control.cc: control for control in jx.controls.values() if control.cc is not None}

		assert len(numbers) == 49
		directions = [control.direction for control in numbers.values()]
		assert (directions.count("both"), directions.count("receives"), directions.count("transmits")) == \
			(42, 7, 0)
		assert {cc for cc, control in numbers.items() if control.direction == "receives"} == \
			{1, 5, 7, 11, 41, 64, 91}

		# The chart's own spelling is the label, and no range is printed for any controller.
		assert numbers[21].label == "DCO-1 ENEV MOD"
		assert all(control.range == (0, 127) for control in numbers.values())

		# No parameter numbers travel, and bank select is the program change's, not a control.
		assert not {0, 6, 10, 32, 38, 98, 99, 100, 101} & set(numbers)

	def test_two_names_printed_twice_are_told_apart_by_number (self) -> None:
		"""The chart prints DCO-1 RANGE on 20 and 47 and PORTAMENTO TIME on 5 and 117."""
		jx = pymidiinstrumentdefs.load("roland/jx_08", [CORPUS])

		assert (jx.controls["dco1_range_20"].cc, jx.controls["dco1_range_47"].cc) == (20, 47)
		assert jx.controls["dco1_range_20"].label == jx.controls["dco1_range_47"].label == "DCO-1 RANGE"
		assert (jx.controls["portamento_time_5"].cc, jx.controls["portamento_time_117"].cc) == (5, 117)
		assert jx.controls["portamento_time_5"].label == jx.controls["portamento_time_117"].label == \
			"PORTAMENTO TIME"
		assert jx.controls["portamento_time_5"].direction == "receives"
		assert jx.controls["portamento_time_117"].direction == "both"

		account = " ".join((jx.source or "").split())

		assert "no row is named for DCO-1's TUNE" in account

	def test_two_parts_and_a_system_channel (self) -> None:
		jx = pymidiinstrumentdefs.load("roland/jx_08", [CORPUS])

		assert set(jx.parts) == {"part", "system"}
		assert jx.parts["part"].count == 2 and jx.parts["part"].channel == "assigned"
		assert jx.parts["part"].receives == ("notes", "controls", "program_change")
		assert jx.parts["system"].receives == ("notes", "program_change")

		account = " ".join((jx.source or "").split())

		assert "\"Selects the step sequencer pattern.\" (reference p. 64)" in account
		assert "\"Transmits/receives between the selected part and the system.\" (reference p. 64)" in account

	def test_program_change_reaches_256_patches_by_bank (self) -> None:
		jx = pymidiinstrumentdefs.load("roland/jx_08", [CORPUS])

		assert jx.midi.program_change is not None
		assert (jx.midi.program_change.receives, jx.midi.program_change.sends) == (True, True)
		assert jx.midi.program_change.presets == 256

		account = " ".join((jx.source or "").split())

		assert "\"letting you save a total of 4 x 8 x 8 = 256 patches.\" (reference p. 16)" in account
		assert "no page maps a number to a group, bank and patch" in account

	def test_the_rest_of_the_chart (self) -> None:
		jx = pymidiinstrumentdefs.load("roland/jx_08", [CORPUS])

		assert jx.midi.channels == (1, 16) and jx.midi.mode == 3
		assert (jx.midi.clock, jx.midi.transport) == ("both", "both")
		assert jx.midi.nrpn == "none" and jx.midi.sysex is False

		assert jx.voice.note_range == (0, 127)
		assert jx.voice.velocity is not None
		assert (jx.voice.velocity.note_on, jx.voice.velocity.note_off) == ("both", False)
		assert jx.voice.aftertouch == "poly"
		assert jx.voice.pitch_bend is not None and jx.voice.pitch_bend.programmable is True
		assert jx.voice.pitch_bend.semitones is None

	def test_what_no_page_says (self) -> None:
		"""No polyphony, no factory channel, and no word on what a value means."""
		jx = pymidiinstrumentdefs.load("roland/jx_08", [CORPUS])

		assert jx.voice.polyphony is None and jx.voice.voicing_modes == ()
		account = " ".join((jx.source or "").split())

		assert "No page gives a factory channel for any of the three" in account
		assert "NO RANGE IS PRINTED FOR ANY CONTROLLER, AND NO PAGE SAYS HOW A VALUE MAPS ONTO ITS " \
			"PARAMETER." in account
		assert "THE ENVELOPE SECTION'S TABLE LEAVES OUT A SLIDER ITS PICTURE SHOWS." in account

	def test_firmware_and_sources (self) -> None:
		"""1.03 changed nothing but its number, and it is the JD-08's own file."""
		jx = pymidiinstrumentdefs.load("roland/jx_08", [CORPUS])
		jd = pymidiinstrumentdefs.load("roland/jd_08", [CORPUS])

		assert jx.model.firmware == jd.model.firmware == "1.03"
		assert set(jx.sources) == {"reference", "chart_html", "quick_start", "manuals_page", "updates",
			"release_notes"}
		assert jx.sources["reference"].page_offset == 0
		assert jx.sources["chart_html"].paginated is False


class TestOPZ:

	"""A web guide whose one table of controller numbers is what the OP-Z receives."""

	def test_fifty_three_controls_every_one_received (self) -> None:
		"""Eighteen parameters twice, absolute and relative, then system, track and ui rows."""
		opz = pymidiinstrumentdefs.load("teenage_engineering/op_z", [CORPUS])

		assert len(opz.controls) == 53
		assert {control.direction for control in opz.controls.values()} == {"receives"}

		absolute = sorted(c.cc for c in opz.controls.values() if c.group == "parameters" and c.cc is not None)
		relative = [c for c in opz.controls.values() if c.group == "parameters_relative"]
		assert absolute == list(range(1, 19))
		assert sorted(c.cc for c in relative if c.cc is not None) == list(range(32, 50))
		assert all(c.choices == {"n1": 1, "n127": 127} for c in relative)

		# Nothing says what a knob sends before the player sets it.
		account = " ".join((opz.source or "").split())

		assert "\"incoming midi table\" (midi)" in account
		assert "no page prints those numbers before the player sets them" in account

	def test_the_channel_column_decides_which_controls_reach_a_track (self) -> None:
		opz = pymidiinstrumentdefs.load("teenage_engineering/op_z", [CORPUS])

		parted = {c.cc for c in opz.controls.values() if c.part == "track"}
		unparted = sorted(c.cc for c in opz.controls.values() if c.part is None and c.cc is not None)

		assert len([c for c in opz.controls.values() if c.part == "track"]) == 44
		assert {50, 51, 53, 54, 60, 61, 62, 63} <= parted
		assert unparted == [52, 55, 56, 57, 102, 102, 103, 103, 103]

		# 103 three times, for three things; 102 twice, on what the table calls channels 0 and 1.
		assert opz.controls["select_pattern"].range == (0, 15)
		assert opz.controls["next_pattern"].choices == {"triggered": 16}
		assert opz.controls["previous_pattern"].choices == {"triggered": 17}
		assert (opz.controls["active_track"].range, opz.controls["parameter_page"].range) == ((0, 15), (0, 3))

	def test_one_part_of_sixteen_tracks_with_no_addressing_and_polyphony_per_track (self) -> None:
		opz = pymidiinstrumentdefs.load("teenage_engineering/op_z", [CORPUS])

		assert set(opz.parts) == {"track"}
		track = opz.parts["track"]
		assert (track.count, track.channel, track.receives) == (16, "assigned", ("notes", "controls"))
		assert opz.voice.polyphony is None and track.polyphony is None
		# Only tracks 5 to 8 play pitches; the drum tracks are kits, so no addressing is claimed.
		assert track.addressing is None and opz.voice.addressing is None

		account = " ".join((opz.source or "").split())

		assert "\"each track in this group has a two note polyphony per step.\" (tracks)" in account
		assert "Note: this doesn't affect the number of notes per step, which is still four.\" (reference)" in account
		assert "\"they are all sample based and consist of 24 different sounds across the musical keyboard.\" (tracks)" \
			in account

	def test_program_change_selects_patterns_both_ways (self) -> None:
		opz = pymidiinstrumentdefs.load("teenage_engineering/op_z", [CORPUS])

		assert opz.midi.program_change is not None
		assert (opz.midi.program_change.receives, opz.midi.program_change.sends) == (True, True)
		assert opz.midi.program_change.presets is None

		account = " ".join((opz.source or "").split())

		assert "\"each of the 10 projects holds 16 pattern.\" (project)" in account

	def test_clock_both_ways_transport_received_and_what_is_not_recorded (self) -> None:
		opz = pymidiinstrumentdefs.load("teenage_engineering/op_z", [CORPUS])

		assert (opz.midi.clock, opz.midi.transport) == ("both", "receives")
		assert opz.midi.nrpn is None and opz.midi.sysex is None and opz.midi.mode is None
		assert opz.voice.velocity is None and opz.voice.aftertouch is None and opz.voice.pitch_bend is None

		account = " ".join((opz.source or "").split())

		assert "\"pass incoming midi start/continue/stop to other ports\" (os_updates)" in account

	def test_firmware_and_sources (self) -> None:
		"""The guide is numbered to the newest OS, 1.2.45."""
		opz = pymidiinstrumentdefs.load("teenage_engineering/op_z", [CORPUS])

		assert (opz.model.manufacturer, opz.model.name, opz.model.firmware) == \
			("teenage engineering", "OP-Z", "1.2.45")
		assert len(opz.sources) == 15
		assert all(source.paginated is False for source in opz.sources.values())
