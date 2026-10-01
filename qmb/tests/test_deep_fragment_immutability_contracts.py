from collections.abc import Mapping, MutableMapping, Sequence
from types import MappingProxyType
from typing import TypeVar, cast

import pytest
from qmb.config.fragments import ConfigFragment
from qmb.registryread.as_of import RegistryFragment
from qmf.core import Result, fingerprint, is_ok

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


@pytest.mark.parametrize(
    "body",
    [
        {"a": [{"b": 1}]},
        {"a": ({"b": 1},)},
        {"a": [[{"b": 1}]]},
        {"a": ({"b": [{"c": 1}]}, [{"d": 1}])},
    ],
)
def test_registry_fragment_recursively_freezes_input_and_output(
    body: dict[str, object],
) -> None:
    source = _ok(fingerprint({"source": 1}))
    fragment = _ok(RegistryFragment.try_create(source, body))
    pinned_identity = fragment.fp1_identity()
    pinned_fingerprint = _ok(fingerprint(pinned_identity))

    # Mutate the original graph at every mapping/sequence depth that is present.
    def mutate(value: object) -> None:
        if isinstance(value, dict):
            mapping = cast("dict[object, object]", value)
            for key, child in tuple(mapping.items()):
                if isinstance(child, dict):
                    mutate(cast("dict[object, object]", child))
                elif isinstance(child, list):
                    mutate(cast("list[object]", child))
                elif isinstance(child, tuple):
                    mutate(cast("tuple[object, ...]", child))
                elif isinstance(child, int):
                    mapping[key] = child + 1
        elif isinstance(value, (list, tuple)):
            for child in cast("Sequence[object]", value):
                mutate(child)

    mutate(body)
    assert fragment.fp1_identity() == pinned_identity
    assert _ok(fingerprint(fragment.fp1_identity())) == pinned_fingerprint

    with pytest.raises(TypeError):
        cast("MutableMapping[str, object]", fragment.body)["new"] = 1
    nested: object = fragment.body["a"]
    if isinstance(nested, tuple):
        nested = cast("tuple[object, ...]", nested)[0]
    while isinstance(nested, tuple):
        nested = cast("tuple[object, ...]", nested)[0]
    if isinstance(nested, Mapping):
        with pytest.raises(TypeError):
            cast("MutableMapping[str, object]", nested)["b"] = 2


def test_config_fragment_recursively_freezes_keys_and_registry_delivery() -> None:
    source = _ok(fingerprint({"source": 1}))
    keys: dict[str, object] = {"sections": [{"name": "entry", "rules": [{"weight": 1}]}]}
    fragment = ConfigFragment(
        format_version=1,
        source_kind="book",
        source_fp1=source,
        keys=keys,
        fingerprint=_ok(fingerprint({"config": 1})),
    )
    original_identity = fragment.fp1_identity()
    sections = cast("list[object]", keys["sections"])
    section = cast("dict[str, object]", sections[0])
    rules = cast("list[object]", section["rules"])
    rule = cast("dict[str, object]", rules[0])
    rule["weight"] = 9
    assert fragment.fp1_identity() == original_identity
    delivered = _ok(fragment.as_registry_fragment())
    delivered_keys = cast("Mapping[str, object]", delivered.body["keys"])
    delivered_sections = cast("tuple[object, ...]", delivered_keys["sections"])
    delivered_section = cast("Mapping[str, object]", delivered_sections[0])
    delivered_rules = cast("tuple[object, ...]", delivered_section["rules"])
    delivered_rule = cast("Mapping[str, object]", delivered_rules[0])
    assert delivered_rule["weight"] == 1
    assert _ok(fingerprint(delivered.fp1_identity())) == delivered.fingerprint
    assert isinstance(fragment.keys, MappingProxyType)
