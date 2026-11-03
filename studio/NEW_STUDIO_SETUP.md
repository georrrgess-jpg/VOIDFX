# Setting up a second voidfx studio

A studio is a Claude Code session, on the web or desktop, attached to the **`georrrgess-jpg/voidfx`** repository. Two studios can run at the same time, which doubles throughput.

## 1. Create the session

1. Start a new Claude Code session on the repository `georrrgess-jpg/voidfx`, from the branch with this kit (`claude/gallant-planck-pqpczp`, or `main` once it's merged).
2. Give the studio its **own branch**, for example `studio2/<edit-name>`. Keep Studio 1 on its own branch.
3. Use a **separate version range** so edit folders never collide:
   - Studio 1: `v8`, `v9`, `v10` …
   - Studio 2: `v101`, `v102` …

## 2. Upload the source library

`src/` is not in git (media is too large). Upload the packs, songs and logo you want into the session and copy them into `src/` with **exactly** the names in `studio/src_manifest.json`. `studio/SCENE_PACKS.md` lists every file with its original upload name. Then run:

```bash
bash tools/setup_studio.sh
```

This:
- installs any missing Python packages and fonts;
- downloads YuNet and MODNet;
- checks every `src/` file against the manifest (sizes and checksums);
- smoke-tests the benchmark EDL.

`--check` verifies without installing anything. Only the files a given edit uses need to be present.

## 3. Start the edit

Paste the filled-in prompt from `studio/START_PROMPT.md`. The studio reads the handbook and catalog, scaffolds `vN/` from the newest benchmark engine, and follows the fast loop:
1. `song_map`;
2. EDL;
3. `build.sh prep auto`;
4. `clip`;
5. `audio`;
6. one `video qc`;
7. visual sign-off;
8. deliver.

## 4. Keep both studios improving

- When you approve an edit as a standard, tell that studio: it updates `studio/VOIDFX_STUDIO.md` (likes, the benchmark table) and `CLAUDE.md`.
- New transitions go into that edit's renderer and are listed in `docs/TOOLKIT.md`.
- Merge each studio's branch into `main` (via a PR) after a shipped edit, so the other studio picks up the new transitions, rules and pitfalls on its next pull.
- Rejections go into the "rejected" table in the handbook straight away, so neither studio repeats them.

## 5. Speed tips

- Send **one brief** and **one feedback message per revision**. The studio applies everything in one pass and one render (about 10 minutes).
- Reuse the cached shot lists and transcripts for known packs. Only new packs need `analyze.py` and `transcribe.py`.
- A full edit typically takes 1.5–2.5 hours of wall-clock from brief to shipped MP4, mostly unattended. Two studios give two edits in the same time.
