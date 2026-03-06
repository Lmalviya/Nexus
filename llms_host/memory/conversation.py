import redis
import json
import os
from typing import List, Dict, Any
from datetime import datetime

# Assuming llms_host is the package name based on directory structure
try:
    from llms_host.agents.summarizer import SummarizerAgent
except ImportError:
    # Fallback if running from a different context
    try:
        from llm_host.agents.summarizer import SummarizerAgent
    except ImportError:
        pass

class Conversation:
    def __init__(self, agent_name: str, session_id: str):
        self.agent_name = agent_name
        self.session_id = session_id
        self.key = f"conversation:{session_id}"
        
        # Redis connection
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        
        # Context window settings
        self.threshold = 30
        self.first_threshold = 5
        self.last_threshold = 10

    def load_history(self) -> List[Dict[str, Any]]:
        """
        Loads the full conversation history from Redis.
        Expects a JSON object with a 'messages' list (Backend format).
        """
        data = self.redis_client.get(self.key)
        if data:
            try:
                session = json.loads(data)
                return session.get("messages", [])
            except json.JSONDecodeError:
                print(f"Error decoding session data for {self.key}")
                return []
        return []

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
            try:
                summary_text = SummarizerAgent().summarize(to_summarize)
            except Exception as e:
                print(f"Summarization failed: {e}")
                summary_text = "[Summary generation failed]"
            
            context_messages.append({"role": "system", "content": f"Previous conversation summary: {summary_text}"})
            
            # Keep the last few messages for immediate context
            context_messages.extend(messages[-self.last_threshold:])
            
            return context_messages
        
        return messages

    def save_turn(self, user_message: str, assistant_message: str, metadata: Dict[str, Any] = None):
        """
        No-op: Backend handles persistence now.
        """
        pass

    def add_system_message(self, content: str):
        """
        Adds a system message if needed.
        """
        data = self.redis_client.get(self.key)
        if data:
            try:
                session = json.loads(data)
                msg_obj = {"role": "system", "content": content}
                session["messages"].append(msg_obj)
                self.redis_client.set(self.key, json.dumps(session))
            except Exception as e:
                print(f"Error adding system message: {e}")

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
        log_key = f"agent_logs:{self.agent_name}:{self.session_id}"
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "messages": messages
        }
        self.redis_client.rpush(log_key, json.dumps(log_entry))