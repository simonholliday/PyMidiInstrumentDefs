# PyMidiInstrumentDefs

What a particular model of MIDI instrument answers to -- its controls, its
voicing, its note range -- read from definitions transcribed from the
manufacturers' own manuals.

It is the companion to [PyMidiDefs](https://github.com/simonholliday/PyMidiDefs),
which carries the MIDI specification's own constants. PyMidiDefs says CC 7 is
Volume; this package says a Matriarch's CC 94 switches it between one, two and
four voices.

## Two kinds of fact

PyMidiDefs holds **specification** facts. CC 7 is Volume; note 60 is C4. They
are true for everybody, permanently, they are transcribed from published
standards, and they cannot be wrong about the world.

This package holds **model** facts. A Minitaur ignores notes above 72; a
Matriarch's CC 94 switches it between one, two and four voices. They are true
for everybody who owns that model, and they change when the manufacturer ships
firmware.

The difference matters when you are deciding how much to trust a number. **A
model fact is a report, and reports are wrong in the wild.** For one parameter
on one common synth -- the Minitaur's key priority -- the manual, the firmware
addendum, and the `.midnam` file everybody shares give three different answers.
So every instrument definition carries a `source` saying which manual and which
page it came from, and one imported automatically stays marked `unverified`
until a person has checked it. [Sources](#sources), below, says where each of
the bundled ones came from and gives that Minitaur disagreement in full.

**Rig facts are not here and never will be.** Which channel *your* Minitaur is
on, which port it is plugged into, which notes you have chosen to play -- those
belong to your own project, not to a definition shared by everyone who owns the
same box.

**And specification facts stay in PyMidiDefs.** The channel mode messages, CC
120 to 127 -- All Sound Off, Local Control and the rest -- mean the same on every
instrument that has them, so a definition does not list them as controls even
where a manufacturer's chart prints them. The validator refuses one, and names
the PyMidiDefs constant it would have duplicated.

## Installation

```bash
pip install pymidiinstrumentdefs
```

Requires Python 3.10 or later. It depends on PyMidiDefs and on PyYAML, since
every definition is a YAML file.

To install the latest unreleased code straight from the repository:

```bash
pip install git+https://github.com/simonholliday/PyMidiInstrumentDefs.git
```

## Usage

```python
import pymidiinstrumentdefs

matriarch = pymidiinstrumentdefs.load("moog/matriarch")

matriarch.voice.voicing_modes            # (1, 2, 4)  switchable voicing
matriarch.voice.plays_note(60)           # True
matriarch.controls["glide_type"].kind    # 'choice'

# What to send to put a banded control into a named state. Definitions record
# the band boundaries as manuals print them; working out the number is this
# library's job.
matriarch.controls["glide_type"].value_for("exp")   # 106

pymidiinstrumentdefs.available()         # what is on the search path
```

Some instruments are several instruments at once, each answering on its own
MIDI channel. A definition says so with `parts`, and a control names the part
it belongs to — so the same controller number can mean two different things
and still be unambiguous:

```python
streichfett = pymidiinstrumentdefs.load("waldorf/streichfett")

streichfett.parts["solo"].channel_for(1)   # 2 — one channel above the strings
streichfett.parts["solo"].takes("notes")   # True
streichfett.parts["solo"].polyphony        # 8 — its own voices, not the strings'
streichfett.controls_by_part()[""]         # the controls on the base channel
streichfett.controls_reaching("strings")   # all 19 — the strings sit on the base channel
```

### Names, and where the files go

A definition is named for its maker and its model, and the name is also where
its file sits: `moog/matriarch` is `moog/matriarch.yaml`, in a folder named for
the maker. Each half is lower case, digits and underscores.

Definitions are looked for in three places, nearest first:

1. an `instruments/` folder beside your project,
2. your own library, one per person, so a definition you write once is found
   by every tool you run:
   - Linux: `~/.local/share/pymidiinstrumentdefs/` (or under `$XDG_DATA_HOME`)
   - macOS: `~/Library/Application Support/pymidiinstrumentdefs/`
   - Windows: `%APPDATA%\pymidiinstrumentdefs\`
3. the set bundled with this package.

So **a file you drop always beats one we shipped**. That is the whole answer to
adding your own synth: no index to edit, no registration, no pull request. To
describe your own synth, or to correct one of ours, write
`instruments/<maker>/<model>.yaml` beside your project. A definition is one
self-contained YAML file, and you share it by sending it.

### The bundled definitions

| Name | Instrument |
|------|------------|
| `behringer/model_d` | Behringer MODEL D -- no control changes at all; its remote surface is SysEx |
| `modal/carbon8m` | Modal CARBON8M -- 106 controls, and a voice count set per patch |
| `moog/dfam` | Moog DFAM -- no MIDI at all, and the file says so |
| `moog/labyrinth` | Moog Labyrinth -- answers to notes, clock and transport, and nothing else |
| `moog/matriarch` | Moog Matriarch -- 36 controls, and a voice count you can switch over MIDI |
| `moog/minitaur` | Moog Minitaur -- plays notes 0-72, with the firmware v2.1 corrections |
| `moog/subharmonicon` | Moog Subharmonicon -- reads a note as an offset from C4, not as a pitch |
| `pwm/malevolent` | PWM Malevolent -- from its quick-start guide alone, and says so |
| `roland/tr8s` | Roland TR-8S -- eleven voices of four controls, and two it only sends |
| `sequential/take_5` | Sequential Take 5 -- 170 controls, most reachable by CC and by finer NRPN |
| `soma/pulsar_23` | Soma Pulsar-23 -- every note and controller assigned by MIDI learn |
| `vermona/drm1_mkiv` | Vermona DRM1 MkIV -- a drum machine that ignores controller data |
| `voce/electric_piano` | Voce ELECTRIC PIANO -- 16 or 32 voices, depending on the chorus |
| `waldorf/streichfett` | Waldorf Streichfett -- controls whose values are exact numbers, not bands |

The set is a starting point rather than a catalogue. `moog/dfam` is five lines,
because the DFAM has no MIDI at all and saying so is worth more than saying
nothing. Three others -- the Labyrinth, the MODEL D and the DRM1 -- are nearly
as short for the same reason: somebody read the whole manual and found no
control changes, and the file records that it looked.

### Starting from a MIDNAM file

If your instrument has a `.midnam` file -- Ardour bundles several hundred --
`pymidiinstrumentdefs.midnam` will start a definition from it:

```python
import pymidiinstrumentdefs.midnam

draft = pymidiinstrumentdefs.midnam.read_file("Moog_Minitaur.midnam")

pymidiinstrumentdefs.midnam.suggested_name(draft)   # 'moog_music/minitaur'
print(pymidiinstrumentdefs.midnam.to_yaml(draft))
```

What that lands is a **draft**, and it says so in its own first line. MIDNAM
carries a control map and nothing else -- no polyphony, no note range, no
velocity response -- and the numbers it does carry are worth checking against
the manual. It stays marked `unverified` until you replace the `source` line
with what you checked it against.

**This is not how the bundled definitions were made.** Those came from manuals,
and none of them is an import. [Sources](#sources) measures how far a `.midnam`
can be trusted, on the one instrument where both can be compared.

## Sources

**A definition is only as good as its `source` line, and that line is the
authority -- not this README.**

```python
matriarch = pymidiinstrumentdefs.load("moog/matriarch")

matriarch.source        # the manual and the pages, in the file's own words
matriarch.sources       # the same, in fields: edition, address, SHA-256, page offset
matriarch.is_unverified # True if nobody has checked it yet
matriarch.warnings      # what the validator thought worth saying
```

The definitions bundled here were read out of **manufacturers' own
documents**, page by page, and each names the document and the pages it came
from. Usually that is the user manual. For the TR-8S and the Take 5 it is the
maker's MIDI implementation document, and for the Malevolent a quick-start
guide, because that is all there is, and its file keeps to what the guide says. Two were checked against a second source as well: the
Minitaur against Moog's firmware v2.1 addendum, and the DRM1's note map against
a working implementation of the same machine.

**None of them was imported from a `.midnam` file, and none ever will be.** The
importer is a tool for starting a definition of *your* instrument; it is not
where ours come from.

Three tests hold that line, so it is a property of the package rather than a
promise in a README: one refuses to ship a definition that does not name a
document and cite pages, one refuses anything still marked `unverified`, and one
refuses anything the importer wrote.

The Minitaur is the worked example of why that second source matters. Its
manual prints the key-priority bands as `0-42`, `43-84`, `87-127` -- leaving 85
and 86 assigned to nothing -- and the firmware addendum corrects the third band
to **86**. This package carries 86, and the file says why it differs from the
printed table. That is the level of care every bundled definition is held to,
and it is why a `source` line records pages rather than saying "the manual".

**Anything imported is a draft, and is not held to that at all.**
`pymidiinstrumentdefs.midnam` starts a definition from a `.midnam` file, and
what it lands says `imported from <file>, unverified` in its own source line,
keeps saying it, and is reported by the validator until a person replaces it.

That is not a reason to avoid importing -- it is a good way to start and a poor
place to stop, and it is worth being precise about which. Comparing the widely
shared `Moog_Minitaur.midnam` against the same instrument's manual and firmware
addendum, on the one instrument where this package holds both:

- **all 37 control-change numbers agree**, and
- **all 17 14-bit pairings agree**, which is the tedious half of a definition and
  the half most easily mistyped by hand;
- **4 of the 11 comparable band boundaries differ**, including the key-priority
  band it gives as `85` where the manual says `87` and the addendum says `86`.

None of those four changes what gets *sent*, because a band is transmitted as its
midpoint rather than its edge. They do change what gets *read back*: ask that
imported definition what a value of 85 means on key priority and it says `last`,
where the corrected file says `high`. So an import is reliable about which
controller does what, and not yet reliable about what its values mean.

**And a definition you supply yourself is yours.** Files you drop beside your
project or into your own library beat the ones bundled here, by design, and
this package makes no claim about where their numbers came from.

**Writing one, and want the numbers to be right?**
[docs/adding-an-instrument.md](docs/adding-an-instrument.md) is the long answer:
where makers actually publish, which kinds of source can be the only source for a
fact and which can do no more than disagree with you, how to tell which firmware a
document describes when its own date will not tell you, and how to cite it so that a
stranger can check every number in the file.

## History

These definitions, the loader and the importer were first published inside
PyMidiDefs 0.4.0, as `pymididefs.instruments`, and moved here so that
specification constants and instrument reports can be released separately.
PyMidiDefs' own history up to that point is in its repository, ending at
commit `4abf367`.

## License

MIT -- you are free to use, copy, modify, merge, publish, distribute,
sublicense, and sell copies of this software in any project, including
commercial and closed-source applications. The only requirement is that you
include the LICENSE file when redistributing the software. See
[LICENSE](https://github.com/simonholliday/PyMidiInstrumentDefs/blob/main/LICENSE)
for the full text.
