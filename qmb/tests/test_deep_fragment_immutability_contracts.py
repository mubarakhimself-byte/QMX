from collections.abc import Mapping
from types import MappingProxyType

import pytest
from qmb.config.fragments import ConfigFragment
from qmb.registryread.as_of import RegistryFragment
from qmf.core import fingerprint, is_ok


def _ok(result):
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
def test_registry_fragment_recursively_freezes_input_and_output(body):
    source = _ok(fingerprint({"source": 1}))
    fragment = _ok(RegistryFragment.try_create(source, body))
    pinned_identity = fragment.fp1_identity()
    pinned_fingerprint = _ok(fingerprint(pinned_identity))

    # Mutate the original graph at every mapping/sequence depth that is present.
    def mutate(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(child, (dict, list, tuple)):
                    mutate(child)
                elif isinstance(child, int):
                    value[key] = child + 1
        elif isinstance(value, (list, tuple)):
            for child in value:
                mutate(child)

    mutate(body)
    assert fragment.fp1_identity() == pinned_identity
    assert _ok(fingerprint(fragment.fp1_identity())) == pinned_fingerprint

    with pytest.raises(TypeError):
        fragment.body["new"] = 1
    nested = fragment.body["a"]
    if isinstance(nested, tuple):
        nested = nested[0]
    while isinstance(nested, tuple):
        nested = nested[0]
    if isinstance(nested, Mapping):
        with pytest.raises(TypeError):
            nested["b"] = 2


def test_config_fragment_recursively_freezes_keys_and_registry_delivery():
    source = _ok(fingerprint({"source": 1}))
    keys = {"sections": [{"name": "entry", "rules": [{"weight": 1}]}]}
    fragment = ConfigFragment(
        format_version=1,
        source_kind="book",
        source_fp1=source,
        keys=keys,
        fingerprint=_ok(fingerprint({"config": 1})),
    )
    original_identity = fragment.fp1_identity()
    keys["sections"][0]["rules"][0]["weight"] = 9
    assert fragment.fp1_identity() == original_identity
    delivered = _ok(fragment.as_registry_fragment())
    assert delivered.body["keys"]["sections"][0]["rules"][0]["weight"] == 1
    assert _ok(fingerprint(delivered.fp1_identity())) == delivered.fingerprint
    assert isinstance(fragment.keys, MappingProxyType)
