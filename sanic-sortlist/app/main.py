from sanic import Sanic
from sanic.response import text

app = Sanic("MyHelloWorldApp")

@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
@app.get("/sort")
async def sort_list(request):
    numbers = request.args.getlist("number", type=int)
    sorted_numbers = sorted(numbers)
    return text(f"Sorted numbers: {sorted_numbers}")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)