# Channels

The canonical channel registry: one block per place a piece can appear.
Every stage that routes, shapes, repurposes or schedules writing reads this
file, and only this file, for what a channel is. A channel that is not
declared here is unknown: the stage stops and says so rather than guessing a
form for it.

Channel ids are stable. Stages, briefs, `social.md` and the schedule name a
channel by its id, never by a paraphrase.

## Channel and destination are different things

A **channel** is where, why and how a piece appears: its job in the system,
who reads it there, the form and length it rewards, and its cadence.

A **destination** is the single place a piece's call to action sends the
reader. Every post, issue or page carries exactly one destination, decided
before it is written. A piece appearing on two channels still picks one
destination each time it appears. Never collapse the two: "posted to
LinkedIn" answers where it appeared; "points at the newsletter list" answers
where the reader goes next.

Destinations are built and tracked in `knowledge/links.md`. This file says
which destinations a channel may use. One post, one destination: a post
driving to the newsletter list never also plugs the site, and a post driving
to the site never also plugs the list.

## Channel: linkedin-feed

- **Job:** Reach and discovery. The channel new readers arrive through.
- **Schedule name:** LinkedIn
- **Audience:** [segment ids from `knowledge/audiences.md`, or from
  `positioning.md` Segments until the audience model lands. Founders,
  product leaders, operators and peers who have not met the work yet.]
- **Voice overlay:** The short-form register: `knowledge/social-rules.md`
  over `knowledge/voice-guide.md`. A register, never a second voice guide.
- **Form and length:** Original posts, proof-led. About 1,300 characters
  comfortable, 3,000 hard.
- **Cadence:** Three original posts a week. Fewer, better posts beat a full
  grid; an empty slot beats a filler post.
- **Source material:** Shipped pieces, build logs and the back catalogue.
  Every post is built from something the source actually says.
- **Default CTA and destination:** Exactly one destination per post. The
  default is the piece or the newsletter list; the hub or a product
  destination only when the post's job says so.
- **Link placement:** First comment, never in the post body. The comment is
  added and pinned by hand after the post is live.
- **utm:** source `linkedin.com`, medium `social`, per `knowledge/links.md`.
- **Relationships:** Companion to `linkedin-newsletter`. A feed post may
  point at a newsletter issue but never reproduces it; identical copy never
  appears on both.
- **Review and publish gate:** The `social` stage's two gates, then the
  `publish` confirm gate and the never-publish check. Nothing schedules
  itself.

## Channel: linkedin-newsletter

- **Job:** Reach and discovery for the agent-organisation work, among people
  in AI and technology who have no direct relationship with the writer yet.
- **Audience:** [segment ids as above. AI and technology readers discovering
  the work on LinkedIn rather than already reading the main publication.]
- **Voice overlay:** The field-note register: `knowledge/voice-guide.md`,
  executive level. Crisp claim, receipt attached, no posturing.
- **Form and length:** 600 to 900 words. Each issue carries one claim, one
  receipt, one honest failure or limit, and one operating lesson. Nothing
  publishes without a receipt.
- **Cadence:** Fortnightly.
- **Source material:** The live build: what shipped, the decisions behind
  it, what broke. Receipts come from the working files, never invented.
- **Default CTA and destination:** One destination per issue, alternating
  between joining the main newsletter list and the relevant page on the
  hub. Never both in one issue.
- **Link placement:** Inline in the issue. The first-comment rule belongs
  to the feed, not here.
- **utm:** source `linkedin.com`, medium `newsletter`, per
  `knowledge/links.md`.
- **Relationships:** Companion to `intentionaut-newsletter`, never its
  mirror. Every two or three field notes feed one deeper synthesis there.
  Identical full-article cross-posting is never allowed.
- **Review and publish gate:** The full stage pipeline, interview to
  finalise, and the writer's review of the finished issue. Nothing
  publishes without a receipt attached.

## Channel: intentionaut-newsletter

- **Job:** Owned depth. The publication the writer owns the reader
  relationship through.
- **Audience:** [segment ids as above. Subscribers: readers with a direct
  relationship, who chose the list.]
- **Voice overlay:** The essay register of `knowledge/voice-guide.md`.
- **Form and length:** The essay. A synthesis of two or three field notes
  that adds a model, framework or full case the field notes did not carry.
  Never a mirror of a LinkedIn issue.
- **Cadence:** The publication's cadence, declared in `positioning.md`.
- **Source material:** The field notes from `linkedin-newsletter`, the
  working files behind them, and anything `harvest` surfaces for the
  piece's theme and audience.
- **Default CTA and destination:** The issue is the destination. Where it
  points elsewhere, it points at one place: usually the hub page holding
  the body of work.
- **Link placement:** Inline.
- **utm:** Links out of the issue follow `knowledge/links.md`; the issue
  itself is the destination other channels' campaigns point at.
- **Relationships:** The deeper sibling of `linkedin-newsletter`. Synthesis
  adds what the field notes did not carry; it never reprints them.
- **Review and publish gate:** The full stage pipeline and the writer's
  approval of the final copy.

## Channel: hub

- **Job:** Durable authority and commercial context. The home of the body
  of work: artefacts, cases, biography and the advisory route.
- **Audience:** [People checking the work after meeting it elsewhere,
  including anyone weighing an advisory conversation.]
- **Voice overlay:** `knowledge/voice-guide.md`, web register.
- **Form and length:** Evergreen pages. No length constraint; a page is as
  long as the job needs.
- **Cadence:** Evergreen, on demand. No weekly rhythm. The hub is a
  destination first and a channel second.
- **Source material:** Shipped pieces, cases and artefacts, kept current.
- **Default CTA and destination:** The hub is a destination. A page routes
  the reader to one next step: the advisory conversation or the newsletter
  list, never both stacked.
- **Link placement:** Not applicable.
- **utm:** The hub is what campaigns point at; it is a destination in
  `knowledge/links.md`, not a source.
- **Relationships:** What the other channels point at. The hub holds the
  durable version; channels excerpt and link.
- **Review and publish gate:** The writer reviews any page before it goes
  live.

## Channel: product-destination

- **Job:** The destination for career-evidence stories only. [The writer's
  careers product. Its named entry lives in the writer's house; see
  `docs/plans/channels-registry.md`.]
- **Audience:** [Jobseekers and the people who coach them.]
- **Voice overlay:** The product's own copy register, kept separate from
  the newsletter and social registers.
- **Form and length:** Set by the product's own surfaces, declared in the
  writer's house copy of this file.
- **Cadence:** On demand.
- **Source material:** Career-evidence stories only.
- **Default CTA and destination:** This is a destination, not a channel for
  general material. Generic agent-organisation material must not route here
  merely because a post needs a CTA.
- **Link placement:** Not applicable.
- **utm:** A destination in `knowledge/links.md`, not a source.
- **Relationships:** Destination for career-evidence posts on
  `linkedin-feed`. Nothing else points here.
- **Review and publish gate:** The writer reviews anything that names or
  links the product.

## Adding a channel

One new block, every field answered or marked `unknown`. A channel without
a job is a habit, and a channel without a gate is a leak: declare both or
do not add it. Stages read the registry at run time, so a new block is the
whole change. When the channel has slots in `social-schedule.md`, give it a
**Schedule name:** matching the name that file's tables use, so
`scripts/channel_check.py` can hold the two files to one answer.

## What a channel is not

- Not a scheduler account. Scheduler ids stay in `knowledge/social-schedule.md`.
- Not a destination. Destinations live in `knowledge/links.md`.
- Not a theme or an audience. Those are declared once, in their own files,
  and referenced here by id.
