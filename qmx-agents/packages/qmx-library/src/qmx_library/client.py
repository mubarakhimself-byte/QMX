"""The Hub client and the owner table (Library AD-11, AD-14, AD-19).

With `settings.toml [library] primary = server` the PC store is a replica plus a hot-blob cache,
and its writes go to the Hub over the tailnet. This module is the PC's side of that: which store
owns a ref (read from the one setting), and the HTTP calls that carry a `LibraryPort` verb to the
Hub. It holds no key of its own; the pairing key is a file whose bytes are never printed.

Order never comes from a clock here (AD-14): a ref move is accepted only when the Hub's head is an
ancestor of the local head, and replication walks objects by their parent hashes.
"""

from __future__ import annotations

import base64
import json
import tomllib
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Literal, cast

from pydantic import JsonValue

from qmx_library.port import (
    BlobRef,
    Claim,
    Commit,
    Draft,
    Hit,
    JsonObject,
    LibraryRefused,
    ObjectId,
    PurgeResult,
)

type Primary = Literal["pc", "server"]
type Owner = Literal["pc", "server", "either"]
"""`either` is a namespace whose owner is the store that minted the run: run ids are UUIDv7, so
the store that holds the first move is the one that minted it (AD-7)."""

PRIMARY: Final = "primary"
HUB_URL: Final = "hub_url"
SETTINGS: Final = "settings.toml"
PAIRING_KEY: Final = "vault/pairing-key"


@dataclass(frozen=True, slots=True)
class Ref:
    """One ref as a store or the Hub reports it: where it points, when it last moved, and under
    which principal (the owner's, so a mirror records the true writer)."""

    item: str
    ref: str
    head: str
    at: str = ""
    principal: str = ""


class OwnerTable:
    """Which store owns which ref namespace, from AD-11 and AD-19, for one `primary` value.

    The table is the whole point of AD-19: flipping `[library] primary` changes the owner of
    `main`, the drafts, the item states, memory and the agent refs together, and no code changes.
    """

    def __init__(self, primary: Primary) -> None:
        if primary not in ("pc", "server"):
            raise LibraryRefused("schema_invalid", f"[library] primary = {primary!r}")
        self.primary: Primary = primary

    def owner(self, ref: str) -> Owner:
        if ref == "main":
            return self.primary
        parts = ref.split("/")
        if len(parts) < 3 or parts[0] != "refs":
            return "either"
        space, rest = parts[1], parts[2:]
        match space:
            case "drafts" | "variants" | "purges" if len(rest) == 1:
                return self.primary
            case "items" if len(rest) == 2 and rest[1] == "state":
                return self.primary
            case "agents" if len(rest) == 2:
                return self.primary
            case "sessions" if len(rest) == 1:
                return self.primary
            case "conflicts":
                return self.primary
            case "memory" if len(rest) == 2 and rest[0] in {"home", "operator"}:
                return self.primary
            case "memory" | "champions" | "challengers":
                return "server"
            case "hub":
                return "server"
            case "runs":
                return "either"
            case _:
                return "either"


def settings_path(home: Path) -> Path:
    return home / SETTINGS


def library_settings(home: Path) -> Mapping[str, Any]:
    """`settings.toml [library]`, empty when the file or the section is absent."""
    path = settings_path(home)
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        document: dict[str, Any] = tomllib.load(handle)
    return cast(Mapping[str, Any], document.get("library", {}))


def primary(home: Path) -> Primary:
    """AD-19's one setting. Absent means `pc`, which is where every home starts."""
    found = str(library_settings(home).get(PRIMARY, "pc"))
    if found == "pc":
        return "pc"
    if found == "server":
        return "server"
    raise LibraryRefused("schema_invalid", f"[library] primary = {found!r}")


def owners(home: Path) -> OwnerTable:
    return OwnerTable(primary(home))


def hub_url(home: Path) -> str | None:
    found = library_settings(home).get(HUB_URL)
    return None if found is None else str(found)


@dataclass(frozen=True, slots=True)
class HubClient:
    """One HTTP call per verb, on the tailnet, with the pairing key as its bearer.

    It is the PC's `Peer` for `qmx_hub.replicate`: `refs`, `blob`, `manifest`, `put_blob`,
    `put_manifest`, `advance` and `apply_purge` are all the Hub exposes.
    """

    url: str
    key: str
    who: str
    timeout: float = 60.0
    name: str = "server"
    """The Hub store's name, for the owner table: the peer is always the server store."""

    @classmethod
    def connect(
        cls,
        home: Path,
        *,
        who: str = "operator",
        key_file: Path | None = None,
        timeout: float = 60.0,
    ) -> HubClient:
        url = hub_url(home)
        if url is None:
            raise LibraryRefused("storage_failure", f"no [library] hub_url in {home}")
        path = key_file or home / PAIRING_KEY
        if not path.exists():
            raise LibraryRefused("storage_failure", f"no pairing key at {path}")
        return cls(url, path.read_text(encoding="utf-8").strip(), who, timeout)

    def call(self, verb: str, **args: JsonValue) -> JsonValue:
        body = json.dumps({"who": self.who, "args": args}).encode("utf-8")
        request = urllib.request.Request(  # noqa: S310 (the URL is the home's own setting)
            f"{self.url}/v1/op/{verb}",
            body,
            {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as answer:  # noqa: S310
                document = cast(dict[str, JsonValue], json.loads(answer.read()))
        except urllib.error.HTTPError as error:
            document = cast(dict[str, JsonValue], json.loads(error.read()))
            if document.get("ok") is False:
                raise LibraryRefused(
                    str(document.get("code", "storage_failure")), str(document.get("message", ""))
                ) from None
            raise
        if document.get("ok") is not True:
            raise LibraryRefused(
                str(document.get("code", "storage_failure")), str(document.get("message", ""))
            )
        return document["value"]

    def health(self) -> Mapping[str, JsonValue]:
        request = urllib.request.Request(  # noqa: S310
            f"{self.url}/healthz", headers={"Authorization": f"Bearer {self.key}"}
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as answer:  # noqa: S310
            return cast(Mapping[str, JsonValue], json.loads(answer.read()))

    def refs(self) -> list[Ref]:
        rows = cast(list[dict[str, str]], self.call("refs"))
        return [
            Ref(row["item"], row["ref"], row["head"], row.get("at", ""), row.get("principal", ""))
            for row in rows
        ]

    def object_ids(self) -> set[str]:
        return {str(object_id) for object_id in cast(Sequence[str], self.call("object_ids"))}

    def manifest(self, object_id: ObjectId) -> Mapping[str, JsonValue] | None:
        found = self.call("manifest", object_id=object_id)
        return None if found is None else cast(Mapping[str, JsonValue], found)

    def put_manifest(self, manifest: Mapping[str, JsonValue]) -> ObjectId:
        return str(self.call("put_manifest", manifest=cast(JsonValue, dict(manifest))))

    def ingest(self, manifest: Mapping[str, JsonValue]) -> str:
        return self.put_manifest(manifest)

    def store_blob(self, data: bytes) -> str:
        return self.put_blob(data)

    def blob_ids(self) -> set[str]:
        return {str(blob_id) for blob_id in cast(Sequence[str], self.call("blob_ids"))}

    def ancestry(self, object_id: ObjectId) -> set[str]:
        return {
            str(found) for found in cast(Sequence[str], self.call("ancestry", object_id=object_id))
        }

    def mirror(self, row: Ref, *, expected_head: str | None) -> None:
        self.call(
            "mirror",
            item=row.item,
            ref=row.ref,
            head=row.head,
            at=row.at,
            principal=row.principal,
            expected_head=expected_head,
        )

    def tombstone(self, blob_id: str) -> Mapping[str, JsonValue] | None:
        found = self.call("tombstone", blob_id=blob_id)
        return None if found is None else cast(Mapping[str, JsonValue], found)

    def blob(self, blob_id: str) -> bytes | None:
        request = urllib.request.Request(  # noqa: S310
            f"{self.url}/v1/blob/{blob_id.removeprefix('sha256:')}",
            headers={"Authorization": f"Bearer {self.key}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as answer:  # noqa: S310
                return answer.read()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise

    def put_blob(self, data: bytes) -> str:
        request = urllib.request.Request(  # noqa: S310
            f"{self.url}/v1/blob",
            data,
            {"Authorization": f"Bearer {self.key}", "Content-Type": "application/octet-stream"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as answer:  # noqa: S310
            return str(cast(dict[str, JsonValue], json.loads(answer.read()))["blob_id"])

    def advance(self, item: str, ref: str, new_head: str, *, expected_head: str | None) -> None:
        self.call("advance", item=item, ref=ref, new_head=new_head, expected_head=expected_head)

    def apply_purge(self, blob_id: str, *, reason: str, at: str) -> None:
        self.call("apply_purge", blob_id=blob_id, reason=reason, at=at)

    def get(self, object_id: ObjectId, *, blobs: Literal["meta", "fetch"] = "meta") -> JsonObject:
        return cast(JsonObject, self.call("get", object_id=object_id, blobs=blobs))

    def search(self, text: str, *, kind: str | None = None, limit: int = 20) -> list[Hit]:
        rows = cast(
            list[dict[str, JsonValue]], self.call("search", text=text, kind=kind, limit=limit)
        )
        return [
            Hit(str(row["object_id"]), str(row["item"]), str(row["kind"]), str(row["title"]), 0.0)
            for row in rows
        ]

    def put(self, draft: Draft, *, on: str, expected_head: ObjectId | None) -> Commit:
        value = cast(
            dict[str, JsonValue],
            self.call("put", draft=draft_payload(draft), on=on, expected_head=expected_head),
        )
        return Commit(
            str(value["object_id"]),
            str(value["item"]),
            str(value["ref"]),
            None if value.get("prev_head") is None else str(value["prev_head"]),
            int(str(value["seq"])),
        )

    def claim(self, intent_key: str, run_id: str, ttl: int) -> Claim:
        value = cast(
            dict[str, JsonValue],
            self.call("claim", intent_key=intent_key, run_id=run_id, ttl=ttl),
        )
        expires = value.get("expires")
        return Claim(
            bool(value["granted"]),
            None if value.get("run_id") is None else str(value["run_id"]),
            None if expires is None else datetime.fromisoformat(str(expires)),
        )

    def release(self, intent_key: str, run_id: str) -> None:
        self.call("release", intent_key=intent_key, run_id=run_id)

    def purge(self, blob_id: str, reason: str) -> PurgeResult:
        value = cast(dict[str, JsonValue], self.call("purge", blob_id=blob_id, reason=reason))
        return PurgeResult(str(value["blob_id"]), str(value["ref"]), Path(str(value["tombstone"])))


def draft_payload(draft: Draft) -> JsonObject:
    """A `Draft` as JSON: bytes become base64, a `BlobRef` stays a reference."""
    return {
        "kind": draft.kind,
        "item": draft.item,
        "title": draft.title,
        "summary": draft.summary,
        "fields": draft.fields,
        "blobs": {
            slot: (
                data.blob_id
                if not isinstance(data, bytes)
                else {"base64": base64.b64encode(data).decode("ascii")}
            )
            for slot, data in draft.blobs.items()
        },
        "relations": [list(relation) for relation in draft.relations],
        "parents": None if draft.parents is None else list(draft.parents),
        "tags": list(draft.tags),
    }


def draft_from_payload(payload: Mapping[str, JsonValue]) -> Draft:
    """The Hub's side of `draft_payload`."""
    blobs: dict[str, bytes | BlobRef] = {}
    for slot, data in cast(Mapping[str, JsonValue], payload.get("blobs") or {}).items():
        if isinstance(data, dict):
            blobs[slot] = base64.b64decode(str(cast(dict[str, JsonValue], data)["base64"]))
        else:
            blobs[slot] = BlobRef(str(data))
    parents = payload.get("parents")
    return Draft(
        kind=str(payload["kind"]),
        item=None if payload.get("item") is None else str(payload["item"]),
        title=str(payload.get("title", "")),
        summary=str(payload.get("summary", "")),
        fields=cast(JsonObject, payload.get("fields") or {}),
        blobs=blobs,
        relations=[
            (str(relation[0]), str(relation[1]))
            for relation in cast(Sequence[Sequence[str]], payload.get("relations") or [])
        ],
        parents=None if parents is None else [str(p) for p in cast(Sequence[str], parents)],
        tags=[str(tag) for tag in cast(Sequence[str], payload.get("tags") or [])],
    )
