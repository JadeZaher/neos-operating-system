"""Quiz schemas."""

import datetime as _dt
import uuid
from typing import Optional

from pydantic import BaseModel


class QuizListItem(BaseModel):
    id: uuid.UUID
    course_id: Optional[uuid.UUID] = None
    ecosystem_id: Optional[uuid.UUID] = None
    domain_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    mode: str
    visibility: str
    is_published: bool
    is_entry_quiz: bool = False
    time_limit: Optional[int] = None
    passing_score: Optional[int] = None
    allow_retakes: bool
    created_at: _dt.datetime
    updated_at: _dt.datetime


class QuizDetail(QuizListItem):
    survey_json: Optional[dict] = None
    created_by: Optional[uuid.UUID] = None


class QuizCreateRequest(BaseModel):
    course_id: Optional[uuid.UUID] = None
    ecosystem_id: Optional[uuid.UUID] = None
    domain_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    mode: str = "standard"
    survey_json: Optional[dict] = None
    time_limit: Optional[int] = None
    passing_score: Optional[int] = None
    allow_retakes: bool = True
    visibility: str = "public"
    is_published: bool = False
    created_by: Optional[uuid.UUID] = None


class QuizUpdateRequest(BaseModel):
    course_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    mode: Optional[str] = None
    survey_json: Optional[dict] = None
    time_limit: Optional[int] = None
    passing_score: Optional[int] = None
    allow_retakes: Optional[bool] = None
    visibility: Optional[str] = None
    is_published: Optional[bool] = None


class QuizSubmitRequest(BaseModel):
    survey_results: Optional[dict] = None
    score: Optional[float] = None
    time_spent: Optional[int] = None
    is_passed: Optional[bool] = None
    result_metadata: Optional[dict] = None


class QuizResultItem(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    member_id: uuid.UUID
    score: Optional[float] = None
    is_passed: Optional[bool] = None
    time_spent: Optional[int] = None
    survey_results: Optional[dict] = None
    result_metadata: Optional[dict] = None
    completed_at: Optional[_dt.datetime] = None


class UserTagItem(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    quiz_result_id: Optional[uuid.UUID] = None
    tag_key: str
    tag_value: str
    tag_category: Optional[str] = None
    data_type: Optional[str] = None
    numeric_value: Optional[float] = None


class UserBadgeItem(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    badge_key: str
    badge_name: str
    badge_description: Optional[str] = None
    badge_category: Optional[str] = None
    badge_icon: Optional[str] = None
    strength: Optional[float] = None
    source_tag_keys: Optional[dict] = None
    earned_at: Optional[_dt.datetime] = None
