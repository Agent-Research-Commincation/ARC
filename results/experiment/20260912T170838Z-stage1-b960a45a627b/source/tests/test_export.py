"""Portable evidence replay: no provider calls and no dependence on local records."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_experiment import CONFIG, PROBLEM, ScriptedBackend
from experiment.artifacts import file_hashes, verify_seal
from experiment.records import review_run
from experiment.runner import run_batch
from scripts.export_histories import export

ROOT = Path(__file__).resolve().parents[1]


class ExportTests(unittest.TestCase):
    def test_export_replays_selected_review_after_original_directory_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            tmp = Path(tmp)
            run, _ = run_batch(CONFIG, PROBLEM, 2, backend_factory=ScriptedBackend, output_root=tmp/'original')
            review, _ = review_run(run)
            before = file_hashes(run), file_hashes(review)
            output = export(run, tmp/'delivery', review)
            self.assertEqual(file_hashes(review), file_hashes(output/'selected-review'))
            self.assertEqual(before, (file_hashes(run), file_hashes(review)))
            relocated = tmp/'different location'
            shutil.move(str(output), relocated)
            shutil.rmtree(tmp/'original')
            reply = subprocess.run([sys.executable, '-I', '-B', str(relocated/'replay_review.py'),
                                    '--export', str(relocated), '--output', str(tmp/'replayed')],
                                   cwd=tmp, capture_output=True, text=True)
            self.assertEqual(reply.returncode, 0, reply.stdout+reply.stderr)
            self.assertTrue(json.loads(reply.stdout)['matched'])
            self.assertEqual(json.loads(reply.stdout)['trials'], 30)
            verify_seal(relocated)

    def test_tampered_selected_evaluator_is_rejected_before_replay(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            tmp = Path(tmp)
            run, _ = run_batch(CONFIG, PROBLEM, 2, backend_factory=ScriptedBackend, output_root=tmp/'original')
            review, _ = review_run(run)
            output = export(run, tmp/'delivery', review)
            evaluator = output/'selected-review/evaluation-source/experiment/evaluation.py'
            evaluator.write_text(evaluator.read_text()+'\nraise RuntimeError("must not execute")\n')
            reply = subprocess.run([sys.executable, '-I', '-B', str(output/'replay_review.py'),
                                    '--export', str(output), '--output', str(tmp/'replayed')],
                                   capture_output=True, text=True)
            self.assertNotEqual(reply.returncode, 0)
            self.assertIn('Seal mismatch', reply.stderr)
            self.assertFalse((tmp/'replayed').exists())

    def test_python_guard_denies_reads_from_original_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            # Load the guard first, then deliberately try to use the original root.
            code = """import importlib.util, pathlib
spec=importlib.util.spec_from_file_location('guard', __import__('sys').argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.restrict_io([__import__('sys').argv[2]], __import__('sys').argv[2])
pathlib.Path(__import__('sys').argv[3]).read_text()
"""
            reply = subprocess.run([sys.executable, '-I', '-B', '-c', code,
                                    str(ROOT/'scripts/replay_review.py'), str(tmp), str(ROOT/'config/problem.json')],
                                   capture_output=True, text=True)
            self.assertNotEqual(reply.returncode, 0)
            self.assertIn('Replay read outside bundle/stdlib', reply.stderr)

if __name__ == '__main__':
    unittest.main()
