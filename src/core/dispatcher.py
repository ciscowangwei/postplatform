import yaml
import os
import re
from typing import Any, Dict, Tuple

class Dispatcher:
    """
    Handles template parsing, variable resolution, and routing to platform-specific content.
    """
    
    def __init__(self, global_vars: Dict[str, Any] = None):
        self.global_vars = global_vars or {}

    def _resolve_content(self, content: Any, platform_vars: Dict[str, Any]) -> Any:
        """
        Resolves placeholders in the format {{var_name}}.
        Final Value = platform_vars[var] ?? global_vars[var].
        """
        if not isinstance(content, str):
            return content

        def replace_var(match):
            var_name = match.group(1).strip()
            # Priority: Platform-specific -> Global -> Original placeholder
            return str(platform_vars.get(var_name, self.global_vars.get(var_name, match.group(0))))

        return re.sub(r'\{\{(.*?)\}\}', replace_var, content)

    def dispatch(self, template_path: str, account_id: str) -> Dict[str, Any]:
        """
        Loads YAML template, resolves content based on account_id (simulated as platform_vars),
        and returns the resolved data.
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in template: {e}")
        
        if not template_data:
            raise ValueError("Template file is empty")

        # Handle both nested 'template' key and flat structure
        data = template_data.get('template', template_data)
        
        # Platform detection from account_id (e.g., "reddit_browser_user" -> "reddit")
        platform = account_id.split('_')[0] if '_' in account_id else account_id
        
        # Use a fallback for platform name if it's something like 'reddit_browser'
        if platform == 'reddit':
            pass # correct
        elif 'reddit' in account_id:
            platform = 'reddit'
            
        platform_vars = data.get('platform_overrides', {}).get(platform, {})
        platform_content = data.get('content', {}).get(platform)
        
        if platform_content is None:
            raise KeyError(f"No content defined for platform '{platform}' in template")
        
        resolved_content = self._resolve_content(platform_content, platform_vars)
        
        return {
            "content": resolved_content,
            "platform": platform,
            "account_id": account_id
        }
