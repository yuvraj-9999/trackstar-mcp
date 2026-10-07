from trackstar_mcp.repositories.mock_repository import MockRepository

class WareHouseService:
    def __init__(self):
        self.repository = MockRepository()

    def get_warehouses(self) -> list[dict]:
            return self.repository.get_warehouses()

    def get_warehouse(self, warehouse_id: str) -> dict | None:
        warehouse = self.repository.get_warehouse_by_id(warehouse_id)

        if warehouse is None:
            return None

        return warehouse

    def get_low_stock_inventory(self, warehouse_id: str) -> list[dict] | None:
        
        warehouse = self.get_warehouse(warehouse_id)

        if warehouse is None:
            return None
            
        inventory = self.repository.get_inventory_by_warehouse(warehouse_id)

        low_stock_items = []

        for item in inventory:
            fulfillable = item["fulfillable"]
            reorder_point = item["reorder_point"]

            if fulfillable < reorder_point:
                low_stock_items.append(item)

        return low_stock_items

    def get_pending_returns(self, warehouse_id: str) -> list[dict] | None:

        warehouse = self.get_warehouse(warehouse_id)

        if warehouse is None:
            return None


        returns = self.repository.get_returns_by_warehouse(warehouse_id)

        pending_statuses = {"open", "in-transit", "receiving"}

        pending_returns = []

        for return_item in returns:
            if return_item["status"] in pending_statuses:
                pending_returns.append(return_item)

        return pending_returns

        
    def investigate_warehouse(self, warehouse_id: str) -> dict | None:
        warehouse = self.get_warehouse(warehouse_id)

        if warehouse is None:
            return None

        low_stock_inventory = self.get_low_stock_inventory(warehouse_id)
        pending_returns = self.get_pending_returns(warehouse_id)

        return {
            "warehouse": warehouse,
            "low_stock_inventory": low_stock_inventory,
            "pending_returns": pending_returns,
        }

    def _get_inventory_severity(self, fulfillable: int, reorder_point: int) -> str:
        if fulfillable > reorder_point:
            return "healthy"

        if fulfillable == reorder_point:
            return "at_reorder_point"

        if fulfillable <= reorder_point * 0.25:
            return "critical"

        return "low"

    def _analyze_inventory_item(self, item: dict) -> dict:
        fulfillable = item["fulfillable"]
        reorder_point = item["reorder_point"]

        severity = self._get_inventory_severity(fulfillable, reorder_point)

        return {
            "inventory_id": item["id"],
            "sku": item["sku"],
            "name": item["name"],
            "severity": severity,
            "fulfillable": fulfillable,
            "reorder_point": reorder_point,
            "shortfall": max(reorder_point - fulfillable, 0),
        }

    def _analyze_warehouse_inventory(self, warehouse_id: str) -> list [dict] | None:
        warehouse = self.get_warehouse(warehouse_id)

        if warehouse == None:
            return None

        inventory = self.repository.get_inventory_by_warehouse(warehouse_id)

        return [
            self._analyze_inventory_item(item)
            for item in inventory
        ]


    def _get_return_receiving_details(self, return_item: dict) -> list[dict]:
        receiving_details = []

        for shipment in return_item.get("shipments", []):
            for line_item in shipment.get("line_items", []):
                receiving_details.extend(line_item.get("receiving_details", []))

        return receiving_details
    
    
    def _get_return_severity(self, return_item: dict) -> str:
        status = return_item["status"]

        receiving_details = self._get_return_receiving_details(return_item)

        for detail in receiving_details:
            condition = detail.get("condition")

            if condition == "damaged":
                return "high"

        if status == "receiving":
            return "high"

        if status == "in-transit":
            return "medium"

        if status == "open":
            return "medium"

        return "low"

    def _analyze_return(self, return_item: dict) -> dict:
        severity = self._get_return_severity(return_item)

        receiving_details = self._get_return_receiving_details(return_item)

        affected_inventory = [
            {
                "inventory_id": line_item["inventory_item_id"],
                "sku": line_item["sku"],
                "expected_quantity": line_item["expected_quantity"],
                "received_quantity": line_item["received_quantity"],
                "restocked_quantity": line_item["restocked_quantity"],
            }
            for line_item in return_item.get("line_items", [])
        ]

        return {
            "return_id": return_item["id"],
            "status": return_item["status"],
            "severity": severity,
            "order_id": return_item.get("order_id"),
            "affected_inventory": affected_inventory,
            "receiving_details": receiving_details,
        }

    def _analyze_warehouse_returns(self, warehouse_id: str) -> list[dict] | None:
        warehouse = self.get_warehouse(warehouse_id)

        if warehouse is None:
            return None
        
        returns = self.repository.get_returns_by_warehouse(warehouse_id)

        return [
            self._analyze_return(return_item)
            for return_item in returns
        ]

    def get_related_returns(self, inventory_id: str, return_analyses: list[dict]) -> list[dict]:

        return [
            return_analysis
            for return_analysis in return_analyses
            for line_item in return_analysis.get("affected_inventory", [])
            if line_item.get("inventory_id") == inventory_id
        ]

    def _analyze_inventory_return_relationship(self,inventory_analysis: dict,related_returns: list[dict],) -> list[dict]:
        findings = []

        for return_analysis in related_returns:
            status = return_analysis["status"]

            if status == "in-transit":
                findings.append(
                    {
                        "type": "inventory_return_relationship",
                        "relationship": "pending",
                        "severity": "high"
                        if inventory_analysis["severity"] == "critical"
                        else "medium",
                        "inventory_id": inventory_analysis["inventory_id"],
                        "sku": inventory_analysis["sku"],
                        "return_id": return_analysis["return_id"],
                        "reason": (
                        "The related return is still in transit "
                        "and cannot currently be counted as "
                        "available replenishment."
                        ),
                    }
                )

            elif status == "receiving":
                receiving_details = return_analysis["receiving_details"]

                damaged_quantity = sum(
                    detail.get("quantity", 0)
                    for detail in receiving_details
                    if detail.get("condition") == "damaged"
                )

                if damaged_quantity > 0:
                    findings.append(
                        {
                        "type": "inventory_return_relationship",
                        "relationship": "not_replenishing",
                        "severity": "high"
                        if inventory_analysis["severity"] == "critical"
                        else "medium",
                        "inventory_id": inventory_analysis["inventory_id"],
                        "sku": inventory_analysis["sku"],
                        "return_id": return_analysis["return_id"],
                        "reason": (
                            f"{damaged_quantity} returned unit(s) "
                            "were received in damaged condition and "
                            "should not currently be treated as "
                            "replenishment."
                        ),
                    }
                )

            elif status == "received":
                restocked_quantity = sum(
                    item.get("restocked_quantity", 0)
                    for item in return_analysis["affected_inventory"]
                )

                if restocked_quantity > 0:
                    findings.append(
                        {
                            "type": "inventory_return_relationship",
                            "relationship": "replenishing",
                            "severity": "low",
                            "inventory_id": inventory_analysis["inventory_id"],
                            "sku": inventory_analysis["sku"],
                            "return_id": return_analysis["return_id"],
                            "restocked_quantity": restocked_quantity,
                            "reason": (
                                f"{restocked_quantity} returned unit(s) "
                                "have been restocked and can contribute "
                                "to inventory replenishment."
                            ),
                        }
                    )

        return findings


    def analyze_warehouse(self, warehouse_id: str) -> dict | None:
        warehouse = self.get_warehouse(warehouse_id)

        if warehouse == None:
            return None

        inventory_analyses = self._analyze_warehouse_inventory(warehouse_id)

        return_analyses = self._analyze_warehouse_returns(warehouse_id)

        relationships = []

        for inventory_analysis in inventory_analyses:
            related_returns = self.get_related_returns(inventory_analysis["inventory_id"], return_analyses)

            relationship_findings = (self._analyze_inventory_return_relationship(inventory_analysis, related_returns))

            relationships.extend(relationship_findings)

        return {
            "warehouse": warehouse,
            "inventory_analysis": inventory_analyses,
            "return_analysis": return_analyses,
            "inventory_return_relationships": relationships,
        }
