from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json

@dataclass
class ChatMessage:
    """Mensaje de chat a nivel de aplicación."""
    from_id: str
    msg: str
    ts: float
    mid: str
    cmd: Optional[str] = None
    to: Optional[str] = "*"   # "*" = grupal; alias/IP = privado

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self), ensure_ascii=False).encode("utf-8")

    @staticmethod
    def from_bytes(data: bytes) -> "ChatMessage":
        obj: Dict[str, Any] = json.loads(data.decode("utf-8"))
        return ChatMessage(
            from_id=obj.get("from_id", ""),
            msg=obj.get("msg", ""),
            ts=float(obj.get("ts", 0.0)),
            mid=obj.get("mid", ""),
            cmd=obj.get("cmd"),
            to=obj.get("to", "*"),
        )
