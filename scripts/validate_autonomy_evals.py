#!/usr/bin/env python3
"""Validate the static CADS autonomy eval dataset. No execution or persistence."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "evals" / "autonomy" / "cases.json"
RISK = {"LOW", "MEDIUM", "HIGH"}
ORACLE = {"OBJECTIVE", "MIXED", "SUBJECTIVE", "WEAK"}
HUMAN = {"NONE", "SUBJECTIVE_JUDGEMENT", "AUTHORITY_ONLY"}
REQUIRED_FIELDS = {"id","title","failure_class","risk_class","goal","oracle_strength","expected_behavior","expected_human_attention","required_evidence","failure_signals","anti_shortcuts"}
FORBIDDEN_FIELDS = {"phase","workflow_state","task_lifecycle","retry_history","planner_state","chain_of_thought","subagent_graph","model_routing","session_history","trusted_model","model_tier","vendor_tier"}
REQUIRED_FAILURE_CLASSES = {"state-leakage","journey-composition","runtime-identity","external-effect-ambiguity","weak-oracle","oracle-integrity","decision-drift","nonconverging-repair","persistence-compatibility","ui-discoverability","parallel-candidate-integration","semantic-conflict","acceptance-authority","consequential-authority","stale-writer","context-continuity","conditional-review","intent-ambiguity","machine-workflow-behavior","intent-change-impact","accepted-contract-drift","design-ceremony-floor"}

def _text(value, name):
    if not isinstance(value, str) or not value.strip(): raise ValueError(f"{name} must be a non-empty string")
    return value.strip()

def _texts(value, name):
    if not isinstance(value, list) or not value: raise ValueError(f"{name} must be a non-empty list")
    return [_text(item, f"{name}[]") for item in value]

def validate(path=DEFAULT):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("schema_version") != 1: raise ValueError("schema_version must be 1")
    _text(value.get("suite_id"), "suite_id"); _text(value.get("purpose"), "purpose")
    cases = value.get("cases")
    if not isinstance(cases, list) or not (15 <= len(cases) <= 26): raise ValueError("cases must contain 15..26 representative Goals")
    ids=set(); classes=set(); risk={k:0 for k in RISK}; oracle={k:0 for k in ORACLE}; human={k:0 for k in HUMAN}
    for i, case in enumerate(cases):
        if not isinstance(case, dict): raise ValueError(f"cases[{i}] must be an object")
        bad=sorted(set(case)&FORBIDDEN_FIELDS)
        if bad: raise ValueError(f"cases[{i}] contains forbidden execution/policy field(s): {', '.join(bad)}")
        missing=sorted(REQUIRED_FIELDS-set(case)); extra=sorted(set(case)-REQUIRED_FIELDS)
        if missing: raise ValueError(f"cases[{i}] missing field(s): {', '.join(missing)}")
        if extra: raise ValueError(f"cases[{i}] contains unsupported field(s): {', '.join(extra)}")
        cid=_text(case['id'], f"cases[{i}].id")
        if cid in ids: raise ValueError(f"duplicate case id: {cid}")
        if not cid.startswith('AE-'): raise ValueError(f"case id must start with AE-: {cid}")
        ids.add(cid); classes.add(_text(case['failure_class'], f"cases[{i}].failure_class"))
        _text(case['title'], f"cases[{i}].title"); _text(case['goal'], f"cases[{i}].goal"); _text(case['expected_behavior'], f"cases[{i}].expected_behavior")
        r=_text(case['risk_class'], f"cases[{i}].risk_class"); o=_text(case['oracle_strength'], f"cases[{i}].oracle_strength"); h=_text(case['expected_human_attention'], f"cases[{i}].expected_human_attention")
        if r not in RISK: raise ValueError(f"invalid risk_class for {cid}: {r}")
        if o not in ORACLE: raise ValueError(f"invalid oracle_strength for {cid}: {o}")
        if h not in HUMAN: raise ValueError(f"invalid expected_human_attention for {cid}: {h}")
        risk[r]+=1; oracle[o]+=1; human[h]+=1
        _texts(case['required_evidence'], f"cases[{i}].required_evidence"); _texts(case['failure_signals'], f"cases[{i}].failure_signals"); _texts(case['anti_shortcuts'], f"cases[{i}].anti_shortcuts")
    missing_classes=sorted(REQUIRED_FAILURE_CLASSES-classes)
    if missing_classes: raise ValueError(f"required failure class coverage missing: {', '.join(missing_classes)}")
    if risk['HIGH'] < 5 or risk['LOW'] < 2: raise ValueError("suite must retain both consequential and low-risk representative cases")
    if oracle['OBJECTIVE'] < 10 or oracle['SUBJECTIVE'] < 1 or oracle['WEAK'] < 1: raise ValueError("suite must cover objective, subjective and weak-oracle cases")
    if human['NONE'] <= human['SUBJECTIVE_JUDGEMENT'] + human['AUTHORITY_ONLY']: raise ValueError("suite should primarily test autonomous execution")
    return {"result":"PASS","suite_id":value['suite_id'],"case_count":len(cases),"failure_class_count":len(classes),"risk_counts":risk,"oracle_counts":oracle,"human_attention_counts":human}

def main(argv):
    path = Path(argv[1]).resolve() if len(argv)>1 else DEFAULT
    try: result=validate(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"result":"BLOCK","message":str(exc)}, sort_keys=True)); return 2
    print(json.dumps(result, sort_keys=True)); return 0

if __name__ == '__main__': raise SystemExit(main(sys.argv))
