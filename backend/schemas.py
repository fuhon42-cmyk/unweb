from pydantic import BaseModel


class ExtractRequest(BaseModel):
    url: str
    use_llm: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [{"url": "https://example.com/article", "use_llm": True}]
        }
    }


class ExtractResponse(BaseModel):
    title: str
    description: str
    content: str
    structured_data: dict
    actions: list[str]
    metadata: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Example Article",
                    "description": "An example article description",
                    "content": "Full article content here...",
                    "structured_data": {"author": "John Doe", "date": "2024-01-01"},
                    "actions": ["save", "share"],
                    "metadata": {"source": "web", "word_count": 1200},
                }
            ]
        }
    }


class PublishRequest(BaseModel):
    url: str
    content: str
    site_name: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com/article",
                    "content": "Content to publish...",
                    "site_name": "my-blog",
                }
            ]
        }
    }


class PublishResponse(BaseModel):
    llms_url: str
    site_id: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "llms_url": "https://llms.example.com/p/abc123",
                    "site_id": "site_abc123",
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    error: str
    detail: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"error": "not_found", "detail": "The requested resource was not found."}
            ]
        }
    }


class AuthRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user_id: str
    api_key: str


class KeyItem(BaseModel):
    id: str
    key: str
    created_at: str


class KeysResponse(BaseModel):
    keys: list[KeyItem]
