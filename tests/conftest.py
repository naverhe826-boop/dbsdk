import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture
def simple_string_schema():
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
        },
    }


@pytest.fixture
def simple_int_schema():
    return {
        "type": "object",
        "properties": {
            "age": {"type": "integer", "minimum": 0, "maximum": 100},
        },
    }


@pytest.fixture
def nested_order_schema():
    return {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "minimum": 1, "maximum": 9999},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                },
            },
            "orders": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "amount": {"type": "number", "minimum": 0.01, "maximum": 9999.99},
                        "status": {"type": "string", "enum": ["pending", "paid", "shipped", "done"]},
                    },
                },
                "minItems": 2,
                "maxItems": 5,
            },
        },
    }
