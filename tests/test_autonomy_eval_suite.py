from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'evals'/'autonomy'/'cases.json'
VALIDATOR=ROOT/'scripts'/'validate_autonomy_evals.py'

class AutonomyEvalSuiteTests(unittest.TestCase):
    def data(self): return json.loads(DATA.read_text(encoding='utf-8'))
    def test_dataset_has_representative_size_and_unique_ids(self):
        cases=self.data()['cases']; self.assertGreaterEqual(len(cases),15); self.assertLessEqual(len(cases),25)
        ids=[c['id'] for c in cases]; self.assertEqual(len(ids),len(set(ids)))
    def test_dataset_covers_core_failure_classes(self):
        classes={c['failure_class'] for c in self.data()['cases']}
        required={"state-leakage","journey-composition","runtime-identity","external-effect-ambiguity","weak-oracle","oracle-integrity","decision-drift","nonconverging-repair","persistence-compatibility","ui-discoverability","parallel-candidate-integration","semantic-conflict","acceptance-authority","consequential-authority","stale-writer","context-continuity","conditional-review","release-evidence-continuity","intent-ambiguity","machine-workflow-behavior","intent-change-impact","design-ceremony-floor"}
        self.assertTrue(required <= classes)
    def test_dataset_contains_no_runtime_or_model_trust_state(self):
        forbidden={"phase","workflow_state","task_lifecycle","retry_history","planner_state","chain_of_thought","subagent_graph","model_routing","session_history","trusted_model","model_tier","vendor_tier"}
        for case in self.data()['cases']: self.assertFalse(forbidden & set(case), case['id'])
    def test_suite_keeps_owner_attention_exceptional(self):
        cases=self.data()['cases']; none=sum(c['expected_human_attention']=='NONE' for c in cases); subjective=sum(c['expected_human_attention']=='SUBJECTIVE_JUDGEMENT' for c in cases); authority=sum(c['expected_human_attention']=='AUTHORITY_ONLY' for c in cases)
        self.assertGreater(none, subjective+authority); self.assertGreaterEqual(subjective,1); self.assertGreaterEqual(authority,1)
    def test_validator_passes_canonical_dataset(self):
        proc=subprocess.run([sys.executable,str(VALIDATOR)],cwd=ROOT,text=True,encoding='utf-8',capture_output=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr); payload=json.loads(proc.stdout); self.assertEqual(payload['result'],'PASS'); self.assertEqual(payload['case_count'],25)
    def test_validator_fails_closed_on_execution_state_field(self):
        value=self.data(); value['cases'][0]['phase']='RUNNING'
        with tempfile.TemporaryDirectory(prefix='cads-evals-') as raw:
            path=Path(raw)/'cases.json'; path.write_text(json.dumps(value),encoding='utf-8')
            proc=subprocess.run([sys.executable,str(VALIDATOR),str(path)],cwd=ROOT,text=True,encoding='utf-8',capture_output=True,timeout=30)
        self.assertEqual(proc.returncode,2,proc.stdout+proc.stderr); self.assertEqual(json.loads(proc.stdout)['result'],'BLOCK')

if __name__=='__main__': unittest.main()