from typing import Any

from app.langgraph_agent.schemas import ProductInformationArguments
from app.langgraph_agent.tools.context import ToolContext


async def product_information(context: ToolContext, arguments: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Search internal product records and return structured product information."""

    query = arguments.get("query") or arguments.get("product")

    if not query:
        # Fall back to the user's message, but clean it up.
        query = user_message

    query = (
        query.replace("Tell me about", "")
            .replace("tell me about", "")
            .replace("Show me", "")
            .replace("show me", "")
            .replace("information on", "")
            .strip(" .?!")
    )

    parsed = ProductInformationArguments(
        query=query,
        limit=arguments.get("limit", 8),
    )
    products = context.repository.search_products(parsed.query, parsed.limit)
    return {
        "products": [
            {
                "product": product.name,
                "benefits": product.benefits,
                "dosage": product.dosage,
                "side_effects": product.side_effects,
                "clinical_notes": product.clinical_notes,
            }
            for product in products
        ]
    }
