# API list

Auth:
- POST /auth/register
- POST /auth/login

Admin:
- GET /admin/users
- POST /admin/managers
- POST /admin/recharge
- POST /admin/status
- POST /admin/mute
- POST /admin/notices
- POST /admin/ip-blacklist
- POST /admin/device-ban
- POST /admin/backup
- GET /admin/audits

Chat:
- POST /chat/messages
- GET /chat/messages

Red packets:
- POST /red-packets
- POST /red-packets/{packet_id}/claim

Notice and advanced stubs:
- GET /notices
- POST /push/simulate
- POST /speech/transcribe
- POST /video/rooms

Health:
- GET /health
