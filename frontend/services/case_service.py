from services import api_client


def get_cases(skip=0, limit=50, customer_id=None, status=None):
    params = {"skip": skip, "limit": limit}
    if customer_id:
        params["customer_id"] = customer_id
    if status:
        params["status"] = status
    return api_client.get("/cases", params=params)


def get_case(case_id: str):
    return api_client.get(f"/cases/{case_id}")


def create_case(data: dict):
    return api_client.post("/cases", data)


def update_case(case_id: str, data: dict):
    return api_client.patch(f"/cases/{case_id}", data)


def delete_case(case_id: str):
    return api_client.delete(f"/cases/{case_id}")
