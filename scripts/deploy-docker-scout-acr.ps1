$ErrorActionPreference = "Stop"

param(
    [string]$RegistryName = "bkltblacklight",
    [string]$EventGridTopicName = "docker-scout-repository-ACR-1-83b3",
    [string]$WebhookUrl = "https://api.dso.docker.com/webhook/658f1650-2b3f-4b83-8439-b0c7c721b68a",
    [string]$AccessTokenName = "docker-scout-readonly-token-ACR-1-83b3",
    [switch]$ConfirmExternalDeploy
)

if (-not $ConfirmExternalDeploy) {
    Write-Host "BLOCKED: this script deploys Azure/EventGrid resources and prints an ACR token." -ForegroundColor Red
    Write-Host "Run only after explicit user approval: .\scripts\deploy-docker-scout-acr.ps1 -ConfirmExternalDeploy" -ForegroundColor Yellow
    exit 2
}

$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
if (-not (Test-Path $az)) {
    throw "未找到 Azure CLI: $az"
}

Write-Host "==> 检查 Azure 登录态..." -ForegroundColor Cyan
$subscriptionId = & $az account show --query id -o tsv 2>$null
if (-not $subscriptionId) {
    throw "Azure 未登录。请先运行: az login --use-device-code"
}
Write-Host "   已登录订阅: $subscriptionId" -ForegroundColor Green

Write-Host "==> 读取 ACR 所在资源组..." -ForegroundColor Cyan
$resourceGroup = & $az acr show -n $RegistryName --query resourceGroup -o tsv
if (-not $resourceGroup) {
    throw "未找到 ACR: $RegistryName，请确认名称与当前订阅是否正确。"
}
Write-Host "   ACR 资源组: $resourceGroup" -ForegroundColor Green

$templateDir = Join-Path $PSScriptRoot "_generated"
New-Item -ItemType Directory -Path $templateDir -Force | Out-Null
$templateFile = Join-Path $templateDir "docker-scout-acr-template.json"

$template = @'
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "DockerScoutWebhook": {
      "type": "String",
      "metadata": {
        "description": "EventGrid subscription webhook URL"
      }
    },
    "RegistryName": {
      "type": "String",
      "metadata": {
        "description": "Name of the registry to add Docker Scout"
      }
    },
    "systemTopics_dockerScoutRepository": {
      "type": "String",
      "defaultValue": "docker-scout-repository",
      "metadata": {
        "description": "EventGrid topic name"
      }
    },
    "DockerScoutTokenName": {
      "type": "String",
      "defaultValue": "docker-scout-readonly-token",
      "metadata": {
        "description": "Read-only ACR token name for Docker Scout"
      }
    }
  },
  "resources": [
    {
      "type": "Microsoft.EventGrid/systemTopics",
      "apiVersion": "2023-06-01-preview",
      "name": "[parameters('systemTopics_dockerScoutRepository')]",
      "location": "[resourceGroup().location]",
      "identity": {
        "type": "None"
      },
      "properties": {
        "source": "[extensionResourceId(resourceGroup().Id, 'Microsoft.ContainerRegistry/Registries', parameters('RegistryName'))]",
        "topicType": "Microsoft.ContainerRegistry.Registries"
      }
    },
    {
      "type": "Microsoft.EventGrid/systemTopics/eventSubscriptions",
      "apiVersion": "2023-06-01-preview",
      "name": "[concat(parameters('systemTopics_dockerScoutRepository'), '/image-change')]",
      "dependsOn": [
        "[resourceId('Microsoft.EventGrid/systemTopics', parameters('systemTopics_dockerScoutRepository'))]"
      ],
      "properties": {
        "destination": {
          "endpointType": "WebHook",
          "properties": {
            "endpointUrl": "[parameters('DockerScoutWebhook')]",
            "maxEventsPerBatch": 1,
            "preferredBatchSizeInKilobytes": 64
          }
        },
        "eventDeliverySchema": "EventGridSchema",
        "filter": {
          "includedEventTypes": [
            "Microsoft.ContainerRegistry.ImagePushed",
            "Microsoft.ContainerRegistry.ImageDeleted"
          ],
          "enableAdvancedFilteringOnArrays": true
        },
        "labels": [],
        "retryPolicy": {
          "maxDeliveryAttempts": 30,
          "eventTimeToLiveInMinutes": 1440
        }
      }
    },
    {
      "type": "Microsoft.ContainerRegistry/registries/tokens",
      "apiVersion": "2023-01-01-preview",
      "name": "[concat(parameters('RegistryName'), '/', parameters('DockerScoutTokenName'))]",
      "properties": {
        "credentials": {},
        "scopeMapId": "[resourceId('Microsoft.ContainerRegistry/registries/scopeMaps', parameters('RegistryName'), '_repositories_pull_metadata_read')]"
      }
    }
  ]
}
'@

Set-Content -Path $templateFile -Value $template -Encoding UTF8

$deploymentName = "docker-scout-acr-" + (Get-Date -Format "yyyyMMddHHmmss")
Write-Host "==> 开始 ARM 部署: $deploymentName" -ForegroundColor Cyan
& $az deployment group create `
    --name $deploymentName `
    --resource-group $resourceGroup `
    --template-file $templateFile `
    --parameters `
      DockerScoutWebhook=$WebhookUrl `
      RegistryName=$RegistryName `
      systemTopics_dockerScoutRepository=$EventGridTopicName `
      DockerScoutTokenName=$AccessTokenName `
    --only-show-errors -o jsonc

Write-Host "==> 生成 ACR Token 密码..." -ForegroundColor Cyan
$credJson = & $az acr token credential generate `
    --name $AccessTokenName `
    --registry $RegistryName `
    --password1 `
    --expiration-in-days 365 `
    -o json

if ($LASTEXITCODE -ne 0) {
    throw "Token 密码生成失败，请检查权限。"
}

$cred = $credJson | ConvertFrom-Json
$password = $cred.passwords[0].value
if (-not $password) {
    throw "未拿到 token 密码。"
}

Write-Host ""
Write-Host "✅ 部署完成。" -ForegroundColor Green
Write-Host "Docker Scout 填写信息：" -ForegroundColor Yellow
Write-Host "  Registry: $RegistryName.azurecr.io"
Write-Host "  Token Name: $AccessTokenName"
Write-Host "  Token Password: $password"
Write-Host ""
Write-Host "下一步：把上面 Token Name + Token Password 粘贴到 Docker Scout 的 Azure ACR 集成页面完成启用。"
