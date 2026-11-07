# Handoff ledger (Flash studio)

| Date | Direction | Handoff | Verdict | Adopted / notes |
|---|---|---|---|---|
| 2026-11-07 | sent → Dexter studio | `2026-11-07_flash_v10_LET_IT_HAPPEN_standard.md` | standard (rev 5) | Catch-up; first sent in the earlier report format, reissued in the shared template |
| 2026-11-07 | sent → Dexter studio | `2026-11-07_flash_v11_BOP_standard.md` | standard (rev 4) | Catch-up; reissued in the shared template |
| 2026-11-07 | received ← Dexter studio | `2026-11-07_dexter_v105_DRACULA_standard.md` | standard (rev 3) | Rules 1–6 adopted (all apply to Flash). Conflicts noted: two `tools/sharpness.py` versions with different score scales; the scaffold base (agreed: Dexter from v105, Flash from v11). `--src` ranking added to this studio's tool |
| 2026-11-07 | received ← Dexter studio | `2026-11-07_dexter_v105_DRACULA_standard_report.md` | standard (rev 3) | Same edit, in the earlier report format. New beyond the handoff: rule 7 (mix effects against the master's loudness), the flash-check thresholds (ported into `qc11.py` §7b) and the LOWBIT flag (added to `sharpness.py --src`). Run on v11: no white-out runs, max 1 flash/s, but the drop impact frame (454) peaks at mean luma 173 (one frame, over the 110 flare limit) |
