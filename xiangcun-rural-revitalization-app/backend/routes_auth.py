import sqlite3
from fastapi import APIRouter, HTTPException, Request
from .database import conn, make_token, now, password_hash, record
from .schemas import LoginIn, RegisterIn

router = APIRouter(prefix='/auth', tags=['认证'])

@router.post('/register')
def register(data: RegisterIn, request: Request):
    c = conn(); ip = request.client.host if request.client else 'unknown'
    if c.execute('SELECT 1 FROM ip_rules WHERE ip=?', (ip,)).fetchone():
        raise HTTPException(403, 'IP 已限制')
    id_hash = password_hash(data.id_card)
    if c.execute('SELECT 1 FROM users WHERE id_card_hash=? AND status="banned"', (id_hash,)).fetchone():
        raise HTTPException(403, '该身份证已封禁')
    try:
        cur = c.execute('INSERT INTO users(phone,password_hash,name,id_card_hash,role,realname_verified,status,created_at) VALUES(?,?,?,?,?,?,?,?)',
                        (data.phone, password_hash(data.password), data.name, id_hash, 'user', 1, 'active', now()))
        record(c, cur.lastrowid, 'register', 'user', data.phone, ip, data.device)
        c.commit(); return {'ok': True, 'user_id': cur.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(409, '手机号已存在')
    finally:
        c.close()

@router.post('/login')
def login(data: LoginIn, request: Request):
    c = conn(); ip = request.client.host if request.client else 'unknown'
    if c.execute('SELECT 1 FROM ip_rules WHERE ip=?', (ip,)).fetchone():
        raise HTTPException(403, 'IP 已限制')
    if c.execute('SELECT 1 FROM device_rules WHERE device=?', (data.device,)).fetchone():
        raise HTTPException(403, '设备已限制')
    row = c.execute('SELECT * FROM users WHERE phone=? AND password_hash=?', (data.phone, password_hash(data.password))).fetchone()
    if not row:
        raise HTTPException(401, '账号或密码错误')
    if row['status'] == 'banned':
        raise HTTPException(403, '账号已封禁')
    tk = make_token()
    c.execute('INSERT INTO sessions(token,user_id,ip,device,created_at) VALUES(?,?,?,?,?)', (tk, row['id'], ip, data.device, now()))
    record(c, row['id'], 'login', 'session', '', ip, data.device)
    c.commit(); c.close()
    return {'token': tk, 'role': row['role'], 'user_id': row['id']}
