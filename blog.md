# Azure Functions ([Python]Durable Function)

# はじめに

こんにちは。ACS 事業部の奥山です。

Azure Functions の Durable Functions (Python) についての調査・検証を行ったので、備忘録を兼ねてブログにしておきます。

現在、担当しているシステムで時間のかかる処理を行う必要があり、調べた内容です。
様々な実現方法があるとは思いますが、Azure なら Durable Functions お勧めです！

## Durable Functions (Azure Functions) とは

以前に Durable Functions について[ブログ](https://techblog.ap-com.co.jp/entry/2022/06/02/170053)を書いたブログを紹介

# Python での実装について

※このブログでは実際のソースコードなどは記載しません。

Azure Functions Python でのプログラミングには プログラミング モデル v1 と v2 があります。
v1 と v2 の最も大きな違いは functions.json を利用するかどうかですかね。 v2 では functions.json がなくなりデコレーターでバインディング等の設定を指定することになり、コード中心になります。
※ 今回は v2 で実装を進めています。

## python での実装 (最低限のはじめかた)

[Azure Functions の Python 開発者向けガイド](https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators)

## Blueprints (フォルダ構成を変更)

フォルダ構成を推奨フォルダー構造を参考に、ブループリントを利用して少し機能単位にフォルダを分けました。

```
$ tree
.
├── __pycache__
│   ├── func1_blueprint.cpython-310.pyc
│   └── function_app.cpython-310.pyc
├── blog.md
├── func01 ※一つ目の機能
│   ├── __pycache__
│   │   └── func1_blueprint.cpython-310.pyc
│   └── func1_blueprint.py
├── func02 ※二つ目の機能
│   ├── __pycache__
│   │   └── func2_blueprint.cpython-310.pyc
│   └── func2_blueprint.py
├── function_app.py
├── host.json
├── local.settings.json
└── requirements.txt
```

# アプリケーション パターン #3: 非同期 HTTP API

時間のかかる処理に有効なのが [アプリケーション パターン #3: 非同期 HTTP API](https://learn.microsoft.com/ja-jp/azure/azure-functions/durable/durable-functions-overview?tabs=in-process%2Cnodejs-v3%2Cv2-model&pivots=python#async-http) です。

![img](./blog_img/blog_img_01.png)

実装自体は 通常の durable functions と同様です。
何もしなくてもオーケストレーター関数の状態をクエリする Webhook HTTP API が組み込み処理が利用できます。※赤枠のところ

## 状態をクエリする Webhook HTTP API

※ [インスタンスの管理](https://learn.microsoft.com/ja-jp/azure/azure-functions/durable/durable-functions-instance-management?tabs=python) を参照

Webhook HTTP API の URL は HTTP-Triggered 関数の場合、REST の Response に含まれています。

```
response = client.create_check_status_response(req, instance_id)
```

レスポンスを確認すると以下のように URL が確認できます。

```bash
$ curl -sS http://localhost:7071/api/orchestrators/hello_orchestrator   | jq .
{
  "id": "59258d16b93544338469fd8d954b5e9d",
  "statusQueryGetUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/<id>",
  "sendEventPostUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/<id>/raiseEvent/{eventName}",
  "terminatePostUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/<id>/terminate",
  "rewindPostUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/<id>/rewind",
  "purgeHistoryDeleteUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/<id>",
  "restartPostUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/<id>/restart",
  "suspendPostUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/<id>/suspend",
  "resumePostUri": "http://localhost:7071/runtime/webhooks/durabletask/instances/<id>/resume"
}
```

## Runtime Status

Client はポーリングによって操作が完了したことを認識することができます。
Client は API を通してオーケストレーションの状態をしることができます。

| RuntimeStatus  | 意味                                                                    |
| -------------- | ----------------------------------------------------------------------- |
| Pending        | スケジュール済み                                                        |
| Running        | 実行中                                                                  |
| Completed      | 完了　                                                                  |
| ContinuedAsNew | インスタンスが新しい履歴で自身を再開しました。 これは一時的な状態です。 |
| Failed         | 失敗                                                                    |
| Terminated     | 停止                                                                    |
| Suspended      | 再開(resume)待ち                                                        |

# スケーリングとパフォーマンスの調整

## インスタンス数

vm の数 ※

## 環境変数（local.settings.json）

FUNCTIONS_WORKER_PROCESS_COUNT 　 process の数 (default:1)
PYTHON_THREADPOOL_THREAD_COUNT thread の数 (default:None)
　※実行中に設定されるスレッドの数を保証しない

## host.json

maxConcurrentActivityFunctions (default:10)
maxConcurrentOrchestratorFunctions (default:100)

※Consumption plan と NON-Consumption plan でデフォルト値が違う

```
    int maxConcurrentOrchestratorsDefault = this.inConsumption ? 5 : 10 * Environment.ProcessorCount;
    int maxConcurrentActivitiesDefault = this.inConsumption ? 10 : 10 * Environment.ProcessorCount;
```

[Azure Functions で Python アプリのスループット パフォーマンスを向上させる](https://learn.microsoft.com/ja-jp/azure/azure-functions/python-scale-performance-reference) に書かれている以下の２つのパラメータを調整して性能をコントロールできます。

[アプリケーション設定](https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-app-settings)

| 設定名                         | 備考                                    |
| ------------------------------ | --------------------------------------- |
| FUNCTIONS_WORKER_PROCESS_COUNT | 既定値は 1 です。 許容される最大値は 10 |
| PYTHON_THREADPOOL_THREAD_COUNT | スレッド数（初期値は None）             |

## 性能確認用の処理

次のような処理を実行して処理時間を計測してみました。

# 最後に

私達 ACS 事業部は Azure・AKS を活用した内製化のご支援をしております。ご相談等ありましたらぜひご連絡ください。

[https://www.ap-com.co.jp/cloudnative/?utm_source=blog&utm_medium=article_bottom&utm_campaign=cloudnative:embed:cite]

また、一緒に働いていただける仲間も募集中です！  
切磋琢磨しながらスキルを向上できる、エンジニアには良い環境だと思います。ご興味を持っていただけたら嬉しく思います。

[https://www.ap-com.co.jp/recruit/info/requirements.html?utm_source=blog&utm_medium=article_bottom&utm_campaign=recruit:embed:cite]

<fieldset style="border:4px solid #95ccff; padding:10px">
本記事の投稿者: [奥山 拓弥](https://techblog.ap-com.co.jp/archive/author/mountain1415)  
</fieldset>

host.json

```
"extensions": {
    "durableTask": {
      "maxConcurrentActivityFunctions": 4,
      (default: Consumption plan: 10Dedicated, Premium plan: 10X the number of processors on the current machine)
      "maxConcurrentOrchestratorFunctions": 4
      (default: Consumption plan: 5Dedicated, Premium plan: 10X the number of processors)
    }
```

evn

```
FUNCTIONS_WORKER_PROCESS_COUNT (default:1)
PYTHON_THREADPOOL_THREAD_COUNT (default: 値は None ※cpuのcore数)
```

az functionapp config appsettings set -n $FUNC_NAME2 -g $RG_NAME --settings "FUNCTIONS_WORKER_PROCESS_COUNT=1"
az functionapp config appsettings set -n $FUNC_NAME2 -g $RG_NAME --settings "PYTHON_THREADPOOL_THREAD_COUNT=1"

az webapp log tail --resource-group <RESOURCE_GROUP_NAME> --name <FUNCTION_APP_NAME>
az webapp log tail --resource-group $RG_NAME --name $FUNC_NAME2

024-06-22T22:40:20Z [Information] Executing StatusCodeResult, setting HTTP status code 200
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Checking worker statuses (Count=10)
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=f4dd1707-b82f-44ab-a16a-456fa48108ce, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=dce16424-a35a-4bd5-8edb-b9420d35e4d8, Latency=5ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=d4a224fe-885b-4206-8cf2-01b43f60d0ba, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=8dc51031-429f-43f7-bce1-014e5cd728c2, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=6cecb72e-4d83-4e37-bd3d-a07a3eab05fe, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=debaf19e-3be5-4e4f-a4ee-c3d4ac52e6ad, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=c52d645f-eb87-4b9d-89bd-8192f431bba7, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=f60fccae-1429-4f35-9b70-24601cf8bc2f, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=8011aa0f-4695-4390-8402-4fc155fd6364, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Worker status: ID=ee2bc3fd-30e5-4224-92eb-1ad838436e4b, Latency=4ms
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 290): History=(0,0,0,0,0), AvgCpuLoad=0, MaxCpuLoad=0
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 96): History=(0,0,0,0,0), AvgCpuLoad=0, MaxCpuLoad=0
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 313): History=(0,1,0,0,0), AvgCpuLoad=0.2, MaxCpuLoad=1
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 341): History=(0,0,0,0,0), AvgCpuLoad=0, MaxCpuLoad=0
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 359): History=(0,0,0,0,0), AvgCpuLoad=0, MaxCpuLoad=0
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 377): History=(0,0,0,0,0), AvgCpuLoad=0, MaxCpuLoad=0
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 402): History=(0,1,0,0,0), AvgCpuLoad=0.2, MaxCpuLoad=1
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 426): History=(0,1,0,0,0), AvgCpuLoad=0.2, MaxCpuLoad=1
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 452): History=(0,0,0,1,0), AvgCpuLoad=0.2, MaxCpuLoad=1
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 470): History=(0,0,0,0,0), AvgCpuLoad=0, MaxCpuLoad=0
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host process CPU stats (PID 61): History=(2,9,2,1,1), AvgCpuLoad=3, MaxCpuLoad=9
2024-06-22T22:40:20Z [Verbose] [HostMonitor] Host aggregate CPU load 4
2024-06-22T22:40:20Z [Information] Executing StatusCodeResult, setting HTTP status code 200
2024-06-22T22:40:20Z [Information] funcdurablepy202406-control-00: Skipping ownership lease aquiring for funcdurablepy202406-control-00
2024-06-22T22:40:20Z [Information] funcdurablepy202406-control-03: Skipping ownership lease aquiring for funcdurablepy202406-control-03
2024-06-22T22:40:20Z [Information] F2 input: 4 start, hostname: SandboxHost-638546923930202365, process:id 359 thread ID: 139711492794112
2024-06-22T22:40:20Z [Information] F2 input: 14 start, hostname: SandboxHost-638546923930202365, process:id 402 thread ID: 139940352481024
2024-06-22T22:40:20Z [Information] F2 input: 24 start, hostname: SandboxHost-638546923930202365, process:id 96 thread ID: 140347730921216
2024-06-22T22:40:20Z [Information] F2 input: 44 start, hostname: SandboxHost-638546923930202365, process:id 313 thread ID: 140571282192128
2024-06-22T22:40:21Z [Information] F2 input: 5 start, hostname: SandboxHost-638546923930202365, process:id 359 thread ID: 139711492794112
2024-06-22T22:40:21Z [Information] F2 input: 15 start, hostname: SandboxHost-638546923930202365, process:id 402 thread ID: 139940352481024
2024-06-22T22:40:21Z [Information] TaskActivityDispatcher-86053700561849108652d2d8e7b7ef42-0: Delaying work item fetching because the current active work-item count (4) exceeds the configured maximum active work-item count (4)
2024-06-22T22:40:21Z [Information] F2 input: 25 start, hostname: SandboxHost-638546923930202365, process:id 96 thread ID: 140347730921216
2024-06-22T22:40:21Z [Information] F2 input: 45 start, hostname: SandboxHost-638546923930202365, process:id 313 thread ID: 140571282192128
2024-06-22T22:40:22Z [Information] funcdurablepy202406-control-01: Skipping ownership lease aquiring for funcdurablepy202406-control-01
2024-06-22T22:40:22Z [Information] funcdurablepy202406-control-02: Skipping ownership lease aquiring for funcdurablepy202406-control-02
2024-06-22T22:40:22Z [Information] F2 input: 6 start, hostname: SandboxHost-638546923930202365, process:id 359 thread ID: 139711492794112
2024-06-22T22:40:22Z [Information] F2 input: 16 start, hostname: SandboxHost-638546923930202365, process:id 402 thread ID: 139940352481024
2024-06-22T22:40:22Z [Information] F2 input: 26 start, hostname: SandboxHost-638546923930202365, process:id 96 thread ID: 140347730921216
2024-06-22T22:40:22Z [Information] F2 input: 46 start, hostname: SandboxHost-638546923930202365, process:id 313 thread ID: 140571282192128
2024-06-22T22:40:23Z [Information] F2 input: 7 start, hostname: SandboxHost-638546923930202365, process:id 359 thread ID: 139711492794112
2024-06-22T22:40:23Z [Information] F2 input: 17 start, hostname: SandboxHost-638546923930202365, process:id 402 thread ID: 139940352481024
2024-06-22T22:40:23Z [Information] F2 input: 27 start, hostname: SandboxHost-638546923930202365, process:id 96 thread ID: 140347730921216
2024-06-22T22:40:23Z [Information] F2 input: 47 start, hostname: SandboxHost-638546923930202365, process:id 313 thread ID: 140571282192128

2024-06-22T08:37:46Z [Information] F2 input: 80 start, hostname: SandboxHost-638546312758159482, process:id 7501 thread ID: 140583828383488
2024-06-22T08:37:46Z [Information] F2 input: 90 start, hostname: SandboxHost-638546312758159482, process:id 87 thread ID: 140470678845184
2024-06-22T08:37:47Z [Information] F2 input: 12 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650986403584
2024-06-22T08:37:47Z [Information] F2 input: 32 start, hostname: SandboxHost-638546288731124428, process:id 87 thread ID: 140206111000320
2024-06-22T08:37:47Z [Information] F2 input: 2 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650969618176
2024-06-22T08:37:47Z [Information] F2 input: 42 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650994796288
2024-06-22T08:37:47Z [Information] F2 input: 62 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650978010880
2024-06-22T08:37:47Z [Information] funcdurablepy202406-control-00: Skipping ownership lease aquiring for funcdurablepy202406-control-00
2024-06-22T08:37:47Z [Information] funcdurablepy202406-control-02: Skipping ownership lease aquiring for funcdurablepy202406-control-02
2024-06-22T08:37:47Z [Information] funcdurablepy202406-control-03: Skipping ownership lease aquiring for funcdurablepy202406-control-03
2024-06-22T08:37:47Z [Information] F2 input: 81 start, hostname: SandboxHost-638546312758159482, process:id 7501 thread ID: 140583828383488
2024-06-22T08:37:47Z [Information] F2 input: 91 start, hostname: SandboxHost-638546312758159482, process:id 87 thread ID: 140470678845184
2024-06-22T08:37:48Z [Information] funcdurablepy202406-control-00: Skipping ownership lease aquiring for funcdurablepy202406-control-00
2024-06-22T08:37:48Z [Information] funcdurablepy202406-control-01: Skipping ownership lease aquiring for funcdurablepy202406-control-01
2024-06-22T08:37:48Z [Information] F2 input: 13 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650986403584
2024-06-22T08:37:48Z [Information] F2 input: 33 start, hostname: SandboxHost-638546288731124428, process:id 87 thread ID: 140206111000320
2024-06-22T08:37:48Z [Information] F2 input: 3 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650969618176
2024-06-22T08:37:48Z [Information] F2 input: 43 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650994796288
2024-06-22T08:37:48Z [Information] F2 input: 63 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650978010880
2024-06-22T08:37:48Z [Information] F2 input: 92 start, hostname: SandboxHost-638546312758159482, process:id 87 thread ID: 140470678845184
2024-06-22T08:37:48Z [Information] F2 input: 82 start, hostname: SandboxHost-638546312758159482, process:id 7501 thread ID: 140583828383488
2024-06-22T08:37:49Z [Information] F2 input: 14 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650986403584
2024-06-22T08:37:49Z [Information] F2 input: 34 start, hostname: SandboxHost-638546288731124428, process:id 87 thread ID: 140206111000320
2024-06-22T08:37:49Z [Information] F2 input: 4 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650969618176
2024-06-22T08:37:49Z [Information] F2 input: 44 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650994796288
2024-06-22T08:37:49Z [Information] F2 input: 64 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650978010880
2024-06-22T08:37:49Z [Verbose] funcdurablepy202406-applease: Starting app lease renewal with token 1e191e85-0000-0000-0000-000000000000
2024-06-22T08:37:49Z [Verbose] funcdurablepy202406-applease: app lease renewal with token 1e191e85-0000-0000-0000-000000000000 succeeded
2024-06-22T08:37:49Z [Information] funcdurablepy202406-control-01: Skipping ownership lease aquiring for funcdurablepy202406-control-01
2024-06-22T08:37:49Z [Information] funcdurablepy202406-control-02: Skipping ownership lease aquiring for funcdurablepy202406-control-02
2024-06-22T08:37:49Z [Information] funcdurablepy202406-control-03: Skipping ownership lease aquiring for funcdurablepy202406-control-03
2024-06-22T08:37:49Z [Information] F2 input: 93 start, hostname: SandboxHost-638546312758159482, process:id 87 thread ID: 140470678845184
2024-06-22T08:37:49Z [Information] F2 input: 83 start, hostname: SandboxHost-638546312758159482, process:id 7501 thread ID: 140583828383488
2024-06-22T08:37:50Z [Information] F2 input: 15 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650986403584
2024-06-22T08:37:50Z [Information] F2 input: 35 start, hostname: SandboxHost-638546288731124428, process:id 87 thread ID: 140206111000320
2024-06-22T08:37:50Z [Information] F2 input: 5 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650969618176
2024-06-22T08:37:50Z [Information] F2 input: 45 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650994796288
2024-06-22T08:37:50Z [Information] F2 input: 65 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650978010880
2024-06-22T08:37:50Z [Information] TaskActivityDispatcher-496a451ba6b94f4d888e326ea1e955d1-0: Delaying work item fetching because the current active work-item count (8) exceeds the configured maximum active work-item count (8)
2024-06-22T08:37:50Z [Information] F2 input: 84 start, hostname: SandboxHost-638546312758159482, process:id 7501 thread ID: 140583828383488
2024-06-22T08:37:50Z [Information] F2 input: 94 start, hostname: SandboxHost-638546312758159482, process:id 87 thread ID: 140470678845184
2024-06-22T08:37:51Z [Information] F2 input: 16 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650986403584
2024-06-22T08:37:51Z [Information] F2 input: 36 start, hostname: SandboxHost-638546288731124428, process:id 87 thread ID: 140206111000320
2024-06-22T08:37:51Z [Information] F2 input: 6 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650969618176
2024-06-22T08:37:51Z [Information] F2 input: 46 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650994796288
2024-06-22T08:37:51Z [Information] F2 input: 66 start, hostname: SandboxHost-638546288731124428, process:id 5809 thread ID: 139650978010880

2024-06-22T08:19:41Z [Verbose] funcdurablepy202406-control-02: ownership lease renewal with token 8f66d1b3-0485-4bc6-ae2f-31929f01d5d5 succeeded
2024-06-22T08:19:41Z [Verbose] funcdurablepy202406-control-00: ownership lease renewal with token 12b53993-9dab-4bdd-8b99-bb3d1a089afc succeeded
2024-06-22T08:19:41Z [Verbose] funcdurablepy202406-control-01: ownership lease renewal with token 8a4087e6-a855-49e4-959e-73b1fcd8cf22 succeeded
2024-06-22T08:19:42Z [Information] F2 input: 42 start, hostname: SandboxHost-638546401320140818, process:id 86 thread ID: 139639015220992
2024-06-22T08:19:43Z [Verbose] [HostMonitor] Checking worker statuses (Count=1)
2024-06-22T08:19:43Z [Verbose] [HostMonitor] Worker status: ID=8235c3d2-f43c-4453-bb77-63fa55c4397d, Latency=1ms
2024-06-22T08:19:43Z [Verbose] [HostMonitor] Host process CPU stats (PID 86): History=(0,0,0,0,1), AvgCpuLoad=0.2, MaxCpuLoad=1
2024-06-22T08:19:43Z [Verbose] [HostMonitor] Host process CPU stats (PID 60): History=(2,1,1,4,2), AvgCpuLoad=2, MaxCpuLoad=4
2024-06-22T08:19:43Z [Verbose] [HostMonitor] Host aggregate CPU load 2
2024-06-22T08:19:43Z [Information] Executing StatusCodeResult, setting HTTP status code 200
2024-06-22T08:19:43Z [Information] F2 input: 43 start, hostname: SandboxHost-638546401320140818, process:id 86 thread ID: 139639015220992
2024-06-22T08:19:44Z [Information] F2 input: 44 start, hostname: SandboxHost-638546401320140818, process:id 86 thread ID: 139639015220992
2024-06-22T08:20:35Z [Information] F2 input: 95 start, hostname: SandboxHost-638546401320140818, process:id 86 thread ID: 139639015220992
2024-06-22T08:20:35Z [Verbose] [HostMonitor] Checking worker statuses (Count=1)
2024-06-22T08:20:35Z [Verbose] [HostMonitor] Worker status: ID=8235c3d2-f43c-4453-bb77-63fa55c4397d, Latency=1ms
2024-06-22T08:20:35Z [Verbose] [HostMonitor] Host process CPU stats (PID 86): History=(1,0,0,0,0), AvgCpuLoad=0.2, MaxCpuLoad=1
2024-06-22T08:20:35Z [Verbose] [HostMonitor] Host process CPU stats (PID 60): History=(4,3,1,3,0), AvgCpuLoad=2, MaxCpuLoad=4
2024-06-22T08:20:35Z [Verbose] [HostMonitor] Host aggregate CPU load 2
2024-06-22T08:20:35Z [Information] Executing StatusCodeResult, setting HTTP status code 200
2024-06-22T08:20:36Z [Information] F2 input: 96 start, hostname: SandboxHost-638546401320140818, process:id 86 thread ID: 139639015220992
2024-06-22T08:20:36Z [Verbose] funcdurablepy202406-applease: Starting app lease renewal with token 1e191e85-0000-0000-0000-000000000000
2024-06-22T08:20:36Z [Verbose] funcdurablepy202406-applease: app lease renewal with token 1e191e85-0000-0000-0000-000000000000 succeeded
2024-06-22T08:20:37Z [Information] F2 input: 97 start, hostname: SandboxHost-638546401320140818, process:id 86 thread ID: 139639015220992
2024-06-22T08:20:38Z [Information] F2 input: 98 start, hostname: SandboxHost-638546401320140818, process:id 86 thread ID: 139639015220992
2024-06-22T08:20:39Z [Information] F2 input: 99 start, hostname: SandboxHost-638546401320140818, process:id 86 thread ID: 139639015220992

mysql
engine.py の処理で利用しているライブラリ

[2024-06-17T08:52:16.672Z] F2 input: 79 start, hostname: IT-PC-2402-1092, pID: 3656399 thID: 140361662715456
[2024-06-17T08:52:16.672Z] F2 input: 119 start, hostname: IT-PC-2402-1092, pID: 3656450 thID: 140220934641216
[2024-06-17T08:52:16.690Z] F2 input: 139 start, hostname: IT-PC-2402-1092, pID: 3656399 thID: 140361654322752
[2024-06-17T08:52:16.713Z] F2 input: 109 start, hostname: IT-PC-2402-1092, pID: 3656450 thID: 140219986708032
[2024-06-17T08:52:16.730Z] F2 input: 129 start, hostname: IT-PC-2402-1092, pID: 3656399 thID: 140361645930048
[2024-06-17T08:52:16.749Z] F2 input: 99 start, hostname: IT-PC-2402-1092, pID: 3656450 thID: 140219978315328
[2024-06-17T08:52:16.773Z] F2 input: 169 start, hostname: IT-PC-2402-1092, pID: 3656399 thID: 140361637537344
[2024-06-17T08:52:16.794Z] F2 input: 159 start, hostname: IT-PC-2402-1092, pID: 3656450 thID: 140219969922624
[2024-06-17T08:52:16.821Z] F2 input: 179 start, hostname: IT-PC-2402-1092, pID: 3656399 thID: 140361629144640
[2024-06-17T08:52:16.843Z] F2 input: 149 start, hostname: IT-PC-2402-1092, pID: 3656450 thID: 140219961529920

04Z] Executed 'Functions.hello_orchestrator2' (Succeeded, Id=4992f719-5892-4b2e-84bd-2a24abdd7fcc, Duration=11ms)
[2024-06-17T08:55:03.111Z] F2 input: 146 start, hostname: IT-PC-2402-1092, pID: 3657847 thID: 140199384286784
[2024-06-17T08:55:03.138Z] F2 input: 161 start, hostname: IT-PC-2402-1092, pID: 3657887 thID: 140043532310080
[2024-06-17T08:55:03.160Z] F2 input: 151 start, hostname: IT-PC-2402-1092, pID: 3658035 thID: 140386710320704
[2024-06-17T08:55:03.180Z] F2 input: 156 start, hostname: IT-PC-2402-1092, pID: 3657847 thID: 140199375894080
[2024-06-17T08:55:03.203Z] F2 input: 171 start, hostname: IT-PC-2402-1092, pID: 3658176 thID: 140253222364736
[2024-06-17T08:55:03.227Z] F2 input: 176 start, hostname: IT-PC-2402-1092, pID: 3657887 thID: 140043549095488
[2024-06-17T08:55:03.248Z] F2 input: 186 start, hostname: IT-PC-2402-1092, pID: 3658035 thID: 140385976272448
[2024-06-17T08:55:03.273Z] F2 input: 181 start, hostname: IT-PC-2402-1092, pID: 3658176 thID: 140253213972032
[2024-06-17T08:55:03.291Z] F2 input: 191 start, hostname: IT-PC-2402-1092, pID: 3657887 thID: 140043557488192
[2024-06-17T08:55:03.310Z] F2 input: 196 start, hostname: IT-PC-2402-1092, pID: 3658035 thID: 140385951094336
[2024-06-17T08:55:04.113Z] F2 input: 147 start, hostname: IT-PC-2402-1092, pID: 3657847 thID: 140199384286784
[2024-06-17T08:55:04.140Z] F2 input: 162 start, hostname: IT-PC-2402-1092, pID: 3657887 thID: 140043532310080
[2024-06-17T08:55:04.161Z] F2 input: 152 start, hostname: IT-PC-2402-1092, pID: 3658035 thID: 140386710320704
[2024-06-17T08:55:04.183Z] F2 input: 157 start, hostname: IT-PC-2402-1092, pID: 3657847 thID: 140199375894080
[2024-06-17T08:55:04.204Z] F2 input: 172 start, hostname: IT-PC-2402-1092, pID: 3658176 thID: 140253222364736
[2024-06-17T08:55:04.228Z] F2 input: 177 start, hostname: IT-PC-2402-1092, pID: 3657887 thID: 140043549095488
[2024-06-17T08:55:04.250Z] F2 input: 187 start, hostname: IT-PC-2402-1092, pID: 3658035 thID: 140385976272448
[2024-06-17T08:55:04.275Z] F2 input: 182 start, hostname: IT-PC-2402-1092, pID: 3658176 thID: 140253213972032
[2024-06-17T08:55:04.293Z] F2 input: 192 start, hostname: IT-PC-2402-1092, pID: 3657887 thID: 140043557488192
[2024-06-17T08:55:04.311Z] F2 input: 197 start, hostname: IT-PC-2402-1092, pID: 3658035 thID: 140385951094336
[2024-06-17T08:55:05.114Z] F2 input: 148 start, hostname: IT-PC-2402-1092, pID: 3657847 thID: 140199384286784
[2024-06-17T08:55:05.141Z] F2 input: 163 start, hostname: IT-PC-2402-1092, pID: 3657887 thID: 140043532310080
[2024-06-17T08:55:05.162Z] F2 input: 153 start, hostname: IT-PC-2402-1092, pID: 3658035 thID: 140386710320704
[2024-06-17T08:55:05.184Z] F2 input: 158 start, hostname: IT-PC-2402-1092, pID: 3657847 thID: 140199375894080
[2024-06-17T08:55:05.205Z] F2 input: 173 start, hostname: IT-PC-2402-1092, pID: 3658176 thID: 140253222364736
[2024-06-17T08:55:05.229Z] F2 input: 178 start, hostname: IT-PC-2402-1092, pID: 3657887 thID: 140043549095
