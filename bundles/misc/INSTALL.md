# Install misc skills

On macOS, read the [bundle manifest](manifest.json) and copy each listed skill directory into `~/.agents/skills/`, preserving its name, files, and modes. If a destination already exists, compare the two copies and confirm any replacement that the user has not already authorized.

`free_space` uses the standard library of `/usr/bin/python3`. Verify the installed helper with the following command, which only prints usage.

```sh
/usr/bin/python3 -I ~/.agents/skills/free_space/scripts/cleanup.py --help
```
