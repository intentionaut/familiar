# Contributing

Familiar is a prompt pack. Most contributions are a few lines of markdown.
Three kinds are especially welcome.

## 1. A language

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

## 2. A pattern

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

## 3. A style

If you have adapted Familiar to a different kind of publication (a research
digest, a company changelog, a magazine), a short `knowledge/styles/<name>.md`
describing what you changed in positioning, voice and slot shapes helps the
next person. Same rule: real examples, no invented ones.

## House rules for the repo itself

- Plain language. If a sentence could appear on a SaaS landing page, cut it.
- No em dashes in shipped prose.
- Never a key, token or personal account id in any file.
- Prompts propose; the writer decides. A change that makes a stage apply
  something without confirmation will not be merged.
