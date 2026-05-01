"""Training plan generation logic.

Ported from the Streamlit app. Pure Python — no Streamlit dependencies.
"""
from datetime import date, timedelta

PLANS = {
    "pfitz-18-55":  dict(kind="pfitz", name="Pfitz 18/55", weeks=18, peak_mpw=55, desc="18-week, peaks at 55 mpw"),
    "pfitz-18-70":  dict(kind="pfitz", name="Pfitz 18/70", weeks=18, peak_mpw=70, desc="18-week, peaks at 70 mpw"),
    "pfitz-12-55":  dict(kind="pfitz", name="Pfitz 12/55", weeks=12, peak_mpw=55, desc="12-week, peaks at 55 mpw"),
    "pfitz-12-70":  dict(kind="pfitz", name="Pfitz 12/70", weeks=12, peak_mpw=70, desc="12-week, peaks at 70 mpw"),
    "me-gale-70":   dict(kind="me", me_plan="gale",    weeks=18, peak_mpw=70, name="ME Gale 70",    desc="Marathon Excellence — 18-week Gale, peaks at 70 mpw"),
    "me-gale-80":   dict(kind="me", me_plan="gale",    weeks=18, peak_mpw=80, name="ME Gale 80",    desc="Marathon Excellence — 18-week Gale, peaks at 80 mpw"),
    "me-tornado-85":dict(kind="me", me_plan="tornado", weeks=18, peak_mpw=85, name="ME Tornado 85", desc="Marathon Excellence — 18-week Tornado, peaks at 85 mpw"),
    "me-tornado-95":dict(kind="me", me_plan="tornado", weeks=18, peak_mpw=95, name="ME Tornado 95", desc="Marathon Excellence — 18-week Tornado, peaks at 95 mpw"),
}

# ── Marathon Excellence plans (John Davis) ──────────────────
# Each week: (primary_workout, secondary_workout_or_None, weekend_workout, gale_70_mi, gale_80_mi)
# For Gale and Tornado, indexes 3 and 4 are the two mileage variants
ME_GALE = [
    ("6 mi Kenyan-style progression run",                            "8 × 3 min at 90–92% 5k w/ 1 min jog",             "9–10 × 2 min at 100% 5k w/ 1.5 min jog",                                  50, 55),
    ("7 mi Kenyan-style progression run",                            "6 mi at 85% 5k",                                  "5 mi easy + 3 sets of: 1.5 mi at 88–90% 5k, 0.5 mi moderate",            55, 60),
    ("4 × (3-2-1 min at 98-100-102% 5k w/ 1-1-2 min jog)",           "7 × 4 min at 90–92% 5k w/ 1 min jog",             "12–13 mi at 80% 5k through hills",                                        60, 65),
    ("7 mi at 85% 5k",                                               None,                                              "14–15 mi easy through hills",                                             50, 55),
    ("6 × 5 min at 90–92% 5k w/ 1 min jog",                          "8 × 1 km at 95% 5k w/ 2 min jog",                 "8 mi Kenyan-style progression w/ fast finish",                            60, 67),
    ("8 mi at 85% 5k",                                               "8 × 800m at 100% 5k w/ 2–3 min walk/jog",         "14–15 mi at 80% 5k",                                                      64, 72),
    ("5 × 1 mi at 95% 5k w/ 3 min jog",                              "6–7 × (1200m at 90–92% 5k, 400m at 80% 5k)",     "16–18 mi easy through hills",                                             68, 76),
    ("9–10 mi at 100% MP",                                           None,                                              "4 × 2 km at 108–110% MP w/ 3–4 min jog",                                  55, 63),
    ("5 × (1600m at 105–107% MP, 400m at 95–98% MP)",                None,                                              "16–18 mi at 90–92% MP",                                                   70, 80),
    ("3 × (2 km at 108% MP, 2 min jog, 1 km at 110% MP, 5 min walk/jog)", None,                                         "10–11 mi at 100% MP",                                                     70, 80),
    ("9–10 × (1 km at 105% MP, 1 km at 90% MP)",                     None,                                              "18–20 mi at 90–92% MP",                                                   70, 80),
    ("3 × 3 km at 108–110% MP w/ 4–5 min walk/jog",                  None,                                              "8 × (2 km at 100% MP, 1 km at 90% MP)",                                   58, 68),
    ("6–7 × (2 km at 105% MP, 1 km at 90% MP)",                      None,                                              "5 mi at 90%; 5 mi at 92%; 5 mi at 94%; 3–5 mi at 96% MP",                 70, 80),
    ("12–15 × 500m at 108–110% MP w/ 30–45 sec walk",                None,                                              "6 × (3 km at 100% MP, 1 km at 90% MP)",                                   68, 73),
    ("3.5–5.5 mi at 105% MP",                                        None,                                              "20–21 mi at 95% MP",                                                      63, 68),
    ("8 mi Kenyan-style progression run",                            None,                                              "5 × (4 km at 100% MP, 1 km at 90% MP)",                                   63, 68),
    ("7–8 × (1 km at 103–105% MP, 1 km at 92–94% MP)",               None,                                              "5–6 × 1200m at 107–110% MP w/ 2–3 min jog",                               55, 60),
    ("5–6 × 4 min at 103–106% MP w/ 1 min jog",                      None,                                              "Marathon",                                                                26, 26),
]

ME_TORNADO = [
    ("7 mi Kenyan-style progression run",                            "8–9 × 3 min at 90–92% 5k w/ 45 sec jog",          "7 mi easy + 5 mi progressing moderate to 90% 5k + 1 mi easy",            60, 65),
    ("7 mi at 85% 5k",                                               "10 × 2 min at 100–102% 5k w/ 1.5 min jog",        "8 mi Kenyan-style progression run",                                      65, 70),
    ("8 × 1 km at 95% 5k w/ 2 min jog",                              "8 mi at 85% 5k",                                  "13–14 mi at 80% 5k through rolling hills",                               70, 76),
    ("2 sets of 4-3-2-1 min at 96-98-100-102% 5k w/ 1 min mod / 2–3 min jog", None,                                      "7–8 × 4 min at 90–92% 5k w/ 1 min jog",                                  60, 65),
    ("5 × 1 mi at 95% 5k w/ 3 min jog",                              "9–10 mi at 85% 5k",                               "16–18 mi easy through rolling hills",                                    72, 78),
    ("3-2-1-3-2-1 km at 86–88% 5k w/ 2 min walk",                    "7 × (1200m at 90–92% 5k, 400m at 80% 5k)",        "15–16 mi at 80% 5k through rolling hills",                               78, 84),
    ("3 × (2 km at 108% MP, 2 min jog, 1 km at 110–112% MP, 4–5 min jog)", None,                                         "10–11 mi at 100% MP",                                                    83, 90),
    ("6 × (1600m at 105–107% MP, 400m at 95–98% MP)",                None,                                              "4-1, 3-1, 2-1, 1-1 km at 101–103% / 105% MP w/ 2 min walk between all",  75, 82),
    ("5 × 2 km at 108–110% MP w/ 4 min jog",                         None,                                              "17–19 mi at 90–92% MP through rolling hills",                            85, 95),
    ("AM: 7 × 1 km at 103–106% MP w/ 1 min jog / PM: 12 × 500m at 108–110% MP w/ 30 sec walk", None,                     "12–13 mi at 100% MP",                                                    85, 95),
    ("10 × (1 km at 105% MP, 1 km at 90–92% MP)",                    None,                                              "5-5-5-(3 to 5) mi at 90-92-94-96% MP",                                   85, 95),
    ("AM: 5–6 × 2 km at 103% MP w/ 2 min walk / PM: 4 × 500m at 108–110% MP w/ 30 sec walk; 4 min rest; 3–5 km at 108–110% MP", None, "6 × (3 km at 100% MP, 1 km at 90% MP)",                                  80, 90),
    ("4–5 × 3 km at 103–105% MP w/ 2–3 min walk",                    None,                                              "20–22 mi at 95% MP",                                                     74, 82),
    ("AM: 3-2-1-1 km at 102–106% MP w/ 2 min walk / PM: 12–15 × 400m at 108–110% MP w/ 25 sec walk", None,               "6 × (4 km at 100% MP, 1 km at 90% MP)",                                  78, 83),
    ("8–10 × 3 min at 104–107% MP w/ 30 sec jog",                    None,                                              "7-6-5-(2 to 4) mi at 92-94-96-98% MP",                                   73, 83),
    ("12 × 500m at 108–110% MP w/ 30 sec walk",                      None,                                              "6-5-4-3-2-1 km at 98–102% w/ 1 km at 90% MP",                            70, 81),
    ("8 × (1 km at 103–105% MP, 1 km at 92–94% MP)",                 None,                                              "2 × 2 km at 107% MP; 2–4 × 1 km at 108–110% MP w/ 3 min jog",            63, 70),
    ("6–8 × 3 min at 105–107% MP w/ 45 sec jog",                     None,                                              "Marathon",                                                               26, 26),
]

ME_SCHEDULES = dict(gale=ME_GALE, tornado=ME_TORNADO)

# Week-by-week template for Pfitz 18-week plans.
# Each entry: (workout_type, long_run_mi, weekly_total_mi_for_55_plan)
# - Workout type cycles through tempo/vo2/easy across the plan
# - long_mi and weekly_total are the actual Pfitz 18/55 prescriptions
# 70-mpw plans use a separate scaling factor so they ramp realistically
PFITZ_18_TEMPLATE = [
    # (workout, long, total_55)   # phase notes
    ("tempo", 12,  33),  # wk 1  endurance build
    ("vo2",   13,  37),  # wk 2
    ("tempo", 15,  42),  # wk 3
    ("easy",  12,  32),  # wk 4  recovery week (no quality)
    ("tempo", 16,  44),  # wk 5
    ("vo2",   15,  46),  # wk 6
    ("tempo", 17,  48),  # wk 7
    ("easy",  13,  37),  # wk 8  recovery
    ("vo2",   18,  50),  # wk 9  LT/endurance phase
    ("tempo", 18,  52),  # wk 10
    ("vo2",   20,  55),  # wk 11 PEAK
    ("tempo", 14,  44),  # wk 12 recovery
    ("tempo", 20,  55),  # wk 13 race-prep
    ("vo2",   18,  55),  # wk 14
    ("tempo", 20,  55),  # wk 15
    ("easy",  16,  43),  # wk 16 taper begins
    ("tempo", 14,  39),  # wk 17
    ("easy",   8,  26),  # wk 18 race week (8mi long is shake-out, race separate)
]

# Pfitz 70-plan totals (different from a simple scale of 55)
# Source: Pfitz 18/70 published progression
PFITZ_18_TOTAL_70 = [45, 48, 53, 42, 55, 58, 62, 50, 65, 67, 70, 55, 68, 70, 70, 55, 50, 30]

def expand_pfitz_week(workout_type, long_mi, total_mi):
    """Given a workout type, long run miles, and weekly total, distribute remaining miles
    across easy days. Returns a list of run dicts (day numbering will be reassigned later).
    Layout: long run + 1 quality + remaining easy days summing to (total - long - quality_mi).
    """
    # Quality session length scales with weekly total
    if workout_type == "easy":
        # Recovery week: no quality, use a medium-long instead
        quality_mi = round(total_mi * 0.18)
        runs = [
            dict(d=0, t="long", m=long_mi),
            dict(d=99, t="easy", m=quality_mi),  # placeholder day, redistributed later
        ]
    else:
        quality_mi = max(7, round(total_mi * 0.18))
        runs = [
            dict(d=0, t="long", m=long_mi),
            dict(d=99, t=workout_type, m=quality_mi),
        ]
    remaining = total_mi - long_mi - quality_mi
    # Distribute remaining across 3 easy days for 5-day weeks (will become 4 for 6-day weeks
    # via the auto-add-6th-day logic)
    n_easy_days = 3
    if n_easy_days > 0 and remaining > 0:
        per_day = remaining / n_easy_days
        # Vary slightly: shortest day before quality, medium-long mid-week, easy near rest
        easy_mileages = [
            max(3, round(per_day * 0.85)),
            max(3, round(per_day * 1.15)),
            max(3, round(per_day * 1.0)),
        ]
        # Fix rounding so total matches
        delta = remaining - sum(easy_mileages)
        easy_mileages[1] += delta
        for em in easy_mileages:
            if em > 0:
                runs.append(dict(d=99, t="easy", m=em))
    return runs

# Generate BASE_18_55 from the template
BASE_18_55 = []
for i, (wo, long_mi, total) in enumerate(PFITZ_18_TEMPLATE):
    runs = expand_pfitz_week(wo, long_mi, total)
    BASE_18_55.append(dict(w=i+1, runs=runs))

# Generate BASE_18_70 — same workout types and long-run progression but higher totals
# Long runs in 70-plan are a bit longer too
LONG_RUN_BUMP_70 = {12:13, 13:14, 14:15, 15:16, 16:17, 17:18, 18:19, 20:21}  # +1 to longer runs
BASE_18_70 = []
for i, (wo, long_mi, _) in enumerate(PFITZ_18_TEMPLATE):
    long_70 = LONG_RUN_BUMP_70.get(long_mi, long_mi)
    runs = expand_pfitz_week(wo, long_70, PFITZ_18_TOTAL_70[i])
    BASE_18_70.append(dict(w=i+1, runs=runs))

# 12-week Pfitz plans are authored separately — they assume runners have an existing base
# (~75-80% of peak mileage). Source: Pfitz "Advanced Marathoning" describes 12-week as a
# compressed program for runners coming off another marathon cycle.
# Note: exact week-by-week numbers from the book aren't published online; these are
# best-effort approximations matching the documented structure (build → peak → taper)
# and the source noting "peak hit at week 5-6, several weeks in 60s" for 12/70.

# (workout, long_mi, total_55, total_70)
PFITZ_12_TEMPLATE = [
    ("tempo", 14, 42, 52),  # wk 1  endurance build
    ("vo2",   16, 46, 58),  # wk 2
    ("tempo", 17, 48, 62),  # wk 3
    ("easy",  13, 38, 48),  # wk 4  recovery/cutback
    ("vo2",   18, 50, 65),  # wk 5  LT/endurance phase
    ("tempo", 20, 55, 70),  # wk 6  PEAK
    ("vo2",   18, 52, 67),  # wk 7
    ("tempo", 20, 55, 70),  # wk 8  PEAK
    ("easy",  16, 44, 55),  # wk 9  recovery/cutback before race-prep
    ("tempo", 20, 55, 68),  # wk 10 race-prep peak
    ("easy",  14, 39, 50),  # wk 11 taper
    ("easy",   8, 26, 30),  # wk 12 race week
]

BASE_12_55 = []
BASE_12_70 = []
for i, (wo, long_mi, t55, t70) in enumerate(PFITZ_12_TEMPLATE):
    BASE_12_55.append(dict(w=i+1, runs=expand_pfitz_week(wo, long_mi, t55)))
    long_70 = LONG_RUN_BUMP_70.get(long_mi, long_mi)
    BASE_12_70.append(dict(w=i+1, runs=expand_pfitz_week(wo, long_70, t70)))

def redistribute_pfitz_days(week_runs, long_day=0, quality_day=3, rest_day=1):
    """Reassign day numbers based on user-configured preferences.
    Day convention: 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat.

    Defaults: long=Sun, quality=Wed, rest=Mon (standard Pfitz).
    For 5-day weeks (55-mpw plans), a 2nd rest is placed to maximize spacing.
    For 6-day weeks (70-mpw plans), only the user-selected rest day is used.
    """
    long_runs = [r for r in week_runs if r["t"] == "long"]
    other     = [r for r in week_runs if r["t"] != "long"]
    quality_types = {"tempo", "vo2", "race"}
    qualities = [r for r in other if r["t"] in quality_types]
    easies    = [r for r in other if r["t"] not in quality_types]

    n_runs = len(other) + len(long_runs)

    # All weekdays minus long_day and rest_day
    all_days = [0, 1, 2, 3, 4, 5, 6]
    available = [d for d in all_days if d not in {long_day, rest_day}]

    # For 5-day weeks, add a second rest day spaced to maximize gap from long_day and rest_day
    if n_runs == 5 and len(available) > 4:
        # Find the day that maximizes minimum distance from long_day and rest_day
        def min_dist(d):
            def cyclic(a, b): return min((a-b) % 7, (b-a) % 7)
            return min(cyclic(d, long_day), cyclic(d, rest_day), cyclic(d, quality_day))
        # Pick the day with greatest minimum distance from both rest and long
        # (excluding quality_day so we don't override the user's quality preference)
        candidates = [d for d in available if d != quality_day]
        if candidates:
            second_rest = max(candidates, key=lambda d: min(
                ((d - long_day) % 7, (long_day - d) % 7),
                ((d - rest_day) % 7, (rest_day - d) % 7)
            )[0])
            available = [d for d in available if d != second_rest]

    # Trim available to match run count (excluding long run, which goes on long_day)
    needed = n_runs - len(long_runs)  # how many non-long slots we need
    while len(available) > needed:
        # Drop the day adjacent to quality_day or long_day (least useful for an easy run)
        # Just drop from the end
        available.pop()

    placed = []
    # Place qualities — first one goes on user's quality_day, additional ones spaced out
    quality_slots = [quality_day]
    if len(qualities) > 1:
        # For multiple qualities, add a second slot far from the first
        for d in [(quality_day + 3) % 7, (quality_day + 4) % 7, (quality_day + 2) % 7]:
            if d in available and d != long_day and d != rest_day:
                quality_slots.append(d)
                break
    for i, q in enumerate(qualities):
        chosen = quality_slots[i] if i < len(quality_slots) else (available[0] if available else quality_day)
        placed.append(dict(d=chosen, t=q["t"], m=q["m"], **({"note":q["note"]} if "note" in q else {})))
        if chosen in available:
            available.remove(chosen)

    # Fill remaining with easies
    easies_sorted = sorted(easies, key=lambda r: r["m"])
    for e in easies_sorted:
        if not available:
            break
        chosen = available[0]
        placed.append(dict(d=chosen, t=e["t"], m=e["m"], **({"note":e["note"]} if "note" in e else {})))
        available.remove(chosen)

    # Add long run
    for lr in long_runs:
        placed.append(dict(d=long_day, t=lr["t"], m=lr["m"], **({"note":lr["note"]} if "note" in lr else {})))

    # Sort by display order (Mon → Sun)
    def display_order(d):
        return 7 if d == 0 else d
    return sorted(placed, key=lambda r: display_order(r["d"]))


def build_schedule(plan_key, long_day=0, quality_day=3, rest_day=1):
    p = PLANS[plan_key]
    if p.get("kind") == "me":
        return build_me_schedule(p)
    # Pick the right pre-built base schedule (no scaling — each is authored to its peak mileage)
    if p["weeks"] == 18 and p["peak_mpw"] == 55:   src = BASE_18_55
    elif p["weeks"] == 18 and p["peak_mpw"] == 70: src = BASE_18_70
    elif p["weeks"] == 12 and p["peak_mpw"] == 55: src = BASE_12_55
    elif p["weeks"] == 12 and p["peak_mpw"] == 70: src = BASE_12_70
    else:
        # Fallback to 18/55 scaled if a non-standard plan slips through
        scale = p["peak_mpw"] / 55
        src = [dict(w=wk["w"], runs=[dict(**r, m=round(r["m"]*scale)) for r in wk["runs"]])
               for wk in BASE_18_55]
    weeks = []
    is_high_volume = p["peak_mpw"] >= 70  # 70+ mpw plans run 6 days/week
    for i, wk in enumerate(src):
        runs = [dict(d=r["d"], t=r["t"], m=r["m"]) for r in wk["runs"]]
        if is_high_volume:
            # Add a 6th easy run for high-volume plans; mileage already targets the right total
            # so this 6th run takes a small slice from existing easies (recompute distribution)
            week_total = sum(r["m"] for r in runs)
            if len(runs) < 6:
                rec_mi = max(3, min(6, round(week_total * 0.08)))
                # Reduce the largest easy run to make room
                easies = [r for r in runs if r["t"] == "easy"]
                if easies:
                    biggest = max(easies, key=lambda r: r["m"])
                    biggest["m"] = max(3, biggest["m"] - rec_mi)
                runs.append(dict(d=99, t="easy", m=rec_mi))
        # Reassign days so rest is on Mon (and Fri for 5-day weeks), quality is mid-week,
        # and easies are spread across the rest of the week.
        runs = redistribute_pfitz_days(runs, long_day=long_day, quality_day=quality_day, rest_day=rest_day)
        weeks.append(dict(w=i+1, runs=runs))
    return weeks

def build_me_schedule(plan_meta):
    """Build Marathon Excellence week structure.
    Day convention: 0=Sun, 1=Mon, ..., 6=Sat. We use:
      Mon (d=1): rest (no run)
      Tue (d=2): primary workout
      Wed (d=3): easy
      Thu (d=4): secondary workout if present, else easy
      Fri (d=5): easy
      Sat (d=6): easy
      Sun (d=0): weekend workout (long)
    Easy miles are distributed to hit the weekly target.
    """
    sched_key = plan_meta["me_plan"]
    variant = 0 if plan_meta["peak_mpw"] in (70, 85) else 1
    raw = ME_SCHEDULES[sched_key]

    # Estimate workout mileage from the prescription text.
    # Approach: pull explicit mile ranges if present; otherwise use category defaults.
    # Since ME plans specify mileage via the weekly total column, the workout-level
    # estimates just need to be in the right ballpark so easy days get a sensible
    # remainder.
    def workout_miles(text, slot="primary"):
        import re
        if text is None: return 0
        if "Marathon" == text.strip(): return 26.2

        # Explicit mi pattern, e.g. "7 mi at 85%"  or  "16–18 mi easy"
        mi = re.findall(r"(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*mi(?!n)", text)
        if mi:
            total = 0
            for m in mi:
                lo = float(m[0]); hi = float(m[1]) if m[1] else lo
                total += (lo + hi) / 2
            # Weekend workouts with explicit miles = full workout miles (incl WU/CD embedded)
            return total

        # km-based: estimate total from the listed intervals + add WU/CD
        total_km = 0
        rep = re.search(r"(\d+)\s*×\s*\(([^)]+)\)", text)
        if rep:
            n = int(rep.group(1))
            inner_km = re.findall(r"(\d+(?:\.\d+)?)\s*km", rep.group(2))
            inner_m_match = re.search(r"(\d+)\s*m(?!i)", rep.group(2))
            total_km = n * sum(float(x) for x in inner_km)
            if inner_m_match: total_km += n * int(inner_m_match.group(1)) / 1000
        else:
            km_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*km", text)
            for m in km_matches:
                lo = float(m[0]); hi = float(m[1]) if m[1] else lo
                total_km += (lo + hi) / 2
            # treat "N × 500m" style too
            m_rep = re.findall(r"(\d+)\s*×\s*(\d+)\s*m(?!i)", text)
            for n, mm in m_rep:
                total_km += int(n) * int(mm) / 1000
        if total_km > 0:
            total_km += 4   # WU + CD
            return total_km * 0.621

        # Pure time-based intervals, fallback by slot
        defaults = dict(primary=7, secondary=7, weekend=9)
        return defaults.get(slot, 7)

    weeks = []
    for wi, row in enumerate(raw):
        primary, secondary, weekend, mi_a, mi_b = row
        week_total = mi_a if variant == 0 else mi_b

        is_race_week = (wi == len(raw) - 1)

        # Assign workout miles
        primary_mi   = round(workout_miles(primary,   slot="primary"), 1)
        secondary_mi = round(workout_miles(secondary, slot="secondary"), 1) if secondary else 0
        weekend_mi   = round(workout_miles(weekend,   slot="weekend"), 1)
        # Floors so estimates stay sensible even when text parsing falls short
        primary_mi   = max(primary_mi, 6)
        if secondary: secondary_mi = max(secondary_mi, 6)
        weekend_mi   = max(weekend_mi, 8 if not is_race_week else weekend_mi)

        if is_race_week:
            # Only schedule the marathon itself, plus light shake-outs in the week
            runs = [
                dict(d=2, t="easy_me",    m=5,   note=primary),
                dict(d=4, t="easy",       m=4),
                dict(d=6, t="easy",       m=3),
                dict(d=0, t="race",       m=26, note="Marathon"),
            ]
            weeks.append(dict(w=wi+1, runs=runs))
            continue

        # Cap workout mileage at the week total to prevent overshoot
        fixed_total = primary_mi + secondary_mi + weekend_mi
        if fixed_total > week_total:
            # scale down proportionally (rare — only if estimator overshoots)
            scale = week_total / fixed_total
            primary_mi   = round(primary_mi * scale, 1)
            secondary_mi = round(secondary_mi * scale, 1)
            weekend_mi   = round(weekend_mi * scale, 1)
            fixed_total  = primary_mi + secondary_mi + weekend_mi

        easy_budget = max(0, week_total - fixed_total)

        # Distribute easy miles with realistic cadence:
        #   Wed = recovery (after Tue primary) — shortest
        #   Fri = medium-long if primary was AM+PM or big; else medium
        #   Sat = recovery (before Sun long run) — shorter
        #   Thu = easy if no secondary
        # Absorb extra volume into Fri (medium-long day)
        if secondary is None:
            easy_days_idx = [3, 4, 5, 6]  # Wed, Thu, Fri, Sat
            weights = [0.18, 0.22, 0.38, 0.22]
        else:
            easy_days_idx = [3, 5, 6]  # Wed, Fri, Sat
            weights = [0.25, 0.50, 0.25]

        easy_miles_list = [round(easy_budget * w * 2) / 2 for w in weights]
        diff = round((easy_budget - sum(easy_miles_list)) * 2) / 2
        max_idx = weights.index(max(weights))
        easy_miles_list[max_idx] = max(0, easy_miles_list[max_idx] + diff)

        # Iteratively cap any single easy day based on weekly volume.
        # Higher-mileage weeks allow longer easy days (runners doing 90+ mpw
        # often have one medium-long day around 14–16 mi).
        if   week_total >= 90: EASY_CAP = 16
        elif week_total >= 75: EASY_CAP = 14
        elif week_total >= 60: EASY_CAP = 13
        else:                  EASY_CAP = 11
        for _ in range(5):
            over_indices = [i for i,m in enumerate(easy_miles_list) if m > EASY_CAP]
            if not over_indices: break
            for i in over_indices:
                overflow = easy_miles_list[i] - EASY_CAP
                easy_miles_list[i] = EASY_CAP
                # distribute only to days not already over cap
                others = [j for j in range(len(easy_miles_list)) if j not in over_indices and easy_miles_list[j] < EASY_CAP]
                if not others: break
                per = overflow / len(others)
                for j in others:
                    easy_miles_list[j] = round((easy_miles_list[j] + per) * 2) / 2

        runs = []
        runs.append(dict(d=2, t="me_primary", m=primary_mi, note=primary))
        if secondary:
            runs.append(dict(d=4, t="me_secondary", m=secondary_mi, note=secondary))
        for idx, em in zip(easy_days_idx, easy_miles_list):
            if em > 0:
                runs.append(dict(d=idx, t="easy", m=em))
        runs.append(dict(d=0, t="me_weekend", m=weekend_mi, note=weekend))

        weeks.append(dict(w=wi+1, runs=runs))

    return weeks

def build_planned_map(plan_key, race_date_str, long_day=0, quality_day=3, rest_day=1):
    schedule = build_schedule(plan_key, long_day=long_day, quality_day=quality_day, rest_day=rest_day)
    p = PLANS[plan_key]
    race_date = date.fromisoformat(race_date_str)

    # The schedule uses d=0 for Sunday, d=1..6 for Mon..Sat (Sun-first convention).
    # We display weeks Mon-Sun. plan_start = Monday of the first week of the plan.
    # Last week ends on race_date (a Sunday in the typical case). So:
    #   plan_start = Monday of race week - (weeks-1) weeks
    # "Monday of race week" = race_date - race_date.weekday()
    race_week_mon = race_date - timedelta(days=race_date.weekday())
    plan_start = race_week_mon - timedelta(weeks=p["weeks"]-1)

    # Helper: convert schedule's Sun-first day number (0=Sun..6=Sat) to Mon-first offset (0=Mon..6=Sun)
    def day_offset(d):
        return 6 if d == 0 else d - 1

    planned = {}
    for wi, wk in enumerate(schedule):
        for run in wk["runs"]:
            d = plan_start + timedelta(days=wi*7 + day_offset(run["d"]))
            ds = d.isoformat()
            if ds != race_date_str and d < race_date:
                planned[ds] = run
    planned[race_date_str] = dict(t="race", m=26)
    return planned, plan_start.isoformat()

def apply_swaps(planned_map, swaps):
    """Apply user day-swaps on top of the base planned map."""
    result = dict(planned_map)
    for ds, run in swaps.items():
        if run is None:
            result.pop(ds, None)
        else:
            result[ds] = run
    return result
