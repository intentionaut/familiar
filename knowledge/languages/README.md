# Languages

One file per house language other than English, named by ISO 639-1 code
(`de.md`, `pt-BR.md`, `he.md`). The line edit and draft stages read the file
matching `Language:` in `knowledge/positioning.md`.

Each file says three things:

1. Which of the English-orthography rules in `style-rules.md` to skip or
   replace (dashes, spelling, heading case, hyphenated pairs, quotation marks,
   Oxford comma).
2. The overused AI words and phrases in that language.
3. Structural tells specific to the language.

`_template.md` is the starting point. Contributions welcome; see
`CONTRIBUTING.md`.
