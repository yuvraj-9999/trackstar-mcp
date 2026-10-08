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
           - Low stock in this prototype is determined using the
             prototype-defined reorder point:
             fulfillable < reorder_point

           - The reorder_point field is a prototype operational-analysis
             field and is not treated as a Trackstar API field.

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
                   └── return.shipments[]
                           └── shipment.line_items[].inventory_item_id
                                → inventory.id

           The inventory-return relationship is used by this MCP to determine
           how related returns affect an inventory situation.

           Related returns may be classified as:
           - replenishing: returned units have been restocked and can contribute
             to inventory replenishment.
           - pending: the return cannot currently be counted as replenishment,
             such as when it is still in transit.
           - not_replenishing: returned units should not currently be counted
             as replenishment, such as units received in damaged condition.

           The reorder_point and target_stock_level fields are prototype
           operational-analysis fields used by this MCP. They are not treated
           as Trackstar API fields.

           This resource describes the normalized operational data model.
           Operational records should be retrieved through the available tools.
           """

@mcp.tool()
def list_warehouses() -> list[dict]:
    """
    List all warehouses available for operational investigation.

    Use this tool when the user wants to discover which warehouses
    are available before selecting a specific warehouse to inspect.

    Returns:
        A list of warehouse records containing their identifiers
        and available warehouse information.

    Notes:
        This tool only lists warehouses. It does not analyze
        inventory, returns, or operational issues.
        This tool is read-only and does not modify any records.
    """
    return warehouse_service.get_warehouses()

@mcp.tool()
def get_warehouse(warehouse_id: str) -> dict | None:
    """
    Get detailed information about a specific warehouse.

    Use this tool when the user wants information about a
    warehouse itself, such as its identity, location, contact
    information, capabilities, timezone, or operational status.

    Args:
        warehouse_id: The unique ID of the warehouse to retrieve.

    Returns:
        The warehouse record if the specified warehouse exists.
        Returns null if no warehouse matches the provided ID.

    Notes:
        This tool retrieves warehouse metadata only. It does not
        analyze inventory levels, returns, or operational issues.

        This tool is read-only and does not modify any records.
    """
    return warehouse_service.get_warehouse(warehouse_id)

@mcp.tool()
def find_low_stock_inventory(warehouse_id: str) -> list[dict] | None:
    """
    Find inventory items in a specific warehouse that are below
    their reorder point.

    Use this tool when the user specifically wants to identify
    low-stock inventory rather than perform a broader warehouse
    investigation.

    Args:
        warehouse_id: The unique ID of the warehouse to investigate.

    Returns:
        A list of inventory records whose fulfillable quantity
        is below their reorder point.

        Returns null if the specified warehouse does not exist.

    Notes:
        Low stock is determined by:

        fulfillable < reorder_point

        The reorder point is a prototype operational-analysis
        field used by this MCP and is not treated as a Trackstar
        API field.

        This tool only evaluates inventory levels. It does not
        analyze related returns or determine whether returns can
        contribute to replenishment.

        This tool is read-only and does not modify any records.
    """
    return warehouse_service.get_low_stock_inventory(warehouse_id)

@mcp.tool()
def get_pending_returns(warehouse_id: str) -> list[dict] | None:
    """
    Find returns that are currently pending for a specific warehouse.

    Use this tool when the user specifically wants to inspect
    pending returns rather than perform a broader warehouse
    investigation.

    Args:
        warehouse_id: The unique ID of the warehouse to investigate.

    Returns:
        A list of pending return records.

        Returns null if the specified warehouse does not exist.

    Notes:
        Pending returns currently include returns with these
        statuses:

        - open
        - in-transit
        - receiving

        This tool reports pending returns but does not determine
        whether a return can contribute to inventory replenishment.
        Use analyze_warehouse for relationships between returns
        and inventory.

        This tool is read-only and does not modify any records.
    """

    return warehouse_service.get_pending_returns(warehouse_id)

@mcp.tool()
def analyze_warehouse(warehouse_id: str,) -> dict | None:
    """
    Analyze a warehouse's operational state and identify
    findings that may require human attention.

    Use this tool when the user wants an overall operational
    assessment of a warehouse rather than a single type of record.

    The analysis considers:
    - inventory levels relative to reorder points
    - inventory severity
    - pending and completed returns
    - relationships between inventory items and related returns
    - whether related returns are replenishing, pending, or
      not currently contributing to replenishment

    Args:
        warehouse_id: The unique ID of the warehouse to analyze.

    Returns:
        A structured operational analysis containing:
        - warehouse information
        - inventory analysis
        - return analysis
        - inventory-return relationships
        - operational findings

        Returns null if the specified warehouse does not exist.

    Notes:
        This tool is read-only and does not modify inventory,
        returns, warehouse records, or other operational data.

        Findings are based only on the data available through
        the MCP. The tool does not assume that an operational
        action has been approved or performed.
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

            Use the available warehouse analysis to identify the most
            important operational findings.

            Pay particular attention to:
            - inventory below reorder points
            - critically low inventory
            - returns that are still pending and cannot currently
              contribute to replenishment
            - returns received in damaged condition
            - returns that have been successfully restocked and can
              contribute to replenishment
            - relationships between inventory conditions and related returns

            For each important finding:
            - explain what is happening
            - explain why it matters
            - support the explanation using the available evidence

            Prioritize findings by operational significance rather than
            simply listing every record.

            Only make conclusions supported by the available warehouse data.
            Do not assume that an action has been approved, performed, or
            is possible unless the available data establishes it.

            Keep the human operator in the decision loop.
    """

if __name__ == "__main__":
    mcp.run()