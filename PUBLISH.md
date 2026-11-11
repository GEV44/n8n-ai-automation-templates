# Publish (run by Gev)

From the repo folder, after `gh auth login`:

```bash
gh repo create GEV44/n8n-ai-automation-templates --public --source . --remote origin --push \
  --description "Six import-ready n8n workflows: AI lead qualification, Gmail triage, Telegram FAQ assistant, bookings, news monitor, review analyzer"

gh repo edit GEV44/n8n-ai-automation-templates --homepage "https://gev44.github.io" \
  --add-topic n8n --add-topic n8n-workflows --add-topic automation --add-topic ai-automation \
  --add-topic openai --add-topic langchain --add-topic telegram-bot --add-topic gmail \
  --add-topic google-sheets --add-topic chatbot --add-topic no-code
```

Then check the Actions tab shows the `validate` run green, pin the repo on your GitHub profile, and link it from the portfolio site.
