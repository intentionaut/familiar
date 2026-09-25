# Style rules (mechanical pass)

A checklist precise enough for any model or human to run consistently.
Every flag must come with the exact rewritten line. Never auto-apply changes:
the writer accepts, rejects, or revises each one.

## Language gate

Read `Language:` in `knowledge/positioning.md` first. If it is not English,
open `knowledge/languages/<code>.md` and follow its skip/keep/replace table
before applying anything below. The rules marked **(en)** assume English
orthography and will damage other languages if applied blindly: the dash
rule, house spelling, sentence-case headings, hyphenated word pairs,
quotation marks and the number-spelling convention. Everything else (padding,
hedging, fake candour, forced groups of three, announced evidence,
authority-flexing) is about how models pad meaning and travels across
languages, with the language file adding its own vocabulary. If no language
file exists for the house language, say so, apply only the language-agnostic
rules, and point the writer at `CONTRIBUTING.md`.

## Absolute rules

| # | Rule | Fix pattern |
|---|------|-------------|
| 1 | **(en)** No em dashes (— or ―) anywhere, including titles (drop this rule in positioning.md if the house uses them) | Recast with comma, colon, semicolon or period |
| 2 | **(en)** House spelling, as set in knowledge/positioning.md | Default British: organise, realise, favourite, colour, behaviour, licence (n.), programme (except computer program). Swap the list if the house is American |
| 3 | No banned/hype vocabulary | Flag every word in the overused list below, plus: journey (metaphor), transform (unless literal), supercharge, realm, "in today's fast-paced world" |
| 4 | **(en)** Sentence case headlines and subheadings | Match existing site convention |

## AI-tell patterns to flag

Sweep for every pattern below. Each flag gets the exact rewritten line. When
unsure whether a phrase is an AI tell or the writer's deliberate dry wit, mark
it UNCERTAIN with your reasoning.

Patterns 1 to 25 follow [humanizer](https://github.com/blader/humanizer) 3.0.0
by Siqi Chen (MIT licence), which draws on Wikipedia's "Signs of AI writing";
their wording and examples are adapted here with credit, and keep humanizer's
numbers so the two lists can be compared. Familiar's own tells follow them,
each from a real draft. `scripts/humanizer-check.py` reports when the lists
drift apart.

### Why these read as machine-written

A model writes the most likely next thing, so it makes the choice that suits
the widest range of readers and subjects. A writer chooses for one reader and
one subject, so their choices are uneven and specific. Every pattern here is
the default choice in one of five forms: staging (signalling importance instead
of adding a fact), rhythm by rule, inflation, formatting by rule, and leftovers
from a chat or a draft. Word habits change with each model release; the
structural habits persist, which is why they come first.

### How strongly each one counts

- **Act on one sighting:** patterns 1 to 5. One instance is a flag.
- **Weak alone:** marked below. One instance is a choice a careful writer makes
  on purpose. Flag it only when other tells share the passage, and name them.
- **Everything else:** one clear instance is enough, after checking it is not
  doing real work.

Never flag a watched phrase inside a quotation, a title or a proper name, or in
a passage that discusses the phrase rather than using it. Several tells together
are the safeguard: people who judge by feel do little better than chance.

A fix never loses a fact. A rewrite that drops a number, a name, a date, a quote
or a claim is a worse edit than the tell it removed (see "Tightening that costs
a specific" below). Where a sentence needs a detail the writer has not given,
the fix is a bracket, not an invention.

### A. Staging instead of stating (act on one sighting)

1. **Not X but Y.** "not just X, but Y", "it's not X, it's Y", "X rather than
   Y" used for weight, the same contrast split across two sentences ("This does
   not mean X. It means Y."), and a clipped negative tail (", no guessing"). The
   negative half names something nobody claimed, so the positive half sounds
   larger. State the point. Keep a contrast only when the negative half corrects
   a belief the reader actually holds, or when both halves carry information.
   Before: "The options come from the selected item, no guessing." After: "The
   options come from the selected item, so nobody has to guess."
2. **One-line closers and dramatic fragments.** A one-sentence paragraph that
   restates the paragraph before it; "That is the real win."; "Let that sink
   in."; the same closer after several sections; a row of fragments ("No
   aesthetic prior. No nostalgia."); a word in capitals, or with full stops
   between the words, for emphasis. A short sentence may carry emphasis when it
   carries something new. Cut one that repeats, and merge a row of fragments
   into a sentence with a claim in it.
3. **Sayings that sound deep.** "the real question is", "at its core", "what
   really matters", "fundamentally", "the heart of the matter", "X is the Y of
   Z", "X becomes a trap", "not a tool but a mirror", "the language of", "the
   currency of", "the architecture of". An ordinary point dressed as a hidden
   truth. Replace the saying with the specific claim. Before: "Symmetry is the
   language of trust." After: "Symmetric layouts feel more predictable to
   users."
4. **A staged run-up before the point.** "Let's dive in", "here's what you need
   to know", "without further ado", "Honestly?", "Look,", "Here's the thing",
   "The thing is", "Let's be honest", "Real talk". The same move on a sentence:
   "I should say plainly that...", "Here is the argument...", "Let me be clear".
   Remove the run-up and make the point. "Honestly" inside an ordinary sentence
   is fine; the tell is the standalone opener before a routine claim.
   Two announcements of the same kind: "tell the story" ("tell the story of how
   we got here", "the data tells the story"), which performs storytelling
   instead of doing it, and "a familiar moment" (also "a familiar scene", "a
   familiar feeling"), which declares a moment familiar instead of rendering
   one the reader recognises. Open the scene or state the fact.
5. **Arguing with no one.** "This isn't about...", "I'm not saying...", "To be
   clear", "Don't get me wrong", "Some might say... but", "A tempting approach
   would be", "You might think... but". An objection or an option that appears
   nowhere else, usually left from an earlier draft. Remove the defence; if it
   holds a real claim, state the claim. Keep an objection the text attributes or
   answers in full, and an option a reader would actually weigh.

### B. Rhythm by rule

6. **Forced groups of three.** Ideas in threes to sound complete: in one
   sentence ("innovation, inspiration and insights"), as three parallel
   examples, or as three short facts and then a lesson. Check each item adds a
   distinct idea; merge them, develop the strongest, or change the shape. Keep
   three when the meaning has three parts.
7. **Repeated sentence openings.** Several sentences in a row starting with the
   same subject. Merge them, change the subject, or begin with the action. Do
   not ban the word: repetition for rhythm is a writer's choice. *Weak alone.*
8. **(en)** **Dashes as the universal connector.** Absolute rule 1 above sets
   the rate. A dash lets the writer skip choosing how two clauses relate. One
   dash is *weak alone*; a text full of them is not. A spaced double hyphen used
   as a dash counts as one. Dashes inside code, commands, paths and URLs are not
   prose.
9. **Stacked qualifiers.** "to be fair", "it's also possible", "could
   potentially", "might arguably", "in some cases it may", and hedging before
   any opinion. Qualifier after qualifier until every claim sounds unsure,
   usually repairing an earlier overstatement. Keep a qualifier the meaning
   needs; keep scope statements and real corrections. One "perhaps" is a human
   habit. *Weak alone.*
10. **(en)** **Hyphenated pairs everywhere.** "cross-functional", "data-driven",
    "high-quality", "real-time", "long-term" hyphenated in every position. Keep
    the hyphen before a noun ("a high-quality report") and drop it after ("the
    report is high quality"). *Weak alone.*
11. **Passive voice and missing subjects.** The actor hidden or the subject
    dropped ("No configuration file needed."). Say who acts. *Weak alone.*

### C. Inflation and borrowed authority

The fact underneath is usually sound. Keep it and remove the dressing.

12. **Overused AI words.** Models use these far more often than people do,
    especially in groups. A formal word outside this list is not a tell by
    itself.
    - actually (as filler; keep it where it corrects an expectation), additionally
    - align with, bolstered, deep dive, delve
    - emphasising, enduring, enhance, fostering, garner
    - gate, gated, gating, used figuratively (keep technical uses, and a named
      term of art such as a stage's "decision gate")
    - highlight (as a verb), interplay, intricate / intricacies
    - key, as an importance-filler adjective ("key players")
    - landscape (as an abstract noun: "the AI landscape")
    - meticulous / meticulously, pivotal / crucial / paramount
    - quietly, as a metaphor for small or unnoticed ("quietly reshaping"); keep
      it for actual sound
    - robust (figurative; keep technical uses), showcase, tapestry, testament
    - underscore (as a verb), valuable, vibrant
    - labyrinth, seamless / seamlessly, leverage (as a verb), harness (as a
      verb), navigate ("navigate the complexities"), elevate, unlock, empower,
      game-changer, cutting-edge, transformative, holistic, comprehensive /
      all-encompassing, multifaceted, synergy, paradox / juxtaposition,
      dichotomy, nuanced, spectrum ("on the spectrum of")
    - "It is worth noting that...", "It is important to mention..."
13. **Inflated significance.** "stands as a testament", "a pivotal moment",
    "plays a key role", "marking a shift", "reflects a broader", "a lasting
    legacy", "setting the stage for", "evolving landscape"; a stock
    "challenges and future outlook" section; a send-off ("the future looks
    bright", "exciting times ahead"). An ordinary detail said to mark a change,
    prove a legacy or promise a future. Keep the fact, drop the significance,
    and end on the last concrete fact.
14. **Vague connection.** "associated with", "in connection with", "linked
    to", "tied to", where the relationship is known. Name it ("founded and
    conducts"); if the source does not say, keep the vague wording rather than
    invent a role.
15. **Shallow -ing riders.** "highlighting", "underscoring", "reflecting",
    "symbolising", "contributing to", "fostering", "showcasing" bolted onto a
    fact to make it sound deeper. Keep the fact; keep the rider only when a
    source supports what it claims.
16. **Sales language.** "boasts", "vibrant", "rich" (figurative), "profound",
    "commitment to", "nestled", "in the heart of", "groundbreaking",
    "renowned", "breathtaking", "stunning", "streamline", "next-level". State
    what the thing is.
17. **Borrowed authority.** "experts argue", "observers have cited", "industry
    reports", "research suggests", "according to a recent study"; a list of
    prestige outlets standing in for what was said. Name the real source and
    what it said, or cut the claim. Never invent a source.
18. **Avoiding is, are and has.** "serves as", "stands as", "functions as",
    "boasts", "features", "offers", "represents a". Use *is*, *are* and *has*.

### D. Formatting by rule

Templates produce clean formatting too. The tell is decoration on every item.

19. **Bold as decoration.** Words bolded for no reason; every list item given a
    bold label and a colon. Remove the bold, and turn a labelled list into prose
    when the labels carry nothing of their own.
20. **Decorative headings.** Every main word capitalised, emojis or arrows as
    decoration, a rule between every section, a first heading that repeats the
    title. Sentence case, no decoration, the title once.
21. **(en)** **Curly quotation marks** where the house or target format uses
    straight ones. Most editors curl automatically. *Weak alone.*

### E. Leftovers from the chat and the draft

Remove these outright.

22. **Chatbot residue.** "I hope this helps", "Great question!", "Certainly!",
    "Would you like...", "Let me know", "Here is a...". The most certain tell
    here and the easiest to miss when it wraps real content.
23. **Knowledge-limit disclaimers and guesses.** "as of my last update", "based
    on available information", "not widely documented", then a plausible guess
    ("she likely grew up..."). Say what the source does not show, or cut the
    sentence. Never present a guess as a fact.
24. **A heading repeated in the first sentence.** "## Performance" followed by
    "Speed matters." Remove the repeated line.
25. **Writing about the previous version.** Documentation that describes what
    it replaced instead of what it does. The previous version belongs only in
    change logs, release notes and migration guides.

### Familiar's own tells

Beyond humanizer, each found in a real draft.

- **Announcing evidence before presenting it.** "The research bears this out",
  "The data shows", "Studies confirm". State the finding.
- **Tightening that costs a specific.** A rewrite that is shorter but has lost a
  number, the name of a thing, or the mechanic that made a claim checkable.
  Tidier and says less. Cut abstraction, never a concrete: if a passage must be
  shorter, the adjectives go first and the evidence last.
- **A second clause that drops its verb to lean on the first one's.** "...gives
  every line one sentence, and nothing enough room to be evidence". It means
  "and nothing *gives* enough room"; the elision is a rhythm move, not a meaning
  one. Same family: "and none more so than", "and nowhere more than".
- **A decisive verb pointed at a vague "it".** "Ten requirements, and two of
  them decide it". Decide what? It sounds consequential and names nothing. Same
  family: "make or break it", "is the whole game", "that's the difference".
  Name the thing, or cut the clause.
- **Metronome prose.** Sentences of the same length three or more times in a
  row. Vary them.
- **Vague openers.** "This", "That", "It" starting a sentence with no clear noun
  behind it.
- **Treating the reader as knowing nothing** about a topic they chose to read.
- **Summarising what the opening already said.**
- **Closing on an inspirational call to action or a rhetorical question** that
  asks nothing. A real question the reader would want to answer is not this.
- **Bullet lists where prose would carry the argument.**
- **Three-sentence paragraphs throughout.**
- **"TL;DR" summaries** at the top or bottom.
- **Tone:** relentless enthusiasm; no opinion without the other side presented
  at once; everything an "opportunity" or a "journey"; clinical detachment where
  the topic calls for a stance; the colourless voice that is correct and says
  nothing.
- **Authority-flexing.** Credential drops, past employers named for weight,
  "I've spent N years in these rooms", "as a [title]", scenes written from above
  the other people in them. Replace with one precise scene written as a
  participant (see voice-guide "Authority").
- **Hedged positions that should be firm.** Where a hedge sits where the writer
  could take a stance, surface the trade-off and ask them to choose a side;
  never firm it up for them.
- **(en)** **Invented compound adjectives** ("future-forward", "human-centred").
- **Abstract nouns where concrete ones are sharper** ("implementation" for
  "doing", "utilisation" for "use").
- **"Whether you're X, Y, or Z"** openings that try to address everyone; "It's
  safe to say that..."; "The good news is...".
- **Unsourced quotes, statistics or claims of fact.**
- **Exclamation marks outside quoted speech.**

### Leave these alone

These carry a writer's voice. Keep them unless they hurt the meaning:

- a specific, unusual detail ("the lawyer who used to work upstairs from my
  dentist")
- mixed feelings and unresolved tension
- dated references, slang and in-jokes that belong to a time and a group
- a first-person choice the writer can explain
- a genuine aside, parenthetical or self-correction

## Framing people and products fairly

Writing about your own work means writing about employers, clients, colleagues
and tools that let you down. The line edit flags where the piece talks one of
them down, and offers the version that keeps the point.

This is a flag with an exact rewrite, like every other line-edit finding. The
writer accepts, rejects or revises it.

### A named person or company

Most often a former employer or client, mentioned in passing on the way to
something else. The reader fills in more than the sentence said, and the subject
cannot reply.

> Flagged: The data team there was a mess and nobody had owned it in years.
> Offered: Nobody owned the data model, so every team kept their own copy.

The second one is the same fact and it is about the system rather than the
people. Keep the criticism, lose the character judgement.

### The writer's own earlier work

Changing your mind is worth writing about and it reads as authority. It stops
doing that when the sentence is about how bad the old version was rather than
what the new one does.

> Flagged: The first version was embarrassing, I have no idea what I was
> thinking.
> Offered: The first version asked for the title too early. This one waits until
> the piece is finished.

### A product or tool the piece describes

Including the writer's own. Say what it does now. If something changed, one
clause on what is better is enough, and jokes at a product's expense read
differently in a public archive than they did on the day.

## House style details

- Reading ease: a tripwire, not a target. Report the Flesch score and grade
  level on every pass, and flag a piece that sits well outside the writer's own
  usual range. Never edit towards the number. Nine formulas score the same text
  across a 4.5-grade spread, their correlation with what readers actually find
  difficult is weak, and they have been known to be gameable since 1981: capping
  sentence length moves every score without making anything clearer. A piece
  that reads 15 points below the writer's normal is worth a look. A piece at 58
  is not a problem.
- Coined or unfamiliar terms: italics on first use, define immediately in plain words
- Links: inline, descriptive anchor text (never "click here")
- Blockquotes for other people's words; always name the speaker
- **(en)** Numbers: spell out one to nine, numerals for 10+, always numerals for data
- Oxford comma: optional, follow the writer's habit within a piece, stay consistent
- Paragraphs: short. Two to four sentences typical.
- Every piece ends with an invitation to reply or a question to the reader

## Output format for the line-edit report

For each finding:

```
[line N] "<quoted text>"
Issue: <which rule or pattern, with its number>
Why it matters: <one sentence>
Fix: <exact rewritten line in the writer's voice>
```

Then a summary table: total flags per category, reading ease score, grade level,
and the three highest-impact fixes.
