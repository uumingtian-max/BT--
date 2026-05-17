const MIME_EXT = {
  'image/png': 'png',
  'image/jpeg': 'jpg',
  'image/webp': 'webp',
  'image/gif': 'gif',
  'image/bmp': 'bmp',
  'video/mp4': 'mp4',
  'video/webm': 'webm',
  'audio/mpeg': 'mp3',
  'audio/wav': 'wav',
  'audio/ogg': 'ogg',
};

export function extensionForMime(type = '') {
  return MIME_EXT[String(type).toLowerCase()] || '';
}

export function normalizeClipboardFile(file, index = 0, now = Date.now()) {
  if (!file) return null;
  const originalName = typeof file.name === 'string' ? file.name.trim() : '';
  if (originalName) return file;

  const ext = extensionForMime(file.type) || 'bin';
  const stamp = new Date(now).toISOString().replace(/[-:TZ.]/g, '').slice(0, 14);
  const nextName = `pasted-${stamp}-${index + 1}.${ext}`;

  if (typeof File === 'function') {
    return new File([file], nextName, {
      type: file.type || 'application/octet-stream',
      lastModified: now,
    });
  }
  return file;
}

export function extractClipboardFiles(clipboardData) {
  if (!clipboardData) return [];

  const files = [];
  const addFile = (file) => {
    if (!file) return;
    const normalized = normalizeClipboardFile(file, files.length);
    if (normalized) files.push(normalized);
  };

  const items = Array.from(clipboardData.items || []);
  for (const item of items) {
    if (item?.kind !== 'file') continue;
    addFile(item.getAsFile?.());
  }

  if (!files.length) {
    for (const file of Array.from(clipboardData.files || [])) {
      addFile(file);
    }
  }

  const seen = new Set();
  return files.filter((file) => {
    const key = [file.name || '', file.size || 0, file.type || ''].join('|');
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
