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

# A controller number the maker publishes and then says the instrument neither
# sends nor answers to.  Carried rather than left out, because an absent row
# reads exactly like one nobody looked at, and this one tells somebody building
# a control map not to bother.
NEITHER: typing.Final[str] = "none"

DIRECTIONS: typing.Final[frozenset[str]] = frozenset({BOTH, TRANSMITS, RECEIVES, NEITHER})


# ── Identity ─────────────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Model:

	"""Which instrument this is.  Only the name is required.

	``firmware`` is **the firmware this definition describes**, spelled as the maker
	spells it, because what an instrument answers to changes when it is updated: a
	Minitaur before 2.1 ignores a note above its top octave, and from 2.1 sounds the
	equivalent pitch instead.  A definition that does not say is quietly describing
	two different instruments.  ``none`` says the model has no firmware at all, which
	is established rather than assumed, and absent means nobody recorded it.

	``revision`` is a **hardware** revision, where the maker sells one as a distinct
	thing: a Vermona DRM1 MkIV is not a MkIII, and the facts differ.
	"""

	name: str
	manufacturer: str | None = None
	firmware: str | None = None
	revision: str | None = None


	@property
	def states_no_firmware (self) -> bool:

		"""True when somebody established that this model has no firmware at all.

		Distinct from silence, which only means nobody looked - the same
		distinction ``midi: none`` keeps.
		"""

		return self.firmware == "none"


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

	``range_known`` is false where the file says ``range: unknown``: the maker's
	documents do not establish what values the control takes, because they print
	none or print two that cannot both be true.  ``range`` is then the widest the
	message can carry: 0-127 for a controller, and 0-16383 for a controller with a
	fine half or a control reached only by NRPN.  That is so everything the
	instrument might take can still be sent; it is not a claim about the
	instrument, and a panel that draws a slider from it should say so, or not draw
	one.  The flag is said of ``range`` alone: a control with a controller number
	and an NRPN may state ``nrpn_range`` beside it, which is then known, and where
	it states none nothing is made up for it.  A control that states no range at
	all is a different thing, and is 0-127 as it always was.

	``direction`` says which way the control travels, and one the instrument
	only transmits must never be offered as something to send.  Nor must one
	whose direction is ``none``: a number its maker published and then said the
	instrument does nothing with, either way.

	``assignment`` says what the owner can change about the control, where
	anything: ``default`` is a factory assignment the owner can move to another
	number, ``slot`` is a fixed number whose destination the owner picks, and
	``off`` is the maker's recommended assignment, switched off until the owner
	enables it.  ``None`` is a number the maker fixes.  A panel can label a fixed
	number by its parameter and say of the others where the instrument starts.
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
	assignment: str | None = None
	kind_override: str | None = None
	range_known: bool = True


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

		"""False for a control the instrument does not recognise: one it only transmits, or one it ignores both ways."""

		return self.direction not in (TRANSMITS, NEITHER)


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

	``note_on`` is ``received``, ``both`` (received, and sent as well),
	``ignored``, or ``gated``: the last meaning it arrives but is inaudible as the
	instrument ships, until something else is changed; ``gated_by`` names the
	controls that do the gating.  A panel can use that to explain a velocity lane
	that appears to do nothing.  Any other word is refused.

	``transmits`` is whether the instrument **sends** velocity, apart from what it
	does with velocity it is sent.  A MicroBrute is the case: its keys send
	velocity to everything else and it answers to none, so its ``note_on`` is
	``ignored`` and ``transmits`` is true.  ``both`` already says sent as well, so
	beside it ``transmits`` may only agree.  ``None`` is nobody having recorded it.
	"""

	note_on: str | None = None
	note_off: bool | None = None
	gated_by: tuple[str, ...] = ()
	transmits: bool | None = None


@dataclasses.dataclass(frozen=True)
class PitchBend:

	"""How far the instrument bends, and whether that is settable."""

	semitones: int | None = None
	programmable: bool | None = None


@dataclasses.dataclass(frozen=True)
class SentMap:

	"""The note numbers an instrument sends for its voices, under one setting.

	``voices`` is what each voice **answers to**.  What the instrument **sends**
	for a voice is another fact, and where a setting chooses between sets of
	numbers it is more than one.  A TR-707 sends each of its fifteen voices on one
	number from Setting A or from Setting B, and thirteen of the fifteen differ
	between the two.

	``label`` is the setting's name as the maker prints it.  ``factory`` marks the
	setting a document says the instrument ships in, on one map at most.  ``notes``
	gives a voice's number under this setting, by the names ``voices`` uses, and
	need not name every voice.
	"""

	label: str | None = None
	factory: bool = False
	notes: dict[str, int] = dataclasses.field(default_factory=dict)


def _every_note (voices: dict[str, int], voice_notes: dict[str, tuple[int, ...]]) -> dict[str, tuple[int, ...]]:

	"""Every number each voice answers to, the first being the one ``voices`` gives it.

	A map built from ``voices`` alone, as the MIDNAM importer builds one, gets each
	voice its one number.  Numbers that disagree with ``voices`` are refused: whichever
	attribute a program reads, it has to find the same voices and the same first number.
	"""

	for name, notes in voice_notes.items():
		if name not in voices or not notes or notes[0] != voices[name]:
			raise ValueError(f"voice_notes[{name!r}] has to begin with the number voices gives {name!r}")

	return {name: voice_notes.get(name, (note,)) for name, note in voices.items()}


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

	``addressing`` says how a note's number is read: ``pitches``, ``voices``
	through the ``voices`` map, ``relative`` for an instrument that reads a note
	as an offset from ``reference_note``, ``any`` for one that takes notes and
	reads nothing from their number, and ``none`` for one that answers to no
	notes at all.  The last two want opposite things from a panel: a volca drum
	as it ships sounds the part whose channel carried the note whatever its number, so
	every key of a grid does the same thing, while a DFAM should get no grid.  ``note_map`` is
	``learned`` where the owner assigns the notes, by MIDI learn or by setting them in a
	menu, in which case any ``voices`` given are the factory defaults rather than fixed facts.

	``voices`` gives each named voice the note number to send for it, and
	``voice_notes`` every number the voice answers to, that one first.  A TR-08's
	bass drum answers to 36 and to 35, so ``voices`` has 36 for it and
	``voice_notes`` has ``(36, 35)``; a voice with one number has a tuple of one.

	``voices_sent`` is what the instrument itself sends for its voices: a
	``SentMap`` for each setting an owner can choose, under a short name, and one
	entry where there is no setting.  Empty is nobody having recorded what it sends,
	which is not the same as sending the numbers it answers to.

	``aftertouch`` says which kind of aftertouch the instrument answers to:
	``channel``, ``poly``, ``both`` (both kinds, even where a setting picks which
	one reaches the sound, since the setting is the player's and the model answers
	to either), ``received`` (it answers to aftertouch and no document says which
	kind) or ``none``.  Any other word is refused.  ``aftertouch_transmits`` is
	whether it **sends** aftertouch, apart from what it does with aftertouch it is
	sent, as ``Velocity.transmits`` is for velocity: a Yamaha DX7's MIDI data format
	has aftertouch among what it transmits and not among what it receives, so it
	records ``none`` and true.
	Which kind it sends has no field.  ``None`` is nobody having recorded it.
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
	aftertouch_transmits: bool | None = None
	pitch_bend: PitchBend | None = None
	voices: dict[str, int] = dataclasses.field(default_factory=dict)
	voice_notes: dict[str, tuple[int, ...]] = dataclasses.field(default_factory=dict)
	voices_sent: dict[str, SentMap] = dataclasses.field(default_factory=dict)


	def __post_init__ (self) -> None:

		"""Give every voice its numbers, so ``voice_notes`` names each voice that ``voices`` does."""

		object.__setattr__(self, "voice_notes", _every_note(self.voices, self.voice_notes))


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

	``clock`` and ``transport`` say which way each goes, from the instrument's
	side: ``receives``, ``sends``, ``both`` or ``none``.  Any other word is
	refused, ``transmits`` among them, since that is a control's word for its
	direction and is not what these fields have ever said.

	``mpe`` says whether the instrument takes part in MIDI Polyphonic Expression
	at all, and which way: ``receives``, ``sends``, ``both`` or ``none``, the words
	``clock`` uses.  ``per_voice_channels`` keeps its narrower meaning, that the
	voices take a channel each.  The two come apart on a Cascadia, which answers
	to MPE with one voice, so it receives MPE and has no voices to spread.

	``mode`` is the chart's Mode row, 1 to 4, as the default both ways.  Where
	the chart gives a different default each way - a JUNO-106 recognises mode 1
	and announces mode 3 - ``mode`` is ``None`` and ``mode_receives`` and
	``mode_sends`` give each.  Those two are filled for a single figure as well,
	so a consumer that cares about one direction reads that one and needs no
	special case.
	"""

	stated_none: bool = False
	channels: tuple[int, int] | None = None
	mode: int | None = None
	mode_receives: int | None = None
	mode_sends: int | None = None
	clock: str | None = None
	transport: str | None = None
	program_change: ProgramChange | None = None
	control_change: str | None = None
	nrpn: str | None = None
	sysex: bool | None = None
	per_voice_channels: bool | None = None
	mpe: str | None = None


	@property
	def refuses_control_change (self) -> bool:

		"""True when somebody checked and the instrument answers to no controller.

		Distinct from silence, which only means nobody looked.
		"""

		return self.stated_none or self.control_change == "none"


	@property
	def learns_control_change (self) -> bool:

		"""True when some of the instrument's controller numbers are its owner's to assign.

		By MIDI learn or by setting a number in a menu: either way the number is the
		owner's, and no file can publish it.  **The file may carry controls all the
		same.**  Those are the numbers the maker fixes, or the ones it prints as what
		the instrument ships sending, and ``learned`` says the rest is the owner's.
		Waldorf's Iridiums have fifteen or sixteen numbers their maker fixes, most of
		them modulation sources, and map everything else by learning; a MONTAGE
		prints the number each of its physical controllers ships on, and every one
		can be moved.  Which way a number travels is not what the word says: a D-50's
		are the ones its pedals send.  A
		file with no controls and this word has no factory map at all, which is
		neither an unread page nor a checked absence.
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
class Mode:

	"""One named state of the whole instrument, chosen by a setting.

	In a mode a different map, a different set of parts or a different channel
	layout holds: a drumlogue answers on one channel as it ships, and across
	consecutive channels when a global setting says so.  A part naming a mode
	exists only in it; a part naming none exists in every mode, as every part
	did before modes existed.

	``factory`` is true on the one mode a document says the instrument ships
	in, and never inferred: a state entered by holding a button at power-on is
	not thereby the other one's default.

	``unparted`` says whether the controls that name no part, the instrument's
	own map on its base channel, answer in this mode.  True unless a file says
	otherwise.

	``channels`` is the range the base channel can be set to while this mode
	holds, where that differs from ``midi.channels``: a volca drum's six parts sit
	on channels 1 to 6 and cannot move, and on its single channel the owner picks
	any of 1 to 16.  ``None`` is the instrument's own range.  Ask
	``Definition.channels_in()`` and it answers for either.
	"""

	label: str | None = None
	factory: bool = False
	unparted: bool = True
	channels: tuple[int, int] | None = None


@dataclasses.dataclass(frozen=True)
class Part:

	"""One separately addressable part of an instrument, on a channel or within one.

	``channel`` is ``assigned`` where the part is given a channel of its own, as
	each of the Digitone's tracks and its effects unit is.  ``channel_offset`` is
	the other shape, where a part's channel is derived from the instrument's base
	channel and cannot be set on its own: a Streichfett's solo section answers one
	channel above its strings section, and a Voce plays three parts on three
	adjacent channels.

	``fixed_channel`` is a third, for a part on a channel no setting moves,
	whatever the base channel is: a JD-Xi's drum part is on channel 10.  The file
	gives the number in ``channel``, and ``channel`` is then ``None`` here.

	``follows_base`` is said of an assigned part that starts on the base channel,
	until its owner gives it a channel of its own: each of a Korg wavestate's
	Layers has a setting, on by default, that puts it on the Global Channel until
	its owner turns it off.  It is said only where a page says the part starts
	there.

	``count`` is how many identical instances there are, so four synth tracks are
	described once rather than four times.  Where a part derives its channel, its
	instances run consecutively from the offset, and on a fixed channel they run
	up from its number.

	``receives`` is what a consumer reads to know what a part is *for*: which kinds
	of message reach it at all.  It is a list rather than a flag because the cases
	need one — the Voce's three parts each take notes and their own program change
	while its effect controls are global to all three.  ``None`` is nobody having
	recorded it, and an empty tuple is a part recorded as receiving nothing, which
	a consumer may treat differently: offering a note grid a musician can try, or
	knowing not to draw one.  ``addressing`` says how
	notes are read **when** the part takes them, and means nothing when it does not.

	``unrecorded`` is the third answer, for a kind of message the instrument does
	not ignore and that this file cannot tell a program how to send to the part.
	There are two cases, opposite in what is known.  The kind arrives where the part
	sits and no document says whether or how it reaches this part: a volca drum on
	its single channel receives notes there, and no page says which of its six parts
	a note sounds.  Or the kind does reach the part, by a route the documents give
	and this format has no place for: a Tracker's selected instrument is played on a
	channel that has a setting of its own, apart from the setting for the channel
	its controls arrive on, and a part has one channel.  Left out of ``receives``
	alone, that kind reads as one the part does not take, which is not what the
	documents say.  ``takes()`` answers ``None`` for it.

	``polyphony`` is how many voices a part has to itself, and it counts **each
	instance**: three parts at eight voices is eight each.  Voices shared across
	parts are stated once, on the instrument, rather than here.

	``polyphony_shared`` true says the figure is the instances' **together**
	instead: a JD-XA's four digital parts have 64 voices between them, while each
	of its four analogue parts has one of its own.  It says nothing about how the
	instances divide the figure, which no page of that instrument says either.

	``voices`` is a part's own name-to-note map, as ``Voice.voices`` is the
	instrument's, for notes that reach this part and each do one named thing.  A
	note here need not sound: an MC-707's control channel works sixteen Scatter
	pads with notes 60 to 75, and a Digitone II's effects channel taps the tempo
	with one note.  ``note_map`` says of that map what ``Voice.note_map`` says of
	the instrument's: ``learned`` where the owner assigns the notes, so that the
	``voices`` given are where the part starts and not fixed facts, as a RADIAS's
	sixteen kit instruments sit on C2 to D#3 in every factory kit and each can be
	moved.  ``fixed`` is the maker's map and no setting changes it, and ``None`` is
	nobody having recorded which.

	``voice_notes`` and ``voices_sent`` are a part's as they are the instrument's:
	every number each of its voices answers to, the one in ``voices`` first, and
	the numbers the instrument sends for those voices under each setting.

	``mode`` names the one mode this part exists in, and ``None`` is every mode.

	``nrpn_msb`` addresses a part's instances by NRPN MSB rather than by
	channel: the first instance takes ``nrpn_msb`` and each next instance the
	next MSB, as ``channel_offset`` counts channels.  A control on such a part
	gives its ``nrpn`` as the first instance's number, as the document prints it.

	``within`` names another part whose channel each instance shares, as a
	Tonverk's eight subtracks sit inside an audio track running its Subtracks
	machine.  Such a part takes no channel or offset of its own: the part it
	names gives it, and ``count`` is how many sit inside each of that part's
	instances.
	"""

	label: str | None = None
	channel: str | None = None
	channel_offset: int | None = None
	count: int = 1
	receives: tuple[str, ...] | None = None
	addressing: str | None = None
	polyphony: int | None = None
	polyphony_shared: bool | None = None
	voices: dict[str, int] = dataclasses.field(default_factory=dict)
	mode: str | None = None
	nrpn_msb: int | None = None
	within: str | None = None
	unrecorded: tuple[str, ...] = ()
	note_map: str | None = None
	voice_notes: dict[str, tuple[int, ...]] = dataclasses.field(default_factory=dict)
	voices_sent: dict[str, SentMap] = dataclasses.field(default_factory=dict)
	fixed_channel: int | None = None
	follows_base: bool = False


	def __post_init__ (self) -> None:

		"""Give every voice its numbers, so ``voice_notes`` names each voice that ``voices`` does."""

		object.__setattr__(self, "voice_notes", _every_note(self.voices, self.voice_notes))


	@property
	def is_assigned (self) -> bool:

		"""True when this part is given a channel rather than deriving one.

		False for a part that says neither, which nothing can address: offering a
		channel picker for it would claim something nobody recorded.  False too
		for a part ``within`` another, which takes that part's channel, and for a
		part on a fixed channel, where there is nothing to choose.  True for a
		part that ``follows_base``, since its owner can give it a channel.
		"""

		return self.channel == ASSIGNED


	def takes (self, message: str) -> bool | None:

		"""Whether this part answers to a kind of message — notes, controls, program change.

		``True`` where the file records it, and ``None`` where the file lists the kind
		as ``unrecorded``: it arrives where the part sits with no document saying
		whether or how it reaches the part, or it reaches the part by a route the format
		has no place for.  Either way a program cannot count on the kind, sent on the
		part's channel, reaching this part: in the first case which part it reaches is
		unsaid, and in the second the channel may be another.  And it is not a no: a
		panel that drew nothing for it would be saying the part takes none.  ``None``
		is false to a caller that asks only yes or no.

		A part that says nothing about what it receives answers ``False`` to
		everything it does not name as unrecorded, which is honest: nobody recorded
		it.  Read ``receives`` itself to tell that apart from a part recorded as
		receiving nothing.
		"""

		if message in self.unrecorded:
			return None

		return self.receives is not None and message in self.receives


	def channel_for (self, base: int, instance: int = 0) -> int | None:

		"""Which MIDI channel one instance of this part sits on, given a base channel.

		``None`` where the part is assigned a channel instead and does not follow
		the base channel, or sits ``within`` another part and takes its channel,
		so a caller asking is told the question does not apply rather than handed
		a number.

		A part that ``follows_base`` is on the base channel, every instance of it,
		which is where it starts: once its owner gives it a channel, which one is
		their setting and not this file's.  A part on a fixed channel ignores the
		base, and its instances count up from its number.

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

		if self.fixed_channel is not None:
			return self.fixed_channel + instance

		if self.follows_base:
			return base

		if self.channel_offset is None:
			return None

		return (base - 1 + self.channel_offset + instance) % 16 + 1


def _numbers (control: Control) -> set[tuple[str, int]]:

	"""The numbers a control is sent on, told apart by kind: its controller's, its fine half's and its NRPN's."""

	numbers: set[tuple[str, int]] = set()

	if control.cc is not None:
		numbers.add(("cc", control.cc))

	if control.lsb is not None:
		numbers.add(("cc", control.lsb))

	if control.nrpn is not None:
		numbers.add(("nrpn", control.nrpn))

	return numbers


# ── Where the facts came from ────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class PageRun:

	"""A stretch of a document whose printed page numbers sit one distance from the file's.

	``from_printed`` is the first printed page of the stretch, and ``offset`` is
	what to add to a printed page number in it to reach the page of the file.
	"""

	from_printed: int
	offset: int


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
	A document with no pages at all - a plain-text implementation chart runs to
	numbered sections instead - says so with ``paginated: false``.

	A document can also number itself in more than one run.  An OP-XY guide's
	printed pages 1 to 52 are file pages 5 to 56, an unnumbered overflow page
	follows, and from printed page 53 on the file is five ahead.  So
	``page_offset`` may be written as a list of ``{from_printed, offset}`` runs,
	held in ``page_runs``, each applying from its first printed page until the
	next begins.  ``page_offset`` is then the first run's, and only ``file_page``
	is right for every page.

	``pictured_pages`` names the printed pages of this document whose numbers are
	published **only as an image**, so that a checker reading the text finds
	nothing and knows why.  An Arturia DrumBrute Impact is the case: 107 pages of
	ordinary text, and the one page that gives its drum map gives it as a
	screenshot of the maker's editor.  Declaring the page is a claim about the
	document a reader can turn to and check, and it is deliberately not inferred -
	a checker that excused any number absent from a page carrying a photograph
	would excuse an invented one on most pages of most manuals.
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
	pictured_pages: tuple[int, ...] = ()
	page_runs: tuple[PageRun, ...] = ()


	def file_page (self, printed: int) -> int | None:

		"""Which page of the file carries a given printed page number.

		``None`` where the document has no pages, so a caller asking the question
		is told the question does not apply rather than given a number.  Where the
		document numbers itself in runs, the run a page falls in decides its
		offset, and a page before the first run takes the first run's.
		"""

		if not self.paginated:
			return None

		offset = self.page_offset

		for run in self.page_runs:
			if printed >= run.from_printed:
				offset = run.offset

		return (printed + offset + self.pages_per_sheet - 1) // self.pages_per_sheet


# ── The whole document ───────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Definition:

	"""One instrument definition, read and checked.

	``groups`` is what to call each group of controls, as the instrument's own
	document names that section of its panel.  It holds only the labels a file
	states.  A group given none is shown by its identifier, which is honest,
	where a label guessed from ``bd`` would read as the maker's word for it and
	would be wrong.

	``warnings`` carries what the validator thought worth saying but not worth
	refusing the file over — most often that provenance is missing, or that an
	import has not yet been checked by a person.

	``modes`` holds the states the whole instrument can be put in, each under a
	short name, and is empty for the instrument most files describe, which has
	one.
	"""

	version: int
	model: Model
	source: str | None = None
	sources: dict[str, Source] = dataclasses.field(default_factory=dict)
	midi: Midi = dataclasses.field(default_factory=Midi)
	voice: Voice = dataclasses.field(default_factory=Voice)
	modes: dict[str, Mode] = dataclasses.field(default_factory=dict)
	parts: dict[str, Part] = dataclasses.field(default_factory=dict)
	groups: dict[str, str] = dataclasses.field(default_factory=dict)
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


	@property
	def factory_mode (self) -> str | None:

		"""The name of the mode a document says the instrument ships in, if one does.

		``None`` where no mode is marked, which is the ordinary case: most makers
		do not say, and nothing here guesses for them.
		"""

		for name, mode in self.modes.items():
			if mode.factory:
				return name

		return None


	def channels_in (self, mode: str) -> tuple[int, int] | None:

		"""The range the base channel can be set to in one mode.

		The mode's own range where it gives one, and the instrument's where it does
		not.  ``None`` where neither is recorded.  A mode this file does not declare
		is refused rather than answered.
		"""

		if mode not in self.modes:
			raise ValueError(f"{mode!r} is not one of this instrument's modes: {sorted(self.modes)}")

		return self.modes[mode].channels or self.midi.channels


	def parts_in (self, mode: str) -> dict[str, Part]:

		"""The parts that exist in one mode: those naming it, and those naming none.

		A mode this file does not declare is refused rather than answered, since
		every part naming no mode would otherwise be handed back for a typo.
		"""

		if mode not in self.modes:
			raise ValueError(f"{mode!r} is not one of this instrument's modes: {sorted(self.modes)}")

		return {name: part for name, part in self.parts.items() if part.mode in (None, mode)}


	def controls_in (self, mode: str) -> list[Control]:

		"""The controls that answer in one mode, in file order.

		The controls naming no part, unless the mode says ``unparted: false``,
		and the controls of every part that exists in the mode.  So a drumlogue's
		single-channel map answers in its factory mode and not in its
		multi-channel one, where each part's own map does instead.
		"""

		present = self.parts_in(mode)
		unparted = self.modes[mode].unparted

		return [
			control for control in self.controls.values()
			if (control.part is None and unparted) or control.part in present
		]


	def grouped_controls (self) -> dict[str, list[Control]]:

		"""The controls collected by their group, in the order to show them.

		``groups`` sets that order where a file names one: a labelled group comes
		first, in the order the labels are written.  That is what lets a file
		follow the maker's panel while its controls stay in the order the
		document prints their numbers, which is the order they were read in.  Any
		group no label names follows, in file order, and controls naming no group
		are collected under the empty string.  A page that does not care about
		groups can ignore this and read ``controls``, which is the flat list it
		would have had anyway.
		"""

		collected: dict[str, list[Control]] = {}

		for control in self.controls.values():
			collected.setdefault(control.group or "", []).append(control)

		# A labelled group no control joined is left out rather than shown empty:
		# the label is a heading, and a heading over nothing is worse than none.

		ordered: dict[str, list[Control]] = {}

		for name in self.groups:
			if name in collected:
				ordered[name] = collected.pop(name)

		ordered.update(collected)

		return ordered


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


	def controls_reaching (self, part: str, instance: int = 0, moved: bool = False) -> list[Control]:

		"""The controls one instance of a part answers to on its channel, in file order.

		A part's own controls, and — for the one instance sitting on the base
		channel, or every instance of a part that follows it, where the part is
		recorded as receiving controls — the controls that name no part, since
		those are sent on the base channel too.  So a Streichfett's strings part
		gets all nineteen, because its channel *is* the base channel and it takes
		controls there, while its solo part gets none.

		A Voce is why the rule asks what the part receives.  Its three parts start
		on the base channel but take only notes and program change, and its effect
		controls are "global to all three": they stay with the instrument rather
		than being filed under its first part.

		An assigned part that does not follow the base channel gets only its own.
		Whether a player happens to put it on the base channel is their project's
		business, not this file's.  A part on a fixed channel gets only its own
		too, whether or not the base channel is set to its number.  A control the
		instrument only transmits, or ignores both ways, is included like any
		other; read ``is_sendable`` for which a panel may send.

		A part that ``follows_base`` has two answers, and ``moved`` picks one.
		Where it starts, every instance sits on the base channel and gets the
		controls naming no part, where it takes controls and its mode lets them
		answer, and its own, leaving out, where it is handed them, any of its own
		on a number one of them already carries: a controller number, a fine
		half's or an NRPN.  Those are the part's copies for when it is moved, as a
		modwave's Layers have seven: on the base channel the number is the
		instrument's, so it is told once, whichever way each copy travels.  A
		control of its own carrying two numbers is left out where either is
		carried.
		Moved to a channel of its own, the part gets its own controls only.  Asking
		for the moved state of a part that does not follow the base channel is
		refused, as asking for an instance it does not have is.

		A part existing in one mode gets the controls naming no part only where
		that mode lets them answer: in a mode saying ``unparted: false`` the
		base-channel map is silent.  A part existing in every mode cannot know
		which one a caller means, so it gets them as before; ask ``controls_in()``
		what answers in one mode.  A part ``within`` this one is asked about by
		its own name, since its controls reach one of its instances rather than
		this part.
		"""

		found = self.parts[part]

		if not 0 <= instance < found.count:
			raise ValueError(f"instance {instance} is outside 0-{found.count - 1}, as {part!r} has {found.count}")

		if moved and not found.follows_base:
			raise ValueError(f"{part!r} does not follow the base channel, so it has no moved state")

		# Offsets wrap at 16 like channels do, so an instance is on the base
		# channel whenever its offset comes round to a whole number of sixteen.

		on_offset = found.channel_offset is not None and (found.channel_offset + instance) % 16 == 0

		on_base = (on_offset or (found.follows_base and not moved)) \
			and found.takes(CONTROLS) \
			and (found.mode is None or self.modes[found.mode].unparted)

		# A following part's own copy of a number the instrument's map carries is for
		# when the part is moved, so on the base channel it is left to the map.

		shared: set[tuple[str, int]] = set()

		if on_base and found.follows_base:
			for control in self.controls.values():
				if control.part is None:
					shared |= _numbers(control)

		return [
			control for control in self.controls.values()
			if (control.part == part and not shared & _numbers(control))
				or (control.part is None and on_base)
		]


	def panel_first (self) -> list[Control]:

		"""The controls with those the box has no knob for first, then file order.

		Opt-in, and deliberately not the default: the flag is a strong hint and a
		poor rule.  A control that *does* have a knob can still be the one a part
		most wants on glass.
		"""

		return sorted(self.controls.values(), key=lambda control: not control.panel_only)
