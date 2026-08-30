# Plan: drafts at a glance, and the CMS as the draft store

**Written:** 30 August 2026. **Status:** proposal, nothing built.
**Scope:** two additions to Familiar. A `status` command that shows every piece
in flight, and a set of adapters that let a stage work against a draft that
lives in Ghost, beehiiv or Substack.

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

### A contradiction to resolve first

The repo disagrees with itself about where the context log lives.

- `knowledge/context-log.md:3`: "`SESSION-CONTEXT.md` **at the project root**
  is how a piece survives a closed terminal." **[READ]**
- All eight prompts repeat "the project root `SESSION-CONTEXT.md`", for example
  `prompts/draft.md:58`. **[READ]**
- `dex/familiar/SKILL.md:92-93`: "Familiar's `SESSION-CONTEXT.md` lives in the
  **piece folder**, not the vault root, so it never collides with Dex's own
  session files." **[READ]**

So a Dex user and a standalone user store the same information in two
different places. This has to be settled before `status` can read anything.
The plan settles it in section 1.

Two small bugs found while reading, unrelated to this work, worth a one line
fix each: `prompts/dev-edit.md:37` reads "They accept, reject, or revises each
item herself", left over from the de-gendering pass, and `prompts/outline.md:7`
still says "the target issue folder" where every other file says piece.

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

Move to **one `SESSION-CONTEXT.md` per piece folder**, which is what
`dex/familiar/SKILL.md:92` already does. Three reasons: a piece is a folder and
should be self contained, so moving or archiving a piece takes its history with
it; a shared root file grows without bound and mixes twenty pieces into one
stream; and Dex already collides with a vault-root file.

Migration is one pass and it is safe, because the existing entry heading already
names the piece. `knowledge/context-log.md:10` defines the heading as
`## YYYY-MM-DD HH:MM  <stage>  <piece folder>`, and the real log on this machine
follows it: `## 2026-08-30 08:55  line-edit  pieces/2026-08-30-kernic-site-copy`.
**[READ]** So `status` can split a root log into per-piece logs with no
guessing. Ship the migration inside `status` itself: on first run, if a root
`SESSION-CONTEXT.md` exists, offer to split it, and copy rather than move so
nothing is destroyed.

Until the split happens, `status` reads both and prefers the per-piece file.

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
$ familiar connect ghost

  1. In Ghost, go to Settings, Integrations, Add custom integration.
  2. Name it Familiar. Copy the Admin API key. It looks like
     6512c0a1e4b0f0f0f0f0f0f0:9a8b7c...
  3. Paste it here. It goes into your keychain, never into a file.

  Admin API URL: https://example.com
  Admin API key: ****

  Connected. 3 drafts, 41 published posts. Familiar can read and update
  drafts. It cannot publish; there is no code in it that can.
```

The last line matters. A writer handing a tool an admin key deserves to be told
what it will refuse to do, at the moment they hand it over.

---

## 4. The adapters

Build order is set by what each API can actually do, verified today.

### 4.1 Ghost, first

**Why first.** It is the only one of the three with a documented, supported,
complete API, and it is the only one with collision detection built in, which
means the risky part of this whole feature is handled by the vendor.

- Content format: "By default, the API expects and returns content in the
  **Lexical** format only", and `formats=html,lexical` returns both.
  **[LIVE, docs.ghost.org/admin-api/posts, 30 Aug 2026]**
- Updating requires `updated_at`: "The `updated_at` field is required as it is
  used to handle collision detection", and the docs recommend "perform a GET
  request to fetch the latest data before updating a post".
  **[LIVE, docs.ghost.org/admin-api/posts/updating-a-post, 30 Aug 2026]**
  A mismatch raises `UpdateCollisionError`, the same error Ghost surfaces in its
  own editor as "Someone else is editing this post".
  **[LIVE, github.com/TryGhost/Ghost issue 10691, read 30 Aug 2026]**
- Sending HTML instead of Lexical: `PUT /ghost/api/admin/posts/:id/?source=html`,
  with the post object wrapped in a `posts` array. The `html` field on its own
  is not writeable, because Ghost regenerates it from Lexical.
  **[LIVE, forum.ghost.org thread 44374, read 30 Aug 2026. This is a forum
  resolution rather than a documented parameter, so verify before shipping.]**
- Auth: a JWT signed HS256 from the Admin API key. `hmac`, `hashlib`, `base64`
  and `json` are all standard library, so no dependency is needed. **[LIVE]**

**Round trip:** pull with `formats=html,lexical`, convert the HTML to Markdown
for `draft.md`, push with `?source=html` after converting back.

**What can be lost, and the honest answer.** Markdown cannot hold everything
Lexical can. Ghost cards for embeds, galleries, bookmarks, buttons, toggles and
email-only blocks have no Markdown spelling. The pull will flatten them.

The fix is to refuse rather than to flatten silently. On pull, walk the Lexical
tree, and if it contains a node type that has no Markdown equivalent, name it
and stop:

```
This draft contains 2 blocks Markdown cannot hold:
  a bookmark card and an email-only block.

Pulling would flatten them, and pushing back would delete them. Options:
  familiar pull --text-only   work on the prose, push is disabled for this piece
  edit those blocks in Ghost, and pull again once they are the last thing you add
```

A plain prose draft, which is what most newsletter issues are, round trips
cleanly. A draft full of cards should be edited where the cards live.

### 4.2 beehiiv, second

**What is there.** More than expected, and asymmetric in a way that decides the
design.

- Create: `POST /v2/publications/{id}/posts`, `title` required, and either
  `blocks` or `body_content` but not both. `body_content` is raw HTML.
  **[LIVE, developers.beehiiv.com/api-reference/posts/create, 30 Aug 2026]**
- Update: `PATCH /v2/publications/{id}/posts/{postId}`. Partial semantics,
  "Only the fields provided in the request body will be updated". Has a
  `content_merge_strategy` that defaults to `replace`.
  **[LIVE, developers.beehiiv.com/api-reference/posts/update.md, 30 Aug 2026]**
- List: `GET /v2/publications/{id}/posts`, with `status` filtering on `draft`,
  `confirmed`, `archived` or `all`.
  **[LIVE, developers.beehiiv.com/api-reference/posts/index, 30 Aug 2026]**
- Get: `GET /v2/publications/{id}/posts/{postId}`.
  **[LIVE, developers.beehiiv.com/api-reference/posts/show.md, 30 Aug 2026]**
- Drafts are the default from 6 August 2026: "a Create post API call made
  without a status parameter will default to draft instead of publishing
  automatically". **[LIVE, beehiiv help article 36759164012439, 30 Aug 2026]**
  Familiar should pass `status: "draft"` explicitly anyway and never rely on a
  default that changed once and could change again.

**Two constraints that shape the adapter.**

1. **Get returns rendered HTML, and no blocks.** The content comes back through
   `expand` options named `free_web_content`, `free_email_content`,
   `premium_web_content` and similar, and the documentation notes "Generating
   HTML is slow". There is no `blocks` expand option.
   **[LIVE, posts/show.md, 30 Aug 2026]** So a pull cannot reconstruct the
   editable document. It gets the rendered page, wrappers and all.
2. **Update is plan gated.** The update endpoint is "available to publications
   on the Max and Enterprise plans". **[LIVE, posts/update.md, 30 Aug 2026]**
   A writer on a lower plan can create drafts and cannot update them.

**So the beehiiv adapter is push first.** Familiar's `draft.md` is the source of
truth, beehiiv holds the copy. Push sends `body_content` as HTML. Pull is used
to detect that the remote changed, by hashing the rendered content, rather than
to rebuild `draft.md`. If the writer has edited in beehiiv's UI, `status` will
say the remote moved and the honest instruction is to copy the changes back by
hand, once.

On a lower plan, `connect` says so at connect time and push creates a new draft
each time, named `Title (Familiar, 30 Aug 14:02)`, leaving the old one alone.
Creating clutter is a better failure than silently doing nothing.

**What can be lost:** polls, buttons, paywall breaks, section blocks, adverts
and embeds are all block types the create endpoint understands and that plain
HTML does not carry back. Inline styles survive a push, style blocks do not:
"style tags are removed. All style block elements are stripped" while "inline
styles are preserved". **[LIVE, posts/create, 30 Aug 2026]**

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
  drafts create` always creates an unpublished draft. It never schedules, sends,
  publishes, or deletes content." **[LIVE, same page]** That is a good
  neighbour to a tool with Familiar's refusals.

**How to treat it.** As an optional dependency that Familiar never installs and
never requires. If the writer has it, the Substack adapter shells out to it. If
they do not, `connect substack` explains the situation in two sentences and
offers the clipboard path instead.

**Say the risk in the product, not only in this plan.** The `connect substack`
output should carry the warning:

```
Substack has no official API. This uses a community library that talks to
undocumented endpoints, and it can break with no notice. Familiar will tell
you when it breaks. It will not guess.
```

**The fallback that always works.** `familiar push --clipboard` puts the draft
on the clipboard as HTML, and `familiar pull --paste` reads it back. It is
manual, it depends on nothing, and it is the honest floor. Ship it in the same
phase, because it is also the answer for any platform nobody has written an
adapter for.

**What can be lost:** footnotes are the specific worry. Substack footnotes have
no Markdown spelling and are a real part of how essays are written there.
Subtitle, section, and paywall markers are also editor concepts rather than
document ones. **[NEEDS SOURCE: how python-substack 0.4.0 represents footnotes
and subtitles on the way in, and whether they survive a round trip. Test with a
real draft before this adapter goes past a preview.]**

### 4.4 Summary

| | Ghost | beehiiv | Substack |
|---|---|---|---|
| Official API | yes | yes | no |
| Create draft | yes | yes | via community library |
| Update draft | yes | Max and Enterprise plans only | via community library |
| Read draft content | yes, Lexical and HTML | rendered HTML only | via community library |
| Collision detection | yes, `updated_at` | none found | none |
| Familiar's stance | two way sync | push first, pull to detect change | optional, warned, clipboard floor |

---

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
root-log split, and the `AGENTS.md` section on commands.

**Why first.** It is useful on its own, it needs no credentials, no network and
no vendor, and it is the thing a writer with four pieces in flight feels
immediately. It is a weekend for one person, and most of that weekend is
deciding what the table says rather than writing code.

**What it proves.** That the context log is worth machine-reading. If the
decision-gate lines turn out to be too vague to print, that is a finding about
the prompts and it changes what the stages write. Better to learn it here than
after three adapters exist.

**Stop if:** the derived stage disagrees with the writer's own sense of where a
piece is, more than about once in ten. That means the file-order model is wrong
and needs rethinking before anything is built on it.

### Phase 2: Ghost, two way.

**What ships.** `scripts/cms.py` with the shared logic and the Ghost adapter.
`connect`, `list`, `pull`, `push`, `link`, `remote.json`, hashes, the conflict
stop, the unsupported-block refusal, and the one line added to three prompts.

**What it proves.** That the round trip preserves a real draft. The test is
specific: take a published Intentionaut issue, pull it, change one sentence,
push it, pull it again, and diff. Anything that is not the one sentence is a
bug in the converter.

**Stop if:** the Markdown round trip cannot survive that test on ordinary prose.
A converter that quietly reorders or drops formatting fails the one rule this
feature cannot break.

### Phase 3: beehiiv, push first.

**What ships.** The beehiiv adapter, the plan check at connect time, the
create-new-draft fallback for lower plans, and the remote-changed detection.

**What it proves.** That an asymmetric platform can be supported honestly, with
the tool saying what it cannot do rather than pretending.

**Stop if:** the rendered-HTML pull turns out to be so far from the editable
draft that "the remote changed" fires constantly. A change detector that cries
wolf gets ignored, and then it is worse than nothing.

### Phase 4: Substack and the clipboard.

**What ships.** `push --clipboard` and `pull --paste` first, because they always
work. Then the optional `python-substack` path behind a clear warning.

**What it proves.** Whether an unofficial integration can be offered without
promising something Familiar cannot keep.

**Stop if:** the community library needs a password rather than a cookie for
most people. Asking a writer to hand a tool their Substack password is a line
worth not crossing, and the clipboard path is a perfectly good answer instead.

---

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
| Overwrite a newer remote version | Ghost enforces it with `updated_at` and returns a collision error. For beehiiv and Substack, the hash comparison in section 2 does the same job, and a conflict stops rather than merging. `--force` is the only path through, and it is typed by a human and names what it is discarding. |
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
- **A context log per piece.** The log moves from one shared file into each
  piece folder, so moving or archiving a piece takes its history with it. Your
  existing log is split on first run, and copied rather than moved.
```

```markdown
## 0.5.0 (unreleased)

Work on the draft that lives in Ghost, without keeping two copies.

**What this gives you:**

- **Pull a draft, edit it, push it back.** Every stage works on the draft
  exactly as before. Familiar handles fetching it and sending the new version
  to the same draft in Ghost.
- **It cannot publish.** There is no publishing code in it. It writes drafts,
  it checks a post is still a draft before it touches it, and it will not send
  a scheduled post.
- **It will not overwrite you.** If the copy in Ghost changed while you were
  working, Familiar stops, saves the other version beside yours, and lets you
  compare them. Nothing is merged for you.
- **It says what it cannot carry.** A draft with bookmark cards or email-only
  blocks is flagged before anything is pulled, because plain text cannot hold
  them and pushing back would delete them.
```

```markdown
## 0.6.0 (unreleased)

beehiiv drafts, with the parts beehiiv cannot do said plainly.

**What this gives you:**

- **Send a finished draft to beehiiv.** Familiar writes it as a draft, never a
  send, and tells you the plan you need for updates before you connect rather
  than after.
- **It tells you when the copy in beehiiv moved.** beehiiv gives back the
  rendered page and not the editable one, so Familiar can see that something
  changed and cannot bring the change down for you. It says exactly that.
```

```markdown
## 0.7.0 (unreleased)

Substack, and a clipboard path that works anywhere.

**What this gives you:**

- **Copy a finished draft anywhere.** `push --clipboard` puts the piece on your
  clipboard, formatted, ready to paste into any editor. No account, no key.
- **Substack drafts, with the risk stated.** Substack has no official API.
  Familiar can use a community library if you have it installed, and it says so
  before you connect, and it tells you when it breaks rather than guessing.
```

---

## Three questions before phase one starts

1. **Does the context log move to per-piece files?** It is the right shape and
   Dex already assumes it, but it changes eight prompts and the format doc, and
   it is your working state. Yes moves the plan forward as written. No means
   `status` parses the shared root file by its heading, which works today and
   gets slower and noisier as pieces pile up.

2. **Which platform do you actually publish on?** Intentionaut is on beehiiv,
   which is the platform with the weakest read path and a plan gate on updates.
   Building Ghost first is right on the engineering merits and gives you nothing
   you can use. Say whether phase 2 should be Ghost, because it proves the
   design properly, or beehiiv, because it is the one you would use on the third
   of September.

3. **What is the honest size of the problem?** This plan assumes several pieces
   in flight at once. Right now there are two piece folders on this machine. If
   the real number stays under three, phase 1 is most of the value and phases 2
   to 4 are a bet on a future workload. Worth saying out loud before a weekend
   goes into it.
