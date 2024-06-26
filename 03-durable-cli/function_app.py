import azure.functions as func
import azure.durable_functions as df
import time
import logging
import json

myApp = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@myApp.route(route="check/orchestrators")
@myApp.durable_client_input(client_name="client")
async def check_orchestrator(req: func.HttpRequest, client):
    instances = await client.get_status_all()
    for instance in instances:
        # logging.info(instance.to_json())
        instance_dict = instance.to_json()
        
        # logging.info((type(instance_dict)))        
        if instance_dict["runtimeStatus"] != "Completed":
            logging.info(f'name: {instance_dict["name"]} instanceId : {instance_dict["instanceId"]} runtimeStatus: {instance_dict["runtimeStatus"]} lastUpdatedTime: {instance_dict["lastUpdatedTime"]}')
            
    return ""

# An HTTP-Triggered Function with a Durable Functions Client binding
@myApp.route(route="orchestrators/{functionName}")
@myApp.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    function_name = req.route_params.get('functionName')

    # 'functionName' がすでに動いているかどうかを確認する
    instances = await client.get_status_all()
    running = False
    for instance in instances:
        # logging.info(instance.to_json())
        instance_dict = instance.to_json()
        
        # logging.info((type(instance_dict)))        
        if instance_dict["runtimeStatus"] != "Completed":
            logging.info(f'name: {instance_dict["name"]} instanceId : {instance_dict["instanceId"]} runtimeStatus: {instance_dict["runtimeStatus"]} lastUpdatedTime: {instance_dict["lastUpdatedTime"]}')            
            # logging.log(json.dumps(instance))
            # 動作中の場合はここでErrorにできる
            running = True
            # raise Exception('すでに実行中の場合 500')
    if running:
        raise Exception('すでに実行中の場合 500')


    # Orchestrator関数の開始
    instance_id = await client.start_new(function_name)
    response = client.create_check_status_response(req, instance_id)
    return response

# Orchestrator
@myApp.orchestration_trigger(context_name="context")
def hello_orchestrator(context):
    #
    # #1. 関数チェーン
    #
    result1 = yield context.call_activity("hello", "Seattle")
    result2 = yield context.call_activity("hello", "Tokyo")
    result3 = yield context.call_activity("hello", "London")

    return [result1, result2, result3]

# Activity
@myApp.activity_trigger(input_name="city")
def hello(city: str):
    # 時間のかかる処理
    for i in range(10):
        logging.info(f" hello sleep. city: {city}")
        time.sleep(1) #10秒
    
    logging.info(" hello done")
    return f"Hello {city}"

# Orchestrator
@myApp.orchestration_trigger(context_name="context")
def hello_orchestrator2(context):
    #
    # #2. ファンイン/ファンアウト
    #
    result1 = yield context.call_activity("hello2", "F1")

    parallel_tasks = [
        context.call_activity("hello2", "F2"),
        context.call_activity("hello2", "F2"),
        context.call_activity("hello2", "F2"),
    ]
    result2 = yield context.task_all(parallel_tasks)

    result3 = yield context.call_activity("hello2", "F3")

    return [result1, result2, result3]

# Activity
@myApp.activity_trigger(input_name="city")
def hello2(city: str):
    # 時間のかかる処理
    for i in range(5):
        logging.info(f" hello sleep. city: {city}")
        time.sleep(1) #10秒
    
    logging.info(" hello done")
    return f"Hello {city}"

@myApp.function_name(name="QueueFunc")
@myApp.queue_trigger(arg_name="msg", queue_name="my-batchjob-queue",
                   connection="AzureWebJobsStorage")  # Queue trigger
@myApp.queue_output(arg_name="outputQueueItem", queue_name="my-batchjob-queue-out",
                 connection="AzureWebJobsStorage")  # Queue output binding
@myApp.durable_client_input(client_name="client")
async def test_function(msg: func.QueueMessage,
                  outputQueueItem: func.Out[str], client) -> None:
    logging.info('Python queue trigger function processed a queue item: %s',
                 msg.get_body().decode('utf-8'))

    # Orchestrator関数の開始
    instance_id = await client.start_new('hello_orchestrator2')
    # response = client.create_check_status_response(req, instance_id)

    outputQueueItem.set(f'{instance_id} is started.')