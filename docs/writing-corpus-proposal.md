# Familiar does not know what the writer has already published

Proposal, 2026-09-09. Nothing here is applied.

## The failure this comes from

A writer asked what themes Familiar noticed across her projects. Seven passes
of `harvest` produced findings she rejected as too low-level, then as invented,
then as untrustworthy, then as accurate and useless. Every pass read her
repositories: build logs where there were none, git digests, dated rule files,
strategy documents, and finally the session transcript.

Her published writing was in a repository nobody had asked for. Fifteen essays,
eleven drafts, ten talks. Every piece argues a claim about a shift in the
industry, evidenced with named companies and dated reports. Her own building
almost never appears in them.

So `harvest` was answering the wrong question. It asks *what recurs in the
work*, and produces findings about the work. What she needed was *which of the
claims I have already published did this fortnight produce evidence for* — and
one of her drafts turned out to end on an open question that a strategy session
three weeks later had answered, first-hand, on her own company. That connection
is invisible to every stage Familiar currently has, because no stage reads what
the writer has published.

**This is not specific to her.** Any writer arriving with an archive has their
declared positions sitting in it. `learn ingest` reads that archive once, for
voice, and keeps no record of what any piece argued. `themes.md` — the file
whose whole job is holding declared positions — is a blank form, and hers stayed
empty while forty-six declarations sat in a repo.

## What exists, and what is missing from it

| Today | Holds | Gap |
|---|---|---|
| `learn ingest` | Reads the archive in bulk; proposes `voice-guide.md` and `canonical.md`; mentions themes for `positioning.md` | Extracts *how* the writer writes and discards *what they argued* |
| `themes.md` | Declared themes, stable ids, evidence bar | A blank form with a high fill cost. The template's own note explains why inference was removed; nothing replaced it as a way in |
| `harvest` | Logs, digests, reflections, pieces, cuts | Never reads published work. Cannot tell a new finding from one the writer published two years ago |
| `pieces/` | Pieces made inside Familiar | Says nothing about the archive that predates the install |

## Proposal

Five changes, four of them small, each extending something that exists.

### 1. A corpus setting, shaped like the one for build logs

`knowledge/writing.md`, mirroring `build-logs.md`:

```
- Published writing lives in: [folder, repo, or export]
- Where it publishes: [URL]
```

Resolved additively like `pieces`, not first-hit like `knowledge` — a writer
with a blog repo and a newsletter export has both, and dropping one loses
claims with nothing to say why.

### 2. `learn ingest` gains a second output: a claims ledger

Ingest already reads the corpus and already samples above thirty pieces. Add
`knowledge/claims.md`, one row per piece:

```markdown
### <title>
Published: <date> · <url>
Claim: <the piece's argument, quoted from the piece>
Evidenced with: <what it rested on — reports, companies, first-hand>
Left open: <a question the piece asked and did not answer, or "nothing">
```

`Left open` is the field that earns the feature. A published question the
writer has since answered is the strongest follow-up available, and it is
currently unrecoverable without rereading the archive by hand.

A ledger is not a voice file. Keep it separate so a voice refresh does not
rewrite the record of what was argued.

### 3. Themes get a way in that is not a blank page

Ingest proposes themes **from the ledger**, with the pieces as evidence, for
the writer to accept or edit. This stays inside "Declared before inferred":
the proposal carries its evidence, it is marked `inferred (unconfirmed)`, and
it is not a theme until the writer confirms it in `themes.md`.

The template's history says harvest used to re-derive themes every run and the
count moved with the derivation rather than the work. That argument is against
*a stage silently inferring on every run*. It is not an argument for a blank
form, which is what produced an empty file beside a full archive.

### 4. Harvest asks the other question first

Add a section above the existing ones:

> **Evidence for claims you have already made.** For each row of the ledger the
> period speaks to, name the claim, the new evidence, and which of four it is:
> **answers an open question · extends · counter-example · contradicts.**

`contradicts` justifies itself on its own: run once here, it found a published
project page describing a product feature removed three days earlier.

Read the ledger **first**, before logs and digests. It is the only source that
says what the writer argues rather than what they did, and a stage that reads
only the work produces findings about the work.

Where there is no ledger, say so once, in the words the missing-source table
already uses, and run as today.

### 5. Ask once, at first engagement

`checkin.md` has a first-engagement offer and AGENTS.md has the introduce-a-loop-
once rule. One line inside that introduction:

> Published anywhere? Point me at the folder or the export once and I will read
> what you have argued, not just how you write.

Then never again unless asked.

## A second gap, found on the way

`prompts/harvest.md` defines a digest as "one project's git history,
reconstructed by `scripts/project-digest.py`". `scripts/session-digest.py`
exists and is called only by `case-study`, which writes it into a piece folder.
So session transcripts — where a writer reacts in real time, in their own words,
with no co-author — are unreachable from harvest. Feeding one in by hand was the
first source in this session where every writer turn was unambiguously the
writer's.

Either harvest should read session digests from the same folder, or the two
should be named differently so the limitation is visible.

## What this does not fix

A writer with no archive gets nothing from any of it. For them the answer
remains `reflection.md`, which is off in the template and is the only source
that records thinking rather than output.
