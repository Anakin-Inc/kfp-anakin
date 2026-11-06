"""The examples and the secret helper compile to what a cluster needs."""

import importlib.util
import pathlib

import yaml
from kfp import compiler, dsl

from kfp_anakin import scrape_url, with_api_key

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_example(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "examples" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_docs(pipeline, tmp_path):
    target = tmp_path / "p.yaml"
    compiler.Compiler().compile(pipeline, str(target))
    return list(yaml.safe_load_all(target.read_text()))


def test_web_to_dataset_compiles_with_secret_on_each_keyed_task(tmp_path) -> None:
    docs = compile_docs(load_example("web_to_dataset").web_to_dataset, tmp_path)
    assert docs[0]["pipelineInfo"]["name"] == "anakin-web-to-dataset"
    executors = docs[1]["platforms"]["kubernetes"]["deploymentSpec"]["executors"]
    assert len(executors) == 2
    for executor in executors.values():
        secret = executor["secretAsEnv"][0]
        assert secret["secretName"] == "anakin"
        assert secret["keyToEnv"] == [{"secretKey": "api-key", "envVar": "ANAKIN_API_KEY"}]


def test_keyless_example_compiles(tmp_path) -> None:
    docs = compile_docs(load_example("keyless_scrape").keyless_scrape, tmp_path)
    assert docs[0]["pipelineInfo"]["name"] == "anakin-keyless-scrape"


def test_with_api_key_accepts_a_custom_secret(tmp_path) -> None:
    @dsl.pipeline(name="custom-secret")
    def pipeline():
        with_api_key(scrape_url(url="https://a.io"), secret_name="web", secret_key="token")

    docs = compile_docs(pipeline, tmp_path)
    executor = next(
        iter(docs[1]["platforms"]["kubernetes"]["deploymentSpec"]["executors"].values())
    )
    assert executor["secretAsEnv"][0]["secretName"] == "web"
    assert executor["secretAsEnv"][0]["keyToEnv"][0]["secretKey"] == "token"
