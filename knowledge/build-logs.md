# Build logs

A build log is where the material for writing about your work comes from. It
records what shipped, what was decided, what went wrong and what it cost, while
you still remember. The `case-study` stage reads one and turns it into a brief
and a set of interview questions.

Run `familiar log` to see every project and which ones are keeping one.

## Settings

- Projects live in: ~/Projects
- Cross-project log: [path, or "none"]

## Cross-project days

Some days span five repos, and no single project log holds them. A per-project
log splits that day into five accounts, none of which says what the day was.

For those, keep one cross-project log: same rules as any other (dated, newest at
the bottom, append-only, record don't dramatise), but grouped by project under a
single date and written as the view from above. Per-project logs still own the
detail; this one owns the shape.

Only worth starting once you regularly work across repos in a day. Below that it
is just a second place to forget to write in.

## Watched

Projects where `familiar log add` has installed the hooks. One line each, the
project folder then the name of its log file, both in backticks. The hook reads
this to find the right file, so a log called anything at all is found.

Edit by hand if you move a project or rename its log.

**A log can live outside the project it describes.** Record a path rather than
a filename and every reader follows it, including the hook. That is the answer
for a public repository, where a candid log holding defect notes and plan of
record cannot be committed, and gitignoring it leaves exactly one copy on one
disk:

```
familiar log move <project> ~/wherever/your/notes/live
```

It moves the file, rewrites the line here, and leaves the hooks alone, because
the hooks read this file.

<!-- familiar log add appends below this line -->

