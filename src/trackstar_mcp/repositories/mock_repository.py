import json
from pathlib import Path

class MockRepository:
    def __init__(self):
        self.data_dir = Path(__file__).resolve().parents[3]/"data"

        self.warehouses = self._load_data("warehouse.json")
        self.inventory = self._load_data("inventory.json")
        self.returns = self._load_data("returns.json")

        def _load_data(self, filename: str) -> list[dict]: 
            file_path = self.data_dir / filename

            with file_path.open("r", encoding="utf-8") as file:
                return json.load(file)

        def get_warehouses(self) -> list[dict]:
            return self.warehouses

        def get_inventory(self) -> list[dict]:
            return self.inventory

        def get_returns(self) -> list[dict]:
            return self.get_returns

        def get_warehouse_by_id(self,warehouse_id: str) -> dict | None:
            return next(
                (
                    warehouse
                    for warehouse in self.warehouses
                    if warehouse["id"] == warehouse_id
                ),
                None,
            )

        def get_inventory_by_warehouse(self,warehouse_id:str) -> list[dict]:
            return [
                item 
                for item in self.inventory
                if item["warehouse_id"] == warehouse_id
            ]

        def get_returns_by_warehouse(self, warehouse_id: str) -> list[dict]:
            return [
                return_item 
                for return_item in self.returns
                if return_item["warehouse_id"] == warehouse_id
            ]