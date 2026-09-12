"""Offline regressions for the redesigned lab; no provider calls or saved experiments."""
import base64
import contextlib
import copy
import io
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_experiment import CONFIG, PROBLEM, GOOD_SCHEDULE, LANGUAGE, LANGUAGE_ENTRIES, ScriptedBackend, action
from experiment.codex import AppServer, ActionFormatError, CodexError
from experiment.problem import agent_input, feasible_scores, oracle, problem_diagnostics, team_summary
from experiment.protocols import (canonical_frame, compact, empty_frame, render_assembly, render_logic, transmit,
    vector_decode, vector_encode, parse_assembly, MAX_REASONS)
from experiment.records import check_claim, review_run, write_trial_records
from experiment.runner import Recorder, Trial, run_batch, summarize


def message(kind, schedule=None, **contents):
    f = empty_frame(kind)
    f.update(contents)
    f['schedule'] = schedule or {}
    return compact(f)


class SequenceBackend(ScriptedBackend):
    def __init__(self, sequence):
        super().__init__(CONFIG)
        self.sequence = list(sequence)

    def turn(self, tid, text, schema=None, request_id=None):
        actor = self.roles[tid]
        self.inputs.append((actor, text))
        expected, result = self.sequence.pop(0)
        if actor != expected:
            raise AssertionError('Expected %s, got %s' % (expected, actor))
        usage = self.usage[tid]['total']
        for key, amount in [('inputTokens',100),('outputTokens',30),('totalTokens',130)]:
            usage[key] += amount
        if isinstance(result, Exception):
            raise result
        return result


def finishing_steps(schedule=GOOD_SCHEDULE):
    return [('A', action('send',message('propose',schedule))),
            ('B', action('send',message('accept',schedule))),
            ('A', action('submit',schedule=schedule)), ('B', action('submit',schedule=schedule))]


class ProblemRegressions(unittest.TestCase):
    def test_coupling_and_decisive_private_fact(self):
        original = copy.deepcopy(PROBLEM)
        d = problem_diagnostics(PROBLEM)
        self.assertEqual(d['oracle']['feasible_count'],54)
        self.assertEqual(d['oracle']['optimal_score'],27)
        self.assertEqual(d['oracle']['optimal_schedules'],[{'M1':4,'M2':11,'M3':10}])
        self.assertEqual(d['coupling_gap'],1)
        self.assertEqual(d['per_meeting_independent_maxima']['M1'],{'score':8,'slots':[4]})
        self.assertEqual(d['per_meeting_independent_maxima']['M2'],{'score':9,'slots':[4]})
        self.assertEqual(d['sensitivity_probe']['optimal_score'],24)
        self.assertEqual(d['sensitivity_probe']['feasible_count'],36)
        self.assertEqual(PROBLEM,original)
        for actor in ('A','B'):
            text = compact(agent_input(PROBLEM,actor))
            for private_evaluation in ('optimal_score','coupling_gap','sensitivity_probe'):
                self.assertNotIn(private_evaluation,text)

    def test_summaries_preserve_full_problem_for_every_schedule(self):
        from experiment.records import summary_counterfactual
        unchanged = ['available','A','M3',10,team_summary(PROBLEM,'A','M3',10)['available']]
        self.assertEqual(summary_counterfactual(PROBLEM,unchanged),feasible_scores(PROBLEM))


class CodecRegressions(unittest.TestCase):
    def test_large_summary_and_reason_frames_roundtrip(self):
        rng = random.Random(17)
        for _ in range(25):
            f = empty_frame('reject')
            f['summaries'] = [[relation,team,meeting,slot,rng.randrange(2 if relation=='available' else 10)]
                             for relation in ('available','preference') for team in ('A','B')
                             for meeting in ('M1','M2','M3') for slot in range(12)]
            f['reasons'] = [['overlap','M1','M2',slot] for slot in range(12)]
            for stage, text in [(2,compact(f)),(3,render_logic(f)),(4,compact(f)),(5,render_assembly(f)),(6,render_logic(f,LANGUAGE))]:
                with self.subTest(stage=stage):
                    self.assertEqual(transmit(stage,text,LANGUAGE).frame,canonical_frame(f))
            self.assertEqual(parse_assembly(render_assembly(f)),canonical_frame(f))

    def test_out_of_domain_summary_or_reason_is_rejected_by_every_codec(self):
        for changes in ({'summaries':[['preference','A','M3',10,10]]},
                        {'summaries':[['available','A','M3',12,1]]},
                        {'reasons':[['overlap','M1','M1',4]]},
                        {'reasons':[['unavailable','M3','B3',-1]]}):
            f = empty_frame()
            f.update(changes)
            for stage in (2,4):
                with self.assertRaises(ValueError):
                    transmit(stage,compact(f))


class RunnerRegressions(unittest.TestCase):
    def run_sequence(self, sequence, stage=2):
        backend = SequenceBackend(sequence)
        with tempfile.TemporaryDirectory() as tmp:
            rec = Recorder(Path(tmp)/'trial')
            result = Trial(backend,CONFIG,PROBLEM,stage,rec).run()
            events = [json.loads(line) for line in (rec.folder/'events.jsonl').read_text().splitlines()]
            return result, events, backend

    def test_confirmation_after_submission_preserves_commitment(self):
        steps = finishing_steps()[:3] + [
            ('B',action('send',message('accept',GOOD_SCHEDULE))), ('A',action('wait')),
            ('B',action('submit',schedule=GOOD_SCHEDULE))]
        r, events, _ = self.run_sequence(steps)
        self.assertTrue(r['success'])
        self.assertEqual(r['proposal_revision'],0)
        self.assertEqual(set(r['submission_versions']),{'A','B'})
        self.assertFalse(any(e['method']=='experiment/submissions_invalidated' for e in events))

    def test_explicit_revision_invalidates_and_notifies_both_agents(self):
        replacement = {'M1':1,'M2':4,'M3':10}
        steps = finishing_steps()[:3] + [('B',action('revise',message('propose',replacement))),
            ('A',action('wait')),('B',action('submit',schedule=replacement)),('A',action('submit',schedule=replacement))]
        r, events, backend = self.run_sequence(steps)
        self.assertTrue(r['success'])
        self.assertEqual(r['quality_gap'],1)
        self.assertEqual(r['proposal_revision'],1)
        self.assertTrue(all(s['revision']==1 for s in r['submission_versions'].values()))
        for actor in ('A','B'):
            self.assertTrue(any(a==actor and 'must submit again' in text for a,text in backend.inputs))
        notices = [e['params'] for e in events if e['method']=='experiment/submissions_invalidated']
        self.assertEqual(notices[0]['cleared_agents'],['A'])

    def test_rejected_revision_does_not_cancel_commitments(self):
        steps = finishing_steps()[:3] + [('B',action('revise','invalid')),
            ('B',action('send',message('accept',GOOD_SCHEDULE))),('A',action('wait')),
            ('B',action('submit',schedule=GOOD_SCHEDULE))]
        r, _, _ = self.run_sequence(steps)
        self.assertTrue(r['success'])
        self.assertEqual(r['proposal_revision'],0)
        self.assertEqual(r['protocol_error_counts']['message_payload'],1)

    def test_changing_an_existing_submission_requires_explicit_revision(self):
        changed = {'M1':1,'M2':4,'M3':10}
        steps = finishing_steps()[:3] + [('B',action('send',message('accept',GOOD_SCHEDULE))),
            ('A',action('submit',schedule=changed)),('A',action('wait')),('B',action('submit',schedule=GOOD_SCHEDULE))]
        r,_,_ = self.run_sequence(steps)
        self.assertTrue(r['success'])
        self.assertEqual(r['submissions']['A'],GOOD_SCHEDULE)
        self.assertEqual(r['protocol_error_counts']['task_action'],1)

    def test_wire_bytes_and_model_facing_text_have_separate_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = Recorder(Path(tmp)/'trial')
            r = Trial(ScriptedBackend(CONFIG),CONFIG,PROBLEM,5,rec).run()
            packets = [json.loads(line)['params'] for line in (rec.folder/'events.jsonl').read_text().splitlines()
                       if json.loads(line)['method']=='experiment/packet']
            self.assertEqual(r['task_sender_text_bytes'],sum(len(p['sender_source'].encode()) for p in packets))
            self.assertEqual(r['task_receiver_text_bytes'],sum(len(p['receiver_text'].encode()) for p in packets))
            self.assertNotEqual(r['task_sender_text_bytes'],r['payload_bytes'])

    def test_envelope_and_response_parse_errors_allow_same_actor_to_correct(self):
        for bad,category in [(action('wait','not empty'),'action_envelope'),
                             (ActionFormatError('response_parse','invalid JSON','{bad'),'response_parse')]:
            r,events,backend = self.run_sequence([('A',bad)]+finishing_steps())
            self.assertTrue(r['success'])
            self.assertEqual(r['actions'],5)
            self.assertEqual(r['protocol_error_counts'][category],1)
            self.assertIn('rejected',backend.inputs[1][1])
            rejected = [e for e in events if e['method']=='experiment/rejected']
            self.assertIsNotNone(rejected[0]['params']['raw_response'])

    def test_language_setup_envelope_error_has_correction_opportunity(self):
        steps = [('A',action('wait','bad')),('A',action('define_language',language=LANGUAGE_ENTRIES)),
                 ('B',action('accept_language')),('A',action('submit',schedule=GOOD_SCHEDULE)),
                 ('B',action('submit',schedule=GOOD_SCHEDULE))]
        r,_,_ = self.run_sequence(steps,stage=6)
        self.assertTrue(r['success'])
        self.assertEqual(r['protocol_error_counts']['action_envelope'],1)
        self.assertGreater(r['language_setup_seconds'],0)

    def test_repeated_bad_envelope_can_correct_after_old_limit(self):
        r,_,backend = self.run_sequence([('A',action('wait','bad'))]*30+finishing_steps())
        self.assertTrue(r['success'])
        self.assertEqual(r['actions'],34)
        self.assertEqual(r['protocol_errors'],30)

    def test_infrastructure_failure_is_not_a_format_correction(self):
        r,_,backend = self.run_sequence([('A',CodexError('connection failed'))])
        self.assertEqual(r['status'],'infrastructure_error')
        self.assertEqual(r['protocol_errors'],0)
        self.assertEqual(len(backend.inputs),1)

    def test_last_initialization_failure_is_terminal_but_not_a_task_success(self):
        calls = []
        def factory(*args,**kwargs):
            calls.append(1)
            if len(calls)==30:
                raise CodexError('last initialization failed')
            return ScriptedBackend(*args,**kwargs)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            folder,s = run_batch(CONFIG,PROBLEM,2,backend_factory=factory,output_root=tmp)
            self.assertEqual((s['attempted_trials'],s['completed_trials'],s['success_count']),(30,29,29))
            self.assertTrue(s['batch_complete'])
            self.assertEqual(s['success_rate'],29/30)
            self.assertIsNone(s['model_cost_per_success_estimate_usd'])
            self.assertEqual(json.loads((folder/'manifest.json').read_text())['status'],'completed')
            self.assertTrue((folder/'trial-30/observation.md').exists())

    def test_partial_measured_cost_does_not_make_infrastructure_batch_complete(self):
        rows = [{'success':True,'status':'success','quality_gap':0,'total_cost_estimate_usd':1,
                 'model_cost_estimate_usd':.5,'elapsed_seconds':1,'communication_bytes':10,
                 'protocol_cpu_seconds':0,'protocol_errors':0} for _ in range(5)]
        rows[-1].update(success=False,status='infrastructure_error')
        s = summarize(rows, expected=5)
        self.assertEqual(s['total_cost_estimate_usd'],5)
        self.assertEqual(s['cost_per_success_estimate_usd'],1.25)
        self.assertEqual(s['model_cost_per_success_estimate_usd'],.625)


class RecordsRegressions(unittest.TestCase):
    def test_all_six_record_formats_and_review_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            for stage in range(1,7):
                rec = Recorder(Path(tmp)/('trial-stage-%d'%stage))
                Trial(ScriptedBackend(CONFIG),CONFIG,PROBLEM,stage,rec).run()
                data = write_trial_records(rec.folder,PROBLEM,stage,Path(tmp)/('review-%d'%stage))
                self.assertEqual(data['codec_errors'],0)
                self.assertTrue(data['completion']['identical_submissions'])
                self.assertEqual(data['content_review_status'],'pending' if stage==1 else 'complete')
                self.assertEqual(data['incorrect_claims'],None if stage==1 else 0)

    def test_wrong_fact_and_summary_impact_are_separate_from_final_success(self):
        base = feasible_scores(PROBLEM)
        submissions = {'A':GOOD_SCHEDULE,'B':GOOD_SCHEDULE}
        wrong = check_claim(PROBLEM,'fact',['available','B3',10,0],base,submissions,{})
        self.assertFalse(wrong['correct'])
        self.assertEqual(wrong['impact']['optimal_score_after'],24)
        self.assertTrue(wrong['impact']['submitted_schedule_affected'])
        irrelevant = check_claim(PROBLEM,'fact',['available','A3',2,0],base,submissions,{})
        self.assertFalse(irrelevant['impact']['schedule_scores_changed'])
        summary = check_claim(PROBLEM,'summary',['available','B','M3',10,0],base,submissions,{})
        self.assertEqual(summary['impact']['optimal_score_after'],24)

    def test_natural_review_pending_then_separate_human_annotations(self):
        sequence=[('A',action('send','B3 cannot attend slot 10.')),('B',action('submit',schedule=GOOD_SCHEDULE)),('A',action('submit',schedule=GOOD_SCHEDULE))]
        with tempfile.TemporaryDirectory() as tmp:
            rec=Recorder(Path(tmp)/'trial')
            Trial(SequenceBackend(sequence),CONFIG,PROBLEM,1,rec).run()
            raw=(rec.folder/'events.jsonl').read_bytes()
            out=Path(tmp)/'review1'
            data=write_trial_records(rec.folder,PROBLEM,1,out)
            self.assertEqual(data['content_review_status'],'pending')
            self.assertIsNone(data['incorrect_claims'])
            manual=json.loads((out/'manual-review.json').read_text())
            manual['reviewer']='fixture reviewer'
            manual['entries'][0].update(status='complete',evidence='B3 cannot attend slot 10.',kinds=['inform'],claims=[{'type':'fact','value':['available','B3',10,0],'evidence':'B3 cannot attend slot 10.'}])
            manual_path=Path(tmp)/'annotations.json';manual_path.write_text(json.dumps(manual))
            data=write_trial_records(rec.folder,PROBLEM,1,Path(tmp)/'review2',manual_path)
            self.assertEqual(data['incorrect_claims'],1)
            self.assertEqual(data['codec_errors'],0)
            self.assertEqual(raw,(rec.folder/'events.jsonl').read_bytes())
            self.assertFalse((rec.folder/'observation.json').exists())
            manual['events_sha256']='wrong';manual_path.write_text(json.dumps(manual))
            with self.assertRaises(ValueError):write_trial_records(rec.folder,PROBLEM,1,Path(tmp)/'review3',manual_path)

    def test_versioned_reviews_preserve_every_original_file(self):
        from experiment.artifacts import file_hashes,verify_seal
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            folder,_=run_batch(CONFIG,PROBLEM,2,backend_factory=ScriptedBackend,output_root=tmp)
            raw=file_hashes(folder)
            first,rows=review_run(folder)
            second,_=review_run(folder)
            self.assertEqual(len(rows),30)
            self.assertNotEqual(first,second)
            self.assertEqual(raw,file_hashes(folder))
            verify_seal(first);verify_seal(second);verify_seal(folder)
            for name in ('observation.json','observation.md','transcript.md','Agent_A.md','Agent_B.md'):
                self.assertTrue((first/'trial-01'/name).exists())

    def test_codec_change_is_detected_even_if_altered_claim_would_be_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = Recorder(Path(tmp)/'trial')
            Trial(ScriptedBackend(CONFIG),CONFIG,PROBLEM,2,rec).run()
            events = [json.loads(line) for line in (rec.folder/'events.jsonl').read_text().splitlines()]
            packet = next(e['params'] for e in events if e['method']=='experiment/packet')
            changed = empty_frame()
            changed['facts'] = [['available','A1',1,1]]
            packet['payload_base64'] = base64.b64encode(compact(changed).encode()).decode()
            packet['receiver_text'] = compact(changed)
            # Corrupt only this disposable fixture, never an experiment log.
            (rec.folder/'events.jsonl').write_text('\n'.join(compact(e) for e in events)+'\n')
            data = write_trial_records(rec.folder,PROBLEM,2,Path(tmp)/"review")
            self.assertEqual(data['codec_errors'],1)

    def test_app_server_classifies_malformed_json_as_correctable(self):
        backend = AppServer(CONFIG)
        backend.queue.put({'method':'item/completed','params':{'threadId':'t','item':{'type':'agentMessage','text':'{bad'}}})
        backend.queue.put({'method':'turn/completed','params':{'threadId':'t','turn':{'id':'u','status':'completed'}}})
        with patch.object(backend,'rpc',side_effect=[{'turn':{'id':'u'}},{},{}]):
            with self.assertRaises(ActionFormatError) as caught:
                backend.turn('t','fixture')
        self.assertEqual(caught.exception.category,'response_parse')
        self.assertEqual(caught.exception.raw,'{bad')

    def test_readable_export_uses_requested_run_and_preserves_originals(self):
        from scripts.export_histories import export, hashes
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            folder,_ = run_batch(CONFIG,PROBLEM,5,backend_factory=ScriptedBackend,output_root=tmp)
            before = hashes(folder)
            output = Path(tmp)/'readable'
            export(folder,output)
            self.assertEqual(before,hashes(folder))
            self.assertTrue((output/'README.md').exists())
            self.assertEqual((output/'trial-01/events.jsonl').read_bytes(),(folder/'trial-01/events.jsonl').read_bytes())
            with self.assertRaises(ValueError):
                export(folder,output)
