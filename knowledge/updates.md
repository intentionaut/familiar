# Updates

Whether `familiar doctor` may check for a newer Familiar. Off until you turn it
on, and the template counts as off.

## Settings

- Update check: [on / off]

## What it does when on

Once a day at most, `doctor` fetches the release page at
familiar.intentionaut.com and compares the newest version there with the one in
this clone. It prints one line and stops:

- a newer version exists, and how to update (`git pull`), or
- this clone is current, or
- `unknown`, because the page could not be reached. Unknown is never reported
  as "current".

It never updates anything itself, never blocks a command, and never runs from
any other stage or script. The day's answer is kept under `~/.familiar/` so a
second `doctor` the same day does not fetch again.

Installed as a plugin rather than a clone? Your agent's plugin manager owns
updates; this check is for clones.
