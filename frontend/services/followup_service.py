from services import api_client


def get_followups(skip=0, limit=50, case_id=None, customer_id=None, status=None):
    params = {"skip": skip, "limit": limit}
    if case_id:
        params["case_id"] = case_id
    if customer_id:
        params["customer_id"] = customer_id
    if status:
        params["status"] = status
    return api_client.get("/followups", params=params)


def get_followup(followup_id: str):
    return api_client.get(f"/followups/{followup_id}")


def create_followup(data: dict):
    return api_client.post("/followups", data)


def update_followup(followup_id: str, data: dict):
    return api_client.patch(f"/followups/{followup_id}", data)
