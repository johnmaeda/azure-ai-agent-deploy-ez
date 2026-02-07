### How the **project identifier** is used (and what it “is”)

In the Microsoft Foundry / Azure AI Foundry “project” model, the **project identifier** is essentially the **resource ID for the project** (an Azure ARM-style ID). You use it when you need to scope operations *to a project* (most commonly **RBAC**, and in some APIs, “list deployments in this project”). In the Foundry quickstart, Microsoft explicitly pulls the project’s resource ID and then uses it as the `--scope` for role assignment. ([Microsoft Learn][1])

**Get the project identifier (resource ID):**

```bash
PROJECT_ID=$(az cognitiveservices account project show \
  --name <foundry-resource-name> \
  --resource-group <rg> \
  --project-name <foundry-project-name> \
  --query id -o tsv)

echo $PROJECT_ID
```

That’s the “project identifier” you’ll see referenced conceptually across Foundry project tooling and SDKs (some SDKs literally model this as “account identifier” + “project identifier”). ([Microsoft Learn][2])

> Important nuance: the specific doc you linked (“create model deployments”) is primarily showing **Foundry Models deployments on the Foundry resource** via `az cognitiveservices ...` (account/resource-scoped), so it doesn’t *need* the project identifier for the core deployment commands. It *does* require a Foundry project as a prerequisite, but the CLI flow shown uses the **resource** name + resource group. ([Microsoft Learn][3])

---

## How to list available models (so you know what to pass to the CLI)

The doc’s recommended way is:

```bash
az cognitiveservices account list-models \
  -n <foundry-resource-name> \
  -g <rg>
```

…and they show piping through `jq` to extract the fields you need for deployment: `name`, `format` (provider), `version`, and `skus` (deployment type / SKU). ([Microsoft Learn][3])

### List **Microsoft**-published models only

The output includes `format` (provider). Filter to Microsoft:

```bash
az cognitiveservices account list-models -n <foundry-resource-name> -g <rg> \
| jq '.[] | select(.format=="Microsoft") | {name, format, version, skus: [.skus[].name]}'
```

If you prefer a quick “just give me the canonical 4-tuple I must supply” view:

```bash
az cognitiveservices account list-models -n <foundry-resource-name> -g <rg> \
| jq -r '.[] | select(.format=="Microsoft") |
  "\(.name)\tformat=\(.format)\tversion=\(.version)\tsku=\(.skus[0].name)"'
```

This matches the doc’s guidance that you must supply **model name, model format/provider, model version, and SKU** when creating a deployment. ([Microsoft Learn][3])

---

## How to tell whether a model “exists” and whether it’s deployed

### 1) Does the model exist / is it available to you?

Use `list-models` and search for the name:

```bash
MODEL_NAME="Phi-3.5-vision-instruct"

az cognitiveservices account list-models -n <foundry-resource-name> -g <rg> \
| jq -e --arg m "$MODEL_NAME" '.[] | select(.name==$m)'
```

* Exit code **0** → found (available)
* Exit code **1** → not found (not available in that resource/region/entitlement)

(Availability can depend on SKU/region/marketplace permissions, etc.) ([Microsoft Learn][3])

### 2) Is it deployed?

List deployments on the Foundry resource:

```bash
az cognitiveservices account deployment list -n <foundry-resource-name> -g <rg>
```

…and/or check a specific deployment:

```bash
az cognitiveservices account deployment show \
  --deployment-name <deployment-name> \
  -n <foundry-resource-name> \
  -g <rg>
```

The quickstart notes you’ll see `"provisioningState": "Succeeded"` when it’s ready. ([Microsoft Learn][1])

### 3) “Is the deployed thing healthy/real?” (practical check)

Once deployed, the endpoint is shared and you route by **deployment name** in the `model` parameter; the doc shows getting the inference endpoint URI from the resource. ([Microsoft Learn][3])
So an end-to-end verification is:

1. deployment `show` says `Succeeded`
2. inference call using `model=<deployment-name>` returns 200

---

## If you meant *project-scoped* deployments (serverless endpoints) instead

Foundry also has the “AI project” notion where deployments can be listed **per project** via the Azure AI Foundry REST surface (example: “List all deployed models in the project”). ([Microsoft Learn][4])
In those scenarios, the **project identifier** becomes the natural scope handle (project → deployments), even if the “Foundry Models on a Foundry resource” flow is resource-scoped.

---

### Copy/paste mini “decoder ring” (what to feed the deployment CLI)

From `list-models`, collect:

* `--model-name` → `.name`
* `--model-format` → `.format` (provider like `Microsoft`, `OpenAI`, etc.)
* `--model-version` → `.version`
* `--sku-name` → one of `.skus[].name`
* `--sku-capacity` → often `skus[0].capacity.default` (varies by model/SKU) ([Microsoft Learn][3])

Then deploy using the pattern shown in the doc. ([Microsoft Learn][3])

---

If you paste the exact **“project identifier”** snippet from the doc section you’re looking at (or tell me which CLI command it appears in), I’ll map it precisely to the underlying resource it’s scoping (project vs resource) and give you the exact “list / show / verify” command set for that path.

[1]: https://learn.microsoft.com/en-us/azure/ai-foundry/tutorials/quickstart-create-foundry-resources?view=foundry "Quickstart: Set up Microsoft Foundry resources - Microsoft Foundry | Microsoft Learn"
[2]: https://learn.microsoft.com/en-us/dotnet/api/azure.ai.agentserver.core.context.foundryprojectinfo?view=azure-dotnet-preview&utm_source=chatgpt.com "FoundryProjectInfo Class (Azure.AI.AgentServer.Core.Context)"
[3]: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/create-model-deployments?view=foundry-classic "Deploy models using Azure CLI and Bicep - Microsoft Foundry | Microsoft Learn"
[4]: https://learn.microsoft.com/en-us/rest/api/aifoundry/aiprojects/deployments/list?view=rest-aifoundry-aiprojects-v1&utm_source=chatgpt.com "Deployments - List - REST API (Azure AI Foundry)"
