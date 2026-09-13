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
Nothing here is remembered, inferred, or copied from another database.

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

**Can confirm a fact, but should not be the only source**

- The maker's support articles and knowledge base.
- The parameter list inside the maker's own editor or librarian software.
- A measurement you took yourself from the instrument with a MIDI monitor — which is
  a fact about *your* unit and its firmware, so say so.

**Can only tell you where to look, or that something is worth re-reading**

- Community databases such as MIDI Guide, and `.midnam` files.
- Working code that drives the same machine.
- Copies on third-party sites — for a discontinued instrument this may be the only
  copy left, and it is still not the maker's: check it against anything else you can
  find, and say in your citation that it is a third-party copy.
- Forum posts and videos.

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

The format has no field for firmware, so **say it in the source line** when it
matters.

## 4. Read the document without losing half of it

**Cite printed page numbers, not the reader's page numbers, and check the offset for
every document separately.** A manual whose printed page 1 is the PDF's page 10 will
have you citing pages that do not exist. Some manuals print two pages to a sheet.
Some, like the Korg one above, have no offset at all. There is no general rule; check
each one.

**A text document has no pages.** Makers do publish plain-text MIDI implementations —
one such runs 2,221 lines across fourteen numbered sections and contains no page
breaks whatever. Cite its **section**, the way the document numbers it, and quote
enough of the row that a reader can search for it.

**Extract the table twice, and compare the two.** This is the single highest-value
habit in this guide, and it is worth spelling out why.

Writing the definition for the Korg above, a script pulled 47 control changes out of
that text file. It ran cleanly and reported no errors. The real number is **67**. The
pattern matching the table's hex column had been written as `[0-9A-F]` and the maker
prints lowercase hex, so every row whose hex digits contained a letter — including
CUTOFF and RESONANCE — was dropped in silence. A second extraction, done
independently, found all 67 immediately.

**Count the rows in the source and account for every one of them.** Every row is
either in your definition, or excluded for a reason you can state: it is a channel
mode message, it is a blank row, it is an NRPN rather than a CC, or the format has no
way to carry it. "I did not notice it" is not one of the reasons.

**Expect the maker's document to contradict itself, and record it when it does.**
Reading one 2,221-line implementation twice turned up a footnote marker the document
never defines, a row citing a footnote from the wrong section, a value list ending in
`128` where MIDI has no such value, two adjacent bands that overlap at their shared
edge, and one parameter whose polarity is given one way where the instrument transmits
it and the other way where it receives it. None of this is unusual. **Where a source
contradicts itself, or two sources disagree, record both readings and say so in a
comment. Never pick one silently.**

## 5. Write the definition

**Name it by its path.** `corpus/moog/matriarch.yaml` loads as `moog/matriarch`. Both
halves match `[a-z][a-z0-9_]*`. The folder is the maker's short name — `moog`, not
`moog_music` — while `model.manufacturer` is free text, spelled the way the maker
prints it.

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
  User manual, 44 pages, in which the word "MIDI" does not appear — verified
  across every page. The instrument is driven by clock and trigger at the
  patchbay and by its own 8-step analogue sequencer.

midi: none

voice:
  addressing: none
  polyphony: 1
```

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

**Three kinds of fact, and only one of them belongs in your file.** Facts about the
MIDI specification — channel mode messages, CC 120 to 127, Data Entry on CC 6 and 38 —
are not your instrument's parameters, and the validator will refuse them. Facts about
*your* rig — the channel you happen to use — are not properties of the model.
`channels` is the range the instrument can be set to. Anything the format cannot yet
express goes in a comment, never in an invented field.

**Give it a test.** One test of the fact the file exists for: the thing a consumer
would get wrong without it.

## 6. Cite it so a stranger can check you

The `source` field is prose, and it is the authority for the whole file. Make it carry:

- **what kind of document** it is — user manual, MIDI implementation, quick start guide,
  firmware addendum;
- **its title as printed**, including the maker's own typos, which is often how you find
  it again;
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
  and it is not zero three times.
- **`pages_per_sheet`** is for a manual that prints two pages on one sheet, which
  no offset can express. One definition here cites pp. 62-63 of a 40-sheet file,
  and that is only not a contradiction once the sheet count is known.

## 7. When there is no document

Some instruments — discontinued ones especially — have nothing published any more.
The maker's site may be gone, or the current owner of the brand may host only the
reissue's documents.

You can still write a definition. **Mark it `unverified` in its own source line**, say
exactly what you did use — a measurement from your own unit, a third-party copy of a
manual, a photographed chart from the box — and keep it beside your own project, where
it will load in preference to anything bundled.

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
- disagreements between sources are recorded rather than resolved silently;
- `pytest` and `mypy` both pass.

Then open a pull request. Expect to be asked which document, which edition, and which
page — because that is the question this whole guide exists to make answerable.
