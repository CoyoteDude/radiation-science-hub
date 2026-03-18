# Contributing to ENDF

The basic rule about contributing to ENDF is: show up at the CSEWG meeting. After this, contact the ENDF Library Manager for access to the gitlab repository. If you are reading this, presumably you have access to the gitlab repository and may want to read further...

**TABLE OF CONTENTS**

- [Adding your evaluation](#adding-your-evaluation)
- [Reviewing evaluations](#reviewing-evaluations)
- [Tracking bugs](#tracking-bugs)
- [ENDF branches](#endf-branches)
- [Roles and permissions](#roles-and-permissions)
- [ENDF repositories at other institutions](#endf-repositories-at-other-institutions)

## Adding your evaluation

Before you can commit your evaluation, you will need a clone of the current library:

> $ git clone <https://git.nndc.bnl.gov/endf/library/atomic_relax.git>

By default you will be placed on the `phase1` branch. This is the main ENDF development branch and is the traditional place for Phase I ENDF testing.

Note, the ENDF files in this project have a distinctive naming convention that must be followed for our checking system to process them correctly. For this sublibrary, file names use the `atom-ZZZ_Sym_AAA.endf` pattern (or `atom-ZZZ_Sym_AAAmM.endf` for isomeric targets). Here `ZZZ` and `AAA` are the atomic number and mass, respectively. Add leading zeros to `ZZZ` and `AAA` to ensure a three character field. `Sym` is the element symbol, properly capitalized (i.e. "U" for Uranium and "Ta" for Tantalum). For isomers, `M` is the isomeric state index, e.g. 1, 2, ... The ground state has no `mM` in the filename.

Now you may add or overwrite the exiting file with your evaluation:

> $ cp my-great-evaluation.txt atomic_relax/atom-059_Pr_142.endf

Note, some operating systems (e.g. Windows) hide the file extension. Please ensure your files have the correct `.endf` extension. From inside the checked out library, do a `git add` and a `git commit`

> $ cd atomic_relax

> $ git add atom-059_Pr_142.endf

> $ git commit atom-059_Pr_142.endf

Now you have saved your evaluation in your local repository. You still must push it to [git.nndc.bnl.gov](https://git.nndc.bnl.gov).

> $ git push

Congratulations! You have now submitted your evaluation.

But wait... By committing to `phase1` you have notified ADVANCE, the ENDF continuous integration system, of a change in need of checking. When the job complete, check the build report at <https://www.nndc.bnl.gov/endf/b7.dev/qa/atomic_relax/reports/atomic_relax.html>. Please review the report and correct any issues you see there, commit your changes and push them to the `phase1` branch.

## Reviewing evaluations

CSEWG is developing formal review criteria. Whatever the details of this review may include, we do know that a review of the ADVANCE build reports for the evaluations will be of the full review. So, please review the report and correct any issues you see there.

That said, the mechanics of the process itself is taking form:

1. Following your commit to the `phase1` branch, a branch forked off `phase2` will be created, named `Review/atom-ZZZ_Sym_AAAmM` for your file `atom-ZZZ_Sym_AAAmM.endf`.

2. Your evaluation will be copied into this branch.

3. The ENDF library manager will initiate a merge request to merge `Review/atom-ZZZ_Sym_AAAmM` into `phase2`. This merge request comes with an issue tracker specific to this merge request.

4. The ENDF library manager will assign one or more reviewers for your evaluation.

5. The reviewer will place their review in the issue tracker.

6. The evaluator and reviewer now iterate: they can discuss, make changes, etc. until a consensus on the acceptability of the evaluation is achieved. Note, the discussion is open and viewable to all CSEWG members who have activated their Gitlab accounts. This means that proper professional etiquette must be maintained and information security rules followed. OUO, PII AND HIGHER CLASSIFICATION LEVEL INFORMATION MAY NOT BE POSTED IN THE TRACKER. If you need to have such a discussion, please seek a more appropriate forum for the discussion.

7. Once consensus is achieved, the ENDF library manager will "click the merge button" and close the merge request. This will move the final evaluation to the `phase2` branch.

8. Once the evaluation is in the `phase2` branch, the CSEWG Validation Committee can begin its review of the entire `phase2` branch.

## Tracking bugs

Bug reports and requests for improvement can be posted on the issue tracker for this library: <https://git.nndc.bnl.gov/endf/library/atomic_relax/-/issues>.

## ENDF branches

Each sublibrary has at least three branches:

- `phase1` -- This is ENDF's Phase I testing branch.

  - All new and changed evaluations must be committed here.
  - Feel free to branch from this branch, but merge your changes back here when you are done.
  - The ADVANCE continuous integration system watches this and publishes results to <http://www.nndc.bnl.gov/endf/b7.dev/qa/index.html>.
  - Evaluations are reviewed here and, when accepted, are merged into the phase2 branch.

- `Review/atom-ZZZ_Sym_AAA` -- this is a review branch for an evaluation transitioning from Phase I testing to Phase II validation review. Review branches come and go as reviews are initiated and completed.

- `phase2` -- This is ENDF's Phase II testing branch.

  - Evaluations here should be processable by any processing code.
  - Evaluations in this branch are ready for integral testing.
  - The CSEWG Validation committee is responsible for checking and "blessing" this branch.

- `master` -- This branch collects evaluations ready for release.

## Roles and permissions

At the 2019 CSEWG meeting, David Brown laid out a scheme of permissions that involved lab "POCs", "reviewers" and "evaluators". These roles don't quite map onto the system of permissions that gitlab provides. Also, they neglect the other ENDF projects (formats manual, QA docs, checking codes, etc.).

Gitlab provides these access levels:

```
10 => GUEST_ACCESS      # Not used, read-only access to everything
20 => REPORTER_ACCESS   # Can read most things and may add trackers
30 => DEVELOPER_ACCESS  # Can make branches, commit things, approve merge requests
40 => MAINTAINER_ACCESS # NNDC only
50 => OWNER_ACCESS      # ENDF library manager
```

Given this and the current constellation of ENDF projects, we established this default set of CSEWG access:

```
"library" group                      REPORTER_ACCESS  # can elevate if requested or evaluation/validation/executive committee or reviewer
'QA' group     'standards' project   REPORTER_ACCESS  # can elevate if requested or evaluation/validation/executive committee or reviewer
"tools" group  "NNDCtk" project      REPORTER_ACCESS  # can elevate if requested or formats/evaluation/validation/executive committee
"format" group "endf6man" project    REPORTER_ACCESS  # can elevate if requested or formats/executive committee
```

Given the variety of roles in CSEWG and the different committees, I came up with this permission/role matrix:

Role       | Library group or projects | QA/standards project | tools/NNDCtk project | format/endf6man project
---------- | ------------------------- | -------------------- | -------------------- | -----------------------
standard   | REPORTER_ACCESS           | REPORTER_ACCESS      | REPORTER_ACCESS      | REPORTER_ACCESS
reviewer   | DEVELOPER_ACCESS          | DEVELOPER_ACCESS     | REPORTER_ACCESS      | REPORTER_ACCESS
evaluation | DEVELOPER_ACCESS          | DEVELOPER_ACCESS     | DEVELOPER_ACCESS     | REPORTER_ACCESS
validation | DEVELOPER_ACCESS          | DEVELOPER_ACCESS     | DEVELOPER_ACCESS     | REPORTER_ACCESS
formats    | REPORTER_ACCESS           | REPORTER_ACCESS      | DEVELOPER_ACCESS     | DEVELOPER_ACCESS
executive  | DEVELOPER_ACCESS          | DEVELOPER_ACCESS     | DEVELOPER_ACCESS     | DEVELOPER_ACCESS

Note, these are just default permissions in the user add script. We can easily upgrade/downgrade permissions as needed.

## ENDF repositories at other institutions

We only have a limited number of seats, so you'll likely need a good reason for access. Therefore, we encourage each institution that contributes to CSEWG to make their own, in house, copy of the ENDF family of projects. A lab representative can the push the aggregated changesets from these in house repositories to the master repositories at the NNDC.
