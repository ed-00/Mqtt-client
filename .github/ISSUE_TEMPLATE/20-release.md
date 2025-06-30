---
name: 20 release
about: Request or make a versioned release
title: "[REL] "
labels: 20 release
assignees: sbtal

---

# Release guidelines

See Språkbanken Tal's branching and versioning guidelines before 
getting to work on the release.

# Background

Describe why the release is needed (e.g. the deprecation of some outdated 
API feature, addition of new features, significant bug fixes, or a wider 
general versioning release). 

Describe depencencies and concerns regarding other repos or releases.

Indicate the new version number (preferably, include this imn the issue title).

See SBTal's [versioning guidelines](https://github.com/sprakbankental/docs-policy/blob/main/docs/html/gdl-versioning.html).


* Make a clear note of the proposed upcoming release, e.g. Full release (including release candidates), pre-release, or a hotfix.* 

* Release candidates of vM.N.O from prereleases of vM.N.O, e.g.
  - Minor release: v1.0.0-X.Y.Z (on `develop`) ==> v1.0.0-RC1 
  (on new branch `release/v1.0.0`)
  - Maintainance release: v1.19.1-X.Y.Z (on `develop`) ==> v1.19.1-RC1 
    (on new branch `release/v1.19.1`)
  - Major release: v2.0.0-Y-Y-Z (on `develop`) ==> v2.0.0-RC1 
    (on new branch `release/v2.0.0`)
* New release candidates after changes (of an RC that failed to make it to 
  release), e.g.
  - v2.0.0-RC1 (on `release/v2.0.0`) ==> v2.0.0-RC2 (on the same branch)
* Full releases from release candidates, which also triggers a new 
development release with any changes from the release candidate included:
  - Minor release: v1.0.0-RC1 (on `release/v1.0.0`) ==> v1.0.0 
    (on `main`, after merge) ==> v1.0.1-0.0.0 
	(on `develop`, again after merge)
  - Maintainance release: v1.19.1-RC1 (on `release/v1.19.1`) ==> 
    v1.19.1 (on `main`, after merge) ==> v1.19.2-0.0.0 
	(on `develop`, again after merge)
  - Major release: v2.0.0-RC1 (on `release/v2.0.0`) ==> v2.0.0 
    (on `main`, after merge) ==> v2.0.1-0.0.0 
	(on `develop`, again after merge)
* New prerelease
  - Maintainance: v2.0.1-0.0.0 (on develop) ==> v2.0.1-0.0.1 (on develop). 
    No need to change the target version, as its maintainance number is 
	increased at the initial prerelease)
  - Minor (first time for this target release): v2.0.1-0.0.0 (on develop) 
    ==> v2.1.0-0.1.0 (on develop).
    The target is upgraded to a minor release, and the maintainance release 
	is set to 0 for both target and development release versions. Subsequent 
	maintainance or minor release changes only affects the development number.
  - Minor (after at least one minor or major prerelease has been made since 
    last full release): v2.1.0-0.1.0 (on develop) ==> v2.1.0-0.2.0 (on develop).
	No need to change the target version, as its minor number was 
	increased at the first minor development release.
  - Major (first time for this target release): v2.0.1-0.0.0 (on develop) ==> 
    v3.0.0-1.0.0 (on develop). 
	The target is upgraded to a major release, and the maintainance+minor 
	release is set to 0 for both target and development release versions. 
	Subsequent maintainance or minor release changes only affects the 
	development number.
  - Major (after at least one major prerelease has been made since last 
    full release): v3.0.0-1.0.0 (on develop) ==> v3.0.0-2.0.0 (on develop). 
	No need to change the target version, as its major number was 
	increased at the first major development release.
	
# Tasks

## Stable release

See SBTal's [stable release tutorial](https://github.com/sprakbankental/docs-policy/blob/main/docs/html/tut-git-new-stable-release.html).

- [ ] Create a release branch from `develop` and create a release candidate on it
  - [ ] e.g. `git checkout -b release/1.0.0`
  - [ ] push and track the branch `git push -u origin release/1.0.0`)
  - [ ] E.g. `git tag v1.0.0-RC1`, `git push origin v1.0.0-RC1` 
- [ ] Restart `develop` 
  - [ ]  Checkout `develop` again
  - [ ] Add new tag on develop (e.g. with the tag `v1.0.1-0.0.0`)
  - [ ] Push the new tag (e.g. `git push origin v1.0.1-0.0.0`)
- [ ] Review the release candidate. If fixes are needed, iterate:
  - [ ] Make them, on the release branch
  - [ ] Make new release candidate
  - [ ] Merge changes back to `develop`
- [ ] Once the code passes review
  - [ ] Checkout `main`
  - [ ] pull, for good measure. then merge `release/1.0.0`
  - [ ] Merge the final release candidate into main, e.g. `git merge v1.0.0-RC2` 
  - [ ] Fix documentation
    - [ ] Update the `repoversion` attribute in `/docs/asciidoc/attributes/config.adoc` to the new version and commit
    - [ ] Build both html and pdf documentation
  - [ ] tag with new version `git tag v1.0.0`
  - [ ] `git push origin v1.0.0`
  - [ ] Finally, merge the RC with `develop`unless there are no changes, increase `DEVPATCH` on develop by one
  - [ ] Update the `repoversion` attribute in `/docs/asciidoc/attributes/config.adoc` to the new version and commit
  - [ ] push changes to `develop`
  - [ ] Add the tag , e.g. `git tag v1.0.1-0.0.1`, `git push origin v1.0.1-0.0.1`

## Development release

See SBTal's [stable release tutorial](https://github.com/sprakbankental/docs-policy/blob/main/docs/html/tut-git-new-prerelease.html).

- [ ] Find the current version `VERSION` (= `TARGETVERSION-DEVVERSION`)
- [ ] Check commits since last release
* If breaking changes to public API, 
  - Since last increment of the major stable release target version: increase both the stable target and develop major version and set their minor and patch to 0 (e.g. 1.2.3-0.1.1 ⇒ 2.0.0-1.0.0)
  -  Since last increment of the develop major version: increase develop major version and set its minor and patch to 0 (e.g. 2.0.0-1.1.1 ⇒ 2.0.0-2.0.0)
* If non/breaking changes to public API
  - Since last increment of the minor stable release target version: increase both the stable target and develop minor version and set their patch to 0 (e.g. 1.2.3-0.0.1 ⇒ 1.3.0-0.1.0)
  - Since last increment of the develop minor version: increase develop minor version and set its patch to 0 (e.g. 1.3.0-0.1.0 ⇒ 1.3.0-0.2.0)
* If no breaking changes, increase develop patch version (e.g. 1.3.0-0.2.0 ⇒ 1.3.0-0.2.1)
- [ ] Make sure you are on develop (we do not use release branches for development 
  releases, they are release directly off develop).
- [ ] Pull any changes, so you're up to date
- [ ] Merge any feature branches that should be included
- [ ] Fix documentation
  - [ ] Update the `repoversion` attribute in `/docs/asciidoc/attributes/config.adoc` to the new version and commit
  - [ ] Build both html and pdf documentation
- [ ] Push changes right away
- [ ] Add the tag. The tag message MESSAGE should be “`TARGETVERSION` prerelease `DEVVERSION`”
- [ ] Push the tag 
- [ ] Optionally, go to GitHub and base a packaged release on the version. For development versions, this is usually not necessary.


## Hotfix

Hotfixes are branched directly from a stable release on `main` (e.g. `v1.0.0`).

- [ ] Checkout a new hotfix branch (these arejust numbered with ordinals, so e.g. `hotfix-1`)
- [ ] Make the necessary changes. This should never change the API, hotfixes are purely for bugs and security.
- [ ] Update the `repoversion` attribute in `/docs/asciidoc/attributes/config.adoc` to the new version and cmmit
- [ ] Merge back onto main, and release a patch by increasing it's patch number by one (e.g. `v1.0.1`)
- [ ] Also merge back to ddevelop, with a similar patch release (where the main release target is updated if need be, that is if the target has not yet been increased on the major or minor level).
