const STORAGE_KEY = 'bt_ui_prefs_v1';

const DEFAULTS = {
  showAgentTopology: false,
  useNoirEmpty: true,
  useDigitalHumanStage: false,
  hideSidebarHero: true,
};

export function loadUiPrefs() {
  if (typeof window === 'undefined') return { ...DEFAULTS };
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULTS };
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULTS };
  }
}

export function saveUiPrefs(partial) {
  const next = { ...loadUiPrefs(), ...partial };
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* ignore quota */
  }
  return next;
}
