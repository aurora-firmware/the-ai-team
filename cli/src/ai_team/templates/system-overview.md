---
id: "S-000"
title: "[Specification Title]"
version: "0.1"
status: draft  # draft | review | approved | superseded
created: YYYY-MM-DD
author: "[Author name or agent role]"
---

# [Specification Title]

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

<!-- Recipe: one short paragraph. What the project is and the outcome it
  exists to deliver. -->

What is this project, and what outcome does it exist to deliver?

## Users

<!-- Recipe: one line per kind of user, naming the situations they use the
  system in and what each needs from it. -->

- **User kind.** In what situations this user works with the system and what they need from it.

## Pain points

<!-- Recipe: the concrete problems those users have today that the project
  removes. -->

- The concrete problem a user has today.

## Use cases

<!-- Recipe: the main things a user does with the system, each as one short
  scenario from the user's point of view and each tied to the pain point it
  removes. -->

- **Use case title.** One short scenario from the user's point of view. Removes: the pain point it addresses.

## Solution overview

<!-- Recipe: a few paragraphs on how the system addresses the pain points,
  without naming technologies. -->

How does the system address the pain points above?

## Components

<!-- Recipe: the parts the system is divided into. A component is a part of
  the software solution, or something that affects the solution's use,
  delivery or deployment: software, documentation, delivery and deployment,
  or tooling. Each passes three checks: it serves at least one use case (or,
  in the infrastructure group, affects the solution's use, delivery or
  deployment); one spec could own its contract; its boundary would hold if
  the implementation were reorganised. Each entry gives its name, its owned
  responsibility (what it is for), its boundary (what it is not responsible
  for), and the other components it works with. Development infrastructure
  entries also carry Decisions needed: questions to answer before
  development starts. S-000 asks them and never answers them. S-000 owns the
  decomposition; a feature spec owns the contract of one component. -->

### Solution

<!-- The software delivered to the end user that removes the pain points. -->

#### Component name

- **Name:** The component's name.
- **Responsibility:** What the component is for.
- **Boundary:** What the component is not responsible for.
- **Works with:** The other components it works with.

### Development infrastructure

<!-- Everything the project needs to build, check, document and deliver the
  solution; not delivered to the end user. -->

#### Component name

- **Name:** The component's name.
- **Responsibility:** What the component is for.
- **Boundary:** What the component is not responsible for.
- **Works with:** The other components it works with.
- **Decisions needed:** The questions to answer before development starts, such as the language and version or the test harness.

## Project exclusions

<!-- Recipe: what the project deliberately does not do, each with a one-line
  reason. -->

- **Exclusion title.** One-line reason the project does not do this.

## Amendment Log

<!-- Optional. Use when an approved spec is amended after tasks are in flight.
| Date | What changed | Why | Affected tasks |
|------|-------------|-----|----------------|
| YYYY-MM-DD | Description of change | Reason for amendment | T-XXX, T-YYY |
-->
