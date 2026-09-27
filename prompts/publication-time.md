# Stage: publication-time

For newsletters and articles only. This stage chooses a manual publication
window; it does not schedule, publish or send. Feed posts, replies and weekend
social engagement remain outside this stage and keep their own cadence.

Read the finished piece, its `draft.md` frontmatter and the channel id declared
in `knowledge/channels.md`. Read `knowledge/publication-windows.md` from the
writer's own knowledge folder. If the channel's row is missing or still a
placeholder, ask for the writer's window instead of inventing one.

For a filled row, find the next valid future time from the current clock using
its IANA timezone, allowed weekdays, local window and exceptions. Show the
weekday, full date, local time and UTC offset; verify daylight-saving changes.
The draft's proposed `date:` is not proof the piece was published. If the
writer requests a time outside the window, ask whether to keep that exception
or use the next window. Do not move their requested date silently.

On the writer's choice, record channel id, chosen local timestamp and offset,
any exception, and status `held for manual publication` in
`publication-time.md` inside the private piece folder. This is a reminder for
the writer, not a platform queue or permission to publish. Keep the piece at
the publication gate. If the time passes or the piece changes, offer a new
window and ask before updating the record. Never mark it sent from this hold.

Record actual publication and engagement separately from the proposed time.
After several comparable items, propose a default-window change with evidence;
only the writer updates `knowledge/publication-windows.md`.
