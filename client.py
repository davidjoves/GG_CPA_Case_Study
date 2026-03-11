"""
MCP Client for Tax AI Agent

This client connects to the Tax AI Agent using STDIO and executes tasks such as generating code and testing functionality.
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI