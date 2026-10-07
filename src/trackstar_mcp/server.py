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
   - inventory.onhand represents the total quantity physically on hand.
   - inventory.committed represents inventory assigned to orders.
   - inventory.unfulfillable represents inventory that cannot currently
     be fulfilled.
   - inventory.fulfillable represents inventory currently available
     to fulfill orders.
   - inventory.sellable represents inventory available to sales channels.
   - inventory.awaiting represents inventory expected to arrive.
   - Low stock is determined using the prototype's reorder point:
     fulfillable < reorder_point

3. Returns
   - Represents a customer return associated with a warehouse.
   - return.warehouse_id references warehouse.id
   - return.line_items[] contains the inventory items associated
     with the return.
   - return.line_items[].inventory_item_id references inventory.id.
   - return.line_items[].sku identifies the associated product.
   - return.shipments[] represents shipment information associated
     with the return.
   - return.shipments[].line_items[] identifies the inventory items
     included in the shipment.
   - receiving_details[] contains information recorded when returned
     inventory is received, including quantity, condition, and
     disposition.
   - Pending returns currently have one of these statuses:
     open, in-transit, or receiving.

Relationships:

Warehouse
    ├── Inventory
    │     └── inventory.warehouse_id → warehouse.id
    │
    └── Returns
          ├── return.warehouse_id → warehouse.id
          └── return.line_items[].inventory_item_id → inventory.id
          │
          └── return.shipments[]
                └── shipment.line_items[].inventory_item_id
                    → inventory.id

The reorder_point and target_stock_level fields are prototype
operational-analysis fields used by this MCP. They are not treated
as Trackstar API fields.

This resource describes the normalized operational data model.
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
def analyze_warehouse(warehouse_id: str,) -> dict | None:
    """
    Analyze the operational state of a specific warehouse.

    Args:
        warehouse_id: The unique ID of the warehouse to analyze.

    Returns:
        A structured operational analysis containing warehouse
        information, inventory analysis, return analysis,
        inventory-return relationships, and operational findings.

        Returns null if the specified warehouse does not exist.

    Notes:
        This tool only reads operational data and does not modify
        any records.
    """
    return warehouse_service.analyze_warehouse(warehouse_id)

@mcp.prompt(
    name="warehouse_operations_review",
    description=(
        "Review a warehouse's operational state and identify "
        "issues that require human attention."
    ),
)
def warehouse_operations_review(warehouse_id: str) -> str:
    return f"""
Review the operational state of warehouse '{warehouse_id}'.

Use the warehouse analysis to identify the most important
operational findings.

Pay particular attention to:
- inventory below reorder points
- critically low inventory
- returns that are still pending and cannot currently contribute
  to replenishment
- returns received in damaged condition
- returns that have been successfully restocked and can contribute
  to replenishment
- relationships between inventory conditions and related returns

For each important issue:
- explain what is happening
- explain why it matters
- use the available evidence from the analysis

Prioritize findings by operational significance rather than
simply listing every record.

Do not assume that any recommended action has been approved.
Keep the human operator in the decision loop.
"""