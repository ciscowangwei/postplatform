import pytest
from unittest.mock import MagicMock, patch
from src.adapters.reddit_adapter import RedditAdapter

@pytest.fixture
def mock_creds():
    return {
        'client_id': 'mock_id',
        'client_secret': 'mock_secret',
        'username': 'mock_user',
        'password': 'mock_password',
        'user_agent': 'test_agent'
    }

@patch('praw.Reddit')
def test_reddit_verify_auth_success(mock_praw, mock_creds):
    # Setup mock
    mock_reddit_instance = mock_praw.return_value
    mock_reddit_instance.user.me.return_value = True
    
    adapter = RedditAdapter(mock_creds)
    assert adapter.verify_auth("acc_1") is True

@patch('praw.Reddit')
def test_reddit_verify_auth_failure(mock_praw, mock_creds):
    # Setup mock
    mock_reddit_instance = mock_praw.return_value
    mock_reddit_instance.user.me.side_effect = Exception("Auth failed")
    
    adapter = RedditAdapter(mock_creds)
    assert adapter.verify_auth("acc_1") is False

@patch('praw.Reddit')
def test_reddit_post_text_only(mock_praw, mock_creds):
    mock_reddit_instance = mock_praw.return_value
    mock_subreddit = MagicMock()
    mock_submission = MagicMock()
    mock_submission.url = "https://reddit.com/r/test/comments/123"
    
    mock_reddit_instance.subreddit.return_value = mock_subreddit
    mock_subreddit.submit.return_value = mock_submission
    
    adapter = RedditAdapter(mock_creds)
    content = {
        'title': 'Test Title',
        'body': 'Test Body',
        'subreddit': 'test'
    }
    
    url = adapter.post(content)
    
    assert url == "https://reddit.com/r/test/comments/123"
    mock_subreddit.submit.assert_called_once_with(title='Test Title', selftext='Test Body')

@patch('praw.Reddit')
def test_reddit_post_with_media(mock_praw, mock_creds):
    mock_reddit_instance = mock_praw.return_value
    mock_subreddit = MagicMock()
    mock_submission = MagicMock()
    mock_submission.url = "https://reddit.com/r/test/comments/456"
    
    mock_reddit_instance.subreddit.return_value = mock_subreddit
    mock_subreddit.submit.return_value = mock_submission
    
    adapter = RedditAdapter(mock_creds)
    content = {
        'title': 'Test Media Title',
        'subreddit': 'test',
        'media_path': '/tmp/test.jpg'
    }
    
    url = adapter.post(content)
    
    assert url == "https://reddit.com/r/test/comments/456"
    # Verify that submit was called with url (media) instead of selftext
    args, kwargs = mock_subreddit.submit.call_args
    assert 'url' in kwargs
    assert 'https://i.redd.it/mock_upload_test.jpg' == kwargs['url']
