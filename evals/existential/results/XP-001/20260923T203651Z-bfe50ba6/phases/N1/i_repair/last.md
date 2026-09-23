**Changed**

- Added a more specific first-use Production CSS rule so the primary action stays fixed and visible when the later `position: static` rule applies.
- Extended the isolated browser check to measure the action at 1366×768 and 1366×600, with and without the first-use class. It checks visibility, hit testing, task-content reachability, horizontal overflow, pointer clicks, and Enter activation against the current task type.

**Checks run:** `node --check scripts/browser_production_task_workbench_smoke.mjs` and `git diff --check` passed. I did not run the browser journey: this checkout has no isolated server command available, and the documented app launcher uses the canonical runtime, which the brief prohibits contacting.

The new browser assertions are therefore unverified in a live browser. The “no scope” case is simulated by toggling the first-use class on the selected-scope fixture; it does not exercise the application’s actual no-scope setup path. No product acceptance is claimed.