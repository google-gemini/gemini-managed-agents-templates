// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * Approvals dashboard server for the refund-triage managed agent.
 *
 * This is the application side of the template: the agent runs in the Gemini
 * sandbox, but its custom functions execute HERE. issue_refund is simulated
 * against a mock payment system; escalate_to_human parks the call in a pending
 * queue until a reviewer clicks Approve / Deny / Investigate in the browser,
 * then the interaction continues via previous_interaction_id.
 *
 * The GEMINI_API_KEY never reaches the browser — the UI only talks to this
 * server, which is the same isolation you'd want in production.
 *
 * Run from client-web/:  npm install && GEMINI_API_KEY=... npm start
 */

import { serve } from "@hono/node-server";
import { serveStatic } from "@hono/node-server/serve-static";
import { Hono } from "hono";
import { streamSSE } from "hono/streaming";
import { execFile } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions";
const API_REVISION = "2026-05-20";
const PORT = Number(process.env.PORT ?? 8787);

// client-web/ lives inside the template; generate_payload.py expects to run
// with the template directory as cwd (it reads agent.yaml, skills/, workspace/).
const CLIENT_DIR = path.dirname(fileURLToPath(import.meta.url));
const TEMPLATE_ROOT = path.resolve(CLIENT_DIR, "..");
const PAYLOAD_SCRIPT = path.resolve(TEMPLATE_ROOT, "..", "generate_payload.py");

const API_KEY = process.env.GEMINI_API_KEY;
if (!API_KEY) {
  console.error("Error: GEMINI_API_KEY is not set.");
  process.exit(1);
}

const DEFAULT_PROMPT =
  "Process all pending refund requests: issue refunds for the ones policy " +
  "allows, and escalate the rest to me with your recommendation.";

// ---------------------------------------------------------------------------
// Event log + SSE fan-out. The full event history is replayed to late-joining
// browsers so a refresh never loses state.
// ---------------------------------------------------------------------------

interface DashboardEvent {
  id: number;
  type: string;
  at: string;
  data: Record<string, unknown>;
}

const events: DashboardEvent[] = [];
const subscribers = new Set<(event: DashboardEvent) => void>();
let nextEventId = 1;

function emit(type: string, data: Record<string, unknown> = {}): void {
  const event: DashboardEvent = {
    id: nextEventId++,
    type,
    at: new Date().toISOString(),
    data,
  };
  events.push(event);
  for (const notify of subscribers) notify(event);
  console.log(`[${event.at}] ${type}`, JSON.stringify(data).slice(0, 200));
}

// ---------------------------------------------------------------------------
// Interactions API plumbing (raw REST, mirroring probers.sh and the Python
// console so all three clients exercise the identical wire format).
// ---------------------------------------------------------------------------

interface ContentItem {
  type?: string;
  text?: string;
}

interface InteractionStep {
  type?: string;
  id?: string;
  call_id?: string;
  name?: string;
  arguments?: unknown;
  content?: ContentItem[];
}

interface Interaction {
  id: string;
  status?: string;
  environment_id?: string;
  steps?: InteractionStep[];
}

async function buildInitialPayload(prompt: string): Promise<Record<string, unknown>> {
  const { stdout } = await execFileAsync("python3", [PAYLOAD_SCRIPT, prompt], {
    cwd: TEMPLATE_ROOT,
    maxBuffer: 64 * 1024 * 1024,
    env: { ...process.env },
  });
  return JSON.parse(stdout) as Record<string, unknown>;
}

async function getInteraction(id: string): Promise<Interaction> {
  const response = await fetch(`${API_URL}/${id}`, {
    headers: { "x-goog-api-key": API_KEY!, "Api-Revision": API_REVISION },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Interactions API GET ${response.status}: ${body.slice(0, 2000)}`);
  }
  return (await response.json()) as Interaction;
}

/**
 * POST an interaction with streaming enabled and relay the agent's thought
 * summaries to the dashboard as they arrive — this is what makes the UI feel
 * alive during the long stretches where the agent is reading skills, running
 * triage, or deciding what to escalate next.
 *
 * Resolves with the final interaction object (completed, or paused with
 * "requires_action" when a custom function call needs a result from us).
 */
async function postInteraction(payload: Record<string, unknown>): Promise<Interaction> {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      "x-goog-api-key": API_KEY!,
      "Api-Revision": API_REVISION,
      "x-server-timeout": "600",
    },
    body: JSON.stringify({ ...payload, stream: true }),
  });
  if (!response.ok || !response.body) {
    const body = await response.text();
    throw new Error(`Interactions API ${response.status}: ${body.slice(0, 2000)}`);
  }

  let interactionId: string | undefined;
  let finalInteraction: Interaction | undefined;

  const handleStreamEvent = (data: string): void => {
    if (data === "[DONE]") return;
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(data) as Record<string, unknown>;
    } catch {
      return; // tolerate partial/keepalive frames
    }
    const interaction = parsed["interaction"] as Interaction | undefined;
    if (interaction?.id) {
      interactionId = interaction.id;
      // Terminal frames (completed / requires_action) carry the full steps.
      if (interaction.steps) finalInteraction = interaction;
    }
    const delta = parsed["delta"] as
      | { type?: string; content?: { text?: string } }
      | undefined;
    if (parsed["event_type"] === "step.delta" && delta?.type === "thought_summary") {
      const text = delta.content?.text?.trim();
      if (text) emit("agent_thinking", { text });
    }
  };

  // Minimal SSE parser: frames are separated by blank lines; we only need
  // the data: payloads.
  const decoder = new TextDecoder();
  let buffer = "";
  for await (const chunk of response.body) {
    buffer += decoder.decode(chunk as Uint8Array, { stream: true });
    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .join("\n");
      if (data) handleStreamEvent(data);
    }
  }

  if (finalInteraction) return finalInteraction;
  // The stream ended without a full terminal frame (e.g. transport hiccup):
  // fetch the authoritative state instead of guessing.
  if (interactionId) return getInteraction(interactionId);
  throw new Error("Stream ended without an interaction id.");
}

/**
 * Pending custom function calls awaiting a result from us. The steps also
 * contain the agent's built-in tool activity (read_file, code execution, ...)
 * as function_call/function_result PAIRS — only unpaired function_call steps
 * are ours, and only while the interaction is paused with "requires_action".
 */
function extractFunctionCalls(interaction: Interaction): InteractionStep[] {
  if (interaction.status !== "requires_action") return [];
  const steps = interaction.steps ?? [];
  const answered = new Set(
    steps.filter((s) => s.type === "function_result").map((s) => s.call_id),
  );
  return steps.filter((s) => s.type === "function_call" && !answered.has(s.id));
}

function extractText(interaction: Interaction): string {
  const parts: string[] = [];
  for (const step of interaction.steps ?? []) {
    if (step.type !== "model_output") continue;
    for (const item of step.content ?? []) {
      if (item.type === "text" && item.text) parts.push(item.text);
    }
  }
  return parts.join("\n");
}

function parseArguments(raw: unknown): Record<string, unknown> {
  if (typeof raw === "string") return JSON.parse(raw) as Record<string, unknown>;
  return (raw ?? {}) as Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// The application-controlled functions.
// ---------------------------------------------------------------------------

type Decision = "approve" | "deny" | "investigate";

interface PendingApproval {
  call: InteractionStep;
  args: Record<string, unknown>;
  resolve: (outcome: { decision: Decision; note: string }) => void;
}

const pendingApprovals = new Map<string, PendingApproval>();
let running = false;

function issueRefund(args: Record<string, unknown>): Record<string, unknown> {
  const result = {
    status: "success",
    confirmation_id: `PAY-${String(args["request_id"])}-OK`,
  };
  emit("refund_issued", {
    request_id: args["request_id"],
    order_id: args["order_id"],
    amount: args["amount"],
    reason: args["reason"],
    confirmation_id: result.confirmation_id,
  });
  return result;
}

async function escalateToHuman(
  call: InteractionStep,
  args: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const callId = call.id ?? `call-${nextEventId}`;
  const outcome = await new Promise<{ decision: Decision; note: string }>((resolve) => {
    pendingApprovals.set(callId, { call, args, resolve });
    emit("escalation_pending", {
      call_id: callId,
      request_id: args["request_id"],
      summary: args["summary"],
      recommendation: args["recommendation"],
      policy_flags: args["policy_flags"] ?? [],
    });
  });
  emit("decision_recorded", {
    call_id: callId,
    request_id: args["request_id"],
    decision: outcome.decision,
    note: outcome.note,
  });
  return { decision: outcome.decision, approver: "web-reviewer", note: outcome.note };
}

async function handleFunctionCall(call: InteractionStep): Promise<Record<string, unknown>> {
  let result: Record<string, unknown>;
  try {
    const args = parseArguments(call.arguments);
    if (call.name === "issue_refund") {
      result = issueRefund(args);
    } else if (call.name === "escalate_to_human") {
      result = await escalateToHuman(call, args);
    } else {
      result = { status: "error", message: `Unknown function: ${String(call.name)}` };
    }
  } catch (error) {
    result = { status: "error", message: String(error) };
  }
  return {
    type: "function_result",
    call_id: call.id,
    name: call.name,
    is_error: result["status"] === "error",
    result: [{ type: "text", text: JSON.stringify(result) }],
  };
}

// ---------------------------------------------------------------------------
// The run loop: create the interaction, execute function calls (escalations
// wait for the reviewer), continue with results until the agent is done.
// ---------------------------------------------------------------------------

async function runLoop(prompt: string): Promise<void> {
  emit("run_started", { prompt });
  try {
    const initialPayload = await buildInitialPayload(prompt);
    // Continuation requests must repeat the agent/model parameter.
    const agentParam: Record<string, unknown> = {};
    for (const key of ["agent", "model"]) {
      if (key in initialPayload) agentParam[key] = initialPayload[key];
    }
    let interaction = await postInteraction(initialPayload);
    for (;;) {
      const calls = extractFunctionCalls(interaction);
      if (calls.length === 0) break;
      // Parallel on purpose: several escalations can sit in the queue at once,
      // and the reviewer answers them in any order.
      const results = await Promise.all(calls.map(handleFunctionCall));
      interaction = await postInteraction({
        ...agentParam,
        previous_interaction_id: interaction.id,
        // Reuse the same sandbox so workspace state (audit log, triage
        // results) persists across the function-calling round-trips.
        environment: interaction.environment_id,
        input: results,
      });
    }
    emit("run_complete", { summary: extractText(interaction) });
  } catch (error) {
    emit("run_error", { message: String(error) });
  } finally {
    running = false;
    pendingApprovals.clear();
  }
}

// ---------------------------------------------------------------------------
// HTTP surface.
// ---------------------------------------------------------------------------

const app = new Hono();

app.post("/api/run", async (c) => {
  if (running) {
    return c.json({ error: "A run is already in progress." }, 409);
  }
  running = true;
  const body = await c.req.json().catch(() => ({}));
  const prompt =
    typeof body.prompt === "string" && body.prompt.trim() ? body.prompt.trim() : DEFAULT_PROMPT;
  // History is scoped to the current run: a fresh run starts a fresh feed,
  // and SSE replay reconstructs exactly this run for late-joining browsers.
  events.length = 0;
  void runLoop(prompt);
  return c.json({ ok: true, prompt });
});

app.post("/api/decide", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const callId = String(body.call_id ?? "");
  const decision = String(body.decision ?? "") as Decision;
  const note = typeof body.note === "string" ? body.note.trim() : "";
  if (!["approve", "deny", "investigate"].includes(decision)) {
    return c.json({ error: "decision must be approve, deny, or investigate" }, 400);
  }
  const pending = pendingApprovals.get(callId);
  if (!pending) {
    return c.json({ error: `No pending escalation with call_id ${callId}` }, 404);
  }
  pendingApprovals.delete(callId);
  pending.resolve({ decision, note });
  return c.json({ ok: true });
});

app.get("/api/events", (c) =>
  streamSSE(c, async (stream) => {
    // Replay history so a page refresh reconstructs the full dashboard.
    for (const event of events) {
      await stream.writeSSE({ id: String(event.id), event: "update", data: JSON.stringify(event) });
    }
    let open = true;
    const notify = (event: DashboardEvent) => {
      void stream
        .writeSSE({ id: String(event.id), event: "update", data: JSON.stringify(event) })
        .catch(() => {
          open = false;
        });
    };
    subscribers.add(notify);
    stream.onAbort(() => {
      open = false;
      subscribers.delete(notify);
    });
    while (open) {
      await stream.sleep(15000);
      await stream.writeSSE({ event: "ping", data: "" }).catch(() => {
        open = false;
      });
    }
    subscribers.delete(notify);
  }),
);

app.get("/api/state", (c) =>
  c.json({
    running,
    pending: [...pendingApprovals.entries()].map(([callId, approval]) => ({
      call_id: callId,
      request_id: approval.args["request_id"],
      recommendation: approval.args["recommendation"],
    })),
  }),
);

app.use("/*", serveStatic({ root: path.relative(process.cwd(), path.join(CLIENT_DIR, "public")) }));

serve({ fetch: app.fetch, port: PORT }, () => {
  console.log(`Refund triage approvals dashboard: http://localhost:${PORT}`);
  console.log(`Template root: ${TEMPLATE_ROOT}`);
});
