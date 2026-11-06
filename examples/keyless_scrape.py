"""Scrape one page with no API key or Kubernetes secret: the quickest way to try the package.

Keyless calls use a small free per-IP allowance.
"""

from kfp import compiler, dsl

from kfp_anakin import scrape_url


@dsl.pipeline(name="anakin-keyless-scrape")
def keyless_scrape(url: str = "https://example.com") -> dsl.Dataset:
    return scrape_url(url=url).outputs["document"]


if __name__ == "__main__":
    compiler.Compiler().compile(keyless_scrape, "keyless_scrape.yaml")
