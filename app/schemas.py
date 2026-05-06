from __future__ import annotations

from pydantic import BaseModel, Field


class PostIngest(BaseModel):
    platform: str = Field(min_length=1)
    text: str = Field(min_length=10)
    published_at: str | None = None
    url: str | None = None


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=5)
    platforms: list[str] = Field(default_factory=lambda: ["linkedin", "x", "instagram"])
    examples_per_platform: int = Field(default=3, ge=1, le=8)
    brand_context: str | None = None


class IdeasRequest(BaseModel):
    topic: str = Field(min_length=5)
    examples: int = Field(default=5, ge=1, le=10)
    brand_context: str | None = None


class DraftOut(BaseModel):
    id: int
    topic: str
    platform: str
    content: str
    status: str
    created_at: str
