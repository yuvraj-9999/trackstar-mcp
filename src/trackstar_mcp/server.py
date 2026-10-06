from mcp.server import MCPServer

from trackstar_mcp.services.warehouse_service import WareHouseService

mcp = MCPServer("Trackstar Warehouse Operations")

warehouse_service = WareHouseService()

@mcp.tool()
def list_warehouses() -> list[dict]:
    """List all warehouses avialable for operational investigation"""
    return warehouse_service.get_warehouses()

