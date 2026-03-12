#!/bin/bash

echo "🚀 Family Financial Analyst - GitHub Push Helper"
echo "================================================"
echo ""
echo "This will push your code to: https://github.com/TalMarkovith/Family-Financial-Analyst"
echo ""
echo "You need a GitHub Personal Access Token (PAT)."
echo "If you don't have one, create it at: https://github.com/settings/tokens/new"
echo "Required scope: 'repo'"
echo ""
read -p "Enter your GitHub username (TalMarkovith): " username
username=${username:-TalMarkovith}

read -sp "Enter your GitHub Personal Access Token: " token
echo ""

# Push using token authentication
git push https://${username}:${token}@github.com/TalMarkovith/Family-Financial-Analyst.git main --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "🌐 View at: https://github.com/TalMarkovith/Family-Financial-Analyst"
else
    echo ""
    echo "❌ Push failed. Please check your token and try again."
fi
