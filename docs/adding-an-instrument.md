# Adding an instrument

This is how to write a definition somebody else can trust: where to find what your
instrument's maker published, how to tell which document actually describes your
unit, how to read it without quietly losing half of it, and how to cite it so a
stranger can check every number you wrote.

You do not need permission to write a definition. Drop a file beside your project
and it beats anything bundled here, by design. This guide matters when you want the
numbers to be *right* — and it is what a definition offered to the bundled set is
held to.

**One promise runs through all of it: every number in a definition can be traced to
a document its maker published, and to the place in that document where it appears.**
Nothing here is remembered or copied from another database, and where a definition infers
anything from what a document does say, it says so and why.

## 1. Find what the maker published

Instrument makers publish in three shapes, and it is worth knowing which one you are
dealing with before you start looking:

- **A page per product.** Elektron, Arturia, Roland, Novation, Behringer, Waldorf and
  Erica Synths each give a model its own downloads or support page.
- **One page for the whole range.** Moog and Dreadbox publish a single downloads page
  filtered by product; Teenage Engineering keeps its guides together.
- **A separate MIDI implementation document.** Korg, and often Roland, Novation,
  Sequential and Oberheim, publish the CC and NRPN tables *apart from* the manual.

That third case matters more than it sounds. Where a maker publishes a separate MIDI
document, **the manual will not contain the CC numbers at all.** A 68-page owner's
manual for a current Korg synth prints three CC numbers in total and refers you
elsewhere for the rest. If you only read the manual, you will conclude the instrument
has almost no MIDI surface, and you will be wrong.

### The download often takes two steps

A link on a downloads page frequently points at another *page*, not at a file. Fetch
it with a script and you get `HTTP 200`, a perfectly ordinary response, and a few
kilobytes of HTML — which will happily save itself as `manual.pdf` and hash like a
real document.

**Check what landed before you trust it.** `file` on the saved bytes, or simply open
it. If it is HTML, the real file is usually linked inside it, often on a content
delivery network under a path that is a hash — a name that says nothing about which
product it belongs to, and that may not survive the maker's next site change.

So record **two** addresses for every document:

- **the landing page**, which a person can navigate to next year, and
- **the file URL**, which is what you actually read.

## 2. Know what each kind of source is good for

Not every source can do every job. Three tiers, and the difference between them is
the difference between a definition that holds up and one that does not.

**Can be the only source for a fact**

- The maker's MIDI implementation document or chart.
- The maker's user manual.
- The maker's firmware addenda and release notes.
- The maker's own published specifications, such as the specification list on a
  product page — for the facts they state, and only once you have saved a copy of
  what you read (see below).

**Can confirm a fact, but should not be the only source**

- The maker's support articles and knowledge base.
- The parameter list inside the maker's own editor or librarian software.
- A measurement you took yourself from the instrument — which is a fact about *your*
  unit and its firmware, so say so. It can stand alone for **a single fact the
  maker's documents leave open**, in a definition otherwise traced to them, provided
  the file says plainly that it was measured, on what firmware, and when. Measure it
  so the instrument reports the answer, not your ear: a value read back from its own
  SysEx dump can be checked by someone else, and an impression of a sound cannot.

**Can only tell you where to look, or that something is worth re-reading**

- Community databases such as MIDI Guide, and `.midnam` files.
- Working code that drives the same machine.
- Documents a third party wrote: a reviewer's table, a retailer's summary, somebody's own
  chart. **A third party's copy of the maker's own manual is a different thing**, and the
  next paragraphs say when it can carry a definition.
- Forum posts and videos.

**A third party's copy of the maker's own manual can stand in for the maker's.** Where the
maker is gone, or no longer serves the manual that holds the MIDI map, a copy somebody
else keeps - an enthusiast's scan, a retailer's download, a support mirror - may carry a
definition, because what it holds is still the maker's document. Four conditions come with
it:

- **Label it.** Say in the source that it is a third-party copy: whose copy it is, where
  you fetched it, and why no copy from the maker was used - the maker is gone, or its link
  is dead, with the address and the date.
- **Compare it.** Look for a second, independent copy and compare the two, and check every
  number the copy shares with anything the maker does still serve: a quick start guide,
  release notes, a specifications page.
- **Read it twice**, by eye where it is a scan, with a blind second reading checking every
  number and every quotation.
- **Replace it when you can.** If the maker's own copy comes back, cite that instead.

**Another model's document can give a number only where your instrument's own document
says the two share an engine.** A Novation Summit's guide calls it a two-part instrument
*"built around a dual implementation of Peak's synth core"*, and it prints the numbers of
one modulation matrix slot where the Peak's manual numbers all sixteen. That sentence is
what lets the Peak's manual supply the other fifteen, which is how `novation/summit` carries
them. Believing two instruments are related is not enough: the maker has to say so, in the
document about the instrument you are writing for. It lets a definition carry a number its
own documents do not print, which is why the condition is narrow. Where it is met:

- cite the other model's document in `sources` like any other, and say in the account that
  it describes another instrument (until the format has a field for that);
- state the inference in the account, with what supports it - for the Summit, the two
  documents give the same parameter names, ranges and defaults, and the same numbers for
  the one slot both print;
- and expect the citation check to read that document like any other.

**A web page changes without warning, so save what you read.** A product page is
the maker's word, but unlike a PDF it serves different bytes to everyone and can be
edited overnight. Save a copy — its visible text is enough to cite, and keep the page
as fetched beside it — record the SHA-256 of the copy you cite, and say when you read
it. No later fetch will match that hash, and it is not meant to: it proves what the
page said on the day. Where what you cite is not in the visible text, because the page
carries it in a script, cite the page as fetched as a source of its own, with its own
SHA-256: a TD-3's product pages list their downloads that way, and the citation check
reads a saved `.html` file as it reads a text file.

The worked case is a string machine whose manual never states its polyphony. Its
maker's hardware page does — *"128 voice fully polyphonic Strings section"* and
*"Eight voice polyphonic Solo section"* — and an automated summary of the maker's site
attributed the first figure to the software version instead. **Read the page itself
whenever a fact depends on which product it describes.**

**Why community databases sit in the third tier, even when they are right.** They are
transcriptions of the same manuals you are reading, made by people who were not asked
to record which manual they used. Checked against a maker's own document for one
current synth, one such entry got every one of its 60 control numbers right — and was
missing seven more the maker documents, including the NRPN transport, and carried no
NRPN parameters at all where the maker lists sixty-one. Nothing in it was wrong. It
was simply not the whole thing, and nothing on the page told you that.

Use them the way they are useful: **to disagree with you.** If a database and the
maker's document differ, you have found somewhere to look twice. Never lift a value
from one.

## 3. Work out which firmware the document describes

This is the step most often skipped, and it silently invalidates definitions.

A document's date and the date shown beside it on the download page are **different
dates**, and neither one tells you which firmware it covers. A current Korg synth's
MIDI implementation states `Revision 1.01 (2020.2.10)` in its own first line, while
the download page lists it as `2020.03.10` — a month later, the same day as a firmware
release. The document is *older* than the firmware, and describes it anyway, because
it was written ahead of the release.

**So do not reason from dates in either direction.** Do this instead:

1. Read the firmware release notes and note what they say changed about MIDI —
   "added CCs for the joystick", "aftertouch reception", and so on.
2. Search the document for those things by name.
3. If they are there, the document covers that firmware. If they are not, you have
   found a gap, and the definition should say which firmware it describes.

**Then record it in the file, in the two places that answer two different
questions.**

- **`model.firmware` is the firmware this definition describes**, spelled as the maker
  spells it. **Quote it.** YAML reads `1.10` as the number 1.1, which is a different
  release, and a maker who ships both would have one recorded as the other. The
  validator refuses an unquoted version for exactly that reason.
- **A release-notes source says what was current when you looked.** Its `edition` is the
  newest firmware the maker had published, and `retrieved` is the day you read the page.
  A definition whose `model.firmware` is behind that edition is one to revisit.

```yaml
model:
  name: Digitone
  firmware: "1.43"              # the firmware this file describes

sources:
  release_notes:
    kind: release_notes
    title: Digitone OS release notes
    edition: OS 1.43            # the newest published when this was checked
    landing: "https://www.elektron.se/support-downloads/digitone"
    retrieved: 2026-09-14
```

**Where the instrument has no firmware at all, write `firmware: none`.** That is a
checked absence, as `midi: none` is, and it is not the same as leaving the field out,
which says only that nobody looked. A hardware revision the maker sells as its own
thing is `revision` instead, as a Vermona DRM1 MkIV is not a MkIII.

**No history is kept**: the version this file describes, and the date somebody last
asked what the newest one was.

## 4. Read the document without losing half of it

**Cite printed page numbers, not the reader's page numbers, and check the offset for
every document separately.** A manual whose printed page 1 is the PDF's page 10 will
have you citing pages that do not exist. Some manuals print two pages to a sheet.
Some, like the Korg one above, have no offset at all. There is no general rule; check
each one.

**A text document has no pages.** Makers do publish plain-text MIDI implementations —
one such runs 2,221 lines across fourteen numbered sections and contains no page
breaks whatever. Cite its **section**, the way the document numbers it, and quote
enough of the row that a reader can search for it. How to write that so the quotation
checker can read it is under *Write a quotation's locator the one way a machine can
read*, below: declare the source `paginated: false`, and cite it by its key, a comma, and
then the section.

**Extract the table twice, and compare the two.** This is the single highest-value
habit in this guide, and it is worth spelling out why.

Writing the definition for the Korg above, a script pulled 47 control changes out of
that text file. It ran cleanly and reported no errors. The real number is **67**. The
pattern matching the table's hex column had been written as `[0-9A-F]` and the maker
prints lowercase hex, so every row whose hex digits contained a letter — including
CUTOFF and RESONANCE — was dropped in silence. A second extraction, done
independently, found all 67 immediately.

**And this applies to the words as much as the numbers, because an extractor's reading
is not the page.** Writing the Machinedrum definition, a correct quotation failed
`check_quotations.py`, which reported it was on "no page of any document held" — the
strongest thing that tool says. The transcription was right. `pypdf`, which the tool
reads with, returns that manual's `non-registered` as `nonxregistered`: across 126
sheets it finds 2,816 hyphens where PyMuPDF finds 3,764, and it puts an `x` inside 61
words. They are the words a MIDI definition reaches for — `highxpass`, `lowxpass`,
`hixhat`, `prexdelay`.

So **if the gate cannot find a quotation, check whether it crosses a hyphen before you
change a word of it.** The checker folds hyphens away deliberately, so a hyphen the
extractor *drops* costs nothing; one it replaces with a letter is the single case that
folding cannot absorb. Open the page, read what is printed, and quote that. Where the
word itself is unquotable, quote the halves either side of it and say in the file why —
do not reach for brackets or an ellipsis to paper over a hyphen the page really prints.

**Count the rows in the source and account for every one of them.** Every row is
either in your definition, or excluded for a reason you can state: it is a channel
mode message, it is a blank row, it is an NRPN rather than a CC, or the format has no
way to carry it. "I did not notice it" is not one of the reasons.

**Expect the maker's document to contradict itself, and record it when it does.**
Reading one 2,221-line implementation twice turned up a footnote marker the document
never defines, a row citing a footnote from the wrong section, a value list ending in
`128` where MIDI has no such value, two adjacent bands that overlap at their shared
edge, and one parameter whose polarity is given one way where the instrument transmits
it and the other way where it receives it. None of this is unusual. **Never pick a reading
silently.** What a definition carries depends on the shape of the disagreement.

### When a document disagrees with itself

**A value is recorded where everything the document says about it agrees, or where
something outside the disagreement settles it - and the disagreement is written down
either way.** Five cases come up, and the question that sorts the second from the third is
whether the two statements could both be true of the same instrument.

1. **One statement that looks wrong: carry it, and doubt it in writing.** A Bass Station
   II's guide gives its modulation wheel as CC 0, which the MIDI specification gives to
   bank select, and that guide is the only document there is. Its definition carries 0,
   because that is what the maker published, and says in a comment that the number is very
   hard to believe. A definition says what the maker said and where that looks wrong; it
   does not correct the maker.

2. **Two statements that cannot both be true: carry neither, and say what both were.** A
   Novation Peak's parameter list prints most of its defaults twice, as the number sent
   and as the screen shows it, and the row's own range gives the arithmetic between them:
   on a range printed `0-127 (-64 to +63)`, `64 (0)` checks out, and Glide Time's
   `0 (60)`, on `0-127 (0 to +127)`, cannot. With its init patch table and its text as
   further statements, 32 of its 246 controls carry no default for that reason, and the
   file sets out each way the document failed to settle them. The two statements need not
   sit side by side - a Circuit Tracks guide gives five defaults one way in its control
   map and another in its patch format further on, and those five carry none either. And a
   whole table can fail this way: a volca fm's implementation prints one control's ten
   bands in hexadecimal and in decimal, the two disagree in four rows, and the decimal
   column overlaps itself, so its definition names the ten bands and numbers none of them.

3. **One statement narrower than the other: look outside the pair first.** An Arturia
   PolyBrute 12's specifications list its aftertouch as *"channel aftertouch"* and, a few
   lines further on, as *"channel or polyphonic"*. Both could be true of an instrument
   that does both, so this is not the second case. The body of the manual settles it -
   four of its five aftertouch modes send polyphonic aftertouch when MPE is off - so the
   definition records that it sends aftertouch and sets out all three statements. **A third
   witness has to be about the same thing**, not merely nearby in the same document: those
   pages are about what the keybed sends, so they settle that and say nothing of what the
   instrument answers to, which the definition takes from another page. Where nothing
   outside the pair settles it, carry neither, as in the second case.

4. **A clause that cannot be read is damaged, not competing** - one that does not add up
   on its own terms, such as a list that skips a member of its own sequence. A Prophet-5's
   implementation gives its program change as 0-39, and then enumerates thirty-two values
   across Banks 1, 2, 4 and 5, skipping Bank 3, where its bank selector cycles through
   five. The enumeration is not a second statement of the range so much as a sentence that
   does not hold together, so the figure the row states outright stands, and its user
   guide's 400 programs, in groups of five banks of eight, agree with it. The definition
   gives the reach as 40 and sets the enumeration out, so that a reader can see what was
   set aside.

5. **Two editions under one version stamp are a pair.** Roland has served two files of the
   TR-6S's MIDI implementation chart, both printing Version 1.00 and the same date, and
   they disagree about one note number: 58 in the earlier file, 55 in the later. A maker's
   version stamp is not evidence that two files are the same document, and the later file
   is not right merely for being later. So they are one document saying two things, and
   the cases above apply to them as to any other. Cite both, so that a reader can see the
   disagreement.

**Two documents that disagree are the same problem**, and the same answers apply. The
TR-6S's chart and its parameter guide disagree about system exclusive, and its definition
records neither.

**A document that gives a thing twice is a document you can audit, so audit it.** A maker
who prints a value in hexadecimal and in decimal, or a default in a column and again in a
patch table, has handed you a check that costs nothing to run, and several of the cases
above were found exactly that way.

## 5. Write the definition

**Name it by its path.** `corpus/moog/matriarch.yaml` loads as `moog/matriarch`. Both
halves match `[a-z][a-z0-9_]*`. The folder is the maker's short name — `moog`, not
`moog_music` — while `model.manufacturer` is free text, spelled the way the maker
prints it. A maker whose name begins with a digit is spelled out as it is said, so
1010music's folder would be `ten_ten_music`.

**Transcribe from the maker's document; never import and ship.** The importer that
reads `.midnam` files is a good way to *start* your own definition and a poor place to
stop: what it produces marks itself `unverified` in its own source line, and the
validator says so.

**Leave out anything the source does not give you.** A definition that is silent about
polyphony is honest; one that guesses `1` is not.

**Write `none` only where you searched every page**, and let the source line say you
did. This is the smallest complete definition in the bundled set, and it is a real
instrument:

```yaml
definition: 1

model:
  manufacturer: Moog Music
  name: DFAM

source: >-
  User manual, 44 pages, in which the word "MIDI" does not appear - verified
  across every page. The instrument is driven by clock and trigger at the
  patchbay and by its own 8-step analogue sequencer.

midi: none

voice:
  addressing: none
  polyphony: 1
```

**`addressing: none` is an instrument no note reaches; `any` is one that takes every note
and reads nothing from its number.** A volca drum's factory chart recognises notes 0 to 127
and remarks "Each sound does not correspond to a note number": the channel picks the part, and
the note says nothing more. That is `any`. Keep `none` for the DFAM's case, where there is
nothing to send a note to.

**Search for what sends a controller, and not only for the word.** A manual can have its
instrument answer to a controller without naming one. A Model D's manual never says
`control change`, and it has `the modulation wheel on a MIDI keyboard` adjust a depth. So
before writing `control_change: none`, look for a wheel, a pedal, a footswitch, a joystick,
a ribbon, breath, modulation, expression, sustain and volume too, and read every hit. Where
the instrument answers to one and the maker prints no number, leave `control_change` unset
and quote the sentence: `none` would be untrue, and a control needs a number its maker
prints.

**For `nrpn`, a chart that lists every controller number is a search of every page.** An
NRPN travels on controllers 98 and 99, with its value on 6 and 38, and its registered
counterpart, the RPN, travels on 100 and 101 with the same two for its value. So where a
MIDI implementation chart lists every controller number the instrument uses, and 6, 38 and
98 to 101 are not among them, the chart has said that the instrument takes no NRPN, and
`midi.nrpn: none` records it. Say in a comment beside it which numbers the chart does
list, so a reader can see the absence was checked rather than assumed.

**Put a blank line between the topics of your `source` account.** It is a folded
scalar, so a single line break becomes a space and the whole account arrives as one
string — but a *blank* line survives as a real line break, and that is where a reader's
page starts a new paragraph. An account of any length that has none reads as one slab.
Open a topic in capitals where that suits it, as most accounts here do — `NOT RECORDED,
and marked in place:` and the like — and put a blank line before it either way, so the
breaks do not depend on anyone recognising a lead-in. Nothing about this changes what an
account says, only where it breaks.

**An NRPN printed as two columns is recorded as one number.** Many makers print an
NRPN's parameter number whole, and it goes in `nrpn` as printed. Others print an MSB
column and an LSB column, as Elektron does: record `nrpn` as **MSB x 128 + LSB**, which
is the number that goes on the wire, and say so in a comment. The citation check knows
both forms - it looks for the number, and where that is not on the page for the two
halves - and it reports how many it could only find as halves, because small numbers are
easy to find on a page full of them.

**A number printed only in hexadecimal is written in decimal.** Some makers print a
message as its bytes, so a controller appears as `Bn 4A xx` and its number, 74, appears
nowhere. Write 74, as every number in a definition is written, and cite the page. The
citation check looks for 74 first and, only if it is nowhere else, for `4A` as a word of
its own, in capitals. It names each number it found only that way, so read each one on
its page: prose prints short hexadecimal words too, and a power adapter rated at `1A`
would answer for controller 26. It never reads a form made only of digits as
hexadecimal on its own, because a page printing `40` far more likely means forty than 64.
The exception is a form the maker marks: `0x21` is 33 whatever its digits, and is read in
either case and at any width. Its digits are never read as a decimal number, so a definition
holding 21 is not found on a page that prints only `0x21`. **A marked form is read as one
number and never as two bytes**: `0x045D` is 1117, so an NRPN whose two bytes a maker runs
together that way, meaning MSB `04` and LSB `5D`, is reported missing and has to be read by
hand.

**An NRPN printed as two hexadecimal bytes is one decimal number too.** Korg's RADIAS
gives Vocoder Band14 Panpot as `04  5D`: write 4 x 128 + 93 = 605. The citation check
looks for 605, then for `04` and `5D` side by side on one line with nothing but spaces
between them, and only then for a 4 and a 93 anywhere in decimal. It reports how many it
found only as such a pair. Standing side by side is what lets a byte made only of digits
count there: `04  60` is found for 608, where a `60` alone would be read as sixty.

**The pair is matched wherever it stands, so read every row on its page, both bytes.**
The check cannot tell one row from the next, and it does not refuse a slip: `04  5D` read
as one number is 1117, which is not found as a pair and is still found if an 8 and a 93
are anywhere on the cited pages in decimal. Where a definition's NRPNs are found both
ways, some as pairs and some only as decimal halves, it names the fewer of the two, or
all of them where there are as many each way, and those are the ones to look at first.
That catches a slip on one row. It does not catch one made on every row: the wrong
numbers are then the many, or are other rows' pairs.

**So the check also asks whether each pair stands beside its label.** It counts the NRPNs
whose two bytes are on a line that also carries the control's `label`, spacing, case and
punctuation aside, the label standing as words of its own in what the line holds besides
the pair. A control that gives no label is compared by its key. Where your labels are the
table's own words that line is the control's row, and a number taken from another row is not
on it: on the two definitions here whose NRPNs are printed as pairs, every one is beside its
label, and with each number moved down a row, none is. Once two or more are beside their
labels, and they are most of the NRPNs whose two bytes stand side by side on a cited page at
all, an NRPN that is not beside its own is named, and that is how a byte of the first bank
read as decimal shows: `00 14` held as 14 is found as itself, because the page prints a 14,
and is not beside its label. Two kinds are not named: one found as two halves in decimal,
which the report sets out above, and one of 128 or more printed whole, which is a number read
off another table and no byte misread. A number named that way is not thereby wrong, and the
report says of each whether it is printed whole. Where your labels are your own words the
count is
nought, which says nothing about your numbers, so it fails no definition. And it is a check
of the row and not of the base: two decimal numbers on a label's line are read as bytes too.
No other way of setting two bytes down is read: not with a bar, a comma or a colon between
them, not with an `H` after each, and not set tight against a full stop, a colon, a stroke or
a hash.

**Stepped controls: bands and exact values are different things.**

- `values` holds where each **band** starts, for a document printing `0-42 = Off`.
- `choices` holds **exact** values, for a document printing `0 = Off`.

```yaml
  sustain_pedal:
    label: Sustain Pedal
    cc: 64
    values: {"off": 0, "on": 64}

  string_registration:
    label: String Registration
    cc: 70
    choices: {base: 0, both: 1, octave: 2}     # "2 = 8va"
```

A control never has both. Where the document names the states but not their numbers —
or lists a different number of states from the range — **keep the control continuous**
and name the states in a comment. Never number states by the order a list prints them
in. An on/off parameter printed as `0-1` stays `range: [0, 1]` unless the document
says which number is which.

**`default` is the value a control starts at, where the maker prints one** - in a default
column, an init patch table, or the text beside a parameter:

```yaml
  voice_mode:
    label: Voice Mode
    nrpn: 2
    range: [0, 4]
    default: 3
```

Write the number that goes on the wire, which is not always the number on the screen. A
Novation list prints `64 (0)` and never says which is which; the row's own range, printed
`0-127 (-64 to +63)`, is what shows that 64 is sent and 0 is shown. The validator refuses
a default outside the control's range. **Defaults are often stated twice** - in a column
and again in an init patch table - so they are often where a document disagrees with
itself, and section 4 says what to carry when it does.

**Where the documents do not establish a range, say `range: unknown`.** Leaving `range` out
does not say that: a control with no `range` is 0 to 127, which is a claim. A DeepMind 12's
NRPN table prints its modulation sources as 0-22, and the same edition's list of sources runs
to 24, so neither figure can be carried as the range. And a Pro 3's guide lists 353 NRPNs by
name with no range beside any of them, where 0 to 127 is known to be wrong for some.

```yaml
  mod_1_source:
    label: Mod 1 Source
    nrpn: 93
    # The table prints 0-22 (manual p. 137), and the list it points to has 24 (manual p. 93).
    range: unknown
```

Put what the maker printed in the comment, with its page. A program reading the file is told
`range_known` is false, and is given the widest range the message can carry - 0 to 127 for a
controller, and 0 to 16383 for a controller with a fine half or a control reached only by
NRPN - so that it can still send every value that message might take. A control with both a
controller number and an NRPN is given the controller's range, and nothing is made up for its
NRPN: state `nrpn_range` beside the word where the documents give it. A control like this
may have `choices`, which are exact values, and a `default`. It may not have `values`: the
last band runs to the top of the range, and there is no top. **The word needs a reader that
knows it**: one older than the release that added it refuses the file, where it only warns
about a field it does not know.

**Three kinds of fact, and only one of them belongs in your file.** Facts about the
MIDI specification are not your instrument's parameters. The channel mode messages,
CC 120 to 127, are the clearest case and **the validator refuses them outright**.
Data Entry on CC 6 and 38 is the next clearest and the validator does *not* refuse it,
because it cannot: a maker may document that pair as a control of its own, and one in
this corpus does — the DX7's transmitted table calls CC 6 "the data entry knob", a
front-panel control, and the definition carries it. So leave 6 and 38 out when they are
only how an NRPN's value travels, and say in a comment why they are there when they are
not. Facts about *your* rig — the channel you happen to use — are not properties of the
model.
`channels` is the range the instrument can be set to. Anything the format cannot yet
express goes in a comment, never in an invented field.

**`control_change` says two things a list of controls cannot.** `control_change: none` is a
checked absence: somebody read the documents and the instrument answers to no controller, as
`midi: none` says of MIDI altogether. `control_change: learned` says the owner assigns
controller numbers, by MIDI learn or by setting a number in a menu, so no file can publish
them. **`learned` may stand beside controls.** The controls are then the numbers the maker
fixes, or the ones it prints as what the instrument ships sending, and the word says the rest
is the owner's. Waldorf's Iridiums have fifteen or sixteen numbers their maker fixes, most of
them modulation sources, and map any other parameter by learning; a MONTAGE prints the number
each of its physical controllers ships on, and every one can be moved. The paragraph on
`assignment` below is how a control says the owner can move it. Leave `control_change` out
where neither word is so.

```yaml
midi:
  # "the maker's sentence about giving a parameter a controller" (manual p. 12)
  control_change: learned

controls:
  # A number the maker fixes, from its table of modulation sources (manual p. 34).
  mod_wheel: {label: Mod Wheel, cc: 1, direction: receives}
```

`voice.note_map: learned` is the same word for the notes in `voice.voices`: the owner assigns
which note plays which voice, and a map the file gives is then where the instrument starts and
not a fixed fact. `fixed` says the maker's map cannot be changed, and leaving it out says
nobody has recorded which.

**Bank select is in the MIDI specification too, and it is carried anyway, wherever the
maker numbers it.** CC 0 and CC 32 choose a bank of programs rather than shaping a sound,
and they go in as controls all the same, with the maker's labels and ranges:

```yaml
  bank_select_msb: {label: Bank select MSB, cc: 0, group: system}
  bank_select_lsb: {label: Bank select LSB, cc: 32, group: system}
```

**A row the maker publishes as neither sent nor received is carried as well, with
`direction: none`.** An AstroLab's table prints Master Volume on 7 and then says `Never` under
Sending and `Never` under Receiving. Left out, that row would look like one nobody read;
carried, it says the maker answered, and a consumer looking for something to send passes over
it. The other directions are `receives` and `transmits`, for a row that travels one way only,
and `both`, which is what leaving `direction` out means.

```yaml
  master_volume: {label: Master Volume, cc: 7, direction: none, group: master}
```

**A number the owner can change says so with `assignment`.** Most controller numbers are the
maker's, and a control that leaves `assignment` out is one of them. `assignment: default` is a
factory assignment the owner can move to another number: a microKORG's panel numbers come from
a table whose column is headed "Initial". `assignment: slot` is a fixed number whose
destination the owner picks, like the four inputs of an OP-1 field's MIDI LFO.
`assignment: "off"` is a number the maker recommends and leaves switched off until the owner
enables it, like a KRONOS's KARMA controls and pads; it is quoted because YAML reads a bare off
as false. A panel can then label a number with no `assignment` by its parameter, offer a
`default` as where the instrument starts, show a `slot` by its position rather than a
destination, and say that an `"off"` number has first to be switched on.

```yaml
  filter_cutoff:    {label: Cutoff, cc: 74, group: filter, assignment: default}
  midi_lfo_input_1: {label: MIDI LFO input 1, cc: 1, group: midi_lfo, assignment: slot}
```

**MPE is two fields, and they answer different questions.** `midi.mpe` says whether the
instrument takes part in MIDI Polyphonic Expression at all, and which way: `receives`,
`sends`, `both` or `none`, the words `clock` uses. `midi.per_voice_channels: true` says
something narrower, that its voices take a channel each, one note to a channel. A Cascadia
answers to MPE and sounds one note, so it records `mpe: receives` and leaves
`per_voice_channels` out; a Prophet-6's six voices sit on MIDI channels 2 to 7 under MPE, so it
records both. Several monosynths chained so that each sounds one voice of a shared polyphony
is not `per_voice_channels`: that is a rig, not a model.

```yaml
midi:
  per_voice_channels: true
  mpe: receives       # "doesn't output MPE from its own keyboard"
```

Everything else about MPE goes in a comment beside them: which channel is the master and
which the members take, the dialect (an Osmose takes Haken's MPE+), how many voices MPE can
use where that differs from `polyphony` (a Super 6 plays six of its twelve under MPE), and
behaviour that changes with the path a note arrives by. None of these has a field, and each
waits for a second instrument that needs one.

**Aftertouch says which kind the instrument answers to, and what it sends is a field of its
own.** `voice.aftertouch` takes `channel`, `poly`, `both`, `received` or `none`, and the loader
refuses any other word. `received` is for a document that says the instrument answers to
aftertouch and never says which kind: a Typhon's manual lists aftertouch among the messages it
accepts and no page says channel or poly, so writing either would read like a statement. `both`
is an instrument that answers to both kinds, even where a setting picks which one reaches the
sound - an opsix's chart recognises both, and the setting is the player's. What the instrument
**sends** is `voice.aftertouch_transmits`, true or false, as `voice.velocity.transmits` is for
velocity. A Yamaha DX7's manual sets out, in its MIDI data format, the data it transmits and
the data it receives, and only the first has aftertouch, so it records:

```yaml
voice:
  aftertouch: none              # the received data has no aftertouch
  aftertouch_transmits: true    # the transmitted data has 1101nnnn
```

A format that sets out every message received is a statement of what arrives. A short list is
not, and leaving something out of one is not a stated no: a Minimoog Model D's MIDI In line
omits aftertouch and its MIDI Out line has it, so the Model D records
`aftertouch_transmits: true` and leaves `aftertouch` unset. Which kind is sent has no field.
Say it in a comment beside the flag, as a Leviasynth's does for the setting that chooses it.

**Sending means making the message, and playing one back is not that.**
`aftertouch_transmits` is true where the instrument makes pressure messages of its own, from
keys, pads, a ribbon or a track's own parameter. A sequencer that plays back pressure it
recorded from another instrument does not make it true, and neither does a setting that
echoes at the output what arrives at the input. An ESQ-1's chart marks pressure as
transmitted beside the remark `Transmitted only if recorded`, and no page says its keyboard
senses any, so it records `aftertouch_transmits: false` with the remark in a comment.
Somebody choosing a controller, or a program deciding whether to expect pressure from a
keyboard, is asking whether the instrument makes any.

**Some instruments are several instruments.** A Digitone is four synth tracks, four MIDI
tracks and an effects unit, each answering on its own MIDI channel. A Streichfett's solo
section answers one channel above its strings. A Voce plays three parts across three
adjacent channels. Where that is so, say it with `parts`, and let each control name the
part it belongs to:

```yaml
parts:
  synth:
    label: Synth Track
    count: 4                  # four identical tracks, described once
    channel: assigned         # the player gives each one a channel
    receives: [notes, controls]
    addressing: pitches
  fx:
    label: FX
    channel: assigned
    receives: [controls]      # it takes no notes

controls:
  filter_attack:    {label: Attack Time, cc: 70, part: synth, group: filter}
  chorus_high_pass: {label: High-pass,   cc: 70, part: fx,    group: chorus}
```

**The same controller number can mean different things in different parts, and on a
multi-track instrument it usually does.** Those two rows are both CC 70 and are not the
same parameter — one reaches a synth track, the other the effects channel. Naming the part
is what tells them apart. On one such instrument, 33 of its 71 controller numbers carry
more than one meaning.

Where a part cannot be given a channel of its own but derives one from the instrument's
base channel, say that instead:

```yaml
parts:
  strings: {channel_offset: 0, receives: [notes, controls, program_change], addressing: pitches}
  solo:    {channel_offset: 1, receives: [notes], addressing: pitches}
```

Eight rules worth holding on to:

- **A control naming no part is on the base channel.** In a file that declares parts there
  is no single part to fall back on, so that is what leaving `part` off means. It is a real
  case rather than a tidy default: a Streichfett's balance, effects and performance controls
  are all of that kind.
- **So where there is no base channel, or every part takes the standard controllers, those
  controllers name their part.** A Roland MC-707's eight tracks each answer on a channel
  the player gives them, and nothing derives from a base, so a control naming no part
  would mean a channel the instrument does not have: every one of its controls names the
  track. And where each part receives modulation, volume, pan and the rest, one copy
  naming no part would say they reach the base channel alone. Write them once for each
  kind of part instead. A JUPITER-X's four parts are one kind and its drum part another,
  so its standard controllers are written twice, and the drum part's list is shorter
  because its documents give it fewer.
- **`receives` is a list because one flag is not enough.** A Voce's three parts each take
  notes *and their own program change*, while its effect controls are global to all three.
  No single true-or-false can say that. Leave `receives` out where the document does not
  say; `receives: []` says the part was found to take nothing, which is a different fact.
- **Claim only what the document says.** A Streichfett's manual says its solo section can be
  *triggered* on the next channel up. It never says a control change reaches it there — so
  that part receives `notes`, and nothing more is claimed. A control sent to a channel an
  instrument ignores does nothing, and says nothing about why. So a control naming a part
  whose `receives` leaves out `controls` is refused: the file would be saying both.
- **Where a kind of message reaches the instrument and no page ties it to the part, say
  `unrecorded`.** A volca drum on its single channel receives notes there, and its chart gives
  each of the six parts its controllers and never says which part a note sounds. With
  `receives: [controls]` alone, a program reads the part as taking no notes and draws no keys
  for an instrument that plays from them. `unrecorded: [notes]` says the third thing: notes
  arrive here, and how they reach this part is not in the documents. The words are those of
  `receives`, a kind goes in one list or the other, and `takes()` answers `None` for it. A part
  whose notes are unrecorded cannot have `voices`, and one whose controls are cannot be named
  by a control it receives: either would be the record the word says is missing.

  ```yaml
  parts:
    part_1: {channel_offset: 0, receives: [controls], unrecorded: [notes]}
  ```
- **Say whether parts share their voices.** A Digitone's eight voices go to whichever of
  its tracks plays next, so eight is a ceiling across all four, not a figure each can count
  on. A Streichfett's two sections have voices of their own, 128 and eight. Those are
  different instruments to play, and one number cannot tell them apart:

  ```yaml
  # one pool, drawn on by every part
  voice: {polyphony: 8, polyphony_shared: true}

  # a pool for each part, counted per instance
  parts:
    strings: {channel_offset: 0, polyphony: 128}
    solo:    {channel_offset: 1, polyphony: 8}
  voice: {polyphony_shared: false}
  ```

  Where an instrument lets a player divide a shared pool between parts, that division is a
  setting and belongs to their project, like the channel. Saying nothing about voices is
  still honest; one figure for an instrument with parts that take notes, without saying
  which it is, draws a warning.

  A part's figure counts each of its instances. Where the instances of one part share a
  figure between them, say so on that part. A JD-XA's four analogue parts have a voice each,
  and its four digital parts have 64 between them, divided in a way no page describes:

  ```yaml
  parts:
    analog:  {channel: assigned, count: 4, polyphony: 1}
    digital: {channel: assigned, count: 4, polyphony: 64, polyphony_shared: true}
  voice: {polyphony_shared: false}
  ```
- **A note that works a control rather than sounding goes in the part's own `voices`.** An
  MC-707's control channel turns its sixteen Scatter pads on and off with notes 60 to 75, and
  a Digitone II's effects channel taps the tempo with one note. Give that part `notes` in its
  `receives`, `addressing: voices`, and a name for each note, the way `voice.voices` names an
  instrument's drums:

  ```yaml
  parts:
    fx: {channel: assigned, receives: [notes, controls], addressing: voices, voices: {tap_tempo: 127}}
  ```
- **A part's notes may be where the owner starts, and `note_map: learned` says so.** A RADIAS
  kit puts its sixteen instruments on the same keys in every factory kit, and each key is a
  setting an owner can move. Give the part its `voices` and `note_map: learned`, as
  `voice.note_map` says of an instrument's own map; `fixed` says the maker fixes them, and
  leaving it out says nobody recorded which. It is said of notes the part takes, so it is
  refused on a part that takes none or whose notes are `unrecorded`.

  ```yaml
  parts:
    kit:
      channel: assigned
      receives: [notes]
      addressing: voices
      note_map: learned          # each key is a setting of the kit, and these are the factory's
      voices: {inst_1: 36, inst_2: 37}
  ```

**Some instruments change shape with a setting.** A Korg drumlogue answers on one channel
as it ships, and on a channel for each of its parts when a global setting says so, with a map
in which one number can mean something different on each part. That is a *mode*: a named
state of the whole instrument, in which a different map, a different set of parts or a
different channel layout holds. Declare the modes in `modes`, and let a part name the one it
exists in:

```yaml
modes:
  single:
    label: SINGLE Ch.
    factory: true             # only where a document says so
  multi:
    label: MULTI Ch.
    unparted: false           # the controls naming no part do not answer here

parts:
  part_1: {label: Part 1, mode: multi, channel_offset: 0, receives: [notes, controls]}

controls:
  bd_tune:        {label: BD TUNE, cc: 20}                  # the single-channel map
  part_1_bd_tune: {label: BD TUNE, cc: 20, part: part_1}    # part 1's, in the other mode
```

- **A part naming no mode exists in every mode**, as every part did before modes existed. A
  file declaring no modes reads exactly as it did.
- **`factory: true` marks the mode the instrument ships in, and only where a document says
  so**, on one mode at most. The drumlogue's manual calls its single-channel implementation
  the factory default. Most makers do not say, and a state entered by holding a button at
  power-on is not thereby the other one's default: leave both unmarked.
- **`unparted: false` says the controls naming no part do not answer in that mode.** Those
  controls are the instrument's own map on its base channel, and in the drumlogue's other mode
  that map is not the one that answers. Left out, it is true.
- **`channels` on a mode is the range the base channel can be set to in that mode**, where it
  differs from `midi.channels`. A volca drum's six parts sit on channels 1 to 6 and cannot
  move, which is a base channel fixed at 1; on its single channel the owner picks any of 1 to
  16. A page asks `channels_in()` with the mode's name and gets the mode's range, or the
  instrument's where the mode gives none.

  ```yaml
  midi:
    channels: [1, 1]                 # the base channel, where the mode says nothing else
  modes:
    split: {label: Split}            # six parts on channels 1 to 6, which cannot move
    single: {label: Single, channels: [1, 16]}
  ```
- **Declared modes must change something**: a part names one, or one says `unparted: false`,
  or the base channel's range is not the same in each. Modes that change nothing draw a
  warning, and so does a single mode, since a mode is one of several states.
- **A mode is the whole instrument's.** Where a setting on one track decides what a number
  means, as an Analog Rytm's machines do, that stays in words.

A page asking what answers in one mode calls `controls_in()` and `parts_in()` with its name,
and `factory_mode` names the marked one.

**A mode also lets the instrument's figure for voices stand beside a part's.** One figure for
the whole instrument and one for a part is refused, because it gives two answers to one
question, unless every part with voices of its own exists in one of two or more modes. An
OB-X8 has eight voices in every mode, and in Split mode four on each half:

```yaml
modes:
  normal: {label: Normal}
  split:  {label: Split}
  double: {label: Double}
parts:
  lower: {mode: split, channel_offset: 0, polyphony: 4}
  upper: {mode: split, channel_offset: 1, polyphony: 4}
voice: {polyphony: 8, polyphony_shared: false}
```

**And a part's instances can be told apart by NRPN rather than by channel.** An Elektron
Tonverk's audio track running its Subtracks machine holds eight subtracks, on the track's
channel, which take the same 49 parameters, the first subtrack on NRPN MSB 1 and each next one
on the next MSB. Say where the part sits with `within`, and where its instances start with
`nrpn_msb`:

```yaml
parts:
  audio:    {label: Audio track, channel: assigned, count: 8, receives: [notes, controls]}
  subtrack: {label: Subtrack, within: audio, count: 8, nrpn_msb: 1, receives: [controls]}

controls:
  subtrack_amp_pan: {label: AMP pan, nrpn: 138, part: subtrack}   # the first subtrack's
```

- **`nrpn_msb` is the first instance's MSB**, and each next instance takes the next, as
  `channel_offset` counts channels. A control on the part gives its `nrpn` as the first
  instance's number, as the page prints it, so the citation check reads printed numbers. The
  last instance's MSB must stay within 127.
- **`within` names the part whose channel each instance shares.** A part inside another takes
  no channel or offset of its own, and the part it names must have one to give. Its `count` is
  how many sit inside each of that part's instances, and more than one with no `nrpn_msb` to
  tell them apart draws a warning.
- **A control on a part with `nrpn_msb` gives an `nrpn`, in the first instance's MSB.** Any
  other NRPN would reach no instance, or the wrong one, and where there are several instances
  a controller number could not say which it reaches, so all of these are refused. And a part's instances are
  told apart one way: several of them counted by channel and by MSB at once are refused.

A part is not a panel. It says where a control is addressed, not how anything should be
drawn — that stays the consuming page's business, as with everything else here.

### Say what the maker calls each group

`group` on a control is a name for a machine. `groups` is what to call that group where a
person will read it, and it is the maker's word rather than yours:

```yaml
groups:
  osc_1: OSC 1
  analog_filter: Analog Filter
  cycling_env: Cycling Env
```

**Take the label from the document, the same way you take a number from it.** Some makers
print it for you: a MiniFreak's implementation chart has a Section column, and an Elektron
appendix heads a table per section. Where the chart is a flat list, the manual's own
section headings are the next place to look, and they are usually its walk around the
panel. Say in a comment where each set came from, as you would for anything else here.

Four rules, each of which a bundled definition needed:

- **The label is free text and the group is a name.** `arp_seq: Arp / Seq` is legal and
  `Arp Seq: ...` is not, because the group is addressed and the label is read.
- **The order you write them is the order to show them.** A group you do not name follows
  the ones you do, in file order, so labelling some and not others is a file part way
  through rather than an error.
- **A label may differ from the group's name, and sometimes must.** A MiniFreak's chart
  heads its mod wheel row "MIDI", which is a useless group name in a file that is entirely
  about MIDI and exactly right as a heading over the row it is printed above.
- **Where the maker gives no name, say so rather than inventing one.** Roland's documents
  never expand BD, SD or RC anywhere, in either manual, so `roland/tr8s` labels them BD, SD
  and RC, and its comment records where the expansions were looked for. A label nobody
  printed is a fact nobody checked.

**Give it a test.** One test of the fact the file exists for: the thing a consumer
would get wrong without it.

## 6. Cite it so a stranger can check you

The `source` field is prose, and it is the authority for the whole file. Make it carry:

- **what kind of document** it is — user manual, MIDI implementation, quick start guide,
  firmware addendum;
- **its title as printed**, including the maker's own typos, which is often how you find
  it again. **A web page's title is the one the page serves**: the text of its `<title>`,
  read from the page as you saved it, with the site's name and the punctuation as they
  come and white space run together. So `Downloads | volca drum | KORG (USA)` and not
  `volca drum downloads`. A shorter description of a page is not its title, and nobody
  searching for it will find the page;
- **its edition or revision, and its date**, as the document states them — not as the
  download page states them;
- **where it can be obtained**, so a reader is not left searching;
- **which file you actually read**, where it matters — makers reissue documents under the
  same title, and a size or a checksum is the only thing that pins down which one you
  had in front of you;
- **the pages or sections** each group of facts came from;
- **and what you checked and did not find**, where the file is silent on purpose.

A good one from the bundled set reads:

> MIDI Implementation Chart, Version 1.10, dated 4 October 2018: a single page (p. 1),
> and every row of it is below. Its 55 control numbers and 11 note numbers agree
> exactly with a working implementation of the same machine.

That names the kind, the version, the date, the locator, and the cross-check. Add
where to get it and it is complete.

### And say it again where a machine can read it

Prose is for the person. A definition may also carry a `sources:` block, which is
the same citation in fields a script can follow:

```yaml
sources:
  midi_impl:
    kind: midi_implementation
    title: minilogue xd/MIDI Implimentation     # as printed, typo and all
    edition: Revision 1.01                      # what the document says
    dated: 2020-02-10                           # not what the download page says
    landing: https://www.korg.com/us/support/download/product/0/811/
    url: https://cdn.korg.com/us/support/download/files/5227b0b2....txt
    sha256: f34014c103b0127f...
    retrieved: 2026-09-13
    paginated: false        # this one is plain text, in sections, with no pages
```

Every field is optional. Three of them earn their place by catching things prose
cannot:

- **`sha256`** pins which file you read. Checked across the definitions bundled
  here, one maker's address now serves a **later edition** than the one that was
  read — 92 pages where there were 88 — and its cited pages no longer carry all
  the facts. Nothing but a hash would have shown that.
- **`page_offset`** is what to add to a printed page to reach the page of the
  file, because there is no rule: among these manuals it is zero eleven times,
  and it is not zero three times. Where a document numbers itself in more than
  one run - an unnumbered page in the middle, and every page after it one further
  from the file - give a run for each, from its first printed page:

  ```yaml
      page_offset:
        - {from_printed: 1, offset: 4}
        - {from_printed: 53, offset: 5}   # file page 57 prints no number
  ```
- **`pages_per_sheet`** is for a manual that prints two pages on one sheet, which
  no offset can express. One definition here cites pp. 62-63 of a 40-sheet file,
  and that is only not a contradiction once the sheet count is known.

A fourth is for the case where the numbers are not text at all:

- **`pictured_pages`** names the printed pages of this document whose numbers are
  published **only as an image** — a screenshot, a photograph of a panel, a chart
  drawn rather than set. The citation checker reads text, so it finds nothing on
  such a page; declaring the page tells it that the silence is the document's and
  not the definition's, and it reports those numbers as **unchecked** rather than
  missing.

  ```yaml
  sources:
    manual:
      page_offset: 5
      pictured_pages: [99]    # the drum map is a screenshot of the maker's editor
  ```

  **Declare it only where it is true, and say in a comment how you read the
  picture.** This is the one field that switches off the strongest check here, so
  it is deliberately not inferred: a checker that excused any number absent from a
  page carrying an image would excuse an invented one on most pages of most
  manuals. The checker does verify the half it can — that a page you call pictured
  carries an image at all — and reports a page that does not as a fault, which
  catches a mistyped number and a declaration left behind after a maker revised the
  document. It cannot verify that your numbers are inside the picture. **Nothing
  but reading it twice can**, so read it twice, by eye, from the image at its own
  resolution, and look for an arithmetic relation the document itself explains.

### Write a quotation's locator the one way a machine can read

Every quotation should be followed by a locator. For a document with pages, write it in
exactly one shape:

```
"the maker's sentence" (p. 42)               one document, or one that needs no naming
"the maker's sentence" (pp. 42-43)           a spread
"the maker's sentence" (p. 42, 44)           two pages of one citation
"the maker's sentence" (user_guide p. 104)   a key from this definition's own sources:
```

**A source key, not a description of the document.** `(user guide p. 104)` is two words and
does not parse. `(user_guide p. 104)` names a key, and the quotation is then looked for in
**that document alone** — which is the stronger check, because a page number that happens to
exist in one of the other three cannot pass it.

**Nothing else goes inside the brackets of a page citation.** Not a version, as in
`(release notes 1.4.0 p. 8)`.
Not the document after the page, as in `(p. 89 of the guide)`. And not your own aside about
the quotation, as in `(p. 22, the misspelling is the manual's)` — that belongs in the
sentence around the quotation, where a reader will see it.

**A document with no pages is cited by its key, and may say where in it.** A web page or a
plain-text file has no page to turn to and is declared `paginated: false`, so its locator is
the source key on its own:
`"the maker's sentence" (release_notes)`. Where the document has places of its own, say which
after the key and a comma: `(os_updates, #243)` for an entry, `(release_notes, 1.4.1)` for a
version. The key is written exactly as it is under `sources`, and the comma has to be there.
The quotation is then looked for in the whole of that source. What follows the comma is for
your reader and is not checked. It must not look like a page, `p.` and a number, which is the
shape above and belongs to a document that has pages.

**A document that has pages is always cited by its page, never by its key alone.**
`"the maker's sentence" (manual)` used to be looked for in the whole manual, and it passed
without a page ever being turned to. Thirty-eight quotations in seven definitions were written
that way. The checker now refuses the shape, and `(manual, section 4)` with it. Where it holds
the document and can read it, its report names the page the passage is on, so that you can
write it in: `(manual p. 17)`. If the document really has no pages to turn to, say
`paginated: false` on its source, and the key alone is then the right locator.

**And a document with no pages is never cited by a page.** `(release_notes p. 3)`, where
`release_notes` says `paginated: false`, has no page to turn to. It used to be counted as
unchecked without a word, and it fails now. So does `(p. 3)` with no key, where none of the
definition's sources has pages.

**A document's name that is not one of your keys fails the run.** `(chart)` where the sources
are `manual` and `chart_article`, or `(midi_impl, #243)` where there is no `midi_impl`: the
word is what the definitions bundled here call a document, so it reads as one, and yours has
not got it. A word counts as such a name if it is a source key with an underscore in it
anywhere in the corpus, or one of nine words that name a document and little else: `addendum`,
`changelog`, `chart`, `guide`, `implementation`, `manual`, `reference`, `specifications` and
`supplement`. Any other word of one piece is an aside, whatever some definition uses it for a
key: `(midi)`, `(keyboard)` and `(update)` fail nothing. Before a page, any name that is not
one of your keys is refused, as `(handbook p. 3)` is. So is one of those names in other
capitals where it is your key, `(Manual)` for `manual`. **A key spelt wrongly is not caught
this way.** `(manaul)` is nobody's key, so it leaves the quotation with no locator, exactly as
an aside such as `(sic)` or `(our emphasis)` does. Put an aside in the sentence and not in the
brackets, and read the list of passages with no locator, which is where a misspelt key shows.

**A number on its own is read too, and is the weaker locator.** It needs a dot in it or the
word `section` before it: `(15.6)`, `(section 4)`, `(1.55D)`. It names no document, so the
passage is looked for in every document the definition cites that has no pages and that the
checker could read, and the report says which holds it. A bare `(16)` is not read as a
locator at all. **A number alone is for a document with no pages.** Where a document has
pages its page says more, and a search of the whole of it is what the bare key was refused
for; so where every source of a definition has pages, a number alone fails the run as the
bare key does. **Prefer the key** even where a number is allowed. It is the stronger check,
and it stays a check when one of the definition's unpaged documents is not in the library: a
number alone that is found in none of the others is then unchecked, because the passage may
be in the document nobody could read.

**This is enforced, and the reason is worth a paragraph.** A locator the checker could not
read was indistinguishable from no locator at all, and a quotation with no locator is passed
over in silence — so a definition reported "14 of 14 quotations are on the page they cite"
while holding 34 that cite a page. Forty-eight quotations across thirteen definitions were in
that state. Reading them found five that were wrong, and **three of those were quotations
saying something the maker had not said** — the one fault a page citation cannot catch,
because the page is real and the sentence is not. The checker now refuses a locator it cannot
read instead of skipping it, so an unreadable one fails the run rather than passing quietly.
The run also fails on a source the definition has not got; on a document with pages cited
without one, or one without pages cited by a page; on a curly quote mark outside a quotation;
on a quotation with its locator inside backticks; on quote marks or backticks that do not
pair, or that pair wrongly so far as it can tell; and on an account that is not written as a
block scalar. Each is explained in this section.

**A locator goes after each closing quote, not once at the end of the sentence.** This is the
commonest way one goes missing, and it reads as though everything is cited:

```
wrong    The chart marks "Song Position", "Song Select" and "Tune Request" (p. 9).
right    The chart marks "Song Position" (p. 9), "Song Select" (p. 9) and
         "Tune Request" (p. 9).
```

In the first, only the last of the three is checked and the other two are not looked at by
anything. Five quotations in one definition were in that state, four of them the second half
of a sentence whose first half carried the citation.

**Where a passage is not quoting a document, use backticks instead of quote marks.** A field
value, a file name, a term you are naming rather than citing — `System Exclusive`, not
`"System Exclusive"`. The checker reads past a backticked span, so this is the remedy for
anything it reports that was never meant as a quotation. **The one thing it will not read
past is a quotation with its locator**: a quoted passage and a `(p. 4)` after it, inside
backticks, fails the run, because that is what a backtick left open makes of a real
quotation. A PDF's internal metadata title and a quotation of another definition in this
corpus are both this case: neither has a page to cite, so neither should be written as a
quotation.

**Close every backtick and every quote mark you open.** The checker finds a quotation by
pairing the quote marks in order, after taking out each code span: a run of backticks, and
everything up to the next run of as many. One backtick left open turns every later code span
inside out: the prose between two spans is taken out and what was inside them is read. One
definition had a parameter's name opened and never closed, and from there on the pairing saw 7
of its 25 page citations. So a definition with a paragraph in which either mark does not pair
is not checked at all, and fails the run until the stray one is closed; the report names the
line that paragraph begins on. A paragraph is what it is in the account, lines with no empty
line among them; among comments it is a run of lines that each carry a comment. An empty line
ends it, and so does a bare `#` or a line of YAML with no comment; a line of YAML with a
comment after it does not. A quotation and a code span each begin and end in one paragraph. If
you need a lone `"` in a sentence, an inch mark for instance, put it inside backticks. A lone
backtick that a maker prints cannot be written at all inside one backtick each side, so put two
each side, which is a code span too and may hold one, or say it in words. A run of backticks is
closed only by a run of as many, and one that nothing closes is a stray mark like any other.
Two spans set back to back are read as one, which changes nothing.

**Two stray marks are worse than one, because the count is even again.** Everything between
them is paired inside out and nothing is odd. The checker cannot count its way to that, so it
looks at what the pairs enclose: a "quotation" that begins or ends with a space, or is empty,
or begins with the `**` that closed another quotation's emphasis and then a locator, is the
prose between two quotations, and a quoted passage with its locator inside backticks is a
quotation somebody's backtick swallowed. Either fails the run. A quotation that begins with a
bracket of its own, such as a section heading printed `(10.4) Sync`, is none of these.
Neither is proof, and a stray pair can still fall where it shows no sign, so read the list of
passages with no locator when you change a definition: prose turning up in it is the other
sign. Where a maker really does print a passage with a space at its edge, or nothing between
two marks, write it in backticks, since nothing of that kind can be looked for on a page.

**Write a quote mark inside a quotation as a single one.** The maker's sentence may quote a
word itself: `set this to "ON" or "P-Dump"`. Inside your quotation those marks become single,
`"set this to 'ON' or 'P-Dump'" (p. 55)`, because a double one ends your quotation early and
the rest is looked for by its tail, or not at all. The comparison ignores which kind of mark
it is. Twelve definitions had a double mark inside a quotation, and one of the quotations it
hid cited the wrong page.

**Write the quote marks straight.** Only straight marks are paired. A curly mark inside a
passage is fine, because it is the maker's own: `"Works the same as “start.”" (p. 62)` is one
quotation and is looked for as one. A passage that is itself in curly marks is seen by
nothing, so a curly mark anywhere outside a quotation fails the run.

**Write the account as a block scalar**, `source: >-`, as every definition here does. The
checker finds the account by that line, or by `source: |`. An account written any other way,
in quote marks on one line for instance, is read by nothing, so it fails the run.

**A square bracket in a quotation is the maker's or yours, and the checker tries both.** It
may be yours, adapting a word to your sentence: `"make[s] it possible"` for a page that says
`makes it possible`. Or it may be the maker's, as when a manual prints a range as
`[1 Note...12 Note]`. The passage is looked for with its brackets as printed, and then with
what is in them left out, provided at least eight characters remain outside them. A passage
that is all bracket used to have nothing left to look for, and was found on every page. **The
second way does not look inside the brackets at all**, so a passage found only that way is
named in the report: that is right for `make[s]`, and it is no check of a range the maker
printed, so quote a maker's bracket exactly.

**Two things you do not have to worry about.** Emphasis around a quotation is fine —
`**"the part parameters"** (p. 45)` is read exactly as the plain form is. And a passage
shorter than twelve characters is not checked at all, because a short phrase matches half a
manual; that is a deliberate floor rather than something to work around, so do not lean on a
three-character quotation to carry a claim.

**You can see what the checker did not look at.** Run it on your own definition —
`python tools/check_quotations.py <maker>/<model>`, two seconds against half an hour for the
corpus — and it prints, besides the checks that ran, how many passages are in quotation marks
with no locator and how many fell under the floor. Those two figures are what let you square
its count against your own reading of the file. **A figure you cannot reconcile cannot be
told from a complete one**, which is how a definition came to report five of five while
holding thirty nobody had read.

**Where a passage appears in two of a maker's documents, cite the one you transcribed.** A
locator names one document and one page. The two often word it differently — one Access
manual prints "Bend Up > -64" where that maker's own reference prints "Bend Up -64" — so the
quotation belongs to whichever you actually read, and the other document is worth a sentence
of its own rather than a second page number in the same brackets.

## 7. When there is no document

Some instruments — discontinued ones especially — have nothing published any more.
The maker's site may be gone, or the current owner of the brand may host only the
reissue's documents. **Look for somebody else's copy of the maker's own manual
first**: section 2 says when one can carry a definition, bundled or not.

Where there is no such copy, you can still write a definition. **Mark it `unverified` in
its own source line**, say exactly what you did use - a measurement from your own unit, a
photographed chart from the box, a table somebody else drew up - and keep it beside your
own project, where it will load in preference to anything bundled.

What it cannot do is join the bundled set, because that set makes a promise about
provenance it could not keep on your behalf.

## 8. Offering a definition to the bundled set

Definitions bundled with this package are held to the rules above, and three tests
enforce the part a machine can check: `test_every_bundled_definition_states_its_provenance`
refuses a file that does not name a document, `test_every_bundled_definition_cites_pages`
refuses one that cites no pages, and `test_nothing_bundled_is_an_import` refuses
anything the importer wrote. A fourth, `test_no_bundled_definition_carries_a_warning`,
means the validator has to be silent about your file.

Adding a file also means adding its name to `test_the_bundled_names`. That is
deliberate: it makes the addition visible in review.

Before offering one, check that:

- every number traces to a document you can name, with the page or section it came from;
- you extracted the tables twice and the two agree;
- every row of the source is either in the file or excluded for a stated reason;
- every `none` records what you searched for and where;
- every disagreement is carried as section 4 sorts it, and none is resolved silently;
- the citation check below passes against your own copies of the documents;
- `pytest` and `mypy` both pass.

### Let a script follow your citation

`tools/check_citations.py` does by machine what a reviewer would do by hand. Point it
at the folder of documents you fetched, and for each definition it finds the document
by the `sha256` in your `sources` block, turns to the pages your `source` line cites —
applying the `page_offset` and `pages_per_sheet` you recorded — and reports every
control number, LSB, NRPN and note number that is **not** printed there.

```bash
export PYMIDIINSTRUMENTDEFS_LIBRARY=/path/to/your/manuals
python tools/check_citations.py moog/minitaur       # or no name, for all of them
```

**It looks for a number in the order of what finding it proves.** Printed whole on a
cited page is what it calls found. After that come the weaker checks, each reported apart
and never counted as found: an NRPN as two hexadecimal bytes side by side, or as two halves
in decimal; a controller inside a short range the maker prints; the digits of the number
with a gap between them on one line, which is how some text layers set a number and is also
how `5: 0.5      21: 2.1` comes to hold a 521; and last a byte in hexadecimal. Each number
found by any of the last three is named, to be read on its page, and one found inside a range
is named with every short range it falls inside, and with the line a range stands on where
that line holds more than the range, because a range is matched wherever it stands: one
definition's 53 was "inside" the `49-54` of a table of clock divisions. **Where
the range it names is a row of an implementation chart, cite the page that prints the numbers
themselves.** A chart's Control Change row gives `12-31` and names nothing. The list that
gives each of those numbers a name is usually a page or two away, and with that page cited
the numbers are found whole.

**Every page you cite is read in every document that has pages**, so `manual p. 2` turns
your chart to its second sheet too, and a number printed only there counts as found. Name the
document before each page, `(chart p. 2)`, and run it with `--attribute` to have each page
read in the document its citation names and in no other. That is not yet the default.
**The key has to be the word directly before the `p.`, written as it is under `sources`.**
`Chart p. 1`, `the chart (p. 2)` and `the manual's p. 4` name no document, so those pages are
still read in all of them, and the report lists the pages it read that way. And a key that
stands there by accident is believed: `see the chart p. 4 of the manual` credits page 4 to
the chart. So write the citation as a citation, `(manual p. 4)`, and not into a sentence.

It separates four faults, because they have four different fixes: a number that is not
on the page you cited, a page the document does not have, a document whose hash matches
nothing you have — which usually means the maker has revised it since you read it, so
your citation now points into an edition nobody here has seen — and a definition too
broken to load, which it reports as a sentence rather than a stack trace.

It is not part of the test suite, and that is deliberate: the documents it reads are
copyrighted and are never committed, so in CI it could only skip, and a skip nobody
reads is a green tick certifying nothing.

**A pass is narrower than it looks.** It means the cited page carries the number. It
does not mean the number means what you say it means, that a band boundary is right,
or that nothing was left out — a check that reads your definition to know what to look
for can never tell you about a control you never wrote down.

When all of that is done, open a pull request. Expect to be asked which document, which
edition, and which page — because that is the question this whole guide exists to make
answerable.
