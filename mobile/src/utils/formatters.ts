/**
 * Formatters for dates, times, and durations.
 * Cross-platform compatible (iOS, Android, Web) without external date libraries.
 */

/**
 * Format an ISO timestamp (e.g. "2026-09-26T16:15:24.000Z") to a user-friendly string
 * such as "Today · 9:00 AM", "Yesterday · 7:30 PM", or "Sep 26 · 9:00 AM".
 */
export function formatTimestamp(isoString?: string | null): string {
  if (!isoString) return '—';

  const date = new Date(isoString);
  if (isNaN(date.getTime())) return '—';

  const now = new Date();
  const isToday =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const isYesterday =
    date.getFullYear() === yesterday.getFullYear() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getDate() === yesterday.getDate();

  // Time format e.g. "9:00 AM"
  let hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12; // 0 should be 12
  const timeStr = `${hours}:${minutes < 10 ? '0' : ''}${minutes} ${ampm}`;

  if (isToday) {
    return `Today · ${timeStr}`;
  }
  if (isYesterday) {
    return `Yesterday · ${timeStr}`;
  }

  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthName = months[date.getMonth()];
  const day = date.getDate();

  if (date.getFullYear() === now.getFullYear()) {
    return `${monthName} ${day} · ${timeStr}`;
  }

  return `${monthName} ${day}, ${date.getFullYear()} · ${timeStr}`;
}

/**
 * Returns the device's local calendar date in format "YYYY-MM-DD".
 * Avoids UTC timezone day-shift caused by `new Date().toISOString()`.
 */
export function getLocalDateString(date: Date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Format a date string (e.g. "YYYY-MM-DD") along with an optional created_at timestamp.
 */
export function formatCheckinDate(dateStr?: string | null, createdAtIso?: string | null): string {
  if (createdAtIso) {
    return formatTimestamp(createdAtIso);
  }
  if (!dateStr) return '—';

  const todayStr = getLocalDateString();
  if (dateStr === todayStr) {
    return 'Today';
  }

  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = getLocalDateString(yesterday);
  if (dateStr === yesterdayStr) {
    return 'Yesterday';
  }

  try {
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const monthIndex = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${months[monthIndex]} ${day}`;
    }
  } catch {
    // fallback
  }

  return dateStr;
}

/**
 * Format minutes duration (e.g. 45 -> "45 min", 75 -> "1 hr 15 min").
 */
export function formatMinutes(minutes?: number | null): string {
  if (minutes == null || isNaN(minutes)) return '0 min';
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hrs = Math.floor(minutes / 60);
  const rem = minutes % 60;
  return rem > 0 ? `${hrs} hr ${rem} min` : `${hrs} hr`;
}

/**
 * Format seconds duration into a human-readable string (e.g. 90 -> "1 min 30s" or "2 min").
 */
export function formatSeconds(seconds?: number | null): string {
  if (seconds == null || isNaN(seconds)) return '0 min';
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const mins = Math.floor(seconds / 60);
  const remSecs = seconds % 60;
  if (remSecs === 0) {
    return `${mins} min`;
  }
  return `${mins} min ${remSecs}s`;
}

/**
 * Format a ratio metric (range 0.0 to 1.0) into a percentage string (e.g. 0.85 -> "85%").
 */
export function formatRatioToPercent(ratio?: number | null): string {
  if (ratio == null || isNaN(ratio)) return '—';
  return `${Math.round(ratio * 100)}%`;
}

/**
 * Format a score percentage metric (range 0.0 to 100.0) into a percentage string (e.g. 75.0 -> "75%").
 * Does NOT multiply by 100 because the value is already in 0-100 scale.
 */
export function formatScorePercent(score?: number | null): string {
  if (score == null || isNaN(score)) return '—';
  return `${Math.round(score)}%`;
}

/**
 * Format a score metric (range 0.0 to 100.0) with specified decimals (e.g. 55.4 -> "55.4").
 */
export function formatScore(score?: number | null, decimals: number = 0): string {
  if (score == null || isNaN(score)) return '—';
  return decimals === 0 ? Math.round(score).toString() : score.toFixed(decimals);
}

/**
 * Format start delay in minutes.
 * Distinguishes true measured 0 minutes from missing data (null/undefined).
 */
export function formatStartDelay(minutes?: number | null): string {
  if (minutes == null || isNaN(minutes)) return '—';
  return `${Math.round(minutes)} mins`;
}

