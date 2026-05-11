import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page
from src.core.base_adapter import BaseAdapter
from typing import Any, Dict, List
import datetime
import os

class RedditBrowserAdapter(BaseAdapter):
    """
    Reddit implementation using Playwright for browser automation.
    Used when the user cannot create a developer app or prefers to bypass API limits.
    """

    def __init__(self, cookies: List[Dict[str, Any]]):
        self.cookies = cookies

    async def _get_browser_context(self, playwright) -> tuple[BrowserContext, Page]:
        # Use a realistic User-Agent to avoid "Blocked by network security"
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale="en-US"
        )
        
        # Stealth: Remove the 'webdriver' flag to bypass bot detection
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        await context.add_cookies(self.cookies)
        page = await context.new_page()
        return context, page

    def verify_auth(self, account_id: str) -> bool:
        return asyncio.run(self._async_verify_auth())

    async def _async_verify_auth(self) -> bool:
        async with async_playwright() as p:
            context, page = await self._get_browser_context(p)
            try:
                await page.goto("https://www.reddit.com/user/me")
                # Check if we are on the profile page and not redirected to login
                return "user/me" in page.url or await page.query_selector("text=Log Out") is not None
            except Exception:
                return False
            finally:
                await context.close()

    def upload_media(self, file_path: str) -> str:
        # In browser mode, upload is handled during the post process
        return file_path

    def post(self, content: Dict[str, Any]) -> str:
        return asyncio.run(self._async_post(content))

    async def _async_post(self, content: Dict[str, Any]) -> str:
        async with async_playwright() as p:
            context, page = await self._get_browser_context(p)
            try:
                # 1. Navigate to the target subreddit
                subreddit = content.get('subreddit', 'all')
                await page.goto(f"https://www.reddit.com/r/{subreddit}/")
                
                # --- Human Assistance Window ---
                # Wait for the user to handle potential CAPTCHAs or login challenges
                # in the visible browser window.
                print("Browser opened. Please handle any CAPTCHAs or login checks in the window now...")
                await asyncio.sleep(60) 
                print("Wait time finished, proceeding with the post...")
                # ------------------------------

                # 2. Click "Create Post"
                # Reddit's selectors change often, so we use text-based or aria-label selectors
                await page.click("text=Create Post")

                # 3. Fill Title
                await page.fill("tje-textarea", content.get('title', '')) # Common Reddit title selector

                # 4. Handle Media/Text
                media_path = content.get('media_path')
                if media_path and os.path.exists(media_path):
                    # Upload image/video
                    await page.set_input_files("input[type='file']", media_path)
                else:
                    # Fill body text for self-posts
                    await page.fill("div[role='textbox']", content.get('body', ''))

                # 5. Submit
                await page.click("button:has-text('Post')")
                await page.wait_for_load_state("networkidle")
                
                return page.url

            except Exception as e:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"logs/reddit_browser_error_{timestamp}.png"
                os.makedirs("logs", exist_ok=True)
                await page.screenshot(path=screenshot_path)
                raise RuntimeError(f"Reddit Browser post failed: {str(e)}. Screenshot: {screenshot_path}")
            finally:
                await context.close()
