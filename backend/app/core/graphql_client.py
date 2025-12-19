from __future__ import annotations

import httpx

INTROSPECTION_QUERY = {
    "query": """
    query PrediQLIntrospection {
      __schema {
        types { kind name }
        queryType { name }
        mutationType { name }
      }
    }
    """,
    "variables": {},
}


class GraphQLClient:
    def __init__(self, endpoint: str, headers: dict[str, str] | None = None) -> None:
        self.endpoint = endpoint
        self.headers = headers or {}

    async def fetch_introspection(self) -> dict | None:
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                resp = await client.post(self.endpoint, json=INTROSPECTION_QUERY, headers=self.headers)
                resp.raise_for_status()
                return resp.json()
            except Exception:
                return None

    async def execute_query(self, query: str, variables: dict | None = None) -> dict | None:
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                resp = await client.post(self.endpoint, json={"query": query, "variables": variables or {}}, headers=self.headers)
                resp.raise_for_status()
                return resp.json()
            except Exception:
                return None
