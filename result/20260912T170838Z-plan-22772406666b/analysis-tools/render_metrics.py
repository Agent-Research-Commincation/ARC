"""Render completed aggregate artifacts; no models, source edits or rescoring.

Usage: python3 -B render_metrics.py ANALYSIS [--overview PATH] [--report PATH]
Optional document links are relative to metrics.md and emitted only for existing files.
"""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import sys
from urllib.parse import quote

TERMINAL = {'success', 'failed', 'stopped', 'cancelled', 'infrastructure_error'}
TRANSITIONS = {'optimal': '최적', 'valid_suboptimal': '유효·비최적', 'invalid': '불가능',
               'failed': '실패', 'stopped': '자체 종료', 'missing': '후보 없음',
               'unreviewed': '검수 대기', 'no_task_message': '작업 메시지 없음',
               'cancelled': '취소', 'infrastructure_error': '인프라 오류'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def fmt(value, digits=2):
    require(value is None or numeric(value), 'Invalid numeric measurement')
    return '미측정' if value is None else f'{value:,.{digits}f}'


def stat_text(stats, statistic='mean', digits=2, scale=1):
    expected = stats['expected_count']
    measured = stats.get('measured_count', stats.get('n'))
    require(type(expected) is int and type(measured) is int and 0 <= measured <= expected,
            'Invalid measurement coverage')
    if expected == 0:
        return '해당 회차 없음'
    value = stats[statistic]
    value = value * scale if value is not None else None
    label = fmt(value, digits)
    if measured != expected:
        label += f'<br>측정 {measured}/{expected}회'
    return label


def indexed(items, kind):
    result = {}
    for item in items:
        stage = item['stage']
        require(type(stage) is int and stage not in result, 'Duplicate/invalid ' + kind + ' stage')
        result[stage] = item
    require(result, 'No ' + kind + ' stages')
    return result


def load_completed(folder):
    aggregate = read(folder / 'stage_summary.json')
    processes = read(folder / 'process-summary.json')
    trials = read(folder / 'trial_rows.json')
    integrity = read(folder / 'integrity.json')
    plan = aggregate['plan_id']
    require(all(x.get('plan_id') == plan for x in (processes, trials, integrity)), 'Plan mismatch')
    require(aggregate.get('integrity_valid') is True and trials.get('integrity_valid') is True
            and integrity.get('valid') is True, 'Aggregate integrity is not verified')
    require(integrity.get('comparison_settings_equal') is True
            and integrity.get('inputs_unchanged_after_read') is True, 'Input integrity is incomplete')
    require(aggregate['comparison_group'] == trials.get('comparison_group') == integrity.get('comparison_group'),
            'Comparison group mismatch')
    require(processes.get('selected_review_hash_binding_verified') is True
            and processes.get('independent_outcome_check_passed') is True, 'Process checks are incomplete')
    summaries = indexed(aggregate['stages'], 'aggregate')
    process_stages = indexed(processes['stages'], 'process')
    records = indexed(integrity['records'], 'integrity')
    require(summaries.keys() == process_stages.keys() == records.keys(), 'Stage coverage mismatch')
    rows = trials['rows']
    expected_keys = []
    for stage, summary in summaries.items():
        expected = summary['expected_trials']
        require(type(expected) is int and expected > 0, 'Invalid expected_trials')
        require(summary.get('manifest_status') not in ('running', 'planned', 'pending')
                and summary.get('batch_confirmed') is True
                and summary['recorded_trials'] == expected and summary['not_started_trials'] == 0,
                'Only fully terminated campaigns can be rendered')
        record = records[stage]
        require(record.get('source_status') not in ('running', 'planned', 'pending')
                and all(record.get(k) is True for k in ('source_seal_verified', 'review_seal_verified',
                                                       'review_source_binding_verified')), 'Unsealed or running input')
        for key in ('source', 'review', 'readable'):
            if record.get(key):
                original = Path(record[key]).resolve()
                require(folder != original and original not in folder.parents, 'Output would alter an input tree')
        expected_keys.extend((stage, n) for n in range(1, expected + 1))
        subset = [r for r in rows if r['stage'] == stage]
        process = process_stages[stage]
        require(process['n'] == expected, 'Process stage trial count mismatch')
        coverage = dict(Counter(r['content_review_status'] for r in subset))
        require(summary['content_review_counts'] == process['content_review_counts'] == coverage,
                'Review coverage mismatch')
        require(summary['success_count'] == sum(r['success'] is True for r in subset)
                and summary['optimal_count'] == sum(r['optimal'] is True for r in subset), 'Outcome count mismatch')
        require(sum(process['candidate_transitions'].values()) == expected, 'Candidate transition coverage mismatch')
        for statistics in summary['metrics'].values():
            require(statistics['expected_count'] == expected, 'Metric denominator mismatch')
    require(Counter((r['stage'], r['trial']) for r in rows) == Counter(expected_keys), 'Trial coverage mismatch')
    require(all(r.get('recorded') is True and r.get('status') in TERMINAL for r in rows), 'Running or missing trial')
    require(processes['trials_checked'] == processes['expected_trials'] == len(rows), 'Process campaign count mismatch')
    raw_path = folder / 'raw-measurement-audit.json'
    if raw_path.exists():
        raw = read(raw_path)
        require(raw.get('verified') is True and raw.get('plan_id') == plan and raw.get('trials') == len(rows),
                'Raw measurement audit mismatch')
    return [summaries[k] for k in sorted(summaries)], process_stages, rows


def document_link(folder, target, label, explicit=False):
    target = Path(target).resolve()
    if not target.is_file():
        require(not explicit, 'Requested link target does not exist: ' + str(target))
        return None
    relative = quote(os.path.relpath(target, folder), safe='/.-_')
    return f'[{label}]({relative})'


def render(folder, overview=None, report=None):
    folder = Path(folder).resolve()
    summaries, process_stages, rows = load_completed(folder)
    total = len(rows)
    expected_values = sorted({s['expected_trials'] for s in summaries})
    repeats = '·'.join(str(n) for n in expected_values)
    links = [document_link(folder, overview or folder.parent / 'README.md', '전체 결과와 대화', overview is not None)]
    if report is not None:
        links.append(document_link(folder, report, '사람이 읽는 실험 보고서', True))
    else:
        default_report = next((p / 'docs' / 'experiment-report.md' for p in folder.parents
                               if (p / 'docs' / 'experiment-report.md').is_file()), None)
        if default_report is not None:
            links.append(document_link(folder, default_report, '사람이 읽는 실험 보고서'))
    lines = [f'# {total}회 상세 측정표', '']
    if any(links):
        lines += [' · '.join(link for link in links if link), '']
    lines += ['평균·중앙값·범위는 각 지표가 측정된 회차를 기준으로 하며 성공·실패를 함께 포함한다. '
              '일부 회차만 측정됐으면 셀에 측정 회차 수를 표시한다. 총합은 모든 회차가 측정됐을 때만 표시한다. '
              '성공 회차 시간은 별도 열이다. 입력·출력은 A와 B의 합이며 캐시 입력은 입력 토큰의 일부다. '
              '비용은 고정 API 단가의 추정이며 실제 구독 청구액이 아니다.']

    def table(title, headers, items):
        lines.extend(['', '## ' + title, '', '| ' + ' | '.join(headers) + ' |', '|' + '---|' * len(headers)])
        lines.extend('| ' + ' | '.join(str(v).replace('|', '\\|').replace('\n', '<br>') for v in row) + ' |' for row in items)

    def name(s):
        return str(s['stage']) + ' · ' + s['label']

    def metric(s, key, stat='mean', digits=2, scale=1):
        return stat_text(s['metrics'][key], stat, digits, scale)

    def per_success(s, key):
        return '산출 불가 (성공 0건)' if not s['success_count'] else fmt(s[key], 6)

    table('결과와 비용', ['방식', '유효 합의 / 전체', '최적 / 전체', '전체 모델 추정 USD',
                         '성공당 모델 추정 USD', '성공당 총비용 추정 USD', '회차당 통신 처리 추정 USD'], [
        [name(s), f"{s['success_count']}/{s['expected_trials']}", f"{s['optimal_count']}/{s['expected_trials']}",
         metric(s, 'model_cost_estimate_usd', 'total', 6), per_success(s, 'model_cost_per_success_estimate_usd'),
         per_success(s, 'total_cost_per_success_estimate_usd'), metric(s, 'communication_processing_cost_estimate_usd', digits=6)]
        for s in summaries])
    lines += ['', '성공당 비용은 실패·중단을 포함한 전체 비용을 성공 건수로 나눈 값이다. '
                  '총비용·통신 처리 비용이 미측정이면 0으로 채우지 않는다.']
    table('전체 종료 시간', ['방식', '평균 초', '중앙값 초', '최소 초', '최대 초', '성공 회차 평균 초', '성공 회차 중앙값 초'], [
        [name(s)] + [metric(s, 'elapsed_seconds', k, 1) for k in ('mean', 'median', 'min', 'max')]
        + [stat_text(process_stages[s['stage']]['success_elapsed_seconds'], k, 1) for k in ('mean', 'median')]
        for s in summaries])
    lines += ['', '종료 시간은 실행 환경 초기화부터 기록 렌더링까지의 회차별 경과시간이다. '
                  '실행기 배정·worktree 준비 시간은 제외되며 병렬 캠페인의 실제 경과시간과 회차 시간 합은 다르다.']
    table('대화와 모델 사용량: 회차 평균', ['방식', '전달 작업 메시지', '사전 메시지', '실행기 입력 요청/턴',
                                        '입력 토큰', '그중 캐시 입력', '출력 토큰'], [
        [name(s)] + [metric(s, k) for k in ('task_message_count', 'language_message_count', 'runner_turns',
                                          'input_tokens', 'cached_input_tokens', 'output_tokens')] for s in summaries])
    lines += ['', '실행기 요청/턴은 experiment/input의 수이며 공급자 내부 호출 또는 HTTP 요청 수가 아니다.']
    table('채널 전송량: 회차 평균', ['방식', '본문 B', '헤더 B', '합계 B', '작업 송신 텍스트 B', '작업 수신 텍스트 B'], [
        [name(s)] + [metric(s, k) for k in ('payload_bytes', 'envelope_bytes', 'communication_bytes',
                                          'task_sender_text_bytes', 'task_receiver_text_bytes')] for s in summaries])
    lines += ['', 'B는 바이트다. 채널 바이트에는 전달된 사전 합의 패킷도 포함한다. 작업 텍스트는 전달 작업 메시지만 '
                  '합산하며 사전 합의·제어 응답·반복 컨텍스트를 제외한다. 누적 모델 입력 토큰과 다른 지표다.']
    table('로컬 통신 처리: 회차 평균', ['방식', '작업 인코딩 CPU ms', '작업 디코딩 CPU ms', '프레이밍 CPU ms',
                                     '전체 프로토콜 CPU ms', '전체 프로토콜 경과 ms'], [
        [name(s)] + [metric(s, k, digits=3, scale=1000) for k in ('encoding_cpu_seconds', 'decoding_cpu_seconds',
                         'framing_cpu_seconds', 'protocol_cpu_seconds', 'protocol_wall_seconds')] for s in summaries])
    lines += ['', '작업 인코딩·디코딩은 전달 task 패킷의 코덱 시간이다. 프레이밍은 전달된 전체 패킷, '
                  '전체 프로토콜 시간은 전달 패킷과 코덱 거절 처리의 합이다. LLM의 통신 이해·추론 비용을 분리 측정한 값이 아니다.']

    def process_count(s, key, denominator):
        p = process_stages[s['stage']]
        n = p['content_review_counts'].get('complete', 0) if denominator == 'review' else s['metrics'][denominator]['measured_count']
        if n == 0:
            return '미측정 (대상 0회)'
        count = p['counts'].get(key, 0)
        require(type(count) is int and 0 <= count <= n, 'Process count exceeds measured denominator')
        return f'{count}/{n}'

    table('과정 관찰: 해당 회차 / 검수·측정 회차', ['방식', '질문·요청', '변경된 후보 제안', '실제 revise', '문법·제어 거절', '지원 주장 오류'], [
        [name(s)] + [process_count(s, k, d) for k, d in (
            ('with_request_or_question', 'review'), ('with_changed_proposal', 'review'),
            ('with_explicit_revision', 'explicit_revisions'), ('with_protocol_rejection', 'protocol_errors'),
            ('with_confirmed_content_error', 'review'))] for s in summaries])
    table('내용 검수 범위', ['방식', '완료 / 전체 회차', '검수 상태별 회차'], [
        [name(s), f"{s['content_review_counts'].get('complete', 0)}/{s['expected_trials']}",
         ', '.join(f'{k}: {v}' for k, v in sorted(s['content_review_counts'].items()))] for s in summaries])
    lines += ['', '질문·후보 변경·내용 오류의 분모는 내용 검수가 완료된 회차다. 검수 대기를 오류 0회로 취급하지 않는다. '
                  'revise와 문법·제어 거절은 해당 실행 기록이 측정된 회차가 분모다. 후보 변경과 revise는 다르며 '
                  'revise는 제출 전에도 사용할 수 있는 제어 행동이다. 질문·수락 표시가 이해나 검산을 입증하지 않는다.']
    table('지원 주장 검산', ['방식', '검토한 작업 메시지', '맞음', '틀림', '의미 판정 보류', '스키마 밖·모호 표현', '복원 오류'], [
        [name(s)] + [metric(s, k, 'total', 0) for k in ('reviewed_messages', 'correct_claims', 'incorrect_claims',
                                                       'undetermined_claims', 'unjudgeable_expressions', 'codec_errors')]
        for s in summaries])
    kinds = sorted({str(r.get('annotation_reviewer_kind')) for r in rows if r.get('annotation_reviewer_kind') is not None})
    lines += ['', '자연어 내용 지표는 선택된 원문 근거 주석을, 구조화 내용 지표는 지원 필드 검산을 따른다. '
                  f"주석에 기록된 검수자 유형: {', '.join(kinds) if kinds else '별도 명시 없음'}. "
                  '이 표만으로 사람의 전수 검수나 별도 독립 검토 완료를 주장하지 않는다. 주장 범위·반복·유보 표현이 달라 '
                  '오류 개수 또는 단순 오류율로 정확도 순위를 만들지 않는다. 불가능 후보의 확정형 총점 주장은 '
                  '의미 판정을 보류하고 산술합을 따로 보존한다. 잠정·조건부 표현은 선택된 주석의 범위를 따른다.']
    transitions = []
    for s in summaries:
        for transition, count in sorted(process_stages[s['stage']]['candidate_transitions'].items()):
            initial, final = transition.split(' -> ')
            transitions.append([name(s), TRANSITIONS.get(initial, initial) + ' → ' + TRANSITIONS.get(final, final), count])
    table('첫 전체 후보에서 최종 결과까지', ['방식', '전이', '회차 수'], transitions)
    lines += ['', '첫 전체 후보는 검수된 전달 메시지에서 모든 회의 배치가 처음 나타난 일정이며 propose에 한정하지 않는다. '
                  '검수 대기는 후보 없음과 다르다. 시작과 끝이 최적이어도 중간 오류가 없었다는 뜻은 아니다.']
    table('선발화 역할별 결과', ['방식', '선발화', '회차', '성공', '평균 모델 추정 USD', '평균 종료 초'], [
        [name(s), actor, group['trials'], group['successes'], stat_text(group['model_cost'], digits=6),
         stat_text(group['elapsed_seconds'], digits=1)] for s in summaries for actor in ('A', 'B')
        for group in [process_stages[s['stage']]['by_first_speaker'][actor]]])
    lines += ['', f'방식별 {repeats}회는 같은 문제의 반복이며 서로 다른 과제 수가 아니다. '
                  '같은 머신·서비스를 사용했으며 서비스 부하와 캐시 조건을 단계별로 통제하거나 초기화하지 않았다.']
    raw_links = [document_link(folder, folder / filename, label) for filename, label in (
        ('trial_rows.json', '회차별 집계'), ('stage_summary.json', '방식별 통계'),
        ('process-summary.json', '후보·과정 독립 검산'), ('integrity.json', '세션·봉인 검증'),
        ('raw-measurement-audit.json', '실제 토큰·패킷 검산'))]
    lines += ['', '원값: ' + ', '.join(link for link in raw_links if link) + '.', '']
    output = folder / 'metrics.md'
    output.write_text('\n'.join(lines), encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis', type=Path)
    parser.add_argument('--overview', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        print(render(args.analysis, args.overview, args.report))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print('Rendering refused: ' + str(exc), file=sys.stderr)
        sys.exit(2)
