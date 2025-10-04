from core.exceptions import YAMLValidationError


YAML_SCHEMA = {
    "type": "object",
    "properties": {
        "disciplines": {"type": "object"},
        "metadata": {
            "type": "object",
            "properties": {
                "year": {"type": "string"},
                "degree": {"type": "string"},
                "page_id": {"type": "integer"}
            },
            "required": ["year", "degree"]
        }
    },
    "required": ["disciplines", "metadata"]
}


# ============================================================================
# CORE FUNCTIONS - Чисті функції для обробки даних
# ============================================================================

def validate_yaml_schema(data: dict) -> bool:
    """Валідація структури YAML даних"""
    try:
        required_keys = ['disciplines', 'metadata']
        if not all(key in data for key in required_keys):
            raise YAMLValidationError(f"Missing required keys: {required_keys}")

        metadata = data['metadata']
        if 'year' not in metadata or 'degree' not in metadata:
            raise YAMLValidationError("Metadata must contain 'year' and 'degree'")

        return True
    except Exception as e:
        raise YAMLValidationError(f"YAML validation failed: {e}")
