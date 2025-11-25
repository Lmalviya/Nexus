import traceback
from retrival.get_context import get_context

def run_test():
    user_query = "What are the top selling products last month?"
    user_id = "test_user"
    conversation_id = "conv_123"
    try:
        context = get_context(user_query, user_id, conversation_id)
        print("\n=== Retrieval Result ===")
        for i, item in enumerate(context, 1):
            print(f"{i}: {item}\n")
    except Exception as e:
        print("Error during retrieval pipeline:")
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
