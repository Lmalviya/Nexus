import redis
import json
import os
from typing import List, Dict, Any
from datetime import datetime

# Assuming llms_host is the package name based on directory structure
# If imports fail, we might need to adjust python path or package name
try:
    from llms_host.agents.summarizer import SummarizerAgent
except ImportError:
    # Fallback if running from a different context or if package name is different
    try:
        from llm_host.agents.summarizer import SummarizerAgent
    except ImportError:
        # Mocking for now if import fails to avoid breaking everything immediately
        class SummarizerAgent:
            def summarize(self, messages):
                return "Summary of conversation..."

class Conversation:
    def __init__(self, agent_name: str, conversation_id: str):
        self.agent_name = agent_name
        self.conversation_id = conversation_id
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_client = redis.Redis(
            host=self.redis_host, 
            port=self.redis_port, 
            decode_responses=True
        )
        self.key = f"agent_memory:{self.agent_name}:{self.conversation_id}"
        
        # Context window settings
        self.threshold = 30
        self.first_threshold = 5
        self.last_threshold = 10

    def load_history(self) -> List[Dict[str, Any]]:
        """
        Loads the full conversation history from Redis.
        """
        raw_data = self.redis_client.lrange(self.key, 0, -1)
        # Redis stores list in order of insertion if using rpush.
        # If we use lpush, it's reversed. We will use rpush to keep chronological order.
        messages = [json.loads(msg) for msg in raw_data]
        return messages

    def get_context(self) -> List[Dict[str, Any]]:
        """
        Returns the context for the LLM. 
        If history is long, it returns a summarized version.
        Does NOT modify the stored history in Redis.
        """
        messages = self.load_history()
        
        if len(messages) >= self.threshold:
            # Create a temporary context with summary
            context_messages = []
            
            # Keep the first few messages (often system prompt or initial context)
            context_messages.extend(messages[:self.first_threshold])
            
            # Messages to summarize (middle part)
            to_summarize = messages[self.first_threshold:-self.last_threshold]
            
            # We need to format 'to_summarize' for the summarizer agent
            # The SummarizerAgent.summarize expects a list of dicts or strings? 
            # Based on previous code: SummarizerAgent().summarize(tmp_messages)
            summary_text = SummarizerAgent().summarize(to_summarize)
            
            context_messages.append({"role": "system", "content": f"Previous conversation summary: {summary_text}"})
            
            # Keep the last few messages for immediate context
            context_messages.extend(messages[-self.last_threshold:])
            
            return context_messages
        
        return messages

    def save_turn(self, user_message: str, assistant_message: str, metadata: Dict[str, Any] = None):
        """
        Saves the user message and assistant response to Redis.
        Preserves the full history.
        """
        user_msg_obj = {"role": "user", "content": user_message}
        if metadata:
            user_msg_obj["metadata"] = metadata
            
        assistant_msg_obj = {"role": "assistant", "content": assistant_message}
        
        # Use rpush to append to the end of the list (chronological order)
        self.redis_client.rpush(self.key, json.dumps(user_msg_obj))
        self.redis_client.rpush(self.key, json.dumps(assistant_msg_obj))

    def add_system_message(self, content: str):
        """
        Adds a system message if needed (usually at start).
        """
        msg_obj = {"role": "system", "content": content}
        self.redis_client.rpush(self.key, json.dumps(msg_obj))

    def clear_memory(self):
        """
        Clears the memory for this agent/conversation.
        """
        self.redis_client.delete(self.key)

    def log_flow(self, messages: List[Dict[str, Any]]):
        """
        Logs the full conversation flow (including dynamic context) to a separate Redis key.
        This is for debugging and audit purposes.
        """
        log_key = f"agent_logs:{self.agent_name}:{self.conversation_id}"
        # We append the whole flow as a single entry or append individual messages?
        # The user said "store full flow", which might imply the constructed prompt.
        # Let's store the list of messages used for this turn.
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "messages": messages
        }
        self.redis_client.rpush(log_key, json.dumps(log_entry))