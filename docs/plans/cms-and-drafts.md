# Plan: drafts at a glance, and the CMS as the draft store

**Written:** 30 August 2026. **Revised:** 30 August 2026, after the first two
questions were answered. **Status:** proposal, nothing built.
**Scope:** two additions to Familiar. A `status` command that shows every piece
in flight, and a set of adapters that let a stage work against a draft that
lives in beehiiv, Ghost or Substack.

**Decisions already taken, and applied to the repo:**

- The context log moves into the piece folder. Done: eight prompts,
  `AGENTS.md`, `knowledge/context-log.md`, `pieces/README.md` and the Dex skill
  all say the same thing now, and the existing root log has been split.
- **beehiiv is the first adapter. Ghost is next.** Intentionaut publishes on
  beehiiv, so beehiiv is the one that gets used rather than the one that
  demonstrates well. This costs something real, and section 4.1 says what.

Confidence markers used below: **[READ]** taken from a file in this repo,
with the line. **[LIVE]** checked against a vendor's own documentation today,
with the date. **[NEEDS SOURCE]** could not be verified; do not build on it
until someone has.

---

## 0. What this plan assumes about Familiar

Four facts from the repo shape everything that follows.

- **A piece is a folder of plain files.** `pieces/README.md:5-16` lists them:
  `brief.md`, `interview-questions.md`, `notes.md`, `outline.md`, `draft.md`,
  `edits/*.md`, `social.md`. **[READ]**
- **Stages read and write files, and know nothing else.** Every prompt begins
  by reading files: `prompts/dev-edit.md:9` is "Read the piece's draft.md
  (newest `pieces/*/` if not given via $ARGUMENTS)". No prompt contains a URL,
  a tool name, or an API. **[READ]** This is the property that makes CMS
  support cheap. If a file called `draft.md` is on disk, every stage already
  works, whatever put it there.
- **Scripts are Python 3, standard library only.** `scripts/humanizer-check.py:17`
  imports `re, sys, json, datetime, pathlib, urllib.request` and nothing else,
  and reaches the network with `urllib.request.urlopen`
  (`scripts/humanizer-check.py:25`). **[READ]** There is no `package.json`, no
  `requirements.txt`, no install step. Keep it that way.
- **The gates are the product.** `AGENTS.md:20-21`: "Stages are gated: never
  advance to the next stage without the writer asking." **[READ]**

### A contradiction, now resolved

The repo disagreed with itself about where the context log lives. It has since
been fixed in favour of the piece folder; the evidence below is kept because it
is why `status` has to tolerate both shapes for a while.

- `knowledge/context-log.md:3`: "`SESSION-CONTEXT.md` **at the project root**
  is how a piece survives a closed terminal." **[READ]**
- All eight prompts repeat "the project root `SESSION-CONTEXT.md`", for example
  `prompts/draft.md:58`. **[READ]**
- `dex/familiar/SKILL.md:92-93`: "Familiar's `SESSION-CONTEXT.md` lives in the
  **piece folder**, not the vault root, so it never collides with Dex's own
  session files." **[READ]**

A Dex user and a standalone user stored the same information in two different
places. **Fixed on 30 August 2026:** the piece folder wins, for the reasons in
section 1. `status` still reads a root log if it finds one, because other
people's clones will have one until they run the split.

Two small bugs found while reading, also fixed: `prompts/dev-edit.md:37` read
"They accept, reject, or revises each item herself", left over from the
de-gendering pass, and `prompts/outline.md:7` said "the target issue folder"
where every other file says piece.

---

## 1. The status model

### What "the stage a piece is at" means

There are two different questions hiding in that phrase, and `status` should
answer both, because a writer needs both.

1. **How far has this piece got?** Answered by which files exist. A piece with
   `outline.md` and no `draft.md` has been outlined and not drafted. This is
   cheap to compute, impossible to get wrong, and survives a lost context log.
2. **What is waiting on me?** Answered by the last context-log entry, whose
   format already carries exactly this: `knowledge/context-log.md:12-16` defines
   `Status:`, `Decision gate:` and `Next stage:`. **[READ]** The decision gate
   line is the single most useful string in the whole system for a writer coming
   back cold, and `knowledge/context-log.md:23-24` already says so: "The decision
   gate is the important line. It is what the next session reads first."

**The rule: files give the skeleton, the log gives the open decision.** When
they disagree, files win on "how far" and the log wins on "what next", and
`status` says the log looks stale rather than guessing.

### Where the log lives, settled

**One `SESSION-CONTEXT.md` per piece folder.** This is done, and it is what
`dex/familiar/SKILL.md:92` already did. Three reasons: a piece is a folder and
should be self contained, so moving or archiving a piece takes its history with
it; a shared root file grows without bound and mixes twenty pieces into one
stream; and Dex already collides with a vault-root file.

Migration was one pass and it was safe, because the entry heading already
names the piece. `knowledge/context-log.md:10` defines the heading as
`## YYYY-MM-DD HH:MM  <stage>  <piece folder>`, and the real log on this machine
follows it: `## 2026-08-30 08:55  line-edit  pieces/2026-08-30-kernic-site-copy`.
**[READ]** So a root log splits into per-piece logs with no guessing. That is
how the local one was split on 30 August: entries copied, never moved, and the
original left in place with a note.

Ship the same migration inside `status`, because other people's clones will
still have a root log. On first run, if one exists, offer to split it, copy
rather than move, and prefer the per-piece file wherever both exist.

### How status derives a stage

For each `pieces/<slug>/`, in this order:

| Files present | Stage reported |
|---|---|
| `social.md` | social |
| `edits/line-edit-report.md` newer than `draft.md` | line-edit |
| `edits/dev-edit-report.md` newer than `draft.md` | dev-edit |
| `draft.md` | draft |
| `outline.md` | outline |
| `notes.md` | interview |
| `brief.md` or `interview-questions.md` | case-study |
| none of the above | empty |

The `newer than draft.md` test matters. A writer who runs a dev edit, applies
it, and rewrites `draft.md` is back at draft, and the folder should say so.
Modification time is enough for this and needs no new state.

`status` then reads the last entry in that piece's context log and takes
`Status:`, `Decision gate:` and `Next stage:` verbatim. It never paraphrases
the decision gate. It is the writer's own sentence, and shortening it is how a
status view starts lying.

Staleness: if the newest file in the folder is more than seven days old, mark
the piece resting. Seven days is a guess and should be a flag.

### What it prints

One piece, and the common case:

```
$ familiar status

  PIECE                            STAGE      WAITING ON YOU                          TOUCHED  DRAFT
  2026-08-30-familiar              draft      Rewrite, then ask for a dev edit            2h    local
  2026-08-26-socratic-enrichment   outline    Pick A, B or C, or merge them               4d    local
  2026-08-22-step-free-london      line-edit  12 flags to accept or reject                6d    ghost
  2026-08-14-duckwatch             social     Confirm the week, or leave a slot empty     2w    local

  4 pieces, 3 waiting on you.
  Pick one up:  familiar resume 2026-08-30-familiar
```

Zero pieces:

```
$ familiar status

  No pieces yet.
  Start one:  familiar interview "the thing that has been rattling around"
```

Twenty pieces, sorted by what is waiting and then by recency, with the resting
ones folded away:

```
$ familiar status

  PIECE                            STAGE      WAITING ON YOU                          TOUCHED  DRAFT
  2026-08-30-familiar              draft      Rewrite, then ask for a dev edit            2h    local
  ... 6 more waiting ...

  12 resting (nothing touched in 7 days). Show them:  familiar status --all

  20 pieces, 7 waiting on you.
```

A piece whose context log is missing or older than its newest file:

```
  2026-08-19-kernic-copy           dev-edit   log is behind the files, open it to see     3d    local
```

That line is the honest answer. Inventing a decision gate from the report file
would be a guess, and a guess in a status view is worse than a gap.

### Resume in one step

```
$ familiar resume 2026-08-30-familiar

  2026-08-30-familiar  ·  draft  ·  touched 2h ago  ·  draft is local

  Last entry, 30 Aug 10:10, draft:
    Status: waiting on the writer
    Decision gate: The writer rewrites; dev-edit only when asked.

  Files: notes.md, outline.md, draft.md, session.md
  4 brackets left in draft.md.

  Continue:  familiar dev-edit 2026-08-30-familiar
```

`resume` prints and stops. It does not run the next stage. Running the stage
for the writer would break `AGENTS.md:20-21`, and the value here is the
twenty seconds of orientation, not the keystroke saved.

### Why status is a command and not a stage

Stages end at a gate because they make an editorial decision. `status`,
`resume`, `pull` and `push` make none, so they have no gate. Naming this
distinction in `AGENTS.md` protects the rule: adding a command should never
look like adding an ungated stage. `push` is the one exception, because it
changes something outside the machine, and it confirms for that reason rather
than for an editorial one.

---

## 2. The draft-location model

### Where the state goes

A separate `remote.json` in the piece folder, and **not** a block in
`draft.md` frontmatter.

The reason is specific. `prompts/draft.md:44-50` defines the frontmatter as
the writer's own fields, `title`, `subtitle`, `alternates`, `date`. **[READ]**
That frontmatter travels to the CMS on a push. Machine sync state in the same
block would eventually appear in a published post, or would have to be stripped
on every push, and a stripper is a thing that can fail. Keep them apart.

```json
{
  "platform": "ghost",
  "post_id": "6512c0a1e4b0f...",
  "url": "https://example.com/ghost/#/editor/post/6512c0a1e4b0f...",
  "pulled_at": "2026-08-30T10:12:04Z",
  "remote_version": "2026-08-30T10:09:58.000Z",
  "remote_hash": "sha256:6f1c...",
  "local_hash": "sha256:a03e...",
  "format": "html"
}
```

`remote_version` is whatever the platform gives that changes when the post
changes. Ghost has one, `updated_at`, and it is load bearing there. beehiiv and
Substack need the hash instead. Recording both costs nothing and means one code
path.

`remote.json` is covered by the existing `.gitignore:5` rule `pieces/*/`
**[READ]**, so it never reaches the public repo. It holds an id and a URL and
no credentials.

### Deciding who is newer

Three way, using the two hashes recorded at the last sync:

| Local changed | Remote changed | What happens |
|---|---|---|
| no | no | nothing to do, say so |
| yes | no | push offers to send the local draft |
| no | yes | pull offers to bring the remote draft down |
| yes | yes | conflict, stop |

"Changed" is a hash comparison against `local_hash` and `remote_hash`. No
timestamps, no clock skew, no trust in either machine's clock.

### What a conflict does

It stops, and it writes rather than merges.

```
Both copies changed since the last sync on 30 Aug at 10:12.

  Local:   draft.md, 1,174 words, changed 2h ago
  Remote:  ghost, 1,203 words, changed 40m ago

Wrote the remote copy beside yours as draft.remote.md. Nothing was
overwritten and nothing was sent.

  Compare:  diff draft.md draft.remote.md
  Keep yours:   familiar push --force
  Keep theirs:  familiar pull --force
```

There is no automatic merge, and there should never be one. A three way text
merge of prose produces a document neither party wrote, which is the exact
failure the whole tool exists to avoid. Writing `draft.remote.md` beside
`draft.md` also reuses a convention the writer already knows, from
`AGENTS.md:37-39`: "ask whether to replace it, add to it, or write a numbered
variant beside it (`draft-2.md`)". **[READ]**

`--force` in either direction is the only way to lose a version, it is typed by
a human, and it says which side is being discarded before it acts.

---

## 3. The integration contract

### One script, four verbs

`scripts/cms.py`, Python 3, standard library only, following the shape of the
two scripts already in the repo.

```
cms.py connect <platform>              store a credential, verify it, say what it can see
cms.py list <platform>                 the drafts this account can reach
cms.py pull <platform> <post> <piece>  write draft.md and remote.json into the piece folder
cms.py push <piece>                    send draft.md back as a new version of the same draft
cms.py link <piece>                    print the URL of the draft in the CMS
```

Every adapter implements five functions with the same signatures, and the
script holds all the shared logic: hashing, conflict detection, writing
`remote.json`, and refusing to do anything a refusal in section 7 forbids.

```python
class Adapter:
    name: str
    def check(self) -> dict:        # credentials present and valid, what plan/scopes
    def list_drafts(self) -> list:  # [{id, title, updated, url}]
    def pull(self, post_id) -> dict # {title, subtitle, body, format, version, url}
    def push(self, post_id, doc)    # returns the new version marker
    def url(self, post_id) -> str
```

Nothing above the adapter knows which platform it is talking to, and nothing
below it knows what a stage is.

### Where credentials live

In the system keychain, read at run time, never in a file the repo tracks.

- **macOS:** `security add-generic-password -s familiar-ghost -a <site> -w`
  and read back with `security find-generic-password -s familiar-ghost -w`.
  `subprocess` is standard library, so this needs no dependency.
- **Anywhere else, and CI:** an environment variable, `FAMILIAR_GHOST_KEY`,
  `FAMILIAR_BEEHIIV_KEY`, `FAMILIAR_SUBSTACK_COOKIE`. Read at run time only.
- **Never:** a dotfile in the repo, a line in `knowledge/`, an argument on the
  command line that would land in shell history.

This matches the rule already written for the social stage in `AGENTS.md:59-62`:
"Keys and tokens never go in that file." **[READ]** The same sentence should
appear in the CMS section of `AGENTS.md` word for word.

### Connecting in under two minutes

```
$ familiar connect beehiiv

  1. In beehiiv, go to Settings, Integrations, API.
  2. Create a key with posts:read and posts:write. Copy it.
  3. Paste it here. It goes into your keychain, never into a file.

  Publication ID: pub_...
  API key: ****

  Connected to Intentionaut. 2 drafts, 26 published posts.

  What Familiar can do here:
    write a draft            yes
    update an existing draft no, your plan does not include it. Each push
                             writes a new dated draft and leaves the old one.
    read a draft back        only the rendered page, so Familiar can tell you
                             the copy in beehiiv changed and cannot bring the
                             change down for you
    publish or send          no. There is no code in Familiar that can.
```

The last four lines matter. A writer handing a tool an API key deserves to be
told what it will refuse to do, and what it cannot do on their plan, at the
moment they hand it over rather than the first time it fails.

---

## 4. The adapters

Build order is set by where the writing actually goes. beehiiv is where
Intentionaut publishes, so it is first, and section 4.1 is honest about the
price of that choice. Ghost is second, because it is the platform that lets
the two way path exist at all. Substack is last and optional, because it has
no API to build on.

### 4.0 The Markdown converter, needed before any adapter

Every platform here speaks HTML. `draft.md` is Markdown. Python has no
Markdown in the standard library, and section 0 says no dependencies, so
Familiar needs its own converter. This is the first thing to build, and it is
the thing most likely to lose content, so it gets the strictest rule in the
plan.

**Write a small deterministic converter for the subset a newsletter draft
actually uses:** headings, paragraphs, bold, italic, links, blockquotes,
ordered and unordered lists, inline code, code blocks, horizontal rules,
images. That is roughly a hundred and fifty lines each way and it covers every
piece in this repo.

**Then make it refuse.** On the way out, if the Markdown contains anything the
converter does not recognise, it stops and names the line rather than dropping
it or passing it through raw. On the way in, if the HTML contains a tag outside
the subset, it stops and names the tag. A converter that guesses is the single
most likely way this feature loses a writer's work, and the fix is for it to
have no guessing branch.

```
Line 84 uses a footnote reference, which this converter does not handle.

Nothing was sent. Options:
  rewrite the footnote as an inline aside
  familiar push --strict=off   sends it as literal text, which is almost
                               certainly not what you want
```

**Test it against itself before trusting it.** Convert every `draft.md` in
`pieces/` to HTML and back, and diff. Any difference that is not whitespace is
a bug. This test costs nothing to run and should be the first thing in CI for
this feature.

### 4.1 beehiiv, first

**Why first.** Because it is where Intentionaut is published, and a tool that
works on the platform you do not use is a demonstration. Everything below is
the cost of that decision, stated plainly so it is chosen rather than
discovered.

**What the API can do**, verified today:

- Create: `POST /v2/publications/{id}/posts`, `title` required, and either
  `blocks` or `body_content` but not both. `body_content` is raw HTML.
  **[LIVE, developers.beehiiv.com/api-reference/posts/create, 30 Aug 2026]**
- Update: `PATCH /v2/publications/{id}/posts/{postId}`. Partial semantics,
  "Only the fields provided in the request body will be updated". It has a
  `content_merge_strategy` that defaults to `replace`, with `append`,
  `prepend` and `append_to_template` as alternatives. Familiar always sends
  `replace` explicitly and never relies on the default.
  **[LIVE, developers.beehiiv.com/api-reference/posts/update.md, 30 Aug 2026]**
- List: `GET /v2/publications/{id}/posts`, filtered by `status` on `draft`,
  `confirmed`, `archived` or `all`.
  **[LIVE, developers.beehiiv.com/api-reference/posts/index, 30 Aug 2026]**
- Get: `GET /v2/publications/{id}/posts/{postId}`.
  **[LIVE, developers.beehiiv.com/api-reference/posts/show.md, 30 Aug 2026]**
- Drafts became the create default on 6 August 2026: "a Create post API call
  made without a status parameter will default to draft instead of publishing
  automatically". **[LIVE, beehiiv help article 36759164012439, 30 Aug 2026]**
  Familiar passes `status: "draft"` explicitly on every call regardless. A
  default that changed once can change again, and the cost of being wrong here
  is a published post.

**The three constraints that shape the adapter.**

1. **Get returns rendered HTML, and never the editable document.** Content
   comes back through `expand` options named `free_web_content`,
   `free_email_content`, `premium_web_content` and similar, and the docs note
   "Generating HTML is slow". There is no `blocks` expand option.
   **[LIVE, posts/show.md, 30 Aug 2026]** So a pull cannot reconstruct the
   draft. It gets the rendered page, wrappers and all.
2. **Update is plan gated.** The update endpoint is "available to publications
   on the Max and Enterprise plans". **[LIVE, posts/update.md, 30 Aug 2026]**
   Below that, a writer can create drafts and cannot update them.
3. **There is no collision detection.** Nothing in the documented response
   gives a version marker to send back. **[LIVE, posts/update.md, 30 Aug 2026]**

**So the beehiiv adapter is push first.** `draft.md` is the source of truth and
beehiiv holds a copy. Push sends `body_content` as HTML. Pull exists, and it is
used to answer one question only: has the remote copy changed since Familiar
last wrote it. It answers that by hashing the rendered content and comparing,
which is exactly the mechanism section 2 already describes.

If the writer has edited in beehiiv's editor, `status` will say the remote
moved, and the honest instruction is to copy those edits back by hand, once.
Familiar will not pretend it can merge a rendered page into a Markdown draft.

**On a plan without update**, `connect` says so at connect time, and push
creates a new draft each run, titled `<Title> (Familiar, 30 Aug 14:02)`,
leaving the previous one untouched. Clutter the writer can see and delete is a
better failure than a silent no-op.

**What can be lost.** Polls, buttons, paywall breaks, section blocks, adverts
and embeds are all block types the create endpoint understands that plain HTML
does not carry back. Style handling is specific: "style tags are removed. All
style block elements are stripped" while "inline styles are preserved".
**[LIVE, posts/create, 30 Aug 2026]** So a draft assembled from beehiiv blocks
should be finished in beehiiv. A draft that is prose, which is what a
Familiar piece is, survives.

**Because beehiiv gives no collision detection, the general mechanism gets
built first.** That is the quiet benefit of this ordering. Had Ghost gone
first, the temptation would have been to lean on `updated_at` and discover
later that it does not generalise. Building the hash comparison for beehiiv
means Ghost inherits a mechanism that already works, and uses `updated_at` as
a second, better check on top.

### 4.2 Ghost, next

**Why second.** It is the only one of the three with a documented, supported
API complete enough for a real two way sync, and the only one where the
dangerous part is handled by the vendor.

- Content format: "By default, the API expects and returns content in the
  **Lexical** format only", and `formats=html,lexical` returns both.
  **[LIVE, docs.ghost.org/admin-api/posts, 30 Aug 2026]**
- Updating requires `updated_at`: "The `updated_at` field is required as it is
  used to handle collision detection", and the docs recommend "perform a GET
  request to fetch the latest data before updating a post".
  **[LIVE, docs.ghost.org/admin-api/posts/updating-a-post, 30 Aug 2026]**
  A mismatch raises `UpdateCollisionError`, the same error Ghost shows in its
  own editor as "Someone else is editing this post".
  **[LIVE, github.com/TryGhost/Ghost issue 10691, read 30 Aug 2026]**
- Sending HTML instead of Lexical: `PUT /ghost/api/admin/posts/:id/?source=html`,
  with the post object wrapped in a `posts` array. The `html` field on its own
  is not writeable, because Ghost regenerates it from Lexical.
  **[LIVE, forum.ghost.org thread 44374, read 30 Aug 2026. A forum resolution
  rather than a documented parameter, so verify before shipping.]**
- Auth: a JWT signed HS256 from the Admin API key. `hmac`, `hashlib`, `base64`
  and `json` are all standard library, so this needs no dependency. **[LIVE]**

**Round trip:** pull with `formats=html,lexical`, convert the HTML to Markdown
for `draft.md`, push with `?source=html`. Send `updated_at` from the GET
performed immediately before, and treat a collision error as a conflict under
section 2 rather than as something to retry.

**What can be lost.** Markdown cannot hold everything Lexical can. Ghost cards
for embeds, galleries, bookmarks, buttons, toggles and email-only blocks have
no Markdown spelling. The converter in 4.0 refuses rather than flattening:

```
This draft contains 2 blocks Markdown cannot hold:
  a bookmark card and an email-only block.

Pulling would flatten them, and pushing back would delete them. Options:
  familiar pull --text-only   work on the prose; push is disabled for this piece
  keep those blocks last in Ghost, and pull before you add them
```

### 4.3 Substack, last and optional

**There is no official API.** What exists is a set of unofficial tools.

- `python-substack`, version 0.4.0, released 24 August 2026, can "create, list,
  inspect, schedule, unschedule, publish, and delete Substack drafts", converts
  Markdown to rich drafts, and uploads local images. It authenticates with
  email and password, or with browser cookies, and the maintainer notes cookies
  are "usually more reliable when Substack requires captcha or magic-link
  sign-in". **[LIVE, pypi.org/project/python-substack, 30 Aug 2026]**
- Its own warning: "This project is not affiliated with Substack. It uses
  undocumented Substack interfaces that may change without notice."
  **[LIVE, same page]**
- It already separates the two operations Familiar cares about: "`substack
  drafts create` always creates an unpublished draft. It never schedules,
  sends, publishes, or deletes content." **[LIVE, same page]**

**How to treat it.** As an optional dependency Familiar never installs and
never requires. If the writer has it, the adapter shells out to it. If not,
`connect substack` explains the situation in two sentences and offers the
clipboard path.

**Say the risk in the product, not only here.** The `connect substack` output
should carry it:

```
Substack has no official API. This uses a community library that talks to
undocumented endpoints, and it can break with no notice. Familiar will tell
you when it breaks. It will not guess.
```

**The fallback that always works.** `familiar push --clipboard` puts the draft
on the clipboard as HTML, and `familiar pull --paste` reads it back. It is
manual, it depends on nothing, and it is the honest floor. It is also the
answer for any platform nobody has written an adapter for, so it is worth
shipping early rather than last.

**What can be lost:** footnotes are the specific worry, because Substack
footnotes have no Markdown spelling and are a real part of how essays are
written there. Subtitle, section and paywall markers are editor concepts rather
than document ones. **[NEEDS SOURCE: how python-substack 0.4.0 represents
footnotes and subtitles on the way in, and whether they survive a round trip.
Test with a real draft before this adapter goes past a preview.]**

### 4.4 Summary

| | beehiiv | Ghost | Substack |
|---|---|---|---|
| Official API | yes | yes | no |
| Create draft | yes | yes | via community library |
| Update draft | Max and Enterprise plans only | yes | via community library |
| Read draft content | rendered HTML only | yes, Lexical and HTML | via community library |
| Collision detection | none found | yes, `updated_at` | none |
| Familiar's stance | push first, pull to detect change | two way sync | optional, warned, clipboard floor |
| Order | first, because it is used | second, because it works properly | last, because it may break |

## 5. What changes in the prompts

Very little, which is the point. The adapter writes `draft.md`, so the stages
carry on reading `draft.md`.

**One line, added to the Setup section of `prompts/dev-edit.md`,
`prompts/line-edit.md` and `prompts/draft.md`, after the existing "Read the
piece's draft.md" line:**

> If `remote.json` is in the piece folder, say in one line where the draft
> lives and when it was last synced. If it says the remote copy has changed
> since then, stop and tell the writer to pull or resolve it first. Do not
> edit a stale draft.

That is the whole prompt change. It keeps the prompts tool-agnostic: the prompt
reads a JSON file that is already on disk, and never fetches anything.

**`prompts/social.md`** needs nothing. It already has the strictest gate in the
system and does not touch `draft.md`.

**`AGENTS.md`** needs a new short section after "Moving between stages":

> ## Commands, and how they differ from stages
>
> `status`, `resume`, `pull`, `push` and `link` are commands. They make no
> editorial decision, so they have no gate. `push` confirms before it sends,
> because it changes something outside this machine. Nothing else in Familiar
> reaches the network. Keys and tokens never go in a file this repo tracks.

**`skills/familiar/SKILL.md`** needs the commands added under the stage table,
kept separate from it so the router does not treat them as stages:

> Commands, which have no gate because they make no editorial decision:
> `status`, `resume <piece>`, `pull <platform> <post> <piece>`, `push <piece>`,
> `link <piece>`. Run `scripts/cms.py` for the last three.

**`dex/familiar/SKILL.md`** needs the same block, plus one line under "What Dex
adds", because the vault changes where things are:

> **Status across the vault.** `status` reads `04-Projects/Writing/*/`, not
> `pieces/`. Credentials come from the keychain, never from the vault.

**`knowledge/context-log.md`** needs its first line corrected to the per-piece
location, and a line saying `status` reads the last entry and quotes the
decision gate verbatim, so that whoever writes an entry knows it will be read
by a machine as well as a person.

---

## 6. Phases

### Phase 1: status and resume. No CMS at all.

**What ships.** `scripts/status.py`. Reading piece folders, deriving the stage
from files, reading the last context entry, printing the table, `resume`, the
root-log split for other people's clones, and the `AGENTS.md` section on
commands.

**Why still first.** It needs no credentials, no network and no vendor, and it
is the thing a writer with four pieces in flight feels immediately. It is a
weekend for one person, and most of that weekend is deciding what the table
says rather than writing code.

**What it proves.** That the context log is worth machine-reading. If the
decision-gate lines turn out to be too vague to print, that is a finding about
the prompts, and it changes what every stage writes. Better to learn it here
than after an adapter exists.

**Stop if:** the derived stage disagrees with the writer's own sense of where a
piece is, more than about once in ten. That means the file-order model is wrong
and needs rethinking before anything is built on it.

### Phase 2: the Markdown converter, and beehiiv push.

**What ships.** The converter from 4.0, both directions, with its refusal
behaviour and the round-trip test over every existing `draft.md`. Then
`scripts/cms.py` with the shared logic and the beehiiv adapter: `connect`,
`list`, `push`, `link`, `remote.json`, the hashes, and the conflict stop.

Pull ships in this phase too, limited to what beehiiv can honestly support: it
fetches the rendered content, hashes it, and updates `remote_hash`. It does not
overwrite `draft.md`. The command says so every time it runs.

**What it proves.** Two things. That a Familiar draft survives the trip into
beehiiv and looks right in the editor, and that the general conflict mechanism
works without a vendor's version marker to lean on.

**The test.** Take a finished Intentionaut issue, push it as a draft, open it
in beehiiv, and read it beside `draft.md`. Every heading, link, emphasis and
blockquote in the right place, and nothing added. Then change one word in
beehiiv, run `status`, and confirm it says the remote moved.

**Stop if:** the plan tier turns out to block updates and creating a new draft
per push is genuinely annoying rather than merely untidy. In that case the
honest product is push-once plus the clipboard, and the adapter should say so
rather than growing workarounds.

### Phase 3: Ghost, two way.

**What ships.** The Ghost adapter, JWT auth, `formats=html,lexical` on pull,
`?source=html` on push, `updated_at` as a second collision check on top of the
hashes, and the unsupported-block refusal wired to the converter.

**What it proves.** That the round trip is genuinely lossless when the platform
lets it be. The test is specific: pull a real post, change one sentence, push,
pull again, and diff. Anything that is not the one sentence is a bug in the
converter.

**Stop if:** the Markdown round trip cannot survive that test on ordinary
prose. A converter that quietly reorders or drops formatting fails the one rule
this feature cannot break, and there is no point continuing to Substack with a
broken foundation.

### Phase 4: the clipboard, then Substack.

**What ships.** `push --clipboard` and `pull --paste` first, because they work
everywhere and need nothing. Then the optional `python-substack` path behind
the warning in 4.3.

**What it proves.** Whether an unofficial integration can be offered without
promising something Familiar cannot keep.

**Stop if:** the community library needs a password rather than a cookie for
most people. Asking a writer to hand a tool their Substack password is a line
worth not crossing, and the clipboard path is a good enough answer instead.

## 7. Risks and refusals

The rule for this whole section: prevent, do not discourage. A refusal that
lives in a prompt is a preference. A refusal that lives in the absence of code
is a guarantee.

| Must never | How it is prevented |
|---|---|
| Publish a post | No publish code path exists. The adapter class has no publish method, the status field is hard coded to draft on every write, and the Substack adapter calls only the library's draft subcommands. There is nothing to call by mistake. |
| Schedule a send | Same. No adapter accepts a `scheduled_at`, `publish_at` or `send_at` field. Passing one is a programming error, and the shared layer strips scheduling keys from any document before it reaches an adapter. |
| Change a live post | `push` reads the post's status first. If it is anything other than a draft, it stops and says so. This is one API call and it is not optional. |
| Delete a draft | No delete code path exists, in any adapter, including the two platforms whose APIs offer it. |
| Overwrite a newer remote version | The hash comparison in section 2 does this for every platform, including the two that offer nothing. Ghost adds `updated_at` on top and returns a collision error of its own. A conflict stops rather than merging. `--force` is the only path through, it is typed by a human, and it names what it is discarding. |
| Put a credential in a tracked file | Credentials are read from the keychain or an environment variable at run time. `connect` writes to the keychain and prints nothing back. `remote.json` holds an id and a URL. |
| Send the writer's draft anywhere they did not ask | Only `push` reaches out, only on an explicit command, and it prints the platform, the post title and the word count before it does. |
| Lose work in a conflict | The remote copy is written to `draft.remote.md` and nothing is overwritten. Both versions exist on disk before the writer chooses. |

Three risks with no clean prevention, which should be stated in the product:

- **An unofficial API can break.** Substack, at any time. Familiar says so at
  connect time and reports the failure rather than retrying.
- **A converter can be subtly wrong.** Markdown to HTML and back is not
  lossless in general. The mitigation is the refusal in 4.1 and the diff test
  in phase 2, and neither is a proof.
- **A vendor can change a default.** beehiiv changed the create-post default on
  6 August 2026. **[LIVE]** The answer is to send every field explicitly and
  never rely on a default, anywhere.

---

## 8. Changelog entries, written first

House style from `CHANGELOG.md`: a headline in plain words, then "What this
gives you:" with bolded outcomes.

```markdown
## 0.4.0 (unreleased)

See every piece you have in flight, and what each one is waiting on.

**What this gives you:**

- **One view of the work.** `familiar status` lists every piece, the stage it
  reached, the decision waiting on you in your own words from the context log,
  and when you last touched it. Pieces you have not opened in a week fold away.
- **Pick a piece back up in one step.** `familiar resume <piece>` prints where
  it got to, the open decision, and the exact command to continue. It prints
  and stops; it never runs the next stage for you.
- **A context log per piece.** The log lives in the piece folder now, so moving
  or archiving a piece takes its history with it. An older log at the project
  root is split on first run, and copied rather than moved.
```

```markdown
## 0.5.0 (unreleased)

Send a finished draft straight to beehiiv, without keeping two copies.

**What this gives you:**

- **Your draft, in beehiiv, in one command.** `familiar push` writes the piece
  into beehiiv as a draft. Headings, links, emphasis and quotes arrive intact,
  because the converter refuses to send anything it cannot carry rather than
  flattening it.
- **It cannot publish or send.** There is no publishing code in it. It writes
  drafts, it says so explicitly on every call rather than trusting a default,
  and it checks a post is still a draft before touching it.
- **It tells you when the copy in beehiiv moved.** beehiiv hands back the
  rendered page and not the editable one, so Familiar can see that something
  changed and cannot bring the change down for you. It says exactly that,
  rather than guessing or overwriting.
- **It tells you what your plan allows before you connect.** Updating an
  existing draft needs a higher beehiiv plan. On a lower one, each push writes
  a new dated draft and leaves the old one alone.
```

```markdown
## 0.6.0 (unreleased)

Work on the draft that lives in Ghost, in both directions.

**What this gives you:**

- **Pull a draft, edit it, push it back.** Every stage works on the draft
  exactly as before. Familiar handles fetching it and sending the new version
  to the same draft in Ghost.
- **It will not overwrite you.** If the copy in Ghost changed while you were
  working, Familiar stops, saves the other version beside yours, and lets you
  compare them. Nothing is merged for you.
- **It says what it cannot carry.** A draft with bookmark cards or email-only
  blocks is flagged before anything is pulled, because plain text cannot hold
  them and pushing back would delete them.
```

```markdown
## 0.7.0 (unreleased)

A clipboard path that works anywhere, and Substack with the risk stated.

**What this gives you:**

- **Copy a finished draft anywhere.** `push --clipboard` puts the piece on your
  clipboard, formatted, ready to paste into any editor. No account, no key, no
  integration required.
- **Substack drafts, honestly.** Substack has no official API. Familiar can use
  a community library if you already have it, it says so before you connect,
  and it tells you when it breaks rather than guessing.
```

---

## What is still open

The first two questions from the original plan are answered and applied. Three
remain, and the first one blocks phase 2.

1. **Which beehiiv plan is Intentionaut on?** Updating an existing draft is
   limited to Max and Enterprise. **[LIVE, posts/update.md, 30 Aug 2026]** On
   anything lower, phase 2 ships as create-only, every push leaves a new dated
   draft, and that is the product rather than a bug to work around. This needs
   answering before any code is written, because it changes what the adapter
   is.

2. **Where does the beehiiv API key come from, and does it already exist?**
   The plan assumes an API key with `posts:write`. If Intentionaut's beehiiv
   account does not have API access on its plan, phase 2 stops before it starts
   and the clipboard path in phase 4 becomes the thing worth building first.

3. **What is the honest size of the problem?** This plan assumes several pieces
   in flight at once. There are two piece folders on this machine. If the real
   number stays under three, phase 1 is most of the value, and phases 2 to 4
   are a bet on a future workload. Worth saying out loud before a weekend goes
   into it.
