from dataclasses import dataclass, field


@dataclass
class UploadResult:
    """Framework independent upload response, rendered by the views"""

    status: int = 200
    data: dict | None = None
    headers: dict[str, str] = field(default_factory=dict)
    content: bytes | str = b""
