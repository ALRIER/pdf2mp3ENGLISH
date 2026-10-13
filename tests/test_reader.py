import ast
from pathlib import Path


def test_reader_module_syntax():
    source = Path(__file__).resolve().parents[1] / 'reader.py'
    tree = ast.parse(source.read_text())
    assert any(isinstance(node, ast.FunctionDef) and node.name == 'show_reader' for node in tree.body)
