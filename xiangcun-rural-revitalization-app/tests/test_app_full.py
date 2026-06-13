import os, tempfile
os.environ['APP_DB'] = tempfile.NamedTemporaryFile(delete=False).name
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import init_db

init_db(reset=True)
c = TestClient(app)

def login(phone, pw, device='dev'):
    r = c.post('/auth/login', json={'phone': phone, 'password': pw, 'device': device})
    assert r.status_code == 200, r.text
    return r.json()['token']

def H(token):
    return {'Authorization': 'Bearer ' + token}

def register_user(phone, id_card):
    r = c.post('/auth/register', json={'phone': phone, 'password': 'pw', 'name': phone, 'id_card': id_card})
    assert r.status_code == 200, r.text
    return r.json()['user_id']

def test_00_health():
    assert c.get('/health').json()['ok'] is True

def test_01_register_login_and_manager():
    user_id = register_user('u1', 'id1')
    admin = login('admin', 'admin123456')
    r = c.post('/admin/managers', headers=H(admin), json={'phone': 'mgr1', 'password': 'pw', 'name': '管理1'})
    assert r.status_code == 200
    mgr_id = r.json()['manager_id']
    r = c.get('/admin/users', headers=H(admin))
    assert any(x['id'] == user_id for x in r.json()['users'])
    assert any(x['id'] == mgr_id and x['realname_verified'] == 0 for x in r.json()['users'])

def test_02_chat_and_mute_receive_only():
    admin = login('admin', 'admin123456')
    uid = register_user('u2', 'id2')
    t = login('u2', 'pw')
    assert c.post('/chat/messages', headers=H(t), json={'room': 'public', 'body': 'hello'}).status_code == 200
    assert c.post('/admin/mute', headers=H(admin), json={'user_id': uid, 'seconds': 60}).status_code == 200
    assert c.post('/chat/messages', headers=H(t), json={'room': 'public', 'body': 'blocked'}).status_code == 403
    assert c.get('/chat/messages?room=public', headers=H(t)).status_code == 200

def test_03_red_packet_rules():
    admin = login('admin', 'admin123456')
    register_user('u3', 'id3')
    mgr = c.post('/admin/managers', headers=H(admin), json={'phone': 'mgr2', 'password': 'pw'}).json()['manager_id']
    assert c.post('/admin/recharge', headers=H(admin), json={'user_id': mgr, 'amount': 100}).status_code == 200
    mt = login('mgr2', 'pw')
    packet_id = c.post('/red-packets', headers=H(mt), json={'amount': 50, 'count': 1}).json()['packet_id']
    assert c.post(f'/red-packets/{packet_id}/claim', headers=H(mt)).status_code == 403
    ut = login('u3', 'pw')
    assert c.post(f'/red-packets/{packet_id}/claim', headers=H(ut)).status_code == 200
    assert c.post(f'/red-packets/{packet_id}/claim', headers=H(ut)).status_code in (404, 409)

def test_04_ban_blocks_login_and_id_card():
    admin = login('admin', 'admin123456')
    uid = register_user('u4', 'id4')
    assert c.post('/admin/status', headers=H(admin), json={'user_id': uid, 'status': 'banned'}).status_code == 200
    assert c.post('/auth/login', json={'phone': 'u4', 'password': 'pw'}).status_code == 403
    assert c.post('/auth/register', json={'phone': 'u4b', 'password': 'pw', 'name': 'x', 'id_card': 'id4'}).status_code == 403

def test_05_notice_push_speech_video():
    admin = login('admin', 'admin123456')
    uid = register_user('u5', 'id5')
    ut = login('u5', 'pw')
    assert c.post('/admin/notices', headers=H(admin), json={'title': '公告', 'body': '内容'}).status_code == 200
    assert c.get('/notices', headers=H(ut)).json()['notices']
    assert c.post('/push/simulate', headers=H(admin), json={'user_id': uid, 'title': '推送', 'body': '内容'}).status_code == 200
    assert c.post('/speech/transcribe', headers=H(ut), json={'audio_text_stub': '你好'}).json()['text'] == '你好'
    assert 'join_token' in c.post('/video/rooms', headers=H(ut), json={'room': 'r1'}).json()

def test_06_security_and_backup_and_audits():
    admin = login('admin', 'admin123456')
    assert c.post('/admin/device-ban', headers=H(admin), json={'value': 'bad-device', 'reason': '测试'}).status_code == 200
    assert c.post('/auth/login', json={'phone': 'admin', 'password': 'admin123456', 'device': 'bad-device'}).status_code == 403
    assert c.post('/admin/backup', headers=H(admin)).status_code == 200
    audits = c.get('/admin/audits', headers=H(admin)).json()['audits']
    assert any(x['action'] == 'device_rule' for x in audits)

def test_07_admin_can_recharge_user():
    admin = login('admin', 'admin123456')
    uid = register_user('u7', 'id7')
    assert c.post('/admin/recharge', headers=H(admin), json={'user_id': uid, 'amount': 12}).status_code == 200
    users = c.get('/admin/users', headers=H(admin)).json()['users']
    assert [u for u in users if u['id'] == uid][0]['balance'] == 12
