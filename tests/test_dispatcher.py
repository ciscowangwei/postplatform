import pytest
import yaml
import os
from src.core.dispatcher import Dispatcher

def test_basic_resolution_global_vars():
    # Only global variables, no platform overrides
    global_vars = {"name": "World", "city": "New York"}
    dispatcher = Dispatcher(global_vars=global_vars)
    
    # Mock template content
    template_path = "test_basic.yaml"
    content = {
        "platform_overrides": {},
        "content": {
            "twitter": "Hello {{name}} from {{city}}!"
        },
        "adapter_map": {
            "twitter": "TwitterAdapter"
        }
    }
    with open(template_path, "w") as f:
        yaml.dump(content, f)
    
    try:
        resolved, adapter = dispatcher.dispatch(template_path, "twitter_1")
        assert resolved["content"] == "Hello World from New York!"
        assert adapter == "TwitterAdapter"
    finally:
        if os.path.exists(template_path):
            os.remove(template_path)

def test_platform_override():
    # Platform vars should override global vars
    global_vars = {"name": "GlobalName", "city": "GlobalCity"}
    dispatcher = Dispatcher(global_vars=global_vars)
    
    template_path = "test_override.yaml"
    content = {
        "platform_overrides": {
            "twitter": {"name": "TwitterUser"}
        },
        "content": {
            "twitter": "Hello {{name}} from {{city}}!"
        },
        "adapter_map": {
            "twitter": "TwitterAdapter"
        }
    }
    with open(template_path, "w") as f:
        yaml.dump(content, f)
    
    try:
        resolved, adapter = dispatcher.dispatch(template_path, "twitter_1")
        # name should be TwitterUser (override), city should be GlobalCity (global)
        assert resolved["content"] == "Hello TwitterUser from GlobalCity!"
    finally:
        if os.path.exists(template_path):
            os.remove(template_path)

def test_missing_platform_data():
    dispatcher = Dispatcher()
    template_path = "test_missing.yaml"
    content = {
        "content": {
            "twitter": "Hello!"
        },
        "adapter_map": {
            "twitter": "TwitterAdapter"
        }
    }
    with open(template_path, "w") as f:
        yaml.dump(content, f)
    
    try:
        # Request a platform that doesn't exist in content
        with pytest.raises(KeyError):
            dispatcher.dispatch(template_path, "linkedin_1")
    finally:
        if os.path.exists(template_path):
            os.remove(template_path)

def test_invalid_yaml():
    dispatcher = Dispatcher()
    template_path = "test_invalid.yaml"
    with open(template_path, "w") as f:
        f.write("this is not: valid: yaml: {")
    
    try:
        with pytest.raises(ValueError, match="Invalid YAML format"):
            dispatcher.dispatch(template_path, "twitter_1")
    finally:
        if os.path.exists(template_path):
            os.remove(template_path)

def test_file_not_found():
    dispatcher = Dispatcher()
    with pytest.raises(FileNotFoundError):
        dispatcher.dispatch("non_existent.yaml", "twitter_1")
