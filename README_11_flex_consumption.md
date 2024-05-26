# Flex Consumption Plan

仮想ネットワークの統合　が可能 ★

Python 3.10、Python 3.11

```
python -VV
Python 3.11.9 (main, May 25 2024, 11:44:56) [GCC 9.4.0]
```

2024/05 時点は Preview です。

## 前提

https://learn.microsoft.com/ja-jp/azure/azure-functions/create-first-function-cli-python?tabs=linux%2Cbash%2Cazure-cli%2Cbrowser

Azure CLI バージョン ※最新を利用

```
az version
{
  "azure-cli": "2.61.0",
  "azure-cli-core": "2.61.0",
  "azure-cli-telemetry": "1.1.0",
  "extensions": {}
}
```

Azure Functions Core Tools

```
func --version
4.0.5801
```

# 補足

```
# @app.route(route="HttpExample", auth_level=func.AuthLevel.Anonymous)
@app.route(route="HttpExample", auth_level=func.AuthLevel.ANONYMOUS)
```

定義が変わった？？

# az cli (azure function)

az

```
export RG_NAME=rg-func-2024-05
export STORAGE_NAME=st2024func0001test
export REGION=eastasia
export FUNC_NAME=func-app-py-202405

# rg
az group create --name $RG_NAME --location $REGION
# az group delete -n $RG_NAME

# storage (--allow-blob-public-access false)
az storage account create --name $STORAGE_NAME --location $REGION --resource-group $RG_NAME --sku Standard_LRS

# list-flexconsumption-locations ※japaneastはまだ提供されていない
az functionapp list-flexconsumption-locations --output table
Name
---------------------
eastus
northeurope
southeastasia
eastasia
eastus2
southcentralus
australiaeast
northcentralus(stage)
westus2
uksouth
eastus2euap
westus3
swedencentral

# function (--flexconsumption-location)
az functionapp create --resource-group $RG_NAME --flexconsumption-location $REGION --runtime python --runtime-version 3.11 --functions-version 4 --name $FUNC_NAME --os-type linux --storage-account $STORAGE_NAME
```

## v2 プログラミング モデルを有効にする

※アプリケーション設定

```
az functionapp config appsettings set --name $FUNC_NAME --resource-group $RG_NAME --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing
```

# az function (ここからはプログラミング)

※<プロジェクト フォルダ> を作成しておく
仮想環境作成

```
python -m venv .venv
source .venv/bin/activate
```

## create project

仮想環境に Python v2 関数プロジェクトを作成

```
cd <プロジェクト フォルダ>
func init --python
```

## create func

```
func new --name HttpExample --template "HTTP trigger" --authlevel "ANONYMOUS"
```

## run on local

```
func start
```

## deploy

```
func azure functionapp publish $FUNC_NAME
```
