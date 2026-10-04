# PyMidiInstrumentDefs

What a particular model of MIDI instrument answers to - its controls, its
voicing, its note range - read from definitions transcribed from the
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
on one common synth - the Minitaur's key priority - the manual, the firmware
addendum, and the `.midnam` file everybody shares give three different answers.
So every instrument definition carries a `source` saying which manual and which
page it came from, and one imported automatically stays marked `unverified`
until a person has checked it. [Sources](#sources), below, says where each of
the bundled ones came from and gives that Minitaur disagreement in full.

**Rig facts are not here and never will be.** Which MIDI channel *your*
Minitaur is on, which port it is plugged into, which notes you have chosen to
play - those belong to your own project, not to a definition shared by
everyone who owns the same box.

**And specification facts stay in PyMidiDefs.** The MIDI channel mode messages,
CC 120 to 127 - All Sound Off, Local Control and the rest - mean the same on
every instrument that has them, so a definition does not list them as controls
even where a manufacturer's chart prints them. The validator refuses one, and
names the PyMidiDefs constant it would have duplicated.

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
it belongs to - so the same controller number can mean two different things
and still be unambiguous:

```python
streichfett = pymidiinstrumentdefs.load("waldorf/streichfett")

streichfett.parts["solo"].channel_for(1)   # 2 - one channel above the strings
streichfett.parts["solo"].takes("notes")   # True
streichfett.parts["solo"].polyphony        # 8 - its own voices, not the strings'
streichfett.controls_by_part()[""]         # the controls on the base channel
streichfett.controls_reaching("strings")   # all 19 - the strings sit on the base channel
```

A definition also says what its maker calls each group of controls, which is
what a page can head a table with. The groups are what the maker's own document
groups them into, in the order to show them:

```python
take_5 = pymidiinstrumentdefs.load("sequential/take_5")

take_5.groups["mod_1"]                   # 'Mod 1' - the mod matrix slot, as the panel numbers it
take_5.groups["envelope_1"]              # 'Env 1 (Filter)' - the guide's own words for which is which
list(take_5.grouped_controls())[:3]      # ['performance', 'oscillators', 'glide']
```

A group with no label is shown by its own name, which is honest: a label is
only ever there because a document says it.

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
| `akai/mpc_live` | Akai Professional MPC Live: no controls either, because one user guide covers ten machines and every controller number in it is one the owner assigns |
| `akai/mpc_sample` | Akai Professional MPC Sample: no controls at all, because its maker publishes no controller number and the absence is proved rather than assumed |
| `arturia/astrolab` | Arturia AstroLab: 36 controls off a table that gives a direction for every row in both directions - and a Section column that cannot be read as a grouping, because the rows are in controller-number order |
| `arturia/drumbrute_impact` | Arturia DrumBrute Impact: publishes no controller number at all - its drum map is the one set of numbers it states, and it states them inside a screenshot |
| `arturia/microfreak` | Arturia MicroFreak: four paraphonic voices, and 21 controls out of a manual with no MIDI chart in it |
| `arturia/minifreak` | Arturia MiniFreak: six voices, twelve when paraphonic, and one control its manual never mentions that its firmware release notes do |
| `arturia/polybrute` | Arturia PolyBrute: 74 controls off a chart set as eighteen small tables three across, whose column positions shift from one block of rows to the next |
| `arturia/polybrute_12` | Arturia PolyBrute 12: the same 74-number chart as the PolyBrute, asserted against it number for number - plus controller 74, the MPE Slide dimension, which that chart does not list |
| `asm/hydrasynth_explorer` | ASM Hydrasynth Explorer: 110 controls off a chart its maker prints twice, once by module and once by number - and four more the maker puts on numbers the MIDI specification reserves for channel mode, which this format cannot hold |
| `behringer/model_d` | Behringer MODEL D: no control changes at all; its remote surface is SysEx |
| `behringer/pro_800` | Behringer PRO-800: 70 controls out of a table whose six columns say what each number is - 34 of them 14-bit, paired to a fine half by name alone, at three different offsets and none of them the MIDI specification's |
| `behringer/td_3` | Behringer TD-3: no control changes either, established from the maker's own complete MIDI message table - its "Modded Out" sibling adds exactly one and needs a definition of its own |
| `dreadbox/typhon` | Dreadbox Typhon: 98 controllers out of a three-column list on two pages of the manual, which is the only place its maker publishes them - the standalone CC chart on the same download page belongs to a different instrument |
| `elektron/analog_four` | Elektron Analog Four: 229 controls off an appendix whose maker publishes it three times over, in which 157 parameters can be reached by NRPN and by nothing else |
| `elektron/analog_rytm_mkii` | Elektron Analog Rytm MKII: 99 controls of the 319 its appendix prints, because the other 220 are 32 machines' names for the same eight numbers |
| `elektron/digitakt` | Elektron Digitakt: eight audio tracks and eight that only send, with thirty controller numbers meaning more than one thing |
| `elektron/digitakt_ii` | Elektron Digitakt II: 144 controls off an appendix that numbers two of its own sections twice, and gives four pairs of parameters the same NRPN |
| `elektron/digitone` | Elektron Digitone: nine parts on nine MIDI channels, where one CC means three things |
| `elektron/digitone_ii` | Elektron Digitone II: 164 controls over sixteen tracks that each sound or send, sharing sixteen voices - and eleven NRPNs that mean one thing on an audio track and another on a MIDI track |
| `elektron/model_cycles` | Elektron Model:Cycles: the Model:Samples' manual with a synth in it, where four of its 30 controls mean something different on each of six machines |
| `elektron/model_samples` | Elektron Model:Samples: 29 controls off a one-page appendix headed CC MSB that gives an LSB for exactly one of them |
| `elektron/octatrack` | Elektron Octatrack: two controller maps where 51 numbers mean different things, one file for the MKI and the MKII because their appendices agree row for row - and sixteen rows the maker puts on numbers the MIDI specification reserves for channel mode, which this format cannot hold |
| `elektron/syntakt` | Elektron Syntakt: twelve tracks and an FX track, where 28 controller numbers mean one thing on a track and another on the FX track |
| `erica_synths/perkons_hd_01` | Erica Synths PĒRKONS HD-01: 44 controls off two pages of a manual reached through a news item, whose numbers a player can rewrite in a file on the SD card |
| `expressive_e/osmose` | Expressive E Osmose: an MPE instrument whose 24 voices each take a MIDI channel of their own, and which ignores velocity entirely |
| `korg/electribe` | Korg electribe: 18 controls out of a plain text file that prints every number twice, with sixteen parts on one MIDI channel and no way given of choosing one |
| `korg/microkorg` | Korg microKORG: 41 controller numbers that are the factory assignment and not fixed, each meaning one thing in a synth program and another in a vocoder one |
| `korg/microkorg2` | Korg microKORG2: 181 controls out of a maker who prints the same map three times, where the NRPN table gives six parameters one address and numbers two more twice over, and the manual's own pages are what put all eight right |
| `korg/minilogue` | Korg minilogue: 39 controls, thirteen of them switches whose named bands the maker gives twice over - as the values it sends and as the bands it reads them in - from an implementation its maker publishes as a plain text file and again, five years later, as a chart in the manual |
| `korg/minilogue_xd` | Korg minilogue xd: 58 controls and 61 NRPNs, out of a document that inverts two of them between sending and receiving |
| `korg/modwave_mk_ii` | Korg modwave mk II: one manual covers three models, and the only difference is the voice count - with a chart whose two direction columns had to be proved rather than read in order |
| `korg/monologue` | Korg monologue: 24 controls out of an implementation printed twice, one direction each, where two numbers are received only and one control's bands are the footnote the maker forgot |
| `korg/multi_poly` | Korg multi/poly: nine fixed controllers and twelve that are factory defaults, off a chart page three of whose spans are enciphered |
| `korg/opsix` | Korg opsix: 30 controls off one chart page whose text is enciphered, five of them recognised and never sent |
| `korg/volca_beats` | Korg volca beats: 20 controls and ten parts off a plain text file, where the chart beside it draws its yes and no marks and names only seven of the ten |
| `korg/volca_drum` | Korg volca drum: six parts on six channels, and the one of its maker's two charts that the instrument answers to out of the box |
| `korg/wavestate` | Korg wavestate: 41 of its 50 controller numbers are defaults a player can reassign, and its maker publishes no control-change chart |
| `make_noise/zero_coast` | Make Noise 0-COAST: 19 controllers off a list whose maker says most of them are ignored unless the instrument is in a particular mode - and one row of which is not text at all but a drawing |
| `modal/carbon8m` | Modal CARBON8M: 106 controls, and a voice count set per patch |
| `moog/dfam` | Moog DFAM: no MIDI at all, and the file says so |
| `moog/grandmother` | Moog Grandmother: one voice, five controls in 14-bit pairs, and a value table of 24 clock divisions |
| `moog/labyrinth` | Moog Labyrinth: answers to notes, clock and transport, and nothing else |
| `moog/matriarch` | Moog Matriarch: 37 controls, one of which only its firmware notes mention, and a voice count you can switch over MIDI |
| `moog/messenger` | Moog Messenger: 56 controls, 31 of them 14-bit pairs the specification's own way round, with every band named |
| `moog/minitaur` | Moog Minitaur: plays notes 0-72, with the firmware v2.1 corrections |
| `moog/mother_32` | Moog Mother-32: seven controllers, four of which reach no sound at all but a voltage at a jack the player patches |
| `moog/muse` | Moog Muse: 102 controls off one appendix that four documents print identically, two of whose rows are misprinted - and two timbres on two MIDI channels out of the box |
| `moog/sub_37` | Moog Sub 37: 114 controls, every one of them the same as the Subsequent 37's, established by reading both charts rather than assumed |
| `moog/subharmonicon` | Moog Subharmonicon: reads a note as an offset from C4, not as a pitch, and answers to one controller its manual does not list |
| `moog/subsequent_37` | Moog Subsequent 37: 114 controls in CC and NRPN pairs, out of a chart whose empty cells were proved empty rather than unread |
| `native_instruments/maschine_plus` | Native Instruments MASCHINE+: two controller numbers in 243 pages, both of them ones the MIDI specification had already spoken for - every other one belongs to the owner, and the document that would hold them ships inside an application |
| `novation/bass_station_ii` | Novation Bass Station II: 94 controls across three products that share one guide, and one controller number the guide prints that the MIDI specification says is something else |
| `novation/circuit` | Novation Circuit: 299 controls over two synths, four drums and a session, from a guide that prints seventy-four of its rows twice and leaves thirty-nine out - two of the eight macro knobs among them |
| `novation/circuit_rhythm` | Novation Circuit Rhythm: 74 controls over eight sample tracks and a project, out of the third Circuit here - where 64 of its numbers are also the Circuit's, only eleven of those mean the same thing, and the master filter moved |
| `novation/circuit_tracks` | Novation Circuit Tracks: 358 controls, the most here, over two synth tracks, four drum tracks, two MIDI tracks and a project - including eight the maker's contents page files as a table of values rather than of controls |
| `novation/mininova` | Novation MiniNova: 557 controls off a nine-sheet chart, where 105 answer to a controller number and the other 452 only to an NRPN, and no parameter to both |
| `novation/peak` | Novation Peak: 246 controls off two documents three firmware releases apart, 33 of which carry no default, because the maker's default column does not agree with itself |
| `oberheim/teo_5` | Oberheim TEO-5: 198 controls off an implementation document that says in its own words the map belongs to a Sequential synth |
| `polyend/tracker` | Polyend Tracker: 80 controls in two maps that are live in different modes - the performance effects and mixer whenever it listens, the instrument's own parameters only in synthesiser mode - plus one controller the manual's table drops and the instrument's own screen shows |
| `pwm/malevolent` | PWM Malevolent: from its quick-start guide alone, and says so |
| `roland/d_50` | Roland D-50: the manual twice sends you to a MIDI implementation chart that is not in it, so this carries no controls - only the two ranges its pedals may be set to send |
| `roland/fantom_6_7_8` | Roland FANTOM-6/7/8: 31 controls, every one of them the MIDI specification's own assignment under its own name, out of a 67-page implementation whose transmit section names five fewer than its receive section and says why |
| `roland/juno_106` | Roland JUNO-106: two controller numbers in the whole instrument, and everything else it can be told is system exclusive |
| `roland/mc_101` | Roland MC-101: 28 controls over four tracks and a fifth channel that makes no sound, from a chart its maker publishes in numbered editions - of which the middle one is missing, so one firmware step was never printed |
| `roland/mc_707` | Roland MC-707: three editions of one chart served from one path, a control channel that makes no sound, and an effect send two documents put on two different numbers |
| `roland/s_1` | Roland S-1: 54 controls out of two tables that each hold half the answer - a chart with ranges and no names, a list with names and no directions - and two of them told apart only by a drawn waveform |
| `roland/tr8s` | Roland TR-8S: eleven voices of four controls, and two it only sends |
| `roland/tr_1000` | Roland TR-1000: 66 controls off a real chart, which is nine firmware releases behind the instrument it describes |
| `roland/tr_6s` | Roland TR-6S: 34 controls, 33 of which are the TR-8S's - and one the TR-8S has not, named BEAT and explained nowhere |
| `sequential/prophet_5` | Sequential Prophet-5: 64 controls off a real MIDI implementation, which is also the Prophet-10's and is older than two of the instrument's own operating systems |
| `sequential/prophet_6` | Sequential Prophet-6 keyboard and desktop module: 113 controls, most reachable by CC and by finer NRPN, from an appendix its maker prints three times over - twice in the English manual and once again in the German - with no two printings agreeing |
| `sequential/take_5` | Sequential Take 5: 170 controls, most reachable by CC and by finer NRPN |
| `soma/pulsar_23` | Soma Pulsar-23: every note and controller assigned by MIDI learn |
| `synthstrom_audible/deluge` | Synthstrom Audible Deluge: no fixed controller or note map at all, read from both of the guidebooks its maker publishes - one per display edition - whose last chapter turns out to be a reprint of a user-written guide |
| `teenage_engineering/ep_133_ko_ii` | teenage engineering EP–133 K.O. II: four controllers and 48 pads, out of a web guide whose implementation chart says yes with a picture and no with a letter |
| `teenage_engineering/op_1` | teenage engineering OP-1: publishes no controller number at all - four incoming control changes are routed by the player, per sound |
| `teenage_engineering/op_xy` | teenage engineering OP-XY: its maker publishes one guide twice, and the two editions give different numbers for the same row |
| `udo_audio/super_6` | UDO Audio Super 6: 86 controls off the most complete implementation a new maker has brought here - every number from 0 to 127 given a row, and 41 of them carrying an NRPN that is the controller number plus 1024 |
| `vermona/drm1_mkiv` | Vermona DRM1 MkIV: a drum machine that ignores controller data |
| `voce/electric_piano` | Voce ELECTRIC PIANO: 16 or 32 voices, depending on the chorus |
| `waldorf/blofeld` | Waldorf Blofeld: a chart with a row for all 128 controller numbers, seventeen of which are not controls - and one manual covering a Desktop with no MIDI out and a Keyboard with one |
| `waldorf/iridium` | Waldorf Iridium: no control map at all - almost every parameter is reached by MIDI learn, so what is here is the fifteen controller numbers the maker fixes, out of a manual two product pages serve as the same bytes |
| `waldorf/streichfett` | Waldorf Streichfett: controls whose values are exact numbers, not bands |
| `yamaha/dx7` | Yamaha DX7: sends one set of controllers and answers to another, out of a 1983 manual that only exists as a scan |

The set is a starting point rather than a catalogue. `moog/dfam` is five lines,
because the DFAM has no MIDI at all and saying so is worth more than saying
nothing. Three others - the Labyrinth, the MODEL D and the DRM1 - are nearly
as short for the same reason: somebody read the whole manual and found no
control changes, and the file records that it looked.

### Starting from a MIDNAM file

If your instrument has a `.midnam` file - Ardour bundles several hundred -
`pymidiinstrumentdefs.midnam` will start a definition from it:

```python
import pymidiinstrumentdefs.midnam

draft = pymidiinstrumentdefs.midnam.read_file("Moog_Minitaur.midnam")

pymidiinstrumentdefs.midnam.suggested_name(draft)   # 'moog_music/minitaur'
print(pymidiinstrumentdefs.midnam.to_yaml(draft))
```

What that lands is a **draft**, and it says so in its own first line. MIDNAM
carries a control map and nothing else - no polyphony, no note range, no
velocity response - and the numbers it does carry are worth checking against
the manual. It stays marked `unverified` until you replace the `source` line
with what you checked it against.

**This is not how the bundled definitions were made.** Those came from manuals,
and none of them is an import. [Sources](#sources) measures how far a `.midnam`
can be trusted, on the one instrument where both can be compared.

## Sources

**A definition is only as good as its `source` line, and that line is the
authority - not this README.**

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
a working implementation of the same machine. The MiniFreak's second source is the
maker's own firmware release notes, which carry one control - CC 7, volume - that
its manual never mentions, and the file says so where it records it.

**None of them was imported from a `.midnam` file, and none ever will be.** The
importer is a tool for starting a definition of *your* instrument; it is not
where ours come from.

Three tests hold that line, so it is a property of the package rather than a
promise in a README: one refuses to ship a definition that does not name a
document and cite pages, one refuses anything still marked `unverified`, and one
refuses anything the importer wrote.

The Minitaur is the worked example of why that second source matters. Its
manual prints the key-priority bands as `0-42`, `43-84`, `87-127` - leaving 85
and 86 assigned to nothing - and the firmware addendum corrects the third band
to **86**. This package carries 86, and the file says why it differs from the
printed table. That is the level of care every bundled definition is held to,
and it is why a `source` line records pages rather than saying "the manual".

**Anything imported is a draft, and is not held to that at all.**
`pymidiinstrumentdefs.midnam` starts a definition from a `.midnam` file, and
what it lands says `imported from <file>, unverified` in its own source line,
keeps saying it, and is reported by the validator until a person replaces it.

That is not a reason to avoid importing - it is a good way to start and a poor
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

MIT - you are free to use, copy, modify, merge, publish, distribute,
sublicense, and sell copies of this software in any project, including
commercial and closed-source applications. The only requirement is that you
include the LICENSE file when redistributing the software. See
[LICENSE](https://github.com/simonholliday/PyMidiInstrumentDefs/blob/main/LICENSE)
for the full text.
