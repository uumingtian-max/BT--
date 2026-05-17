import os
import re
from pathlib import Path
from typing import Iterable

MAX_READ_BYTES = int(os.environ.get('AGENT_FILE_READ_MAX_BYTES', str(2 * 1024 * 1024)))
READ_PREVIEW_CHARS = int(os.environ.get('AGENT_FILE_READ_PREVIEW_CHARS', '10000'))
MAX_LIST_ENTRIES = int(os.environ.get('AGENT_LIST_FILES_MAX_ENTRIES', '500'))

WORKSPACE = Path(os.path.join(os.path.dirname(__file__), '..', 'workspace')).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

# backend/tools -> …/ai-agent-project
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

HOME = Path.home()


def _existing_first(paths: Iterable[Path], fallback: Path) -> Path:
    for path in paths:
        try:
            if path.exists():
                return path.resolve()
        except OSError:
            continue
    return fallback.resolve()


def _downloads_candidates() -> list[Path]:
    candidates = [
        HOME / 'Downloads',
        HOME / '下载',
        HOME / 'OneDrive' / 'Downloads',
        HOME / 'OneDrive' / '下载',
        HOME / 'Desktop' / 'Downloads',
        HOME / 'Desktop' / '下载',
    ]
    if os.name == 'nt':
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders',
            ) as key:
                raw, _ = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')
                candidates.insert(0, Path(os.path.expandvars(str(raw))))
        except OSError:
            pass
    return list(dict.fromkeys(candidates))


KNOWN_BASES = {
    'desktop': (HOME / 'Desktop').resolve(),
    'documents': (HOME / 'Documents').resolve(),
    'downloads': _existing_first(_downloads_candidates(), HOME / 'Downloads'),
    'pictures': (HOME / 'Pictures').resolve(),
    'videos': (HOME / 'Videos').resolve(),
    'project': PROJECT_ROOT,
    'agent_sandbox': WORKSPACE,
}

KNOWN_BASE_CANDIDATES = {
    'downloads': _downloads_candidates(),
}

OUTPUTS_DIR = (PROJECT_ROOT / 'outputs').resolve()
WRITABLE_ROOTS: tuple[Path, ...] = tuple(
    dict.fromkeys(
        [
            PROJECT_ROOT,
            WORKSPACE,
            OUTPUTS_DIR,
            KNOWN_BASES['desktop'],
            KNOWN_BASES['documents'],
            KNOWN_BASES['downloads'],
            KNOWN_BASES['agent_sandbox'],
        ]
    )
)

ALIAS_MAP = {
    '桌面': 'desktop',
    'desktop': 'desktop',
    '文档': 'documents',
    'documents': 'documents',
    '我的文档': 'documents',
    '下载': 'downloads',
    'downloads': 'downloads',
    '图片': 'pictures',
    'pictures': 'pictures',
    '视频': 'videos',
    'videos': 'videos',
    # 模型常说 workspace/工作区：指整个项目，不要指空的 backend/workspace
    '工作区': 'project',
    'workspace': 'project',
    '项目': 'project',
    'project': 'project',
    '代码库': 'project',
    '沙盒': 'agent_sandbox',
    'sandbox': 'agent_sandbox',
}


def _clean_user_path(raw_path: str) -> str:
    text = (raw_path or '').strip().strip('"\'')
    text = text.replace('/', os.sep)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('上的', os.sep).replace('里的', os.sep).replace('中的', os.sep)
    if text in {'桌面上', '文档上', '下载上', '图片上', '视频上'}:
        text = text[:-1]
    return text.strip().strip('\\/')


def _search_named_target(name: str):
    if not name:
        return None
    candidate_name = Path(name).name
    for base in KNOWN_BASES.values():
        direct = base / candidate_name
        if direct.exists():
            return direct.resolve()
        # 只搜索两层深度，避免大目录递归卡住请求线程
        try:
            for item in base.iterdir():
                if item.name == candidate_name:
                    return item.resolve()
                if item.is_dir():
                    try:
                        for sub in item.iterdir():
                            if sub.name == candidate_name:
                                return sub.resolve()
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            continue
    return None


def _map_virtual_user_path(text: str):
    normalized = text.replace('\\', '/').strip()
    patterns = [
        r"^(?:/)?Users/(?:当前用户|[^/]+)/(Desktop|Documents|Downloads|Pictures|Videos)(?:/(.*))?$",
        r"^(?:/)?home/(?:当前用户|[^/]+)/(Desktop|Documents|Downloads|Pictures|Videos)(?:/(.*))?$",
        r"^~/(Desktop|Documents|Downloads|Pictures|Videos)(?:/(.*))?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, normalized, re.IGNORECASE)
        if not match:
            continue
        folder = (match.group(1) or '').lower()
        suffix = (match.group(2) or '').strip('/')
        base = KNOWN_BASES.get(folder)
        if not base:
            continue
        return (base / suffix).resolve() if suffix else base
    return None


def resolve_user_path(raw_path: str) -> Path:
    text = _clean_user_path(raw_path)
    if not text:
        # 未给路径时列桌面，避免落到空的 agent 沙盒目录
        return KNOWN_BASES['desktop']

    virtual_path = _map_virtual_user_path(text)
    if virtual_path:
        return virtual_path

    expanded = Path(os.path.expanduser(text))
    if expanded.is_absolute():
        abs_path = expanded.resolve()
        try:
            if abs_path == WORKSPACE.resolve():
                return PROJECT_ROOT
        except OSError:
            pass
        for base in KNOWN_BASES.values():
            try:
                abs_path.relative_to(base)
                return abs_path
            except ValueError:
                continue
        return abs_path

    lowered = text.lower()
    for alias, base_key in ALIAS_MAP.items():
        if lowered == alias:
            return KNOWN_BASES[base_key]
        if lowered.startswith(alias + os.sep) or lowered.startswith(alias + '\\') or lowered.startswith(alias + '/'):
            suffix = text[len(alias):].lstrip('\\/')
            return (KNOWN_BASES[base_key] / suffix).resolve()

    searched = _search_named_target(text)
    if searched:
        return searched

    return (WORKSPACE / Path(text).name).resolve()


def _known_base_key_for_path(path: Path) -> str | None:
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    for key, base in KNOWN_BASES.items():
        try:
            if resolved == base.resolve():
                return key
        except OSError:
            continue
    for key, candidates in KNOWN_BASE_CANDIDATES.items():
        for candidate in candidates:
            try:
                if resolved == candidate.resolve():
                    return key
            except OSError:
                continue
    return None


def _fallback_existing_dirs(base_key: str | None) -> list[Path]:
    candidates: list[Path] = []
    if base_key:
        candidates.extend(KNOWN_BASE_CANDIDATES.get(base_key, []))
        if base_key == 'downloads':
            candidates.extend([KNOWN_BASES['desktop'], PROJECT_ROOT])
    candidates.extend([KNOWN_BASES['desktop'], PROJECT_ROOT])
    out: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            marker = str(resolved).lower()
            if marker in seen or not resolved.exists() or not resolved.is_dir():
                continue
            seen.add(marker)
            out.append(resolved)
        except OSError:
            continue
    return out


def read_file(path):
    p = resolve_user_path(path)
    if not p.exists():
        return f'Not found: {p}'
    if not p.is_file():
        return f'Not a file: {p}'
    try:
        size = p.stat().st_size
        with open(p, 'rb') as f:
            data = f.read(MAX_READ_BYTES + 1)
        truncated_bytes = len(data) > MAX_READ_BYTES or size > MAX_READ_BYTES
        if truncated_bytes:
            data = data[:MAX_READ_BYTES]
        content = data.decode('utf-8', errors='replace')
        preview = content[:READ_PREVIEW_CHARS]
        truncated_chars = len(content) > len(preview)
        note = ''
        if truncated_bytes:
            note += f'\n[WARN] File preview capped at {MAX_READ_BYTES} bytes from {size} bytes.'
        if truncated_chars:
            note += f'\n[WARN] Text preview capped at {READ_PREVIEW_CHARS} chars.'
        return f'[PATH] {p}{note}\n\n' + preview + ('...' if truncated_chars else '')
    except Exception as e:
        return f'Error: {e}'


def _assert_writable_target(path: Path) -> None:
    resolved = path.resolve()
    for base in WRITABLE_ROOTS:
        try:
            resolved.relative_to(base.resolve())
            return
        except ValueError:
            continue
    raise PermissionError(
        f"Write blocked: {resolved} is outside allowed roots (project, outputs, desktop, documents, downloads, sandbox)."
    )


def assert_known_user_path(path: Path, action: str = 'Access') -> None:
    resolved = path.resolve()
    for base in KNOWN_BASES.values():
        try:
            resolved.relative_to(base.resolve())
            return
        except ValueError:
            continue
    raise PermissionError(f"{action} blocked: {resolved} is outside known user/project roots.")


def write_file(path, content):
    p = resolve_user_path(path)
    try:
        _assert_writable_target(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content)
        return f'Written to {p}'
    except Exception as e:
        return f'Error: {e}'


def list_files(directory):
    p = resolve_user_path(directory)
    if not p.exists():
        base_key = _known_base_key_for_path(p)
        fallbacks = _fallback_existing_dirs(base_key)
        if fallbacks:
            fallback = fallbacks[0]
            try:
                items = []
                all_items = sorted(fallback.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                for item in all_items[:MAX_LIST_ENTRIES]:
                    label = '[DIR]' if item.is_dir() else '[FILE]'
                    items.append(f'{label} {item.name}')
                if len(all_items) > MAX_LIST_ENTRIES:
                    items.append(f'...(truncated, showing {MAX_LIST_ENTRIES} of {len(all_items)} entries)')
                note = (
                    f'[WARN] Requested path not found: {p}\n'
                    f'[FALLBACK] Listing existing directory instead: {fallback}'
                )
                return f'{note}\n[PATH] {fallback}\n' + ('\n'.join(items) if items else 'Empty')
            except Exception as e:
                return f'Not found: {p}\nFallback failed: {e}'
        return f'Not found: {p}'
    if not p.is_dir():
        return f'Not a directory: {p}'
    try:
        items = []
        all_items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        for item in all_items[:MAX_LIST_ENTRIES]:
            label = '[DIR]' if item.is_dir() else '[FILE]'
            items.append(f'{label} {item.name}')
        if len(all_items) > MAX_LIST_ENTRIES:
            items.append(f'...(truncated, showing {MAX_LIST_ENTRIES} of {len(all_items)} entries)')
        return f'[PATH] {p}\n' + ('\n'.join(items) if items else 'Empty')
    except Exception as e:
        return f'Error: {e}'
