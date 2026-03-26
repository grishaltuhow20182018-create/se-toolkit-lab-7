# LMS Bot Development Plan

## Overview

This document outlines the development plan for the LMS Telegram Bot (Lab 7). The bot provides students with a convenient way to check their lab submissions, scores, and interact with the Learning Management System through Telegram.

## Architecture

### Project Structure

```
bot/
├── bot.py              # Entry point with --test mode support
├── config.py           # Configuration and environment loading
├── handlers/           # Command handlers (business logic)
│   └── __init__.py     # Handler functions
├── services/           # External API clients
│   └── __init__.py     # LMS API and LLM clients
├── pyproject.toml      # Dependencies
└── .env.bot.secret     # Environment variables (gitignored)
```

### Key Design Decisions

1. **Testable Handlers**: All command handlers are pure functions that take input and return text. They don't depend on Telegram's aiogram library. This allows testing with `--test` mode without connecting to Telegram.

2. **Separation of Concerns**:
   - `handlers/` - Business logic only
   - `services/` - External API communication
   - `bot.py` - Telegram integration and CLI

3. **Test Mode**: The `--test` flag enables offline testing by calling handlers directly and printing results to stdout.

## Task Breakdown

### Task 1: Plan and Scaffold ✅

- [x] Create directory structure
- [x] Implement `--test` mode
- [x] Create handler stubs
- [x] Set up `pyproject.toml`
- [x] Write this development plan

### Task 2: Backend Integration

- [ ] Implement real LMS API client in `services/`
- [ ] Connect `/health` to actual backend health endpoint
- [ ] Implement `/labs` to fetch from `/items/`
- [ ] Implement `/scores` to fetch from `/logs/`
- [ ] Add error handling for API failures
- [ ] Test with real backend data

### Task 3: Intent Routing

- [ ] Implement LLM client in `services/`
- [ ] Create intent detection prompt
- [ ] Route natural language queries to appropriate handlers
- [ ] Handle fallback when LLM is unavailable
- [ ] Test with various user queries

### Task 4: Deployment

- [ ] Create systemd service for the bot
- [ ] Set up auto-restart on failure
- [ ] Configure logging
- [ ] Test deployment on VM
- [ ] Verify bot responds in Telegram

## Testing Strategy

1. **Unit Tests**: Test handlers in isolation (Task 2)
2. **Integration Tests**: Test API clients with mock responses
3. **Manual Testing**: Use `--test` mode for each command
4. **End-to-End**: Deploy and test in Telegram

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | `123456:ABC-DEF1234...` |
| `LMS_API_BASE_URL` | Backend API URL | `http://localhost:42002` |
| `LMS_API_KEY` | Backend API key | `your-api-key` |
| `LLM_API_KEY` | LLM API key | `sk-...` |
| `LLM_API_BASE_URL` | LLM API URL | `http://localhost:42005/v1` |
| `LLM_API_MODEL` | LLM model name | `coder-model` |

## Timeline

| Task | Estimated Time | Dependencies |
|------|----------------|--------------|
| Task 1 | 1 hour | None |
| Task 2 | 3-4 hours | Task 1, backend running |
| Task 3 | 2-3 hours | Task 1, Qwen API |
| Task 4 | 1-2 hours | Task 2-3 completed |

## Risks and Mitigations

1. **API Changes**: Backend endpoints might change. Mitigation: Use typed API client with clear error messages.

2. **LLM Rate Limits**: Qwen has daily limits. Mitigation: Cache intent results, fallback to command-based routing.

3. **Bot Token Exposure**: Never commit `.env.bot.secret`. Mitigation: Added to `.gitignore`, use example file.

## Success Criteria

- ✅ Bot responds to all commands in test mode
- ✅ Bot responds to all commands in Telegram
- ✅ Real data from backend displayed correctly
- ✅ Natural language queries work with LLM
- ✅ Bot runs continuously on VM with auto-restart
