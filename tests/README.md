# Tests

Run them:

```sh
python3 -m unittest discover -s tests -t .
```

Standard library only. No install, no network, no key, no model. The whole
suite runs in well under a second, and it runs in CI on every push.

## What is here, and why

**`test_structure.py`** checks the repo holds together: every command has a
prompt, every prompt has a command, the installer picks up every adapter, and
nothing references a prompt, knowledge file or script that does not exist. It
also holds Familiar to its own first style rule and fails on an em dash in
shipped prose.

**`test_queue_check.py`** covers the parsing and date maths in
`scripts/queue-check.py`, the only script with real logic in it.

## What is deliberately not here

No prompt evals. Familiar's prompts are prose, and testing prose against a
model is slow, expensive and answers a question nobody was asking. These tests
exist to stop obvious mistakes reaching someone's clone, not to grade writing.

## Every test here earned its place

Each one is a bug that actually shipped or was caught on the way out:

- **`repurpose` shipped with no command.** The installer worked from a
  hardcoded stage list and silently skipped a stage added later.
- **The queue check asked for `status` as a string** where the scheduler wants
  an array, so it would have reported "could not check" on every run.
- **The scheduler flag was read out of the prose explaining it.** The config
  block documents `scheduler: none`, and an unanchored search matched that
  sentence instead of the setting.
- **Em dashes reached shipped prose**, in a repo whose first style rule bans
  them.

If you fix a bug here, leave a test behind. That is the whole policy.
