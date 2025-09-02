from sanic import Blueprint, Request, json

search_api = Blueprint("search_api", url_prefix="/api")

@search_api.post("/sort_list")
async def sort_list(request: Request):
    """
    期待收到 JSON:
    {
      "data": [3, "b", 2, "a", 1]
    }
    回傳：
    {
      "data": [1, 2, 3, "a", "b"]
    }
    """
    payload = request.json or {}
    data = payload.get("data")

    if not isinstance(data, list):
        return json({"error": "`data` 必須是 list"}, status=400)

    nums = [x for x in data if isinstance(x, (int, float))]
    strs = [x for x in data if isinstance(x, str)]
    nums.sort()
    strs.sort()

    return json({"data": nums + strs})
