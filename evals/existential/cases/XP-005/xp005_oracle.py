"""Offline XP-005 behavior probe. All CDP and provider effects are local fixtures."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent


class OracleFailure(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OracleFailure(message)


def node_action(candidate: Path, package: Path, scenario: str, action: str, trace: Path) -> dict:
    env = os.environ.copy()
    env.update({
        'MA_NODE_PACKAGE_ROOT': str(package), 'CDP_PORT': '9111',
        'MA_ACTION': action, 'CHANNEL_ID': 'UC_LOCAL_A',
        'PHONE_NUMBER': '+84900000001', 'XP005_SCENARIO': scenario,
        'XP005_TRACE': str(trace),
    })
    proc = subprocess.run(
        ['node', str(candidate / 'multiple_automation/node_control/studio_runtime.mjs')],
        cwd=candidate, env=env, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=20, check=False,
    )
    require(proc.returncode == 0, f'local CDP fixture failed: {proc.stderr[-300:]}')
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    require(bool(lines), 'verification action gave no structured result')
    value = json.loads(lines[-1])
    require(isinstance(value, dict), 'verification action result was not an object')
    return value


def run(candidate: Path) -> dict:
    from probes.phone_verification_provider import NumberLease, OperationState as ProviderState, OtpResult, Service
    from multiple_automation.adapters.raw_cdp import RawCDPPhoneUIAdapter
    from multiple_automation.eligibility_phone import AcquisitionResult, EligibilityPhoneService
    from multiple_automation.secure_store import ProtectedPhoneLease
    from multiple_automation.store import SQLiteProductStore, WorkspaceBusyError

    findings: dict[str, object] = {}
    failures: list[str] = []

    def check(name: str, callback) -> None:
        try:
            findings[name] = callback()
        except Exception as exc:
            failures.append(f'{name}: {type(exc).__name__}: {exc}')

    with tempfile.TemporaryDirectory(prefix='xp005-local-') as temp:
        root = Path(temp)
        package = root / 'fake_cdp'
        module = package / 'node_modules/chrome-remote-interface'
        module.mkdir(parents=True)
        (package / 'package.json').write_text('{"private":true}\n', encoding='utf-8')
        shutil.copyfile(HERE / 'xp005_cdp_fixture.js', module / 'index.js')

        def probe_states():
            trace = root / 'node-actions.txt'
            step_one = node_action(candidate, package, 'step_one', 'VERIFY_SUBMIT_PHONE', trace)
            unresolved = node_action(candidate, package, 'step_one', 'VERIFY_RECONCILE_PHONE', trace)
            step_two = node_action(candidate, package, 'step_two', 'VERIFY_SUBMIT_PHONE', trace)
            require(step_one.get('state') == 'RECONCILE_REQUIRED', 'step-one SMS wording was mistaken for accepted submission')
            require(unresolved.get('state') == 'UNKNOWN', 'step-one readback was mistaken for reconciliation')
            require(step_two.get('state') == 'ACCEPTED', 'actual step-two evidence was not recognized')
            require(trace.read_text(encoding='utf-8').splitlines() == ['mousePressed', 'mousePressed'],
                    'local submission fixture observed an unexpected click count')
            return {'step_one': step_one['state'], 'unresolved': unresolved['state'], 'step_two': step_two['state']}

        def probe_transport():
            trace = root / 'transport.txt'
            before = node_action(candidate, package, 'before_click', 'VERIFY_SUBMIT_PHONE', trace)
            during = node_action(candidate, package, 'during_click', 'VERIFY_SUBMIT_PHONE', trace)
            require(before.get('state') == 'RECONCILE_REQUIRED',
                    'pre-click transport loss did not stop for reconciliation')
            require(during.get('state') == 'RECONCILE_REQUIRED',
                    'mid-click transport loss did not stay uncertain')
            require(trace.read_text(encoding='utf-8').splitlines() == ['mousePressed'],
                    'fixture observed an unexpected additional click')
            return {'before_click': before, 'during_click': during}

        check('verification_readback', probe_states)
        check('transport_boundary', probe_transport)

        class LocalProvider:
            def __init__(self):
                self.acquisitions = 0
                self.otp = {}

            def resolve_youtube_service(self):
                return Service('local-youtube', 'Youtube', price='1000')

            def resolve_network(self, name):
                return Service('local-network', name)

            def acquire(self, service, network):
                self.acquisitions += 1
                index = self.acquisitions
                lease = NumberLease('LOCAL', service, f'local-request-{index}',
                                    f'+8490000000{index}', '+84', 'VN')
                self.otp[lease.request_id] = OtpResult(
                    provider='LOCAL', request_id=lease.request_id,
                    state=ProviderState.WAITING_FOR_OTP,
                )
                return AcquisitionResult('ACQUIRED', lease)

            def wait_for_otp(self, request_id):
                return self.otp[request_id]

        class LocalVault:
            def __init__(self):
                self.items = {}

            def put(self, *, operation_id, request_id, phone_number):
                key = f'local-secret-{len(self.items) + 1}'
                item = ProtectedPhoneLease(key, request_id, phone_number)
                self.items[key] = item
                return item

            def get(self, secret_ref):
                return self.items[secret_ref]

        class LocalRunner:
            def __init__(self):
                self.submit_calls = 0
                self.reconcile_calls = 0
                self.reconcile_scenario = 'step_one'
                self.eligible = False

            def run(self, action, **values):
                if action == 'VERIFY_OBSERVE':
                    return {'state': 'VERIFIED' if self.eligible else 'PHONE_REQUIRED'}
                if action == 'VERIFY_SUBMIT_PHONE':
                    self.submit_calls += 1
                    return node_action(candidate, package, 'during_click', action, root / 'service-clicks.txt')
                if action == 'VERIFY_RECONCILE_PHONE':
                    self.reconcile_calls += 1
                    return node_action(candidate, package, self.reconcile_scenario, action, root / 'service-reconcile.txt')
                if action == 'VERIFY_SUBMIT_OTP':
                    self.eligible = True
                    return {'state': 'VERIFIED'}
                if action == 'VERIFY_RECONCILE_OTP':
                    return {'state': 'UNKNOWN'}
                raise OracleFailure(f'unexpected action {action}')

        def make_workspace(store, identity):
            workspace = store.create_workspace()
            account = store.create_google_account(f'{identity}@example.invalid', f'secretref:{identity}')
            proxy = store.create_proxy_binding('operator', f'proxy-{identity}')
            profile = store.create_browser_profile(f'profile-{identity}', proxy)
            store.assign_workspace_identity(workspace, google_account_id=account,
                                            proxy_binding_id=proxy, browser_profile_id=profile)
            channel = store.create_youtube_channel(account, f'UC_LOCAL_{identity}')
            store.bind_workspace_channel(workspace, channel)
            return workspace

        def probe_ownership():
            db = root / 'product.sqlite3'
            store = SQLiteProductStore(db)
            owner_a, owner_b = make_workspace(store, 'A'), make_workspace(store, 'B')
            provider, vault = LocalProvider(), LocalVault()
            runner_a, runner_b = LocalRunner(), LocalRunner()
            service_a = EligibilityPhoneService(store, provider, RawCDPPhoneUIAdapter(runner_a), vault)
            first = service_a.ensure_required_eligibility(owner_a)
            operation = store.get_active_operation(owner_a)
            require(first.status == 'RECONCILE_REQUIRED' and operation is not None,
                    'uncertain submission did not retain active owning task')
            effects = [x for x in store.list_effects(operation.operation_id) if x.effect_type == 'google.phone.submit']
            require(len(effects) == 1 and effects[0].workspace_id == owner_a and
                    effects[0].operation_id == operation.operation_id and effects[0].state == 'RECONCILE_REQUIRED',
                    'uncertain effect lost exact owner or effect identity')
            require(bool(effects[0].evidence), 'durable effect lost uncertainty evidence')
            require(len(store.list_phone_leases(operation.operation_id)) == 1 and provider.acquisitions == 1,
                    'uncertain submission changed its persisted provider lease')
            try:
                store.begin_operation(owner_a, 'VERIFYING', {'intent': 'competing-new-task'})
            except WorkspaceBusyError:
                pass
            else:
                raise OracleFailure('competing task was admitted while original effect remains unresolved')

            service_b = EligibilityPhoneService(store, provider, RawCDPPhoneUIAdapter(runner_b), vault)
            other = service_b.ensure_required_eligibility(owner_b)
            operation_b = store.get_active_operation(owner_b)
            require(other.status == 'RECONCILE_REQUIRED' and operation_b is not None and
                    operation_b.operation_id != operation.operation_id and runner_b.submit_calls == 1,
                    'independent client task was conflated with the uncertain owner')
            require(all(e.workspace_id == owner_b for e in store.list_effects(operation_b.operation_id)),
                    'independent task effects were attributed to another workspace')

            restarted = EligibilityPhoneService(SQLiteProductStore(db), provider,
                                                RawCDPPhoneUIAdapter(runner_a), vault)
            retry = restarted.ensure_required_eligibility(owner_a)
            require(retry.status == 'RECONCILE_REQUIRED' and runner_a.submit_calls == 1 and
                    runner_a.reconcile_calls == 1 and provider.acquisitions == 2,
                    'same intended task retry redispatched instead of reconciling')
            require(store.get_active_operation(owner_a).operation_id == operation.operation_id and
                    store.get_effect(effects[0].effect_id).workspace_id == owner_a,
                    'restart or newer other-client task changed original ownership')

            runner_a.reconcile_scenario = 'step_two'
            recovered = restarted.ensure_required_eligibility(owner_a)
            require(recovered.status == 'WAITING_FOR_OTP' and runner_a.submit_calls == 1,
                    'positive readback did not reconcile original submission without redispatch')
            lease = store.list_phone_leases(operation.operation_id)[0]
            provider.otp[vault.get(lease['secret_ref']).request_id] = OtpResult(
                provider='LOCAL', request_id=vault.get(lease['secret_ref']).request_id,
                state=ProviderState.OTP_RECEIVED, code='123456',
            )
            finished = restarted.ensure_required_eligibility(owner_a)
            require(finished.status == 'VERIFIED' and store.get_active_operation(owner_a) is None,
                    'reconciled original task did not finish independently')
            new = store.begin_operation(owner_a, 'NEW_LOCAL_TASK', {'intent': 'intentional-new-task'})
            require(new.operation_id != operation.operation_id and new.workspace_id == owner_a,
                    'intentional new task was conflated with prior retry')
            return {
                'same_task_reused': True, 'other_workspace_independent': True,
                'partial_effect_reconciled': True, 'new_task_distinct': True,
                'submission_counts': {'owner_a': runner_a.submit_calls, 'owner_b': runner_b.submit_calls},
            }

        check('durable_ownership_and_reconciliation', probe_ownership)

    if failures:
        raise OracleFailure('; '.join(failures))
    return findings


def main() -> int:
    try:
        candidate = Path(sys.argv[1]).resolve()
        evidence = run(candidate)
        result = {'status': 'PASS', 'evidence': evidence}
    except Exception as exc:
        result = {'status': 'FAIL', 'reason': f'{type(exc).__name__}: {exc}'}
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
