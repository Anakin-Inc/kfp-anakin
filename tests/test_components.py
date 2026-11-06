"""Component shape: what the compiled pipeline will run in a pod."""

import builtins
import dis
import types

import pytest

import kfp_anakin

NAMES = sorted(n for n in kfp_anakin.__all__ if n not in {"with_api_key", "__version__"})


def globals_used(code: types.CodeType) -> set[str]:
    names = {i.argval for i in dis.get_instructions(code) if i.opname == "LOAD_GLOBAL"}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            names |= globals_used(const)
    return names


def test_covers_all_tools() -> None:
    assert len(NAMES) == 24


@pytest.mark.parametrize("name", NAMES)
def test_runs_on_supported_python_with_the_sdk(name: str) -> None:
    container = getattr(kfp_anakin, name).component_spec.implementation.container
    assert container.image == "python:3.11-slim"
    assert "anakin-sdk>=0.2.0,<0.3.0" in " ".join(container.command)
    assert "kfp-anakin" not in " ".join(container.command[:-1])


@pytest.mark.parametrize("name", NAMES)
def test_embedded_code_is_self_contained(name: str) -> None:
    """KFP copies only the function and its helpers: any other global fails in the pod."""
    component = getattr(kfp_anakin, name)
    script = component.component_spec.implementation.container.command[-1]
    for used in globals_used(component.python_func.__code__):
        assert hasattr(builtins, used) or f"def {used}(" in script, f"{name} uses {used}"
    assert "kfp_anakin" not in script


@pytest.mark.parametrize("name", NAMES)
def test_every_input_is_documented(name: str) -> None:
    component = getattr(kfp_anakin, name)
    doc = component.python_func.__doc__
    for param in component.python_func.__code__.co_varnames[
        : component.python_func.__code__.co_argcount
    ]:
        assert f"{param}:" in doc, f"{name}: {param} is undocumented"
