from mcp.server import MCPServer

from trackstar_mcp.services.warehouse_service import WareHouseService

mcp = MCPServer("Trackstar Warehouse Operations")

warehouse_service = WareHouseService()

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