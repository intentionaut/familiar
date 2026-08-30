# Pieces

One folder per piece. Stages create their own files.

```
pieces/YYYY-MM-DD-slug/
├── brief.md                  # /case-study output (optional first step)
├── interview-questions.md    # /case-study output
├── notes.md                  # /interview output
├── outline.md                # /outline output, chosen structure marked
├── draft.md                  # /draft output
├── edits/
│   ├── dev-edit-report.md    # /dev-edit output
│   └── line-edit-report.md   # /line-edit output
├── social.md                 # /social output (pool, picks, schedule, result)
└── SESSION-CONTEXT.md        # every stage appends here on exit; read it on resume
```

`scripts/board.py` reads these folders and writes `.board/` beside them: a
board of every piece by stage, and a page per piece for picking one back up.
Both are generated and ignored by git.

Piece folders are ignored by git. This repo is the tool; the writing stays with
you. Back the folder up the way you back up anything else you would mind losing.
