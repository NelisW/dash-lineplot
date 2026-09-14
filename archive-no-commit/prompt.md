This file carries the original request that started work on this tool. It
was extracted, not paraphrased, from `archive-no-commit/prompt.md` in the
sibling `systemCHandbook` repository, where the work was first requested
as part of a larger multi-repository task. It is reproduced here so this
repository's own handoff does not depend on that other repository for its
own history.

---

## Original request (from systemCHandbook/archive-no-commit/prompt.md)

I worked in C++/CMAKE ten years ago and it quite rusted and out of synch
with modern C++ by now. i must build the app in the C_3dof folder, fix its
data and config files and run it.

Build me a plan to do this. I want to do this in pair-programming mode (to
learn and maintain currency). Some of the steps will require some detours
where you must do some work for me, but I will instruct when we get there.

The plan must guide me to systematically work on the following:

- I need to establish and understand a build environment to get a
  compiled and working tool in this folder structure.
- we must find a good dashboard to display all the telemetry outputs. A
  previous tool I used before
  <https://github.com/rianawillers/dash-lineplot/tree/master>, this or any
  other tool could work.
- The code currently only has one scenario, with all data hardcoded. I
  want to add the capability to read the `pre_engagement_trajectory` from
  a file
- I want to review all telemetry outputs. Print me a report on all
  telemetry outputs.
- I want to review the timing of all events.
- I want to add more scenarios.

Develop the plan with step-by-step instructions, with focus on the first
three steps for the initial work.

---

## What this became, for dash-lineplot specifically

The "find a good dashboard" bullet above is the entire origin of this
repository's current line of work. The fork named there,
`rianawillers/dash-lineplot` (already forked as `NelisW/dash-lineplot`,
last pushed 2026-04-21 at the time), was chosen over building a new tool,
because its data model -- a dictionary of filename to table, each plot
naming its own file -- already fit the target project's telemetry: several
files, several independent sample rates, nothing to merge or resample.

The scope agreed at that point: modernise off PySide2/Qt (no Python 3.14
support, the actual blocker) into a browser-only Dash application, and add
a JSON configuration option alongside the existing Excel workbook, since
the target telemetry is JSON.

Everything that followed -- the JSON data reader, multi-rate groups,
enumerations, `commonX`, the range-entry boxes replacing the dead slider,
the compact layout, and the later code-review work in `suggestedwork.md`
-- is downstream of this one paragraph, and is recorded in `handoff.md`
and `handoff-history/` in this repository rather than repeated here. This
file only preserves the original ask.

## Follow-up requests made directly against this repository

These were given directly in sessions working on this repository (not
extracted from `systemCHandbook`), and are recorded here for completeness
since they are part of the same request lineage:

- Generalise the header-row `%`-stripping in the space/comma data reader
  so it works for any column name, not just three hardcoded ones
  (`%Time`, `%CurrentSimTime`, `%t`).
- Remove the `.scd`/`.spc` spectral-data reading branch entirely.
- Analyse the whole codebase for bugs, poor constructs and modernisation
  opportunities, without changing any code, and write the findings up as
  a plan (`suggestedwork.md`) rather than acting on them.
- Move all `dash-lineplot`-specific work history out of the
  `systemCHandbook` handoff/prompt files and into this repository's own
  `archive-no-commit/`, as a single-file handoff plus this prompt file, so
  work here no longer depends on that other repository's session record.
  This is the request this file itself is the result of.
