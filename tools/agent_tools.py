from tools.mongo_tools import MongoTools


class AgentTools:

    _tools = {
        "get_databases": MongoTools.get_databases,
        "get_collections": MongoTools.get_collections,
        "find_documents": MongoTools.find_documents,
        "count_documents": MongoTools.count_documents,
        "search_all": MongoTools.search_all,
    }

    @classmethod
    def execute_tool(cls, tool_name: str, params: dict):

        if tool_name not in cls._tools:
            return f"Tool '{tool_name}' not found. Available: {list(cls._tools.keys())}"

        try:
            return cls._tools[tool_name](**params)

        except TypeError as e:
            return f"Invalid parameters for '{tool_name}': {str(e)}"

        except Exception as e:
            return f"Tool execution failed: {str(e)}"