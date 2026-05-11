import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.adapters.toms_adapter import TomsHardwareAdapter

@pytest.fixture
def mock_cookies():
    return [{"name": "session", "value": "mock_val", "domain": "tomshardware.com", "path": "/"}]

@pytest.mark.asyncio
async def test_toms_verify_auth_success(mock_cookies):
    adapter = TomsHardwareAdapter(mock_cookies)
    
    # Mock Playwright internals
    with patch("playwright.async_api.async_playwright") as mock_p:
        # Mock the chain: async_playwright -> browser -> context -> page
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = MagicMock() # simulate found element
        
        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page
        
        mock_browser = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_p.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        
        # We call the internal async method for easier testing
        result = await adapter._async_verify_auth()
        assert result is True

@pytest.mark.asyncio
async def test_toms_post_flow(mock_cookies):
    adapter = TomsHardwareAdapter(mock_cookies)
    content = {
        'title': 'My GPU Review',
        'body': 'This is great.',
        'forum_url': 'https://forums.tomshardware.com/forum/',
        'media_path': '/tmp/mock_img.jpg'
    }
    
    with patch("playwright.async_api.async_playwright") as mock_p:
        mock_page = AsyncMock()
        mock_page.url = "https://forums.tomshardware.com/threads/123"
        
        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page
        
        mock_browser = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_p.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        
        # Mock os.path.exists to True for the media path
        with patch("os.path.exists", return_value=True):
            url = await adapter._async_post(content)
            
            assert url == "https://forums.tomshardware.com/threads/123"
            mock_page.fill.assert_any_call("input[name='thread_title']", 'My GPU Review')
            mock_page.set_input_files.assert_called_once_with("input[type='file']", '/tmp/mock_img.jpg')
            mock_page.click.assert_called()
