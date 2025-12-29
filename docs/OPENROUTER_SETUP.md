# OpenRouter Integration Guide

## What is OpenRouter?

OpenRouter provides a unified API gateway for accessing multiple LLM providers through a single interface. Instead of managing separate API keys and implementations for Claude, GPT, Llama, Gemini, and other models, you can use one API key to access them all.

## Benefits

- **Cost Optimization**: Route requests to the most cost-effective model
- **Fallback Options**: Access to multiple providers reduces downtime
- **Model Variety**: Access to models not available through direct APIs:
  - Meta Llama models
  - Google Gemini
  - Mistral AI
  - And many more
- **Simplified Billing**: One bill for all AI usage
- **Rate Limit Pooling**: Better rate limit management across providers

## Setup Instructions

### 1. Get Your OpenRouter API Key

1. Visit [https://openrouter.ai](https://openrouter.ai)
2. Sign up or log in
3. Navigate to **Keys** section
4. Create a new API key
5. Copy the key (starts with `sk-or-v1-...`)

### 2. Configure Dreamcatcher

Add your OpenRouter API key to the `.env` file:

```bash
# Option 1: Use OpenRouter exclusively
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Option 2: Use alongside direct API keys (recommended for fallback)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 3. Restart Services

```bash
# If using Docker
docker-compose -f docker-compose.local.yml restart backend

# If running natively
# Stop and restart the backend server
```

### 4. Verify Integration

Run the test script:

```bash
python test_openrouter.py
```

Expected output:
```
🧪 Testing OpenRouter Integration

📊 Service Status:
  - Claude available: True/False
  - OpenAI available: True/False
  - OpenRouter available: True

🎯 Available Models:
  - openrouter/anthropic/claude-3-haiku
  - openrouter/anthropic/claude-3-sonnet
  - openrouter/anthropic/claude-3-opus
  - openrouter/openai/gpt-3.5-turbo
  - openrouter/openai/gpt-4
  - openrouter/meta-llama/llama-3-70b-instruct
  - openrouter/google/gemini-pro
  - openrouter/mistralai/mistral-large

✅ Success!
```

## Available Models

### Claude Models via OpenRouter
- `openrouter/anthropic/claude-3-haiku` - Fast, cost-effective
- `openrouter/anthropic/claude-3-sonnet` - Balanced performance
- `openrouter/anthropic/claude-3-opus` - Maximum capability

### OpenAI Models via OpenRouter
- `openrouter/openai/gpt-3.5-turbo` - Fast, affordable
- `openrouter/openai/gpt-4` - High capability
- `openrouter/openai/gpt-4-turbo` - Fast GPT-4

### Other Provider Models
- `openrouter/meta-llama/llama-3-70b-instruct` - Meta's open model
- `openrouter/google/gemini-pro` - Google's Gemini
- `openrouter/mistralai/mistral-large` - Mistral AI's flagship

See [OpenRouter Models](https://openrouter.ai/models) for the complete list.

## Usage in Dreamcatcher

### Automatic Model Selection

Dreamcatcher will automatically use OpenRouter if:
1. OpenRouter API key is configured
2. Direct API keys (Claude/OpenAI) are not available
3. A direct API fails and OpenRouter is available as fallback

### Explicit Model Selection

You can specify OpenRouter models directly in API calls:

```python
# Via Python API
response = await ai_service.generate_response(
    prompt="Your idea here",
    model="openrouter/anthropic/claude-3-haiku",
    max_tokens=1000
)

# Via REST API
POST /api/ideas/expand
{
  "idea_id": "123",
  "model": "openrouter/meta-llama/llama-3-70b-instruct"
}
```

### Fallback Behavior

Dreamcatcher's AI service includes intelligent fallback:

1. **Primary Request**: Tries specified model
2. **Retry Logic**: 3 attempts with exponential backoff
3. **Fallback**: Switches to alternative models:
   - Direct API → OpenRouter equivalent
   - OpenRouter → Alternative OpenRouter model → Direct API
4. **Tracking**: Logs which model ultimately succeeded

Example fallback chain for Claude:
```
claude-3-opus (fails)
  → claude-3-sonnet (fails)
  → openrouter/anthropic/claude-3-opus (success!)
```

## Cost Management

### Check Pricing

OpenRouter pricing varies by model. Check current rates at:
[https://openrouter.ai/models](https://openrouter.ai/models)

### Monitor Usage

Track your usage through:

1. **OpenRouter Dashboard**: [https://openrouter.ai](https://openrouter.ai)
2. **Dreamcatcher API**: `GET /api/stats`
3. **Usage Stats**: Built into `AIService.get_usage_stats()`

```python
stats = ai_service.get_usage_stats()
print(f"OpenRouter requests: {stats['openrouter_requests']}")
```

### Set Limits

Configure spending limits in OpenRouter dashboard to prevent unexpected bills.

## Troubleshooting

### "OpenRouter client not initialized"

**Cause**: API key not set or invalid

**Solution**:
1. Check `.env` file has `OPENROUTER_API_KEY=sk-or-v1-...`
2. Verify key is valid on OpenRouter dashboard
3. Restart backend service

### "Model not available"

**Cause**: Model may require credits or special access

**Solution**:
1. Check [OpenRouter Models](https://openrouter.ai/models) for availability
2. Ensure you have credits in your account
3. Use a different model or let fallback handle it

### Rate Limit Errors

**Cause**: Too many requests too quickly

**Solution**:
- Dreamcatcher automatically retries with backoff
- OpenRouter aggregates limits across providers
- Consider upgrading your OpenRouter tier

### High Costs

**Cause**: Using expensive models frequently

**Solution**:
1. Use cheaper models for classification/tagging:
   - `openrouter/anthropic/claude-3-haiku`
   - `openrouter/openai/gpt-3.5-turbo`
2. Reserve expensive models for expansion/proposals:
   - `openrouter/anthropic/claude-3-opus`
   - `openrouter/openai/gpt-4`
3. Check usage stats regularly
4. Set spending limits on OpenRouter dashboard

## Best Practices

### 1. Hybrid Approach (Recommended)

Configure multiple API keys for maximum reliability:

```bash
ANTHROPIC_API_KEY=direct_claude_key
OPENAI_API_KEY=direct_openai_key
OPENROUTER_API_KEY=unified_access_key
```

Benefits:
- Direct APIs for primary usage (often cheaper)
- OpenRouter for fallback and additional models
- Access to exclusive models (Llama, Gemini, etc.)

### 2. Model Selection Strategy

- **Idea Capture/Classification**: Use fast, cheap models
  - `openrouter/anthropic/claude-3-haiku`
  - `openrouter/openai/gpt-3.5-turbo`

- **Idea Expansion**: Use balanced models
  - `openrouter/anthropic/claude-3-sonnet`
  - `openrouter/openai/gpt-4-turbo`

- **Proposals/Important Work**: Use premium models
  - `openrouter/anthropic/claude-3-opus`
  - `openrouter/openai/gpt-4`

### 3. Monitor and Optimize

- Review usage stats weekly
- Identify which operations use most tokens
- Optimize prompts to reduce token usage
- Adjust model selection based on cost/performance

## Security Notes

- Never commit API keys to git
- Use `.env` file (in `.gitignore`)
- Rotate keys periodically
- Use different keys for dev/prod
- Monitor for unusual usage patterns

## Additional Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [Model Comparison](https://openrouter.ai/models)
- [Pricing Calculator](https://openrouter.ai/models)

## Support

For OpenRouter-specific issues:
- OpenRouter Discord: [https://discord.gg/openrouter](https://discord.gg/openrouter)
- OpenRouter Docs: [https://openrouter.ai/docs](https://openrouter.ai/docs)

For Dreamcatcher integration issues:
- Check the main [CLAUDE.md](../CLAUDE.md) guide
- Review backend logs for error details
- Run `python test_openrouter.py` for diagnostics
