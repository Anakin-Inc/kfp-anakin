"""Search the web, scrape every result in parallel, and build one dataset from the pages.

Compile it with `python examples/web_to_dataset.py`, then upload
web_to_dataset.yaml in the Kubeflow Pipelines UI, or submit it with kfp.Client.
"""

from kfp import compiler, dsl

from kfp_anakin import scrape_url, search, with_api_key


@dsl.component(base_image="python:3.11-slim")
def merge_documents(
    documents: dsl.Input[list[dsl.Dataset]], merged: dsl.Output[dsl.Dataset]
) -> int:
    """Concatenate the scraped documents into one JSONL dataset."""
    rows = 0
    with open(merged.path, "w", encoding="utf-8") as output:
        for document in documents:
            with open(document.path, encoding="utf-8") as lines:
                for line in lines:
                    output.write(line)
                    rows += 1
    return rows


@dsl.pipeline(name="anakin-web-to-dataset")
def web_to_dataset(prompt: str = "open source vector databases", limit: int = 3) -> dsl.Dataset:
    results = with_api_key(search(prompt=prompt, limit=limit))
    with dsl.ParallelFor(results.outputs["urls"], parallelism=3) as url:
        # Keep pages fresh between runs: KFP caches tasks by their inputs.
        page = with_api_key(scrape_url(url=url)).set_caching_options(False)
    merged = merge_documents(documents=dsl.Collected(page.outputs["document"]))
    return merged.outputs["merged"]


if __name__ == "__main__":
    compiler.Compiler().compile(web_to_dataset, "web_to_dataset.yaml")
