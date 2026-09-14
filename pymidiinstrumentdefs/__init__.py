"""PyMidiInstrumentDefs — what a particular model of MIDI instrument does.

PyMidiDefs holds **specification** facts — CC 7 is Volume, note 60 is C4.  They
are true for everybody, permanently, and they cannot be wrong.

This package holds **model** facts — a Minitaur ignores notes above 72, a
Matriarch's CC 94 switches it between one, two and four voices.  They are true
for everybody who owns that model, and they change when the manufacturer ships
firmware.  A model fact is a *report*, so a definition carries provenance saying
which manual and which page it came from, and an imported one stays marked
unverified until a person has checked it.

**Rig** facts — which channel *your* Minitaur is on, which port it is plugged
into — are never here.  They belong to your own project.

A definition is named for its maker and its model, and the name is also where
its file sits: ``moog/matriarch`` is ``moog/matriarch.yaml``.

::

	import pymidiinstrumentdefs

	matriarch = pymidiinstrumentdefs.load("moog/matriarch")

	matriarch.voice.polyphony                      # None — switchable, see voicing_modes
	matriarch.controls["glide_type"].kind          # 'choice'
	matriarch.controls["glide_type"].value_for("exp")   # what to send for EXP

Definitions are looked for beside your project first, then in your own library,
then in the set bundled here — so a file you drop always beats one we shipped.
That is the whole answer to adding your own synth.

To start one from a MIDNAM file — Ardour bundles several hundred — see
``pymidiinstrumentdefs.midnam``.  What it lands is a draft: MIDNAM carries a
control map and nothing else, and the numbers in it are worth checking.
"""

import importlib.metadata

import pymidiinstrumentdefs.definition
import pymidiinstrumentdefs.loading
import pymidiinstrumentdefs.validation


# Version is derived from the latest git tag at build time via hatch-vcs;
# `importlib.metadata` then reads it from the installed package metadata.
# The fallback only fires if someone runs from a raw source checkout without
# installing the package.
try:
	__version__ = importlib.metadata.version("pymidiinstrumentdefs")
except importlib.metadata.PackageNotFoundError:
	__version__ = "0.0.0+unknown"

# The public surface, re-exported by assignment so each name is the object
# itself: `pymidiinstrumentdefs.load is pymidiinstrumentdefs.loading.load`.
CHOICE = pymidiinstrumentdefs.definition.CHOICE
CONTINUOUS = pymidiinstrumentdefs.definition.CONTINUOUS
SWITCH = pymidiinstrumentdefs.definition.SWITCH
Control = pymidiinstrumentdefs.definition.Control
Definition = pymidiinstrumentdefs.definition.Definition
Midi = pymidiinstrumentdefs.definition.Midi
Model = pymidiinstrumentdefs.definition.Model
Part = pymidiinstrumentdefs.definition.Part
Source = pymidiinstrumentdefs.definition.Source
Voice = pymidiinstrumentdefs.definition.Voice

DefinitionNotFound = pymidiinstrumentdefs.loading.DefinitionNotFound
available = pymidiinstrumentdefs.loading.available
load = pymidiinstrumentdefs.loading.load
load_file = pymidiinstrumentdefs.loading.load_file
locate = pymidiinstrumentdefs.loading.locate
parse = pymidiinstrumentdefs.loading.parse
search_path = pymidiinstrumentdefs.loading.search_path

DefinitionError = pymidiinstrumentdefs.validation.DefinitionError

# Declared rather than implied, so a type checker and a reader agree on what
# the package offers.
__all__ = [
	"CHOICE",
	"CONTINUOUS",
	"SWITCH",
	"Control",
	"Definition",
	"DefinitionError",
	"DefinitionNotFound",
	"Midi",
	"Model",
	"Part",
	"Source",
	"Voice",
	"available",
	"load",
	"load_file",
	"locate",
	"parse",
	"search_path",
]
