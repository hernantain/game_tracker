import { useEffect, useState } from 'react';
import { api, isLegacy } from '../api';

/**
 * What the backend can answer. Driven by GET /api/capabilities so filling a
 * gap in the database turns the matching chart back on with no UI change.
 * In legacy mode everything is available.
 */
export function useCapabilities() {
  const [caps, setCaps] = useState(null);

  useEffect(() => {
    if (isLegacy) return;
    let active = true;
    api.capabilities()
      .then((d) => { if (active) setCaps(d); })
      .catch(() => { if (active) setCaps({}); });
    return () => { active = false; };
  }, []);

  function has(key) {
    if (isLegacy) return true;
    if (!caps) return true;          // optimistic until it loads
    return caps[key]?.available !== false;
  }

  function note(key) {
    return caps?.[key]?.note || null;
  }

  return { caps, has, note, isLegacy };
}
