"""Sentiment analysis — batch-label tweets via LLM."""

import json
import logging

from llm.client import LLMClient

logger = logging.getLogger(__name__)


def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` markdown fences that LLMs love to add."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


SYSTEM_PROMPT = """\
You are a political-media sentiment analyst. You are analyzing tweets and replies
posted directly by a political figure's X/Twitter account.
For each tweet provided, return a JSON array where each element has:
- "tweet_id": the original tweet_id
- "sentiment_score": float from -1.0 (very negative/hostile tone) to 1.0 (very positive/optimistic tone)
- "sentiment_label": one of "positive", "negative", "neutral"
- "category": one of "policy", "economy", "legal", "election", "international", "social", "other"

Respond ONLY with the JSON array, no markdown fences."""


def analyze_sentiment(
    client: LLMClient, tweets: list[dict], chunk_size: int = 10
) -> list[dict]:
    """Send tweets in small chunks for sentiment + category labeling."""
    if not tweets:
        return []

    all_normalized: list[dict] = []

    for start in range(0, len(tweets), chunk_size):
        chunk = tweets[start : start + chunk_size]
        payload = [
            {"tweet_id": t["tweet_id"], "text": t["content"][:500]}
            for t in chunk
        ]
        logger.info(
            "Sending chunk %d–%d / %d to LLM …",
            start + 1, start + len(chunk), len(tweets),
        )

        try:
            content = client.chat(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload)},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
        except Exception:
            logger.error(
                "LLM request failed for chunk %d–%d",
                start + 1, start + len(chunk), exc_info=True,
            )
            continue

        if not content:
            logger.error(
                "LLM returned empty content for chunk %d–%d",
                start + 1, start + len(chunk),
            )
            continue

        raw = _strip_fences(content)
        try:
            results = json.loads(raw)
        except json.JSONDecodeError:
            logger.error(
                "LLM returned invalid JSON for chunk %d–%d: %s",
                start + 1, start + len(chunk), raw[:300],
            )
            continue

        if not isinstance(results, list):
            results = [results]

        # Normalize field names — LLMs often deviate from the prompt
        for i, r in enumerate(results):
            idx = start + i
            tid = r.get("tweet_id") or (
                tweets[idx]["tweet_id"] if idx < len(tweets) else None
            )
            if not tid:
                continue
            score = r.get("sentiment_score")
            label = r.get("sentiment_label") or r.get("sentiment") or "neutral"
            if score is None:
                score = {"positive": 0.5, "negative": -0.5, "neutral": 0.0}.get(
                    label, 0.0
                )
            all_normalized.append({
                "tweet_id": tid,
                "sentiment_score": float(score),
                "sentiment_label": label,
                "category": r.get("category", "other"),
            })

    logger.info(
        "Analyzed sentiment for %d / %d tweets",
        len(all_normalized), len(tweets),
    )
    return all_normalized
