"""Turning a parsed YAML document into a checked instrument definition.

Checking and building are one walk rather than two, because a validator that
agrees with the reader only by coincidence is worse than no validator.

Every refusal names **the file, the section and the entry**, because that is
what somebody staring at a definition they have just written needs to be told.
Anything that is merely worth knowing — no provenance, an import nobody has
checked — is a warning carried on the definition rather than a refusal.

What is deliberately not an error: an unknown top-level section, an unknown
field inside a known section, an empty file, an absent section, and a null
section.  That is what lets one tool grow a section without breaking another.
"""

import datetime
import pathlib
import re
import typing

import pymididefs.cc

import pymidiinstrumentdefs.definition


# The format version this reader understands.  A file naming any other version
# is refused rather than guessed at, and the refusal says both numbers.
VERSION: typing.Final[int] = 1

# Control names, voice names, and each half of a definition's own name, share
# the grammar the project definition files already use.
NAME: typing.Final[re.Pattern[str]] = re.compile(r"[a-z][a-z0-9_]*")

_ADDRESSING: typing.Final[frozenset[str]] = frozenset({"pitches", "voices", "relative", "none"})

_NOTE_MAPS: typing.Final[frozenset[str]] = frozenset({"fixed", "learned"})

# The channel mode messages, CC 120-127, by the name PyMidiDefs gives each. They
# mean the same on every instrument that has them, so they are specification
# facts, and a definition listing one as a control is duplicating the standard.
_CHANNEL_MODE: typing.Final[dict[int, str]] = {
	pymididefs.cc.ALL_SOUND_OFF: "ALL_SOUND_OFF",
	pymididefs.cc.RESET_ALL_CONTROLLERS: "RESET_ALL_CONTROLLERS",
	pymididefs.cc.LOCAL_CONTROL_ON_OFF: "LOCAL_CONTROL_ON_OFF",
	pymididefs.cc.ALL_NOTES_OFF: "ALL_NOTES_OFF",
	pymididefs.cc.OMNI_MODE_OFF: "OMNI_MODE_OFF",
	pymididefs.cc.OMNI_MODE_ON: "OMNI_MODE_ON",
	pymididefs.cc.MONO_MODE_ON: "MONO_MODE_ON",
	pymididefs.cc.POLY_MODE_ON: "POLY_MODE_ON",
}


class DefinitionError(ValueError):

	"""An instrument definition could not be read, and why."""


class _Reader:

	"""Walks one document, collecting warnings and refusing on the first fault."""

	def __init__ (self, source: str) -> None:

		"""Remember what to call the file in every message it produces."""

		self.source = source
		self.warnings: list[str] = []


	def refuse (self, where: str, problem: str) -> typing.NoReturn:

		"""Stop, naming the file, the section and what is wrong with it."""

		raise DefinitionError(f"{self.source}: {where}: {problem}")


	def warn (self, where: str, problem: str) -> None:

		"""Note something worth saying that is not worth refusing the file over."""

		self.warnings.append(f"{self.source}: {where}: {problem}")


	# ── Typed reads, each refusing with the same shape of message ────────────

	def mapping (self, value: object, where: str) -> dict[str, typing.Any]:

		"""Read a section that must be a mapping.  Absent and null read as empty."""

		if value is None:
			return {}

		if not isinstance(value, dict):
			self.refuse(where, f"expected a mapping, found {type(value).__name__}")

		return value


	def integer (self, value: object, where: str, low: int, high: int) -> int:

		"""Read a whole number in range.

		``True`` is an ``int`` in Python and YAML writes it unquoted, so a bool
		would silently arrive as 1.  It is rejected before the range check.
		"""

		if isinstance(value, bool) or not isinstance(value, int):
			self.refuse(where, f"expected a whole number, found {value!r}")

		if not low <= value <= high:
			self.refuse(where, f"{value} is outside {low}-{high}")

		return value


	def text (self, value: object, where: str) -> str:

		"""Read a field that must be text."""

		if isinstance(value, bool):
			# YAML 1.1 reads bare off, on, yes and no as booleans, so a perfectly
			# reasonable band name silently stops being text. Say so, because the
			# file looks right and the fix is one pair of quotes.
			self.refuse(
				where,
				f"found {value}, not text — YAML reads bare off, on, yes and no as "
				f"true and false. Quote it, as in \"off\".",
			)

		if not isinstance(value, str):
			self.refuse(where, f"expected text, found {type(value).__name__}")

		return value


	def flag (self, value: object, where: str) -> bool:

		"""Read a field that must be true or false."""

		if not isinstance(value, bool):
			self.refuse(where, f"expected true or false, found {value!r}")

		return value


	def stamp (self, section: dict[str, typing.Any], field: str, where: str) -> str | None:

		"""Read a date, written either as text or as a bare YAML date.

		``dated: 2020-02-10`` is the obvious way to write one and YAML hands it
		over as a date object rather than as text, so a file that looks perfectly
		correct would be refused.  Both forms are kept as the text they print as.
		"""

		if field not in section or section[field] is None:
			return None

		written: object = section[field]

		if isinstance(written, (datetime.date, datetime.datetime)):
			return written.isoformat()

		return self.text(written, f"{where}.{field}")


	def name (self, value: object, where: str) -> str:

		"""Read an addressable name, which must be lower case, digits and underscores."""

		text = self.text(value, where)

		if not NAME.fullmatch(text):
			self.refuse(where, f"{text!r} is not a name — use lower case, digits and underscores")

		return text


	def pair (self, value: object, where: str, low: int, high: int) -> tuple[int, int]:

		"""Read an inclusive ``[min, max]`` range."""

		if not isinstance(value, list) or len(value) != 2:
			self.refuse(where, f"expected a [min, max] pair, found {value!r}")

		first = self.integer(value[0], f"{where}[0]", low, high)
		second = self.integer(value[1], f"{where}[1]", low, high)

		if first > second:
			self.refuse(where, f"{first} is above {second}, so the range is empty")

		return first, second


	# ── Sections ─────────────────────────────────────────────────────────────

	def model (self, value: object) -> pymidiinstrumentdefs.definition.Model:

		"""Read ``model``.  Its ``name`` is the only required field in the file."""

		section = self.mapping(value, "model")

		if "name" not in section:
			self.refuse("model", "no name — a definition must say which instrument it is")

		return pymidiinstrumentdefs.definition.Model(
			name         = self.text(section["name"], "model.name"),
			manufacturer = self.optional_text(section, "manufacturer", "model"),
			firmware     = self.optional_text(section, "firmware", "model"),
			revision     = self.optional_text(section, "revision", "model"),
		)


	def optional_text (self, section: dict[str, typing.Any], field: str, where: str) -> str | None:

		"""Read a text field that may simply not be there."""

		if section.get(field) is None:
			return None

		return self.text(section[field], f"{where}.{field}")


	def sources (self, value: object) -> dict[str, pymidiinstrumentdefs.definition.Source]:

		"""Read the documents the facts came from, each under a short name.

		Every field is optional, because a definition written from a manual
		somebody has on paper can still say which manual it was.  What is checked
		is that whatever *is* given has the right shape, so a citation a script
		follows cannot quietly be a number where a name should be.
		"""

		found = {}

		for name, entry in self.mapping(value, "sources").items():
			where = f"sources.{name}"
			fields = self.mapping(entry, where)

			found[self.name(name, "sources")] = pymidiinstrumentdefs.definition.Source(
				kind            = self.optional_text(fields, "kind", where),
				title           = self.optional_text(fields, "title", where),
				edition         = self.optional_text(fields, "edition", where),
				dated           = self.stamp(fields, "dated", where),
				landing         = self.optional_text(fields, "landing", where),
				url             = self.optional_text(fields, "url", where),
				sha256          = self.optional_text(fields, "sha256", where),
				retrieved       = self.stamp(fields, "retrieved", where),
				page_offset     = self.integer(fields["page_offset"], f"{where}.page_offset", -999, 999) if "page_offset" in fields else 0,
				pages_per_sheet = self.integer(fields["pages_per_sheet"], f"{where}.pages_per_sheet", 1, 8) if "pages_per_sheet" in fields else 1,
				paginated       = self.flag(fields["paginated"], f"{where}.paginated") if "paginated" in fields else True,
			)

		return found


	def parts (self, value: object) -> dict[str, pymidiinstrumentdefs.definition.Part]:

		"""Read the separately addressable parts of an instrument, each under a short name.

		Most instruments have none, and an absent section is the ordinary case
		rather than an omission.  What is checked is that a part which *is*
		declared can be addressed: a channel it is given or one it derives, never
		both, because a reader could not tell which to believe.
		"""

		found = {}
		receivable = pymidiinstrumentdefs.definition.RECEIVABLE

		for name, entry in self.mapping(value, "parts").items():
			where = f"parts.{name}"
			fields = self.mapping(entry, where)

			channel = self.optional_text(fields, "channel", where)
			assigned = pymidiinstrumentdefs.definition.ASSIGNED

			if channel is not None and channel != assigned:
				self.refuse(
					f"{where}.channel",
					f"{channel!r} is not {assigned!r} — a part is either given a channel "
					f"or derives one with channel_offset",
				)

			offset = None if fields.get("channel_offset") is None \
				else self.integer(fields["channel_offset"], f"{where}.channel_offset", -15, 15)

			if channel is not None and offset is not None:
				self.refuse(where, "has both channel and channel_offset — a part is given a channel or derives one, not both")

			if channel is None and offset is None:
				self.warn(where, "says neither channel nor channel_offset, so nothing can address it")

			addressing = self.optional_text(fields, "addressing", where)

			if addressing is not None and addressing not in _ADDRESSING:
				self.refuse(f"{where}.addressing", f"{addressing!r} is not one of {sorted(_ADDRESSING)}")

			receives: list[str] = []

			for message in self.sequence(fields.get("receives"), f"{where}.receives"):
				kind = self.text(message, f"{where}.receives")

				if kind not in receivable:
					self.refuse(f"{where}.receives", f"{kind!r} is not one of {sorted(receivable)}")

				if kind in receives:
					self.refuse(f"{where}.receives", f"names {kind!r} twice")

				receives.append(kind)

			found[self.name(name, "parts")] = pymidiinstrumentdefs.definition.Part(
				label          = self.optional_text(fields, "label", where),
				channel        = channel,
				channel_offset = offset,
				count          = self.integer(fields["count"], f"{where}.count", 1, 16) if "count" in fields else 1,
				receives       = tuple(receives),
				addressing     = addressing,
			)

		return found


	def midi (self, value: object) -> pymidiinstrumentdefs.definition.Midi:

		"""Read ``midi``, the rows of the implementation chart.

		``midi: none`` states a checked absence for the whole section — an
		instrument with no MIDI at all, which is a real case and not a
		hypothetical one.
		"""

		if value == "none":
			return pymidiinstrumentdefs.definition.Midi(stated_none = True)

		section = self.mapping(value, "midi")
		program_change = None

		if section.get("program_change") is not None and section["program_change"] != "none":
			inner = self.mapping(section["program_change"], "midi.program_change")
			program_change = pymidiinstrumentdefs.definition.ProgramChange(
				receives = None if inner.get("receives") is None
					else self.flag(inner["receives"], "midi.program_change.receives"),
				sends    = None if inner.get("sends") is None
					else self.flag(inner["sends"], "midi.program_change.sends"),
				presets  = None if inner.get("presets") is None
					else self.integer(inner["presets"], "midi.program_change.presets", 0, 16384),
			)

		return pymidiinstrumentdefs.definition.Midi(
			channels = None if section.get("channels") is None
				else self.pair(section["channels"], "midi.channels", 1, 16),
			mode = None if section.get("mode") is None
				else self.integer(section["mode"], "midi.mode", 1, 4),
			clock              = self.optional_text(section, "clock", "midi"),
			transport          = self.optional_text(section, "transport", "midi"),
			program_change     = program_change,
			control_change     = self.optional_text(section, "control_change", "midi"),
			nrpn               = self.optional_text(section, "nrpn", "midi"),
			sysex = None if section.get("sysex") is None
				else self.flag(section["sysex"], "midi.sysex"),
			per_voice_channels = None if section.get("per_voice_channels") is None
				else self.flag(section["per_voice_channels"], "midi.per_voice_channels"),
		)


	def voice (self, value: object) -> pymidiinstrumentdefs.definition.Voice:

		"""Read ``voice`` — what the instrument sounds and what it answers to."""

		section = self.mapping(value, "voice")
		addressing = self.optional_text(section, "addressing", "voice")

		if addressing is not None and addressing not in _ADDRESSING:
			self.refuse("voice.addressing", f"{addressing!r} is not one of {sorted(_ADDRESSING)}")

		reference_note = None if section.get("reference_note") is None \
			else self.integer(section["reference_note"], "voice.reference_note", 0, 127)

		if addressing == "relative" and reference_note is None:
			self.refuse("voice.reference_note", "absent — a relative instrument has to say which note an offset is from")

		if reference_note is not None and addressing != "relative":
			self.refuse("voice.reference_note", "only means something when addressing is relative")

		note_map = self.optional_text(section, "note_map", "voice")

		if note_map is not None and note_map not in _NOTE_MAPS:
			self.refuse("voice.note_map", f"{note_map!r} is not one of {sorted(_NOTE_MAPS)}")

		voices: dict[str, int] = {}

		for name, note in self.mapping(section.get("voices"), "voice.voices").items():
			key = self.name(name, "voice.voices")
			voices[key] = self.integer(note, f"voice.voices.{key}", 0, 127)

		return pymidiinstrumentdefs.definition.Voice(
			addressing = addressing,
			reference_note = reference_note,
			note_map = note_map,
			note_range = None if section.get("note_range") is None
				else self.pair(section["note_range"], "voice.note_range", 0, 127),
			polyphony = None if section.get("polyphony") is None
				else self.integer(section["polyphony"], "voice.polyphony", 0, 256),
			paraphonic = None if section.get("paraphonic") is None
				else self.flag(section["paraphonic"], "voice.paraphonic"),
			voicing_modes = tuple(
				self.integer(mode, "voice.voicing_modes", 0, 256)
				for mode in self.sequence(section.get("voicing_modes"), "voice.voicing_modes")
			),
			velocity     = self.velocity(section.get("velocity")),
			aftertouch   = self.optional_text(section, "aftertouch", "voice"),
			pitch_bend   = self.pitch_bend(section.get("pitch_bend")),
			voices       = voices,
		)


	def sequence (self, value: object, where: str) -> list[typing.Any]:

		"""Read a list.  Absent and null read as empty."""

		if value is None:
			return []

		if not isinstance(value, list):
			self.refuse(where, f"expected a list, found {type(value).__name__}")

		return value


	def velocity (self, value: object) -> pymidiinstrumentdefs.definition.Velocity | None:

		"""Read ``voice.velocity`` — whether how hard a note was played reaches the sound."""

		if value is None:
			return None

		section = self.mapping(value, "voice.velocity")

		return pymidiinstrumentdefs.definition.Velocity(
			note_on  = self.optional_text(section, "note_on", "voice.velocity"),
			note_off = None if section.get("note_off") is None
				else self.flag(section["note_off"], "voice.velocity.note_off"),
			gated_by = tuple(
				self.name(name, "voice.velocity.gated_by")
				for name in self.sequence(section.get("gated_by"), "voice.velocity.gated_by")
			),
		)


	def pitch_bend (self, value: object) -> pymidiinstrumentdefs.definition.PitchBend | None:

		"""Read ``voice.pitch_bend`` — how far it bends, and whether that is settable."""

		if value is None:
			return None

		section = self.mapping(value, "voice.pitch_bend")

		return pymidiinstrumentdefs.definition.PitchBend(
			semitones = None if section.get("semitones") is None
				else self.integer(section["semitones"], "voice.pitch_bend.semitones", 0, 127),
			programmable = None if section.get("programmable") is None
				else self.flag(section["programmable"], "voice.pitch_bend.programmable"),
		)


	def controls (self, value: object) -> dict[str, pymidiinstrumentdefs.definition.Control]:

		"""Read ``controls`` — the parameter surface, one entry per addressable name."""

		controls: dict[str, pymidiinstrumentdefs.definition.Control] = {}

		for raw_name, body in self.mapping(value, "controls").items():
			name = self.name(raw_name, "controls")
			controls[name] = self.control(name, body)

		return controls


	def control (self, name: str, value: object) -> pymidiinstrumentdefs.definition.Control:

		"""Read one control, and the bands or choices it has if it is stepped."""

		where = f"controls.{name}"
		section = self.mapping(value, where)

		extent = self.pair(section["range"], f"{where}.range", 0, 16383) \
			if section.get("range") is not None else (0, 127)

		kind = self.optional_text(section, "kind", where)

		kinds = pymidiinstrumentdefs.definition.KINDS

		if kind is not None and kind not in kinds:
			self.refuse(f"{where}.kind", f"{kind!r} is not one of {sorted(kinds)}")

		if section.get("values") is not None and section.get("choices") is not None:
			self.refuse(
				where,
				"has both values and choices — a stepped control's numbers are either "
				"where its bands start or the exact values it takes, not both",
			)

		direction = self.optional_text(section, "direction", where) or pymidiinstrumentdefs.definition.BOTH
		directions = pymidiinstrumentdefs.definition.DIRECTIONS

		if direction not in directions:
			self.refuse(f"{where}.direction", f"{direction!r} is not one of {sorted(directions)}")

		if section.get("nrpn_range") is not None and section.get("nrpn") is None:
			self.refuse(f"{where}.nrpn_range", "given without an nrpn for it to apply to")

		control = pymidiinstrumentdefs.definition.Control(
			name  = name,
			label = self.optional_text(section, "label", where) or name.replace("_", " "),
			cc = None if section.get("cc") is None
				else self.integer(section["cc"], f"{where}.cc", 0, 127),
			lsb = None if section.get("lsb") is None
				else self.integer(section["lsb"], f"{where}.lsb", 0, 127),
			nrpn = None if section.get("nrpn") is None
				else self.integer(section["nrpn"], f"{where}.nrpn", 0, 16383),
			values = self.values(section.get("values"), where, extent),
			choices = self.choices(section.get("choices"), where, extent),
			range  = extent,
			nrpn_range = None if section.get("nrpn_range") is None
				else self.pair(section["nrpn_range"], f"{where}.nrpn_range", 0, 16383),
			default = None if section.get("default") is None
				else self.integer(section["default"], f"{where}.default", extent[0], extent[1]),
			step = 1 if section.get("step") is None
				else self.integer(section["step"], f"{where}.step", 1, 16383),
			unit  = self.optional_text(section, "unit", where),
			group = self.optional_text(section, "group", where),
			part = None if section.get("part") is None
				else self.name(section["part"], f"{where}.part"),
			panel_only = False if section.get("panel_only") is None
				else self.flag(section["panel_only"], f"{where}.panel_only"),
			direction = direction,
			kind_override = kind,
		)

		stepped = (pymidiinstrumentdefs.definition.CHOICE, pymidiinstrumentdefs.definition.SWITCH)

		if control.kind_override in stepped and not control.states:
			self.warn(
				where,
				f"is declared a {control.kind_override} with no states, so a panel has nothing "
				f"to offer — name the states, or leave it continuous",
			)

		if control.cc in _CHANNEL_MODE:
			self.refuse(
				f"{where}.cc",
				f"{control.cc} is a channel mode message, pymididefs.cc.{_CHANNEL_MODE[control.cc]}, "
				f"which means the same on every instrument that has it — it belongs in PyMidiDefs, "
				f"not in a definition",
			)

		if control.cc is None and control.nrpn is None:
			self.warn(where, "declares neither cc nor nrpn, so nothing can be sent to it")

		return control


	def values (self, value: object, where: str, extent: tuple[int, int]) -> dict[str, int]:

		"""Read the named bands of a stepped control.

		Each entry names the **lowest** value of its band, which is what manuals
		print and what MIDNAM stores.  Entries must ascend and must not repeat: a
		reader that sorted them silently would turn a typo into a wrong setting,
		and two bands sharing a number cannot both be reachable.
		"""

		named: dict[str, int] = {}
		previous: int | None = None

		for raw_name, raw_value in self.mapping(value, f"{where}.values").items():
			name = self.name(raw_name, f"{where}.values")
			low = self.integer(raw_value, f"{where}.values.{name}", extent[0], extent[1])

			if previous is not None and low == previous:
				self.refuse(f"{where}.values.{name}", f"{low} is already the start of an earlier band")

			if previous is not None and low < previous:
				self.refuse(f"{where}.values.{name}", f"{low} comes after {previous} — bands must ascend")

			named[name] = low
			previous = low

		return named


	def choices (self, value: object, where: str, extent: tuple[int, int]) -> dict[str, int]:

		"""Read the named exact values of an enumerated control.

		Each entry is a number sent exactly as written — ``0 = Base, 1 = Both,
		2 = 8va`` — rather than the low end of a band.  Two names may not share a
		number, because only one of them could ever be read back.
		"""

		named: dict[str, int] = {}

		for raw_name, raw_value in self.mapping(value, f"{where}.choices").items():
			name = self.name(raw_name, f"{where}.choices")
			number = self.integer(raw_value, f"{where}.choices.{name}", extent[0], extent[1])

			if number in named.values():
				self.refuse(f"{where}.choices.{name}", f"{number} is already another choice's value")

			named[name] = number

		return named


def check_name (name: str) -> tuple[str, str]:

	"""Split a definition's name into its maker and its model, refusing one that is not addressable.

	A name is the maker's folder and the model's file, ``moog/matriarch``, and
	it is how a project asks for a definition.  Both halves obey the grammar
	everything else here does, which is also what stops a name reaching outside
	the folder it is looked for in.
	"""

	maker, slash, model = name.partition("/")

	if not slash or not NAME.fullmatch(maker) or not NAME.fullmatch(model):
		raise DefinitionError(
			f"{name!r} is not a definition name — a name is the maker and the model, "
			f"each in lower case, digits and underscores, as in moog/matriarch"
		)

	return maker, model


def check_stem (stem: str, source: str) -> None:

	"""Refuse a file whose own name is not addressable.

	The file's name is the model half of a definition's name, and the folder it
	sits in is the maker half, so it has to obey the same grammar as everything
	else here.
	"""

	if not NAME.fullmatch(stem):
		raise DefinitionError(
			f"{source}: file name: {stem!r} is not a name — use lower case, digits and "
			f"underscores, in a folder named for the maker, as in moog/matriarch.yaml"
		)


def build (
	raw: object,
	*,
	source: str,
	path: pathlib.Path | None = None,
) -> pymidiinstrumentdefs.definition.Definition:

	"""Check a parsed document and return the definition it describes.

	``source`` is what to call the file in any message — a path, usually, since
	whoever has to fix the file needs to know which one it is.
	"""

	reader = _Reader(source)

	if not isinstance(raw, dict):
		reader.refuse("file", f"expected a mapping of sections, found {type(raw).__name__}")

	if "definition" not in raw:
		reader.refuse("definition", f"absent — this reader knows version {VERSION}")

	version = reader.integer(raw["definition"], "definition", 0, 16383)

	if version != VERSION:
		reader.refuse("definition", f"file is version {version}, this reader knows version {VERSION}")

	if "model" not in raw:
		reader.refuse("model", "absent — a definition must say which instrument it is")

	model = reader.model(raw["model"])
	provenance = reader.optional_text(raw, "source", "file")
	documents = reader.sources(raw.get("sources"))
	parts = reader.parts(raw.get("parts"))
	controls = reader.controls(raw.get("controls"))
	voice = reader.voice(raw.get("voice"))

	# Provenance is not required by the parser and is required by the practice:
	# a definition without it is a rumour, and the best public definition of a
	# common synth has been found disagreeing with its own manufacturer.

	if provenance is None:
		reader.warn("source", "no provenance — say which manual and which page these facts came from")
	elif "unverified" in provenance.lower():
		reader.warn("source", "still marked unverified — an import is an on-ramp, not an authority")

	if voice.velocity is not None:
		for gate in voice.velocity.gated_by:
			if gate not in controls:
				reader.refuse(
					"voice.velocity.gated_by",
					f"names {gate!r}, which is not one of this instrument's controls",
				)

	# A control naming a part nothing declares would be addressed on a channel
	# that does not exist, which fails silently on the wire.  Refused for the
	# same reason gated_by is: a name that resolves to nothing is a typo.

	for control in controls.values():
		if control.part is not None and control.part not in parts:
			reader.refuse(
				f"controls.{control.name}.part",
				f"names {control.part!r}, which is not one of this instrument's parts",
			)

	return pymidiinstrumentdefs.definition.Definition(
		version  = version,
		model    = model,
		source   = provenance,
		sources  = documents,
		midi     = reader.midi(raw.get("midi")),
		voice    = voice,
		parts    = parts,
		controls = controls,
		path     = path,
		warnings = tuple(reader.warnings),
		raw      = raw,
	)
