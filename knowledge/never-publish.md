# Never publish

A list of things that must never appear in anything you send out.

Writing in public about work you did for other people means carrying names you
signed an agreement about, numbers nobody cleared, and clients who never agreed
to be written about. This is the one check Familiar will refuse to let past.

It is empty until you fill it in. An empty list is off, silently and with no
warning tone.

## What it is, and what it is not

**It matches literal strings you typed here.** Nothing else. It does not
understand your writing, it cannot spot a paraphrase, and it will not catch "the
travel company in Watford" when the list says the company's name.

Treat it as the last catch for the mistake you already know you could make, not
as a check that your draft is safe to publish. Only you can decide that.

## Settings

- Never publish: [on / off]

## Block

Names and money. A match here stops a publish. Put things here where seeing the
string in a draft is enough to know it is wrong: client names under an
agreement, agency and recruiter names, salary figures, an unannounced product.

```
[Client Name Ltd]
[£00,000]
```

## Warn

Numbers and phrases that are usually fine and occasionally not. A match here is
reported and does not stop anything. Unpublished metrics from a former
employer belong here, because "8%" belongs to everyone and the context is what
makes it a problem.

```
[42% conversion]
```

## Notes

- **One string per line**, inside the fenced blocks. A line starting with `#` is
  ignored, and anything after two spaces and a `#` on a line is a note about
  where the string came from, not part of the string.
- **Names match whole words**, so a three-letter company will not fire inside a
  longer word. Money and numbers match anywhere.
- **Case does not matter.**
- **Keep this file where your other knowledge files live**, not in a public
  repo. It is a concentrated list of exactly the things you do not want seen,
  which makes it more sensitive than any single draft.
- Something else can generate it. A tool that already knows your clients can
  write this file, as long as it writes this format and writes it into your
  house.
