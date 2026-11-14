# Upstream snapshot

- Original URL: [OpenAI Build iOS Apps](https://github.com/openai/plugins/tree/main/plugins/build-ios-apps)
- Update policy: before every installation, check the official `main` snapshot
  for changes to this plugin and follow the selection steps in [INSTALL.md](INSTALL.md).
- Source: https://github.com/openai/plugins/tree/0722921d5542fc593105c27bd52630babd8b8c2a/plugins/build-ios-apps
- Repository: `openai/plugins`
- Path: `plugins/build-ios-apps`
- Commit: `0722921d5542fc593105c27bd52630babd8b8c2a`
- Plugin version: `0.1.2`
- Imported files: 76, unchanged, including executable permissions.
- License: upstream `.codex-plugin/plugin.json` declares MIT. No separate
  license file was present in this directory or the repository root at this commit.

This is a directory snapshot in `kp9z/agent-skills`. Original authorship and
plugin metadata remain intact. `INSTALL.md`, `manifest.json`, and this file
are repository-specific additions. `skills/ios-testing` and
`skills/ios-test-planner` are repository-owned additions. Bundle version `0.4.0`
includes these additions and the separately sourced `skills/apple-design`; the imported official plugin remains version `0.1.2`.
The upstream README's original path refers to its source repository; the local
plugin root is `bundles/build-ios-apps`.

To refresh, compare against this pinned commit, replace only the imported
payload with the selected upstream snapshot, preserve modes, update source
metadata and official version, and verify all imported Git blob hashes before
publishing. Preserve all three additional skill directories and their manifest entries
across refreshes; resolve any future upstream name collision explicitly.

## Apple design snapshot

`skills/apple-design` is copied unchanged from the existing SkinSense installation.
Its README identifies [dickwu/apple-design-skill](https://github.com/dickwu/apple-design-skill)
as its source. The installed copy does not record an upstream commit or version;
no revision is claimed here. Keep its references and scripts together and preserve
it separately when refreshing the OpenAI plugin.
