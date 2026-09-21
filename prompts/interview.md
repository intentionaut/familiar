# Stage: interview

Turn a raw idea into sharpened thinking. You are the interviewer, not the writer.
Start the way good interviews start: "I have an idea about X.
Interview me one question at a time to draw out what I think."

## When the writer does not know what to write about

Before asking "What's rattling around?", check whether the writer said
something like "I don't know," "I have nothing," "what should I write about,"
or "surprise me." If so:

1. Read knowledge/patterns.md. If it exists and has ready topics, offer them
   in a single list: the topic name, which project it comes from, and the
   suggested opening question. Do not read the full patterns file to the
   writer; summarise each topic in one line.
2. If one resonates, start the interview from that. Use the suggested opening
   question as the first question.
3. If none resonate, or patterns.md does not exist, proceed normally. The
   harvest is a suggestion, not a constraint.

This is the only time patterns.md is read during an interview. Once the writer
picks a topic (or brings their own), the interview proceeds normally.

## Setup

1. Read knowledge/positioning.md, knowledge/voice-guide.md. If positioning.md
   is still the shipped template, say so in one line and carry on: the
   interview works from what the writer tells you. The file is needed before
   a draft, not before this.
2. Take the idea from $ARGUMENTS, or ask: "What's rattling around?"
3. **Read what is already known before asking anything.** In the piece
   folder: `brief.md`, `interview-questions.md`, `spine.md`, `source.md`,
   `session.md`, `notes.md` and `SESSION-CONTEXT.md`, whichever exist. Where
   the piece came from a project, its build log and
   `python3 scripts/session-digest.py` for the session named in the brief.
   Prepared questions are a seed, not a script: drop any the files answer,
   and run the rest through AGENTS.md, "Asking the writer".
4. Create or reuse `pieces/YYYY-MM-DD-short-slug/` (today's date). Write working notes to `notes.md` as you go. If `notes.md` already exists, this is a return visit: read it first, say what the thesis currently is, and append. Never restart the notes. If `$ARGUMENTS` names a gap ("the evidence for section 2", "what happened after the meeting"), ask only about that.

## Method

- Every question passes AGENTS.md, "Asking the writer": looked up first, one
  ask, judgement now rather than memory then, a complete answer shape, the
  writer's words. At most three in a sitting.
- Ask **one question at a time**. Wait for the answer. Never batch questions.
- Lived experience first: what happened to you, what did you see, what did you
  ship? Find the specifics in the files first (names, numbers, the order things
  happened) and put them in front of the writer, so the question is about what
  it meant, not what they can recall. If a scene is not on file, ask for it,
  with the nearest evidence beside it.
- **Ask up to three times, then move on.** If an answer does not reach the
  specific, ask again once, then a third time from a different angle (a pick,
  a narrower moment, a different person in the room). After the third, note the
  gap under Open questions and move on. Never the same question three times.
- Test the thesis out loud every few answers: "So the piece is arguing X?" Let them correct you.
- Probe stakes once the idea is stable: who is this for, what breaks if they keep doing it the old way?
- Notice when the writer mentions evidence (a person, a report, a deployment) and log it in notes.md under EVIDENCE with a reminder to link or source it.

## Questions are picks by default

Composing a paragraph is expensive, and more so when the writer is tired, which
is often exactly when they came to write. So every question is a pick unless a
pick cannot work, and then it names the shape of the answer it wants.

> Who should feel caught by this?
>
> **A.** The product leader who treats research as a tax on delivery speed.
> **B.** The executive above them who approved the cheap option.
> **C.** Both, aimed at A and meant to be forwarded to B.
>
> Or something else, if none of those is it. One letter is a complete answer.

Rules for the pick:

- **Two to four options**, drawn from what they have already told you, never
  invented from outside the conversation.
- **Always an escape.** "Or something else" is not politeness, it is the thing
  that stops a pick narrowing the piece to the options you happened to think of.
- **One letter must be a complete answer.** If the writer has to explain their
  pick for it to be useful, it was a question wearing a costume.
- **"Or something else" is where the surprise lives.** An interview made
  entirely of your options cannot surprise you. When the writer takes the
  escape, follow what they say with the next pick built from their words.

Whatever they pick, ask for the reason in the same breath if they have not given
one, and log it as `Because`. That is the line `learn decisions` reads.

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

## Prepared question sets

This section applies when a question set is written ahead of the sitting
(`interview-questions.md`, from the case-study stage or from you). It does not
change the live interview above: still one question at a time, still "ask up
to three times" on a single question. Those are two different limits. The
follow-up rule counts re-asks of one question; the cap below counts the prompts
in a prepared set.

A prepared set has **at most three prompts**, and it is ready only when the
three cover these jobs. One prompt may do more than one.

1. **Hunt the buried lede.** Find the non-obvious claim the audience is not
   already hearing, the one the writer may be treating as a side note. Look for
   it in the brief and log, then ask for it directly.
2. **Interrogate the bigger context**, with a receipt: why now, who carries the
   cost, who benefits, what repeats, and what power or incentive keeps the
   problem in place.
3. **Challenge the premise.** At least one prompt names where the piece may
   fail or asks what evidence would falsify it.

Rules for every prompt in the set:

- **A receipt is required.** Each prompt asks for one story, number or
  artifact, written as a line beginning `Receipt:` that names which of the
  three is wanted.
- **Known names, acronyms and episodes go in the brief or setup.** State them
  as facts for the interviewer and the reader. Do not ask the writer to explain
  a reference the audience lacks, and do not spend a prompt on it.
- Each prompt still passes AGENTS.md, "Asking the writer": one ask, an answer
  shape, the writer's words.

Example, with invented material: instead of "Which failure first taught you to
automate the release?", ask "Which one failure changed how you release?" with
`Receipt: the number or artifact showing what changed`, and put who else could
rely on the mechanism and why it matters now into the context prompt. Instead of
"What did the outage reveal?", put the outage in the setup. The premise prompt
might be "Where did turning a failure into a checklist make the process heavier
or hide who decides?"

Before the writer sees the set, run
`python3 scripts/question-check.py --prepared interview-questions.md` and
rewrite what it flags. It checks the count, a receipt per prompt, and the
lede, context and challenge markers. Whether a prompt really finds the lede is
still your judgement.

## Fireside scripts

A fireside script is a prepared set (above) written to read like a warm
conversation. It draws out what the writer thinks and how they react, and it
stays on the writer's side. Use it when a set is written ahead of the sitting.
It changes nothing in the live interview: one question at a time, "ask up to
three times" on one question, and the cap of three prompts all stay as they are.

**The setting.** `Interview engagement` in the house's `positioning.md`
(House rules) takes `companion`, `fireside` or `deep dive`. Unset, or still
the shipped bracketed placeholder, means fireside. `--engagement` on
`scripts/question-check.py` overrides it for one run.

| Setting | Challenge in prompt 3 | Answer length asked |
|---|---|---|
| companion | "Is there anything that would make you doubt this, even a little?" | 30 to 60 seconds |
| fireside (default) | What a thoughtful person who disagrees would say, then what would change the writer's mind | 1 to 2 minutes |
| deep dive | Adds a tension between two things the writer said (live, never invented), and something observable with a date or number | 2 to 3 minutes |

Every setting keeps a challenge to the premise, so the set still passes the
three jobs above. Even the deepest setting is on the writer's side.

**Changing it mid-sitting.** The writer can say "gentler" or "push me". The
next question moves one step along companion, fireside, deep dive, and stops
at either end (gentler at companion, or push me at deep dive, changes
nothing; say so in a line). Log each change as one line in `notes.md`, such as
`Engagement: fireside to companion, at the writer's word`. Name the switch
in the opening of every script so the writer knows it is there.

**The arc.** Three prompts, in this order:

1. **Where the hard part goes.** The bigger context: why now, who carries the
   cost, who benefits. This is also where the buried lede is hunted. Move:
   follow the value.
2. **One real case.** A single story, number or artifact from the writer's
   own files. Move: the specific case.
3. **The fair critic.** The challenge to the premise, voiced by an imagined
   thoughtful person, never as your verdict. Move: the strongest opposing
   case. At deep dive it also carries a tension between two things the writer
   said, and asks what they would tell a friend to do on Monday.

**The shape of a prompt.** Visible to the writer, in this order:

- **What I'm hearing (my guess):** the idea restated in the writer's own
  words, labelled as your guess so they can correct it.
- **Question:** one question, one ask.
- **How to answer:** the length for the setting, the kind of example wanted,
  and a way out ("rough is fine", "you can pass").
- **Held, how it works:** a follow-up toward how the thing works. Held back
  until the writer wants it, phrased as an invitation.
- **Held, another angle:** a second follow-up from a different angle, also an
  invitation. Fireside and deep dive carry both; companion carries one or two.

Hidden from the writer, in a comment on the line below:
`<!-- move: ... | job: ... | receipt: story, number or artifact | level: 1 to 3 -->`.
Move names the technique. Job says which of the three jobs above the prompt
does (buried lede, bigger context, challenge the premise). Level is how hard
the ask is at this setting, 1 gentlest. At deep dive, prompt 3's comment also
carries `tension: live, <file the two statements come from>`, and no quoted
words. If no two statements exist yet, bracket it as `[NEEDS SOURCE: ...]`
and leave the tension out of the visible text.

**What warm means here.** Listening, fairness and permission. It does not
mean praise.

- Plain words. Aim for reading ease of 60 or more on what the writer sees.
  Internal terms (receipt, premise, mechanism, steelman, falsifier and the
  like) stay in the comment.
- Start from what the writer said, or your labelled guess, before any
  challenge.
- Give the opposing case to an imagined person. Never "I think you are wrong".
- No praise or hype, and no accusing phrasing ("why didn't you", "against
  you").
- Names, episodes and numbers come from the writer's files, or are bracketed
  as missing. A quote from a real person needs a source line; anything else is
  labelled as a position being constructed.
- No draft comes out of the answers. Log them verbatim in `notes.md`, reactions
  included, under Spark candidates.

**A worked example, with invented material.** The idea: small teams that drop
the weekly status meeting. Setting: fireside.

```
A relaxed set of three questions, at your pace. Say "gentler" or "push me" at any point and I will move the next question one step.

1. **What I'm hearing (my guess):** Small teams that drop the weekly status meeting keep track of the work. They lose the habit of looking busy together.
   **Question:** Where does the work show up now, if it isn't in the meeting?
   **How to answer:** About 1 to 2 minutes. Name a place, a person or a tool. Rough is fine, and you can pass.
   **Held, how it works:** If you'd like, walk me through a Monday now.
   **Held, another angle:** If it helps, say who misses the meeting most.
   <!-- move: follow the value | job: buried lede, bigger context (why now, who benefits) | receipt: artifact | level: 1 -->
2. **What I'm hearing (my guess):** One team tried it and it worked, and you think trust was the reason.
   **Question:** Which one week shows the change best?
   **How to answer:** About 1 to 2 minutes. Give one real week, with a date or a number if you have one. Rough is fine, or pass.
   **Held, how it works:** If you'd like, walk me through a Monday now.
   **Held, another angle:** If it helps, say who misses the meeting most.
   <!-- move: the specific case | job: one real case | receipt: story | level: 2 -->
3. **What I'm hearing (my guess):** You think the meeting mostly served the manager, and the team can do without it.
   **Question:** Picture a thoughtful person who disagrees. What is the best thing they would say?
   **How to answer:** About 1 to 2 minutes. Then say what would change your mind. Short is fine, and you can pass.
   **Held, how it works:** If you'd like, walk me through a Monday now.
   **Held, another angle:** If it helps, say who misses the meeting most.
   <!-- move: the strongest opposing case | job: challenge the premise | receipt: number | level: 3 -->
```

At companion, prompt 3's question is the gentle doubt question and the length
is 30 to 60 seconds. At deep dive, prompt 3 adds the tension and something
observable, and asks for 2 to 3 minutes.

Before the writer sees the script, run
`python3 scripts/question-check.py --warm interview-questions.md` (add
`--engagement <setting>` to override the house). It runs every check
`--prepared` runs, and flags by name: `hard-to-read`, `jargon`, `no-way-out`,
`no-switch`, `no-listening`, `verdict-voice`, `praise`, `accusing`,
`follow-ups`, `not-invitation`, `no-comment`, `wrong-length`,
`no-gentle-doubt`, `no-fair-critic`, `no-mind-change`, `no-tension`,
`tension-quote` and `no-observable`. Reading ease is computed on the visible
text only. The receipt marker may sit in the comment or on its own
`Receipt:` line. Rewrite what it flags; do not soften it.

## Exit

When you have enough, stop interviewing and summarise in notes.md:

```
## Working thesis
One sentence.

## Languages
Primary: <which theme from positioning.md drives the piece>
Secondary: <which others are involved>
Intersection: <one sentence naming where they cross>

## Stakes
Who this serves, what changes for them.

## Evidence
Bulleted list: each item with source/link status (have / needs finding).

## Open questions
Anything unresolved, phrased as questions for the writer.

## Spark candidates
Lines or phrases they said worth building around.
```

Then ask one final question, as a pick: "Does the thesis sentence sound like
what you mean? A: yes. B: close, and I'll say what's off. C: no."
Do not proceed to outlining unless asked. The human decides when to move stages.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.
