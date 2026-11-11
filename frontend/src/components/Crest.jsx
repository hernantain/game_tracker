import { useEffect, useState } from 'react';

/**
 * A club crest, falling back to an initials badge.
 *
 * ESPN has no crest for roughly a third of the teams in the database -- mostly
 * lower-division Copa Argentina sides -- so a missing file is normal, not an
 * error. Rather than tracking availability in the database, the <img> onError
 * swaps in a badge: it costs nothing when the file exists and needs no column
 * to stay in sync.
 *
 * Files live in frontend/public/crests/<size>/<espnTeamId>.png.
 */
export default function Crest({
  espnId,
  name = '',
  size = 64,
  className = '',
  // Applied to the initials badge only. The <img> must never inherit a
  // background, or it would show through the crest's transparency.
  fallbackClassName = '',
}) {
  const [failed, setFailed] = useState(false);

  // A recycled row in a list can hand this a different crest; forget the
  // previous failure so the new one gets its chance to load.
  useEffect(() => { setFailed(false); }, [espnId]);

  const px = size >= 96 ? 128 : 64;   // the two sizes that ship
  const initials = (name || '?')
    .replace(/\(.*?\)/g, '')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();

  if (!espnId || failed) {
    return (
      <span
        aria-hidden="true"
        style={{ width: size, height: size }}
        className={`shrink-0 rounded-full bg-surface-2 border border-surface-3 text-gray-500
                    flex items-center justify-center font-bold leading-none
                    ${className} ${fallbackClassName}`}
      >
        <span style={{ fontSize: Math.max(9, Math.round(size * 0.38)) }}>{initials}</span>
      </span>
    );
  }

  return (
    <img
      src={`/crests/${px}/${espnId}.png`}
      alt=""
      aria-hidden="true"
      loading="lazy"
      width={size}
      height={size}
      onError={() => setFailed(true)}
      style={{ width: size, height: size }}
      className={`shrink-0 object-contain ${className}`}
    />
  );
}
