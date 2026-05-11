# Design Spec: Multi-Platform Auto-Publisher

**Date:** 2026-05-08
**Status:** Draft
**Goal:** A tool to automate content posting (text, image, video) to Reddit and Tom's Hardware using a template-based system and a hybrid auth model.

---

## 1. System Architecture

The system follows a **Plugin-based Adapter Architecture**. The core engine is agnostic of platform-specific logic, communicating only through a standardized interface.

### Data Flow:
`User/CLI` $\rightarrow$ `Dispatcher` $\rightarrow$ `Template Parser` $\rightarrow$ `Auth Manager` $\rightarrow$ `Platform Adapter` $\rightarrow$ `Remote API/Browser`

---

## 2. Auth Management (Hybrid Model)

### 2.1 Storage
- **Backend**: SQLite for metadata, encrypted values for secrets.
- **Encryption**: Use `cryptography.fernet` (Symmetric encryption). The master key is stored in a local environment variable or a protected `.key` file.

### 2.2 Platform-Specific Auth
- **Reddit**:
    - **Method**: OAuth2.
    - **Credentials**: `client_id`, `client_secret`, `username`, `password`, `user_agent`.
    - **Persistence**: Store tokens and refresh them automatically via PRAW.
- **Tom's Hardware**:
    - **Method**: Session Cookie Persistence.
    - **Credentials**: JSON formatted cookies exported from a browser.
    - **Persistence**: Store cookie JSON in the encrypted DB; load into Playwright browser context.

### 2.3 CLI Auth Utility
- `auth login <platform>`: 
    - Reddit: Guide through OAuth flow.
    - Tom's Hardware: Prompt for Cookie JSON string or path to file.

---

## 3. Template & Content System

### 3.1 Template Schema (YAML)
```yaml
template:
  id: "string"
  global:
    title: "string"
    body: "string"
    media:
      - path: "string"
        type: "image|video"
  platforms:
    reddit:
      subreddit: "string"
      flair_id: "string"
      category: "link|text|image|video"
    toms_hardware:
      forum_id: "string"
      tags: ["string"]
```

### 3.2 Variable Resolution
The Dispatcher resolves content using a "Platform-Override" logic:
`Final Value = platform_vars[var] ?? global_vars[var]`

---

## 4. Adapter Interface

All adapters must inherit from `BaseAdapter` and implement:

| Method | Input | Output | Description |
| :--- | :--- | :--- | :--- |
| `verify_auth()` | `account_id` | `bool` | Checks if token/cookie is still valid. |
| `upload_media()` | `file_path` | `media_id/url` | Handles the platform's specific upload API/DOM. |
| `post()` | `resolved_content` | `post_url` | Executes the final publication. |

### 4.1 Reddit Adapter (API)
- **Tooling**: `praw`
- **Logic**: 
    1. Initialize `praw.Reddit` instance.
    2. Upload video/image to Reddit's media server.
    3. Use `subreddit.submit()` with media URL and body.

### 4.2 Tom's Hardware Adapter (Browser)
- **Tooling**: `playwright`
- **Logic**:
    1. Launch headless browser $\rightarrow$ Inject Cookies.
    2. Navigate to the specific forum category URL.
    3. Simulate `click()` on "New Thread".
    4. Use `set_input_files()` for media upload.
    5. `fill()` title and body $\rightarrow$ `click()` Submit.

---

## 5. Error Handling & Reliability

- **Rate Limiting**: Implement an exponential backoff decorator for API calls.
- **Browser Failure**: On `playwright` timeout, take a screenshot of the current page and save to `logs/errors/` for debugging.
- **Validation**: Pre-post check to ensure media files exist and fit platform size limits (e.g., Reddit video limits).
