# Links and tracking

Where a post's link points, and how you know it worked. The `publish` stage
reads this to build every URL it puts in a post, before it counts characters.

Fill it in once. If you do not track anything, set the convention to `none` and
`publish` uses your URLs unchanged.

## The convention

- **convention:** utm
- **source** (`utm_source`): the hostname of the place the click came from, so
  `linkedin.com`, `bsky.app`, `github.com`. Not a nickname, and not the name of
  a campaign. One property, one spelling, forever.
- **medium** (`utm_medium`): the kind of placement. `social` for a feed post,
  `newsletter` for an issue, `profile` for a bio link, `readme` for a repo.
- **campaign** (`utm_campaign`): what is being promoted. Usually the piece's
  slug, so every post about one piece reports together.

A worked example, for a feed post on LinkedIn about a piece slugged
`taking-a-spell`:

```
?utm_source=linkedin.com&utm_medium=social&utm_campaign=taking-a-spell
```

## Destinations

Where posts point when the prompt says "the piece" or "the index".

| Name | URL |
|------|-----|
| piece | [https://example.com/writing/<slug>/] |
| index | [https://example.com/writing/] |
| subscribe | [https://example.com/subscribe/] |

## Rules `publish` follows

1. Build the URL, append the parameters, **then** count the post. A link adds
   between 40 and 90 characters and it is the reason approved copy fails a
   limit check.
2. On an over-limit post, stop and report the count and the overage. Never
   truncate, and never edit the writer's words to make room.
3. Shortening the tracking parameters is the one shortening `publish` may
   propose, because the writer did not write them. Dropping to `utm_source`
   alone is the usual fix on a 300-character channel. Say what is lost: the
   click still attributes to the channel, but not to the piece.
4. A URL that does not resolve yet is not a URL. If a piece has not published,
   keep the placeholder and say the schedule cannot complete until it does, or
   point at the index instead.
