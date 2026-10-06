from trackstar_mcp.repositories.mock_repository import MockRepository

class WareHouseService:
    def __init__(self):
        self.repository = MockRepository()

        def get_warehouses(self):
            return self.repository.get_warehouses()

        def get_warehouse(self, warehouse_id: str):
            warehouse = self.repository.get_warehouse_by_id(warehouse_id)

            if warehouse is None:
                return None

            return warehouse

        def get_low_stock_inventory(self, warehouse_id: str):
            inventory = self.repository.get_inventory_by_warehouse(warehouse_id)

            low_stock_items = []

            for item in inventory:
                fulfillable = item["quantities"]["fulfillable"]
                reorder_point = item["reorder_point"]

                if fulfillable < reorder_point:
                    low_stock_items.append(item)

            return low_stock_items

        def get_pending_returns(self, warehouse_id: str):
            returns = self.repository.get_returns_by_warehouse(warehouse_id)

            pending_statuses = {"open", "in-transit", "receiving"}

            pending_returns = []

            for return_item in returns:
                if return_item["status"] in pending_statuses:
                    pending_returns.append(return_item)

            return pending_returns

