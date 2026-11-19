"""Cloud translation via Azure AI Translator.

Free F0 tier: 2,000,000 characters per month, always free, which is roughly
three to four novels. Needs an Azure resource plus two environment variables:

    BILINGUALZ_AZURE_KEY=...
    BILINGUALZ_AZURE_REGION=global   # or westeurope, brazilsouth, ...

Optional:
    BILINGUALZ_AZURE_ENDPOINT=https://api.cognitive.microsofttranslator.com
"""

from __future__ import annotations

import os
from typing import Callable

Progress = Callable[[float, str], None]

MAX_BATCH = 90            # Azure accepts 100 elements; leave headroom
MAX_BATCH_CHARS = 45_000  # limit is 50,000 per request


class AzureTranslator:
    name = "azure"

    def __init__(self) -> None:
        self.key = os.environ.get("BILINGUALZ_AZURE_KEY", "").strip()
        self.region = os.environ.get("BILINGUALZ_AZURE_REGION", "global").strip()
        self.endpoint = os.environ.get(
            "BILINGUALZ_AZURE_ENDPOINT",
            "https://api.cognitive.microsofttranslator.com",
        ).rstrip("/")
        if not self.key:
            raise RuntimeError(
                "BILINGUALZ_AZURE_KEY is not set. Create a free F0 Translator "
                "resource in Azure, then set BILINGUALZ_AZURE_KEY and "
                "BILINGUALZ_AZURE_REGION."
            )

    def _batches(self, texts: list[str]) -> list[list[str]]:
        batches: list[list[str]] = []
        current: list[str] = []
        size = 0
        for text in texts:
            length = len(text)
            if current and (len(current) >= MAX_BATCH or size + length > MAX_BATCH_CHARS):
                batches.append(current)
                current, size = [], 0
            current.append(text)
            size += length
        if current:
            batches.append(current)
        return batches

    def translate(
        self,
        texts: list[str],
        source: str,
        target: str,
        on_progress: Progress | None = None,
    ) -> list[str]:
        import requests

        url = f"{self.endpoint}/translate"
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Ocp-Apim-Subscription-Region": self.region,
            "Content-Type": "application/json",
        }
        params = {"api-version": "3.0", "from": source, "to": target}

        out: list[str] = []
        batches = self._batches(texts)
        for index, batch in enumerate(batches):
            response = requests.post(
                url,
                params=params,
                headers=headers,
                json=[{"Text": text} for text in batch],
                timeout=120,
            )
            if response.status_code == 401:
                raise RuntimeError("Azure rejected the key (401).")
            if response.status_code == 403:
                raise RuntimeError("Azure refused the request (403): quota or region mismatch.")
            response.raise_for_status()
            out.extend(item["translations"][0]["text"] for item in response.json())
            if on_progress:
                on_progress((index + 1) / len(batches), "translating")

        return out
