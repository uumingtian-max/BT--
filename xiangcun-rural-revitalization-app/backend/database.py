from __future__ import annotations
import hashlib, os, secrets, shutil, sqlite3, time
from pathlib import Path

DB_PATH = os.environ.get('APP_DB', str(Path(__file__).resolve().parent / 'app.db'))
BACKUP_DIR = Path(os.environ.get('BACKUP_DIR', str(Path(__file__).resolve().parent / 'backups')))

def now() -> int:
    return int(time.time())

def password_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def make_token() -> str:
    return secrets.token_hex(24)

def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db(reset: bool = False) -> None:
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    c = conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, password_hash TEXT,
      name TEXT, id_card_hash TEXT, role TEXT DEFAULT 'user', realname_verified INTEGER DEFAULT 0,
      status TEXT DEFAULT 'active', muted_until INTEGER DEFAULT 0, balance INTEGER DEFAULT 0,
      created_by INTEGER, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER, ip TEXT, device TEXT, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, room TEXT, body TEXT, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS notices(id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, target_user_id INTEGER, title TEXT, body TEXT, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS red_packets(id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, amount INTEGER, count INTEGER, claimed_count INTEGER DEFAULT 0, room TEXT, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS red_packet_claims(id INTEGER PRIMARY KEY AUTOINCREMENT, packet_id INTEGER, user_id INTEGER, amount INTEGER, created_at INTEGER, UNIQUE(packet_id,user_id));
    CREATE TABLE IF NOT EXISTS audits(id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id INTEGER, action TEXT, target TEXT, detail TEXT, ip TEXT, device TEXT, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS ip_rules(ip TEXT PRIMARY KEY, reason TEXT, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS device_rules(device TEXT PRIMARY KEY, reason TEXT, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS push_events(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT, body TEXT, created_at INTEGER);
    CREATE TABLE IF NOT EXISTS video_rooms(id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT, creator_id INTEGER, join_token TEXT, created_at INTEGER);
    ''')
    if not c.execute("SELECT id FROM users WHERE role='super_admin' LIMIT 1").fetchone():
        c.execute('INSERT INTO users(phone,password_hash,name,role,realname_verified,status,created_at) VALUES(?,?,?,?,?,?,?)',
                  ('admin', password_hash('admin123456'), '最高管理员', 'super_admin', 1, 'active', now()))
    c.commit(); c.close()

def record(c: sqlite3.Connection, actor_id: int, action: str, target: str = '', detail: str = '', ip: str = '', device: str = '') -> None:
    c.execute('INSERT INTO audits(actor_id,action,target,detail,ip,device,created_at) VALUES(?,?,?,?,?,?,?)',
              (actor_id, action, target, detail, ip, device, now()))

def make_backup() -> str:
    BACKUP_DIR.mkdir(exist_ok=True)
    out = BACKUP_DIR / f'app-backup-{now()}.db'
    shutil.copyfile(DB_PATH, out)
    return str(out)
