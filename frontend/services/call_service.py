from services import api_client


def get_calls(skip=0, limit=50, customer_id=None, case_id=None):
    params = {"skip": skip, "limit": limit}
    if customer_id:
        params["customer_id"] = customer_id
    if case_id:
        params["case_id"] = case_id
    return api_client.get("/calls", params=params)


def get_call(call_id: str):
    return api_client.get(f"/calls/{call_id}")


def create_call(data: dict):
    return api_client.post("/calls", data)
