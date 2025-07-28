from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

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

# Tool registry
TOOLS = {
    "add": add_tool,
    "reverse": reverse_tool,
    "multiply": multiply_tool
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
    }
]

@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """MCP protocol endpoint"""
    logger.info(f"📨 MCP Request: {request.model_dump()}")
    
    try:
        # Handle notifications (no id field)
        if request.id is None and request.method:
            logger.info(f"🔔 Notification: {request.method}")
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
            logger.info("🤝 Initialize")
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
            logger.info("📋 List tools")
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
            
            logger.info(f"🔧 Call tool: {tool_name} with {tool_args}")
            
            if tool_name not in TOOLS:
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {"code": MCP_ERRORS["METHOD_NOT_FOUND"], "message": f"Unknown tool: {tool_name}"}
                }
            
            try:
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
        logger.error(f"💥 Server error: {e}")
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