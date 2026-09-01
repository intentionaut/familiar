# Reflection

Familiar can ask you two questions every so often and write down what you say,
word for word. The answers are the raw material the drafting stages read, and
they are the reason a draft sounds like you rather than like a description of
you.

It is off until you turn it on. Replace the bracketed values.

## Settings

- Reflection: [on / off]
- Cadence: [weekly / fortnightly / monthly]
- Reflections live in: ~/Projects/reflections

**Cadence is a floor, not an alarm.** It is how long has to pass before Familiar
will offer a reflection at the end of a stage. You can always run
`familiar reflect` yourself, and a missed one is fine.

**Off means off.** No offer at the end of a stage, no notification, no mention.

## How the answers are stored

One file per project in the folder above, named after the project, plus a
`threads.md` for ideas you are developing across all of them. Every entry gets a
`## YYYY-MM-DD` heading, newest at the bottom, appended and never edited.

Keep that folder private. These answers are candid by design.

### Never write reflections into a public repo

Check a repository's visibility before putting a reflections file in it. These
answers say how the work feels, what is worrying you, what you are avoiding and
who the work is actually for. That is fine in a private repo and a mistake in a
public one, especially if you are job hunting or working in the open.

If the project repo is public, keep the file in the private reflections folder
and symlink it into the project, so the tooling still finds it while the content
stays out of that history:

```sh
ln -s ../reflections/<project>.md <project>/REFLECTIONS.md
```

Add `REFLECTIONS.md` to that project's `.gitignore` as well. The symlink is a
convenience; the `.gitignore` line is the thing actually protecting you.

Ask rather than assume. A wrong guess here is permanent and indexed.

## Finding themes

A single entry is a mood. The value is in the sequence, and it only appears when
you read the whole file at once rather than entry by entry. Look for:

- **What recurred.** A worry raised three times is a real one. An idea mentioned
  repeatedly before it got built is the thread worth pulling.
- **What resolved**, and what stopped being mentioned without ever resolving.
  The second is usually more interesting, because nobody notices dropping it.
- **Where an answer contradicts an earlier one.** This is where a view actually
  changed, and it is the hardest thing to see about yourself. Quote both sides.

Contradictions are usually the most interesting thing in the file. Surface them
as a question, not as a correction.

## The questions

Two per reflection, one at a time, never two of the same kind. Edit this list,
add your own, delete the ones that do nothing for you. The stage will not repeat
a question, or a close paraphrase, that appears in your last three entries.

### Feel and noticing

- What surprised you this week?
- What are you noticing about how this is going?
- What went better than it had any right to?
- What is true now that would have surprised you a month ago?

### Worry and risk

- What is worrying you about the project right now?
- What decision this week are you least sure about?
- What did we get wrong that you have not spotted?
- Where did you spend time you will regret in a month?

### Direction and purpose

- What do you want to be true about this in three months?
- Has anything changed your mind about what this is for?
- Who is this actually for, and has that answer moved?
- What would have to be true for you to stop working on this?

### Work and craft

- What is the most useful thing that happened, and why that one?
- What did you cut, and do you still think that was right?
- What got easier that used to be hard, and what does that free you up to do?
- Where are you polishing something that does not matter yet?
- What did you learn this week that changes what you build next?

### Honesty and avoidance

- What are you avoiding?
- What are you pretending to have decided that you actually have not?
- What is the thing you keep meaning to do and have not?
- Which part of this would you least want to hand to someone else?

### Users

- What did someone using this do that you did not expect?
- What would you tell someone starting this from scratch?
