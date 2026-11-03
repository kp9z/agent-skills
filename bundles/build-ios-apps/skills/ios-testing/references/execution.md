# Run tests and retain evidence

Prefer repository and CI commands. Otherwise discover the actual project or
workspace, scheme, test plan, and available destination before building commands.
Use the installed tools' help for version-specific options and result schemas.

```sh
xcodebuild -version
xcodebuild -list -workspace MyApp.xcworkspace
xcodebuild -showdestinations -workspace MyApp.xcworkspace -scheme MyApp
```

Use `-project MyApp.xcodeproj` instead of `-workspace` when appropriate. Select
an installed Simulator by its destination ID; do not invent a model or OS version.

Example for one XCTest method, with placeholders replaced by discovered values:

```sh
xcodebuild test \
  -workspace MyApp.xcworkspace \
  -scheme MyApp \
  -destination 'platform=iOS Simulator,id=SIMULATOR-UUID' \
  -only-testing:MyAppTests/LoginTests/testInvalidPassword \
  -resultBundlePath /tmp/ios-testing-focused-UNIQUE.xcresult
```

Choose a new result path for each run, following repository artifact rules.
Do not remove previous evidence to reuse a path. Preserve the runner exit status
when capturing output or piping through a formatter.

The filter above uses XCTest identifiers. For Swift Testing, use identifiers
recognized by the installed runner and verify the selected tests in its results;
do not assume XCTest class and method names apply. A successful process with
zero selected tests does not verify the change.

Run the affected target by narrowing the filter to the target, or remove it to
run the selected scheme and test plan. Honor required plans and configurations.
For a standalone Swift package, `swift test` may be suitable when its code can
run on the host; iOS-only dependencies need an iOS-capable runner.

Open `.xcresult` bundles in Xcode, or inspect them using the installed
`xcrun xcresulttool` commands. Check `xcrun xcresulttool help` before selecting
subcommands because the interface differs between Xcode versions. Confirm
executed, failed, and skipped counts, relevant failure details, and attachments.
Building, `build-for-testing`, or launching the app alone does not execute tests.
Use `test-without-building` only with matching, current build artifacts.

If Xcode, the runtime, dependencies, or the required test runner are unavailable,
perform applicable static checks and report that tests were not run. Do not
substitute an unrelated destination or silently change signing or project settings.

Official references:

- [Running tests and interpreting results](https://developer.apple.com/documentation/xcode/running-tests-and-interpreting-results)
- [Command-line testing](https://developer.apple.com/library/archive/technotes/tn2339/_index.html)
- [Viewing result bundles](https://help.apple.com/xcode/mac/current/en.lproj/devc38fc7392.html)
