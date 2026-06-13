import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from .database import now, record
from .deps import current_user
from .schemas import MessageIn, RedPacketIn

router = APIRouter(tags=['聊天红包'])

@router.post('/chat/messages')
def send_message(data: MessageIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx
    if row['muted_until'] > now():
        raise HTTPException(403, '已禁言，只能接收消息')
    cur = c.execute('INSERT INTO messages(sender_id,room,body,created_at) VALUES(?,?,?,?)', (row['id'], data.room, data.body, now()))
    record(c, row['id'], 'send_message', 'room', data.room, ip, dev)
    c.commit(); c.close(); return {'ok': True, 'message_id': cur.lastrowid}

@router.get('/chat/messages')
def read_messages(room: str = 'public', ctx=Depends(current_user)):
    c, row, ip, dev = ctx
    rows = [dict(x) for x in c.execute('SELECT m.id,u.name sender,m.room,m.body,m.created_at FROM messages m JOIN users u ON u.id=m.sender_id WHERE room=? ORDER BY m.id DESC LIMIT 100', (room,))]
    c.close(); return {'messages': list(reversed(rows))}

@router.post('/red-packets')
def send_packet(data: RedPacketIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx
    if row['balance'] < data.amount:
        raise HTTPException(400, '余额不足')
    c.execute('UPDATE users SET balance=balance-? WHERE id=?', (data.amount, row['id']))
    cur = c.execute('INSERT INTO red_packets(sender_id,amount,count,room,created_at) VALUES(?,?,?,?,?)', (row['id'], data.amount, data.count, data.room, now()))
    record(c, row['id'], 'send_red_packet', 'packet', str(cur.lastrowid), ip, dev)
    c.commit(); c.close(); return {'ok': True, 'packet_id': cur.lastrowid}

@router.post('/red-packets/{packet_id}/claim')
def claim_packet(packet_id: int, ctx=Depends(current_user)):
    c, row, ip, dev = ctx
    if row['role'] == 'admin_manager':
        raise HTTPException(403, '管理账号不能抢红包')
    p = c.execute('SELECT * FROM red_packets WHERE id=?', (packet_id,)).fetchone()
    if not p or p['claimed_count'] >= p['count']:
        raise HTTPException(404, '红包不存在或已抢完')
    amount = max(1, p['amount'] // p['count'])
    try:
        c.execute('INSERT INTO red_packet_claims(packet_id,user_id,amount,created_at) VALUES(?,?,?,?)', (packet_id, row['id'], amount, now()))
        c.execute('UPDATE red_packets SET claimed_count=claimed_count+1 WHERE id=?', (packet_id,))
        c.execute('UPDATE users SET balance=balance+? WHERE id=?', (amount, row['id']))
        record(c, row['id'], 'claim_red_packet', 'packet', str(packet_id), ip, dev)
        c.commit(); return {'ok': True, 'amount': amount}
    except sqlite3.IntegrityError:
        raise HTTPException(409, '已经抢过')
    finally:
        c.close()
