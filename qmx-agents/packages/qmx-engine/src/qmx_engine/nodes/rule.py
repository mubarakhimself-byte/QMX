"""The `rule` node: a safe expression over its inputs that routes to the `true` or `false` port.

The expression is parsed with `ast` and every node checked against a whitelist before anything is
evaluated; then a small interpreter walks the tree. Nothing reaches `eval`, `compile` or a Python
object's attributes: `a.b` reads key `b` of mapping `a`. Calls, lambdas, comprehensions, names or
keys starting with `_`, slices and `**` are refused. The names in scope are `items` (the value on
port `in`) and `inputs` (every port).
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from typing import Any, Final, cast

from pydantic import JsonValue

from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok

MAX_LENGTH: Final = 1000
MAX_REPEAT: Final = 10_000
"""The largest string or list `*` may build, so an expression cannot exhaust memory."""

type Value = JsonValue
type Operator = Callable[[Any, Any], JsonValue]
"""Operands are whatever the inputs hold; a wrong type raises `TypeError`, reported as a
`RuleError`."""

BINARY: Final[Mapping[type[ast.operator], Operator]] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}
COMPARE: Final[Mapping[type[ast.cmpop], Operator]] = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: lambda a, b: a is b,
    ast.IsNot: lambda a, b: a is not b,
}
ALLOWED: Final[tuple[type[ast.AST], ...]] = (
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.USub,
    ast.UAdd,
    ast.BinOp,
    *BINARY,
    ast.Compare,
    *COMPARE,
    ast.IfExp,
    ast.Constant,
    ast.Name,
    ast.Attribute,
    ast.Subscript,
    ast.List,
    ast.Tuple,
    ast.Load,
)


class RuleRefused(ValueError):
    """The expression holds a construct outside the whitelist. Raised before evaluation."""


class RuleError(ValueError):
    """The expression is allowed but failed on these inputs."""


def check(expr: str) -> ast.Expression:
    if len(expr) > MAX_LENGTH:
        raise RuleRefused(f"expression longer than {MAX_LENGTH} characters")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as error:
        raise RuleRefused(f"not an expression: {error.msg}") from None
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED):
            raise RuleRefused(f"{type(node).__name__} is not allowed in a rule")
        name = (
            node.id
            if isinstance(node, ast.Name)
            else node.attr
            if isinstance(node, ast.Attribute)
            else None
        )
        if name is not None and name.startswith("_"):
            raise RuleRefused(f"name {name!r} starts with an underscore")
        if isinstance(node, ast.Constant) and not (
            node.value is None or isinstance(node.value, str | int | float)
        ):
            raise RuleRefused(f"a {type(node.value).__name__} literal is not allowed in a rule")
    return tree


def _key(container: Value, key: Value) -> Value:
    if isinstance(key, str) and key.startswith("_"):
        raise RuleError(f"key {key!r} starts with an underscore")
    if isinstance(container, dict) and isinstance(key, str) and key in container:
        return container[key]
    if (
        isinstance(container, list | str)
        and isinstance(key, int)
        and not isinstance(key, bool)
        and -len(container) <= key < len(container)
    ):
        return container[key]
    raise RuleError(f"no {key!r} in the value")


def _repeat_guard(left: Value, right: Value) -> None:
    for seq, count in ((left, right), (right, left)):
        if isinstance(seq, str | list) and isinstance(count, int) and len(seq) * count > MAX_REPEAT:
            raise RuleError(f"'*' would build more than {MAX_REPEAT} items")


def _evaluate(node: ast.AST, names: Mapping[str, JsonValue]) -> Value:
    match node:
        case ast.Expression(body=body):
            return _evaluate(body, names)
        case ast.Constant(value=value):
            return cast(JsonValue, value)  # `check` let only str, int, float, bool and None in
        case ast.Name(id=name):
            if name not in names:
                raise RuleError(f"unknown name {name!r}")
            return names[name]
        case ast.Attribute(value=value, attr=attr):
            return _key(_evaluate(value, names), attr)
        case ast.Subscript(value=value, slice=index):
            return _key(_evaluate(value, names), _evaluate(index, names))
        case ast.List(elts=elts) | ast.Tuple(elts=elts):
            return [_evaluate(e, names) for e in elts]
        case ast.BoolOp(op=op, values=values):
            result: Value = None
            for v in values:
                result = _evaluate(v, names)
                if bool(result) is isinstance(op, ast.Or):
                    return result
            return result
        case ast.UnaryOp(op=op, operand=operand):
            value = _evaluate(operand, names)
            if isinstance(op, ast.Not):
                return not value
            if not isinstance(value, int | float) or isinstance(value, bool):
                raise RuleError("a sign applies to numbers only")
            return -value if isinstance(op, ast.USub) else value
        case ast.BinOp(left=left, op=op, right=right):
            a, b = _evaluate(left, names), _evaluate(right, names)
            if isinstance(op, ast.Mult):
                _repeat_guard(a, b)
            if isinstance(op, ast.Mod) and isinstance(a, str):
                raise RuleError("'%' formatting is not allowed in a rule")
            return BINARY[type(op)](a, b)
        case ast.Compare(left=left, ops=ops, comparators=comparators):
            a = _evaluate(left, names)
            for op, right in zip(ops, comparators, strict=True):
                b = _evaluate(right, names)
                if not COMPARE[type(op)](a, b):
                    return False
                a = b
            return True
        case ast.IfExp(test=test, body=body, orelse=orelse):
            return _evaluate(body if _evaluate(test, names) else orelse, names)
        case _:
            raise RuleRefused(f"{type(node).__name__} is not allowed in a rule")


def evaluate(expr: str, inputs: JsonValue) -> bool:
    """Check, then evaluate. `RuleRefused` before any evaluation, `RuleError` during it."""
    tree = check(expr)
    ports = inputs if isinstance(inputs, dict) else {}
    try:
        result = _evaluate(tree, {"items": ports.get("in"), "inputs": ports})
    except (TypeError, ArithmeticError) as error:
        raise RuleError(str(error)) from None
    if not isinstance(result, bool):
        raise RuleError(f"the expression gave {type(result).__name__}, not true or false")
    return result


def _failed(code: str, message: str) -> Failed:
    return Failed(code, message, signature(code, message), retryable=False)


class Rule:
    def run(self, job: NodeJob) -> NodeResult:
        parameters = job.node_definition.get("parameters")
        expr = parameters.get("expr") if isinstance(parameters, dict) else None
        if not isinstance(expr, str):
            return _failed("rule_refused", "parameters.expr is not a string")
        try:
            routed = evaluate(expr, job.inputs)
        except RuleRefused as error:
            return _failed("rule_refused", str(error))
        except RuleError as error:
            return _failed("rule_error", str(error))
        ports = job.inputs if isinstance(job.inputs, dict) else {}
        return Ok({"true" if routed else "false": ports.get("in")})
