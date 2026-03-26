from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class AnalysisRequest(BaseModel):
    paper_id: Optional[str] = Field(None, description="DOI or arXiv ID")
    paper_title: Optional[str] = Field(None, description="Paper title for search")
    max_citations: int = Field(20, ge=10, le=50, description="Maximum number of citations (10-50)")
    analyze_depth: int = Field(1, description="How many hops to analyze: 1 = direct citations only, 2 = include citations-of-citations")
    follow_up_limit: int = Field(5, description="When analyze_depth >= 2, how many secondary citations per citing paper to fetch")
    category_filters: Optional[List[str]] = Field(None, description="Filter results by categories: support, extend, neutral, refute")
    use_temporal_weighting: bool = Field(True, description="Weight newer papers more heavily in consensus calculation")
    use_temporal_distribution: bool = Field(True, description="Distribute sampled papers evenly across time periods")
    temporal_lambda: float = Field(0.05, ge=0.0, le=0.5, description="Temporal decay rate (higher = stronger recency bias)")
    favor_newer: bool = Field(True, description="If True, favor newer research; if False, favor older research")
    apply_authorship_bias: bool = Field(True, description="Reduce weight for self-citations")
    authorship_penalty: float = Field(0.5, ge=0.0, le=1.0, description="Weight multiplier for self-citations (0.0 = ignore, 1.0 = no penalty)")
    # Non-proprietary metric weighting
    use_citation_count_weight: bool = Field(False, description="Weight by citing paper's citation count")
    use_influential_citation_weight: bool = Field(False, description="Weight by citing paper's influential citation count")
    use_author_hindex_weight: bool = Field(False, description="Weight by max author h-index of citing paper")
    use_reference_count_weight: bool = Field(False, description="Weight by citing paper's reference count")
    invert_metric_weights: bool = Field(False, description="Invert metric weights (prioritize lower-metric citations)")


class CitationItem(BaseModel):
    citing_paper_id: str
    title: Optional[str] = None
    snippet: str
    polarity: Literal["support", "refute", "extend", "neutral"]
    confidence: float
    explanation: str
    year: Optional[int] = None
    authors: Optional[List[str]] = Field(None, description="Authors of citing paper")
    is_self_citation: bool = Field(False, description="Whether this is a self-citation")
    journal_name: Optional[str] = Field(None, description="Journal/venue name")
    secondary_evidence: Optional[List[dict]] = None
    # Non-proprietary metrics
    citation_count: Optional[int] = Field(None, description="How many times this citing paper has been cited")
    influential_citation_count: Optional[int] = Field(None, description="Number of influential citations this citing paper has")
    author_hindex: Optional[int] = Field(None, description="Max h-index among the citing paper's authors")
    reference_count: Optional[int] = Field(None, description="Number of references in the citing paper")


class AnalysisCounts(BaseModel):
    support: int
    refute: int
    extend: int
    neutral: int


class TrendAnalysis(BaseModel):
    trend_direction: Literal["trending_up", "declining", "stable"]
    momentum_score: float = Field(..., description="Ratio of recent citations to historical average")
    citations_by_year: dict = Field(..., description="Dictionary mapping year to citation count")
    recent_citations_count: int = Field(..., description="Citations in the last 3 years")
    historical_citations_count: int = Field(..., description="Citations before the last 3 years")
    explanation: str


class AnalysisResponse(BaseModel):
    paper_id: str
    paper_title: Optional[str] = None
    is_retracted: bool = False
    retraction_notice: Optional[str] = None
    counts: AnalysisCounts
    items: List[CitationItem]
    consensus_score: float = Field(..., description="(support+0.5*extend - refute) / total")
    trend_analysis: Optional[TrendAnalysis] = None
    analyzed_at: str
