# Multi-Platform Auto-Publisher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tool to automate content posting to Reddit (via API) and Tom's Hardware (via Playwright) using template-based content and a hybrid encrypted auth system.

**Architecture:** Plugin-based Adapter pattern. A central Dispatcher handles template resolution and routes requests to platform-specific Adapters. Auth is managed via an encrypted SQLite store.

**Tech Stack:** Python 3.10+, PRAW (Reddit API), Playwright (Browser Automation), SQLAlchemy (Database), Cryptography (Fernet), PyYAML (Templates), Typer (CLI).

---

## File Structure
- `src/core/auth.py`: Encryption and SQLite credential storage.
- `src/core/dispatcher.py`: Template parsing and adapter routing.
- `src/core/base_adapter.py`: Abstract base class for all platform adapters.
- `src/adapters/reddit_adapter.py`: Reddit-specific implementation using PRAW.
- `src/adapters/toms_adapter.py`: Tom's Hardware implementation using Playwright.
- `src/cli/main.py`: Typer-based CLI for auth and posting.
- `tests/test_auth.py`: Tests for encryption and storage.
- `tests/test_dispatcher.py`: Tests for template resolution.
- `tests/test_adapters.py`: Mocked adapter tests.

---

## Implementation Tasks

### Task 1: Encrypted Auth System
**Files:**
- Create: `src/core/auth.py`
- Test: `tests/test_auth.py`

- [ ] **Step 1: Implement Fernet encryption wrapper**
```python
from cryptography.fernet import Fernet
import os

class SecretStore:
    def __init__(self, key=None):
        self.key = key or os.getenv("PUBLISHER_MASTER_KEY").encode()
        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self.cipher.decrypt(token.encode()).decode()
```

- [ ] **Step 2: Implement SQLite storage for credentials**
Use SQLAlchemy to create a `credentials` table: `platform`, `account_id`, `encrypted_blob`.

- [ ] **Step 3: Write failing test for encryption/decryption and DB persistence**
- [ ] **Step 4: Run test to verify failure**
- [ ] **Step 5: Implement `save_credential` and `get_credential` methods**
- [ ] **Step 6: Run test to verify success**
- [ ] **Step 7: Commit**
`git add src/core/auth.py tests/test_auth.py && git commit -m "feat: implement encrypted auth store"`

### Task 2: Template Parser & Dispatcher
**Files:**
- Create: `src/core/dispatcher.py`
- Test: `tests/test_dispatcher.py`

- [ ] **Step 1: Implement `resolve_content` logic**
Handle the priority: `platform_vars` overrides `global_vars`.
```python
def resolve_content(template_data, platform):
    global_vars = template_data.get('global', {})
    platform_vars = template_data.get('platforms', {}).get(platform, {})
    return {**global_vars, **platform_vars}
```

- [ ] **Step 2: Implement `Dispatcher` class**
Method `dispatch(template_path, account_id)` that loads YAML and calls the correct adapter.

- [ ] **Step 3: Write failing test for template resolution and adapter routing**
- [ ] **Step 4: Run test to verify failure**
- [ ] **Step 5: Complete `Dispatcher` implementation**
- [ ] **Step 6: Run test to verify success**
- [ ] **Step 7: Commit**
`git add src/core/dispatcher.py tests/test_dispatcher.py && git commit -m "feat: implement template dispatcher"`

### Task 3: Base Adapter & Reddit Implementation
**Files:**
- Create: `src/core/base_adapter.py`
- Create: `src/adapters/reddit_adapter.py`
- Test: `tests/test_adapters.py`

- [ ] **Step 1: Define `BaseAdapter` ABC**
Methods: `verify_auth()`, `upload_media()`, `post()`.

- [ ] **Step 2: Implement `RedditAdapter` using PRAW**
```python
import praw
class RedditAdapter(BaseAdapter):
    def post(self, content):
        reddit = praw.Reddit(...)
        subreddit = reddit.subreddit(content['subreddit'])
        return subreddit.submit(title=content['title'], selftext=content['body'])
```

- [ ] **Step 3: Implement media upload for Reddit** (Handling images/videos via PRAW).

- [ ] **Step 4: Write mocked tests for RedditAdapter**
- [ ] **Step 5: Run tests to verify success**
- [ ] **Step 6: Commit**
`git add src/core/base_adapter.py src/adapters/reddit_adapter.py tests/test_adapters.py && git commit -m "feat: implement reddit adapter"`

### Task 4: Tom's Hardware Implementation (Playwright)
**Files:**
- Create: `src/adapters/toms_adapter.py`
- Modify: `tests/test_adapters.py`

- [ ] **Step 1: Implement Browser Context setup**
Load cookies from the Auth store into Playwright.
```python
context = browser.new_context()
context.add_cookies(cookie_list)
```

- [ ] **Step 2: Implement navigation and posting flow**
`page.goto(url)` $\rightarrow$ `click('.new-thread')` $\rightarrow$ `fill('#title', ...)` $\rightarrow$ `set_input_files('input[type="file"]', path)`.

- [ ] **Step 3: Implement error screenshotting**
On failure, `page.screenshot(path=f"logs/error_{timestamp}.png")`.

- [ ] **Step 4: Write integration test (using a test account/mock page)**
- [ ] **Step 5: Run test to verify success**
- [ ] **Step 6: Commit**
`git add src/adapters/toms_adapter.py tests/test_adapters.py && git commit -m "feat: implement toms hardware adapter"`

### Task 5: CLI Interface
**Files:**
- Create: `src/cli/main.py`

- [ ] **Step 1: Implement `auth` command group**
`auth login reddit` (OAuth guide) and `auth login toms` (Cookie import).

- [ ] **Step 2: Implement `post` command**
`post --template path/to/template.yaml --account id`.

- [ ] **Step 3: Implement final integration test** (Manual test run with dummy template).
- [ ] **Step 4: Commit**
`git add src/cli/main.py && git commit -m "feat: implement cli interface"`
