import os
import json
import asyncio
import httpx
import time
from typing import List, Dict, Optional
from datetime import datetime
import random
from .models import CitationItem


# --- Helper Functions ---

async def search_paper_by_title(title: str) -> Optional[str]:
    """Search for a paper by title and return its paper ID using Semantic Scholar."""
    from difflib import SequenceMatcher
    import urllib.parse

    S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"

    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key

    def similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    async def try_search(query: str, limit: int = 5) -> Optional[str]:
        encoded_query = urllib.parse.quote(query)
        search_url = f"{S2_BASE_URL}/paper/search?query={encoded_query}&limit={limit}&fields=paperId,title,year"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    best_match = None
                    best_score = 0.0
                    for paper in data["data"]:
                        paper_title = paper.get("title", "")
                        score = similarity(query, paper_title)
                        if score > best_score:
                            best_score = score
                            best_match = paper
                    if best_match and best_score > 0.6:
                        paper_id = best_match.get("paperId")
                        found_title = best_match.get("title", "")
                        print(f"Found paper: '{found_title}' (similarity: {best_score:.2f}) with ID: {paper_id}")
                        return paper_id
                return None
        except Exception as e:
            print(f"Search attempt failed for '{query}': {str(e)}")
            return None

    # Strategy 1: Exact title
    result = await try_search(title)
    if result:
        return result

    # Strategy 2: Without special characters
    simplified_title = ''.join(c for c in title if c.isalnum() or c.isspace())
    if simplified_title != title:
        print(f"Retrying with simplified title: '{simplified_title}'")
        result = await try_search(simplified_title)
        if result:
            return result

    # Strategy 3: Key words only
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    words = [w for w in title.split() if w.lower() not in stop_words]
    if len(words) >= 3:
        key_words = ' '.join(words[:10])
        print(f"Retrying with key words: '{key_words}'")
        result = await try_search(key_words)
        if result:
            return result

    print(f"No papers found for title: '{title}' after multiple search strategies")
    return None


async def get_paper_metadata(paper_id: str) -> Optional[Dict]:
    """Fetch paper metadata from Semantic Scholar."""
    S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"
    paper_url = f"{S2_BASE_URL}/paper/{paper_id}?fields=paperId,title,year,authors,externalIds,publicationTypes"

    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(paper_url, headers=headers, timeout=10)
            response.raise_for_status()
            metadata = response.json()

            is_retracted = False
            retraction_notice = None

            pub_types = metadata.get("publicationTypes", [])
            if pub_types and any("Retract" in str(pt) for pt in pub_types):
                is_retracted = True
                retraction_notice = "This paper has been retracted."

            title = metadata.get("title", "").lower()
            if any(keyword in title for keyword in ["retracted", "retraction of", "retraction notice"]):
                is_retracted = True
                if not retraction_notice:
                    retraction_notice = "This paper appears to be a retraction notice or has been retracted."

            metadata["is_retracted"] = is_retracted
            metadata["retraction_notice"] = retraction_notice
            return metadata
    except Exception as e:
        print(f"Error fetching paper metadata: {str(e)}")
        return None


def normalize_author_name(name: str) -> str:
    if not name:
        return ""
    parts = name.strip().split()
    if parts:
        last_name = parts[-1].lower()
        last_name = last_name.replace("jr.", "").replace("sr.", "").replace("iii", "").replace("ii", "")
        return ''.join(c for c in last_name if c.isalnum())
    return ""


def check_author_overlap(original_authors: List[dict], citing_authors: List[dict]) -> bool:
    if not original_authors or not citing_authors:
        return False

    orig_names = set()
    for author in original_authors:
        name = author.get("name", "") if isinstance(author, dict) else str(author)
        normalized = normalize_author_name(name)
        if normalized:
            orig_names.add(normalized)

    citing_names = set()
    for author in citing_authors:
        name = author.get("name", "") if isinstance(author, dict) else str(author)
        normalized = normalize_author_name(name)
        if normalized:
            citing_names.add(normalized)

    return bool(orig_names & citing_names)


def apply_temporal_distribution(citations: List[dict], max_citations: int) -> List[dict]:
    """Sample citations with even distribution across time periods."""
    if not citations or len(citations) <= max_citations:
        return citations

    citations_with_years = []
    for citation in citations:
        citing_paper = citation.get("citingPaper", {})
        year = citing_paper.get("year")
        if year:
            citations_with_years.append((year, citation))

    if not citations_with_years:
        return random.sample(citations, min(max_citations, len(citations)))

    citations_with_years.sort(key=lambda x: x[0])
    min_year = citations_with_years[0][0]
    max_year = citations_with_years[-1][0]
    year_range = max_year - min_year + 1

    if year_range <= 1:
        return random.sample(citations, min(max_citations, len(citations)))

    decades = (year_range + 9) // 10
    papers_per_decade = max(1, max_citations // decades)

    decade_buckets = {}
    for year, citation in citations_with_years:
        decade = (year - min_year) // 10
        if decade not in decade_buckets:
            decade_buckets[decade] = []
        decade_buckets[decade].append(citation)

    sampled_citations = []
    for decade in sorted(decade_buckets.keys()):
        bucket = decade_buckets[decade]
        sample_count = min(papers_per_decade, len(bucket))
        sampled_citations.extend(random.sample(bucket, sample_count))

    if len(sampled_citations) < max_citations:
        remaining = max_citations - len(sampled_citations)
        unsampled = [c for c in citations if c not in sampled_citations]
        if unsampled:
            additional = random.sample(unsampled, min(remaining, len(unsampled)))
            sampled_citations.extend(additional)

    return sampled_citations[:max_citations]


def _normalize_metric(items: List[CitationItem], getter, invert: bool = False) -> List[float]:
    """Normalize a metric across items to 0-1 range using min-max normalization.
    Returns a weight multiplier for each item (defaults to 1.0 if metric unavailable).
    If invert=True, higher raw values produce lower weights.
    """
    values = [getter(item) for item in items]
    numeric = [v for v in values if v is not None]

    if not numeric or max(numeric) == min(numeric):
        return [1.0] * len(items)

    min_val = min(numeric)
    max_val = max(numeric)
    val_range = max_val - min_val

    weights = []
    for v in values:
        if v is None:
            weights.append(0.5)  # neutral weight for missing data
        else:
            normalized = (v - min_val) / val_range  # 0.0 to 1.0
            if invert:
                normalized = 1.0 - normalized
            # Scale to 0.1-1.0 range to avoid zeroing out any citation entirely
            weights.append(0.1 + 0.9 * normalized)
    return weights


def calculate_weighted_consensus(
    items: List[CitationItem],
    lambda_decay: float = 0.05,
    favor_newer: bool = True,
    apply_authorship_bias: bool = True,
    authorship_penalty: float = 0.5,
    use_citation_count_weight: bool = False,
    use_influential_citation_weight: bool = False,
    use_author_hindex_weight: bool = False,
    use_reference_count_weight: bool = False,
    invert_metric_weights: bool = False,
) -> float:
    """Calculate consensus score with temporal weighting, authorship bias, and non-proprietary metrics."""
    if not items:
        return 0.0

    current_year = datetime.now().year

    if not favor_newer:
        oldest_year = min((item.year for item in items if item.year), default=current_year)

    # Pre-compute normalized metric weights
    cc_weights = _normalize_metric(items, lambda i: i.citation_count, invert_metric_weights) if use_citation_count_weight else None
    ic_weights = _normalize_metric(items, lambda i: i.influential_citation_count, invert_metric_weights) if use_influential_citation_weight else None
    ah_weights = _normalize_metric(items, lambda i: i.author_hindex, invert_metric_weights) if use_author_hindex_weight else None
    rc_weights = _normalize_metric(items, lambda i: i.reference_count, invert_metric_weights) if use_reference_count_weight else None

    weighted_sum = 0.0
    total_weight = 0.0

    for idx, item in enumerate(items):
        weight = 1.0

        if lambda_decay > 0:
            year = item.year or current_year
            if favor_newer:
                years_ago = max(0, current_year - year)
                temporal_weight = 2.71828 ** (-lambda_decay * years_ago)
            else:
                years_since_oldest = max(0, year - oldest_year)
                temporal_weight = 2.71828 ** (-lambda_decay * years_since_oldest)
            weight *= temporal_weight

        if apply_authorship_bias and item.is_self_citation:
            weight *= authorship_penalty

        # Apply non-proprietary metric weights
        if cc_weights:
            weight *= cc_weights[idx]
        if ic_weights:
            weight *= ic_weights[idx]
        if ah_weights:
            weight *= ah_weights[idx]
        if rc_weights:
            weight *= rc_weights[idx]

        if item.polarity == "support":
            contribution = 1.0
        elif item.polarity == "extend":
            contribution = 0.5
        elif item.polarity == "refute":
            contribution = -1.0
        else:
            contribution = 0.0

        weighted_sum += contribution * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return weighted_sum / total_weight


def calculate_trend_analysis(items: List[CitationItem]) -> Optional[dict]:
    """Calculate citation trend analysis based on publication years."""
    from .models import TrendAnalysis

    if not items:
        return None

    current_year = datetime.now().year
    recent_years_threshold = 3

    citations_by_year = {}
    recent_citations = 0
    historical_citations = 0

    for item in items:
        year = item.year
        if year:
            citations_by_year[year] = citations_by_year.get(year, 0) + 1
            if current_year - year <= recent_years_threshold:
                recent_citations += 1
            else:
                historical_citations += 1

    if not citations_by_year:
        return None

    min_historical_citations = 3

    if historical_citations >= min_historical_citations:
        historical_years = len([y for y in citations_by_year.keys() if current_year - y > recent_years_threshold])
        historical_rate = historical_citations / max(1, historical_years)
        recent_rate = recent_citations / recent_years_threshold if recent_years_threshold > 0 else 0

        if historical_rate > 0:
            momentum_score = recent_rate / historical_rate
        else:
            momentum_score = recent_rate

        if momentum_score >= 1.3:
            trend_direction = "trending_up"
            explanation = f"Research is gaining momentum! Citations have increased {momentum_score:.1f}x compared to historical average."
        elif momentum_score <= 0.7:
            trend_direction = "declining"
            explanation = f"Citation rate has declined to {momentum_score:.1f}x of historical average."
        else:
            trend_direction = "stable"
            explanation = f"Citations are relatively stable at {momentum_score:.1f}x of historical average."
    else:
        momentum_score = 1.0
        trend_direction = "stable"
        if historical_citations == 0:
            explanation = f"All {recent_citations} citations are from the last {recent_years_threshold} years. Insufficient historical data to assess trend."
        else:
            explanation = f"Mostly recent activity ({recent_citations} recent vs {historical_citations} historical). Insufficient historical data for reliable trend assessment."

    return TrendAnalysis(
        trend_direction=trend_direction,
        momentum_score=round(momentum_score, 2),
        citations_by_year={str(k): v for k, v in sorted(citations_by_year.items())},
        recent_citations_count=recent_citations,
        historical_citations_count=historical_citations,
        explanation=explanation
    )


# --- Rate Limiters ---

class RateLimiter:
    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                await asyncio.sleep(sleep_time)
            self.last_request_time = time.time()


# Mistral AI rate limiter (adjust based on your plan/local setup)
mistral_rate_limiter = RateLimiter(requests_per_second=2.0)
s2_rate_limiter = RateLimiter(requests_per_second=1.0)


# --- Mistral AI Classification ---

SYSTEM_PROMPT = (
    "You are a scientific citation analyzer with expertise in analyzing citation relationships. "
    "You MUST respond with ONLY a JSON object, nothing else. No explanatory text before or after the JSON."
)

USER_TEMPLATE = (
    'Classify how this citing paper relates to the cited work as one of: support, refute, extend, or neutral.\n\n'
    'The information provided may include:\n'
    '- Citation context: How the citing paper explicitly mentions the cited work\n'
    '- Citing paper abstract: Summary of the citing paper\n'
    '- Citing paper title: If no abstract is available, infer the relationship from the title\n'
    '- Secondary evidence: How others cite the citing paper (if available)\n\n'
    'Citation information:\n"""{snippet}"""\n\n'
    'Classification guidelines with heuristics:\n\n'
    '1. SUPPORT (validates/confirms):\n'
    '   - Successfully replicates or reproduces the cited work\'s results\n'
    '   - Provides additional empirical evidence supporting the claims\n'
    '   - Uses the method/approach successfully and confirms its effectiveness\n'
    '   - Cites as authoritative evidence for a claim\n'
    '   - Shows consistent/compatible results in a different context\n'
    '   Confidence heuristics:\n'
    '   - High (0.8-1.0): Explicit replication/validation with clear results\n'
    '   - Medium (0.5-0.7): Indirect support through successful use/application\n'
    '   - Low (0.3-0.4): Implied support without detailed validation\n\n'
    '2. EXTEND (builds upon):\n'
    '   - Identifies and addresses limitations or gaps\n'
    '   - Proposes improvements or optimizations\n'
    '   - Applies the approach in a novel context/domain\n'
    '   - Combines with other methods for enhanced results\n'
    '   - Uses as foundation for a new method/approach\n'
    '   Confidence heuristics:\n'
    '   - High (0.8-1.0): Clear advancement with empirical improvements\n'
    '   - Medium (0.5-0.7): Meaningful modifications with some results\n'
    '   - Low (0.3-0.4): Minor tweaks or theoretical extensions\n\n'
    '3. REFUTE (challenges/contradicts):\n'
    '   - Shows contradictory empirical results\n'
    '   - Identifies fundamental flaws in methodology\n'
    '   - Demonstrates limitations that invalidate claims\n'
    '   - Provides counter-evidence or counter-examples\n'
    '   - Shows failures in replication attempts\n'
    '   Confidence heuristics:\n'
    '   - High (0.8-1.0): Strong empirical evidence contradicting claims\n'
    '   - Medium (0.5-0.7): Identified significant limitations/issues\n'
    '   - Low (0.3-0.4): Theoretical objections or edge cases\n\n'
    '4. NEUTRAL (references without clear position):\n'
    '   - Mentions in background/related work\n'
    '   - Lists as one of many approaches\n'
    '   - Uses as example without evaluating\n'
    '   - Cites for terminology or definitions\n'
    '   - No clear stance on validity/effectiveness\n'
    '   Confidence heuristics:\n'
    '   - High (0.8-1.0): Clearly informational/background reference\n'
    '   - Medium (0.5-0.7): Context unclear but no evaluative content\n'
    '   - Low (0.3-0.4): Limited information to determine relationship\n\n'
    'Additional heuristics:\n'
    '1. Look for temporal clues (e.g., "previously", "recently", "building on")\n'
    '2. Identify comparison language ("better", "worse", "similar to", "unlike")\n'
    '3. Note experimental language ("replicate", "validate", "test", "evaluate")\n'
    '4. Consider citation location (methods, results, background, discussion)\n'
    '5. Check for qualifying words ("however", "although", "nonetheless")\n'
    '6. If secondary evidence available, use it to corroborate relationship\n\n'
    'Conservative confidence policy:\n'
    '- Limited context (title only): cap confidence at 0.4\n'
    '- No explicit relationship terms: cap at 0.6\n'
    '- No empirical/experimental evidence: cap at 0.7\n'
    '- Multiple interpretations possible: reduce by 0.2\n\n'
    'Respond with ONLY this JSON format (no other text):\n'
    '{{"polarity": "support|refute|extend|neutral", "confidence": 0.0-1.0, "explanation": "brief reason with key evidence"}}'
)


def _get_mistral_config() -> dict:
    """Get Mistral AI configuration. Supports both Mistral API and local Ollama."""
    # Check for Mistral API key first (cloud API)
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if api_key:
        return {
            "base_url": "https://api.mistral.ai/v1",
            "api_key": api_key,
            "model": os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
        }

    # Fall back to local Ollama endpoint
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    return {
        "base_url": f"{ollama_url}/v1",
        "api_key": "ollama",  # Ollama accepts any key
        "model": os.getenv("OLLAMA_MODEL", "mistral"),
    }


async def _classify_snippet(session: httpx.AsyncClient, snippet: str, retries: int = 3) -> dict:
    """Classify a single citation snippet using Mistral AI."""
    config = _get_mistral_config()

    for attempt in range(retries):
        try:
            await mistral_rate_limiter.acquire()

            request_body = {
                "model": config["model"],
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_TEMPLATE.format(snippet=snippet)}
                ],
                "response_format": {"type": "json_object"},
            }

            resp = await session.post(
                f"{config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json",
                },
                json=request_body,
                timeout=30,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            if not content:
                raise ValueError("Empty response from model")

            if not content.startswith('{'):
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                else:
                    raise ValueError(f"No JSON found in response: {content[:100]}")

            return json.loads(content)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait_time = (attempt + 1) * 5
                print(f"Rate limited (429), waiting {wait_time}s before retry {attempt + 1}/{retries}")
                await asyncio.sleep(wait_time)
                continue
            else:
                return {"polarity": "neutral", "confidence": 0.0, "explanation": f"HTTP {e.response.status_code}: {str(e)[:100]}"}

        except json.JSONDecodeError as e:
            return {"polarity": "neutral", "confidence": 0.0, "explanation": f"JSON parse error: {str(e)[:100]}"}

        except Exception as e:
            if attempt < retries - 1:
                print(f"Error on attempt {attempt + 1}/{retries}: {str(e)[:100]}")
                await asyncio.sleep(2)
                continue
            else:
                return {"polarity": "neutral", "confidence": 0.0, "explanation": f"error: {str(e)[:100]}"}

    return {"polarity": "neutral", "confidence": 0.0, "explanation": "All retry attempts exhausted"}


async def classify_citations_live(citations: List[dict]) -> List[CitationItem]:
    """Classify multiple citations using Mistral AI."""
    valid_citations = [c for c in citations if c.get("snippet")]
    config = _get_mistral_config()
    print(f"Classifying {len(valid_citations)} citations via {config['model']} at {config['base_url']}...")

    async with httpx.AsyncClient() as session:
        tasks = []
        for c in valid_citations:
            snippet = c["snippet"]
            secondary = c.get("secondary") or []
            if secondary:
                sec_parts = []
                for s in secondary[:5]:
                    t = s.get("title") or s.get("citing_paper_id") or "unknown"
                    snip = s.get("snippet") or ""
                    sec_parts.append(f"- {t}: {snip[:300]}")
                snippet = snippet + "\n\nSecondary evidence (how others cite the citing paper):\n" + "\n".join(sec_parts)
            tasks.append(_classify_snippet(session, snippet))

        all_classifications = await asyncio.gather(*tasks)

    items: List[CitationItem] = []
    ALLOWED = {"support", "refute", "extend", "neutral"}
    for c, res in zip(valid_citations, all_classifications):
        paper_id = c.get("citing_paper_id") or "unknown"

        polarity = res.get("polarity") if isinstance(res.get("polarity"), str) else None
        if polarity not in ALLOWED:
            polarity = "neutral"

        try:
            confidence = float(res.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        explanation = res.get("explanation", "")

        author_names = None
        if c.get("authors"):
            author_names = [auth.get("name") if isinstance(auth, dict) else str(auth) for auth in c.get("authors", [])]

        items.append(CitationItem(
            citing_paper_id=paper_id,
            title=c.get("title"),
            snippet=c["snippet"],
            polarity=polarity,
            confidence=confidence,
            explanation=explanation,
            year=c.get("year"),
            authors=author_names,
            is_self_citation=c.get("is_self_citation", False),
            journal_name=c.get("journal_name"),
            secondary_evidence=c.get("secondary") or None,
            citation_count=c.get("citation_count"),
            influential_citation_count=c.get("influential_citation_count"),
            author_hindex=c.get("author_hindex"),
            reference_count=c.get("reference_count"),
        ))

    print(f"Classification complete: {len(items)} items")
    return items


# --- Semantic Scholar Citation Fetching ---

S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "title,contexts,abstract,year,authors,authors.hIndex,venue,publicationVenue,citationCount,influentialCitationCount,referenceCount"


def normalize_paper_id(paper_id: str) -> str:
    """Normalize paper ID to Semantic Scholar format."""
    import re
    paper_id = paper_id.strip()
    if paper_id and not paper_id.startswith(('arXiv:', 'DOI:', 'PMID:', 'CorpusId:')):
        if re.match(r'^\d{4}\.\d{4,5}$', paper_id):
            return f"arXiv:{paper_id}"
    return paper_id


async def fetch_citations_live(
    paper_id: str,
    max_citations: int = 20,
    depth: int = 1,
    follow_up_limit: int = 5,
    original_authors: Optional[List[dict]] = None
) -> List[dict]:
    """Fetch citation data from Semantic Scholar with rate limiting."""
    normalized_id = normalize_paper_id(paper_id)
    print(f"Fetching citations for paper: {paper_id} (normalized to: {normalized_id})")

    url = f"{S2_BASE_URL}/paper/{normalized_id}/citations?fields={S2_FIELDS}&limit={max_citations}"
    headers = {}

    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key

    try:
        await s2_rate_limiter.acquire()

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json().get("data", [])

        output: List[Dict] = []
        print(f"Enriching citations with abstracts...")

        async with httpx.AsyncClient() as client:
            for i, row in enumerate(data):
                cited_paper = row.get("citingPaper", {})
                paper_id_val = cited_paper.get("paperId") or "unknown"
                title = cited_paper.get("title") or "Unknown Title"

                contexts = cited_paper.get("contexts") or []
                abstract = cited_paper.get("abstract") or ""

                if not abstract and paper_id_val != "unknown":
                    try:
                        await s2_rate_limiter.acquire()
                        paper_url = f"{S2_BASE_URL}/paper/{paper_id_val}?fields=abstract"
                        paper_response = await client.get(paper_url, headers=headers, timeout=10)
                        if paper_response.status_code == 200:
                            paper_data = paper_response.json()
                            abstract = paper_data.get("abstract") or ""
                            if abstract:
                                print(f"  [{i+1}/{len(data)}] Fetched abstract for: {title[:60]}...")
                    except Exception as e:
                        print(f"  Could not fetch abstract for {paper_id_val}: {str(e)[:50]}")

                snippet_parts = []
                if contexts and contexts[0] != "Cites the work.":
                    snippet_parts.append(f"Citation context: {contexts[0]}")
                if abstract:
                    abstract_truncated = abstract[:500] + "..." if len(abstract) > 500 else abstract
                    snippet_parts.append(f"Citing paper abstract: {abstract_truncated}")
                else:
                    snippet_parts.append(f"Citing paper title: {title}")

                snippet = " | ".join(snippet_parts) if snippet_parts else "Cites the work."
                year = cited_paper.get("year")
                authors = cited_paper.get("authors", [])
                is_self_citation = check_author_overlap(original_authors or [], authors) if original_authors else False
                venue = cited_paper.get("venue") or ""
                pub_venue = cited_paper.get("publicationVenue") or {}
                journal_name = venue or pub_venue.get("name") or None

                # Extract non-proprietary metrics
                citation_count = cited_paper.get("citationCount")
                influential_citation_count = cited_paper.get("influentialCitationCount")
                reference_count = cited_paper.get("referenceCount")

                # Max h-index among citing paper's authors
                author_hindex = None
                if authors:
                    h_indices = [a.get("hIndex") for a in authors if isinstance(a, dict) and a.get("hIndex") is not None]
                    if h_indices:
                        author_hindex = max(h_indices)

                output.append({
                    "citing_paper_id": paper_id_val,
                    "title": title,
                    "snippet": snippet,
                    "year": year,
                    "authors": authors,
                    "is_self_citation": is_self_citation,
                    "journal_name": journal_name,
                    "citation_count": citation_count,
                    "influential_citation_count": influential_citation_count,
                    "author_hindex": author_hindex,
                    "reference_count": reference_count,
                })

        # 2-hop citations if depth >= 2
        if depth >= 2 and output:
            print("Fetching secondary (2-hop) citations...")
            async with httpx.AsyncClient() as client2:
                for idx, entry in enumerate(output):
                    cid = entry.get("citing_paper_id")
                    if not cid or cid == "unknown":
                        continue
                    try:
                        await s2_rate_limiter.acquire()
                        sec_url = f"{S2_BASE_URL}/paper/{cid}/citations?fields={S2_FIELDS}&limit={follow_up_limit}"
                        sec_resp = await client2.get(sec_url, headers=headers, timeout=20)
                        sec_resp.raise_for_status()
                        sec_data = sec_resp.json().get("data", [])

                        secondary_list: List[Dict] = []
                        for srow in sec_data:
                            sp = srow.get("citingPaper", {})
                            spid = sp.get("paperId") or "unknown"
                            stitle = sp.get("title") or "Unknown Title"
                            scontexts = sp.get("contexts") or []
                            sabstract = sp.get("abstract") or ""
                            if not sabstract and spid != "unknown":
                                try:
                                    await s2_rate_limiter.acquire()
                                    single_url = f"{S2_BASE_URL}/paper/{spid}?fields=abstract"
                                    single_resp = await client2.get(single_url, headers=headers, timeout=10)
                                    if single_resp.status_code == 200:
                                        single_data = single_resp.json()
                                        sabstract = single_data.get("abstract") or ""
                                except Exception:
                                    pass

                            snippet_parts = []
                            if scontexts and scontexts[0] != "Cites the work.":
                                snippet_parts.append(f"Citation context: {scontexts[0]}")
                            if sabstract:
                                ab_trunc = sabstract[:400] + "..." if len(sabstract) > 400 else sabstract
                                snippet_parts.append(f"Abstract: {ab_trunc}")
                            else:
                                snippet_parts.append(f"Title: {stitle}")

                            ssnippet = " | ".join(snippet_parts) if snippet_parts else "Cites the work."
                            secondary_list.append({
                                "citing_paper_id": spid,
                                "title": stitle,
                                "snippet": ssnippet,
                            })

                        entry["secondary"] = secondary_list
                        print(f"  [{idx+1}/{len(output)}] fetched {len(secondary_list)} secondary citations for {entry.get('title')[:60]}")
                    except httpx.HTTPStatusError as e:
                        print(f"  Could not fetch secondary citations for {cid}: HTTP {e.response.status_code}")
                    except Exception as e:
                        print(f"  Error fetching secondary citations for {cid}: {str(e)[:80]}")

        print(f"Successfully fetched {len(output)} citations for paper {normalized_id}")
        return output

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"Paper ID '{normalized_id}' not found in Semantic Scholar")
            return []
        elif e.response.status_code == 429:
            print(f"Rate limited by Semantic Scholar API. Please add a SEMANTIC_SCHOLAR_API_KEY or wait.")
            return []
        else:
            print(f"HTTP error {e.response.status_code}: {e}")
            return []
    except Exception as e:
        print(f"Error fetching citations: {e}")
        return []
