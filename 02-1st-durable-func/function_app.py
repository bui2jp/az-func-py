import azure.functions as func
import azure.durable_functions as df
import logging

# app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# @app.route(route="http_trigger")
# def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
#     logging.info('Python HTTP trigger function processed a request.')

#     name = req.params.get('name')
#     if not name:
#         try:
#             req_body = req.get_json()
#         except ValueError:
#             pass
#         else:
#             name = req_body.get('name')

#     if name:
#         return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
#     else:
#         return func.HttpResponse(
#              "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
#              status_code=200
#         )

myApp = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# クライアント関数
# An HTTP-Triggered Function with a Durable Functions Client binding
@myApp.route(route="orchestrators/{functionName}")
@myApp.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    function_name = req.route_params.get('functionName')
    logging.info(f'start. {function_name}')
    # function_name は Orchestrator関数の名前
    instance_id = await client.start_new(function_name)
    response = client.create_check_status_response(req, instance_id)
    return response

# Orchestrator関数
@myApp.orchestration_trigger(context_name="context")
def hello_orchestrator(context):
    logging.info('start. hello_orchestrator')
    result1 = yield context.call_activity("hello", "Seattle")
    result2 = yield context.call_activity("hello", "Tokyo")
    result3 = yield context.call_activity("hello", "London")

    return [result1, result2, result3]

# Activity関数
@myApp.activity_trigger(input_name="city")
def hello(city: str):
    logging.info('start. hello')
    return f"Hello {city}"