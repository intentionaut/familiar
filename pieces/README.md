# Pieces

One folder per piece. Stages create their own files.

```
pieces/YYYY-MM-DD-slug/
├── source.md                 # /bring input, copied in verbatim and never edited
├── spine.md                  # /bring output: the shape it has, and the claims audit
├── brief.md                  # /bring or /case-study output (optional first step)
├── interview-questions.md    # /bring or /case-study output
├── notes.md                  # /interview output
├── outline.md                # /outline output, chosen structure marked
├── draft.md                  # /draft output
├── edits/
│   ├── dev-edit-report.md    # /dev-edit output
│   └── line-edit-report.md   # /line-edit output
├── cuts.md                   # what any stage cut, and whether it is reusable
├── options.md                # alternatives a stage offered, and which was picked
├── social.md                 # /social output (pool, picks, schedule, result)
├── final.md                  # the record of a send, once the piece has gone out
└── SESSION-CONTEXT.md        # every stage appends here on exit; read it on resume
```

`scripts/board.py` reads these folders and writes `.board/` beside them: a
board of every piece by stage, and a page per piece for picking one back up.
Both are generated and ignored by git.

Piece folders are ignored by git. This repo is the tool; the writing stays with
you. Back the folder up the way you back up anything else you would mind losing.
