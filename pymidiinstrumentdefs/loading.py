"""Finding an instrument definition and reading it.

A definition is named for its maker and its model — ``moog/matriarch`` — and
the name is also where its file sits: ``moog/matriarch.yaml``, in a folder named
for the maker, under one of the directories on the search path.

A reader takes a **search path** and returns the first match, so a definition
sitting beside your project always beats one in your library, and a library one
always beats the set that ships here.  That is the whole answer to "how do I add
my own synth": drop a file.  No index to edit, no registration, no pull request,
and what you write always wins over what we shipped.
"""

import os
import pathlib
import sys
import typing

import yaml

import pymidiinstrumentdefs.definition
import pymidiinstrumentdefs.validation


SUFFIX: typing.Final[str] = ".yaml"

# Where the definitions that ship with this package live, one folder per maker.
BUNDLED: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent / "corpus"


class DefinitionNotFound(LookupError):

	"""No definition of that name was anywhere on the search path."""


def user_library () -> pathlib.Path:

	"""Where this person's own definitions live, by their platform's convention.

	One place per person, so a definition written once is found by every tool
	they run.  Nothing has to exist here; it is simply looked in.
	"""

	if sys.platform == "win32":
		base = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home() / "AppData" / "Roaming"))
		return base / "pymidiinstrumentdefs"

	if sys.platform == "darwin":
		return pathlib.Path.home() / "Library" / "Application Support" / "pymidiinstrumentdefs"

	base = pathlib.Path(os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local" / "share"))

	return base / "pymidiinstrumentdefs"


def search_path (beside: pathlib.Path | None = None) -> tuple[pathlib.Path, ...]:

	"""The places a definition is looked for, nearest first.

	``beside`` is the directory holding the project being worked on; its
	``instruments/`` subdirectory is searched before anything else.  These are
	recommendations rather than requirements — pass your own path to ``load``
	and none of this applies.
	"""

	here = (beside or pathlib.Path.cwd()) / "instruments"

	return (here, user_library(), BUNDLED)


def available (search: typing.Sequence[pathlib.Path] | None = None) -> list[str]:

	"""The names of every definition on the search path, nearest first, once each.

	Only a file in a maker's folder has a name.  A YAML file sitting directly in
	a search directory says nothing about who made the instrument, so it is not
	listed here and cannot be loaded by name.
	"""

	found: list[str] = []

	for directory in (search if search is not None else search_path()):
		if not directory.is_dir():
			continue

		for candidate in sorted(directory.glob(f"*/*{SUFFIX}")):
			name = f"{candidate.parent.name}/{candidate.stem}"

			if name not in found:
				found.append(name)

	return found


def locate (name: str, search: typing.Sequence[pathlib.Path] | None = None) -> pathlib.Path:

	"""The file a name resolves to, first match winning.

	The name is checked before any path is built from it, so a name can only
	ever reach a maker's folder inside a search directory.  Raises
	``DefinitionError`` for a name that is not ``maker/model``, and
	``DefinitionNotFound`` naming every file it looked for — a "not found" that
	does not say where it looked is a riddle.
	"""

	maker, model = pymidiinstrumentdefs.validation.check_name(name)
	directories = tuple(search if search is not None else search_path())

	for directory in directories:
		candidate = directory / maker / f"{model}{SUFFIX}"

		if candidate.is_file():
			return candidate

	looked = "\n".join(f"  {directory / maker / f'{model}{SUFFIX}'}" for directory in directories)

	raise DefinitionNotFound(f"No definition called {name!r}. Looked for:\n{looked}")


def parse (text: str, *, source: str, path: pathlib.Path | None = None) -> pymidiinstrumentdefs.definition.Definition:

	"""Read a definition from YAML text that is already in hand."""

	try:
		document = yaml.safe_load(text)
	except yaml.YAMLError as broken:
		raise pymidiinstrumentdefs.validation.DefinitionError(f"{source}: not valid YAML: {broken}") from broken

	return pymidiinstrumentdefs.validation.build(document, source = source, path = path)


def load_file (path: pathlib.Path | str) -> pymidiinstrumentdefs.definition.Definition:

	"""Read one definition from a named file."""

	file = pathlib.Path(path)

	pymidiinstrumentdefs.validation.check_stem(file.stem, str(file))

	return parse(file.read_text(encoding = "utf-8"), source = str(file), path = file)


def load (
	name: str,
	search: typing.Sequence[pathlib.Path] | None = None,
) -> pymidiinstrumentdefs.definition.Definition:

	"""Find a definition by its ``maker/model`` name and read it, nearest copy winning."""

	return load_file(locate(name, search))
