This plugin allows you to rename a stream's language tag from one language code (e.g., `dut`) to another (e.g., `nld`) without transcoding any of the audio, video, or subtitle streams.

It is extremely useful if you have files with non-standard or alternative ISO tags (like `dut` instead of `nld`) and you want to normalize your entire library so that subsequent plugins (like "Add Extra Stereo Audio") can perfectly match a single language configuration.

## Features:
- Allows specifying a "Search Language" tag to find.
- Allows specifying a "Replace Language" tag to apply.
- Works on ANY stream (Audio, Subtitle, etc.) that contains the search language.
- Purely modifies metadata (super fast, no quality loss).
