---
name: push_to_testflight
description: Archive the current production iOS app and upload it to TestFlight through the project's CLI workflow.
disable-model-invocation: true
---

# Push to TestFlight

Run only when the user explicitly invokes `$push_to_testflight` or `/push_to_testflight`. Invocation authorizes archiving and uploading the current project's production app to TestFlight. Finish after reporting the command result; do not open Chrome, monitor Apple processing, assign tester groups, or release to the App Store.

## Resolve the release

1. Read the project's agent instructions, release script, and release configuration. Follow a release-document pointer when present. Use the production target, bundle ID, signing team, and distribution scope already configured by the project. In SkinSense, read `scripts/release.sh` and `docs/implementation/release.md`; its script uses Release and internal-only TestFlight distribution. Other projects must supply their own supported CLI workflow; do not invent signing settings.
2. Preserve the app version selected by the user or current release configuration, including three-part versions such as `1.0.1`. Keep the marketing version separate from the build number: `1.0.1 (5)` means version `1.0.1`, build `5`. Never bump the app version merely to resolve a duplicate build number. If conversation, configuration, and archives disagree about the intended version, resolve that ambiguity before archiving.
3. Inspect existing archives, upload logs, and release records for the intended app. If configured API access is available, query Apple's existing builds through that access. Choose a positive integer greater than the known build numbers, including manual uploads disclosed by the user. Local files alone cannot prove a number is unused on Apple. Announce the selected version/build and source commit, then proceed within the user's request.

## Build and upload

4. Run the project's required release checks. Reuse recorded passing checks only when they cover the same build inputs and configuration. Preserve the current checkout and unrelated changes; do not switch branches, merge, commit, or push source as part of uploading. If uncommitted app changes make the requested source unclear, clarify which source to release.
5. Reuse an existing archive only when its recorded source fingerprint, version, build number, production target, and signing configuration match this release and there is no successful upload record for it. A matching directory name or Git commit alone does not establish identical inputs when the tree was dirty. Otherwise archive once. Save a release record beside the ignored artifacts containing source commit, a fingerprint of actual build inputs (including dirty/untracked inputs), version/build, target, bundle ID, signing team, archive path, checks, and command results. Keep credentials out of this record.
6. Use the project's CLI upload command directly. Reuse its signing and export options. Use the existing Xcode account with `-allowProvisioningUpdates`, or an API key only if already configured. Keep `.p8` contents and account secrets outside chat, logs, and Git. Poll the running command to its exit status and inspect its final result; a launched command is not an uploaded build.

For SkinSense, set the resolved values explicitly on both commands; the script otherwise defaults the version to `1.0`:

```sh
DEVELOPMENT_TEAM="$release_team" VERSION="$release_version" BUILD_NUMBER="$release_build" scripts/release.sh archive
DEVELOPMENT_TEAM="$release_team" VERSION="$release_version" BUILD_NUMBER="$release_build" scripts/release.sh upload
```

Skip the archive command for a verified reusable archive. A separate validate/export pass is needed only when the project's release checks require it or a specific failure calls for diagnosis; uploading already performs export. Preserve exit status when capturing logs.

## Failures and completion

- Account-access failure: stop and report the exact error. Ask the user to complete Xcode authentication. After they confirm, retry with the same archive. If a manual upload may have happened meanwhile, check its outcome or validate first to avoid another upload of the same build. Account visibility in Settings alone does not establish CLI authentication.
- Duplicate build: Apple received a build with that number. Confirm whether it was this same archive before treating the request as complete. For a new upload, preserve the app version, choose a higher build number using the available evidence, and rearchive. Allow one duplicate-number recovery per invocation; stop on another collision rather than repeatedly uploading.
- Connection loss or an uncertain upload result: inspect the existing log and available Apple build status before retrying. If receipt cannot be determined, report the uncertainty and request the missing outcome. Do not blindly repeat an upload.
- Build, signing, or validation failure: report the error and relevant artifact/log paths. Do not repeatedly retry unchanged commands or alter account/security settings.
- Success: record the CLI's explicit upload success and report the version/build and log path. Say "uploaded; Apple processing not checked." Upload completion does not establish tester availability. End here.
