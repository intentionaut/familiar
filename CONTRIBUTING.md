# Contributing

Familiar is a prompt pack. Most contributions are a few lines of markdown.
Four kinds are especially welcome.

## 1. A stage

A stage is a markdown prompt in `prompts/` that takes the writer through one
gate of the editorial pipeline. If you have built a stage that works for your
kind of publication, it likely works for others.

Most stages are agent-routed: the writer tells the agent what they have (a
draft, notes, an idea) and the agent picks the right stage. Only three commands
exist, one for each way a session starts: `/familiar-new-piece` to begin
something, `/familiar-board` to pick something back up, `/familiar-harvest` to
find something to write about. A new stage almost never needs a command, and a
pull request that adds one should say why routing is not enough.

To submit a stage:

1. Write the prompt as `prompts/<name>.md`. Follow the existing prompts for
   structure: a setup section, a method, clear stopping points, and no
   silent rewrites.
2. If the stage reads knowledge files that are not yet in `knowledge/`, add
   them as templates with bracketed prompts.
3. Add a test case in `tests/test_structure.py` if the stage introduces a
   new invariant (for example, a new knowledge file that must exist).
4. Open a pull request titled `stage: <name>` with:
   - what kind of publication it is for
   - the gate it sits behind (after which stage, before which)
   - one real example of its output

Stages must follow the house rule: they propose, the writer decides. A stage
that applies changes without confirmation will not be merged.

## 2. A language

Familiar's mechanical rules were written for English. Several of them are
about English orthography (em dashes, spelling, sentence-case headings,
hyphenated pairs, curly quotes) and would damage text in another language if
applied blindly. The line edit reads `knowledge/languages/<code>.md` when the
house language is not English.

To add one:

1. Copy `knowledge/languages/_template.md` to `knowledge/languages/<code>.md`
   (ISO 639-1 code: `de`, `pt-BR`, `he`, `ja`).
2. Fill in the three sections: which English-orthography rules to skip or
   replace, the AI-tell words and phrases in that language, and any
   structural tells specific to it (register, gendered address, particles,
   direction).
3. Add one real before/after example per pattern. Real means from a draft you
   saw, not invented.
4. Open a pull request titled `lang: <code>`.

A native or fluent writer of the language should be one of the authors. We
would rather have a short file that is right than a long one that is guessed.

## 3. A pattern

`knowledge/style-rules.md` lists AI tells. Additions are one pattern per pull
request, with:

- the pattern, in plain words
- one real before example (quote it) and the fix
- why it is a tell rather than a style choice, in a sentence
- if it overlaps a [humanizer](https://github.com/blader/humanizer) pattern,
  say which, so the two lists can be kept in step

Bulk imports are declined. The false-positive cost of a bloated list lands on
every writer using it. A weekly check against humanizer already surfaces
candidates in an issue; picking from that issue is a good first contribution.

## 4. A style

If you have adapted Familiar to a different kind of publication (a research
digest, a company changelog, a magazine), a short `knowledge/styles/<name>.md`
describing what you changed in positioning, voice and slot shapes helps the
next person. Same rule: real examples, no invented ones.

## Getting started

```sh
git clone https://github.com/intentionaut/familiar.git
cd familiar
python3 scripts/familiar init
python3 scripts/familiar status
```

The `init` command copies knowledge templates into the current directory and
installs agent commands. Edit `knowledge/positioning.md` and
`knowledge/voice-guide.md` before the first issue.

## House rules for the repo itself

- Plain language. If a sentence could appear on a SaaS landing page, cut it.
- No em dashes in shipped prose.
- Never a key, token or personal account id in any file.
- Prompts propose; the writer decides. A change that makes a stage apply
  something without confirmation will not be merged.

## Tests

```sh
python3 -m unittest discover -s tests -t .
```

Standard library only, no install, under a second. They run in CI on every
push. They check that the repo holds together, that every stage has a command,
that nothing references a file which is not there, and that shipped prose obeys
Familiar's own style rules.

If you fix a bug, leave a test behind. `tests/README.md` says what is covered
and what is deliberately not.
