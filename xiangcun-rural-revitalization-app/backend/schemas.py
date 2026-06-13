from typing import Optional
from pydantic import BaseModel, Field

class RegisterIn(BaseModel):
    phone: str; password: str; name: str; id_card: str; device: str = 'unknown'
class LoginIn(BaseModel):
    phone: str; password: str; device: str = 'unknown'
class CreateManagerIn(BaseModel):
    phone: str; password: str; name: str = '管理账号'
class RechargeIn(BaseModel):
    user_id: int; amount: int = Field(gt=0)
class StatusIn(BaseModel):
    user_id: int; status: str
class MuteIn(BaseModel):
    user_id: int; seconds: int = Field(ge=0)
class MessageIn(BaseModel):
    room: str = 'public'; body: str
class NoticeIn(BaseModel):
    title: str; body: str; target_user_id: Optional[int] = None
class RedPacketIn(BaseModel):
    amount: int = Field(gt=0); count: int = Field(gt=0); room: str = 'public'
class RuleIn(BaseModel):
    value: str; reason: str = '安全风控'
class PushIn(BaseModel):
    user_id: int; title: str; body: str
class SpeechIn(BaseModel):
    audio_text_stub: str
class VideoIn(BaseModel):
    room: str
