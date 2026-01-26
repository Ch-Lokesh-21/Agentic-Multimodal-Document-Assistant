"""
Application configuration settings using Pydantic and pydantic-settings.
"""
from functools import lru_cache
from typing import Literal
from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoDBSettings(BaseSettings):
    """MongoDB connection configuration."""
    model_config = SettingsConfigDict(
        env_prefix="MONGODB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    uri: SecretStr = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI",
    )
    database: str = Field(
        default="multimodal_rag",
        description="MongoDB database name",
    )
    # Collection names
    users_collection: str = Field(default="users")
    sessions_collection: str = Field(default="sessions")
    session_messages_collection: str = Field(default="session_messages")
    documents_collection: str = Field(default="documents")
    checkpoints_collection: str = Field(default="langgraph_checkpoints")
    checkpoint_writes_collection: str = Field(
        default="langgraph_checkpoint_writes")


class JWTSettings(BaseSettings):
    """JWT authentication configuration."""

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: SecretStr = Field(
        default="secret_jwt_key",
        description="Secret key for JWT encoding/decoding",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=3,  
        description="Access token expiration in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days",
    )


class LLMSettings(BaseSettings):
    """Language Model configuration."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = Field(
        default="gpt-4.1-mini",
        description="OpenAI LLM model name",
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses",
    )
    max_tokens: int = Field(
        default=2000,
        gt=0,
        description="Maximum tokens in response",
    )
    max_history_messages: int = Field(
        default=10,
        gt=0,
        description="Maximum number of messages to include in LLM context (most recent kept)",
    )
    max_history_tokens: int = Field(
        default=4000,
        gt=0,
        description="Maximum tokens for conversation history in LLM context",
    )
    history_strategy: Literal["last", "first"] = Field(
        default="last",
        description="Strategy for trimming messages: 'last' keeps most recent, 'first' keeps oldest",
    )


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration."""

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model name",
    )


class VectorStoreSettings(BaseSettings):
    """ChromaDB vector store configuration."""

    model_config = SettingsConfigDict(
        env_prefix="VECTORSTORE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    persist_directory: str = Field(
        default="./app/chroma_data",
        description="Base path to Chroma database directory",
    )
    retrieval_k: int = Field(
        default=5,
        gt=0,
        description="Number of documents to retrieve",
    )
    search_type: str = Field(
        default="mmr",
        description="Search type: 'similarity' or 'mmr'",
    )
    mmr_lambda: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="MMR diversity parameter (0=diverse, 1=relevant)",
    )
    enable_hybrid_search: bool = Field(
        default=True,
        description="Enable hybrid search (semantic + lexical) for complex queries",
    )
    enable_reranking: bool = Field(
        default=True,
        description="Enable LLM-based reranking of results",
    )
    rerank_top_k: int = Field(
        default=5,
        gt=0,
        description="Number of chunks to return after reranking",
    )
    hybrid_semantic_weight: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Weight for semantic search in hybrid mode",
    )
    hybrid_lexical_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for lexical search in hybrid mode",
    )


class ChunkingSettings(BaseSettings):
    """Document chunking configuration for Unstructured."""

    model_config = SettingsConfigDict(
        env_prefix="CHUNKING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    strategy: str = Field(
        default="by_title",
        description="Chunking strategy for Unstructured",
    )
    max_characters: int = Field(
        default=1200,
        gt=0,
        description="Maximum characters per chunk",
    )
    new_after_n_chars: int = Field(
        default=1000,
        gt=0,
        description="Start new chunk after N characters",
    )
    combine_under_n_chars: int = Field(
        default=200,
        gt=0,
        description="Combine chunks under N characters",
    )
    partition_strategy: str = Field(
        default="hi_res",
        description="Partition strategy: 'auto', 'fast', 'hi_res', 'ocr_only'",
    )
    use_api: bool = Field(
        default=True,
        description="Whether to use Unstructured API",
    )


class ImageProcessingSettings(BaseSettings):
    """PDF image extraction configuration."""

    model_config = SettingsConfigDict(
        env_prefix="IMAGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_images: int = Field(
        default=2,
        gt=0,
        description="Maximum images to extract per query",
    )
    max_pages: int = Field(
        default=3,
        gt=0,
        description="Maximum pages LLM can select for images",
    )
    zoom_factor: int = Field(
        default=2,
        gt=0,
        description="PDF to image zoom factor for resolution",
    )
    max_width: int = Field(
        default=1200,
        gt=0,
        description="Maximum image width in pixels",
    )
    detail_level: str = Field(
        default="high",
        description="Vision API detail level: 'low', 'high', 'auto'",
    )


class QueryAnalyzerSettings(BaseSettings):
    """Query analyzer configuration for complex query handling."""

    model_config = SettingsConfigDict(
        env_prefix="QUERY_ANALYZER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_sub_queries: int = Field(
        default=3,
        gt=0,
        le=5,
        description="Maximum number of sub-queries allowed for complex queries",
    )


class RAGSettings(BaseSettings):
    """RAG pipeline configuration."""

    model_config = SettingsConfigDict(
        env_prefix="RAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_citations: int = Field(
        default=5,
        gt=0,
        description="Maximum citations to include in response",
    )
    citation_snippet_length: int = Field(
        default=200,
        gt=0,
        description="Maximum characters for citation snippets",
    )
    min_answer_length: int = Field(
        default=50,
        gt=0,
        description="Minimum answer length for quality check",
    )
    quality_uncertainty_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Uncertainty threshold to trigger fallback",
    )
    default_confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Default confidence score for citations",
    )


class UploadSettings(BaseSettings):
    """File upload configuration."""

    model_config = SettingsConfigDict(
        env_prefix="UPLOAD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    directory: str = Field(
        default="./app/uploads",
        description="Directory for uploaded files",
    )
    max_file_size_mb: int = Field(
        default=50,
        description="Maximum file size in MB",
    )
    allowed_extensions: list[str] = Field(
        default=["pdf", "txt", "md", "docx"],
        description="Allowed file extensions for upload",
    )


class TavilySettings(BaseSettings):
    """Tavily web search configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TAVILY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr | None = Field(
        default=None,
        description="Tavily API key for web search",
    )
    max_results: int = Field(
        default=5,
        description="Maximum web search results",
    )


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(
        default="Agentic Multimodal RAG ",
        description="Application name",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode flag",
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )

    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )

    api_prefix: str = Field(
        default="/api/v1",
        description="API route prefix",
    )

    mongodb: MongoDBSettings = Field(default_factory=MongoDBSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vectorstore: VectorStoreSettings = Field(
        default_factory=VectorStoreSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    image: ImageProcessingSettings = Field(
        default_factory=ImageProcessingSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    upload: UploadSettings = Field(default_factory=UploadSettings)
    tavily: TavilySettings = Field(default_factory=TavilySettings)
    query_analyzer: QueryAnalyzerSettings = Field(
        default_factory=QueryAnalyzerSettings)

    @computed_field
    @property
    def upload_max_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.upload.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> AppSettings:
    """
    Get cached application settings singleton.

    Returns:
        AppSettings: Application configuration instance
    """
    return AppSettings()


settings = get_settings()
