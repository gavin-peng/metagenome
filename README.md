# MetaGenome API

A production-ready RESTful API for managing genomic file assets (VCF, BAM, CRAM) with explicit lifecycle management, content-addressed storage, and extensible validation.

## Features

- **Content-Addressed Storage**: SHA-256 checksums for idempotency and deduplication
- **Explicit State Machine**: UPLOADED → PREPARED → VALIDATED workflow
- **Synchronous Metadata Extraction**: Fast header parsing with 5-second timeout
- **Policy-Based Validation**: Extensible validation rules for genomic files
- **Dynamic Capabilities**: Files advertise what operations they support
- **Comprehensive Error Handling**: 5 distinct error codes with detailed responses

## Quick Start

### Installation

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Run the Server

```bash
# Development mode
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### File Lifecycle

```
POST   /files                      Upload and register a file
POST   /files/{id}/prepare         Extract metadata from headers
POST   /files/{id}/validate        Validate against policy rules
GET    /files/{id}                 Get file summary
GET    /files/{id}/metadata        Get declared + observed metadata
GET    /files/{id}/capabilities    Get file capabilities
```

## State Machine

```
┌─────────────┐
│   UPLOADED  │  Initial state after upload
└──────┬──────┘
       │ POST /files/{id}/prepare
       ↓
┌─────────────┐
│  PREPARED   │  Metadata extracted
└──────┬──────┘
       │ POST /files/{id}/validate
       ↓
┌─────────────┐
│  VALIDATED  │  Ready for queries
└─────────────┘
```

## Usage Examples

### Complete Workflow

```bash
# 1. Upload file
RESPONSE=$(curl -X POST http://localhost:8000/files \
  -F "file=@sample.vcf.gz" \
  -F "file_type=VCF" \
  -F "declared_metadata={\"samples\":[\"SAMPLE1\"]}")

FILE_ID=$(echo $RESPONSE | jq -r '.id')

# 2. Extract metadata
curl -X POST http://localhost:8000/files/$FILE_ID/prepare

# 3. Validate
curl -X POST http://localhost:8000/files/$FILE_ID/validate

# 4. Get capabilities
curl http://localhost:8000/files/$FILE_ID/capabilities
```

## Error Handling

5 distinct HTTP status codes:

| Code | Type | Example |
|------|------|---------|
| 400 | Bad Request | Invalid JSON |
| 408 | Request Timeout | Parsing > 5s |
| 409 | Conflict | Invalid state transition |
| 422 | Unprocessable Entity | Missing VCF header |
| 500 | Internal Server Error | Database error |

## Development

```bash
# Run tests
poetry run pytest

# Code quality
poetry run black app tests
poetry run ruff check app tests
poetry run mypy app
```

## Documentation

See `docs/` for detailed design documentation:
- `DESIGN_DECISIONS_SUMMARY.md` - Architecture overview
- `error_handling_spec.md` - Complete error catalog
- `validation_policy_design.md` - Validation rules specification

## License

MIT License
