# Redis Conversation Storage

This directory contains configuration for Redis, which is used to store user conversation history.

## Data Structure

Conversations are stored with the following key pattern:
```
conversation:{org_id}:{user_id}:{session_id}
```

Each conversation contains:
- Session metadata (user, org, title)
- Message history with token tracking
- Cumulative token usage statistics

## Session Management

User sessions are tracked with:
```
sessions:{org_id}:{user_id}
```

This stores a list of all session IDs for a user.
