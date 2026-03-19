from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from .models import MarketDefinition

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, list):
            raise ValueError("expected a JSON list")
        return parsed
    raise ValueError("expected list-like value")


def _normalize_outcome_name(value: Any) -> str:
    return str(value).strip().lower()


def _build_market_definition(entry: dict[str, Any]) -> MarketDefinition:
    market_id = str(
        entry.get("market_id")
        or entry.get("conditionId")
        or entry.get("market")
        or entry.get("id")
        or ""
    ).strip()
    if not market_id:
        raise ValueError("market_id/conditionId/market is required")

    question = str(entry.get("question") or entry.get("title") or entry.get("slug") or market_id)
    slug = entry.get("slug")
    tags = tuple(str(item) for item in entry.get("tags", []))

    yes_asset_id = entry.get("yes_asset_id")
    no_asset_id = entry.get("no_asset_id")
    outcomes = ("Yes", "No")

    if yes_asset_id and no_asset_id:
        yes_asset_id = str(yes_asset_id)
        no_asset_id = str(no_asset_id)
        if "outcomes" in entry:
            raw_outcomes = _as_list(entry["outcomes"])
            if len(raw_outcomes) == 2:
                outcomes = (str(raw_outcomes[0]), str(raw_outcomes[1]))
    else:
        raw_outcomes = _as_list(entry.get("outcomes"))
        raw_tokens = _as_list(entry.get("clobTokenIds") or entry.get("asset_ids"))
        if len(raw_outcomes) != 2 or len(raw_tokens) != 2:
            raise ValueError("binary market needs exactly two outcomes and two asset ids")
        outcome_map = {_normalize_outcome_name(name): str(token) for name, token in zip(raw_outcomes, raw_tokens)}
        if "yes" not in outcome_map or "no" not in outcome_map:
            raise ValueError("only Yes/No binary markets are supported")
        yes_asset_id = outcome_map["yes"]
        no_asset_id = outcome_map["no"]
        outcomes = ("Yes", "No")

    if yes_asset_id == no_asset_id:
        raise ValueError("yes_asset_id and no_asset_id must differ")

    metadata = {
        key: value
        for key, value in entry.items()
        if key
        not in {
            "market_id",
            "market",
            "id",
            "question",
            "title",
            "slug",
            "tags",
            "yes_asset_id",
            "no_asset_id",
            "outcomes",
            "clobTokenIds",
            "asset_ids",
            "conditionId",
        }
    }

    return MarketDefinition(
        market_id=market_id,
        question=question,
        yes_asset_id=str(yes_asset_id),
        no_asset_id=str(no_asset_id),
        slug=str(slug) if slug is not None else None,
        outcomes=outcomes,
        tags=tags,
        metadata=metadata,
    )


def load_market_definitions(path: Path) -> dict[str, MarketDefinition]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        entries = payload.get("markets")
        if not isinstance(entries, list):
            raise ValueError("whitelist object must contain a markets list")
    elif isinstance(payload, list):
        entries = payload
    else:
        raise ValueError("whitelist must be a list or object with markets")

    definitions: dict[str, MarketDefinition] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"market entry at index {index} must be an object")
        definition = _build_market_definition(entry)
        definitions[definition.market_id] = definition

    if not definitions:
        raise ValueError("whitelist is empty")
    return definitions


def is_fee_free_binary_market(entry: dict[str, Any]) -> bool:
    if entry.get("closed") is True:
        return False
    if entry.get("active") is False:
        return False
    if not entry.get("enableOrderBook"):
        return False
    if entry.get("feesEnabled") is True:
        return False

    try:
        outcomes = _as_list(entry.get("outcomes"))
        token_ids = _as_list(entry.get("clobTokenIds") or entry.get("asset_ids"))
    except Exception:
        return False

    if len(outcomes) != 2 or len(token_ids) != 2:
        return False

    normalized = {_normalize_outcome_name(item) for item in outcomes}
    return normalized == {"yes", "no"}


def discover_gamma_fee_free_market_definitions(
    *,
    session: requests.Session | None = None,
    limit: int = 500,
    max_markets: int | None = None,
) -> dict[str, MarketDefinition]:
    http = session if session is not None else requests.Session()
    definitions: dict[str, MarketDefinition] = {}
    offset = 0

    while True:
        response = http.get(
            GAMMA_MARKETS_URL,
            params={"active": "true", "closed": "false", "limit": limit, "offset": offset},
            timeout=30,
        )
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list):
            raise ValueError("unexpected Gamma API response")
        if not rows:
            break

        for entry in rows:
            if not isinstance(entry, dict):
                continue
            if not is_fee_free_binary_market(entry):
                continue
            definition = _build_market_definition(entry)
            definitions[definition.market_id] = definition
            if max_markets is not None and len(definitions) >= max_markets:
                return dict(sorted(definitions.items()))

        offset += limit
        if len(rows) < limit:
            break

    if not definitions:
        raise ValueError("no fee-free binary markets discovered")
    return dict(sorted(definitions.items()))
