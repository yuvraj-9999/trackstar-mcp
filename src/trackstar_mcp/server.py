from mcp.server import MCPServer

from trackstar_mcp.services.warehouse_service import WareHouseService

mcp = MCPServer("Trackstar Warehouse Operations")

warehouse_service = WareHouseService()

@mcp.resource("trackstar://warehouse-model")
def warehouse_model() -> str:
    return """
Trackstar Warehouse Operations Data Model

The operational model contains three primary entities:

1. Warehouse
   - Represents a physical warehouse or distribution facility.
   - Primary identifier: warehouse.id

2. Inventory
   - Represents a product's inventory state within a warehouse.
   - inventory.warehouse_id references warehouse.id
   - inventory.id uniquely identifies the inventory record.
   - inventory.sku identifies the product.
   - quantities.fulfillable represents inventory currently available
     to fulfill orders.
   - Low stock is determined when:
     fulfillable < reorder_point

3. Returns
   - Represents a customer return associated with a warehouse.
   - return.warehouse_id references warehouse.id
   - return.items[].inventory_id references inventory.id
   - return.items[].sku identifies the associated product.
   - Pending returns have one of these statuses:
     open, in-transit, receiving.

Relationships:

Warehouse
    ├── Inventory
    │     └── inventory.warehouse_id → warehouse.id
    │
    └── Returns
          ├── return.warehouse_id → warehouse.id
          └── return.items[].inventory_id → inventory.id

This resource describes the normalized data model only.
Operational records should be retrieved through the available tools.
"""


@mcp.tool()
def list_warehouses() -> list[dict]:
    """List all warehouses avialable for operational investigation"""
    return warehouse_service.get_warehouses()

@mcp.tool()
def get_warehouse(warehouse_id: str) -> dict | None:
    """Get detailed information about a specific warehouse by its ID"""
    return warehouse_service.get_warehouse(warehouse_id)

@mcp.tool()
def find_low_stock_inventory(warehouse_id: str) -> list[dict] | None:
    """
    Find inventory items in a specific warehouse that are below
    their reorder point.

    Args:
        warehouse_id: The unique ID of the warehouse to investigate.

    Returns:
         A list of inventory records that are below their reorder point.
        Returns null if the warehouse ID does not exist.

    Notes:
        Low stock is determined by comparing the item's fulfillable
        quantity with its reorder point:

        fulfillable < reorder_point

        This tool only reads inventory data and does not modify
        any records.
    """
    return warehouse_service.get_low_stock_inventory(warehouse_id)

@mcp.tool()
def get_pending_returns(warehouse_id: str) -> list[dict] | None:
    """
     Find pending returns for a specific warehouse.

    Args:
        warehouse_id: The unique ID of the warehouse to investigate.

    Returns:
        A list of pending return records.
        Returns null if the specified warehouse does not exist.

    Notes:
        Pending returns have one of these statuses:
        open, in-transit, or receiving.

        This tool only reads return data and does not modify
        any records.

    """

    return warehouse_service.get_pending_returns(warehouse_id)

@mcp.tool()
def investigate_warehouse(warehouse_id: str) -> dict | None:
    """
    Perform a comprehensive operational investigation of a warehouse.

    Args:
        warehouse_id: The unique ID of the warehouse to investigate.

    Returns:
        A dictionary containing three keys:
        - warehouse: Full warehouse record
        - low_stock_inventory: Items below reorder point
        - pending_returns: Pending returns for the warehouse
        Returns null if the warehouse ID does not exist.

    Notes:
        This tool combines the functionality of:
        • get_warehouse
        • get_low_stock_inventory
        • get_pending_returns

        It provides a complete operational snapshot in a single call.

    """
    return warehouse_service.investigate_warehouse(warehouse_id)

@mcp.prompt(
    name= "warehouse_operations_review",
    description="Review a warehouse's operational state and identify issues that require human attention."
)
def warehouse_operations_review(warehouse_id: str) -> str:
    return f"""

    Review the operational state of warehouse '{warehouse_id}'.

    Focus on:
    - inventory below reorder points
    - pending returns
    - relationships between inventory issues and returns
    - issues that may require human attention

    Prioritize findings by operational significance.
    Do not assume that any recommended action has been approved.
    
    """