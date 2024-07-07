export ACR_NAME=acr202406funcapp001
export IMAGE_NAME=durable-func-py
export IMAGE_VER=v2024070703

# az acr login --name $ACR_NAME

# build
docker build --tag $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_VER .

# push
docker push ${ACR_NAME}.azurecr.io/$IMAGE_NAME:$IMAGE_VER


export CONTAITER_APP_NAME=aca-my-first-container-app
az containerapp update --name $CONTAITER_APP_NAME --resource-group $RG_NAME --image $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_VER

# curl -i https://aca-my-first-container-app.kindpebble-2073c725.japaneast.azurecontainerapps.io/api/orchestrators2/hello_o2?myId=my-id-202407002
