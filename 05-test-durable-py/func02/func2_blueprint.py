import logging
import azure.functions as func
import azure.durable_functions as df
import numpy as np
import time
import socket
import threading
import os

bp = df.Blueprint()


def log_thread_info(function_name):
    hostname = socket.gethostname()
    thread_id = threading.get_ident()
    process_id = os.getpid()
    
    message = f"{function_name}, hostname: {hostname}, process:id {process_id} thread ID: {thread_id}"
    logging.info(message)
    return message


# An HTTP-Triggered Function with a Durable Functions Client binding
@bp.route(route="orchestrators2/{functionName}")
@bp.durable_client_input(client_name="client")
async def http_start2(req: func.HttpRequest, client):
    function_name = req.route_params.get('functionName')
    
    # シングルトンで動かす
    instance_id = req.params.get('myId', 'my-id-2024001')
    log_thread_info(f"http_start2: instance_id {instance_id}")
    existing_instance = await client.get_status(instance_id)
    if existing_instance.runtime_status in [df.OrchestrationRuntimeStatus.Completed, df.OrchestrationRuntimeStatus.Failed, df.OrchestrationRuntimeStatus.Terminated, None]:
        taskCount = int(req.params.get('taskCount', '100'))
        log_thread_info(f"http_start2: taskCount {taskCount}")
        instance_id = await client.start_new(function_name, instance_id, taskCount)
        response = client.create_check_status_response(req, instance_id)
    else:
        log_thread_info(f"An instance with ID '${existing_instance.instance_id}' already exists")
        response = client.create_check_status_response(req, instance_id)
        # return {
        #     'status': 409,
        #     'body': f"An instance with ID '${existing_instance.instance_id}' already exists"
        # }


    return response


# Orchestrator
@bp.orchestration_trigger(context_name="context")
def hello_o2(context):

    # F1
    taskCount = context.get_input()
    logging.info(f"hello_o2 taskCount: {taskCount}")
    all_work_batch = yield context.call_activity("F1", taskCount)
    # logging.info(f"all_work_batch: {all_work_batch}")

    # chunkSizeに分割
    chunk_size = 10
    split_work_batches = np.array_split(all_work_batch, chunk_size)
    logging.info(f"split_work_batches: {split_work_batches}")

    # F2
    parallel_size = 5
    parallel_tasks = []
    # n分割してActivityを呼び出す
    split_work_batches = np.array_split(all_work_batch, len(all_work_batch) // 5)
    for works in split_work_batches:
        parallel_tasks.append(context.call_activity("F2", works.tolist()))

    logging.info(f"len of parallel_tasks : {len(parallel_tasks)}")
    outputs = yield context.task_all(parallel_tasks)

    # F3
    result = yield context.call_activity("F3", outputs)
    return result


# Activity
@bp.activity_trigger(input_name="taskCount")
def F1(taskCount=None):
    # logging.info("F1 start")
    # target_task_count = int(os.getenv('TARGET_TASK_COUNT', 100))
    log_thread_info(f"F1: taskCount {taskCount}")
    # 数値の配列作成する
    return [i for i in range(taskCount)]


# Activity
@bp.activity_trigger(input_name="input")
def F2(input):
    outputs = []
    # 時間のかかる処理
    for i in input:
        # logging.info(f"input: {i}")
        output = log_thread_info(f"F2 input: {i} start")
        # time.sleep(1)
        # 疑似的な時間のかかる処理
        generate_primes(100000)

        # output = log_thread_info(f"F2 input: {i} end")
        outputs.append(output)

    logging.info(outputs)
    return outputs

def generate_primes(limit):
    primes = []
    for i in range(2, limit):
        for j in range(2, int(i**0.5) + 1):
            if i % j == 0:
                break
        else:
            primes.append(i)
    return primes


# Activity
@bp.activity_trigger(input_name="input")
def F3(input):
    log_thread_info("F3")
    logging.info("F3 start")
    return input
