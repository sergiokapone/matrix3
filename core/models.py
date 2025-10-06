# cor/models.py

from typing import TypedDict

from pydantic import BaseModel, field_validator


class DisciplineData(TypedDict):
    name: str
    credits: int
    lecturer_id: str | None
    control: str | None
    subdisciplines: dict[str, object] | None


class UploadResult(BaseModel):
    success: bool
    link: str | None
    message: str

    @field_validator("link")
    def validate_link(cls, v: str | None, values: dict[str, object]) -> str | None:
        if values.get("success") and not v:
            raise ValueError("Link is required when success is True")
        return v


class WordPressPage(BaseModel):
    id: int
    title: str = ""
    content: str = ""
    slug: str = ""
    status: str = "publish"
    link: str | None = None
    parent_id: int | None = None
