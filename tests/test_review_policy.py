"""Post-run policy regressions. Uses disposable records and no provider calls."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from test_experiment import CONFIG, PROBLEM, GOOD_SCHEDULE, ScriptedBackend, action
from test_regressions import SequenceBackend, message
from experiment.artifacts import Recorder, file_hashes, verify_seal
from experiment.evaluation import check_claim, claim_counts, raw_preference_sum, REVIEW_POLICY_VERSION
from experiment.problem import evaluate, feasible_scores
from experiment.records import write_trial_records, review_run
from experiment.runner import Trial, run_batch


class ReviewPolicyTests(unittest.TestCase):
    def check(self, kind, value):
        return check_claim(PROBLEM, kind, value, feasible_scores(PROBLEM), {}, {})

    def test_valid_score_is_judged_but_invalid_score_keeps_both_arithmetic_outcomes(self):
        actual = evaluate(PROBLEM, GOOD_SCHEDULE)['score']
        for score in (actual, actual + 1):
            verdict = self.check('schedule_score', {'schedule':GOOD_SCHEDULE, 'score':score})
            self.assertEqual(verdict['correct'], score == actual)
            self.assertEqual(verdict['arithmetic_matches'], score == actual)
        invalid = {'M1':0, 'M2':0, 'M3':0}
        actual = raw_preference_sum(PROBLEM, invalid)
        for score in (actual, actual + 1):
            verdict = self.check('schedule_score', {'schedule':invalid, 'score':score})
            self.assertIsNone(verdict['correct'])
            self.assertIsNone(verdict['expected'])
            self.assertFalse(verdict['candidate_valid'])
            self.assertEqual(verdict['arithmetic_matches'], score == actual)
        # Final task validity and scoring remain unchanged.
        self.assertFalse(evaluate(PROBLEM, invalid)['valid'])
        self.assertIsNone(evaluate(PROBLEM, invalid)['score'])

    def test_undetermined_claims_are_not_counted_as_incorrect(self):
        counts = claim_counts([{'type':'schedule_score','correct':c} for c in (True,False,None,None)])['schedule_score']
        self.assertEqual(counts, {'occurrences':4,'judged':2,'correct':1,'incorrect':1,'undetermined':2})
        only = claim_counts([{'type':'schedule_score','correct':None}])['schedule_score']
        self.assertIsNone(only['incorrect'])
        self.assertEqual(only['undetermined'],1)

    def test_explicit_review_assertions_separate_availability_sum_and_optimality(self):
        # A1 is unavailable at slot 6, but the preference sum is still defined.
        people = next(m['attendees'] for m in PROBLEM['meetings'] if m['id']=='M3')
        value = sum(PROBLEM['people'][p]['preferences'][6] for p in people)
        self.assertTrue(self.check('meeting_score',{'meeting':'M3','slot':6,'score':value})['correct'])
        self.assertFalse(self.check('meeting_available',{'meeting':'M3','slot':6,'available':1})['correct'])
        suboptimal = {'M1':1,'M2':4,'M3':10}
        self.assertTrue(self.check('schedule_valid',{'schedule':suboptimal,'valid':1})['correct'])
        self.assertFalse(self.check('schedule_optimal',{'schedule':suboptimal,'optimal':1})['correct'])
        self.assertTrue(self.check('schedule_constraint',{'schedule':suboptimal,'constraint':'precedence','satisfied':1})['correct'])
        self.assertFalse(self.check('public_precedence',{'before':'M3','after':'M1'})['correct'])

    def test_same_legacy_invalid_claim_is_uncertain_in_natural_and_structured_records(self):
        invalid = {'M1':0,'M2':0,'M3':0}
        score = raw_preference_sum(PROBLEM,invalid)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            observations = []
            for stage in (1,2):
                text = 'The candidate score is %d.' % score if stage==1 else message('inform',evaluations=[['score',0,0,0,score]])
                sequence = [('A',action('send',text)),('B',action('submit',schedule=GOOD_SCHEDULE)),('A',action('submit',schedule=GOOD_SCHEDULE))]
                rec = Recorder(tmp/('trial-%d'%stage))
                Trial(SequenceBackend(sequence),CONFIG,PROBLEM,stage,rec).run()
                original = file_hashes(rec.folder)
                manual_path = None
                if stage==1:
                    pending = tmp/'pending'
                    write_trial_records(rec.folder,PROBLEM,stage,pending)
                    manual = json.loads((pending/'manual-review.json').read_text())
                    manual.update(reviewer='AI test fixture',reviewer_kind='ai')
                    manual['entries'][0].update(status='complete',evidence=text,kinds=['inform'],claims=[
                        {'type':'schedule_score','value':{'schedule':invalid,'score':score},'evidence':text}])
                    manual_path = tmp/'manual.json'
                    manual_path.write_text(json.dumps(manual))
                output = tmp/('review-%d'%stage)
                data = write_trial_records(rec.folder,PROBLEM,stage,output,manual_path)
                observations.append(data)
                self.assertEqual(data['incorrect_claims'],0)
                self.assertEqual(data['undetermined_claims'],1)
                self.assertEqual(data['codec_errors'],0)
                rendered = (output/'observation.md').read_text()
                errors = rendered.split('## 내용 오류와 영향')[1].split('## 판정 보류')[0]
                self.assertNotIn('입력 기준',errors)
                self.assertIn('산술 일치',rendered)
                self.assertEqual(original,file_hashes(rec.folder))
            self.assertEqual(observations[0]['claim_counts_by_type'],observations[1]['claim_counts_by_type'])
            self.assertEqual(observations[0]['annotation_reviewer_kind'],'ai')

    def test_review_archives_policy_and_evaluator_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            folder,_ = run_batch(CONFIG,PROBLEM,2,backend_factory=ScriptedBackend,output_root=tmp)
            before = file_hashes(folder)
            review,_ = review_run(folder)
            manifest = json.loads((review/'manifest.json').read_text())
            self.assertEqual(manifest['review_policy_version'],REVIEW_POLICY_VERSION)
            self.assertEqual(manifest['evaluation_source_files'],file_hashes(review/'evaluation-source'))
            self.assertTrue((review/'evaluation-source/experiment/evaluation.py').exists())
            verify_seal(review)
            self.assertEqual(before,file_hashes(folder))
