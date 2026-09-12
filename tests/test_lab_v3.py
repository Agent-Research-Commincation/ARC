"""Acceptance cases for v3. All model replies are explicit offline fixtures."""
import base64
import contextlib
import copy
import io
import json
import queue
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from test_experiment import CONFIG,PROBLEM,GOOD_SCHEDULE,LANGUAGE,LANGUAGE_ENTRIES,ScriptedBackend,action
from test_regressions import SequenceBackend,finishing_steps,message
from experiment.artifacts import Recorder,source_snapshot,digest,file_hashes,verify_seal,write_json
from experiment.contracts import action_schema,validate_action,validate_config,Cancelled,CodexError,ActionFormatError,MEANINGS
from experiment.codex import AppServer
from experiment.trial import Trial,base_prompt
from experiment.protocols import (empty_frame,compact,canonical_frame,transmit,render_logic,render_assembly,
    FACT_KEYS,SUMMARY_KEYS,REASON_KEYS,QUESTION_KEYS,EVALUATION_KEYS,vector_encode,vector_decode,compile_bytecode,decode_bytecode)
from experiment.problem import independent_oracle,oracle,agent_input
from experiment.metrics import communication_totals,summarize
from experiment.records import review_run
from experiment.evaluation import check_claim,analyze_trial
from experiment.runner import run_batch,execute_trial,failure_result
from experiment.scheduling import make_plan,claim_slot,finish_slot,execute_plan,run_requested,resume_plan,checkpoint_worktrees,load_state


def payload(stage,frame):
    return compact(frame) if stage in (2,4) else render_logic(frame,LANGUAGE if stage==6 else None) if stage in (3,6) else render_assembly(frame) if stage==5 else 'Please review our proposed schedule.'


class ContractsTests(unittest.TestCase):
    def test_thirty_trial_configuration_and_distinct_helper_counts(self):
        from experiment.cli import load_settings
        config, _ = load_settings()
        self.assertEqual(config['repetitions'], 30)
        self.assertEqual(config['first_speakers'], ['A', 'B'] * 15)
        validate_config(CONFIG)
        for count in (0, 5, 29, 31, 30.0, False):
            with self.subTest(count=count), self.assertRaises(ValueError):
                make_plan(config, PROBLEM, [1], count=count)
        with self.assertRaises(ValueError):
            validate_config(dict(config, repetitions=5, first_speakers=['A','B','A','B','A']))
        with self.assertRaises(ValueError):
            validate_config(dict(config, first_speakers=['A'] * 30))
        self.assertEqual(make_plan(config, PROBLEM, [1], purpose='pilot')['count'], 1)
        self.assertEqual(make_plan(config, PROBLEM, [None], purpose='observation')['count'], 5)

    def test_schemas_match_actions_and_hide_setup_meanings(self):
        for stage in range(1,7):
            schema=action_schema(stage)
            self.assertEqual(schema['properties']['action']['enum'],['send','revise','wait','submit','stop'])
            self.assertNotIn('define_language',compact(schema))
            self.assertNotIn('teamavailable',compact(schema))
            with self.assertRaises(ValueError):validate_action(action('define_language',language=LANGUAGE_ENTRIES),stage)
            validate_action(action('stop','I cannot continue.'),stage)
        self.assertEqual(action_schema(6,'setup')['properties']['action']['enum'],['define_language','accept_language','stop'])
        with self.assertRaises(ValueError):action_schema(1,'setup')
        for stage in range(1,6):
            self.assertNotIn('define_language',base_prompt('A',stage))
            self.assertNotIn('must communicate proposals',base_prompt('A',stage))

    def test_every_retired_budget_key_is_rejected(self):
        from experiment.contracts import LEGACY_BUDGET_KEYS
        for key in LEGACY_BUDGET_KEYS:
            with self.assertRaises(ValueError):validate_config(dict(CONFIG,**{key:999999999}))
        with self.assertRaises(ValueError):validate_config(dict(CONFIG,hidden_budget=100))

    def test_confirmation_is_frozen_and_independently_checked(self):
        from experiment.cli import load_settings
        from experiment.artifacts import ROOT
        from scripts.freeze_problem import select_problem
        _,p=load_settings()
        self.assertNotEqual(p,PROBLEM)
        reference=json.loads((ROOT/'config/problem-reference.json').read_text())
        self.assertEqual(reference['problem_hash'],digest(p))
        with patch('experiment.problem.evaluate',side_effect=AssertionError('Must not reuse evaluator')):
            self.assertEqual(independent_oracle(p),reference['oracle'])
        self.assertEqual(select_problem(PROBLEM)[0],p)
        p['secret_oracle']=reference
        self.assertNotIn('secret_oracle',compact(agent_input(p,'A')))


class UnboundedTrialTests(unittest.TestCase):
    def run_steps(self,steps,stage=2,first='A'):
        backend=SequenceBackend(steps)
        with tempfile.TemporaryDirectory() as tmp:
            rec=Recorder(Path(tmp)/'trial')
            result=Trial(backend,CONFIG,PROBLEM,stage,rec,first).run()
            events=[json.loads(x) for x in (rec.folder/'events.jsonl').read_text().splitlines()]
        return result,events,backend

    def test_waits_messages_actions_and_tokens_exceed_old_limits(self):
        steps=[(actor,action('wait')) for _ in range(14) for actor in ('A','B')]
        steps += [(actor,action('send',message('inform'))) for _ in range(11) for actor in ('A','B')]
        steps += finishing_steps()[-2:]
        original=SequenceBackend.turn
        def costly(backend,*args,**kwargs):
            result=original(backend,*args,**kwargs)
            backend.usage[args[0]]['total']['totalTokens']+=200000
            return result
        with patch.object(SequenceBackend,'turn',costly):
            result,events,_=self.run_steps(steps)
        self.assertTrue(result['success'])
        self.assertEqual(result['actions'],52)
        self.assertEqual(result['message_count'],22)
        self.assertEqual(communication_totals(events)['communication_bytes'],result['communication_bytes'])

    def test_setup_can_exceed_old_turn_limit(self):
        steps=[(a,action('define_language',language=LANGUAGE_ENTRIES)) for a in ['A','B']*4]
        steps += [('A',action('accept_language'))]+finishing_steps()[-2:]
        result,events,_=self.run_steps(steps,6)
        self.assertTrue(result['success'])
        self.assertEqual(result['message_count'],9)
        responses=[e for e in events if e['method']=='experiment/response_received']
        applied=[e for e in events if e['method']=='experiment/applied']
        self.assertEqual(len(responses),len(applied))

    def test_invalid_dictionary_processing_is_included_before_correction(self):
        steps=[('A',action('define_language',language=LANGUAGE_ENTRIES[:-1])),
               ('A',action('define_language',language=LANGUAGE_ENTRIES)),('B',action('accept_language'))]+finishing_steps()[-2:]
        result,events,_=self.run_steps(steps,6)
        self.assertTrue(result['success'])
        rejected=[e for e in events if e['method']=='experiment/codec_rejected']
        self.assertEqual(len(rejected),1)
        self.assertEqual(rejected[0]['params']['phase'],'language_setup')
        self.assertAlmostEqual(result['protocol_cpu_seconds'],communication_totals(events)['protocol_cpu_seconds'])

    def test_no_dialogue_required_and_b_can_start(self):
        for stage in range(1,7):
            setup=[('B',action('define_language',language=LANGUAGE_ENTRIES)),('A',action('accept_language'))] if stage==6 else []
            result,_,_=self.run_steps(setup+[('B',action('submit',schedule=GOOD_SCHEDULE)),('A',action('submit',schedule=GOOD_SCHEDULE))],stage,'B')
            self.assertTrue(result['success'])
            self.assertEqual(result['message_count'],2 if stage==6 else 0)

    def test_stop_is_observer_only_in_task_and_setup(self):
        for stage in range(1,7):
            result,events,_=self.run_steps([('A',action('stop','Private reason.'))],stage)
            self.assertEqual(result['status'],'stopped')
            self.assertFalse(any(e['method']=='experiment/packet' for e in events))
            self.assertEqual(result['message_count'],0)

    def test_revision_and_rejected_revision_are_consistent_in_all_formats(self):
        for stage in range(1,7):
            setup=[('A',action('define_language',language=LANGUAGE_ENTRIES)),('B',action('accept_language'))] if stage==6 else []
            f=empty_frame('propose');f['schedule']=GOOD_SCHEDULE
            text=payload(stage,f)
            steps=setup+[('A',action('submit',schedule=GOOD_SCHEDULE)),('B',action('revise',text)),
                         ('A',action('submit',schedule=GOOD_SCHEDULE)),('B',action('submit',schedule=GOOD_SCHEDULE))]
            result,_,_=self.run_steps(steps,stage)
            self.assertTrue(result['success']);self.assertEqual(result['proposal_revision'],1)

    def test_reference_must_have_been_observed_without_oracle_feedback(self):
        f=empty_frame();f['references']=[100]
        r,events,_=self.run_steps([('A',action('send',compact(f)))]+finishing_steps())
        self.assertEqual(r['protocol_errors'],1);self.assertTrue(r['success'])
        refs=empty_frame();refs['references']=[1]
        r,_,_=self.run_steps([('A',action('send',message('inform'))),('B',action('send',compact(refs)))]+finishing_steps()[-2:])
        self.assertTrue(r['success'])

    def test_cancelled_trial_keeps_partial_usage(self):
        r,events,_=self.run_steps([('A',action('send',message('inform'))),('B',Cancelled('cancel fixture'))])
        self.assertEqual(r['status'],'cancelled')
        self.assertEqual(r['message_count'],1)
        self.assertTrue(any(e['method']=='experiment/request_interrupted' for e in events))


class ExtendedCodecTests(unittest.TestCase):
    def test_all_supported_combinations_fit_without_hidden_line_or_byte_cap(self):
        f=empty_frame('reject')
        f['facts']=[list(k)+[1] for k in FACT_KEYS]
        f['summaries']=[list(k)+[1] for k in SUMMARY_KEYS]
        f['reasons']=[list(k) for k in REASON_KEYS]
        f['questions']=[list(k) for k in QUESTION_KEYS]
        f['evaluations']=[list(k)+[1] for k in EVALUATION_KEYS]
        f['schedule']=GOOD_SCHEDULE;f['requests']=['A1','A2','A3','B1','B2','B3']
        f['references']=[1,2**24+1,2**64+9,2**128+3]
        expected=canonical_frame(f)
        for stage in (2,3,4,5,6):
            self.assertEqual(transmit(stage,payload(stage,f),LANGUAGE).frame,expected)
        self.assertGreater(len(render_logic(f).splitlines()),320)

    def test_literal_bytecode_reference_and_evaluation_golden_data(self):
        source='KIND inform\nQFACT available A1 0\nVALID 0 1 2 0\nRECHECK 129'
        golden=b'ACB3\x00\x09\x00\x00\x00\x0d\x00\x01\x02\x00\x0f\x81\x01\xff'
        self.assertEqual(compile_bytecode(source),golden)
        self.assertEqual(decode_bytecode(golden)['references'],[129])
        for wire in (golden[:-2]+b'\x00\x01\xff',b'ACB3\x00\x0f\x81'):
            with self.assertRaises(ValueError):decode_bytecode(wire)

    def test_wrong_but_well_formed_claims_are_transmitted(self):
        f=empty_frame();f['evaluations']=[['valid',0,0,0,1],['score',0,0,0,54]]
        for stage in (2,3,4,5,6):
            self.assertEqual(transmit(stage,payload(stage,f),LANGUAGE).frame['evaluations'],canonical_frame(f)['evaluations'])


class BackendLifecycleTests(unittest.TestCase):
    def test_empty_polls_and_large_time_jumps_do_not_cancel(self):
        backend=AppServer(CONFIG)
        event={'id':1,'result':{'ok':True}}
        with patch.object(backend.queue,'get',side_effect=[queue.Empty]*10+[event]),patch('experiment.codex.time.monotonic',side_effect=[0,10000]):
            self.assertEqual(backend.next_event(),event)

    def test_cancel_and_eof_are_separate(self):
        backend=AppServer(CONFIG);backend.cancel_event.set()
        with self.assertRaises(Cancelled):backend.next_event()
        backend.cancel_event.clear();backend.queue.put({'_closed':True})
        with self.assertRaises(CodexError):backend.next_event()

    def test_late_rpc_response_is_preserved_for_matching_request(self):
        backend=AppServer(CONFIG)
        backend.queue.put({'id':2,'result':{'late':2}});backend.queue.put({'id':1,'result':{'first':1}})
        with patch.object(backend,'send') as send:
            self.assertEqual(backend.rpc('one',{}),{'first':1})
            self.assertEqual(backend.rpc('two',{}),{'late':2})
            self.assertEqual(send.call_count,2)

    def test_completed_response_survives_late_usage_and_closed_queue(self):
        for close in (False,True):
            backend=AppServer(CONFIG)
            backend.queue.put({'method':'turn/completed','params':{'threadId':'t','turn':{'id':'u','status':'completed','items':[{'type':'agentMessage','text':compact(action('wait'))}]}}})
            backend.queue.put({'method':'thread/tokenUsage/updated','params':{'threadId':'t','turnId':'u','tokenUsage':{'total':{'inputTokens':10,'cachedInputTokens':0,'outputTokens':5}}}})
            if close:backend.queue.put({'_closed':True})
            with patch.object(backend,'rpc',return_value={'turn':{'id':'u'}}) as rpc:
                self.assertEqual(backend.turn('t','test'),action('wait'))
                rpc.assert_called_once()
            self.assertEqual(backend.usage['t']['total']['inputTokens'],10)

    def test_reasoning_content_is_redacted_even_inside_turn_items(self):
        events=[];backend=AppServer(CONFIG,events.append)
        backend.queue.put({'method':'turn/completed','params':{'turn':{'items':[{'type':'reasoning','id':'r','text':'private reasoning'}]}}})
        backend.next_event()
        self.assertNotIn('private reasoning',compact(events))

    def test_late_model_reroute_cannot_make_an_ineligible_response_successful(self):
        backend=AppServer(CONFIG)
        backend.queue.put({'method':'turn/completed','params':{'threadId':'t','turn':{'id':'u','status':'completed','items':[{'type':'agentMessage','text':compact(action('wait'))}]}}})
        backend.queue.put({'method':'model/rerouted','params':{'threadId':'t','toModel':'other'}})
        with patch.object(backend,'rpc',return_value={'turn':{'id':'u'}}),patch.object(backend,'send'):
            with self.assertRaises(CodexError):backend.turn('t','fixture')
        self.assertEqual(backend.last_response,compact(action('wait')))


class PlanAndReviewTests(unittest.TestCase):
    def test_concurrent_resume_is_refused_before_copying_or_calling_models(self):
        from experiment.scheduling import coordinator_lock
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'plan.json'
            with coordinator_lock(path),patch('experiment.scheduling._resume_plan') as resume:
                with self.assertRaises(ValueError):resume_plan(path)
                resume.assert_not_called()

    def test_cleanup_failure_preserves_task_result_and_stops_next_allocation(self):
        class CleanupFailure(ScriptedBackend):
            def __exit__(self,*args):raise OSError('fixture cleanup failure')
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            folder,summary=run_batch(CONFIG,PROBLEM,2,backend_factory=CleanupFailure,output_root=tmp)
            result=json.loads((folder/'trial-01/result.json').read_text())
            self.assertTrue(result['success'])
            self.assertEqual(result['operational_status'],'infrastructure_error')
            self.assertEqual(summary['attempted_trials'],1)
            self.assertEqual(summary['infrastructure_errors'],1)
            self.assertIsNone(summary['success_rate'])

    def test_stop_finishes_thirty_attempts_without_success_backfill(self):
        class StopBackend(ScriptedBackend):
            def turn(self,*args,**kwargs):return action('stop','fixture voluntary stop')
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            folder,summary=run_batch(CONFIG,PROBLEM,2,backend_factory=StopBackend,output_root=tmp)
            self.assertEqual(summary['attempted_trials'],30)
            self.assertEqual(summary['success_count'],0)
            self.assertTrue(summary['batch_complete'])
            self.assertIsNone(summary['cost_per_success_estimate_usd'])
            self.assertEqual(len(list(folder.glob('trial-*/result.json'))),30)

    def test_no_judged_claims_are_not_reported_as_zero_errors(self):
        from experiment.evaluation import claim_counts
        self.assertIsNone(claim_counts([])['fact']['incorrect'])
        rows=[failure_result(1,'infrastructure_error','unknown usage')]
        self.assertIsNone(summarize(rows)['known_partial_model_cost_estimate_usd'])

    def test_same_explicit_claims_have_same_natural_and_structured_verdicts(self):
        frame=empty_frame();frame['facts']=[['available','B3',10,0]]
        frame['evaluations']=[['score',4,11,10,1],['valid',4,11,10,0]]
        claimed=[{'type':'fact','value':['available','B3',10,0]},
                 {'type':'schedule_score','value':{'schedule':GOOD_SCHEDULE,'score':1}},
                 {'type':'schedule_valid','value':{'schedule':GOOD_SCHEDULE,'valid':0}}]
        results=[]
        with tempfile.TemporaryDirectory() as tmp:
            for stage in range(1,7):
                setup=[('A',action('define_language',language=LANGUAGE_ENTRIES)),('B',action('accept_language'))] if stage==6 else []
                text='B3 cannot attend slot 10. The proposed schedule is invalid and scores one point.' if stage==1 else payload(stage,frame)
                steps=setup+[('A',action('send',text)),('B',action('stop'))]
                rec=Recorder(Path(tmp)/str(stage));result=Trial(SequenceBackend(steps),CONFIG,PROBLEM,stage,rec).run()
                events=[json.loads(x) for x in (rec.folder/'events.jsonl').read_text().splitlines()]
                manual={1:{'status':'complete','claims':claimed,'kinds':['inform'],'schedule':{},'requests':[],'unjudgeable':[]}} if stage==1 else None
                data=analyze_trial(PROBLEM,stage,events,result,LANGUAGE if stage==6 else None,manual)
                results.append(sorted((c['type'],c['correct']) for c in data['messages'][0]['claims']))
        self.assertTrue(all(r==results[0] for r in results))

    def test_paired_plan_has_exact_slots_and_no_extra_stages(self):
        for stages in ([3],list(range(1,7))):
            p=make_plan(CONFIG,PROBLEM,stages)
            self.assertEqual(len(p['slots']),len(stages)*30)
            for stage in stages:
                self.assertEqual([s['first_speaker'] for s in p['slots'] if s['stage']==stage],['A','B']*15)
            self.assertEqual(p['slots'],make_plan(CONFIG,PROBLEM,stages)['slots'])

    def test_atomic_slot_claim_is_unique(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'plan.json'
            write_json(path,make_plan(CONFIG,PROBLEM,[1]))
            write_json(path.with_name('state.json'),{'status':'running','slots':{'x':{'status':'not_started'}}})
            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(sum(pool.map(lambda _:claim_slot(path,'x'),range(20))),1)
            finish_slot(path,'x',{'status':'failed'})
            self.assertFalse(claim_slot(path,'x'))

    def test_resume_only_unstarted_slots_preserves_original_seal(self):
        calls=[]
        def fail_first(*args,**kwargs):
            calls.append(1);raise CodexError('initialization fixture failure')
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            plan,folders=run_requested(CONFIG,PROBLEM,[2],output_root=tmp,backend_factory=fail_first)
            original=folders[0];hashes=file_hashes(original)
            resumed=resume_plan(plan,backend_factory=ScriptedBackend)
            folder=resumed['2']
            self.assertEqual(hashes,file_hashes(original));verify_seal(original);verify_seal(folder)
            self.assertEqual(json.loads((folder/'trial-01/result.json').read_text())['status'],'infrastructure_error')
            self.assertEqual(json.loads((folder/'summary.json').read_text())['success_count'],29)
            self.assertEqual(len(calls),1)
            with self.assertRaises(ValueError):resume_plan(plan,backend_factory=ScriptedBackend)

    def test_parallel_pause_stops_new_dispatch_but_keeps_active_trial(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            p=make_plan(CONFIG,PROBLEM,[1,2,3],jobs=2)
            path=Path(tmp)/'plan.json';write_json(path,p)
            write_json(path.with_name('state.json'),{'plan_id':p['id'],'status':'running','slots':{s['id']:{'status':'not_started'} for s in p['slots']}})
            folders={str(s):Path(tmp)/str(s) for s in p['stages']}
            barrier=threading.Barrier(2);seen=[]
            def executor(slot,folder,cancel):
                seen.append(slot['id']);barrier.wait(timeout=5)
                status='infrastructure_error' if slot['order']==0 else 'stopped'
                if status=='stopped':
                    deadline=time.monotonic()+5
                    while load_state(path)['status']=='running' and time.monotonic()<deadline:
                        threading.Event().wait(.01)
                return failure_result(slot['stage'],status,'offline dispatch test')
            execute_plan(path,folders,executor=executor)
            self.assertEqual(len(seen),2)
            self.assertEqual(sum(s['status']=='not_started' for s in load_state(path)['slots'].values()),88)

    def test_checkpoint_worktrees_keep_user_head_index_and_changes(self):
        def git(root,*args):
            return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.DEVNULL).strip()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'repo';root.mkdir()
            git(root,'init')
            for folder in ('experiment','config','tests','scripts','docs'):(root/folder).mkdir()
            (root/'lab.py').write_text('print("original")\n');(root/'AGENTS.md').write_text('fixture')
            (root/'README.md').write_text('fixture');(root/'experiment/example.py').write_text('x=1\n')
            (root/'releases').mkdir()
            artifact = root/'releases'/'old-result.zip'
            artifact.write_bytes(b'offline fixture artifact')
            git(root,'add','.');git(root,'-c','user.name=Fixture','-c','user.email=fixture@localhost','commit','-m','fixture')
            original=git(root,'rev-parse','HEAD');index=(root/'.git/index').read_bytes()
            (root/'experiment/example.py').write_text('x=2\n')
            artifact.unlink()
            p={'id':'fixture-plan','stages':[1,2],'source_snapshot':source_snapshot(root)}
            plan_folder=Path(tmp)/'plan';plan_folder.mkdir()
            with patch('experiment.scheduling.ROOT',root):paths=checkpoint_worktrees(p,plan_folder)
            self.assertEqual(git(root,'rev-parse','HEAD'),original)
            self.assertEqual((root/'.git/index').read_bytes(),index)
            self.assertEqual((root/'experiment/example.py').read_text(),'x=2\n')
            self.assertEqual(len({git(Path(p),'rev-parse','HEAD') for p in paths.values()}),1)
            for p in paths.values():
                self.assertFalse((Path(p)/'releases/old-result.zip').exists())
                git(root,'worktree','remove','--force',p)

    def test_evaluation_same_meaning_no_submission_and_repetition(self):
        from experiment.problem import feasible_scores
        v=check_claim(PROBLEM,'fact',['available','B3',10,0],feasible_scores(PROBLEM),{}, {})
        self.assertIsNone(v['impact']['submitted_schedule_affected'])
        for k,value in [('schedule_score',{'schedule':GOOD_SCHEDULE,'score':1}),('schedule_valid',{'schedule':GOOD_SCHEDULE,'valid':0})]:
            self.assertFalse(check_claim(PROBLEM,k,value,{}, {}, {})['correct'])
        frames=[]
        for n in (0,0,1):
            f=empty_frame();f['facts']=[['available','B3',10,n]];frames.append(compact(f))
        steps=[('A',action('send',frames[0])),('B',action('wait')),('A',action('send',frames[1])),('B',action('wait')),('A',action('send',frames[2])),('B',action('stop'))]
        with tempfile.TemporaryDirectory() as tmp:
            rec=Recorder(Path(tmp)/'trial');result=Trial(SequenceBackend(steps),CONFIG,PROBLEM,2,rec).run()
            events=[json.loads(x) for x in (rec.folder/'events.jsonl').read_text().splitlines()]
            review=analyze_trial(PROBLEM,2,events,result)
            self.assertEqual(review['claim_occurrences'],3);self.assertEqual(review['unique_claims'],2)
            self.assertEqual(len(review['claim_changes']),1)

    def test_export_does_not_rescore_and_requires_matching_review(self):
        from scripts.export_histories import export
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            run,_=run_batch(CONFIG,PROBLEM,2,backend_factory=ScriptedBackend,output_root=tmp)
            review,_=review_run(run)
            with patch('experiment.evaluation.analyze_trial',side_effect=AssertionError('No evaluation on export')),patch('experiment.records.review_run',side_effect=AssertionError('No review on export')):
                output=export(run,Path(tmp)/'readable',review)
                self.assertEqual(json.loads((output/'export.json').read_text())['review'],str(review))
            verify_seal(run);verify_seal(review);verify_seal(output)
            (run/'trial-01/events.jsonl').write_text('tampered')
            with self.assertRaises(ValueError):export(run,Path(tmp)/'bad',review)
