"""Importing a MIDNAM file into an instrument definition.

MIDNAM is the one machine-readable description of an instrument that already
exists in quantity -- Ardour alone bundles several hundred -- so it is the
cheapest way to get a definition started.  It is not a way to get one finished.

**An import is an on-ramp, never an authority.**  MIDNAM carries the control
map and nothing else: no polyphony, no note range, no velocity response, no
aftertouch.  Everything in the ``midi`` and ``voice`` sections has to be added
by a person reading the manual.  And the control map itself can simply be
wrong -- the widely shared Moog Minitaur file gives a key-priority band the
manufacturer's own firmware addendum contradicts.

So an import is marked ``unverified`` in its own ``source`` line, the validator
keeps saying so, and it stays said until somebody replaces that line with the
manual and the page they checked it against.
"""

import pathlib
import re
import typing
import xml.etree.ElementTree

import pymidiinstrumentdefs.definition
import pymidiinstrumentdefs.validation


# Bare words YAML 1.1 reads as true or false rather than as text, so a name that
# is any of these has to be quoted on the way out or the file will not load.
YAML_KEYWORDS: typing.Final[frozenset[str]] = frozenset({
	"y", "yes", "n", "no", "true", "false", "on", "off", "null", "none", "~",
})


def _local (tag: str) -> str:

	"""The tag name without whatever namespace the document happened to use."""

	return tag.rsplit("}", 1)[-1]


def _find_all (root: xml.etree.ElementTree.Element, name: str) -> list[xml.etree.ElementTree.Element]:

	"""Every element with this tag name, at any depth and in any namespace."""

	return [element for element in root.iter() if _local(element.tag) == name]


def _text_of (root: xml.etree.ElementTree.Element, name: str) -> str | None:

	"""The text of the first element with this tag name, if there is one."""

	for element in _find_all(root, name):
		if element.text and element.text.strip():
			return element.text.strip()

	return None


def _slug (text: str, prefix: str) -> str:

	"""Turn a human label into an addressable name.

	Names must start with a letter, so anything beginning with a digit takes the
	given prefix rather than being dropped -- "16' Octave" is a real control and
	losing it would be worse than renaming it.
	"""

	cleaned = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

	if not cleaned:
		return ""

	return cleaned if cleaned[0].isalpha() else f"{prefix}_{cleaned}"


def _unique (name: str, taken: typing.Container[str]) -> str:

	"""A name not already used, by numbering the repeats.

	MIDNAM does not require control names to be distinct, and two controls
	quietly becoming one is the kind of loss nobody notices.
	"""

	if name not in taken:
		return name

	for suffix in range(2, 1000):
		candidate = f"{name}_{suffix}"

		if candidate not in taken:
			return candidate

	return name


def _values_of (element: xml.etree.ElementTree.Element) -> dict[str, int]:

	"""The named bands a ``ValueNameList`` element holds.

	A ``Value``'s ``Number`` is the lowest of its band, running to the next entry
	minus one -- the same convention a definition file uses, so nothing has to be
	converted here.
	"""

	values: dict[str, int] = {}

	for value in _find_all(element, "Value"):
		number = value.get("Number")

		if number is None:
			continue

		try:
			low = int(number)
		except ValueError:
			continue

		key = _unique(_slug(value.get("Name") or "", "value") or f"value_{low}", values)
		values[key] = low

	# Real files do not always list bands low to high -- one measured MIDNAM
	# counts a clock divider downwards. A band is defined by its number and not
	# by its position in the file, so sorting loses nothing and is what makes the
	# result a definition this package will actually load.
	return dict(sorted(values.items(), key = lambda pair: pair[1]))


def _shared_value_lists (root: xml.etree.ElementTree.Element) -> dict[str, dict[str, int]]:

	"""The document's named value lists, which controls refer to by name.

	Only lists carrying a ``Name`` are shared. A ``ValueNameList`` written inline
	inside a control's ``Values`` has no name and belongs to that control alone;
	real files use both forms, often in the same document.
	"""

	shared: dict[str, dict[str, int]] = {}

	for element in _find_all(root, "ValueNameList"):
		name = element.get("Name")

		if not name:
			continue

		values = _values_of(element)

		if values:
			shared[name] = values

	return shared


# Moog's files split a 14-bit control into two, named "(Coarse)" and "(Fine)";
# Waldorf's use an "MSB"/"LSB" suffix. Neither is required by MIDNAM, so a pair
# is only joined when the arithmetic agrees as well as the name.
_COARSE: typing.Final[re.Pattern[str]] = re.compile(r"\s*(?:\((?:coarse|msb)\)|\bmsb)\s*$", re.I)
_FINE: typing.Final[re.Pattern[str]] = re.compile(r"\s*(?:\((?:fine|lsb)\)|\blsb)\s*$", re.I)


class _Raw(typing.NamedTuple):

	"""One ``Control`` element, before coarse and fine halves are joined."""

	label: str
	cc: int
	values: dict[str, int]
	extent: tuple[int, int]
	wide: bool


def _raw_controls (
	root: xml.etree.ElementTree.Element,
	shared: dict[str, dict[str, int]],
	warnings: list[str],
	source: str,
) -> list[_Raw]:

	"""Every usable ``Control`` in the document, in the order it appears."""

	found: list[_Raw] = []

	for element in _find_all(root, "Control"):
		number = element.get("Number")
		label = element.get("Name") or ""

		if number is None:
			continue

		try:
			cc = int(number)
		except ValueError:
			continue

		if not 0 <= cc <= 127:
			warnings.append(f"{source}: control {label!r} has number {cc}, which is not 0-127 — skipped")
			continue

		extent = (0, 127)
		values: dict[str, int] = {}

		for holder in _find_all(element, "Values"):
			low, high = holder.get("Min"), holder.get("Max")

			if low is not None and high is not None:
				try:
					extent = (int(low), int(high))
				except ValueError:
					pass

			# A list written inline belongs to this control; one referred to by
			# name is shared with others. Real files use both, often at once.
			for inline in _find_all(holder, "ValueNameList"):
				values = _values_of(inline) or values

			for reference in _find_all(holder, "UsesValueNameList"):
				named = reference.get("Name")

				if named and named in shared:
					values = shared[named]

		found.append(_Raw(
			label  = label,
			cc     = cc,
			values = {name: low for name, low in values.items() if extent[0] <= low <= extent[1]},
			extent = extent,
			wide   = element.get("Type") == "14bit",
		))

	return found


def _join_wide_pairs (
	raw: list[_Raw],
	warnings: list[str],
	source: str,
) -> dict[str, pymidiinstrumentdefs.definition.Control]:

	"""Join controls split into a coarse and a fine half into one 14-bit control.

	MIDNAM has no structural way to say that two control numbers are the two
	halves of one parameter, so files that carry 14-bit controls at all say it in
	the names: Moog writes "(Coarse)" and "(Fine)", Waldorf an "MSB"/"LSB"
	suffix. **A pair is joined only when the arithmetic agrees as well as the
	name** -- the fine number must be the coarse one plus 32, which is the rule
	MIDI itself sets. Where the names pair and the numbers do not, both halves
	are kept apart and the disagreement is reported, because guessing which of
	the two is the typo would be inventing a number.
	"""

	coarse: dict[str, _Raw] = {}
	fine: dict[str, _Raw] = {}

	for entry in raw:
		if _COARSE.search(entry.label):
			coarse[_COARSE.sub("", entry.label).strip().lower()] = entry
		elif _FINE.search(entry.label):
			fine[_FINE.sub("", entry.label).strip().lower()] = entry

	joined: dict[str, _Raw] = {}
	absorbed: set[int] = set()

	for base, low_half in coarse.items():
		high_half = fine.get(base)

		if high_half is None:
			continue

		if high_half.cc != low_half.cc + 32:
			warnings.append(
				f"{source}: {low_half.label!r} and {high_half.label!r} look like a pair, but "
				f"{high_half.cc} is not {low_half.cc} + 32 — left as two controls, and one of "
				f"the two numbers is wrong"
			)
			continue

		joined[base] = high_half
		absorbed.add(id(high_half))

	controls: dict[str, pymidiinstrumentdefs.definition.Control] = {}

	for entry in raw:
		if id(entry) in absorbed:
			continue

		base = _COARSE.sub("", entry.label).strip().lower()
		partner = joined.get(base) if _COARSE.search(entry.label) else None
		label = _COARSE.sub("", entry.label).strip() if partner else entry.label

		key = _unique(_slug(label, "control") or f"control_{entry.cc}", controls)

		controls[key] = pymidiinstrumentdefs.definition.Control(
			name   = key,
			label  = label or key.replace("_", " "),
			cc     = entry.cc,
			lsb    = partner.cc if partner else None,
			values = entry.values,
			range  = entry.extent,
		)

		if entry.wide and partner is None:
			warnings.append(
				f"{source}: {key} is marked 14bit and has no fine half named beside it, "
				f"so `lsb` has to be added by hand"
			)

	return controls


def read (
	text: str,
	*,
	source: str,
	path: pathlib.Path | None = None,
) -> pymidiinstrumentdefs.definition.Definition:

	"""Read a MIDNAM document into a definition, marked unverified.

	Raises ``DefinitionError`` if the document is not parseable XML, or carries
	no model name -- without one there is nothing to file the result under.
	"""

	try:
		root = xml.etree.ElementTree.fromstring(text)
	except xml.etree.ElementTree.ParseError as broken:
		raise pymidiinstrumentdefs.validation.DefinitionError(
			f"{source}: not valid XML: {broken}") from broken

	name = _text_of(root, "Model")

	if not name:
		raise pymidiinstrumentdefs.validation.DefinitionError(
			f"{source}: no <Model> element, so there is no instrument to name")

	warnings: list[str] = []
	shared = _shared_value_lists(root)
	controls = _join_wide_pairs(_raw_controls(root, shared, warnings, source), warnings, source)

	# A drum machine carries one note list per kit -- fifty of them, in one file
	# measured. A definition has room for one voice map, so the first is taken
	# and the rest are named rather than silently flattened together.
	note_lists = _find_all(root, "NoteNameList")
	voices: dict[str, int] = {}

	if note_lists:
		for element in _find_all(note_lists[0], "Note"):
			number = element.get("Number")

			if number is None:
				continue

			try:
				note = int(number)
			except ValueError:
				continue

			if 0 <= note <= 127:
				key = _unique(_slug(element.get("Name") or "", "voice") or f"voice_{note}", voices)
				voices[key] = note

	if len(note_lists) > 1:
		warnings.append(
			f"{source}: {len(note_lists)} note maps in this file — took "
			f"{note_lists[0].get('Name') or 'the first'} and left the rest; "
			f"a definition describes one map, so pick the one you use"
		)

	presets = len(_find_all(root, "Patch")) or None

	warnings.append(
		f"{source}: everything in `midi` and `voice` has to be added by hand — MIDNAM "
		f"carries no polyphony, note range, velocity response or aftertouch"
	)

	return pymidiinstrumentdefs.definition.Definition(
		version = pymidiinstrumentdefs.validation.VERSION,
		model   = pymidiinstrumentdefs.definition.Model(
			name         = name,
			manufacturer = _text_of(root, "Manufacturer"),
		),
		source = f"imported from {pathlib.Path(source).name}, unverified",
		midi = pymidiinstrumentdefs.definition.Midi(
			program_change = None if presets is None
				else pymidiinstrumentdefs.definition.ProgramChange(presets = presets),
		),
		voice = pymidiinstrumentdefs.definition.Voice(
			addressing = "voices" if voices else None,
			voices     = voices,
		),
		controls = controls,
		path     = path,
		warnings = tuple(warnings),
	)


def read_file (path: pathlib.Path | str) -> pymidiinstrumentdefs.definition.Definition:

	"""Read one MIDNAM file into a definition, marked unverified."""

	file = pathlib.Path(path)

	return read(file.read_text(encoding = "utf-8", errors = "replace"), source = str(file), path = file)


def suggested_name (definition: pymidiinstrumentdefs.definition.Definition) -> str:

	"""The ``maker/model`` name this draft should be saved under, which is also its path.

	The maker is spelled the way the MIDNAM spells it, which is often longer
	than the folder a hand-written definition would use — ``moog_music`` where
	the bundled set says ``moog``.  Shorten it if you like; a name only has to
	match where the file is.  A MIDNAM that names no manufacturer is filed
	under ``unknown`` until somebody says who made it.
	"""

	maker = _slug(definition.model.manufacturer or "", "m") or "unknown"
	model = _slug(definition.model.name, "m")

	return f"{maker}/{model}"


def _key (name: str) -> str:

	"""A mapping key, quoted if YAML would read it as something other than text.

	``off`` and ``on`` are the ones that actually happen: they are band names on
	every switch in the world, and YAML 1.1 turns them into false and true.
	"""

	return f'"{name}"' if name.lower() in YAML_KEYWORDS else name


def _scalar (text: str) -> str:

	"""A text value, always quoted, so nothing in a label can change its meaning."""

	escaped = text.replace("\\", "\\\\").replace('"', '\\"')

	return f'"{escaped}"'


def to_yaml (definition: pymidiinstrumentdefs.definition.Definition) -> str:

	"""Write a definition out as the draft file an import lands.

	Deliberately plain: no dependency on a YAML writer, and an ordering that
	matches how the format is documented, because the next thing that happens to
	this file is a person editing it.
	"""

	lines: list[str] = []

	lines.append("# A DRAFT. Nobody has checked this against a manual yet.")
	lines.append("#")
	lines.append("# MIDNAM carries a control map and nothing else. Everything below in `midi`")
	lines.append("# and `voice` has to be filled in by hand, and every number here is worth")
	lines.append("# checking: the most widely shared MIDNAM for a common synth disagrees with")
	lines.append("# its own manufacturer's firmware addendum.")
	lines.append("#")
	lines.append("# Replace the `source` line with the manual and page you checked, and this")
	lines.append("# stops being a draft.")

	for warning in definition.warnings:
		lines.append(f"#   - {warning.split(': ', 1)[-1]}")

	lines.append("")
	lines.append(f"definition: {definition.version}")
	lines.append("")
	lines.append("model:")

	if definition.model.manufacturer:
		lines.append(f"  manufacturer: {_scalar(definition.model.manufacturer)}")

	lines.append(f"  name: {_scalar(definition.model.name)}")
	lines.append("")

	if definition.source:
		lines.append(f"source: {_scalar(definition.source)}")
		lines.append("")

	if definition.midi.program_change and definition.midi.program_change.presets:
		lines.append("midi:")
		lines.append("  program_change:")
		lines.append(f"    presets: {definition.midi.program_change.presets}")
		lines.append("")

	if definition.voice.addressing or definition.voice.voices:
		lines.append("voice:")

		if definition.voice.addressing:
			lines.append(f"  addressing: {definition.voice.addressing}")

		if definition.voice.voices:
			lines.append("  voices:")

			for name, note in definition.voice.voices.items():
				lines.append(f"    {_key(name)}: {note}")

		lines.append("")

	if definition.controls:
		lines.append("controls:")

		for control in definition.controls.values():
			lines.append("")
			lines.append(f"  {_key(control.name)}:")
			lines.append(f"    label: {_scalar(control.label)}")

			if control.cc is not None:
				lines.append(f"    cc: {control.cc}")

			if control.lsb is not None:
				lines.append(f"    lsb: {control.lsb}")

			if control.nrpn is not None:
				lines.append(f"    nrpn: {control.nrpn}")

			if control.range != (0, 127):
				lines.append(f"    range: [{control.range[0]}, {control.range[1]}]")

			if control.default is not None:
				lines.append(f"    default: {control.default}")

			if control.values:
				pairs = ", ".join(f"{_key(name)}: {low}" for name, low in control.values.items())
				lines.append(f"    values: {{{pairs}}}")

			if control.kind_override is not None:
				lines.append(f"    kind: {control.kind_override}")

			if control.unit is not None:
				lines.append(f"    unit: {_scalar(control.unit)}")

			if control.group is not None:
				lines.append(f"    group: {_scalar(control.group)}")

			if control.panel_only:
				lines.append("    panel_only: true")

	return "\n".join(lines).rstrip() + "\n"
