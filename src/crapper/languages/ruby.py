"""Ruby methods and cyclomatic complexity.

Decision points: `if`, `unless`, `elsif`, modifier `if` / `unless` /
`while` / `until` / `rescue`, `while`, `until`, `for`, each `when` and `in`
clause, `rescue`, the ternary, `&&` / `||` / `and` / `or`, and `&.`.
A method's namespace is `Module::Class` from its nesting, with a compact
`class A::B` kept as written. A singleton method (`def self.foo`, or a method
inside `class << self`) is named `self.foo`. A top-level method has the
namespace `Object`. Blocks, lambdas, and nested `def`s stay inside the
enclosing method.
"""

from crapper.languages.treesitter import (
    complexity,
    descendants,
    end_line,
    node_text,
    parse,
    start_line,
)
from crapper.model import Function

_DECISIONS = {
    "if",
    "unless",
    "elsif",
    "if_modifier",
    "unless_modifier",
    "while",
    "until",
    "while_modifier",
    "until_modifier",
    "for",
    "when",
    "in_clause",
    "rescue",
    "rescue_modifier",
    "conditional",
}
_LOGIC = {"&&", "||", "and", "or"}
_METHODS = {"method", "singleton_method"}
_SCOPES = {"module", "class"}


def _is_decision(node) -> bool:
    if not node.is_named:  # keyword tokens reuse node type names such as `if`
        return False
    if node.type in _DECISIONS:
        return True
    if node.type == "binary":
        return any(child.type in _LOGIC for child in node.children)
    return node.type == "call" and any(child.type == "&." for child in node.children)


def _skip(node) -> bool:
    return node.type in _SCOPES or node.type == "singleton_class"


def _is_nested(node) -> bool:
    current = node.parent
    while current is not None:
        if current.type in _METHODS:
            return True
        if current.type in _SCOPES or current.type == "singleton_class":
            return False
        current = current.parent
    return False


def _namespace(data: bytes, node) -> str:
    names: list[str] = []
    current = node.parent
    while current is not None:
        if current.type in _SCOPES:
            name = current.child_by_field_name("name")
            if name is not None:
                names.append(node_text(data, name))
        current = current.parent
    return "::".join(reversed(names)) or "Object"


def _name(data: bytes, node) -> str | None:
    ident = node.child_by_field_name("name")
    if ident is None:
        return None
    name = node_text(data, ident)
    if node.type == "singleton_method":
        return f"{node_text(data, node.child_by_field_name('object'))}.{name}"
    if node.parent is not None and node.parent.parent is not None:
        if node.parent.parent.type == "singleton_class":
            return f"self.{name}"
    return name


def functions_in_source(
    source: str, path: str, source_root: str | None = None
) -> list[Function]:
    data, tree = parse(source, "ruby")
    found: list[Function] = []
    for node in descendants(tree.root_node):
        if node.type not in _METHODS or _is_nested(node):
            continue
        name = _name(data, node)
        if name is None:
            continue
        found.append(
            Function(
                name=name,
                namespace=_namespace(data, node),
                complexity=complexity(node, _is_decision, _skip),
                start_line=start_line(node),
                end_line=end_line(node),
                path=path,
                language="ruby",
            )
        )
    return found
