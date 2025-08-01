from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union
import logging
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

AIARCHIVE_SERVER_BASE_URL = "http://10.0.1.157:3000"

# MCP error codes
MCP_ERRORS = {
    "PARSE_ERROR": -32700,
    "INVALID_REQUEST": -32600,
    "METHOD_NOT_FOUND": -32601,
    "INVALID_PARAMS": -32602,
    "INTERNAL_ERROR": -32603,
}

# Request model
class MCPRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None

# Tool implementations
def add_tool(args: Dict[str, Any]) -> str:
    if "a" not in args or "b" not in args:
        raise ValueError("Missing parameters: a and b")
    if not isinstance(args["a"], (int, float)) or not isinstance(args["b"], (int, float)):
        raise ValueError("Parameters a and b must be numbers")
    return f"Result: {args['a'] + args['b']}"

def reverse_tool(args: Dict[str, Any]) -> str:
    if "text" not in args:
        raise ValueError("Missing parameter: text")
    if not isinstance(args["text"], str):
        raise ValueError("Parameter text must be a string")
    return f"Result: {args['text'][::-1]}"

def multiply_tool(args: Dict[str, Any]) -> str:
    if "a" not in args or "b" not in args:
        raise ValueError("Missing parameters: a and b")
    if not isinstance(args["a"], (int, float)) or not isinstance(args["b"], (int, float)):
        raise ValueError("Parameters a and b must be numbers")
    return f"Result: {args['a'] * args['b']}"

async def save_conversation_tool(args: Dict[str, Any]) -> str:
    if "conversation" not in args:
        raise ValueError("Missing required parameter: conversation")
    
    conversation_content = args["conversation"]
    
    if not isinstance(conversation_content, str):
        raise ValueError("Parameter conversation must be a string")
    
    try:
        async with httpx.AsyncClient() as client:
            # Create multipart form data
            files = {
            'htmlDoc': ('conversation.txt', conversation_content.encode('utf-8'), 'text/plain')
            }
            data = {
                'model': 'Claude (MCP)',
                'skipScraping': ''
            }
            
            # Make request to existing API endpoint
            response = await client.post(
                f"{AIARCHIVE_SERVER_BASE_URL}/api/conversation",
                files=files,
                data=data,
                timeout=30.0
            )
            
            if response.status_code == 201:
                result = response.json()
                return f"Conversation saved successfully! View it at: {result.get('url', 'N/A')}"
            else:
                error_msg = response.text
                raise ValueError(f"API request failed: {response.status_code} - {error_msg}")
                
    except httpx.RequestError as e:
        raise ValueError(f"Failed to connect to scraper server: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error saving conversation: {str(e)}")


# Tool registry
TOOLS = {
    "add": add_tool,
    "reverse": reverse_tool,
    "multiply": multiply_tool,
    "save_conversation": save_conversation_tool
}

# Tool schemas
TOOL_SCHEMAS = [
    {
        "name": "add",
        "description": "Add two numbers together",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "reverse",
        "description": "Reverse a string",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to reverse"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "multiply",
        "description": "Multiply two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    
    {
        "name": "save_conversation",
        "description": "Archive and save your conversation permanently. When called, you MUST include the complete conversation history with ALL human messages AND all assistant responses from the beginning of the conversation. Provide the full conversation content as HTML or plain text in the conversation parameter. Use this after completing a conversation to create a permanent, shareable link. on aiarchives.duckdns.org.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation": {
                    "type": "string", 
                    "description": "The full conversation to save"
                }
            },
            "required": ["conversation"]
        }
    }
]

@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """MCP protocol endpoint"""
    logger.info(f"MCP Request: {request.model_dump()}")
    
    try:
        # Handle notifications (no id field)
        if request.id is None and request.method:
            logger.info(f"Notification: {request.method}")
            return Response(status_code=204)
        
        # Validate JSON-RPC format
        if request.jsonrpc != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": MCP_ERRORS["INVALID_REQUEST"], "message": "Invalid jsonrpc"}
            }
        
        # Handle method calls
        if request.method == "initialize":
            logger.info("Initialize")
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "Python MCP Server", "version": "1.0.0"}
                }
            }
        
        elif request.method == "tools/list":
            logger.info("List tools")
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {"tools": TOOL_SCHEMAS}
            }
        
        elif request.method == "tools/call":
            if not request.params or "name" not in request.params or "arguments" not in request.params:
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {"code": MCP_ERRORS["INVALID_PARAMS"], "message": "Missing name/arguments"}
                }
            
            tool_name = request.params["name"]
            tool_args = request.params["arguments"]
            
            logger.info(f"Call tool: {tool_name} with {tool_args}")
            
            if tool_name not in TOOLS:
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {"code": MCP_ERRORS["METHOD_NOT_FOUND"], "message": f"Unknown tool: {tool_name}"}
                }
            
            try:
                # Handle async tools
                if tool_name == "save_conversation":
                    result = await TOOLS[tool_name](tool_args)
                else:
                    result = TOOLS[tool_name](tool_args)
                    
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "result": {"content": [{"type": "text", "text": result}]}
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {"code": MCP_ERRORS["INVALID_PARAMS"], "message": str(e)}
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": MCP_ERRORS["METHOD_NOT_FOUND"], "message": f"Method not found: {request.method}"}
            }
            
    except Exception as e:
        logger.error(f"Server error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"code": MCP_ERRORS["INTERNAL_ERROR"], "message": str(e)}
        }

@app.get("/health")
async def health():
    return {"status": "healthy", "server": "Python MCP Server"}

@app.get("/mcp")
async def mcp_info():
    return {
        "message": "MCP Server running",
        "tools": [{"name": tool["name"], "description": tool["description"]} for tool in TOOL_SCHEMAS]
    }