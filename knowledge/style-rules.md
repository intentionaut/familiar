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

Sweep for every pattern below. Each flag gets the exact rewritten line. When unsure whether a phrase is an AI tell or the writer's deliberate dry wit, mark it UNCERTAIN with your reasoning.

### Overused words and phrases

- Delve / delve into
- Tapestry / woven tapestry
- Landscape (metaphor: "the AI landscape"; noun modifier: "the competitive landscape")
- Labyrinth / labyrinthine
- Crucial / pivotal / paramount
- Seamless / seamlessly
- Robust / robust framework
- Leverage (as a verb, especially "leverage these tools")
- Harness
- Navigate / navigate the complexities
- Elevate
- Unlock
- Empower
- Game-changer
- Cutting-edge
- Transformative
- Holistic
- Comprehensive / all-encompassing
- Multifaceted
- Synergy / synergistic
- Paradox / juxtaposition
- Dichotomy
- Nuanced / nuanced understanding
- Spectrum ("on the spectrum of")
- It is worth noting that...
- It is important to mention...
- Quietly, as a metaphor for small, gradual or unnoticed ("quietly reshaping",
  "quietly, people are losing"). Keep it only for actual sound. Before: "But
  quietly, people are losing the ability to think through the hard stuff."
  After: "People are losing the ability to think through the hard stuff, and
  nobody has noticed." (Matches humanizer §7; adopted 2026-08-30 from a real
  outline.)

### Structural tells

- Excessive hedging before any opinion
- Bullet-pointed lists where flowing prose would work better
- Paragraphs starting with formulaic transitions: Furthermore, Moreover, Additionally
- Announcing evidence before presenting it: "The research bears this out", "The data shows", "Studies confirm", "This is supported by". State the finding directly; don't frame it as confirmation.
- The "it's not just X, it's Y" construction; "This not only X but also Y" used repeatedly
- Overly symmetrical paragraph structure
- Closing with an inspirational call to action or rhetorical question
- Summarising points already made in the opening paragraph
- Treating every topic as though the reader has zero prior knowledge
- Vague openers: "This", "That", "It" starting a sentence with no clear noun antecedent
- Rule-of-three padding: three parallel items where two (or one) would do
- Metronome prose: symmetrical sentence lengths repeated 3+ times in a row

### Tone tells

- Relentless enthusiasm and positivity
- No opinion stated without immediately presenting the other side
- Everything framed as an "opportunity" or "journey"
- Clinical detachment on topics that call for a stance
- The "personality vacuum": technically correct but colourless voice
- Hedging without content: perhaps, potentially, arguably, might be worth considering
- Marketing speak: empower, streamline, cutting-edge, next-level, transformative
- Authority-flexing: résumé/credential drops, naming past employers for credibility, "I've spent N years in these rooms", "as a [title]" framing, scenes written from above the other people involved. Show, don't tell: replace with one precise lived scene written as a participant (see voice-guide "Authority").
- Hedged positions that should be firm. When a hedge sits where the writer could take a clear stance, surface the tradeoff and ask them to choose a side, rather than quietly firming it up for them. "Firm" is not the same as "strident"; it means a position with a reason you can defend.

### Sentence-level tells

- Long subordinate clauses with em dashes or parentheticals to sound thoughtful
- **(en)** Invented compound adjectives ("future-forward", "human-centred")
- Abstract nouns where concrete ones would be sharper ("implementation" instead of "doing", "utilisation" instead of "use")
- "Whether you're X, Y, or Z" opening that tries to address everyone
- "It's safe to say that..."
- "The good news is..."

### Format tells

- Three-sentence paragraphs throughout
- Bolded single-word or short-phrase headers in lists
- Emoji-heavy headings
- "TL;DR" summaries at the top or bottom
- Outdated or overly generic stat citations ("according to a recent study")
- Unsourced quotes, statistics, or claims of fact
- Exclamation marks outside quoted speech (rare exceptions only)

## House style details

- Reading ease target: 60+ (Flesch), grade level ~8 or below for main body text
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
Issue: <which rule/pattern>
Why it matters: <one sentence>
Fix: <exact rewritten line in the writer's voice>
```

Then a summary table: total flags per category, reading ease score, grade level,
and the three highest-impact fixes.
