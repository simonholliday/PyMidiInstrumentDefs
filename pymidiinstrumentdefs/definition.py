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
	part: str | None = None
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

	``polyphony_shared`` means something only for an instrument with parts, and
	says whether those parts draw on one pool of voices.  ``True`` is a Digitone,
	whose eight voices are taken by whichever of its four tracks plays next, so
	``polyphony`` is a ceiling across all of them together and not a figure each
	track can count on.  ``False`` is a Streichfett, whose strings and solo
	sections each have voices of their own, stated against each part.  ``None``
	is nobody having recorded it.  How a player divides a shared pool, where the
	instrument lets them, is a setting and belongs to their project.

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
	polyphony_shared: bool | None = None
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


# ── Parts ────────────────────────────────────────────────────────────────────
# Some instruments are several separately addressable things at once: a Digitone
# is four synth tracks, four MIDI tracks and an effects unit, each on its own
# channel, and a Streichfett's solo section answers one channel above its
# strings.  Most instruments are not, and a definition naming no parts has one.

# A part given a channel of its own, rather than deriving one from a base.
ASSIGNED: typing.Final[str] = "assigned"

# What a part answers to on its channel.  Not to be confused with a control's
# `direction`, which says which way one control travels.
NOTES: typing.Final[str] = "notes"
CONTROLS: typing.Final[str] = "controls"
PROGRAM_CHANGE: typing.Final[str] = "program_change"

RECEIVABLE: typing.Final[frozenset[str]] = frozenset({NOTES, CONTROLS, PROGRAM_CHANGE})


@dataclasses.dataclass(frozen=True)
class Part:

	"""One separately addressable channel of an instrument.

	``channel`` is ``assigned`` where the part is given a channel of its own, as
	each of the Digitone's tracks and its effects unit is.  ``channel_offset`` is
	the other shape, where a part's channel is derived from the instrument's base
	channel and cannot be set on its own: a Streichfett's solo section answers one
	channel above its strings section, and a Voce plays three parts on three
	adjacent channels.

	``count`` is how many identical instances there are, so four synth tracks are
	described once rather than four times.  Where a part derives its channel, its
	instances run consecutively from the offset.

	``receives`` is what a consumer reads to know what a part is *for*: which kinds
	of message reach it at all.  It is a list rather than a flag because the cases
	need one — the Voce's three parts each take notes and their own program change
	while its effect controls are global to all three.  ``None`` is nobody having
	recorded it, and an empty tuple is a part recorded as receiving nothing, which
	a consumer may treat differently: offering a note grid a musician can try, or
	knowing not to draw one.  ``addressing`` says how
	notes are read **when** the part takes them, and means nothing when it does not.

	``polyphony`` is how many voices a part has to itself, and it counts **each
	instance**: three parts at eight voices is eight each.  Voices shared across
	parts are stated once, on the instrument, rather than here.
	"""

	label: str | None = None
	channel: str | None = None
	channel_offset: int | None = None
	count: int = 1
	receives: tuple[str, ...] | None = None
	addressing: str | None = None
	polyphony: int | None = None


	@property
	def is_assigned (self) -> bool:

		"""True when this part is given a channel rather than deriving one.

		False for a part that says neither, which nothing can address: offering a
		channel picker for it would claim something nobody recorded.
		"""

		return self.channel == ASSIGNED


	def takes (self, message: str) -> bool:

		"""Whether this part answers to a kind of message — notes, controls, program change.

		A part that says nothing about what it receives answers ``False`` to
		everything, which is honest: nobody recorded it.  Read ``receives`` itself
		to tell that apart from a part recorded as receiving nothing.
		"""

		return self.receives is not None and message in self.receives


	def channel_for (self, base: int, instance: int = 0) -> int | None:

		"""Which MIDI channel one instance of this part sits on, given a base channel.

		``None`` where the part is assigned a channel instead, so a caller asking
		is told the question does not apply rather than handed a number.

		Channels wrap at 16, which is documented behaviour rather than arithmetic
		convenience: a Voce on a base channel of 15 plays its three parts on 15,
		16 and 1.

		A base channel outside 1-16, or an instance this part does not have, is
		refused rather than answered: a plausible channel for a fourth instance of
		a part with three would send to something that does not exist.
		"""

		if not 1 <= base <= 16:
			raise ValueError(f"base channel {base} is outside 1-16")

		if not 0 <= instance < self.count:
			raise ValueError(f"instance {instance} is outside 0-{self.count - 1}, as this part has {self.count}")

		if self.channel_offset is None:
			return None

		return (base - 1 + self.channel_offset + instance) % 16 + 1


# ── Where the facts came from ────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Source:

	"""One document the facts were read from, named so a stranger can fetch it.

	``edition`` and ``dated`` are what the document says about *itself*, which is
	not always what the page serving it says: one maker's MIDI implementation
	states a revision a month earlier than the date printed beside its download.

	``landing`` and ``url`` are both kept because they fail differently.  The
	landing page is what a person can still navigate to next year; the file URL
	is what was actually read, and is often a content-hashed path that names no
	product and will not survive the maker's next site change.

	``page_offset`` is what to add to a printed page number to reach the page of
	the file.  It is data rather than a rule because there is no rule: across the
	manuals here it has been -9, +1, 0, and one that prints two pages to a sheet.
	A document with no pages at all -- a plain-text implementation chart runs to
	numbered sections instead -- says so with ``paginated: false``.
	"""

	kind: str | None = None
	title: str | None = None
	edition: str | None = None
	dated: str | None = None
	landing: str | None = None
	url: str | None = None
	sha256: str | None = None
	retrieved: str | None = None
	page_offset: int = 0
	pages_per_sheet: int = 1
	paginated: bool = True


	def file_page (self, printed: int) -> int | None:

		"""Which page of the file carries a given printed page number.

		``None`` where the document has no pages, so a caller asking the question
		is told the question does not apply rather than given a number.
		"""

		if not self.paginated:
			return None

		return (printed + self.page_offset + self.pages_per_sheet - 1) // self.pages_per_sheet


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
	sources: dict[str, Source] = dataclasses.field(default_factory=dict)
	midi: Midi = dataclasses.field(default_factory=Midi)
	voice: Voice = dataclasses.field(default_factory=Voice)
	parts: dict[str, Part] = dataclasses.field(default_factory=dict)
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


	def controls_by_part (self) -> dict[str, list[Control]]:

		"""The controls collected by the part they belong to, in file order.

		Controls naming no part are collected under the empty string, and that
		means **the instrument's base channel**: where a definition names parts
		there is no single part for them to fall back on.  It is a real case
		rather than a tidy default — a Streichfett's balance, effects and
		performance controls are all of that kind, because its manual prints one
		generic control change and ties none of them to a channel.
		"""

		parts: dict[str, list[Control]] = {}

		for control in self.controls.values():
			parts.setdefault(control.part or "", []).append(control)

		return parts


	def controls_reaching (self, part: str, instance: int = 0) -> list[Control]:

		"""The controls one instance of a part answers to on its channel, in file order.

		A part's own controls, and — for the one instance sitting on the base
		channel, where the part is recorded as receiving controls — the controls
		that name no part, since those are sent on the base channel too.  So a
		Streichfett's strings part gets all nineteen, because its channel *is* the
		base channel and it takes controls there, while its solo part gets none.

		A Voce is why the rule asks what the part receives.  Its three parts start
		on the base channel but take only notes and program change, and its effect
		controls are "global to all three": they stay with the instrument rather
		than being filed under its first part.

		An assigned part gets only its own.  Whether a player happens to put it
		on the base channel is their project's business, not this file's.  A
		control the instrument only transmits is included like any other; read
		``is_sendable`` for which a panel may send.
		"""

		found = self.parts[part]

		if not 0 <= instance < found.count:
			raise ValueError(f"instance {instance} is outside 0-{found.count - 1}, as {part!r} has {found.count}")

		# Offsets wrap at 16 like channels do, so an instance is on the base
		# channel whenever its offset comes round to a whole number of sixteen.

		on_base = found.channel_offset is not None \
			and (found.channel_offset + instance) % 16 == 0 \
			and found.takes(CONTROLS)

		return [
			control for control in self.controls.values()
			if control.part == part or (control.part is None and on_base)
		]


	def panel_first (self) -> list[Control]:

		"""The controls with those the box has no knob for first, then file order.

		Opt-in, and deliberately not the default: the flag is a strong hint and a
		poor rule.  A control that *does* have a knob can still be the one a part
		most wants on glass.
		"""

		return sorted(self.controls.values(), key=lambda control: not control.panel_only)
