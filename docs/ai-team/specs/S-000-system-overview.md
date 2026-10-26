---
id: S-000
title: System Overview
version: '0.4'
status: approved  # draft | review | approved | superseded
created: '2026-10-22'
author: planner
---

# System Overview

<!--
This is the system overview spec (S-000): one plain-language document that
says what the project is, who it serves, and which components make it up.
Write for a reader who has never seen the project. Do not include technology
choices, interface definitions, configuration, implementation order, or
per-component status. Those belong in feature specs, ADRs, and the tracker.
Boundary rule: S-000 owns the decomposition — which components exist and
what each is for. A spec owns the contract of one component or feature.
-->

## Purpose

The AI Team Definition is a reusable framework that lets a team of AI agents build and maintain software in a project autonomously. It defines the rules the agents follow (how work is planned, implemented, reviewed, integrated and approved) and installs those rules into any project in one step, together with the agent roles and procedures that carry them out and the tooling that supports them. With the framework in place, the product owner hands feature work and bug fixes to the agents and gets back changes that have been tested, reviewed and integrated, along with a clear record of what was decided and why.

## Users

- **Product Owner.** A human responsible for a project that adopts the framework. The product owner sets the framework up, describes the system and the features or changes they want, approves specifications and releases, starts the autonomous work, and answers escalations. The product owner needs to stay in control of the important decisions without supervising every step, and to see the state of the work at a glance.
- **AI agents.** The planning, architecture, development, review and integration roles that do the work inside an adopting project. Each agent needs unambiguous rules and step-by-step procedures for its role, clear handoffs to the next role, and a reliable way to read and change the project's work items without guessing.

## Pain points

- **Unguided agents improvise.** Without shared rules, AI agents plan, implement and review inconsistently, skip tests or reviews, and declare work done without evidence.
- **All-or-nothing oversight.** The product owner either supervises every agent step or loses track of what was decided, by whom, and why.
- **Blocked or broken work goes unnoticed.** When an agent is stuck or a change breaks something that used to work, nothing tells it where to escalate or how to record and fix the problem, so work stalls or degrades without anyone noticing.
- **Agents guess project specifics.** Agents do not know a project's own build, test and run commands or conventions, so they invent them or stop.
- **Setup is manual and drifts.** Setting up an agent team means copying role and procedure definitions by hand into every project and for every agent tool. The copies drift from each other and from the rules they are meant to follow.
- **Inconsistent work artifacts.** Specifications, tasks, bug reports and decisions are written in a different shape each time, so agents misread them and reviews miss gaps.
- **Work state is scattered.** What is planned, in progress, blocked or done is spread across files and history. Neither the product owner nor the agents can see it reliably, and the bookkeeping clutters the project's history.

## Use cases

- **Adopt the framework.** The product owner runs one setup step in their project and gets the roles, procedures, artifact layout and starter project guidance in place. Removes: setup is manual and drifts.
- **Keep the framework current.** The product owner updates the project to a newer framework version. The delivered roles and procedures are replaced without touching the project's own content, and a layout check reports anything out of place with a suggested fix. Removes: setup is manual and drifts.
- **Teach agents the project's specifics.** The product owner records the project's build, test and run commands and conventions in the project guidance, and every agent reads them from there instead of guessing. Removes: agents guess project specifics.
- **Describe the system.** The product owner and the planning agent write one plain-language overview of the project (its purpose, users, pain points and components), which every later specification is checked against. Removes: inconsistent work artifacts; all-or-nothing oversight.
- **Bootstrap the project.** Once the overview is approved, the planning agent turns its open technology questions into setup tasks. The agents set up the development environment, record the technology decisions, write the coding guidelines and the project guidance, and describe the project in its readme, before any feature is built. Removes: agents guess project specifics.
- **Plan a feature.** The product owner describes a feature. The planning agent explores options with the product owner and writes a specification, the product owner approves it, the planning agent breaks it into small independent tasks, and the architecture agent checks the plan before any work starts. Removes: unguided agents improvise; all-or-nothing oversight.
- **Request a small change.** The product owner asks for a change that is too small for a full specification. The planning agent records it as a change request and turns it into tasks or a specification amendment after an architecture check. Removes: all-or-nothing oversight.
- **Run the development loop.** The product owner starts the loop. The agents implement, review and integrate each pending task in turn, with tests and evidence, and stop only when the queue is empty, a task is blocked, or a question needs the product owner. Removes: unguided agents improvise; all-or-nothing oversight.
- **Fix bugs.** A defect is found by the product owner or by an agent during integration and recorded as a bug. The product owner starts the bug-fix loop, which diagnoses each bug before changing anything, then fixes, reviews and integrates it. Removes: blocked or broken work goes unnoticed.
- **Resolve a blocked item.** An agent that cannot continue escalates to the architecture agent, which either unblocks it or brings the product owner one precise question. Removes: blocked or broken work goes unnoticed; all-or-nothing oversight.
- **Work an item through its lifecycle.** An agent claims a task or bug, records its work log and review verdict, and moves the item to its next state through the framework's commands, without editing files by hand or adding bookkeeping to the project's history. Removes: work state is scattered; inconsistent work artifacts.
- **Check the state of the work.** The product owner asks for the current state and gets a summary of specifications, tasks, bugs and blocked items, and, on request, a written report. Removes: work state is scattered.
- **Approve a release.** When the queues are empty, the product owner reviews the integrated work and its report and approves moving it to the project's main line. Removes: all-or-nothing oversight.

## Solution overview

The framework separates *what must happen* from *how it is carried out*. A single set of process rules defines the lifecycle of every kind of work, the quality gates it passes through, who may approve each gate, and how blocked work escalates. Two gates belong to the product owner: approving a specification before it is broken into tasks, and approving integrated work before it reaches the main line. Everything between those gates runs without the product owner, and the agents stop and ask only when the rules say they must.

The rules are carried out by five agent roles (planning, architecture, development, review and integration) and by step-by-step procedures that each role follows. The procedures require evidence before any claim that work is complete, a diagnosis before any bug fix, and a review before any merge. Agents never read or change work state by hand. They use the framework's commands, which create every artifact from a fixed template, enforce the allowed lifecycle moves, and keep tasks, bugs and change requests in a local tracker outside the project's history. Specifications and decisions stay with the project, because they are design documents reviewed alongside the code.

Each role and procedure is written once and installed in the form the supported agent tool reads, so every project gets the same copy. A single setup step installs these definitions, the artifact layout and starter project guidance into a project, and the same step brings an existing project up to a newer version. The project supplies its own commands and conventions in that guidance, so the framework never assumes how a project is built or tested. Documentation for people explains how to install, configure and use the framework.

Around the delivered software sits the project's development infrastructure: the environment the framework is developed in, the tools that test and check it, the pipelines that check every change and produce releases, and the internal documentation that tells developers how to write the delivered roles and procedures. None of it reaches an adopting project, but it decides how the software is built, checked and delivered.

## Components

The components fall into two groups. The **solution** is the software delivered to the user: ai-team, a single piece of software that removes the pain points above. The **development infrastructure** is everything the project needs to build, check, document and deliver that software; it is not delivered to the user. Each infrastructure component lists the decisions it needs. Those decisions are answered and recorded in the project's internal development documentation by the tasks that follow S-000's approval, not in S-000 itself.

### Solution: ai-team

#### Team definition

- **Name:** Team definition
- **Responsibility:** The content of the agent team: the process rules (the lifecycle of every kind of work, the quality gates and who approves each, the escalation path, and the standards for code, history and documents), the agent roles that carry them out, and the step-by-step procedures each role follows.
- **Boundary:** Does not produce the files installed into a project, which Generators do, and is not delivered to the user as documentation. It does not store or move work items.
- **Works with:** Generators, CLI, Internal documentation.

#### Generators

- **Name:** Generators
- **Responsibility:** Produces every file the framework hands to a project: the agent and skill files for the supported agent tool, generated from the single Team definition source; the artifact layout and starter project guidance; and the fixed templates for each artifact kind (system overview, specification, task, bug report, decision record, change request and status report).
- **Boundary:** Does not author role or procedure content, does not track or move artifacts through their lifecycle, and never writes a project's own commands.
- **Works with:** Team definition, CLI, CI pipelines.

#### CLI

- **Name:** CLI
- **Responsibility:** The single command interface that people and agents use, built for autonomous use by agents. It installs the framework into a project and keeps it current, checks a project's layout, and creates, lists, shows, validates and moves artifacts through their lifecycle. It keeps tasks, bugs and change requests in a local tracker outside the project's history, enforces the allowed lifecycle moves and the special rules for the system overview, and summarises the state of the work.
- **Boundary:** Does not define the process, roles or procedures; does not decide what to build or run the agents and loops; and does not overwrite a project's own content without consent.
- **Works with:** Generators, Team definition, End-user documentation.

#### End-user documentation

- **Name:** End-user documentation
- **Responsibility:** Explains ai-team to the people who adopt it: what it is, how to install it, set it up and customise it for a project, and how to use each command, including a command reference kept in step with the CLI.
- **Boundary:** Does not include the process description or the role and procedure content, and is not the source agents follow.
- **Works with:** CLI, CI pipelines.

### Development infrastructure

#### Development environment

- **Name:** Development environment
- **Responsibility:** Everything a developer, human or agent, needs to build and run the solution from a fresh checkout: the language and its runtime, the reproducible environment and its settings, the project's framework settings, the files kept out of version control, and the remote repository. A remote is required; access to it is confirmed by checking that the remote has a branch.
- **Boundary:** Does not check or test changes and does not produce releases.
- **Works with:** Test tooling, CI pipelines, Internal documentation.
- **Decisions needed:** Which language and version is the solution written in? How is the development environment reproduced on a new machine? Which settings or environment values does it need? Which remote hosts the repository?

#### Test tooling

- **Name:** Test tooling
- **Responsibility:** The tools that check the solution: the test harness, the formatter and the linter, and the single way each is run locally.
- **Boundary:** Does not decide when checks run automatically, which CI pipelines do.
- **Works with:** Development environment, CI pipelines, Internal documentation.
- **Decisions needed:** Which test harness is used? Which formatting and lint rules apply? Which command runs each check, and which checks must pass before work is complete?

#### CI pipelines

- **Name:** CI pipelines
- **Responsibility:** Runs the checks automatically on every proposed change and on the main line, confirms that generated files and the command reference are current, and builds and publishes a versioned release when a version is tagged.
- **Boundary:** Does not decide when to release or what goes into a release, and does not run inside adopting projects.
- **Works with:** Test tooling, Development environment, Generators, End-user documentation.
- **Decisions needed:** Which service runs the pipelines, and on which runners? Which checks block a merge? What does a release contain, and where is it published?

#### Internal documentation

- **Name:** Internal documentation
- **Responsibility:** Tells the people and agents developing ai-team how to work on it: the authoring contracts for writing the delivered roles, procedures, specifications and system overview; coding guidelines; the project rules and commands agents read first; the readme; the maintainer notes; and the recorded answers to every infrastructure decision above.
- **Boundary:** Is not delivered to adopting projects and does not replace the Team definition it explains how to write.
- **Works with:** Team definition, Development environment, Test tooling.
- **Decisions needed:** Where do the architecture and technology choices live, and who keeps them current?

## Project exclusions

- **Project-specific commands.** Each adopting project supplies its own build, test, deploy and run commands, because the framework cannot know them.
- **Technology choices for adopting projects.** The framework governs how work is done, not what it is built with.
- **Running the agents.** The framework relies on existing agent tools to host and run agents; it only defines what they do.
- **A shared or remote work-item tracker.** Work items are tracked locally for now; a shared backend is deferred to a later phase.
- **Deploying or operating the software that adopting projects build.** The framework stops when work is approved onto the project's main line.
- **The copy of ai-team installed in this repository.** The project develops ai-team with ai-team, installed like in any adopting project; that installed copy is local configuration and is neither delivered nor part of the development infrastructure.

## Amendment Log

| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| 2026-10-24 | Use cases: added "Bootstrap the project". Driven by CR-004 item 9 and its Architecture Consistency Review. | CR-004 adds the project bootstrap after S-000 approval, a capability no use case covered. | None in flight |
| 2026-10-25 | Use cases, Solution overview and Generators: the framework supports one agent tool, so setup no longer asks which tools to use and definitions are not turned into one form per tool. Driven by CR-007 and ADR-003. | Codex support was dropped; Claude is the only export target. | None in flight |
| 2026-10-26 | Development environment: a remote repository is required, and access is confirmed by checking that the remote has a branch; the Decisions needed no longer ask how access is confirmed. Decided by the product owner while processing the T-179 handoff. | The project is brownfield; the remote access check only needs to confirm a remote branch exists. | None in flight |
