// node scheduler/test_worker.mjs — the decision logic against a fake GitHub API
import { startUpdate } from "./worker.js";
const now = Date.parse("2026-11-28T05:17:00Z");
const fake = (runs, dispatchStatus = 204) => {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push([init.method || "GET", url, init.body]);
    if (url.endsWith("/dispatches")) return new Response(null, { status: dispatchStatus });
    return new Response(JSON.stringify({ workflow_runs: runs }), { status: 200 });
  };
  return calls;
};
const env = { GH_TOKEN: "x" };
const run = (event, status, started) => ({ id: 1, event, status, run_started_at: started, created_at: started });
let calls, r, ok = true;
const expect = (cond, msg) => { if (!cond) { ok = false; console.error("FAIL", msg); } };

calls = fake([run("workflow_dispatch", "completed", "2026-11-28T00:17:00Z"), run("push", "in_progress", "2026-11-28T05:10:00Z")]);
r = await startUpdate(env, now);
expect(r.started && calls.some(([m, u, b]) => m === "POST" && u.endsWith("/dispatches") && JSON.parse(b).ref === "master"), "starts when nothing is running");
expect(JSON.parse(calls.find(([m]) => m === "POST")[2]).inputs.crawl_minutes === "220", "crawls 220 minutes");

calls = fake([run("workflow_dispatch", "in_progress", "2026-11-28T00:17:00Z")]);
r = await startUpdate(env, now);
expect(!r.started && !calls.some(([m]) => m === "POST"), "does not start while an update runs");

calls = fake([run("schedule", "completed", "2026-11-28T04:00:00Z")]);
r = await startUpdate(env, now);
expect(!r.started, "does not repeat an update GitHub started in the last 2 h");

fake([], 403);
r = await startUpdate(env, now);
expect(!r.started && /403/.test(r.reason), "reports a failed start");

r = await startUpdate({}, now);
expect(!r.started && /not set/.test(r.reason), "reports a missing token");
console.log(ok ? "all scheduler tests passed" : "scheduler tests FAILED");
process.exit(ok ? 0 : 1);
