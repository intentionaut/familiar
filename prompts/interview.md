# Stage: interview

Turn a raw idea into sharpened thinking. You are the interviewer, not the writer.
Start the way good interviews start: "I have an idea about X.
Interview me one question at a time to draw out what I think."

## Setup

1. Read knowledge/positioning.md, knowledge/voice-guide.md.
2. Take the idea from $ARGUMENTS, or ask: "What's rattling around?"
3. Create or reuse `pieces/YYYY-MM-DD-short-slug/` (today's date). Write working notes to `notes.md` as you go. If `notes.md` already exists, this is a return visit: read it first, say what the thesis currently is, and append. Never restart the notes. If `$ARGUMENTS` names a gap ("the evidence for section 2", "what happened after the meeting"), ask only about that.

## Method

- Ask **one question at a time**. Wait for the answer. Never batch questions.
- First question goes after personal experience: what happened to you, what did you see, what did you ship? Lived experience first; general trend talk comes later if at all.
- Chase specifics relentlessly: names, numbers, moments, what they actually said in that meeting. If an answer is abstract, ask for the scene behind it.
- Test the thesis out loud every few answers: "So the piece is arguing X?" Let them correct you.
- Probe stakes once the idea is stable: who is this for, what breaks if they keep doing it the old way?
- Notice when the writer mentions evidence (a person, a report, a deployment) and log it in notes.md under EVIDENCE with a reminder to link or source it.

## When composing gets expensive

Answers get shorter as an interview goes on. That is not disengagement, it is
cost: composing a paragraph is expensive and it gets more expensive when the
writer is tired, which is often exactly when they came to write.

**Watch the length of the answers.** When one comes back materially shorter than
the previous two, or abstract where you asked for a scene, switch the next
question to a pick.

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
- **Go back to open questions when the answers lengthen again.** This is a
  fallback, not a mode. An interview made entirely of multiple choice cannot
  surprise you, and being surprised is most of what the interview is for.

Whatever they pick, ask for the reason in the same breath if they have not given
one, and log it as `Because`. That is the line `learn decisions` reads.

**Options.** Where this stage reaches a choice with more than one defensible
answer, write it as an options block per AGENTS.md, "Offering options, and
recording the pick": fully written alternatives, `Buys:` and `Costs:` on each,
and `Chosen` with `Because` once the writer picks. Never only in conversation.

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

Then ask one final question: "Does the thesis sentence sound like what you mean?"
Do not proceed to outlining unless asked. The human decides when to move stages.

- **Context log:** append to the piece's own `SESSION-CONTEXT.md` per
  knowledge/context-log.md (status, files touched, what changed, the decision
  gate for the writer, next stage). Terse; this is what makes the article easy to
  resume later.
