# Engagement

How you want an agent to talk to you, in every project, including the ones
Familiar knows nothing about. `scripts/setup.sh` installs the rule below into
each agent's own memory file, so it is read at the start of every session rather
than only inside a Familiar stage.

## Where it reaches

Three surfaces, and they do not share a mechanism:

| Surface | Reads | Installed by |
|---|---|---|
| Claude Code, opencode, Codex, Gemini CLI | that agent's memory file | `scripts/setup.sh` |
| An ordinary chat, on the web, desktop or a phone | your account's personal-preferences setting | you, by pasting |
| A project or a workspace in one of those accounts | the same setting, plus whatever the project itself says | you |

**The second one is a paste and will stay one.** There is no file behind it and
nothing to write to, so `python3 scripts/engagement.py --copy` puts the rule on
the clipboard and you put it in the box. That is worth doing rather than
retyping, because the value of this file is that there is one of it: a rule that
exists twice is a rule that disagrees with itself the first time you change your
mind.

Off until you turn it on, and the template counts as off. A bracket installed
into a memory file is a placeholder that every session afterwards reads as an
instruction, which is worse than having no rule at all.

## Settings

- Engagement rule: [on / off]

Installed by `scripts/setup.sh`, along with the commands. Installed Familiar as
a plugin or a skill instead, so there is no `setup.sh` to run? Point the
installer at the file yourself, once:

```sh
python3 scripts/engagement.py --install ~/.claude/CLAUDE.md
python3 scripts/engagement.py --check          # where it landed
```

## Writing it

Write it as instructions to the agent, in your own words. This is the one file
whose wording is read back to you in every session, so a paraphrase of what you
meant costs you on every one of them.

Worth covering, because these are the things an agent otherwise decides for you:

- **What kind of colleague you want.** One line. It sets everything else.
- **Length and register.** How long a message should be, and what to leave out.
- **Humour**, if you want any.
- **What to do when you correct a draft.** The whole thing back, or just the
  changed part.
- **What to do when something is not possible.** Say so, or find a way round,
  or both.
- **What it should do without being asked**, and what it should never do without
  asking.

Say what you want, not what you dislike. A rule written as a complaint is a rule
an agent has to invert before it can act on it, and it will sometimes invert it
wrongly.

Everything under `## The rule` is installed, word for word. Nothing above it
is, so this page can explain itself without explaining itself to you every
session.

## The rule

[Your rule goes here. Deleting this bracket is what switches it on.]
