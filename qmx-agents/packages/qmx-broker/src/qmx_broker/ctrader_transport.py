"""Short read sessions over QMF's framing and compiled protocol definitions."""

import asyncio
import ssl
from typing import Any

from google.protobuf.json_format import MessageToDict, ParseDict
from qmf.core import is_refusal
from qmf.venue.connection import encode_framed_payload
from qmf.venue.proto import CompiledProto

from qmx_broker.adapters import Document

READ_REQUESTS = frozenset(
    {
        "ProtoOAApplicationAuthReq",
        "ProtoOAGetAccountListByAccessTokenReq",
        "ProtoOAAccountAuthReq",
        "ProtoOASymbolsListReq",
        "ProtoOASymbolByIdReq",
        "ProtoOATraderReq",
        "ProtoOAReconcileReq",
        "ProtoOAGetTrendbarsReq",
        "ProtoOASubscribeSpotsReq",
    }
)


class CTraderTransport:
    def __init__(
        self, proto: CompiledProto, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self.proto = proto
        self.reader = reader
        self.writer = writer
        self.sequence = 0
        self.pending_spots: list[Document] = []

    @classmethod
    async def connect(cls, proto: CompiledProto, environment: str) -> CTraderTransport:
        if environment not in {"demo", "live"}:
            raise ValueError("Use demo or live")
        host = f"{environment}.ctraderapi.com"
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, 5035, ssl=ssl.create_default_context()), timeout=5
        )
        return cls(proto, reader, writer)

    def _message(self, name: str) -> Any:
        result = self.proto.message_class(name)
        if is_refusal(result):
            raise ValueError("Pinned protocol definitions do not contain " + name)
        return result.value()

    async def _receive(self) -> tuple[str, str, Document]:
        size = int.from_bytes(await self.reader.readexactly(4), "big")
        if not 0 < size <= 8 * 1024 * 1024:
            raise ValueError("Invalid cTrader frame size")
        envelope = self._message("ProtoMessage")
        envelope.ParseFromString(await self.reader.readexactly(size))
        payload_type = int(envelope.payloadType)
        for name in self.proto.message_names():
            if name == "ProtoMessage":
                continue
            message = self._message(name)
            if getattr(message, "payloadType", None) == payload_type:
                message.ParseFromString(envelope.payload)
                if not message.IsInitialized():
                    raise ValueError("Incomplete cTrader response")
                body = MessageToDict(message, preserving_proto_field_name=True)
                if name in {"ProtoErrorRes", "ProtoOAErrorRes"}:
                    # Remote descriptions may echo credentials; never return them.
                    raise ValueError(
                        "cTrader refused the request; verify permissions and token expiry"
                    )
                return name, str(envelope.clientMsgId), body
        raise ValueError("Unknown payload type in pinned cTrader definitions")

    async def request(self, name: str, values: Document) -> Document:
        if name not in READ_REQUESTS:
            raise ValueError("Broker transport only permits authentication and read requests")
        message = ParseDict(values, self._message(name))
        self.sequence += 1
        request_id = str(self.sequence)
        envelope = self._message("ProtoMessage")
        envelope.payloadType = message.payloadType
        envelope.payload = message.SerializeToString()
        envelope.clientMsgId = request_id
        frame = encode_framed_payload(envelope.SerializeToString())
        if is_refusal(frame):
            raise ValueError("Could not frame cTrader request")
        # Serialized sessions stay below the stricter historical rate limit.
        await asyncio.sleep(0.21)
        self.writer.write(frame.value)
        await self.writer.drain()
        async with asyncio.timeout(5):
            while True:
                received_name, correlation, body = await self._receive()
                if received_name == "ProtoOASpotEvent":
                    self.pending_spots.append(body)
                if correlation == request_id and received_name == name.removesuffix("Req") + "Res":
                    return body

    async def spot(self, name: str, values: Document) -> Document:
        await self.request(name, values)
        latest: Document = {}
        async with asyncio.timeout(5):
            while True:
                if self.pending_spots:
                    body = self.pending_spots.pop(0)
                else:
                    received_name, _, body = await self._receive()
                    if received_name != "ProtoOASpotEvent":
                        continue
                if str(body.get("ctidTraderAccountId", "")) == str(
                    values.get("ctidTraderAccountId", "")
                ) and (
                    "symbolId" not in values or int(body.get("symbolId", 0)) in values["symbolId"]
                ):
                    latest.update(body)
                    if all(key in latest for key in ("bid", "ask", "timestamp")):
                        return latest

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()
