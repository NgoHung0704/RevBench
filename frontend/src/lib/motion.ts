// Shared motion tokens — the single source of truth for the app's motion system.
// Calm, eased, purposeful: short durations, a gentle ease-out with no overshoot.
// Mirrors the CSS vars in globals.css. See docs/DESIGN_BRIEF.md §6.

export const EASE = [0.22, 1, 0.36, 1] as const; // gentle ease-out

export const DUR = {
  micro: 0.15, // hover / focus micro-interactions
  enter: 0.3, // entrances / transitions
  page: 0.34, // page / route
  draw: 0.7, // draw-ins (sparkline, ring, chart wipe), bar fills
} as const;

// 32ms per card; entrance delays are capped (see TickerCard) so a 15-card grid
// settles within ~0.36s and never feels slow.
export const STAGGER = 0.032;
