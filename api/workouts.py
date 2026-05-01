"""Workout segment parsing and pace calculations.

Pure Python — no Streamlit dependencies.
"""
import re

def goal_pace_secs(time_str):
    parts = [int(x) for x in (time_str or "3:30:00").strip().split(":")]
    total = parts[0]*3600 + parts[1]*60 + (parts[2] if len(parts)==3 else 0)
    return round(total / 26.2)

def fmt_pace(spm):
    spm = max(1, round(spm))
    m, s = divmod(spm, 60)
    return f"{m}:{s:02d}/mi"

def fmt_time(secs):
    h, rem = divmod(int(secs), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

# ── structured segments ───────────────────────────────────────
def fmt_range(lo, hi):
    """Format a pace range e.g. 7:40–8:15/mi"""
    return f"{fmt_pace(lo)}–{fmt_pace(hi)}"

# ── Marathon Excellence pace math ─────────────────────────────
# 5K pace from marathon goal via Riegel (T2 = T1 * (D2/D1)^1.06)
# Given marathon pace per mile, returns 5K pace per mile.
def fivek_pace_secs(marathon_gps):
    marathon_time_secs = marathon_gps * 26.2
    fivek_time_secs = marathon_time_secs * (3.10686 / 26.2) ** 1.06
    return fivek_time_secs / 3.10686

def fmt_elapsed(secs):
    """Short elapsed time format — 1:23 or 5:02 or 1:02:30"""
    if secs < 60:
        return f"{int(round(secs))}s"
    if secs < 3600:
        m, s = divmod(int(round(secs)), 60)
        return f"{m}:{s:02d}"
    h, rem = divmod(int(round(secs)), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"

def pace_for_pct(pct_lo, pct_hi, base_pace_secs):
    """Given % of reference pace (5k or MP) and base pace sec/mi, return formatted range.
       Higher % effort = faster pace = fewer seconds per mile.
       % is effort relative to reference race pace, so 100% = base_pace, 108% MP = faster."""
    # 108% of MP effort means running at a pace that's faster than MP.
    # Convert: target pace secs = base_pace / (pct/100)
    lo_pace = base_pace_secs / (pct_hi / 100)   # faster pace comes from higher %
    hi_pace = base_pace_secs / (pct_lo / 100)
    if abs(lo_pace - hi_pace) < 2:
        return fmt_pace(lo_pace)
    return f"{fmt_pace(lo_pace)}–{fmt_pace(hi_pace)}"

def parse_me_segments(note, gps):
    """Parse a Marathon Excellence workout description into structured segments.
    Returns list of (label, distance_str, pace_str, detail).
    Also includes a warmup and cooldown line.
    """
    import re
    if not note:
        return []

    text = note
    fivek_p = fivek_pace_secs(gps)  # 5K pace sec/mi
    mp_p    = gps
    segs    = []

    # Always prefix with a warmup
    segs.append(("Warmup", "~2 mi", fmt_range(gps + 60, gps + 90), "Easy jog to get loose"))

    # Helper to extract % ranges: "90–92% 5k" or "108% MP"
    def find_pct_pace(s):
        """Return (pct_lo, pct_hi, ref) or None. ref = '5k' or 'MP'."""
        m = re.search(r"(\d+)(?:[-–](\d+))?\s*%\s*(5k|MP)", s, re.IGNORECASE)
        if not m: return None
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        return lo, hi, m.group(3).upper()

    def pace_str_for(pct_info):
        lo, hi, ref = pct_info
        base = fivek_p if ref == "5K" else mp_p
        return pace_for_pct(lo, hi, base)

    def effort_for_pct(pct_lo, pct_hi, ref):
        """Plain-English effort description based on intensity."""
        avg = (pct_lo + pct_hi) / 2
        if ref == "5K":
            if avg >= 102: return "All-out — 1500m to 3K race effort. Hard, controlled breathing. Should not be sustainable past the rep duration."
            if avg >= 98:  return "5K race effort. Hard but controlled. Heavy breathing, can only get out 1–2 words at a time."
            if avg >= 92:  return "10K race effort. Comfortably hard — labored breathing, legs working but not redlining. You should finish each rep wanting one more."
            if avg >= 86:  return "Half-marathon race effort. Steady, focused — breathing is elevated but rhythmic. Just below threshold."
            if avg >= 80:  return "Steady aerobic effort. Conversational becomes hard but possible. Builds aerobic strength."
            return         "Easy-to-moderate effort. Should still feel relaxed."
        else:  # MP
            if avg >= 108: return "Faster than marathon pace by ~30 sec/mi. Sharpens your top-end aerobic gear."
            if avg >= 104: return "Slightly faster than goal MP. Should feel controlled but pointed — practice for late-race gear shifts."
            if avg >= 100: return "Goal marathon pace. Feels comfortably hard — sustainable, but not relaxing. This is your race rhythm."
            if avg >= 95:  return "Just below MP. Strong aerobic effort that builds confidence at race-adjacent paces."
            if avg >= 88:  return "Marathon-specific endurance pace. Builds the engine without the recovery cost of true MP work."
            return         "Steady aerobic — recovery between hard efforts."

    # Handle each class of workout

    # 1) Time-based rep: e.g. "8 × 3 min at 90–92% 5k w/ 1 min jog"
    m = re.search(r"(\d+)(?:[-–](\d+))?\s*×\s*(\d+(?:\.\d+)?)\s*min\s*at\s*([^,w]+?)(?:\s*w/\s*(.+))?$", text, re.IGNORECASE)
    if m:
        reps_lo = int(m.group(1))
        reps_hi = int(m.group(2)) if m.group(2) else reps_lo
        rep_min = float(m.group(3))
        pct = find_pct_pace(m.group(4))
        jog = m.group(5) or "jog"
        if pct:
            reps_str = f"{reps_lo}" if reps_lo == reps_hi else f"{reps_lo}–{reps_hi}"
            lo, hi, ref = pct
            base = fivek_p if ref == "5K" else mp_p
            rep_pace_lo = base / (hi / 100)
            rep_pace_hi = base / (lo / 100)
            # Distance covered per rep
            dist_lo = rep_min * 60 / rep_pace_hi  # miles
            dist_hi = rep_min * 60 / rep_pace_lo
            avg_dist = (dist_lo + dist_hi) / 2
            total_hard_mi = reps_lo * avg_dist
            segs.append((
                f"{reps_str} × {rep_min:g} min @ {lo}–{hi}% {ref}" if lo != hi else f"{reps_str} × {rep_min:g} min @ {lo}% {ref}",
                f"~{total_hard_mi:.1f} mi",
                pace_str_for(pct),
                f"Each rep {fmt_elapsed(rep_min*60)} (~{avg_dist:.2f} mi). Recovery: {jog}"
            ))
            segs.append(("Cooldown", "~1–2 mi", fmt_range(gps + 60, gps + 90), "Easy jog"))
            return segs

    # 2) Distance-based rep: "5 × 1 mi at 95% 5k w/ 3 min jog" or "8 × 1 km at 95% 5k"
    m = re.search(r"(\d+)(?:[-–](\d+))?\s*×\s*(\d+(?:\.\d+)?)\s*(mi|km|m)\b\s*at\s*([^,w]+?)(?:\s*w/\s*(.+))?$", text, re.IGNORECASE)
    if m:
        reps_lo = int(m.group(1))
        reps_hi = int(m.group(2)) if m.group(2) else reps_lo
        rep_dist = float(m.group(3))
        unit = m.group(4).lower()
        pct = find_pct_pace(m.group(5))
        jog = m.group(6) or "jog"
        # Convert rep distance to miles
        if unit == "km":
            rep_mi = rep_dist * 0.621371
            dist_label = f"{rep_dist:g} km"
        elif unit == "m":
            rep_mi = rep_dist / 1609.34
            dist_label = f"{rep_dist:g}m"
        else:
            rep_mi = rep_dist
            dist_label = f"{rep_dist:g} mi"
        if pct:
            reps_str = f"{reps_lo}" if reps_lo == reps_hi else f"{reps_lo}–{reps_hi}"
            lo, hi, ref = pct
            base = fivek_p if ref == "5K" else mp_p
            rep_pace_lo = base / (hi / 100)
            rep_pace_hi = base / (lo / 100)
            rep_time_lo = rep_mi * rep_pace_lo
            rep_time_hi = rep_mi * rep_pace_hi
            total_hard_mi = reps_lo * rep_mi
            time_str = (f"{fmt_elapsed(rep_time_lo)}" if abs(rep_time_hi - rep_time_lo) < 2
                        else f"{fmt_elapsed(rep_time_lo)}–{fmt_elapsed(rep_time_hi)}")
            pct_str = f"{lo}–{hi}% {ref}" if lo != hi else f"{lo}% {ref}"
            segs.append((
                f"{reps_str} × {dist_label} @ {pct_str}",
                f"~{total_hard_mi:.1f} mi total",
                pace_str_for(pct),
                f"Each rep: {time_str}. Recovery: {jog}"
            ))
            segs.append(("Cooldown", "~1–2 mi", fmt_range(gps + 60, gps + 90), "Easy jog"))
            return segs

    # 3) Continuous effort: e.g. "7 mi at 85% 5k" or "9–10 mi at 100% MP"
    m = re.search(r"(\d+(?:\.\d+)?)(?:[-–](\d+(?:\.\d+)?))?\s*mi\s*at\s*([^,]+)$", text, re.IGNORECASE)
    if m:
        d_lo = float(m.group(1))
        d_hi = float(m.group(2)) if m.group(2) else d_lo
        pct = find_pct_pace(m.group(3))
        if pct:
            lo, hi, ref = pct
            base = fivek_p if ref == "5K" else mp_p
            pace_lo = base / (hi / 100)
            pace_hi = base / (lo / 100)
            total_time_lo = d_lo * pace_hi
            total_time_hi = d_hi * pace_lo
            d_str = f"{d_lo:g} mi" if d_lo == d_hi else f"{d_lo:g}–{d_hi:g} mi"
            pct_str = f"{lo}–{hi}% {ref}" if lo != hi else f"{lo}% {ref}"
            time_str = f"{fmt_elapsed(total_time_lo)}–{fmt_elapsed(total_time_hi)}"
            segs = segs[:-1] if segs and segs[-1][0] == "Warmup" else segs  # keep warmup
            segs.append((
                f"Continuous @ {pct_str}",
                d_str,
                pace_str_for(pct),
                f"Total elapsed: {time_str}"
            ))
            segs.append(("Cooldown", "~1–2 mi", fmt_range(gps + 60, gps + 90), "Easy jog"))
            return segs

    # 4) Kenyan-style progression — describe the concept
    if "Kenyan-style" in text or "kenyan-style" in text.lower():
        d = re.search(r"(\d+(?:\.\d+)?)\s*mi", text)
        dist = f"{d.group(1)} mi" if d else f"~{6} mi"
        segs = []
        segs.append((
            "Kenyan-style progression",
            dist,
            fmt_range(gps + 30, gps + 75),
            "Start at easy/long pace, progressively pick up to finish near or at MP"
        ))
        segs.append(("Finish effort (last ~1 mi)", "", fmt_pace(gps), "Should feel strong but controlled"))
        return segs

    # 5) Ladder / set patterns:
    #    "2 sets of 4-3-2-1 min at 96-98-100-102% 5k w/ 1 min mod / 2-3 min jog"
    #    "4 × (3-2-1 min at 98-100-102% 5k w/ 1-1-2 min jog)"
    #    "3-2-1-3-2-1 km at 86–88% 5k w/ 2 min walk"
    set_patterns = [
        r"(\d+)\s*sets?\s*of\s*([\d-]+)\s*(min|km|m(?!i)|mi)\s*at\s*([\d-]+)\s*%\s*(5k|MP)(?:\s*w/\s*(.+))?",
        r"(\d+)\s*×\s*\(\s*([\d-]+)\s*(min|km|m(?!i)|mi)\s*at\s*([\d-]+)\s*%\s*(5k|MP)(?:\s*w/\s*([^)]+))?\)",
    ]
    for pat in set_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            n_sets = int(m.group(1))
            durations = [float(x) for x in m.group(2).split("-")]
            unit = m.group(3).lower()
            pcts = [int(x) for x in m.group(4).split("-")]
            ref = m.group(5).upper()
            recovery = m.group(6) or "jog"

            # If pcts shorter than durations, repeat pcts; if pcts longer, the prescription
            # is a ladder where each duration has its own pct. Most ME workouts pair them 1-to-1.
            # Pad pcts to match durations length.
            if len(pcts) < len(durations):
                # Same pct for all reps in ladder
                pcts = [pcts[0]] * len(durations) if len(pcts) == 1 else pcts + [pcts[-1]] * (len(durations) - len(pcts))

            base = fivek_p if ref == "5K" else mp_p

            # Build the per-rep table with exact pace + time/distance
            sets_to_show = 1 if n_sets > 3 else n_sets
            for set_i in range(sets_to_show):
                if n_sets > 1:
                    segs.append((f"— Set {set_i+1} of {n_sets} —", "", "", ""))
                for rep_i, dur in enumerate(durations):
                    pct = pcts[rep_i] if rep_i < len(pcts) else pcts[-1]
                    target_pace = base / (pct / 100)
                    if unit == "min":
                        dist_mi = dur * 60 / target_pace
                        time_str = fmt_elapsed(dur * 60)
                        label = f"Rep {rep_i+1}: {dur:g} min @ {pct}% {ref}"
                        dist_str = f"{dist_mi:.2f} mi"
                    elif unit == "km":
                        dist_mi = dur * 0.621371
                        time_secs = dist_mi * target_pace
                        time_str = fmt_elapsed(time_secs)
                        label = f"Rep {rep_i+1}: {dur:g} km @ {pct}% {ref}"
                        dist_str = f"{dur:g} km"
                    elif unit == "m":
                        dist_mi = dur / 1609.34
                        time_secs = dist_mi * target_pace
                        time_str = fmt_elapsed(time_secs)
                        label = f"Rep {rep_i+1}: {dur:g}m @ {pct}% {ref}"
                        dist_str = f"{dur:g}m"
                    else:  # mi
                        dist_mi = dur
                        time_secs = dist_mi * target_pace
                        time_str = fmt_elapsed(time_secs)
                        label = f"Rep {rep_i+1}: {dur:g} mi @ {pct}% {ref}"
                        dist_str = f"{dur:g} mi"
                    effort = effort_for_pct(pct, pct, ref)
                    segs.append((label, dist_str, fmt_pace(target_pace),
                                 f"Run for {time_str} at {fmt_pace(target_pace)}. {effort}"))

            if n_sets > sets_to_show:
                segs.append((f"↻ Repeat for {n_sets} total sets", "—", "—", f"Pattern above × {n_sets}."))
            segs.append(("Recovery between reps", "—", "—", recovery.strip()))
            segs.append(("Cooldown", "~1–2 mi", fmt_range(gps + 60, gps + 90), "Easy jog to flush the legs and bring HR down."))
            return segs

    # 6) Explicit alternating segments inside parens, e.g. "5 × (1600m at 105–107% MP, 400m at 95–98% MP)"
    paren_alt = re.search(r"(\d+)\s*×\s*\((.+)\)", text)
    if paren_alt:
        n = int(paren_alt.group(1))
        inner = paren_alt.group(2)
        # Parse comma-separated segments
        parts = [p.strip() for p in inner.split(",")]
        parsed_parts = []
        for p in parts:
            # Try to extract distance/time + pct
            d = re.search(r"(\d+(?:\.\d+)?)\s*(km|m(?!i)|mi|min)\s*at\s*(\d+)(?:[-–](\d+))?\s*%\s*(5k|MP)", p, re.IGNORECASE)
            if d:
                amt = float(d.group(1))
                unit = d.group(2).lower()
                pct_lo = int(d.group(3)); pct_hi = int(d.group(4)) if d.group(4) else pct_lo
                ref = d.group(5).upper()
                parsed_parts.append((amt, unit, pct_lo, pct_hi, ref))
            else:
                parsed_parts.append(("recovery", p))

        if parsed_parts and isinstance(parsed_parts[0], tuple) and parsed_parts[0][0] != "recovery":
            # For workouts with many sets, show only set 1 in detail + a note
            sets_to_show = 1 if n > 3 else n
            for set_i in range(sets_to_show):
                if n > 1:
                    segs.append((f"— Set {set_i+1} of {n} —", "", "", ""))
                for rep_i, pp in enumerate(parsed_parts):
                    if pp[0] == "recovery":
                        segs.append(("Recovery", "—", "—", pp[1]))
                        continue
                    amt, unit, pct_lo, pct_hi, ref = pp
                    base = fivek_p if ref == "5K" else mp_p
                    pace_secs = base / (pct_hi / 100)  # use the faster end of range
                    if unit == "km":
                        dist_mi = amt * 0.621371
                        dist_str = f"{amt:g} km"
                        time_str = fmt_elapsed(dist_mi * pace_secs)
                    elif unit == "m":
                        dist_mi = amt / 1609.34
                        dist_str = f"{amt:g}m"
                        time_str = fmt_elapsed(dist_mi * pace_secs)
                    elif unit == "mi":
                        dist_mi = amt
                        dist_str = f"{amt:g} mi"
                        time_str = fmt_elapsed(dist_mi * pace_secs)
                    else:  # min
                        dist_mi = amt * 60 / pace_secs
                        dist_str = f"~{dist_mi:.2f} mi"
                        time_str = fmt_elapsed(amt * 60)
                    pct_str = f"{pct_lo}–{pct_hi}% {ref}" if pct_lo != pct_hi else f"{pct_lo}% {ref}"
                    pace_disp = pace_for_pct(pct_lo, pct_hi, base) if pct_lo != pct_hi else fmt_pace(pace_secs)
                    effort = effort_for_pct(pct_lo, pct_hi, ref)
                    segs.append((f"Segment {rep_i+1}: {pct_str}", dist_str, pace_disp,
                                 f"Run for {time_str} at this pace. {effort}"))
            if n > sets_to_show:
                segs.append((f"↻ Repeat for {n} total sets", "—", "—", f"Pattern above × {n}. Recovery between sets as prescribed."))
            segs.append(("Cooldown", "~1–2 mi", fmt_range(gps + 60, gps + 90), "Easy jog to flush the legs and bring HR down."))
            return segs

    # 7) Hyphenated ladder of distances at single pct, e.g. "3-2-1-3-2-1 km at 86–88% 5k w/ 2 min walk"
    ladder = re.search(r"^([\d-]+)\s*(km|m(?!i)|mi)\s*at\s*(\d+)(?:[-–](\d+))?\s*%\s*(5k|MP)(?:\s*w/\s*(.+))?", text, re.IGNORECASE)
    if ladder:
        amounts = [float(x) for x in ladder.group(1).split("-")]
        unit = ladder.group(2).lower()
        pct_lo = int(ladder.group(3)); pct_hi = int(ladder.group(4)) if ladder.group(4) else pct_lo
        ref = ladder.group(5).upper()
        recovery = ladder.group(6) or "jog"
        base = fivek_p if ref == "5K" else mp_p
        pace_secs = base / (pct_hi / 100)
        for rep_i, amt in enumerate(amounts):
            if unit == "km":
                dist_mi = amt * 0.621371
                dist_str = f"{amt:g} km"
            elif unit == "m":
                dist_mi = amt / 1609.34
                dist_str = f"{amt:g}m"
            else:
                dist_mi = amt
                dist_str = f"{amt:g} mi"
            time_str = fmt_elapsed(dist_mi * pace_secs)
            pace_disp = pace_for_pct(pct_lo, pct_hi, base) if pct_lo != pct_hi else fmt_pace(pace_secs)
            pct_str = f"{pct_lo}–{pct_hi}% {ref}" if pct_lo != pct_hi else f"{pct_lo}% {ref}"
            effort = effort_for_pct(pct_lo, pct_hi, ref)
            segs.append((f"Rep {rep_i+1}: {dist_str} @ {pct_str}", dist_str, pace_disp,
                         f"Should take ~{time_str}. {effort}"))
        segs.append(("Recovery between reps", "—", "—", recovery.strip()))
        segs.append(("Cooldown", "~1–2 mi", fmt_range(gps + 60, gps + 90), "Easy jog to flush the legs and bring HR down."))
        return segs

    # 8) Final fallback — show prescription verbatim with reference paces
    segs.append((
        "Full session",
        "—",
        "See prescription",
        note
    ))
    segs.append(("Your 5K pace (est.)",  "—", fmt_pace(fivek_p), "From Riegel formula vs marathon goal"))
    segs.append(("Your MP (goal)",       "—", fmt_pace(mp_p),    "Marathon goal pace"))
    return segs

def total_miles_placeholder_unused(): return 0  # avoid NameError in fallback branch

def workout_segments(wtype, total_miles, gps, note=None):
    easy_p  = fmt_range(gps + 60, gps + 90)   # 60–90 sec/mi slower than MP
    long_p  = fmt_range(gps + 45, gps + 75)   # 45–75 sec/mi slower than MP
    tempo_p = fmt_range(gps - 25, gps - 15)   # 15K to HM race pace (Pfitz LT)
    vo2_p   = fmt_range(gps - 70, gps - 50)   # ~60 sec/mi faster than MP
    mp_p    = fmt_pace(gps)
    rec_p   = fmt_range(gps + 80, gps + 105)  # very easy recovery jog

    # Marathon Excellence workouts: parse the verbatim note into structured segments
    if wtype in ("me_primary", "me_secondary", "me_weekend"):
        parsed = parse_me_segments(note, gps) if note else []
        if parsed:
            # Prepend verbatim prescription at the top for reference
            header = [("Prescription", "—", "—", note)] if note else []
            return header + parsed
        return [("Session", f"~{total_miles} mi", "—", note or "See book")]

    if wtype == "easy":
        return [("Full run", f"{total_miles} mi", easy_p, "Conversational effort throughout — you should be able to speak full sentences")]

    elif wtype == "long":
        easy_m = round(total_miles * 0.75, 1)
        mp_m   = round(total_miles - easy_m, 1)
        return [
            ("Easy portion", f"{easy_m} mi", long_p, "Relaxed aerobic effort"),
            ("Final portion (optional)", f"{mp_m} mi", mp_p, "Finish at marathon pace only if feeling strong — skip if fatigued"),
        ]

    elif wtype == "tempo":
        wu = min(2.0, round(total_miles * 0.20, 1))
        cd = min(2.0, round(total_miles * 0.20, 1))
        lt = round(total_miles - wu - cd, 1)
        return [
            ("Warmup", f"{wu} mi", easy_p, "Easy effort, gradually loosening up"),
            ("Lactate threshold", f"{lt} mi", tempo_p, "Comfortably hard — labored breathing, few words. This is the key effort"),
            ("Cooldown", f"{cd} mi", easy_p, "Easy effort, flush the legs"),
        ]

    elif wtype == "vo2":
        wu = min(2.0, round(total_miles * 0.18, 1))
        cd = min(2.0, round(total_miles * 0.18, 1))
        interval_block = round(total_miles - wu - cd, 1)
        if interval_block <= 3.5:
            n_reps = 5; rep_m_per = 1000
            rep_str = "5 × 1000m"
        elif interval_block <= 5.0:
            n_reps = 6; rep_m_per = 1000
            rep_str = "6 × 1000m or 5 × 1200m"
        elif interval_block <= 6.5:
            n_reps = 6; rep_m_per = 1200
            rep_str = "6 × 1200m"
        else:
            n_reps = 8; rep_m_per = 1200
            rep_str = "8 × 1200m"
        hard_m = round(n_reps * rep_m_per / 1609.34, 1)

        # Per Pfitz: recovery jog duration ≈ equal to interval duration (not fixed 400m).
        # Recovery pace = very easy, 90-120 sec/mi slower than MP (slower than easy runs).
        # For a rep of rep_m_per meters at VO2 pace (gps - 60 sec/mi):
        vo2_pace_spm = gps - 60  # approx center of VO2 range
        rep_time_secs = (rep_m_per / 1609.34) * vo2_pace_spm
        # Recovery pace: genuinely conversational — slower than easy runs
        rec_pace_spm = gps + 100  # ~100 sec/mi slower than MP
        rec_dist_per = round(rep_time_secs / rec_pace_spm, 2)  # miles of recovery per rep
        rec_m = round((n_reps - 1) * rec_dist_per, 1)
        rec_time_str = f"{int(rep_time_secs // 60)}:{int(rep_time_secs % 60):02d}"
        rec_pace_fmt = fmt_pace(rec_pace_spm)

        actual_subtotal = hard_m + rec_m + wu + cd
        diff = total_miles - actual_subtotal
        if abs(diff) > 0.3:
            cd = max(1.0, round(cd + diff, 1))

        return [
            ("Warmup", f"{wu} mi", easy_p, "Easy jog — get loose, add 4-6 strides at the end"),
            (f"Intervals ({rep_str})", f"{hard_m} mi", vo2_p, "5K race effort. Hard but controlled — not an all-out sprint"),
            (f"Recovery jogs ({n_reps - 1} × ~{rec_time_str})", f"{rec_m} mi",
             "jog / walk",
             f"Jog or walk for ≈ the same duration as the rep (~{rec_time_str} each). "
             f"No pace target — go as slow as you need. Don't start the next rep until breathing is fully under control."),
            ("Cooldown", f"{cd} mi", easy_p, "Easy jog home — shake out the legs"),
        ]

    elif wtype == "race":
        return [
            ("Miles 1–13.1 (first half)", "13.1 mi", mp_p, "Disciplined and patient — resist the crowd and adrenaline"),
            ("Miles 13.1–18 (second half, early)", "4.9 mi", mp_p, "Stay locked in. This stretch decides the race"),
            ("Miles 18–22 (the wall zone)", "4 mi", mp_p, "Dig deep. Shorten stride, stay relaxed, keep turnover high"),
            ("Miles 22–26.2 (finish)", "4.2 mi", fmt_pace(gps - 10), "Give what you have — controlled aggression"),
        ]

    return [("Full run", f"{total_miles} mi", fmt_pace(gps + 75), "")]

# ── pill styles ───────────────────────────────────────────────
PILL_STYLE = {
    "easy":   ("rgba(93,202,165,0.15)",  "#085041", "#5DCAA5"),
    "long":   ("rgba(155,143,232,0.15)", "#3C3489", "#9b8fe8"),
    "tempo":  ("rgba(232,168,37,0.15)",  "#633806", "#e8a825"),
    "vo2":    ("rgba(224,87,87,0.15)",   "#791F1F", "#e05757"),
    "race":   ("#FC4C02",                "#ffffff", "#FC4C02"),
    "actual": ("rgba(91,163,232,0.15)",  "#0C447C", "#5ba3e8"),
    "both":   ("rgba(93,202,165,0.2)",   "#065f46", "#5DCAA5"),
    "missed": ("rgba(224,87,87,0.12)",   "#991b1b", "#e05757"),
}
WTYPE_LABEL = dict(
    easy="Easy run", long="Long run", tempo="Lactate threshold", vo2="VO2 max", race="Race day",
    me_primary="Primary workout", me_secondary="Secondary workout", me_weekend="Weekend workout",
)
WTYPE_PURPOSE = dict(
    easy="Aerobic base building and active recovery.",
    long="Builds endurance, fat oxidation, and mental toughness. The most important run of the week.",
    tempo="Raises lactate threshold — the pace you can sustain for extended periods.",
    vo2="Increases maximal aerobic capacity. High stress, high reward.",
    race="Your goal marathon. Patient first half — the race truly begins at mile 18.",
    me_primary="Main quality session for the week. The most important workout.",
    me_secondary="Second quality session of the week, usually lower intensity than the primary.",
    me_weekend="Long run or marathon-specific session. Often the highest volume of the week.",
)
