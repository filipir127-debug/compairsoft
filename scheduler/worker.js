// CompAirsoft scheduler: a Cloudflare Worker whose cron trigger starts the GitHub Actions update
// (crawl prices, cache photos, translate, publish). GitHub's own schedule is often hours late or
// skipped; Cloudflare's cron fires on time. No public address: it only has a scheduled() handler.
//
// Secret GH_TOKEN: a fine-grained GitHub token for filipir127-debug/compairsoft with
// "Actions: Read and write". Set it in the Cloudflare dashboard (Workers & Pages >
// compairsoft-scheduler > Settings > Variables and Secrets), never in this file.

const REPO = "filipir127-debug/compairsoft";
const WORKFLOW = "update.yml";
const CRAWL_MINUTES = "220"; // crawl + photos (40) + translations (40) must fit GitHub's 6 h job limit

function github(env, path, init = {}) {
  return fetch(`https://api.github.com/repos/${REPO}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "compairsoft-scheduler",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
    },
  });
}

export async function startUpdate(env, now = Date.now()) {
  if (!env.GH_TOKEN) return { started: false, reason: "GH_TOKEN secret is not set" };
  const list = await github(env, `/actions/workflows/${WORKFLOW}/runs?per_page=20`);
  if (!list.ok) return { started: false, reason: `listing runs failed: HTTP ${list.status} ${(await list.text()).slice(0, 200)}` };
  const runs = (await list.json()).workflow_runs.filter((r) => r.event === "schedule" || r.event === "workflow_dispatch");
  const busy = runs.find((r) => r.status !== "completed");
  if (busy) return { started: false, reason: `an update is already ${busy.status} (run ${busy.id})` };
  // GitHub's backup schedule already fired for this slot
  const recent = runs.find((r) => now - Date.parse(r.run_started_at || r.created_at) < 2 * 3600 * 1000);
  if (recent) return { started: false, reason: `an update started at ${recent.run_started_at || recent.created_at}` };
  const res = await github(env, `/actions/workflows/${WORKFLOW}/dispatches`, {
    method: "POST",
    body: JSON.stringify({ ref: "master", inputs: { crawl_minutes: CRAWL_MINUTES } }),
  });
  if (res.status !== 204) return { started: false, reason: `starting failed: HTTP ${res.status} ${(await res.text()).slice(0, 200)}` };
  return { started: true, reason: "update workflow started" };
}

export default {
  async scheduled(controller, env, ctx) {
    const result = await startUpdate(env);
    (result.started ? console.log : console.warn)(`[scheduler] ${result.reason}`);
    if (!result.started && /failed|not set/.test(result.reason)) throw new Error(result.reason); // shows as a failed cron run
  },
};
