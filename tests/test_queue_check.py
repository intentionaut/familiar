"""Unit tests for the queue check's parsing and date maths.

Both have already shipped bugs: the scheduler flag was read out of the prose
that explains it, and the scheduler was asked for `status` as a string when it
requires an array. Neither needs a network to catch.
"""
import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("qc", ROOT / "scripts" / "queue-check.py")
qc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qc)

FILLED = """# Social schedule
## Scheduler
- **scheduler:** buffer
- **key:** `$BUFFER_API_KEY`

| Channel | Channel id | Limit | Link goes |
|---------|-----------|-------|-----------|
| linkedin | 6a91b471ccaf649a673455a5 | 3000 | pinned first comment |
| bluesky | abc123def456abc123def456 | 300 | inline |

## Cadence

| Channel | Days | Count | Default time | Timezone |
|---------|------|-------|--------------|----------|
| LinkedIn | Mon, Wed, Fri | 3/week | 08:30 | Europe/London |
| Bluesky | Tue, Wed, Thu | 3/week | 12:30 | Europe/London |
"""


def write(text):
    d = Path(tempfile.mkdtemp())
    p = d / "social-schedule.md"
    p.write_text(text)
    return p


class Parsing(unittest.TestCase):
    def test_filled_config_yields_ids_and_cadence(self):
        scheduler, ids, cadence = qc.parse(write(FILLED))
        self.assertEqual("buffer", scheduler)
        self.assertEqual("6a91b471ccaf649a673455a5", ids["linkedin"])
        self.assertEqual(["Mon", "Wed", "Fri"], cadence["linkedin"])
        self.assertEqual(["Tue", "Wed", "Thu"], cadence["bluesky"])

    def test_scheduler_none_turns_the_feature_off(self):
        off = FILLED.replace("**scheduler:** buffer", "**scheduler:** none")
        self.assertEqual("none", qc.parse(write(off))[0])

    def test_prose_about_the_flag_is_not_read_as_the_flag(self):
        """The shipped block explains `scheduler: none` in its own prose. An
        unanchored search matched that sentence instead of the setting, and
        reported the feature off on a config that had it on."""
        prose = FILLED.replace(
            "## Scheduler",
            "## Scheduler\n\nOptional. Set `scheduler: none`, or delete this block,\n"
            "and publish prints a table instead.\n")
        self.assertEqual("buffer", qc.parse(write(prose))[0])

    def test_placeholder_ids_are_not_treated_as_configured(self):
        """The shipped template carries bracketed placeholders. Treating one as
        a real channel id would send a post nowhere."""
        template = ROOT / "knowledge" / "social-schedule.md"
        scheduler, ids, cadence = qc.parse(template)
        self.assertEqual("buffer", scheduler, "the template should ship ready to use")
        self.assertEqual({}, ids, "bracketed placeholders must not parse as ids")
        self.assertTrue(cadence, "the template's example cadence should still parse")

    def test_table_headers_and_separators_are_skipped(self):
        rows = list(qc.rows(qc.section(FILLED, "Scheduler")))
        self.assertEqual(2, len(rows))
        self.assertEqual("linkedin", rows[0][0])


class Dates(unittest.TestCase):
    def test_next_monday_from_midweek(self):
        self.assertEqual(dt.date(2026, 9, 7),
                         qc.next_monday(dt.date(2026, 9, 2)))

    def test_next_monday_from_a_monday_is_the_following_one(self):
        """Asked on a Monday, the 'coming week' is the next one, not today."""
        self.assertEqual(dt.date(2026, 9, 7),
                         qc.next_monday(dt.date(2026, 8, 31)))

    def test_next_monday_from_a_sunday(self):
        self.assertEqual(dt.date(2026, 9, 7),
                         qc.next_monday(dt.date(2026, 9, 6)))

    def test_month_end_does_not_roll_the_month(self):
        """A date built from the 31st must not overflow into the month after
        next. This is the shape of bug that put a September event in October."""
        self.assertEqual(dt.date(2026, 9, 7),
                         qc.next_monday(dt.date(2026, 8, 31)))


class Request(unittest.TestCase):
    def test_status_is_sent_as_an_array(self):
        """The scheduler rejects a bare string with a validation error, which
        made the check report 'could not check' on every single run."""
        call = json.loads(qc.list_request("6a91b471ccaf649a673455a5").splitlines()[-1])
        args = call["params"]["arguments"]
        self.assertIsInstance(args["status"], list)
        self.assertEqual(["scheduled"], args["status"])

    def test_request_names_the_channel_asked_for(self):
        """Channels are sent as a list, and the organisation id travels with
        them, because a listing without it is refused."""
        call = json.loads(qc.list_request("abc", "org1").splitlines()[-1])
        args = call["params"]["arguments"]
        self.assertEqual(["abc"], args["channelIds"])
        self.assertEqual("org1", args["organizationId"])


class Responses(unittest.TestCase):
    """The scheduler's answers, and the two ways reading them has gone wrong:
    a validation error searched for slot dates and read as 'every slot empty',
    and a UTC due time compared against a local calendar day."""

    def test_error_response_is_not_a_listing(self):
        self.assertIsNone(qc.tool_payload({"jsonrpc": "2.0", "id": 11,
                                           "error": {"message": "organizationId required"}}))

    def test_connection_shape_yields_posts(self):
        payload = {"edges": [{"node": {"id": "p1", "dueAt": "2026-09-07T07:30:00Z"}}]}
        self.assertEqual(["p1"], [p["id"] for p in qc.posts_of(payload)])

    def test_plain_list_still_yields_posts(self):
        self.assertEqual(2, len(qc.posts_of([{"id": "a"}, {"id": "b"}])))

    def test_due_times_land_on_the_local_day(self):
        """23:30 in London on Monday is 22:30Z; 00:30 London on Tuesday is
        23:30Z Monday. Only the local conversion puts them on the right day."""
        posts = [{"dueAt": "2026-09-07T22:30:00Z"}, {"dueAt": "2026-09-07T23:30:00Z"}]
        got = qc.local_dates(posts, "Europe/London")
        self.assertEqual({dt.date(2026, 9, 7), dt.date(2026, 9, 8)}, got)

    def test_organisation_id_is_found_wherever_it_sits(self):
        self.assertEqual("0123456789abcdef01234567", qc.organization_id(
            {"account": {"organizations": [{"id": "0123456789abcdef01234567", "name": "x"}]}}))
        self.assertIsNone(qc.organization_id({"organizations": []}))

    def test_timezone_comes_from_the_cadence_table(self):
        self.assertEqual("Europe/London", qc.timezone_of(FILLED))
        header_only = FILLED.replace("| Default time | Timezone |", "| Default time (Europe/Berlin) |") \
                            .replace("| 08:30 | Europe/London |", "| 08:30 |") \
                            .replace("| 12:30 | Europe/London |", "| 12:30 |")
        self.assertEqual("Europe/Berlin", qc.timezone_of(header_only))


if __name__ == "__main__":
    unittest.main()


_dspec = importlib.util.spec_from_file_location("doc", ROOT / "scripts" / "doctor.py")
doc = importlib.util.module_from_spec(_dspec)
_dspec.loader.exec_module(doc)


class DoctorState(unittest.TestCase):
    """A bracket is only a blank if the shipped template has the same one."""

    def test_untouched_template_reads_as_a_template(self):
        shipped = ROOT / "knowledge" / "voice-guide.md"
        st, n = doc.state(shipped, shipped)
        self.assertEqual(doc.TEMPLATE, st)
        self.assertGreater(n, 0)

    def test_the_writers_own_brackets_are_not_blanks(self):
        """A voice guide banning 'as a [senior title]' framing is finished, not
        unfilled. Counting that bracket told a writer with a complete voice
        guide that Familiar did not know their voice."""
        shipped = ROOT / "knowledge" / "voice-guide.md"
        filled = write('# Voice guide\n\nNo "as a [senior title]" framing, ever.\n')
        st, n = doc.state(filled, shipped)
        self.assertEqual(doc.OK, st, f"counted the writer's own prose as {n} blank(s)")

    def test_absent_file_is_reported_as_absent_not_empty(self):
        st, n = doc.state(Path(tempfile.mkdtemp()) / "nope.md",
                          ROOT / "knowledge" / "voice-guide.md")
        self.assertEqual(doc.MISSING, st)

    def test_shipped_templates_resolve_when_nothing_is_configured(self):
        cfg, whose = doc.config_dir()
        self.assertTrue(cfg.is_dir())
        self.assertIn(whose, ("yours", "the shipped templates"))
