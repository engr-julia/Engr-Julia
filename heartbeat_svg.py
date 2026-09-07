"""
Generates an animated 'Coding Pulse' ECG-style SVG from daily GitHub
contribution counts.

Idle days  -> a normal, steady heartbeat (never flatlines).
Active days -> the beat for that day spikes taller and switches color,
               scaled by how many contributions happened.
The whole waveform scrolls continuously (like a real monitor feed),
achieved with two identical copies of the path animated side by side.
"""

import random

# ---------- config ----------
DAY_W       = 30      # px per day
N_DAYS      = 30       # how many days of history to show in one loop
H           = 220      # svg height
BASELINE_Y  = 130
IDLE_AMP    = 16        # px height of the normal idle heartbeat spike
MAX_AMP     = 85        # px height cap for a very active day
SECS_PER_DAY = 0.55     # animation speed: seconds of scroll per day

IDLE_COLOR   = "#39d353"   # GitHub-green, dim/idle beat
ACTIVE_COLOR = "#ff2d95"   # hot pink, active beat
GLOW_COLOR   = "#ff8fc9"
BG_TOP       = "#04121a"
BG_BOTTOM    = "#02080c"
GRID_COLOR   = "#0d3b33"


def day_path(local_x0, amp, baseline=BASELINE_Y, w=DAY_W):
    """Return SVG path 'd' data for one day's heartbeat unit, starting
    and ending on the baseline so consecutive days connect seamlessly."""
    x = local_x0
    b = baseline
    pts = [
        (x,             b),
        (x + w*0.12,    b),
        (x + w*0.20,    b - amp*0.22),   # small P wave
        (x + w*0.28,    b),
        (x + w*0.36,    b + amp*0.15),   # Q dip
        (x + w*0.42,    b - amp),        # R spike (the big one)
        (x + w*0.48,    b + amp*0.45),   # S dip
        (x + w*0.56,    b),
        (x + w*0.68,    b - amp*0.28),   # T wave
        (x + w*0.80,    b),
        (x + w,         b),
    ]
    d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f} "
    for px, py in pts[1:]:
        d += f"L {px:.1f},{py:.1f} "
    return d


def build_svg(counts, username="you"):
    """counts: list[int] of contribution counts, oldest -> newest,
    length should equal N_DAYS."""
    n = len(counts)
    total_w = n * DAY_W
    max_count = max(counts) if counts and max(counts) > 0 else 1

    def amp_for(c):
        if c <= 0:
            return IDLE_AMP
        scaled = IDLE_AMP + (c / max_count) * (MAX_AMP - IDLE_AMP)
        return min(scaled, MAX_AMP)

    def color_for(c):
        return ACTIVE_COLOR if c > 0 else IDLE_COLOR

    # Build one cycle's worth of day-paths (used twice, back to back, for
    # a seamless infinite scroll)
    day_elems = []
    for i, c in enumerate(counts):
        d = day_path(i * DAY_W, amp_for(c))
        color = color_for(c)
        glow = f'filter="url(#glow)"' if c > 0 else ""
        stroke_w = 3.4 if c > 0 else 2.2
        day_elems.append(
            f'<path d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="{stroke_w}" stroke-linecap="round" '
            f'stroke-linejoin="round" {glow} opacity="{0.95 if c>0 else 0.75}"/>'
        )
    cycle_svg = "\n      ".join(day_elems)

    dur = n * SECS_PER_DAY
    active_days = sum(1 for c in counts if c > 0)
    total_contribs = sum(counts)
    streak = 0
    for c in reversed(counts):
        if c > 0:
            streak += 1
        else:
            break

    svg = f'''<svg viewBox="0 0 900 {H}" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI', ui-monospace, Menlo, monospace">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{BG_TOP}"/>
      <stop offset="100%" stop-color="{BG_BOTTOM}"/>
    </linearGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3.2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{BG_TOP}" stop-opacity="1"/>
      <stop offset="6%" stop-color="{BG_TOP}" stop-opacity="0"/>
      <stop offset="94%" stop-color="{BG_TOP}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{BG_TOP}" stop-opacity="1"/>
    </linearGradient>
    <clipPath id="clip"><rect x="0" y="0" width="900" height="{H}" rx="14"/></clipPath>
  </defs>

  <g clip-path="url(#clip)">
    <rect width="900" height="{H}" fill="url(#bg)"/>

    <!-- grid -->
    <g stroke="{GRID_COLOR}" stroke-width="1" opacity="0.5">
      {"".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>' for x in range(0, 900, 30))}
      {"".join(f'<line x1="0" y1="{y}" x2="900" y2="{y}"/>' for y in range(0, H, 22))}
    </g>

    <!-- scrolling waveform: two copies back to back, animated left -->
    <g transform="translate(0,0)">
      <animateTransform attributeName="transform" type="translate"
        from="0 0" to="{-total_w} 0" dur="{dur:.2f}s"
        repeatCount="indefinite" calcMode="linear"/>
      <g>
        {cycle_svg}
      </g>
      <g transform="translate({total_w},0)">
        {cycle_svg}
      </g>
    </g>

    <!-- edge fade so the wave doesn't pop in/out abruptly -->
    <rect width="900" height="{H}" fill="url(#fade)"/>

    <!-- header -->
    <text x="20" y="30" fill="#e6ffe9" font-size="15" font-weight="600">{username}'s coding pulse</text>
    <text x="20" y="48" fill="#7fbfa0" font-size="11">always beating · brighter beat = a day you shipped</text>

    <!-- legend -->
    <circle cx="740" cy="24" r="5" fill="{IDLE_COLOR}"/>
    <text x="750" y="28" fill="#9fd6b3" font-size="11">idle</text>
    <circle cx="800" cy="24" r="5" fill="{ACTIVE_COLOR}"/>
    <text x="810" y="28" fill="#9fd6b3" font-size="11">shipped</text>

    <!-- stats -->
    <text x="20" y="{H-14}" fill="#7fbfa0" font-size="11">{total_contribs} contributions · {active_days}/{n} active days</text>
    <text x="770" y="{H-14}" fill="{ACTIVE_COLOR if streak>0 else "#7fbfa0"}" font-size="11">streak: {streak}d</text>

    <!-- pulsing "live" dot -->
    <circle cx="878" cy="20" r="4" fill="{ACTIVE_COLOR}">
      <animate attributeName="opacity" values="1;0.15;1" dur="1.4s" repeatCount="indefinite"/>
    </circle>
  </g>
  <rect width="900" height="{H}" rx="14" fill="none" stroke="#12463d" stroke-width="1"/>
</svg>'''
    return svg


if __name__ == "__main__":
    random.seed(7)
    # mock data: mostly idle, a few bursty days, a short current streak
    counts = [0]*N_DAYS
    for i in [2, 3, 8, 9, 10, 15, 21]:
        counts[i] = random.choice([1, 2, 4, 6])
    counts[-4:] = [3, 5, 2, 7]   # current streak

    svg = build_svg(counts, username="octocat")
    with open("/mnt/user-data/outputs/heartbeat_demo.svg", "w") as f:
        f.write(svg)
    print("wrote heartbeat_demo.svg")
