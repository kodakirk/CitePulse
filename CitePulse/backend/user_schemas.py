"""Pydantic schemas for user authentication and management."""
from typing import Optional
from fastapi_users import schemas
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserRead(schemas.BaseUser[int]):
    id: int
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    full_name: Optional[str] = None
    created_at: datetime
    current_month_analyses: int
    last_reset_date: datetime


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UsageStats(BaseModel):
    current_month_analyses: int
    reset_date: datetime


class AnalysisHistory(BaseModel):
    id: int
    paper_id: str
    paper_title: Optional[str] = None
    created_at: datetime
    citations_analyzed: int
    support_count: int
    extend_count: int
    neutral_count: int
    refute_count: int
    consensus_score: float
    processing_time_seconds: Optional[float]
