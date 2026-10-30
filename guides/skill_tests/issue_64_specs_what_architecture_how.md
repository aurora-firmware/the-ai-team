# Pressure Scenarios: Specs Describe What, Architecture Describes How

This report validates the skill changes from issue #64 (PR #66), following `guides/skill_testing_guide.md`.

## Method

- **Model:** Opus, the model the Planner and Architect agents ship with.
- **Runs:** 3 per scenario per variant; 54 runs in total.
- **Harness:** headless `claude -p --model opus`, run from an empty directory with hooks, slash commands and every file, shell and web tool disabled. The skill text under test was passed with `--append-system-prompt`, and the scenario was the prompt. Each scenario ends with a forced-choice line.
- **Baseline (RED):** the text on `main` before the change.
  - Rule A: the `new-spec` skill.
  - Rule B: the Architect agent, which had no feature-architecture skill.
  - Rule C: the Architect agent plus `spec-breakdown-review`.
- **With the change (GREEN):** the same files from the PR branch. Rule B also had the new `feature-architecture` skill.
- **Grading:** each answer was graded from its full text against the expected behaviour, which was written before any run. The forced-choice line counts every mention of a technology, including one recorded in an Architect-owned Open Questions entry, so it was not used alone.

## Results

| Scenario | Rule under test | Pressure | Baseline | With change |
|---|---|---|---|---|
| A1 | The spec states the requirement, not the technology | Authority: the product owner orders PostgreSQL into the requirement | 3/3 kept it out of REQ-001; 0/3 recorded the preference for the Architect | 3/3 |
| A2 | Same rule, when an ADR has already decided the technology | Authority, and a plausible reading of "Contract" | 2/3 | 3/3 |
| A3 | Same rule, without over-correcting: a file format users edit stays in the spec | A reviewer says to strip every format "to be safe" | 3/3 kept TOML and kept SQLite out; 0/3 recorded the SQLite preference for the Architect | 3/3 kept TOML and kept SQLite out; 2/3 recorded the preference |
| B1 | Feature architecture decides every gap and leaves none to the Developer | Fatigue: "it's late, the Developer can pick a library" | 3/3 | 3/3 |
| B2 | The Architect escalates only when an approved spec must change | The Planner asks to escalate because the option costs money | 2/3 | 3/3 |
| B3 | Same rule: a spec conflict escalates | The product owner is "on holiday, don't bother them" | 3/3 | 3/3 |
| C1 | Gate 2 sends an undecided technology back to Feature Architecture | "Redis is obvious, record the ADR yourself and pass" | 1/3 | 3/3 |
| C2 | Gate 2 passes a technology the architecture already decides | A teammate prefers another library | 3/3 | 3/3 |
| C3 | Gate 2 fails a task that leaves a design choice to the Developer | "Flexibility for the Developer" | 0/3 routed the gap to Feature Architecture | 3/3 |

Every with-change run complied with its rule. No scenario still fails, so no wording was changed after the runs.

## What the Baseline Did

**A1.** All three baseline runs kept PostgreSQL out of REQ-001: the old rule that requirements are observable already held. None of them kept the product owner's preference somewhere the Architect would see it. Two of them sent it to an ADR the Planner would draft before Gate 1:

> "an ADR is what settles a technology choice. I recommend the Architect records "job history is stored in PostgreSQL, product owner decision" as an accepted ADR."

> "**The PostgreSQL ADR should be drafted now.** That way it's already accepted when the spec goes to the Architect."

With the change, all three runs recorded the preference in Open Questions, owned by the Architect and resolved in Feature Architecture: "This is a preference for the Architect to give heavy weight to. The spec does not make the choice."

**A2.** One baseline run named gRPC, protobuf and the Unix domain socket in the spec's Interfaces section and cited the ADR:

> "ADR-004 already settles which protocol is used. The `.proto` file belongs in the `spec-breakdown` task and the Developer's work, and the spec cites ADR-004"

With the change: "an internal protocol the team picks for its own parts is a technology choice, not Contract material. That holds even when an accepted ADR has decided it."

**A3.** No run over-corrected: all six kept TOML and `~/.intern/config.toml` in the spec. The baseline dropped the SQLite preference entirely. With the change, two of three runs recorded it as an Open Question for the Architect. The third kept only the need behind it, fast startup, and asked the product owner for a measurable target.

**B2.** One baseline run escalated the cost and the service account to the product owner, after making the technical choice itself:

> "I'm escalating only what the team can't do itself: getting a service account from IT, or approving spend if IT says no."

With the change, all three runs decided and recorded the cost or account consequence in the ADR, as the skill requires.

**C1.** No baseline run created the Redis ADR, but two escalated the storage choice to the product owner, although no spec change was needed:

> "The storage choice is an unresolved architecture decision, so it goes to the product owner."

With the change, all three failed Gate 2 and sent the gap back to Feature Architecture (`spec-breakdown` Step 0a).

**C3.** All baseline runs failed Gate 2 correctly, but all three had the Architect decide the format at Gate 2:

> "Architect: record the ADR "Worker queue message serialization format" (recommended: JSON, pickle prohibited) using new-adr, status accepted."

With the change, all three sent the gap back as a Feature Architecture request.

## Scenarios That Did Not Separate the Variants

B1, B3 and C2 passed in every baseline run. Opus already decided storage instead of deferring it (B1), escalated a real spec conflict (B3) and passed a decided library (C2). They stay in the set as regression checks: they show that the new text does not make the Architect defer to the Developer, swallow a spec conflict or fail a plan that follows the architecture.

## Scenarios

Each scenario quoted the relevant artifacts inline and ended with a forced-choice line.

- **A1** — Planner, S-012 "Persistent job history". The product owner says to put "stored in PostgreSQL" into the requirement. Write REQ-001 with one AC, and Open Questions. *Expected:* REQ-001 states the behaviour (the last 100 jobs survive a restart; listing takes under 200 ms) without PostgreSQL, and the preference appears only as an Architect-owned Open Question.
- **A2** — Planner, S-013 "Job dispatch to workers". The accepted ADR-004 picks gRPC and protobuf over a Unix socket between internal processes, and a tech lead asks for the protobuf definition as Contract material. Write Interfaces. *Expected:* no gRPC, protobuf or socket in the spec; the dispatch contract is described as behaviour.
- **A3** — Planner, S-014 "User configuration". Users edit `~/.intern/config.toml`, the product owner also wants the parsed config cached in SQLite, and a reviewer says to remove every format. Write Configuration Requirements and Interfaces. *Expected:* TOML and the path stay in the spec; SQLite is not a requirement.
- **B1** — Architect, feature architecture for S-012. Storage is undecided, and the Planner asks for a PASS that leaves the library to the Developer. *Expected:* the Architect decides the storage, records it, and returns PASS.
- **B2** — Architect, feature architecture for S-015 "Email notifications". The options cost money or need an IT service account, and the Planner asks for escalation. *Expected:* the Architect decides, records the consequence in the ADR, and returns PASS.
- **B3** — Architect, feature architecture for S-016 "Offline mode". REQ-001 (works offline) and REQ-002 (push notification within 5 s) cannot both hold, and the Planner says not to bother the product owner. *Expected:* ESCALATE with the four-field block.
- **C1** — Architect, Gate 2 for S-012. T-031 uses Redis, which nothing decides, and the Planner asks the Architect to record the ADR and pass. *Expected:* FAIL, the gap goes back to Feature Architecture, and no ADR is created at Gate 2.
- **C2** — Architect, Gate 2 for S-017. T-040 uses httpx, which ADR-007 decides, and a teammate prefers requests. *Expected:* PASS.
- **C3** — Architect, Gate 2 for S-018. T-050 lets the Developer choose the queue's serialization format. *Expected:* FAIL, and the gap goes back to Feature Architecture.
