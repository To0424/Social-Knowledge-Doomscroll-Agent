"""Tweet summarisation / consolidation via LLM."""

import logging

from llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are SocialScope AI, a social-media intelligence analyst.

The user will provide a collection of tweets from an X/Twitter account.
Each tweet includes text, date, engagement metrics, and (if available)
a sentiment label and topic category.

Your job:
1. **Key themes & topics** — identify the dominant subjects, recurring talking points.
2. **Sentiment overview** — summarise the overall tone and any notable shifts.
3. **Notable tweets** — highlight the most impactful or viral posts (cite text snippets).
4. **Trends** — point out changes over the time range (e.g. increased negativity, new topics emerging).
5. **Actionable takeaway** — one concise paragraph with the most important insight.

Write in clear, concise Markdown.  Use bullet points and bold text for readability.
Ground every claim in the actual data provided — do not hallucinate.\
"""


def summarise_tweets(client: LLMClient, tweets: list[dict], username: str) -> str:
    """Summarise a list of tweets for a given target.

    ``tweets`` should be dicts with at least: content, created_at,
    likes_count, retweets_count, views_count, sentiment_label, category.
    """
    if not tweets:
        return "No tweets found for the selected account and date range."

    # Cap tweets sent to the LLM to avoid overflowing context window.
    # Keep the most recent tweets (already sorted by created_at DESC from DB).
    MAX_TWEETS = 50
    sampled = tweets[:MAX_TWEETS]

    lines: list[str] = []
    for t in sampled:
        date = str(t.get("created_at") or "unknown")[:10]
        sent = t.get("sentiment_label") or "?"
        cat = t.get("category") or "?"
        likes = t.get("likes_count", 0)
        rts = t.get("retweets_count", 0)
        views = t.get("views_count", 0)
        text = (t.get("content") or "")[:280]
        lines.append(
            f"[{date}] sentiment={sent}, category={cat}, "
            f"likes={likes}, RT={rts}, views={views}\n{text}"
        )

    header = f"@{username} — showing {len(sampled)} of {len(tweets)} tweets:\n\n"
    payload = header + "\n---\n".join(lines)

    user_msg = (
        f"Analyze the following tweets from @{username} and provide a structured "
        f"summary following your instructions.\n\n{payload}"
    )

    logger.info("Summarising %d tweets (of %d total) for @%s …", len(sampled), len(tweets), username)
    try:
        return client.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
        )
    except Exception:
        logger.error("LLM summarisation failed", exc_info=True)
        return "Sorry, the LLM failed to generate a summary. Please try again."
