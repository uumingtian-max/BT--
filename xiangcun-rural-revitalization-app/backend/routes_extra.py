from fastapi import APIRouter, Depends
from .database import make_token, now, record
from .deps import current_user, need_admin
from .schemas import PushIn, SpeechIn, VideoIn

router = APIRouter(tags=['通知与高级能力'])

@router.get('/notices')
def notices(ctx=Depends(current_user)):
    c, row, ip, dev = ctx
    rows = [dict(x) for x in c.execute('SELECT * FROM notices WHERE target_user_id IS NULL OR target_user_id=? ORDER BY id DESC', (row['id'],))]
    c.close(); return {'notices': rows}

@router.post('/push/simulate')
def push(data: PushIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; need_admin(row)
    cur = c.execute('INSERT INTO push_events(user_id,title,body,created_at) VALUES(?,?,?,?)', (data.user_id, data.title, data.body, now()))
    record(c, row['id'], 'push', 'user', str(data.user_id), ip, dev)
    c.commit(); c.close(); return {'ok': True, 'push_id': cur.lastrowid}

@router.post('/speech/transcribe')
def speech(data: SpeechIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx
    record(c, row['id'], 'speech_transcribe', 'speech', 'stub', ip, dev)
    c.commit(); c.close(); return {'text': data.audio_text_stub, 'provider': 'stub-local'}

@router.post('/video/rooms')
def video(data: VideoIn, ctx=Depends(current_user)):
    c, row, ip, dev = ctx; join_token = make_token()
    cur = c.execute('INSERT INTO video_rooms(room,creator_id,join_token,created_at) VALUES(?,?,?,?)', (data.room, row['id'], join_token, now()))
    record(c, row['id'], 'video_room', 'room', data.room, ip, dev)
    c.commit(); c.close(); return {'ok': True, 'room_id': cur.lastrowid, 'join_token': join_token}
