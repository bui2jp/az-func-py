import azure.functions as func
import datetime
import json
import logging

app = func.FunctionApp()

@app.route(route="HttpExample", auth_level=func.AuthLevel.ANONYMOUS)
def HttpExample(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"これは楽の湯からです。, {name}. そろそろ帰るかな。")
    else:
        return func.HttpResponse(
             "これは楽の湯から、そろそろ帰るかな。このメッセージをみれたら教えて",
             status_code=200
        )

@app.route(route="HttpExample2", auth_level=func.AuthLevel.ANONYMOUS)
def HttpExample2(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"hi, {name}. this is test.(Example2)")
    else:
        return func.HttpResponse(
             "これは楽の湯から、そろそろ帰るかな。このメッセージをみれたら教えて",
             status_code=200
        )