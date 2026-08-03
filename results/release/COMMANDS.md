# Release commands, to be run by the author

Nothing here has been run. This file lists the commands in order, and the
decision each one commits to.

## 0. Confirm the snapshot decision

Read `RELEASE_NOTES.md` in this directory. It states what the tag contains and
what it excludes, with sizes. If the decision is wrong, change it before tagging,
because a Zenodo record is not straightforwardly retractable.

## 1. Put the release files in the repository root

    cp results/release/RELEASE_NOTES.md RELEASE_NOTES.md

`LICENSE`, `.zenodo.json` and `CITATION.cff` are already written to the root by
`python -m colophon.release`.

## 2. Verify the tree is clean and the suite passes

    python -m pytest -q
    git status --short

## 3. Commit

    git add -A
    git commit -m "Submission package, release prep, and the fourth addendum's six items"

## 4. Point the empty remote at this repository and push

The remote exists and is empty. `main` is the branch the repository was created
with; this working copy is on `master`.

    git remote add origin https://github.com/Volkopat/colophon.git
    git push -u origin master:main

## 5. Enable the Zenodo integration, then tag

Turn the repository on at https://zenodo.org/account/settings/github/ **before**
creating the release. Zenodo only archives releases created after the switch is
on.

    git tag -a v1.0.0 -m "colophon v1.0.0"
    git push origin v1.0.0

Then create a GitHub release from that tag, with `RELEASE_NOTES.md` as the body.

## 6. Fill the DOIs

Zenodo mints a version DOI and a concept DOI. Put them in
`results/submission/fields.json` under `zenodo_version_doi`,
`zenodo_concept_doi` and `release_tag`, then:

    python -m colophon.submission --final

That build refuses while any field is empty, so it is the check that the
placeholders are gone rather than a step that hopes they are.
