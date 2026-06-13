import json, sqlite3
from fastapi import APIRouter, Depends, HTTPException
from .database import make_backup, now, password_hash, record
from .deps import current_user, need_admin, need_super
from .schemas import CreateManagerIn, MuteIn, NoticeIn, RechargeIn, RuleIn, StatusIn

router = APIRouter(prefix='/admin', tags=['后台'])

@router.post('/managers')
def create_manager(data: CreateManagerIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_super(row)
    try:
        cur = c.execute('INSERT INTO users(phone,password_hash,name,role,realname_verified,status,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)',
                        (data.phone, password_hash(data.password), data.name, 'admin_manager', 0, 'active', row['id'], now()))
        record(c, row['id'], 'create_manager', 'user', str(cur.lastrowid), ip, dev)
        c.commit(); return {'ok': True, 'manager_id': cur.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(409, '账号已存在')
    finally:
        c.close()

@router.get('/users')
def users(ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_admin(row)
    rows = [dict(x) for x in c.execute('SELECT id,phone,name,role,realname_verified,status,muted_until,balance,created_by,created_at FROM users ORDER BY id')]
    c.close(); return {'users': rows}

@router.post('/recharge')
def recharge(data: RechargeIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_admin(row)
    c.execute('UPDATE users SET balance=balance+? WHERE id=?', (data.amount, data.user_id))
    record(c, row['id'], 'recharge', 'user', json.dumps(data.model_dump()), ip, dev)
    c.commit(); c.close(); return {'ok': True}

@router.post('/status')
def status(data: StatusIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_admin(row)
    if data.status not in ('active', 'banned'):
        raise HTTPException(400, '状态不支持')
    c.execute('UPDATE users SET status=? WHERE id=?', (data.status, data.user_id))
    record(c, row['id'], 'set_status', 'user', json.dumps(data.model_dump()), ip, dev)
    c.commit(); c.close(); return {'ok': True}

@router.post('/mute')
def mute(data: MuteIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_admin(row)
    c.execute('UPDATE users SET muted_until=? WHERE id=?', (now() + data.seconds, data.user_id))
    record(c, row['id'], 'mute', 'user', json.dumps(data.model_dump()), ip, dev)
    c.commit(); c.close(); return {'ok': True}

@router.post('/notices')
def notices(data: NoticeIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_admin(row)
    cur = c.execute('INSERT INTO notices(sender_id,target_user_id,title,body,created_at) VALUES(?,?,?,?,?)',
                    (row['id'], data.target_user_id, data.title, data.body, now()))
    if data.target_user_id:
        c.execute('INSERT INTO push_events(user_id,title,body,created_at) VALUES(?,?,?,?)', (data.target_user_id, data.title, data.body, now()))
    record(c, row['id'], 'notice', 'notice', str(cur.lastrowid), ip, dev)
    c.commit(); c.close(); return {'ok': True, 'notice_id': cur.lastrowid}

@router.post('/ip-blacklist')
def ip_rule(data: RuleIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_super(row)
    c.execute('INSERT OR REPLACE INTO ip_rules(ip,reason,created_at) VALUES(?,?,?)', (data.value, data.reason, now()))
    record(c, row['id'], 'ip_rule', 'ip', data.value, ip, dev)
    c.commit(); c.close(); return {'ok': True}

@router.post('/device-ban')
def device_rule(data: RuleIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_super(row)
    c.execute('INSERT OR REPLACE INTO device_rules(device,reason,created_at) VALUES(?,?,?)', (data.value, data.reason, now()))
    record(c, row['id'], 'device_rule', 'device', data.value, ip, dev)
    c.commit(); c.close(); return {'ok': True}

@router.post('/backup')
def backup(ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_super(row); c.close()
    return {'ok': True, 'backup': make_backup()}

@router.get('/audits')
def audits(ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_super(row)
    rows = [dict(x) for x in c.execute('SELECT * FROM audits ORDER BY id DESC LIMIT 200')]
    c.close(); return {'audits': rows}
