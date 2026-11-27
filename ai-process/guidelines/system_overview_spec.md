# System Overview Spec (S-000)

S-000 is the canonical project-overview spec: one document that says what the project is, who it serves, and which components make it up. It is written in plain language for a reader who has never seen the project. It has seven sections, in this order:

1. **Purpose** — one short paragraph: what the project is and the outcome it exists to deliver.
2. **Users** — the users of the solution and in what situations, one line per kind of user, naming what each needs from it.
3. **Pain points** — the concrete problems those users have today that the project removes.
4. **Use cases** — the main things a user does with the system, each as one short scenario from the user's point of view and each tied to the pain point it removes.
5. **Solution overview** — how the system addresses the pain points, in a few paragraphs, without naming technologies.
6. **Components** — the parts the system is divided into. Each component entry gives its name, its owned responsibility (what it is for), its boundary (what it is not responsible for), and the other components it works with. Components are split into the Solution and Development infrastructure groups (below).
7. **Project exclusions** — what the project deliberately does not do, each with a one-line reason.

S-000 contains no technology choices, interface definitions, configuration, implementation order, or per-component status. Interface definitions, configuration, and implementation order belong in feature specs; technology choices in the architecture documents and ADRs; per-component status in the tracker.

**What a component is.** A component is a part of the software solution, or something that affects the solution's use, delivery or deployment. A component can be software, documentation (internal or for end users), delivery and deployment (pipelines, scripts), or tooling (development environment, debugging interfaces, test harnesses). Each component passes three checks: it serves at least one use case, or, in the infrastructure group, affects the solution's use, delivery or deployment; one spec could own its contract; and its boundary would hold if the implementation were reorganised.

**Component groups.** Components fall into two groups, written as `### Solution` and `### Development infrastructure` subsections of Components; the seven top-level sections and their order do not change.

- **Solution** — the software delivered to the end user that removes the pain points.
- **Development infrastructure** — everything the project needs to build, check, document and deliver the solution; it is not delivered to the end user. Each infrastructure component also has a **Decisions needed** field: the questions that must be answered before development starts, such as the language and version, how the environment is reproduced, the test harness, the continuous-integration service, and where decisions are recorded. S-000 asks technology questions and never answers them; the answers belong in the project's architecture documents and ADRs, which the project bootstrap writes.

**Users scope.** Users names the users of the solution. The people and agents who develop the project are served by the development infrastructure and are not listed unless they also use the solution.

**Boundary rule:** S-000 owns the decomposition — which components exist and what each is for. A spec owns the contract of one component or feature. A spec's Purpose names the S-000 component it covers when an S-000 exists.
