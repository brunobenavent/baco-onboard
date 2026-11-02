import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fabrica.cli import main


class CliTests(unittest.TestCase):
    def test_named_run_hides_internal_expedient_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "state"
            output = Path(directory) / "expedient.json"
            argv = [
                "baco",
                "run",
                "summarize-pdf-email",
                "--sender",
                "brunobenavent@gmail.com",
                "--telegram",
                "@mi_usuario",
                "--state-dir",
                str(state_dir),
                "--output",
                str(output),
            ]

            with patch("sys.argv", argv):
                exit_code = main()

            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(data["procedure_id"], "summarize-pdf-email")
            self.assertEqual(data["inputs"]["metadata"]["telegram_recipient"], "@mi_usuario")

    def test_run_starts_a_process_and_writes_an_expedient(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "state"
            output = Path(directory) / "expedient.json"
            argv = [
                "baco",
                "run",
                "--message",
                "Resume el PDF",
                "--channel",
                "email",
                "--organization",
                "empresa-demo",
                "--requested-by",
                "brunobenavent@gmail.com",
                "--external-id",
                "mail-1",
                "--procedure-id",
                "summarize-pdf-email",
                "--procedure-version",
                "1.0",
                "--severity",
                "low",
                "--state-dir",
                str(state_dir),
                "--output",
                str(output),
            ]

            with patch("sys.argv", argv):
                exit_code = main()

            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(data["procedure_id"], "summarize-pdf-email")
            self.assertEqual(data["status"], "ready_for_execution")

    def test_status_reads_an_existing_expedient(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "state"
            output = Path(directory) / "expedient.json"
            run_argv = [
                "baco", "run", "--message", "Resume el PDF", "--channel", "email",
                "--organization", "empresa-demo", "--requested-by", "user-1",
                "--external-id", "mail-1", "--procedure-id", "summarize-pdf-email",
                "--procedure-version", "1.0", "--severity", "low", "--state-dir",
                str(state_dir), "--output", str(output),
            ]
            with patch("sys.argv", run_argv):
                main()
            expedient_id = json.loads(output.read_text(encoding="utf-8"))["id"]

            with patch(
                "sys.argv",
                ["baco", "status", "--id", expedient_id, "--state-dir", str(state_dir)],
            ):
                exit_code = main()

            self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
