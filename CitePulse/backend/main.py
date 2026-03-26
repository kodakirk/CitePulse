import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from .models import AnalysisRequest, AnalysisResponse, AnalysisCounts
from . import services
from .database import create_db_and_tables, get_async_session
from .db_models import User, Analysis
from .auth import auth_backend, fastapi_users, current_active_user, current_user_optional
from .user_schemas import UserRead, UserCreate, UsageStats, AnalysisHistory

load_dotenv()


async def _run_migrations():
    """Add columns that may be missing from existing databases."""
    from sqlalchemy import text, inspect
    from .database import engine

    async with engine.connect() as conn:
        def _check_column(connection):
            insp = inspect(connection)
            columns = [c["name"] for c in insp.get_columns("analyses")]
            return "paper_title" in columns

        try:
            has_col = await conn.run_sync(_check_column)
            if not has_col:
                await conn.execute(text(
                    "ALTER TABLE analyses ADD COLUMN paper_title VARCHAR(1024)"
                ))
                await conn.commit()
                print("[DATABASE] Added paper_title column to analyses")
        except Exception:
            # Table may not exist yet — create_db_and_tables will handle it
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    await _run_migrations()
    print("[DATABASE] Tables created successfully")
    yield


app = FastAPI(
    title="CitePulse API",
    description="Analyze academic papers through citation network analysis using Mistral AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS: Allow connections from any host on the local network
# In production on a LAN, the frontend may be accessed via the server's IP
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routers
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix="/users",
    tags=["users"],
)


@app.get("/")
async def root():
    return {
        "service": "CitePulse API",
        "version": "1.0.0",
        "status": "operational",
        "auth_enabled": True,
    }


@app.get("/me/usage", response_model=UsageStats)
async def get_usage_stats(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    return UsageStats(
        current_month_analyses=user.current_month_analyses,
        reset_date=user.last_reset_date,
    )


@app.get("/me/history", response_model=list[AnalysisHistory])
async def get_analysis_history(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    limit: int = 50
):
    from sqlalchemy import select

    stmt = select(Analysis).where(
        Analysis.user_id == user.id
    ).order_by(Analysis.created_at.desc()).limit(limit)

    result = await session.execute(stmt)
    analyses = result.scalars().all()

    return [
        AnalysisHistory(
            id=a.id,
            paper_id=a.paper_id,
            paper_title=a.paper_title,
            created_at=a.created_at,
            citations_analyzed=a.citations_analyzed,
            support_count=a.support_count,
            extend_count=a.extend_count,
            neutral_count=a.neutral_count,
            refute_count=a.refute_count,
            consensus_score=a.consensus_score,
            processing_time_seconds=a.processing_time_seconds,
        )
        for a in analyses
    ]


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    req: AnalysisRequest,
    user: Optional[User] = Depends(current_user_optional),
    session: AsyncSession = Depends(get_async_session)
):
    """Analyze a paper's citation network to determine scientific consensus."""
    # Validate that Mistral AI is configured
    has_mistral = os.getenv("MISTRAL_API_KEY", "").strip()
    has_ollama = os.getenv("OLLAMA_BASE_URL", "").strip()
    if not has_mistral and not has_ollama:
        # Default Ollama is fine, but warn if neither is explicitly set
        print("[WARN] No MISTRAL_API_KEY or OLLAMA_BASE_URL set, defaulting to http://localhost:11434")

    # Handle title-based search
    paper_id = req.paper_id
    if not paper_id and req.paper_title:
        print(f"Searching for paper by title: '{req.paper_title}'")
        paper_id = await services.search_paper_by_title(req.paper_title)
        if not paper_id:
            raise HTTPException(
                status_code=404,
                detail=f"No paper found with title: '{req.paper_title}'"
            )

    if not paper_id:
        raise HTTPException(
            status_code=400,
            detail="Either paper_id or paper_title must be provided"
        )

    # Fetch paper metadata
    paper_metadata = await services.get_paper_metadata(paper_id)
    paper_title = paper_metadata.get("title") if paper_metadata else None
    is_retracted = paper_metadata.get("is_retracted", False) if paper_metadata else False
    retraction_notice = paper_metadata.get("retraction_notice") if paper_metadata else None

    if is_retracted:
        return AnalysisResponse(
            paper_id=paper_id,
            paper_title=paper_title,
            is_retracted=True,
            retraction_notice=retraction_notice,
            counts=AnalysisCounts(support=0, refute=0, extend=0, neutral=0),
            items=[],
            consensus_score=0.0,
            analyzed_at=datetime.now(timezone.utc).isoformat()
        )

    original_authors = paper_metadata.get("authors", []) if paper_metadata else []

    fetch_limit = req.max_citations * 2 if req.use_temporal_distribution else req.max_citations

    citations = await services.fetch_citations_live(
        paper_id,
        fetch_limit,
        depth=req.analyze_depth,
        follow_up_limit=req.follow_up_limit,
        original_authors=original_authors if req.apply_authorship_bias else None,
    )

    if req.use_temporal_distribution and citations and len(citations) > req.max_citations:
        citations = services.apply_temporal_distribution(citations, req.max_citations)

    if not citations:
        return AnalysisResponse(
            paper_id=paper_id,
            paper_title=paper_title,
            counts=AnalysisCounts(support=0, refute=0, extend=0, neutral=0),
            items=[],
            consensus_score=0.0,
            analyzed_at=datetime.now(timezone.utc).isoformat()
        )

    items = await services.classify_citations_live(citations)

    if req.category_filters:
        filtered_items = [i for i in items if i.polarity in req.category_filters]
        items = filtered_items if filtered_items else items

    counts = AnalysisCounts(
        support=sum(1 for i in items if i.polarity == "support"),
        refute=sum(1 for i in items if i.polarity == "refute"),
        extend=sum(1 for i in items if i.polarity == "extend"),
        neutral=sum(1 for i in items if i.polarity == "neutral"),
    )

    has_any_weighting = (
        req.use_temporal_weighting
        or req.apply_authorship_bias
        or req.use_citation_count_weight
        or req.use_influential_citation_weight
        or req.use_author_hindex_weight
        or req.use_reference_count_weight
    )

    if has_any_weighting:
        consensus_score = services.calculate_weighted_consensus(
            items,
            lambda_decay=req.temporal_lambda if req.use_temporal_weighting else 0.0,
            favor_newer=req.favor_newer,
            apply_authorship_bias=req.apply_authorship_bias,
            authorship_penalty=req.authorship_penalty,
            use_citation_count_weight=req.use_citation_count_weight,
            use_influential_citation_weight=req.use_influential_citation_weight,
            use_author_hindex_weight=req.use_author_hindex_weight,
            use_reference_count_weight=req.use_reference_count_weight,
            invert_metric_weights=req.invert_metric_weights,
        )
    else:
        total = max(len(items), 1)
        consensus_score = (counts.support + 0.5 * counts.extend - counts.refute) / total

    trend_analysis = services.calculate_trend_analysis(items)

    response = AnalysisResponse(
        paper_id=paper_id,
        paper_title=paper_title,
        counts=counts,
        items=items,
        consensus_score=round(consensus_score, 3),
        trend_analysis=trend_analysis,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )

    # Save analysis for authenticated users
    if user:
        analysis_record = Analysis(
            user_id=user.id,
            paper_id=paper_id,
            paper_title=paper_title,
            citations_analyzed=len(items),
            support_count=counts.support,
            extend_count=counts.extend,
            neutral_count=counts.neutral,
            refute_count=counts.refute,
            consensus_score=consensus_score,
        )
        session.add(analysis_record)
        user.current_month_analyses += 1
        await session.commit()
        await session.refresh(user)

    return response
