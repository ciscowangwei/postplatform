import typer
from typing import Optional
from pathlib import Path
from src.core.auth import CredentialManager, SecretStore
from src.core.dispatcher import Dispatcher
from src.adapters.reddit_adapter import RedditAdapter
from src.adapters.reddit_browser_adapter import RedditBrowserAdapter
from src.adapters.toms_adapter import TomsHardwareAdapter
import os
import json

app = typer.Typer(help="Multi-Platform Auto-Publisher CLI")
auth_app = typer.Typer(help="Manage account authorizations")
app.add_typer(auth_app, name="auth")

_auth_manager = None

def get_auth_manager():
    global _auth_manager
    if _auth_manager is None:
        if "PUBLISHER_MASTER_KEY" not in os.environ:
            typer.echo("Error: PUBLISHER_MASTER_KEY environment variable not set.", err=True)
            raise typer.Exit(code=1)
        _auth_manager = CredentialManager()
    return _auth_manager

@auth_app.command("login-reddit")
def login_reddit():
    """Login to Reddit using either API or Browser Cookies."""
    mode = typer.prompt("Choose auth mode: [1] API (requires App) [2] Browser (Document.cookie string)")
    
    if mode == "1":
        typer.echo("Reddit API Authorization Guide...")
        client_id = typer.prompt("Enter Client ID")
        client_secret = typer.prompt("Enter Client Secret", hide_input=True)
        username = typer.prompt("Enter Reddit Username")
        password = typer.prompt("Enter Reddit Password", hide_input=True)
        user_agent = typer.prompt("Enter User Agent", default="AutoPublisher/2.0")
        
        account_id = f"reddit_api_{username}"
        creds = {
            "auth_type": "api",
            "client_id": client_id, "client_secret": client_secret,
            "username": username, "password": password, "user_agent": user_agent
        }
    elif mode == "2":
        username = typer.prompt("Enter Reddit Username (for ID)")
        cookie_str = typer.prompt("Paste document.cookie string")
        
        # Automatically parse document.cookie string to Playwright format
        cookies = []
        for pair in cookie_str.split(";"):
            if "=" in pair:
                name, value = pair.strip().split("=", 1)
                cookies.append({
                    "name": name,
                    "value": value,
                    "domain": ".reddit.com",
                    "path": "/"
                })
        
        if not cookies:
            typer.echo("Error: No valid cookies found in the provided string.", err=True)
            raise typer.Exit(code=1)
        
        account_id = f"reddit_browser_{username}"
        creds = {
            "auth_type": "browser",
            "cookies": cookies
        }
    else:
        typer.echo("Invalid mode selection.", err=True)
        raise typer.Exit(code=1)
    
    get_auth_manager().save_credential("reddit", account_id, json.dumps(creds))
    typer.echo(f"Successfully saved credentials for {account_id}")

@auth_app.command("login-toms")
def login_toms():
    username = typer.prompt("Enter Account Identifier")
    cookie_json = typer.prompt("Paste Cookie JSON string")
    try:
        json.loads(cookie_json)
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON.", err=True)
        raise typer.Exit(code=1)
    account_id = f"toms_{username}"
    get_auth_manager().save_credential("toms_hardware", account_id, cookie_json)
    typer.echo(f"Successfully saved cookies for {account_id}")

@app.command("post")
def post(
    template: Path = typer.Option(..., "--template", "-t"),
    account: str = typer.Option(..., "--account", "-a")
):
    if not template.exists():
        typer.echo(f"Error: Template {template} not found.", err=True)
        raise typer.Exit(code=1)

    try:
        dispatcher = Dispatcher()
        resolved_data = dispatcher.dispatch(str(template), account)
        platform = resolved_data['platform']
        content = resolved_data['content']
        
        auth_manager = get_auth_manager()
        encrypted_creds = auth_manager.get_credential(platform, account)
        if not encrypted_creds:
            typer.echo(f"Error: No credentials for {account}", err=True)
            raise typer.Exit(code=1)
        
        creds_data = json.loads(encrypted_creds)
        
        if platform == "reddit":
            auth_type = creds_data.get('auth_type', 'api')
            if auth_type == 'api':
                adapter = RedditAdapter(creds_data)
            else:
                adapter = RedditBrowserAdapter(creds_data.get('cookies', []))
        elif platform == "toms_hardware":
            adapter = TomsHardwareAdapter(creds_data if isinstance(creds_data, list) else json.loads(encrypted_creds))
        else:
            typer.echo(f"Unsupported platform {platform}", err=True)
            raise typer.Exit(code=1)
            
        typer.echo(f"Publishing to {platform} via {getattr(adapter, '__class__').__name__}...")
        url = adapter.post(content)
        typer.echo(f"Success! URL: {url}")
        
    except Exception as e:
        typer.echo(f"Publication failed: {str(e)}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
