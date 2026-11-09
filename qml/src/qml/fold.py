"""One fold over plain rows: what a scope's brakes say it is doing, read the same way everywhere.

A row is one thing that happened at one scope, as a plain mapping, so this module imports no host
and no journal package (AD-21; CHECK B6 says row shapes live in ``qml`` or ``qmf-risk``). Three
kinds are read at unit scope:

``{"kind": "risk_event", "scope", "at", "id", "code", "verb", "reason"}``
    A brake fired. ``verb`` is the row's own verb, ``no_new_entries`` when a writer omits it (the
    shipped default); ``reason`` is the words, the ``code`` when a writer omits it.
``{"kind": "restore", "scope", "at", "id", "code"}``
    A scope came back: his hand, or the rule that fired it.
``{"kind": "fact", "scope", "at", "id", "name", "limit_ns"}``
    A fact the scope's rows read, and how old it may be. Nothing else is carried: the fold judges
    freshness, a reader reads values from the fact surface.

`fold` reads all of them at once; `Fold` reads them as they arrive and can be cached. The cache is
what the snapshot holds: `cached()` is JSON-safe, and `from_cache` reads a cache that does not parse
back as empty, because rows are the truth and a cache is a cache.

The word is derived, never stored: a fire of a verb that acts raises the word to its own and never
lowers a stronger one, a warn-only fire leaves the word as it was, a restore row is the one that
lowers it, and a fact past its limit makes the word ``UNKNOWN``. ``since`` is dated from the row
that began the word, so a brake firing every bar does not reset it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Final, cast

from qmf.core.chrono import Instant
from qmf.risk.controls import RiskState, StateWord, Verb, word_for

__all__ = ["Fold", "fold"]

_KINDS: Final[frozenset[str]] = frozenset({"risk_event", "restore", "fact"})
_DEFAULT_VERB: Final[Verb] = Verb.NO_NEW_ENTRIES
_RANK: Final[Mapping[StateWord, int]] = {
    StateWord.ACTIVE: 0,
    StateWord.RESTORE: 0,
    StateWord.REDUCING: 1,
    StateWord.BENCHED: 2,
    StateWord.HALTED: 3,
}
"""How strong each word is. A fire raises the word and never lowers it, so a weaker fire cannot
clear a stronger brake; ``RESTORE`` ranks with ``ACTIVE`` because it is the row that lets a lower
word arrive again."""


def fold(rows: Iterable[Mapping[str, object]], scope: str, clock: Instant) -> RiskState:
    """The state ``rows`` give ``scope``, read at ``clock``: ``fold`` in one call."""
    reading = Fold(scope)
    reading.extend(rows)
    return reading.state(clock)


class Fold:
    """One scope's rows, reduced as they arrive, and the state they give at a clock.

    ``through`` is the ``(at, id)`` of the last row folded. A row not after it is skipped, so a
    restart may hand the whole journal again without counting a row twice.
    """

    def __init__(self, scope: str) -> None:
        self._scope = scope
        self._through: tuple[int, str] | None = None
        self._word = StateWord.ACTIVE
        self._since: Instant | None = None
        self._reason = ""
        self._facts: dict[str, tuple[int, int]] = {}

    @property
    def scope(self) -> str:
        return self._scope

    @property
    def through(self) -> tuple[int, str] | None:
        """The last row folded, so a reader knows what a cache already holds."""
        return self._through

    def add(self, row: Mapping[str, object]) -> None:
        """Fold one row, or skip it when it is another scope's or already folded."""
        if row.get("scope") != self._scope:
            return
        kind = _text(row, "kind")
        if kind not in _KINDS:
            raise ValueError(f"the fold reads risk_event, restore or fact rows, not {kind!r}")
        at = _int(row, "at")
        ident = _text(row, "id")
        key = (at, ident)
        if self._through is not None and key <= self._through:
            return
        self._through = key
        match kind:
            case "risk_event":
                self._fire(row, at)
            case "restore":
                self._leave(_text(row, "code"), at)
            case _:
                self._fact(row)

    def extend(self, rows: Iterable[Mapping[str, object]]) -> None:
        """Fold rows in the order given."""
        for row in rows:
            self.add(row)

    def state(self, clock: Instant) -> RiskState:
        """The state at ``clock``, with ``UNKNOWN`` when a fact it holds is past its limit."""
        stale = tuple(
            sorted(name for name, (at, limit) in self._facts.items() if clock.value_ns - at > limit)
        )
        if stale:
            return RiskState(
                scope=self._scope,
                word=StateWord.UNKNOWN,
                since=self._since,
                reason=f"stale {', '.join(stale)}",
                stamp=clock,
                unknown=stale,
            )
        return RiskState(
            scope=self._scope,
            word=self._word,
            since=self._since,
            reason=self._reason,
            stamp=clock,
        )

    def cached(self) -> Mapping[str, object]:
        """The state as JSON-safe data, for a snapshot to cache and `from_cache` to read back."""
        return {
            "scope": self._scope,
            "through": None if self._through is None else [self._through[0], self._through[1]],
            "word": self._word.value,
            "since": None if self._since is None else self._since.value_ns,
            "reason": self._reason,
            "facts": {name: [at, limit] for name, (at, limit) in self._facts.items()},
        }

    @classmethod
    def from_cache(cls, cache: object) -> Fold:
        """The fold a `cached` mapping holds, or an empty fold when it does not read as one."""
        if not isinstance(cache, Mapping):
            return cls("")
        body = cast("Mapping[object, object]", cache)
        scope = body.get("scope")
        if not isinstance(scope, str):
            return cls("")
        made = cls(scope)
        try:
            through = body.get("through")
            if through is not None:
                at, ident = cast("list[object]", through)
                made._through = (int(cast("int", at)), str(ident))
            word = StateWord(str(body.get("word")))
            since = body.get("since")
            made._since = None if since is None else Instant(int(cast("int", since)))
            made._reason = str(body.get("reason", ""))
            facts = body.get("facts", {})
            made._facts = {
                str(name): (int(pair[0]), int(pair[1]))
                for name, pair in cast("Mapping[str, list[int]]", facts).items()
            }
            made._word = word
        except (KeyError, TypeError, ValueError, IndexError):
            return cls(scope)
        return made

    def _fire(self, row: Mapping[str, object], at: int) -> None:
        given = row.get("verb")
        verb = _DEFAULT_VERB if given is None else _verb(given)
        reason = _reason(row, _text(row, "code"))
        if verb is Verb.NONE:  # a warn-only fire refuses nothing, so it never releases a bench
            return
        self._arrive(word_for(verb), reason, at)

    def _leave(self, code: str, at: int) -> None:
        self._arrive(StateWord.RESTORE, code, at)

    def _arrive(self, word: StateWord, reason: str, at: int) -> None:
        """Take ``word`` unless a stronger one since the last restore already holds."""
        if word is not StateWord.RESTORE and _RANK[word] < _RANK[self._word]:
            return
        if word is self._word:
            return
        self._word = word
        self._reason = reason
        self._since = Instant(at)

    def _fact(self, row: Mapping[str, object]) -> None:
        name = _text(row, "name")
        limit = _int(row, "limit_ns")
        if limit <= 0:
            raise ValueError(f"a fact's limit is a positive nanosecond count, not {limit}")
        self._facts[name] = (_int(row, "at"), limit)


def _text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"a fold row's {field} is a non-blank string, not {value!r}")
    return value


def _int(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"a fold row's {field} is an integer, not {value!r}")
    return value


def _verb(given: object) -> Verb:
    try:
        return Verb(str(given))
    except ValueError:
        raise ValueError(f"a risk_event row's verb is one of Verb's words, not {given!r}") from None


def _reason(row: Mapping[str, object], code: str) -> str:
    given = row.get("reason")
    return given if isinstance(given, str) and given else code
