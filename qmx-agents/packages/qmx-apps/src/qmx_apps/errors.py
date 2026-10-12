"""Transport-neutral app failures."""

from pydantic import JsonValue

type Document = dict[str, JsonValue]


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status

    def document(self) -> Document:
        return {"error": {"code": self.code, "message": str(self)}}
