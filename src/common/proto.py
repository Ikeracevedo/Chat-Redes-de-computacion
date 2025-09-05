from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json

@dataclass
class ChatMessage:
    """Mensaje de chat a nivel de aplicación.


    Campos mínimos:
    - from_id: identificador visible (IP o alias)
    - msg: texto del mensaje
    - ts: timestamp epoch (float)
    - mid: message id (uuid)
    - cmd: comando opcional ("who", "nick", etc.)
    """
    from_id: str
    msg: str
    ts: float
    mid: str
    cmd: Optional[str] = None

    def to_bytes(self) -> bytes:
        payload = json.dumps(asdict(self), ensure_ascii=False).encode("utf-8")
        return payload


    @staticmethod
    def from_bytes(data: bytes) -> "ChatMessage":
        obj: Dict[str, Any] = json.loads(data.decode("utf-8"))
        return ChatMessage(
            from_id=obj.get("from_id", ""),
            msg=obj.get("msg", ""),
            ts=float(obj.get("ts", 0.0)),
            mid=obj.get("mid", ""),
            cmd=obj.get("cmd"),
        )