import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page
from src.core.base_adapter import BaseAdapter
from typing import Any, Dict, List
import datetime
import os

class TomsHardwareAdapter(BaseAdapter):
    """
    Tom's Hardware implementation using Playwright for browser automation.
    Since there is no public API, this adapter simulates a real user.
    """

    def __init__(self, cookies: List[Dict[str, Any]]):
        """
        Initialize with a list of cookies.
        cookies: List of cookie dictionaries as required by Playwright's add_cookies().
        """
        self.cookies = cookies
        self.browser_type = "chromium"

    async def _get_browser_context(self, playwright) -> tuple[BrowserContext, Page]:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(self.cookies)
        page = await context.new_page()
        return context, page

    def verify_auth(self, account_id: str) -> bool:
        """
        Synchronous wrapper for async auth check.
        Checks if the 'User' profile is visible on the page.
        """
        return asyncio.run(self._async_verify_auth())

    async def _async_verify_auth(self) -> bool:
        async with async_playwright() as p:
            context, page = await self._get_browser_context(p)
            try:
                await page.goto("https://www.tomshardware.com/")
                # Check for common indicators of being logged in (e.g., a profile icon or 'Log Out' text)
                # Note: Selectors need to be updated based on the actual current site DOM.
                is_logged_in = await page.query_selector("text=Log Out") or await page.query_selector(".user-profile")
                return is_logged_in is not None
            except Exception:
                return False
            finally:
                await context.close()

    def upload_media(self, file_path: str) -> str:
        """
        In browser automation, upload is part of the post process.
        We return the path to be used in set_input_files.
        """
        return file_path

    def post(self, content: Dict[str, Any]) -> str:
        """
        Synchronous wrapper for async posting logic.
        """
        return asyncio.run(self._async_post(content))

    async def _async_post(self, content: Dict[str, Any]) -> str:
        async with async_playwright() as p:
            context, page = await self._get_browser_context(p)
            try:
                # 1. Navigate to the specific forum category
                forum_url = content.get('forum_url', 'https://forums.tomshardware.com/')
                await page.goto(forum_url)

                # 2. Click "New Thread" / "Post" button
                # The selector '.btn-new-thread' is a placeholder; actual selector depends on the site
                await page.click("text=Post New Thread")

                # 3. Fill in Title
                await page.fill("input[name='thread_title']", content.get('title', ''))

                # 4. Fill in Body
                await page.fill("textarea[name='message']", content.get('body', ''))

                # 5. Handle Media Upload
                media_path = content.get('media_path')
                if media_path and os.path.exists(media_path):
                    # Find the file input element and upload the file
                    await page.set_input_files("input[type='file']", media_path)

                # 6. Submit the post
                await page.click("button[type='submit']")
                
                # Wait for navigation or success message
                await page.wait_for_load_state("networkidle")
                
                return page.url # Return the URL of the result page

            except Exception as e:
                # Error Screenshotting
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"logs/toms_error_{timestamp}.png"
                os.makedirs("logs", exist_ok=True)
                await page.screenshot(path=screenshot_path)
                raise RuntimeError(f"Tom's Hardware post failed: {str(e)}. Screenshot saved to {screenshot_path}")
            finally:
                await context.close()
