#!/bin/bash

echo "🚀 Preparing Chrome for Remote Debugging Mode..."

# 1. Kill all existing Chrome processes to ensure the debugging port can be opened
echo "Closing all Chrome instances..."
pkill -f "Google Chrome" || echo "No Chrome instances running."

# Give it a moment to fully shut down
sleep 2

# 2. Launch Chrome with remote debugging port 9222
echo "Launching Chrome in debugging mode on port 9222..."
# Note: Using '&' to run in background so the script can finish
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/projects/postplatform/chrome_profile" &

echo "-------------------------------------------------------------------"
echo "✅ Chrome has been launched!"
echo "👉 PLEASE DO THE FOLLOWING NOW:"
echo "1. In the opened Chrome window, log into your Reddit account."
echo "2. Navigate to the target subreddit (optional, but recommended)."
echo "3. Once logged in, you can run the 'post' command in your terminal."
echo "-------------------------------------------------------------------"
 
EOF
