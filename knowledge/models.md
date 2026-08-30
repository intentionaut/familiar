# Model selection

Familiar is model agnostic. No stage or prompt depends on a specific model or
vendor. Use whatever your terminal is configured with; this file only says
where it is worth spending more or less.

## Principles

- Default to your terminal's current model and keep going.
- Capability over vendor. Any model that honours the stage contract in
  `prompts/*.md` is acceptable.
- If a model errors or stalls, do not retry it indefinitely. Fall back to your
  default and continue.

## Where it matters

| Stage | Spend | Why |
|-------|-------|-----|
| /case-study | more | Long build log, several files; a strong reading tier pays off |
| /interview | more | Turn by turn; must hold a growing transcript and notice what you skipped |
| /outline | more | Reasoning across three structures |
| /draft | most | Prose in your voice. Use the best model you have for a piece you care about |
| /dev-edit | more | Editorial judgement on substance |
| /social | more | Short-form voice is unforgiving; quality matters |
| /line-edit | less | A mechanical checklist pass; a fast, cheap model is fine. Step up if it misses things |

## Overriding

In Claude Code, `/model` before a stage. In opencode, set the model on the
agent or command. Do not write a model name into a prompt body.
