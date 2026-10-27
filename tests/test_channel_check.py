"""The channel registry check, on synthetic fixtures.

The four failures it exists to catch: an unknown channel, a missing
destination, two destinations on one post, and the registry contradicting
the schedule. Public repo rule: fixtures are invented, never a writer's
files.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import channel_check  # noqa: E402

REGISTRY = """# Channels

## Channel: feed-one

- **Job:** Reach and discovery.
- **Schedule name:** FeedOne
- **Voice overlay:** The short-form register.
- **Form and length:** Original posts. About 1,300 characters, 3,000 hard.
- **Cadence:** 3 original posts a week.
- **Source material:** Shipped pieces.
- **Default CTA and destination:** One destination per post.
- **Link placement:** First comment.
- **utm:** source `feedone.example.com`, medium `social`.
- **Relationships:** Companion to newsletter-one.
- **Review and publish gate:** The social gates, then publish.

## Channel: feed-two

- **Job:** A second channel with no destination rule.
- **Review and publish gate:** The writer's review.
"""

SCHEDULE_OK = """# Social schedule

## Channels

| Channel | Account | Voice | Limit | Scheduler |
|---------|---------|-------|-------|-----------|
| FeedOne | @writer | first person | 3000 | Buffer |

## Cadence

| Channel | Days | Count | Default time | Timezone |
|---------|------|-------|--------------|----------|
| FeedOne | Mon, Wed, Fri | 3/week | 08:30 | Europe/London |

## Scheduler

| Channel | Channel id | Limit | Link goes |
|---------|-----------|-------|-----------|
| FeedOne | abc123 | 3000 | pinned first comment |
"""

LINKS = """# Links and tracking

## Destinations

| Name | URL |
|------|-----|
| piece | https://example.com/writing/<slug>/ |
| index | https://example.com/writing/ |
"""


def write(folder, name, text):
    path = Path(folder) / name
    path.write_text(text)
    return path


class ChannelCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self.tmp.name)
        write(self.cfg, "channels.md", REGISTRY)
        write(self.cfg, "links.md", LINKS)

    def tearDown(self):
        self.tmp.cleanup()

    def problems(self):
        # An empty pieces folder of its own: left to resolve, check() reads the
        # writer's real pieces (FAMILIAR_PIECES or .familiar) and fails on them.
        pieces = self.cfg / "pieces"
        pieces.mkdir(exist_ok=True)
        return channel_check.check(self.cfg, [pieces])

    def test_a_consistent_house_passes(self):
        write(self.cfg, "social-schedule.md", SCHEDULE_OK)
        problems, warnings = self.problems()
        problems = [p for p in problems if "feed-two" not in p]
        self.assertEqual([], problems)
        self.assertEqual([], warnings)

    def test_an_unconfigured_house_is_quiet(self):
        (self.cfg / "channels.md").unlink()
        self.assertEqual(([], []), self.problems())

    def test_a_channel_block_needs_a_destination_rule(self):
        problems, _ = self.problems()
        self.assertTrue(any("feed-two" in p and "destination" in p
                            for p in problems))

    def test_an_unknown_channel_in_the_schedule_is_flagged(self):
        write(self.cfg, "social-schedule.md",
              SCHEDULE_OK + "| FeedNine | @writer | first person | 500 | Buffer |\n")
        problems, _ = self.problems()
        self.assertTrue(any("FeedNine" in p and "not declared" in p
                            for p in problems))

    def test_a_cadence_contradiction_is_flagged(self):
        write(self.cfg, "social-schedule.md",
              SCHEDULE_OK.replace("3/week", "5/week"))
        problems, _ = self.problems()
        self.assertTrue(any("cadence" in p for p in problems))

    def test_a_limit_contradiction_is_flagged(self):
        write(self.cfg, "social-schedule.md",
              SCHEDULE_OK.replace("| abc123 | 3000 |", "| abc123 | 2800 |"))
        problems, _ = self.problems()
        self.assertTrue(any("limit" in p for p in problems))

    def test_a_non_hostname_utm_source_is_a_warning(self):
        write(self.cfg, "channels.md",
              REGISTRY.replace("source `feedone.example.com`",
                               "source `feedone_feed`"))
        _, warnings = self.problems()
        self.assertTrue(any("hostname" in w for w in warnings))

    def _piece(self, social_md):
        pieces = self.cfg / "pieces"
        piece = pieces / "2026-09-19-example"
        piece.mkdir(parents=True)
        (piece / "social.md").write_text(social_md)
        return [str(pieces)]

    SOCIAL_OK = """# Social: an example

## Chosen

### C1 · feed-one · pillar
channel: feed-one
destination: piece
The full post text.

## Held

### C2 · feed-nine · quote
channel: feed-nine
destination: index
Held copy is never input.
"""

    def test_chosen_posts_check_out_and_held_is_ignored(self):
        write(self.cfg, "social-schedule.md", SCHEDULE_OK)
        extra = self._piece(self.SOCIAL_OK)
        problems, _ = channel_check.check(self.cfg, extra)
        problems = [p for p in problems if "feed-two" not in p]
        self.assertEqual([], problems)

    def test_an_unknown_channel_in_a_post_is_flagged(self):
        extra = self._piece(self.SOCIAL_OK.replace("channel: feed-one",
                                                   "channel: feed-nine"))
        problems, _ = channel_check.check(self.cfg, extra)
        self.assertTrue(any("feed-nine" in p and "not declared" in p
                            for p in problems))

    def test_a_post_without_a_destination_is_flagged(self):
        extra = self._piece(self.SOCIAL_OK.replace("destination: piece\n", ""))
        problems, _ = channel_check.check(self.cfg, extra)
        self.assertTrue(any("no destination" in p for p in problems))

    def test_two_destinations_on_one_post_are_flagged(self):
        extra = self._piece(self.SOCIAL_OK.replace(
            "destination: piece\n", "destination: piece\ndestination: index\n"))
        problems, _ = channel_check.check(self.cfg, extra)
        self.assertTrue(any("2 destinations" in p for p in problems))

    def test_one_line_naming_two_destinations_is_flagged(self):
        extra = self._piece(self.SOCIAL_OK.replace(
            "destination: piece\n", "destination: the piece and the index\n"))
        problems, _ = channel_check.check(self.cfg, extra)
        self.assertTrue(any("one place" in p for p in problems))


SHIPPED = ROOT / "knowledge" / "channels.md"

SHIPPED_SCHEDULE = """# Social schedule

## Channels

| Channel | Account | Voice | Limit | Scheduler |
|---------|---------|-------|-------|-----------|
| LinkedIn | @writer | first person | 3000 | Buffer |
| Bluesky | @writer | first person | 300 | Buffer |

## Scheduler

| Channel | Channel id | Limit | Link goes |
|---------|-----------|-------|-----------|
| linkedin | abc123 | 3000 | pinned first comment |
| bluesky | def456 | 300 | inline |
"""


class ShippedRegistry(unittest.TestCase):
    """The template registry and the sample schedule agree on `linkedin`
    and `bluesky`; the retired `linkedin-feed` id is an unknown channel."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self.tmp.name)
        write(self.cfg, "channels.md", SHIPPED.read_text())
        write(self.cfg, "links.md", LINKS)
        write(self.cfg, "social-schedule.md", SHIPPED_SCHEDULE)
        self.pieces = self.cfg / "pieces"
        self.pieces.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def piece(self, channel):
        d = self.pieces / "2026-01-01-example"
        d.mkdir(exist_ok=True)
        (d / "social.md").write_text(
            f"# Social\n\n## Chosen\n\n### C1\nchannel: {channel}\n"
            f"destination: piece\nText.\n")

    def test_ids_are_linkedin_and_bluesky(self):
        ids = set(channel_check.parse_registry(self.cfg / "channels.md"))
        self.assertIn("linkedin", ids)
        self.assertIn("bluesky", ids)
        self.assertNotIn("linkedin-feed", ids)

    def test_linkedin_and_bluesky_pass_against_the_sample_schedule(self):
        for cid in ("linkedin", "bluesky"):
            self.piece(cid)
            problems, _ = channel_check.check(self.cfg, [self.pieces])
            self.assertEqual([], problems, cid)

    def test_the_old_linkedin_feed_id_is_flagged_as_undeclared(self):
        self.piece("linkedin-feed")
        problems, _ = channel_check.check(self.cfg, [self.pieces])
        self.assertTrue(any("linkedin-feed" in p and "not declared" in p
                            for p in problems), problems)

    def test_an_old_id_in_the_schedule_is_flagged_too(self):
        write(self.cfg, "social-schedule.md", SHIPPED_SCHEDULE.replace(
            "| linkedin | abc123 |", "| linkedin-feed | abc123 |"))
        problems, _ = channel_check.check(self.cfg, [self.pieces])
        self.assertTrue(any("linkedin-feed" in p and "not declared" in p
                            for p in problems), problems)

    def test_a_limit_contradiction_is_caught_under_the_id_spelling(self):
        write(self.cfg, "social-schedule.md", SHIPPED_SCHEDULE.replace(
            "| bluesky | def456 | 300 |", "| bluesky | def456 | 500 |"))
        problems, _ = channel_check.check(self.cfg, [self.pieces])
        self.assertTrue(any("bluesky" in p and "limit" in p
                            for p in problems), problems)

    def test_a_wrapped_field_is_read_whole(self):
        reg = channel_check.parse_registry(self.cfg / "channels.md")
        self.assertIn("3,000 hard", reg["linkedin"]["Form and length"])

    def test_the_bluesky_block_declares_the_required_fields(self):
        reg = channel_check.parse_registry(self.cfg / "channels.md")
        for req in channel_check.REQUIRED:
            self.assertTrue(reg["bluesky"].get(req), req)
        self.assertIn("300", reg["bluesky"]["Form and length"])


if __name__ == "__main__":
    unittest.main()
