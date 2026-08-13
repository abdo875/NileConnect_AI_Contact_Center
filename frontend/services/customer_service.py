from services import api_client


def get_customers(skip=0, limit=50, search=None):
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    return api_client.get("/customers", params=params)


def get_customer(customer_id: str):
    return api_client.get(f"/customers/{customer_id}")


def create_customer(data: dict):
    return api_client.post("/customers", data)


def update_customer(customer_id: str, data: dict):
    return api_client.patch(f"/customers/{customer_id}", data)


def delete_customer(customer_id: str):
    return api_client.delete(f"/customers/{customer_id}")
