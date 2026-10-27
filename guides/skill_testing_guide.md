# Skill Testing Guide

Skills are process documentation that an agent must follow under pressure. This guide applies test-driven development to them: watch an agent fail without the change, write the change to close that failure, then confirm the agent complies. Use it for every new skill and for any change to an enforcement rule — a rationalization table, a gate, a verdict rule, a loop step.

`guides/skill_template.md` is the format contract; this guide is the method that shows a skill works.

## The Cycle

| TDD concept | Skill authoring |
|---|---|
| Write the test first | Write a **pressure scenario** and run it **before** changing the skill |
| Watch it fail (RED) | Run the scenario against an agent that lacks the change, and record its exact rationalizations verbatim |
| Write minimal code | Change the skill to address those specific violations, and nothing else |
| Watch it pass (GREEN) | Run the same scenario with the change and confirm the agent complies |
| Refactor | Look for new rationalizations, plug them, and re-run |

A change that was never watched failing is a guess about what the agent will do.

## Writing a Pressure Scenario

A scenario is a short, self-contained prompt that tempts the agent to break one rule. A scenario that only asks the agent to recite the rule tests recall, not compliance.

1. **Name the rule** under test, as one sentence.
2. **Build a realistic situation** with concrete artifacts — a task file, a diff, a Work Log, a failing output — small enough to paste into the prompt.
3. **Add pressure**: sunk cost ("I already wrote 200 lines"), authority ("the lead said to skip it"), fatigue ("this is the fifth retry"), or a plausible rationale that argues for the shortcut.
4. **Force a choice** the agent must make in its answer — a verdict, a command, a yes or no — so compliance is observable.
5. **Write the expected behavior** before running anything, in terms of what the answer must contain or avoid.

Author at least three scenarios per changed rule, varying the pressure. Keep them with the change (a report beside the guide it validated, or the PR description).

## Running It

- **Baseline (RED):** run each scenario with no skill, or with the skill as it was before your change. Record the answer and quote the rationalization the agent used.
- **With the change (GREEN):** run the same scenarios with the changed skill text supplied as the agent's instructions. Use the model the skill ships to; a skill that works on the most capable model may need more explicit step labels on a cheaper one.
- **Repeat** each run a few times. A single pass is an anecdote; compliance that appears in most runs is a signal.
- **Refactor:** every new rationalization the agent produces becomes a row in the skill's `## Rationalizations` table, and the scenario that surfaced it joins the set.

Headless runs work well for this: pass the scenario as the prompt and the skill body as appended system instructions, and read the text of the answer.

## Skill Discovery Wording

A description that summarizes the workflow gets followed instead of the skill: an agent reads the description, skips the body, and performs a shortened version of the process. The rule is:

> A `description` states **when to use** the skill — the triggering conditions — and at most one clause of **what it is for**. It never lists the steps.

Test discovery with scenarios too: one request the skill should trigger on, and one adjacent request it should not.

## Recording Results

For each validated change, keep a short report with the scenarios, the baseline answers (with the rationalizations quoted), the with-change answers, the number of runs, the model used, and any scenario that still fails. A change whose scenarios still fail is not finished; either strengthen the wording or move the rule earlier in the procedure.

## Checklist

- [ ] The rule under test is stated in one sentence.
- [ ] At least three scenarios with different pressure, expected behavior written first.
- [ ] Baseline run recorded, with rationalizations quoted verbatim.
- [ ] The skill change addresses those rationalizations specifically.
- [ ] With-change runs recorded; remaining failures are either fixed or listed.
- [ ] New rationalizations added to the skill's table.
