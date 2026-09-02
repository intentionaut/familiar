"""Tests for the familiar CLI entry point."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "familiar"


class FamiliarCLI(unittest.TestCase):
    def test_help_exits_cleanly(self):
        result = subprocess.run(
            ["python3", str(CLI), "--help"],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode)
        self.assertIn("familiar", result.stdout)

    def test_new_piece_help(self):
        result = subprocess.run(
            ["python3", str(CLI), "new-piece", "--help"],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode)
        self.assertIn("slug", result.stdout.lower())

    def test_skill_install_help(self):
        result = subprocess.run(
            ["python3", str(CLI), "skill", "install", "--help"],
            capture_output=True, text=True)
        self.assertEqual(0, result.returncode)
        self.assertIn("agent", result.stdout.lower())

    def test_init_creates_config_and_knowledge(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(CLI), "init", "--force"],
                capture_output=True, text=True, cwd=tmp,
                env={**os.environ,
                     "FAMILIAR_KNOWLEDGE": "",
                     "FAMILIAR_CONFIG": "",
                     "FAMILIAR_PIECES": ""})
            self.assertEqual(0, result.returncode,
                             f"init failed: {result.stderr}")
            self.assertTrue((Path(tmp) / ".familiar").is_file())
            self.assertTrue((Path(tmp) / "knowledge").is_dir())
            self.assertTrue((Path(tmp) / "pieces").is_dir())
            # Knowledge files should be copied
            self.assertTrue((Path(tmp) / "knowledge" / "positioning.md").is_file())

    def test_new_piece_scaffolds_correctly(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Set up a minimal .familiar
            pieces_dir = Path(tmp) / "pieces"
            pieces_dir.mkdir()
            knowledge_dir = Path(tmp) / "knowledge"
            knowledge_dir.mkdir()
            (knowledge_dir / "positioning.md").write_text("# test\n")
            (Path(tmp) / ".familiar").write_text(
                f"knowledge = {knowledge_dir}\npieces = {pieces_dir}\n")

            result = subprocess.run(
                ["python3", str(CLI), "new-piece", "test-essay"],
                capture_output=True, text=True, cwd=tmp,
                env={**os.environ,
                     "FAMILIAR_KNOWLEDGE": "",
                     "FAMILIAR_CONFIG": "",
                     "FAMILIAR_PIECES": ""})
            self.assertEqual(0, result.returncode,
                             f"new-piece failed: {result.stderr}")
            # Should create a dated folder
            folders = list(pieces_dir.iterdir())
            piece_folders = [f for f in folders if f.is_dir()]
            self.assertEqual(1, len(piece_folders))
            self.assertIn("test-essay", piece_folders[0].name)
            # Should have the right files
            self.assertTrue((piece_folders[0] / "SESSION-CONTEXT.md").is_file())
            self.assertTrue((piece_folders[0] / "notes.md").is_file())
            self.assertTrue((piece_folders[0] / "edits").is_dir())

    def test_new_piece_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            pieces_dir = Path(tmp) / "pieces"
            pieces_dir.mkdir()
            knowledge_dir = Path(tmp) / "knowledge"
            knowledge_dir.mkdir()
            (knowledge_dir / "positioning.md").write_text("# test\n")
            (Path(tmp) / ".familiar").write_text(
                f"knowledge = {knowledge_dir}\npieces = {pieces_dir}\n")

            env = {**os.environ,
                   "FAMILIAR_KNOWLEDGE": "",
                   "FAMILIAR_CONFIG": "",
                   "FAMILIAR_PIECES": ""}
            # Create once
            subprocess.run(
                ["python3", str(CLI), "new-piece", "dup-test"],
                capture_output=True, text=True, cwd=tmp, env=env)
            # Try again without --force
            result = subprocess.run(
                ["python3", str(CLI), "new-piece", "dup-test"],
                capture_output=True, text=True, cwd=tmp, env=env)
            self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()
