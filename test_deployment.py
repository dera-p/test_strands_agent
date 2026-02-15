import boto3
import uuid
import json

def invoke_agent(agent_id, agent_alias_id, prompt):
    client = boto3.client('bedrock-agent-runtime', region_name='ap-northeast-1')
    session_id = str(uuid.uuid4())
    
    print(f"Invoking Agent: {agent_id} (Alias: {agent_alias_id})")
    print(f"Prompt: {prompt}")
    print("-" * 30)

    try:
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=prompt
        )

        # Process the streaming response
        for event in response.get('completion'):
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    print(chunk['bytes'].decode('utf-8'), end='')
            elif 'trace' in event:
                # Traces can be verbose, uncomment to debug
                # print(json.dumps(event['trace'], indent=2))
                pass
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        if hasattr(e, 'response'):
            print(f"\nError Response: {json.dumps(e.response, default=str, indent=2)}")
        print(f"\nError invoking agent: {e}")

if __name__ == "__main__":
    AGENT_ID = "UJJ4UCM0LN" # Retrieved from previous step
    AGENT_ALIAS_ID = "TSTALIASID" # Draft alias
    PROMPT = "Create a 1-page slide explaining what AWS Bedrock is."
    
    invoke_agent(AGENT_ID, AGENT_ALIAS_ID, PROMPT)
