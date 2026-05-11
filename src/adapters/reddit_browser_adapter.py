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
        # If cookies are provided and we aren't in a specific "connect" mode", 
        # we can either launch a new one or connect to an existing one.
        # To support the "Connect to existing Chrome" mode, we check for a specific flag or config.
        # For now, we'll implement a toggle or a fallback.
        
        try:
            # Attempt to connect to a running Chrome instance on port 9222
            # This is the most robust way to bypass bot detection.
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] # Use the existing default context
            print("Successfully connected to existing Chrome instance via CDP.")
        except Exception as e:
            print(f"Could not connect to existing Chrome (port 9222). Falling back to launched browser. Error: {e}")
            # Fallback to the previous launched browser logic
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale="en-US"
            )
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
                print("Browser opened. Please handle any CAPTCHAs or login checks in the window now...")
                await asyncio.sleep(60) 
                print("Wait time finished, proceeding with the post...")
                # ------------------------------

                # 2. Click "Create Post"
                # Try multiple selectors for the "Create Post" button
                create_post_selectors = ["text=Create Post", "button:has-text('Create Post')", "a[href*='/submit']"]
                posted = False
                for selector in create_post_selectors:
                    try:
                        await page.click(selector, timeout=5000)
                        posted = True
                        break
                    except:
                        continue
                if not posted:
                    raise RuntimeError("Could not find 'Create Post' button")

                # 3. Fill Title (with fallback selectors)
                title_text = content.get('title', '')
                title_selectors = [
                    "tje-textarea", 
                    "input[placeholder*='Title']", 
                    "textarea[placeholder*='Title']",
                    "[aria-label*='Title']"
                ]
                title_filled = False
                for selector in title_selectors:
                    try:
                        await page.fill(selector, title_text, timeout=5000)
                        title_filled = True
                        break
                    except:
                        continue
                if not title_filled:
                    raise RuntimeError("Could not find Title input field")

                # 4. Handle Media/Text
                media_path = content.get('media_path')
                if media_path and os.path.exists(media_path):
                    # Try to click the image upload button first if needed, 
                    # then set input files on the hidden input element
                    try:
                        await page.set_input_files("input[type='file']", media_path, timeout=5000)
                    except:
                        raise RuntimeError("Failed to upload media file")
                else:
                    # Fill body text for self-posts
                    body_text = content.get('body', '')
                    body_selectors = ["div[role='textbox']", "textarea[placeholder*='body']", "[aria-label*='body']"]
                    body_filled = False
                    for selector in body_selectors:
                        try:
                            await page.fill(selector, body_text, timeout=5000)
                            body_filled = True
                            break
                        except:
                            continue
                    if not body_filled:
                        raise RuntimeError("Could not find Body input field")

                # 5. Submit
                submit_selectors = ["button:has-text('Post')", "button[type='submit']", "button:has-text('Submit')"]
                submit_clicked = False
                for selector in submit_selectors:
                    try:
                        await page.click(selector, timeout=5000)
                        submit_clicked = True
                        break
                    except:
                        continue
                if not submit_clicked:
                    raise RuntimeError("Could not find Submit button")
                
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
