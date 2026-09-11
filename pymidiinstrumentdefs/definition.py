"""What an instrument definition says, once it has been read and checked.

These are the shapes a loaded file takes.  They hold **model** facts — what is
true of every unit of one model of instrument, anywhere — as distinct from the
**specification** facts in PyMidiDefs, which are true of all MIDI everywhere,
and from **rig** facts, which belong to one studio and never appear here.

A definition is descriptive and never prescriptive about presentation.  It says
a control accepts three named states; it does not say to draw a segmented
control.  Deciding that is the consuming page's business, and a definition that
names a widget has become a layout file and stops being shareable.

Source: the instrument definition file format, version 1.
"""

import dataclasses
import pathlib
import typing


# ── Control kinds ────────────────────────────────────────────────────────────
# What an instrument accepts for a control, derived from how many named values
# it has.  These are value shapes, not widgets.

CONTINUOUS: typing.Final[str] = "continuous"
SWITCH: typing.Final[str] = "switch"
CHOICE: typing.Final[str] = "choice"

# Every kind a definition may name.
KINDS: typing.Final[frozenset[str]] = frozenset({CONTINUOUS, SWITCH, CHOICE})


# ── Directions ───────────────────────────────────────────────────────────────
# Which way a control travels, from the instrument's side, as the two columns of
# a MIDI implementation chart have always said.  Most go both ways; a control
# the instrument only transmits is one a panel must never offer to send.

BOTH: typing.Final[str] = "both"
TRANSMITS: typing.Final[str] = "transmits"
RECEIVES: typing.Final[str] = "receives"

DIRECTIONS: typing.Final[frozenset[str]] = frozenset({BOTH, TRANSMITS, RECEIVES})


# ── Identity ─────────────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Model:

	"""Which instrument this is.  Only the name is required."""

	name: str
	manufacturer: str | None = None
	firmware: str | None = None
	revision: str | None = None


	def __str__ (self) -> str:

		"""The instrument as a person would name it."""

		return f"{self.manufacturer} {self.name}" if self.manufacturer else self.name


# ── The parameter surface ────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Control:

	"""One parameter of the instrument, and how to address it.

	``values`` names the bands a stepped control has, each entry giving the
	**lowest** value of its band; a band runs to the next entry's value minus
	one, and the last runs to the top of ``range``.  That is how manuals print
	them and how MIDNAM stores them, so nothing has to be converted on the way
	in.  The arithmetic of turning a band into a number to send is this class's
	job, not the file's.

	``choices`` is the other shape a stepped control can take: named values sent
	exactly as written, for a manual that prints ``0 = Base, 1 = Both, 2 = 8va``
	and means 0, 1 and 2.  A control has one or the other, never both.

	``nrpn_range`` is the value range over NRPN where it differs from ``range``,
	for an instrument that offers finer resolution one way than the other.
	``direction`` says which way the control travels, and one the instrument
	only transmits must never be offered as something to send.
	"""

	name: str
	label: str
	cc: int | None = None
	lsb: int | None = None
	nrpn: int | None = None
	values: dict[str, int] = dataclasses.field(default_factory=dict)
	choices: dict[str, int] = dataclasses.field(default_factory=dict)
	range: tuple[int, int] = (0, 127)
	nrpn_range: tuple[int, int] | None = None
	default: int | None = None
	step: int = 1
	unit: str | None = None
	group: str | None = None
	panel_only: bool = False
	direction: str = BOTH
	kind_override: str | None = None


	@property
	def kind (self) -> str:

		"""Whether this control is continuous, a switch, or a choice of states.

		Derived from the number of named values, so the file never has to keep a
		declared kind in step with its own data.  A definition may override it.
		"""

		if self.kind_override is not None:
			return self.kind_override

		if not self.states:
			return CONTINUOUS

		return SWITCH if len(self.states) == 2 else CHOICE


	@property
	def is_14_bit (self) -> bool:

		"""True when this control has a fine half as well as a coarse one.

		Sending the coarse number on its own is still a legal 7-bit message.
		"""

		return self.lsb is not None


	@property
	def states (self) -> list[str]:

		"""The names of the states this control offers, in order, whichever shape they take."""

		return list(self.values or self.choices)


	@property
	def is_sendable (self) -> bool:

		"""False for a control the instrument transmits and does not recognise."""

		return self.direction != TRANSMITS


	def band (self, name: str) -> tuple[int, int]:

		"""The inclusive range of values that mean ``name``.

		A choice is one exact value, so its band is that value alone.  Raises
		``KeyError`` if this control has no such named state.
		"""

		if name in self.choices:
			return self.choices[name], self.choices[name]

		if name not in self.values:
			raise KeyError(f"{self.name} has no value named {name!r}")

		ordered = list(self.values.values())
		low = self.values[name]
		position = ordered.index(low)

		high = ordered[position + 1] - 1 if position + 1 < len(ordered) else self.range[1]

		return low, high


	def value_for (self, name: str) -> int:

		"""The number to send to put this control into the state called ``name``.

		For a band, the middle rather than the edge, so a value that drifts by
		one does not silently become a different setting.  For a choice, exactly
		the value the manual prints, because any other number means nothing.
		"""

		low, high = self.band(name)

		return (low + high) // 2


	def name_for (self, value: int) -> str | None:

		"""Which named state ``value`` falls in, or None if this control has none.

		A choice matches only its exact value.  A number between two choices
		means nothing on the instrument, so it names nothing here.
		"""

		if self.choices:
			return next((name for name, number in self.choices.items() if number == value), None)

		found = None

		for name, low in self.values.items():
			if value >= low:
				found = name

		return found


# ── What it will play ────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Velocity:

	"""How the instrument treats how hard a note was played.

	``note_on`` is ``ignored``, ``received``, or ``gated`` — the last meaning it
	arrives but is inaudible unless something else is turned up, in which case
	``gated_by`` names the controls that do the gating.  A panel can use that to
	explain a velocity lane that appears to do nothing.
	"""

	note_on: str | None = None
	note_off: bool | None = None
	gated_by: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class PitchBend:

	"""How far the instrument bends, and whether that is settable."""

	semitones: int | None = None
	programmable: bool | None = None


@dataclasses.dataclass(frozen=True)
class Voice:

	"""What the instrument sounds, and what it will answer to.

	``polyphony`` is a count and not a flag: ``1`` is monophonic, ``None`` means
	nobody has established it, which is honest and different from unstated.
	Where voicing is a setting, ``voicing_modes`` lists what it can be and
	``polyphony`` names the default.

	``addressing`` is ``relative`` for an instrument that reads a note as an
	offset from ``reference_note`` rather than as a pitch.  ``note_map`` is
	``learned`` where notes are assigned by MIDI learn, in which case any
	``voices`` given are the factory defaults rather than fixed facts.
	"""

	addressing: str | None = None
	reference_note: int | None = None
	note_map: str | None = None
	note_range: tuple[int, int] | None = None
	polyphony: int | None = None
	paraphonic: bool | None = None
	voicing_modes: tuple[int, ...] = ()
	velocity: Velocity | None = None
	aftertouch: str | None = None
	pitch_bend: PitchBend | None = None
	voices: dict[str, int] = dataclasses.field(default_factory=dict)


	def plays_note (self, note: int) -> bool:

		"""Whether this instrument would sound the given note number.

		A note outside the range is **silent** rather than wrong-sounding, which
		is why a panel wants to mark it rather than let a player wonder.  With no
		stated range, every note in 0-127 is assumed playable.
		"""

		if self.note_range is None:
			return 0 <= note <= 127

		low, high = self.note_range

		return low <= note <= high


# ── What it answers to ───────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class ProgramChange:

	"""Whether the instrument changes preset over MIDI, and how many it has."""

	receives: bool | None = None
	sends: bool | None = None
	presets: int | None = None


@dataclasses.dataclass(frozen=True)
class Midi:

	"""The rows of the instrument's MIDI implementation chart.

	``stated_none`` is set when the file says ``midi: none`` — a checked absence
	rather than an unread page, which is the distinction the whole format turns
	on.  The DFAM is the real case: a 44-page manual in which the word "MIDI"
	never appears.
	"""

	stated_none: bool = False
	channels: tuple[int, int] | None = None
	mode: int | None = None
	clock: str | None = None
	transport: str | None = None
	program_change: ProgramChange | None = None
	control_change: str | None = None
	nrpn: str | None = None
	sysex: bool | None = None
	per_voice_channels: bool | None = None


	@property
	def refuses_control_change (self) -> bool:

		"""True when somebody checked and the instrument answers to no controller.

		Distinct from silence, which only means nobody looked.
		"""

		return self.stated_none or self.control_change == "none"


	@property
	def learns_control_change (self) -> bool:

		"""True when the instrument answers to control changes assigned by MIDI learn.

		There is no factory map to publish, so there are no controls, and that
		is neither an unread page nor a checked absence: it is by design.
		"""

		return self.control_change == "learned"


# ── The whole document ───────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Definition:

	"""One instrument definition, read and checked.

	``warnings`` carries what the validator thought worth saying but not worth
	refusing the file over — most often that provenance is missing, or that an
	import has not yet been checked by a person.
	"""

	version: int
	model: Model
	source: str | None = None
	midi: Midi = dataclasses.field(default_factory=Midi)
	voice: Voice = dataclasses.field(default_factory=Voice)
	controls: dict[str, Control] = dataclasses.field(default_factory=dict)
	path: pathlib.Path | None = None
	warnings: tuple[str, ...] = ()
	raw: dict[str, typing.Any] = dataclasses.field(default_factory=dict)


	@property
	def is_unverified (self) -> bool:

		"""True when this came from an importer and no person has checked it yet.

		An import is an on-ramp, never an authority: the best public definition
		of a common synth can disagree with its own manufacturer's manual.
		"""

		return self.source is not None and "unverified" in self.source.lower()


	def grouped_controls (self) -> dict[str, list[Control]]:

		"""The controls collected by their group, in file order.

		Controls naming no group are collected under the empty string.  A page
		that does not care about groups can ignore this and read ``controls``,
		which is the flat list it would have had anyway.
		"""

		groups: dict[str, list[Control]] = {}

		for control in self.controls.values():
			groups.setdefault(control.group or "", []).append(control)

		return groups


	def panel_first (self) -> list[Control]:

		"""The controls with those the box has no knob for first, then file order.

		Opt-in, and deliberately not the default: the flag is a strong hint and a
		poor rule.  A control that *does* have a knob can still be the one a part
		most wants on glass.
		"""

		return sorted(self.controls.values(), key=lambda control: not control.panel_only)
