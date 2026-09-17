# The board's look

Optional. Until you set anything here the board uses its own colours and
follows your system's light or dark setting. Put one setting per line, at the
start of the line, and leave out anything you do not want to change.

- `Scheme:` either `light`, which keeps the board light whatever your system is
  set to, or `system`, which follows it. With `system`, your colours are used
  in light mode and the board keeps its own colours in dark mode, because a
  palette chosen for a light page rarely works inverted.
- `Paper:` the page. `Card:` cards and panels. `Ink:` text. `Muted:` quieter
  text. `Line:` borders. `Accent:` panel headings, highlights, and the mark
  beside a passage that has a note. `Warn:` and `Ok:` are the two status
  colours. Any CSS colour works, such as `#f6f4ef` or `rgb(246 244 239)`.
- `Font:` the body text, and `Display font:` titles and headings, each as a
  CSS font list ending in a generic family such as `serif`. A font shows if it
  is installed on this machine or named under `Google fonts:`; otherwise the
  next in the list is used.
- `Google fonts:` families to load from Google Fonts, by name, separated by
  commas, such as `Literata, Inter`. Then name them in `Font:` or
  `Display font:`. Only the regular weight loads unless you ask for more:
  `Literata:wght@400;700` adds bold, where the family has it. Naming one means
  each page fetches it from Google, which tells Google your address and nothing
  else. Leave the line out and the board fetches nothing.
- `Text size:` the size of the draft's text, such as `18px`.

A value that could break the page (a brace, a semicolon) is ignored.

For example, a light page with a green accent:

    Scheme: light
    Paper: #f6f4ef
    Ink: #1f2a2e
    Accent: #2f6b5a
