from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
from google.protobuf import descriptor_pb2
from qmf.core import is_refusal
from qmf.venue.proto import CompiledProto, compile_descriptor_set

from qmx_broker.ctrader_transport import CTraderTransport


def protocol() -> CompiledProto:
    """Minimal wire fixture retaining the official field numbers and payload ids."""
    descriptor = descriptor_pb2.FileDescriptorSet()
    file = descriptor.file.add(name="offline.proto", syntax="proto2")
    fields = descriptor_pb2.FieldDescriptorProto
    shapes = {
        "ProtoMessage": [
            ("payloadType", 1, fields.TYPE_UINT32, None),
            ("payload", 2, fields.TYPE_BYTES, None),
            ("clientMsgId", 3, fields.TYPE_STRING, None),
        ],
        "ProtoOAApplicationAuthReq": [
            ("payloadType", 1, fields.TYPE_UINT32, "2100"),
            ("clientId", 2, fields.TYPE_STRING, None),
            ("clientSecret", 3, fields.TYPE_STRING, None),
        ],
        "ProtoOAApplicationAuthRes": [("payloadType", 1, fields.TYPE_UINT32, "2101")],
        "ProtoOASubscribeSpotsReq": [
            ("payloadType", 1, fields.TYPE_UINT32, "2127"),
            ("ctidTraderAccountId", 2, fields.TYPE_INT64, None),
            ("symbolId", 3, fields.TYPE_INT64, None),
        ],
        "ProtoOASubscribeSpotsRes": [("payloadType", 1, fields.TYPE_UINT32, "2128")],
        "ProtoOASpotEvent": [
            ("payloadType", 1, fields.TYPE_UINT32, "2131"),
            ("ctidTraderAccountId", 2, fields.TYPE_INT64, None),
            ("symbolId", 3, fields.TYPE_INT64, None),
            ("bid", 4, fields.TYPE_UINT64, None),
            ("ask", 5, fields.TYPE_UINT64, None),
            ("timestamp", 8, fields.TYPE_INT64, None),
        ],
        "ProtoOAErrorRes": [
            ("payloadType", 1, fields.TYPE_UINT32, "2142"),
            ("errorCode", 3, fields.TYPE_STRING, None),
            ("description", 4, fields.TYPE_STRING, None),
        ],
    }
    for name, definitions in shapes.items():
        message = file.message_type.add(name=name)
        for field_name, number, kind, default in definitions:
            field = message.field.add(
                name=field_name, number=number, type=kind, label=fields.LABEL_OPTIONAL
            )
            if default is not None:
                field.default_value = default
            if name == "ProtoOASubscribeSpotsReq" and field_name == "symbolId":
                field.label = fields.LABEL_REPEATED
    result = compile_descriptor_set(
        descriptor.SerializeToString(), package_name="openapi-proto-messages", release_tag=91
    )
    assert not is_refusal(result)
    return result.value


def message(proto: CompiledProto, name: str) -> Any:
    result = proto.message_class(name)
    assert not is_refusal(result)
    return result.value()


def frame(proto: CompiledProto, name: str, correlation: str, **values: Any) -> bytes:
    body = message(proto, name)
    for key, value in values.items():
        setattr(body, key, value)
    envelope = message(proto, "ProtoMessage")
    envelope.payloadType = body.payloadType
    envelope.payload = body.SerializeToString()
    envelope.clientMsgId = correlation
    wire = envelope.SerializeToString()
    return len(wire).to_bytes(4, "big") + wire


class Writer:
    def __init__(self) -> None:
        self.written: list[bytes] = []

    def write(self, wire: bytes) -> None:
        self.written.append(wire)

    async def drain(self) -> None:
        pass


def test_framed_auth_ignores_unrelated_response_and_preserves_request() -> None:
    async def run() -> None:
        proto = protocol()
        reader = asyncio.StreamReader()
        reader.feed_data(
            frame(proto, "ProtoOAApplicationAuthRes", "other")
            + frame(proto, "ProtoOAApplicationAuthRes", "1")
        )
        writer = Writer()
        transport = CTraderTransport(proto, reader, cast(asyncio.StreamWriter, writer))
        assert (
            await transport.request(
                "ProtoOAApplicationAuthReq", {"clientId": "offline", "clientSecret": "offline"}
            )
            == {}
        )
        envelope = message(proto, "ProtoMessage")
        envelope.ParseFromString(writer.written[0][4:])
        assert envelope.clientMsgId == "1" and envelope.payloadType == 2100
        body = message(proto, "ProtoOAApplicationAuthReq")
        body.ParseFromString(envelope.payload)
        assert body.clientId == "offline" and body.clientSecret == "offline"

    asyncio.run(run())


def test_spot_before_subscription_acknowledgement_is_retained() -> None:
    async def run() -> None:
        proto = protocol()
        reader = asyncio.StreamReader()
        reader.feed_data(
            frame(proto, "ProtoOASpotEvent", "", bid=110000, ask=110010, timestamp=1700000000000)
            + frame(proto, "ProtoOASubscribeSpotsRes", "1")
        )
        transport = CTraderTransport(proto, reader, cast(asyncio.StreamWriter, Writer()))
        quote = await transport.spot("ProtoOASubscribeSpotsReq", {})
        assert quote["bid"] == "110000" and quote["timestamp"] == "1700000000000"

    asyncio.run(run())


def test_remote_error_description_is_never_exposed() -> None:
    async def run() -> None:
        proto = protocol()
        reader = asyncio.StreamReader()
        reader.feed_data(
            frame(
                proto,
                "ProtoOAErrorRes",
                "1",
                errorCode="ACCESS_DENIED",
                description="must-not-expose-token",
            )
        )
        transport = CTraderTransport(proto, reader, cast(asyncio.StreamWriter, Writer()))
        with pytest.raises(ValueError, match="refused") as error:
            await transport.request(
                "ProtoOAApplicationAuthReq", {"clientId": "offline", "clientSecret": "offline"}
            )
        assert "must-not-expose-token" not in str(error.value)

    asyncio.run(run())


def test_partial_spots_merge_only_within_the_requested_account_and_symbol() -> None:
    async def run() -> None:
        proto = protocol()
        reader = asyncio.StreamReader()
        reader.feed_data(
            frame(proto, "ProtoOASubscribeSpotsRes", "1")
            + frame(
                proto,
                "ProtoOASpotEvent",
                "",
                ctidTraderAccountId=202,
                symbolId=1,
                ask=999999,
                timestamp=1700000000000,
            )
            + frame(
                proto,
                "ProtoOASpotEvent",
                "",
                ctidTraderAccountId=101,
                symbolId=1,
                bid=110000,
                timestamp=1700000000001,
            )
            + frame(
                proto,
                "ProtoOASpotEvent",
                "",
                ctidTraderAccountId=101,
                symbolId=1,
                ask=110010,
                timestamp=1700000000002,
            )
        )
        transport = CTraderTransport(proto, reader, cast(asyncio.StreamWriter, Writer()))
        quote = await transport.spot(
            "ProtoOASubscribeSpotsReq", {"ctidTraderAccountId": 101, "symbolId": [1]}
        )
        assert quote["bid"] == "110000" and quote["ask"] == "110010"
        assert quote["timestamp"] == "1700000000002"

    asyncio.run(run())


def test_oversized_frame_is_refused_before_reading_body() -> None:
    async def run() -> None:
        reader = asyncio.StreamReader()
        reader.feed_data((9 * 1024 * 1024).to_bytes(4, "big"))
        transport = CTraderTransport(protocol(), reader, cast(asyncio.StreamWriter, Writer()))
        with pytest.raises(ValueError, match="frame size"):
            await transport.request(
                "ProtoOAApplicationAuthReq", {"clientId": "offline", "clientSecret": "offline"}
            )

    asyncio.run(run())
