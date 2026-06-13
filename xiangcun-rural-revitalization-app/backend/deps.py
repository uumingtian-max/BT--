from typing import Optional
from fastapi import Header, HTTPException, Request
from .database import conn

def current_user(authorization: Optional[str] = Header(None), request: Request = None):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, '未登录')
    token = authorization.split(' ', 1)[1]
    c = conn()
    row = c.execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?', (token,)).fetchone()
    if not row:
        c.close(); raise HTTPException(401, '登录失效')
    ip = request.client.host if request and request.client else 'unknown'
    dev = c.execute('SELECT device FROM sessions WHERE token=?', (token,)).fetchone()['device']
    if c.execute('SELECT 1 FROM ip_rules WHERE ip=?', (ip,)).fetchone():
        c.close(); raise HTTPException(403, 'IP 已限制')
    if c.execute('SELECT 1 FROM device_rules WHERE device=?', (dev,)).fetchone():
        c.close(); raise HTTPException(403, '设备已限制')
    if row['status'] == 'banned':
        c.close(); raise HTTPException(403, '账号已封禁')
    return c, row, ip, dev

def need_admin(row):
    if row['role'] not in ('super_admin', 'admin_manager'):
        raise HTTPException(403, '需要后台权限')

def need_super(row):
    if row['role'] != 'super_admin':
        raise HTTPException(403, '需要最高权限')
