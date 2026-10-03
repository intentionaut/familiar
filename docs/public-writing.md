# Writing in public: release notes and pull requests

This repo is public. Its release notes and pull requests are read by people
deciding whether to use or update the software, and by strangers who know
nothing about how it was built. This guide says how to write for them.

## What a note is for

Much of the work here is done by agents, quickly, in many small steps. A note
that lists the steps makes the work read as churn. A note that says nothing
makes it read as nothing. A good note says what the work is worth to the
person using the software: the problem they had, and what they can do now.

## How to write one

1. **Start from the reader's problem.** Name it in their words, then say what
   they can now do. "Exports finish on large projects" comes before anything
   about how.
2. **Write the capability, not the correction.** When a change exists because
   something was wrong, say what the reader now has. One clause on what is
   better, then move on.
3. **Outcome first, mechanism second.** Add the mechanism only when the reader
   needs it to act, such as a setting to change or a command to run.
4. **Count outcomes, never labour.** No counts of commits, files, tests,
   hours, prompts or agents. They measure effort, and the reader came for the
   result.
5. **Three to five bullets, and fewer is better.** Each opens with a bold,
   plain lead. A release that seems to need more is usually two releases, or
   one bullet repeated.
6. **Plain words.** British spelling, phrasing a fluent reader anywhere would
   take literally, no em dashes. If a term would send the reader to a search
   engine, explain it in the clause or cut it.
7. **Never disparage the software, past or present.** Describe what it does
   now. No adjectives about the old way.
8. **No relief from a burden the reader never carried.** "No extra step" only
   works if a version they used had the step.

## What never appears

The test is attributability: could a stranger connect this text to a real
person, a customer or a private conversation?

- **Nothing about a person.** No names, employers, clients, email addresses,
  phone numbers or account ids. No detail of how one person's run went. A
  number that illustrates a problem is fine until it carries a date, a name
  or whose work produced it.
- **Nothing from a conversation.** What was said while building is private,
  including when it was the reason for the change. No prompts, no quotes, no
  link that lets a stranger open a chat or agent session.
- **Nothing unannounced.** No product, customer, partner or plan that is not
  already public.
- **No secrets.** No keys, tokens or private addresses, including in examples.
- **Security fixes say what to do, not how to break it.** "Update to keep
  shared links private", and nothing about the hole.

## Quiet releases

"Bug fixes and updates." is a finished note in two cases:

- the person using the software would notice nothing, or
- the release adds something the maintainer has not yet used. It ships
  quietly and is announced in the first release after it has been used.

In every other case, write the outcome. A quiet line on a release that changed
what people can do undersells the work.

## Pull requests

- **Title:** the change in one line, sentence case, as an outcome where there
  is one.
- **Description:** what changes for the person using the software or working
  in the repo, and how it was checked. Describe the change, never the
  conversation that led to it.
- **Credit:** one line saying an agent wrote it is fine. A link anyone can
  open to the session is not.

Everything under "What never appears" applies to titles, descriptions and
comments too.

## An example

Labour, which reads as churn:

> Refactored the export module, fixed 14 bugs and added 32 tests across 9 files.

Quiet, which reads as nothing:

> Bug fixes and updates.

Outcome:

> **Exports finish on large projects.** An export that stopped part-way on a
> big project now completes, and tells you if a file was skipped.

## What the check enforces

`scripts/public-notes-check.py` runs on every pull request. It refuses:

- an email address, phone number or private key in any added line, the title
  or the description. A pattern known to be safe goes in `.piiallow`
- a private term, from a list held as a repository secret. The log names the
  place, never the term
- a link to a shared chat or agent session, the kind anyone can open
- an em dash in the title, the description or a changelog entry
- a changelog entry with more than five bullets

It is a backstop, not permission. A note it passes can still be wrong.
