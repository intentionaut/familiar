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
- Quote reflections in patterns: words

**What that last one does.** `harvest` reads these answers and writes
`knowledge/patterns.md`, and a sentence of yours quoted there is what makes a
topic writable months later. It also moves a private line into your knowledge
folder, which for some people is a synced folder or a repo. `words` quotes you.
`citation only` names the file and the date instead, which gives you weaker
topics and nothing to leak. Absent means `words`.

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

Two per reflection, one at a time, from two different sections below, picked for
the week that actually happened: a shipping week gets a shipping question, a
writing week a writing one, a week of conversations asks about the people. Edit
this list, add your own, delete the ones that do nothing for you. The stage will
not repeat a question, or a close paraphrase, that appears in your last three
entries.

Every question here opens with who, what, when, where or why, and none of them
carries a verdict for you to confirm. A question that already contains a
judgement (what are you avoiding, what did you get wrong) is a review with a
question mark on it. If a week went badly, the answer is where that gets said.

### Who

- Who did this week's work turn out to be for?
- Who were you thinking about while you worked?
- Who would you show this to first, and why them?
- Who helped this week, whether or not they knew it?
- Who did you talk to about the work this week, and what did they hear?
- Who else has this problem, and what do they do about it?
- Who do you want reading this in a year?

### What

- What surprised you this week?
- What are you noticing about how this is going?
- What is true now that was not true a month ago?
- What did you learn this week that changes what you build next?
- What did you cut, and how does that decision look now?
- What is on your mind about the project right now?
- What did you write this week that you would stand behind in a year?
- What did you read or hear this week that stayed with you?
- What did the week show you about how you work?
- What did someone using this do that you did not expect?
- What do you want to be true about this in three months?
- What would you tell someone starting this from scratch?

### When

- When this week did the work feel most like yours?
- When did you last change your mind about something here, and what moved?
- When did the time go faster than you expected, and when slower?
- When did a piece of writing come easily this week, and what was around it?
- When did you stop for the day, and what made that the moment?
- When did you last enjoy this, and what were you doing?
- When will you know this has done what you wanted it to?

### Where

- Where did the work go this week, and where did you expect it to go?
- Where is this easier than it used to be?
- Where does the hard part live now?
- Where did the piece you were writing end up, compared with where it started?
- Where did a reader or a user meet the work this week, and what did they see?
- Where did the week's biggest decision come from: a fact, a hunch, or someone else?
- Where would you like the time to go next week?

### Why

- Why does this project matter to you right now?
- Why did this project get the week's attention rather than another?
- Why did the most useful thing that happened turn out to be that one?
- Why did the week's biggest decision go the way it did?
- Why this piece, this week, for these readers?
- Why now, for the thing you started this week?
- Why did something you expected to be hard turn out otherwise, or the reverse?
