from sanic import Sanic, Blueprint, Request, json as sanic_json, exceptions
from sanic_ext import validate
# 
from pydantic import BaseModel
from typing import List
# 
import json

# 這邊的 "Backend" 可以任意更改 
# 不要在同一個專案內跟其他 Sanic 物件使用一樣的 name 就好
app = Sanic("Backend")
# 
global DATA
global COUNTRIES
global PERSONS
with open('./data.json', 'r') as file:
    DATA = json.load(file)
    COUNTRIES:list = DATA.get("countries", [])
    PERSONS:list = DATA.get("persons", [])


class GetItem(BaseModel):
    index: int

# 寫法不一樣 功能一樣
# @app.get("/get_item")
@app.route("/get_item", methods=["GET"])
@validate(query=GetItem) # 使用 GET 時建議用 query 
async def get_item(request: Request, query: GetItem):
    _index = query.index
    if _index is None:
        raise exceptions.NotFound("沒有給定 index.")
    
    _index = int(_index)
    country, person = None, None
    
    # 確認 index 區間範圍
    if 0 <= _index and _index < len(COUNTRIES):
        country = COUNTRIES[_index]
    
    if 0 <= _index and _index < len(PERSONS):
        person = PERSONS[_index] 

    return sanic_json({"country": country, "person": person})

# 
# 
class AddItem(BaseModel):
    new_persons: List[str]
    new_countries: List[str]


@app.route("/add_item", methods=["POST"])
@validate(json=AddItem) #因為是用 json format 傳入資料 所以這邊要用 json
async def add_item(request: Request, body: AddItem):
    
    new_persons = body.new_persons 
    new_countries = body.new_countries

    # print("======================")
    # print(new_persons)
    # print(new_countries)
    # print("======================")

    duplicates = []
    for person in new_persons:
        if person in PERSONS:
            # PERSONS 裡面已經存在 重複的 value 了
            duplicates.append(person)
        else:
            # PERSONS 裡面沒有這個 value 所以 append 到 PERSONS
            PERSONS.append(person)
    
    # 概念如上
    for country in new_countries:
        if country in COUNTRIES:
            duplicates.append(country)
        else:
            COUNTRIES.append(country)

    return sanic_json({"duplicate": duplicates})

# 
# 
class DeleteItem(BaseModel):
    delete_target: List[str]

@app.route("/delete_item", methods=["DELETE"])
@validate(json=DeleteItem)
async def delete_item(request: Request, body: DeleteItem):
    delete_target = body.delete_target

    # print(delete_target)
    # print(PERSONS)
    # print(COUNTRIES)

    duplicate_flag = False
    
    for item in delete_target:
        # print(item)
        if item in PERSONS:
            # PERSONS 裡面有 item 所以刪除
            PERSONS.remove(item)
            duplicate_flag = True
        elif item in COUNTRIES:
            COUNTRIES.remove(item)
            duplicate_flag = True

    return sanic_json({
        "delete_result": duplicate_flag
    })


if __name__  == "__main__":
    '''
    host := 允許一些 ip 位置的裝置可以連到這個後端, 常見的有 localhost, 127.0.0.1, 0.0.0.0
            其中 localhost 跟 127.0.0.1 都是指自己, 0.0.0.0 是不限制
    port := 要使用那一個 port 來溝通 範圍 0~65535
    '''
    app.run(host='127.0.0.1', port=2020, auto_reload=True, debug=True)