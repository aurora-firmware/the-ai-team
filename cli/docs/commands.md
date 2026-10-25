<!-- GENERATED FILE — do not edit by hand.
     Regenerate with: bash cli/scripts/gen_docs.sh -->

# `ai-team`

Manage AI-team artifacts: specs, tasks, bugs, and ADRs.

**Usage**:

```console
$ ai-team [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-V, --version`: Print the ai-team version and exit.
* `--help`: Show this message and exit.

**Commands**:

* `adr`: Create and manage ADR artifacts.
* `archive`: Archive old completed tasks and resolved...
* `bug`: Create and manage bug artifacts.
* `change-request`: Create and manage change-request artifacts.
* `check-layout`: Check the repository layout and report...
* `init`: Scaffold an AI-team repository.
* `list`: List tasks, bugs, specs, ADRs, and change...
* `report`: Write a Gate 5 progress report.
* `show`: Show an artifact by identifier.
* `spec`: Create and manage specification artifacts.
* `status`: Show a Gate 5 status summary.
* `task`: Create and manage task artifacts.
* `tracker`: Inspect the local work-item tracker.
* `validate`: Validate artifact metadata and...

## `ai-team adr`

Create and manage ADR artifacts.

**Usage**:

```console
$ ai-team adr [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `new`: Create a new ADR artifact from the bundled...

### `ai-team adr new`

Create a new ADR artifact from the bundled template.

**Usage**:

```console
$ ai-team adr new [OPTIONS] TITLE
```

**Arguments**:

* `TITLE`: [required]

**Options**:

* `--status [proposed|accepted|superseded]`: [default: proposed]
* `--supersedes TEXT`
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

## `ai-team archive`

Archive old completed tasks and resolved bugs into the tracker&#x27;s archive/YYYY-MM/.

**Usage**:

```console
$ ai-team archive [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--older-than TEXT`: [default: 90d]
* `--dry-run`
* `--help`: Show this message and exit.

## `ai-team bug`

Create and manage bug artifacts.

**Usage**:

```console
$ ai-team bug [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `new`: Create a new open bug in the tracker from...
* `start`: Set an open bug to in-progress.
* `resolve`: Set an in-progress bug to resolved.
* `set-status`: Set a bug to any allowed status.

### `ai-team bug new`

Create a new open bug in the tracker from the bundled template.

**Usage**:

```console
$ ai-team bug new [OPTIONS] TITLE
```

**Arguments**:

* `TITLE`: [required]

**Options**:

* `--severity [critical|high|medium|low]`: [default: medium]
* `--task TEXT`
* `--source-branch TEXT`: Branch that introduced a task regression; omit for existing defects.
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

### `ai-team bug start`

Set an open bug to in-progress.

**Usage**:

```console
$ ai-team bug start [OPTIONS] BUG_ID
```

**Arguments**:

* `BUG_ID`: [required]

**Options**:

* `--help`: Show this message and exit.

### `ai-team bug resolve`

Set an in-progress bug to resolved.

**Usage**:

```console
$ ai-team bug resolve [OPTIONS] BUG_ID
```

**Arguments**:

* `BUG_ID`: [required]

**Options**:

* `--help`: Show this message and exit.

### `ai-team bug set-status`

Set a bug to any allowed status.

**Usage**:

```console
$ ai-team bug set-status [OPTIONS] BUG_ID STATUS:{open|in-progress|resolved}
```

**Arguments**:

* `BUG_ID`: [required]
* `STATUS:{open|in-progress|resolved}`: One of: open, in-progress, resolved  [required]

**Options**:

* `--reason TEXT`: Recorded as a Work Log entry.
* `--help`: Show this message and exit.

## `ai-team change-request`

Create and manage change-request artifacts.

**Usage**:

```console
$ ai-team change-request [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `new`: Create a new change-request in the tracker...
* `set-status`: Set a change-request to pending, approved,...

### `ai-team change-request new`

Create a new change-request in the tracker from the bundled template.

**Usage**:

```console
$ ai-team change-request new [OPTIONS] TITLE
```

**Arguments**:

* `TITLE`: [required]

**Options**:

* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

### `ai-team change-request set-status`

Set a change-request to pending, approved, or rejected.

**Usage**:

```console
$ ai-team change-request set-status [OPTIONS] CR_ID STATUS:{pending|approved|rejected}
```

**Arguments**:

* `CR_ID`: [required]
* `STATUS:{pending|approved|rejected}`: One of: pending, approved, rejected  [required]

**Options**:

* `--help`: Show this message and exit.

## `ai-team check-layout`

Check the repository layout and report actionable findings.

**Usage**:

```console
$ ai-team check-layout [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

## `ai-team init`

Scaffold an AI-team repository.

**Usage**:

```console
$ ai-team init [OPTIONS] [PATH] COMMAND [ARGS]...
```

**Arguments**:

* `[PATH]`: [default: .]

**Options**:

* `--tools TEXT`
* `--force`
* `--dry-run`
* `--no-interactive`
* `--create-root-guidance`
* `--update-docs`: On an upgrade, update the ai-team docs without asking.
* `--update-skills`: On an upgrade, update the agents and skills without asking.
* `--project-dir TEXT`: Artifact folder, at any depth (default: the configured one, else &#x27;ai-team&#x27;).
* `--integration-branch TEXT`: Branch work integrates into (default: the configured one, else &#x27;dev-agent&#x27;).
* `--help`: Show this message and exit.

## `ai-team list`

List tasks, bugs, specs, ADRs, and change requests.

**Usage**:

```console
$ ai-team list [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `tasks`: List tasks from the tracker.
* `bugs`: List bugs from the tracker.
* `specs`: List specs from the project specs folder.
* `adrs`: List ADRs from the project decisions folder.
* `change-requests`: List change requests from the tracker.

### `ai-team list tasks`

List tasks from the tracker.

**Usage**:

```console
$ ai-team list tasks [OPTIONS]
```

**Options**:

* `--state TEXT`: Filter by task status.
* `--spec TEXT`: Filter by source spec or change-request ID.
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

### `ai-team list bugs`

List bugs from the tracker.

**Usage**:

```console
$ ai-team list bugs [OPTIONS]
```

**Options**:

* `--state TEXT`: Filter by bug status.
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

### `ai-team list specs`

List specs from the project specs folder.

**Usage**:

```console
$ ai-team list specs [OPTIONS]
```

**Options**:

* `--state TEXT`: Filter by spec status.
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

### `ai-team list adrs`

List ADRs from the project decisions folder.

**Usage**:

```console
$ ai-team list adrs [OPTIONS]
```

**Options**:

* `--state TEXT`: Filter by ADR status.
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

### `ai-team list change-requests`

List change requests from the tracker.

**Usage**:

```console
$ ai-team list change-requests [OPTIONS]
```

**Options**:

* `--state TEXT`: Filter by change-request status.
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

## `ai-team report`

Write a Gate 5 progress report.

**Usage**:

```console
$ ai-team report [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--out PATH`: Override destination path.
* `--help`: Show this message and exit.

## `ai-team show`

Show an artifact by identifier.

**Usage**:

```console
$ ai-team show [OPTIONS] IDENTIFIER COMMAND [ARGS]...
```

**Arguments**:

* `IDENTIFIER`: [required]

**Options**:

* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

## `ai-team spec`

Create and manage specification artifacts.

**Usage**:

```console
$ ai-team spec [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `new`: Create a new specification artifact from...

### `ai-team spec new`

Create a new specification artifact from the bundled template.

**Usage**:

```console
$ ai-team spec new [OPTIONS] [TITLE]
```

**Arguments**:

* `[TITLE]`: Spec title. Optional with --overview.

**Options**:

* `--author TEXT`: [default: planner]
* `--status [draft|review|approved|superseded]`: [default: draft]
* `--overview`: Create the S-000 system overview from the system-overview template.
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

## `ai-team status`

Show a Gate 5 status summary.

**Usage**:

```console
$ ai-team status [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

## `ai-team task`

Create and manage task artifacts.

**Usage**:

```console
$ ai-team task [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `new`: Create a new task in the tracker from the...
* `start`: Set a pending task to in-progress.
* `complete`: Set an in-progress task to completed.
* `unblock`: Set a blocked task back to in-progress.
* `block`: Set a task to blocked and record the...
* `set-status`: Set a task to any allowed status.

### `ai-team task new`

Create a new task in the tracker from the bundled template.

**Usage**:

```console
$ ai-team task new [OPTIONS] TITLE
```

**Arguments**:

* `TITLE`: [required]

**Options**:

* `--priority [critical|high|medium|low]`: [default: medium]
* `--assigned-role TEXT`: [default: unassigned]
* `--spec TEXT`: Source spec or change-request ID.
* `--status [planned|pending]`: &#x27;planned&#x27; keeps the task out of /dev-loop until its plan merges.  [default: pending]
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

### `ai-team task start`

Set a pending task to in-progress.

**Usage**:

```console
$ ai-team task start [OPTIONS] TASK_ID
```

**Arguments**:

* `TASK_ID`: [required]

**Options**:

* `--help`: Show this message and exit.

### `ai-team task complete`

Set an in-progress task to completed.

**Usage**:

```console
$ ai-team task complete [OPTIONS] TASK_ID
```

**Arguments**:

* `TASK_ID`: [required]

**Options**:

* `--help`: Show this message and exit.

### `ai-team task unblock`

Set a blocked task back to in-progress.

**Usage**:

```console
$ ai-team task unblock [OPTIONS] TASK_ID
```

**Arguments**:

* `TASK_ID`: [required]

**Options**:

* `--help`: Show this message and exit.

### `ai-team task block`

Set a task to blocked and record the blocking reason in its Work Log.

**Usage**:

```console
$ ai-team task block [OPTIONS] TASK_ID
```

**Arguments**:

* `TASK_ID`: [required]

**Options**:

* `--reason TEXT`: [required]
* `--help`: Show this message and exit.

### `ai-team task set-status`

Set a task to any allowed status.

**Usage**:

```console
$ ai-team task set-status [OPTIONS] TASK_ID STATUS:{planned|pending|in-progress|blocked|completed|cancelled}
```

**Arguments**:

* `TASK_ID`: [required]
* `STATUS:{planned|pending|in-progress|blocked|completed|cancelled}`: One of: planned, pending, in-progress, blocked, completed, cancelled  [required]

**Options**:

* `--reason TEXT`: Recorded as a Work Log entry.
* `--help`: Show this message and exit.

## `ai-team tracker`

Inspect the local work-item tracker.

**Usage**:

```console
$ ai-team tracker [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `path`: Print the absolute tracker folder shared...

### `ai-team tracker path`

Print the absolute tracker folder shared by every worktree of this repository.

**Usage**:

```console
$ ai-team tracker path [OPTIONS]
```

**Options**:

* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

## `ai-team validate`

Validate artifact metadata and cross-references.

**Usage**:

```console
$ ai-team validate [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--all`: Validate all artifact types.
* `--tasks`: Validate tasks only.
* `--bugs`: Validate bugs only.
* `--specs`: Validate specs only.
* `--adrs`: Validate ADRs only.
* `--change-requests`: Validate change requests only.
* `--json`: Emit JSON output.
* `--help`: Show this message and exit.

