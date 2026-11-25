# 🤖 n8n + Gemini Orchestrator

> Classificação automática de mensagens de clientes usando **IA (Google Gemini)**, uma **API em FastAPI** e um fluxo de automação no **n8n**.

**Projeto integrador — KODIE | Desafio Técnico: IA e Automação**
**Caso escolhido:** 4.1 — Classificação de Mensagens

---

## 📑 Sumário

1. [Apresentação da Ideia](#1-apresentação-da-ideia)
2. [Problema Escolhido](#2-problema-escolhido)
3. [Solução Proposta](#3-solução-proposta)
4. [Tecnologias Utilizadas](#4-tecnologias-utilizadas)
5. [Funcionamento do Sistema](#5-funcionamento-do-sistema)
6. [Como Executar](#6-como-executar)
7. [Documentação do Fluxo de Automação (prints)](#7-documentação-do-fluxo-de-automação-prints)
8. [Prompt Estruturado](#8-prompt-estruturado)
9. [Estrutura do Repositório](#9-estrutura-do-repositório)
10. [Segurança e Credenciais](#10-segurança-e-credenciais)
11. [Solução de Problemas](#11-solução-de-problemas)
12. [Melhorias Futuras](#12-melhorias-futuras)
13. [Licença](#13-licença)

---

## 1. Apresentação da Ideia

A ideia nasceu de uma situação muito comum em pequenas empresas: o atendimento recebe mensagens de clientes todos os dias (WhatsApp, e-mail, formulários) e alguém precisa **ler uma por uma, entender o assunto e encaminhar para o setor certo**.

Esse trabalho manual é lento, repetitivo e sujeito a erros: uma mensagem urgente pode ficar esquecida no meio das demais, e um pedido de venda pode cair no setor de suporte.

Pensando nisso, a proposta foi **tirar essa triagem das mãos de uma pessoa** e entregá-la a uma IA, enquanto uma ferramenta de automação cuida do restante do caminho. A IA **não apenas responde**: ela **interpreta** a mensagem, **decide** a categoria e a prioridade e devolve tudo de forma estruturada, pronta para ser usada por outros sistemas.

## 2. Problema Escolhido

**Caso 4.1 — Classificação de Mensagens.**

> Uma empresa recebe mensagens de clientes com diferentes tipos de solicitações, mas não possui um processo organizado para identificar cada assunto.

O problema a resolver é: **como identificar automaticamente o assunto, a urgência e um resumo de cada mensagem recebida, para que ela seja encaminhada ao setor responsável?**

### Perguntas de investigação do desafio e como o projeto responde

| Pergunta | Resposta no projeto |
|---|---|
| Como a IA pode ajudar a organizar as mensagens? | Lendo o texto e atribuindo categoria, prioridade e resumo. |
| Quais informações precisam ser identificadas? | `categoria`, `prioridade` e `resumo`. |
| Como classificar as mensagens de acordo com o conteúdo? | Prompt com regras, categorias permitidas e exemplos (*few-shot*). |
| Como automatizar o encaminhamento? | Fluxo no n8n acionado por webhook, chamado pela API FastAPI. |
| Como garantir que a resposta da IA esteja em formato adequado? | Prompt que exige JSON puro + node de código que limpa e valida o JSON (ver [seção 5](#5-funcionamento-do-sistema)). |

## 3. Solução Proposta

A solução é composta por **três peças** que trabalham juntas:

1. **API (FastAPI)** — porta de entrada do sistema. Recebe a mensagem, valida os dados e envia ao n8n.
2. **Automação (n8n)** — orquestra o processo: filtra os dados, chama a IA, trata a resposta e devolve o resultado.
3. **IA (Google Gemini)** — interpreta a mensagem e devolve a classificação em JSON.

### Como a IA participa do processo

A IA é o "cérebro" da triagem. Recebe a mensagem do cliente e, guiada por um prompt estruturado, devolve **somente** um objeto JSON:

```json
{
  "categoria": "financeiro",
  "prioridade": "alta",
  "resumo": "Dificuldade ao gerar boleto para pagamento"
}
```

| Campo | Valores possíveis | Descrição |
|---|---|---|
| `categoria` | `suporte`, `vendas`, `financeiro`, `outros` | Setor responsável pela mensagem |
| `prioridade` | `baixa`, `media`, `alta` | Urgência do atendimento |
| `resumo` | texto curto | Síntese do que o cliente precisa |

### Visão geral da arquitetura

```
┌──────────┐   POST /processar   ┌──────────────┐   POST (webhook)   ┌─────────────────────────────────────────────┐
│ Cliente  │ ──────────────────▶ │  API FastAPI │ ─────────────────▶ │                    n8n                      │
│ (Swagger │                     │  (valida os  │                    │                                             │
│ /Postman)│ ◀────────────────── │   dados)     │ ◀───────────────── │ Webhook → Code (filtro) → Gemini            │
└──────────┘   JSON com resultado└──────────────┘  JSON classificado │        → Code (parse JSON) → Respond Webhook│
                                                                     └─────────────────────────────────────────────┘
```

## 4. Tecnologias Utilizadas

| Camada | Tecnologia | Para que serve |
|---|---|---|
| Inteligência Artificial | **Google Gemini** (via node de IA do n8n) | Interpretar e classificar a mensagem |
| Back-end | **Python 3.11** | Linguagem da API |
| Framework web | **FastAPI** | Criação da API e documentação automática (Swagger) |
| Servidor ASGI | **Uvicorn** | Executa a aplicação FastAPI |
| Validação | **Pydantic** | Validação do corpo das requisições |
| HTTP client | **Requests** | Chamada da API ao webhook do n8n |
| Configuração | **python-dotenv** | Leitura de variáveis de ambiente do arquivo `.env` |
| Automação | **n8n** | Orquestração do fluxo (webhook, código, IA, resposta) |
| Testes manuais | **Swagger UI (`/docs`)** e **Postman** | Envio de requisições de teste |
| Controle de versão | **Git / GitHub** | Versionamento e entrega do projeto |

## 5. Funcionamento do Sistema

### 5.1 Como a API recebe os dados

A API expõe dois endpoints:

| Método | Rota | Função |
|---|---|---|
| `GET` | `/health` | Verifica se a API está no ar (`{"status": "ok"}`) |
| `POST` | `/processar` | Recebe a mensagem, valida e envia ao n8n |

O corpo da requisição do `POST /processar` é validado com **Pydantic**:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `mensagem` | `string` (mín. 1 caractere) | ✅ Sim | Conteúdo principal da mensagem do cliente |
| `pergunta` | `string` | Não | Pergunta adicional do cliente |
| `contexto` | `string` | Não | Contexto extra sobre o atendimento |
| `categoria` | `string` | Não | Categoria pré-existente, se houver |
| `filtros` | `objeto` | Não | Filtros adicionais |

Depois de validar, a API:

1. Remove os campos vazios (`None`) para enviar um JSON limpo;
2. Envia os dados por `POST` para a URL do webhook do n8n (definida em `N8N_WEBHOOK_URL`), com *timeout* de 30 segundos;
3. Devolve ao cliente o resultado retornado pelo n8n.

**Tratamento de erros da API:**

| Situação | Código HTTP |
|---|---|
| `N8N_WEBHOOK_URL` não configurada | `500` |
| n8n demorou mais de 30 s para responder | `504` |
| Falha de comunicação com o n8n (fora do ar, URL errada, erro HTTP) | `502` |
| Corpo da requisição inválido (ex.: sem `mensagem`) | `422` (automático do FastAPI) |

### 5.2 Como a IA processa as informações

No n8n, o fluxo executa as etapas abaixo, nesta ordem:

| # | Node | Função |
|---|---|---|
| 1 | **Webhook** | Recebe o `POST` enviado pela API |
| 2 | **Code in JavaScript** (filtro) | Mantém apenas os campos permitidos, remove espaços e campos vazios e gera `dados_filtrados` |
| 3 | **Node de IA (Google Gemini)** | Envia o prompt estruturado + `dados_filtrados` ao modelo e recebe a classificação |
| 4 | **Code in JavaScript** (parse) | Remove eventuais crases de markdown da resposta e converte o texto em JSON válido |
| 5 | **Respond to Webhook** | Devolve o JSON final à API |

**Por que há dois nodes de código?**

- **Antes da IA (filtro):** garante que somente dados úteis e limpos cheguem ao modelo, evitando enviar ao Gemini informações desnecessárias (como *headers* da requisição).
- **Depois da IA (parse):** mesmo pedindo "JSON puro", modelos de linguagem às vezes devolvem a resposta dentro de blocos ` ```json `. Esse node remove essas crases e faz o `JSON.parse`. Se mesmo assim o JSON for inválido, o fluxo **não quebra**: devolve `{"erro": "Falha ao parsear JSON do modelo", "raw": "..."}` para facilitar a depuração.

### 5.3 Como a automação é executada

1. O cliente envia a mensagem para `POST /processar` (pelo Swagger ou Postman).
2. A API valida e encaminha ao webhook do n8n.
3. O n8n filtra os dados, chama o Gemini, trata a resposta e a devolve via **Respond to Webhook**.
4. A API recebe o JSON do n8n e responde ao cliente no formato:

```json
{
  "status": "sucesso",
  "dados_enviados": {
    "mensagem": "não estou conseguindo gerar o boleto para pagar",
    "pergunta": "como posso resolver isso?"
  },
  "resultado_n8n": {
    "categoria": "financeiro",
    "prioridade": "alta",
    "resumo": "Dificuldade ao gerar boleto para pagamento"
  }
}
```

> O campo `categoria` do resultado permite que o próximo passo do fluxo (ex.: Switch/IF no n8n) encaminhe a mensagem ao setor correto — e-mail, Slack, planilha, CRM etc.

---

## 6. Como Executar

### 6.1 Pré-requisitos

| Item | Versão recomendada | Observação |
|---|---|---|
| **Python** | 3.11 ou superior | Necessário 3.10+ (o código usa a sintaxe `str \| None`) |
| **pip** | Atual | Vem junto com o Python |
| **Git** | Qualquer | Para clonar o repositório |
| **n8n** | 1.x / 2.x | Via Docker (recomendado) ou Node.js |
| **Docker** *(para o n8n)* | Atual | Opcional se rodar o n8n via `npx` |
| **Chave de API do Gemini** | — | Gerada gratuitamente no [Google AI Studio](https://aistudio.google.com/apikey) |

### 6.2 Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/n8n-gemini-orchestrator.git
cd n8n-gemini-orchestrator
```

### 6.3 Criar o ambiente virtual e instalar as dependências

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

> ⚠️ **Importante:** o `main.py` usa a biblioteca `requests` para chamar o n8n. Confirme que `requests` está listada no `requirements.txt`. Se não estiver, adicione:
>
> ```bash
> pip install requests
> ```
>
> O `requirements.txt` completo deve ficar assim:
>
> ```
> fastapi
> uvicorn
> requests
> pydantic
> python-dotenv
> google-genai
> ```
>
> (`google-genai` é opcional neste projeto, pois a chamada ao Gemini é feita pelo n8n.)

| Dependência | Função |
|---|---|
| `fastapi` | Framework da API |
| `uvicorn` | Servidor para executar a API |
| `requests` | Chamada HTTP ao webhook do n8n |
| `pydantic` | Validação dos dados de entrada |
| `python-dotenv` | Carrega o arquivo `.env` |
| `google-genai` | SDK do Gemini (disponível para usos futuros) |

### 6.4 Subir o n8n

**Opção A — Docker (recomendada):**

```bash
docker volume create n8n_data

docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```

**Opção B — Node.js (sem Docker):**

```bash
npx n8n
```

Depois, acesse **http://localhost:5678** e crie sua conta de administrador local (primeiro acesso).

### 6.5 Importar o fluxo no n8n

1. No n8n, clique em **Workflows → Import from File**.
2. Selecione o arquivo `workflow/workflow-n8n.json` deste repositório.
3. O fluxo será carregado com todos os nodes conectados.

### 6.6 Configurar a credencial do Gemini no n8n

> 🔑 A chave do Gemini fica **dentro do n8n** (cadastrada como *Credential*), e **não** no `.env` da API. Assim ela nunca vai para o GitHub.

1. Gere uma chave em [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. No n8n, abra o node de IA (Gemini) → **Credential to connect with → Create new credential**.
3. Cole a chave de API e salve.
4. Confirme que o prompt do node é o descrito na [seção 8](#8-prompt-estruturado).

### 6.7 Obter a URL do webhook

1. Abra o node **Webhook** no n8n.
2. Copie a URL conforme o modo de uso:

| Modo | URL | Quando usar |
|---|---|---|
| **Test URL** | `http://localhost:5678/webhook-test/<id>` | Durante o desenvolvimento. É preciso clicar em **Listen for test event** antes de cada envio. |
| **Production URL** | `http://localhost:5678/webhook/<id>` | Uso contínuo. O workflow precisa estar **Active** (toggle no canto superior). |

### 6.8 Configurar as variáveis de ambiente da API

Copie o arquivo de exemplo e edite:

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Conteúdo do `.env`:

```env
N8N_WEBHOOK_URL=http://localhost:5678/webhook-test/SEU-ID-DO-WEBHOOK
```

> O arquivo `.env` está no `.gitignore` e **nunca** deve ser enviado ao GitHub. Somente o `.env.example` é versionado.

### 6.9 Executar a API

Com o ambiente virtual ativo, na pasta do projeto:

```bash
uvicorn main:app --reload
```

A API ficará disponível em:

| Recurso | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger UI (documentação interativa) | http://localhost:8000/docs |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Health check | http://localhost:8000/health |

### 6.10 Testar o sistema

**Passo 1 — Verificar a API:**

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

**Passo 2 — Colocar o n8n para escutar** *(se estiver usando a Test URL)*: abra o workflow, clique no node **Webhook** → **Listen for test event**.

**Passo 3 — Enviar uma mensagem:**

*Pelo Swagger:* acesse http://localhost:8000/docs → `POST /processar` → **Try it out** → cole o JSON abaixo → **Execute**.

*Pelo terminal (curl):*

```bash
curl -X POST http://localhost:8000/processar \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "não estou conseguindo gerar o boleto para pagar", "pergunta": "como posso resolver isso?"}'
```

**Resposta esperada (HTTP 200):**

```json
{
  "status": "sucesso",
  "dados_enviados": {
    "mensagem": "não estou conseguindo gerar o boleto para pagar",
    "pergunta": "como posso resolver isso?"
  },
  "resultado_n8n": {
    "categoria": "financeiro",
    "prioridade": "alta",
    "resumo": "Dificuldade ao gerar boleto para pagamento"
  }
}
```

### 6.11 Como eu executei o projeto (passo a passo do desenvolvimento)

Esta é a ordem exata que segui durante o desenvolvimento e os testes:

1. **Subi o n8n localmente** na porta `5678` (`http://localhost:5678`).
2. **Criei o workflow** com os nodes: Webhook → Code in JavaScript (filtro) → Gemini → Code in JavaScript (parse) → Respond to Webhook.
3. **Configurei o Webhook** com método `POST` e a opção **Respond: Using 'Respond to Webhook' Node**.
4. **Testei o webhook isoladamente pelo Postman**, enviando um JSON de exemplo (`id`, `canal`, `mensagem`, `timestamp`) para a *Test URL*, com **Listen for test event** ativo. Isso permitiu ver a estrutura real dos dados recebidos pelo n8n (os campos úteis ficam dentro de `body`).
5. **Escrevi o primeiro node de código** para ler `body`, manter apenas os campos permitidos e gerar `dados_filtrados`.
6. **Escrevi o prompt** com regras, categorias, formato obrigatório e exemplos, usando `{{ JSON.stringify($json.dados_filtrados) }}` para injetar a mensagem.
7. **Escrevi o segundo node de código** para limpar crases de markdown e converter a resposta da IA em JSON.
8. **Criei a API FastAPI** (`main.py`) com validação via Pydantic e a variável `N8N_WEBHOOK_URL` lida do `.env`.
9. **Executei a API** com `uvicorn main:app --reload` (porta `8000`).
10. **Testei o sistema completo pelo Swagger** (`/docs`), enviando uma mensagem em `POST /processar` e conferindo o JSON classificado na resposta.

---

## 7. Documentação do Fluxo de Automação (prints)

> Todos os prints estão na pasta [`docs/images/`](docs/images/).

### 7.1 Fluxo completo

Visão geral do workflow no n8n, com todos os nodes conectados:

```
Webhook → Code in JavaScript (filtro) → Gemini → Code in JavaScript (parse) → Respond to Webhook
```

> 📸 **[PENDENTE — adicionar print]** `docs/images/00-fluxo-completo.png`
> *Captura de tela do canvas do n8n mostrando todos os nodes conectados.*
>
> Depois de adicionar o arquivo, descomente a linha abaixo:
>
> <!-- ![Fluxo completo](docs/images/00-fluxo-completo.png) -->

### 7.2 Execução bem-sucedida

> 📸 **[PENDENTE — adicionar print]** `docs/images/00-execucao-sucesso.png`
> *Captura de uma execução concluída com sucesso (todos os nodes com o check verde), na aba **Executions** ou no canvas logo após rodar o fluxo.*
>
> <!-- ![Execução bem-sucedida](docs/images/00-execucao-sucesso.png) -->

### 7.3 Configuração dos nodes

#### Node 1 — Webhook

**Função:** é a porta de entrada do fluxo. Recebe o `POST` enviado pela API FastAPI (ou pelo Postman, nos testes).

| Configuração | Valor |
|---|---|
| HTTP Method | `POST` |
| Path | identificador gerado pelo n8n (UUID) |
| Authentication | `None` |
| Respond | `Using 'Respond to Webhook' Node` |

A resposta só é enviada ao final do fluxo, pelo node **Respond to Webhook**, o que permite devolver o resultado da IA para quem chamou.

![Configuração do node Webhook](docs/images/01-webhook-config.png)

*Print do node Webhook. À direita (Output) aparece o dado recebido no teste via Postman: os campos enviados ficam dentro de `body` (`id`, `canal`, `mensagem`, `timestamp`), junto dos `headers` da requisição.*

#### Node 2 — Code in JavaScript (filtro de dados)

**Função:** limpar e padronizar os dados antes de enviá-los à IA.

| Configuração | Valor |
|---|---|
| Mode | `Run Once for All Items` |
| Language | `JavaScript` |

O que o código faz:

1. Lê o conteúdo recebido; se existir `body` (objeto), usa-o como carga útil (*payload*);
2. Mantém **apenas** os campos permitidos: `mensagem`, `pergunta`, `contexto`, `categoria`, `filtros`;
3. Aplica `trim()` nos textos (remove espaços nas pontas);
4. Descarta campos vazios (`null`, `undefined`, `""`, lista vazia ou objeto vazio);
5. Retorna tudo dentro de `dados_filtrados`.

![Node Code in JavaScript - filtro](docs/images/02-code-filtro-node.png)

*Print do node com **Input** (dado bruto do Webhook, à esquerda), o código (centro) e o **Output** (à direita) já filtrado: apenas `dados_filtrados.mensagem` segue adiante.*

Código completo do node:

![Código do node de filtro](docs/images/03-code-filtro-codigo.png)

```javascript
const items = $input.all();

return items.map((item) => {
  const dados = item.json || {};
  const payload =
    dados.body && typeof dados.body === "object" && !Array.isArray(dados.body)
      ? dados.body
      : dados;

  // Inclua "mensagem" (e os campos reais do seu POST)
  const camposPermitidos = ["mensagem", "pergunta", "contexto", "categoria", "filtros"];

  const filtrado = {};

  for (const chave of camposPermitidos) {
    if (!(chave in payload)) continue;

    let valor = payload[chave];

    if (typeof valor === "string") {
      valor = valor.trim();
    }

    const ehVazio =
      valor === null ||
      valor === undefined ||
      valor === "" ||
      (Array.isArray(valor) && valor.length === 0) ||
      (typeof valor === "object" &&
        !Array.isArray(valor) &&
        Object.keys(valor).length === 0);

    if (!ehVazio) {
      filtrado[chave] = valor;
    }
  }

  return {
    json: {
      dados_filtrados: filtrado,
    },
  };
});
```

#### Node 3 — Node de IA (Google Gemini)

**Função:** enviar o prompt estruturado ao modelo e receber a classificação.

| Configuração | Valor |
|---|---|
| Provedor | Google Gemini |
| Credencial | API Key do Google AI Studio (cadastrada no n8n) |
| Prompt | Ver [seção 8](#8-prompt-estruturado) |
| Entrada dinâmica | `{{ JSON.stringify($json.dados_filtrados) }}` |

> 📸 **[PENDENTE — adicionar print]** `docs/images/00-node-gemini.png`
> *Captura do node de IA aberto, mostrando o modelo escolhido, o prompt e o Output com a resposta do Gemini.*
>
> <!-- ![Node Gemini](docs/images/00-node-gemini.png) -->

#### Node 4 — Code in JavaScript (tratamento do JSON da IA)

**Função:** garantir que a resposta da IA seja um JSON válido e utilizável.

O que o código faz:

1. Lê o texto gerado pelo modelo (`content.parts[0].text`, ou `text` como alternativa);
2. Remove eventuais blocos de markdown (` ```json ` e ` ``` `);
3. Aplica `JSON.parse` e devolve o objeto;
4. Se o parse falhar, devolve `{ erro, raw }` em vez de interromper o fluxo.

![Código do node de parse do JSON](docs/images/04-code-parse-json-codigo.png)

```javascript
const items = $input.all();

return items.map((item) => {
  const rawText =
    item.json?.content?.parts?.[0]?.text ??
    item.json?.text ??
    "";

  // Remove eventuais crases de markdown caso apareçam
  const limpo = String(rawText)
    .replace(/^```json\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();

  try {
    const parsed = JSON.parse(limpo);
    return { json: parsed };
  } catch (err) {
    return {
      json: {
        erro: "Falha ao parsear JSON do modelo",
        raw: rawText,
      },
    };
  }
});
```

#### Node 5 — Respond to Webhook

**Função:** devolver o JSON final (`categoria`, `prioridade`, `resumo`) para quem chamou o webhook — no caso, a API FastAPI.

> 📸 **[PENDENTE — adicionar print]** `docs/images/00-node-respond-webhook.png`
> *Captura do node Respond to Webhook com sua configuração e o dado de saída.*
>
> <!-- ![Node Respond to Webhook](docs/images/00-node-respond-webhook.png) -->

### 7.4 Resultados

#### Entrada: requisição enviada à API (Swagger)

Teste do endpoint `POST /processar` no Swagger UI, com o corpo:

```json
{
  "mensagem": "não estou conseguindo gerar o boleto para pagar",
  "pergunta": "como posso resolver isso?"
}
```

![Requisição no Swagger](docs/images/05-swagger-requisicao.png)

#### Saída: resposta classificada pela IA

A API respondeu com **HTTP 200**, devolvendo os dados enviados e o resultado do n8n já classificado pela IA:

![Resposta no Swagger](docs/images/06-swagger-resposta.png)

```json
{
  "status": "sucesso",
  "dados_enviados": {
    "mensagem": "não estou conseguindo gerar o boleto para pagar",
    "pergunta": "como posso resolver isso?"
  },
  "resultado_n8n": {
    "categoria": "financeiro",
    "prioridade": "alta",
    "resumo": "Dificuldade ao gerar boleto para pagamento"
  }
}
```

#### Mais um exemplo de entrada (teste via Postman no Webhook)

Mensagem usada para testar o webhook diretamente:

```json
{
  "id": "msg-9842",
  "canal": "whatsapp",
  "mensagem": "Boa tarde! Não estou conseguindo acessar a minha conta e os emails não estão sendo enviados.",
  "timestamp": "2026-11-23T23:20:00-03:00"
}
```

Nesse caso, o node de filtro mantém somente o campo `mensagem` (os demais não estão na lista de campos permitidos), como mostrado no print do **Node 2**.

#### Resumo do caminho dos dados

| Etapa | Dado |
|---|---|
| Entrada na API | `{ "mensagem": "...", "pergunta": "..." }` |
| Após o Webhook | Objeto com `headers`, `params`, `query`, `body` |
| Após o filtro | `{ "dados_filtrados": { "mensagem": "..." } }` |
| Após a IA | Texto com JSON (`content.parts[0].text`) |
| Após o parse | `{ "categoria": "...", "prioridade": "...", "resumo": "..." }` |
| Resposta final da API | `{ "status": "sucesso", "dados_enviados": {...}, "resultado_n8n": {...} }` |

---

## 8. Prompt Estruturado

O prompt usa quatro técnicas de engenharia de prompt: **definição de papel**, **restrição de formato**, **lista fechada de valores** e **exemplos (few-shot)**.

```text
Você é um classificador de mensagens. Analise a mensagem recebida e classifique-a em apenas UMA das categorias permitidas: "suporte", "vendas", "financeiro" ou "outros".

Responda EXCLUSIVAMENTE com um objeto JSON válido, sem texto adicional, sem explicações e sem blocos de markdown (```).

Formato obrigatório:

{"categoria": "string", "prioridade": "baixa|media|alta", "resumo": "string curta"}

Exemplos:

Mensagem: "Oi, quanto custa o plano mensal para 10 usuários?"

Resposta: {"categoria": "vendas", "prioridade": "media", "resumo": "Consulta de preço para plano de 10 usuários"}

Mensagem: "O sistema está fora do ar desde cedo e não consigo acessar minha conta."

Resposta: {"categoria": "suporte", "prioridade": "alta", "resumo": "Sistema fora do ar impedindo acesso à conta"}

Mensagem: "Preciso da segunda via do boleto que venceu ontem."

Resposta: {"categoria": "financeiro", "prioridade": "media", "resumo": "Solicitação de segunda via de boleto vencido"}

Mensagem: "Obrigado pelo atendimento de ontem!"

Resposta: {"categoria": "outros", "prioridade": "baixa", "resumo": "Agradecimento pelo atendimento"}

Agora classifique a mensagem abaixo:

Mensagem: "{{ JSON.stringify($json.dados_filtrados) }}

Resposta:
```

### Por que o prompt foi escrito assim?

| Trecho | Objetivo |
|---|---|
| "Você é um classificador de mensagens" | Define o papel da IA |
| Categorias entre aspas e lista fechada | Evita categorias inventadas e facilita o roteamento |
| "Responda EXCLUSIVAMENTE com JSON válido" | Garante saída estruturada, fácil de processar |
| Formato obrigatório | Mostra exatamente as chaves e valores esperados |
| 4 exemplos (um por categoria) | Ensinam o padrão esperado, incluindo a variação de prioridade |
| `{{ JSON.stringify($json.dados_filtrados) }}` | Injeta, de forma dinâmica, os dados já filtrados pelo node anterior |

---

## 9. Estrutura do Repositório

```
n8n-gemini-orchestrator/
├── main.py                       # API FastAPI (endpoints /health e /processar)
├── requirements.txt              # Dependências Python
├── .env.example                  # Modelo das variáveis de ambiente (sem credenciais)
├── .gitignore                    # Ignora .env, venv/ e __pycache__/
├── LICENSE                       # Licença MIT
├── README.md                     # Este arquivo
├── workflow/
│   └── workflow-n8n.json         # Fluxo do n8n exportado
└── docs/
    └── images/                   # Prints da automação
        ├── 01-webhook-config.png
        ├── 02-code-filtro-node.png
        ├── 03-code-filtro-codigo.png
        ├── 04-code-parse-json-codigo.png
        ├── 05-swagger-requisicao.png
        └── 06-swagger-resposta.png
```

### Como exportar o fluxo do n8n (JSON)

1. Abra o workflow no n8n.
2. Menu **⋯** (canto superior direito) → **Download**.
3. Salve o arquivo como `workflow/workflow-n8n.json` na raiz do repositório.

> ⚠️ Antes de publicar, abra o JSON e confirme que **não há chaves de API** dentro dele. As credenciais do n8n são guardadas separadamente, mas vale conferir.

---

## 10. Segurança e Credenciais

- ✅ **Nenhuma chave de API, senha ou token é publicado** neste repositório.
- ✅ A chave do Gemini fica cadastrada como *Credential* **dentro do n8n**.
- ✅ A API lê a URL do webhook pela variável de ambiente `N8N_WEBHOOK_URL`, definida no arquivo `.env`.
- ✅ O `.env` está no `.gitignore`; apenas o `.env.example` (com o nome das variáveis, sem valores reais) vai para o GitHub.

Arquivo `.env.example`:

```env
N8N_WEBHOOK_URL=YOUR_N8N_URL_HERE
```

> 💡 Dica: confirme que o `.gitignore` também ignora o cache do Python, adicionando a linha `__pycache__/`.

---

## 11. Solução de Problemas

| Sintoma | Causa provável | Como resolver |
|---|---|---|
| `ModuleNotFoundError: No module named 'requests'` | `requests` não instalada | `pip install requests` |
| `ModuleNotFoundError: No module named 'fastapi'` | Ambiente virtual não ativado / dependências não instaladas | Ative o `venv` e rode `pip install -r requirements.txt` |
| `500 — Variável N8N_WEBHOOK_URL não configurada` | `.env` ausente ou vazio | Crie o `.env` a partir do `.env.example` e reinicie a API |
| `502 — Erro de comunicação com o webhook do n8n` | n8n desligado, URL errada ou n8n respondendo erro (ex.: `404`) | Verifique se o n8n está no ar e se a URL está correta |
| `404` ao chamar a *Test URL* | O n8n não está "escutando" | Clique em **Listen for test event** no node Webhook antes de enviar |
| `404` ao chamar a *Production URL* | Workflow inativo | Ative o workflow (toggle **Active**) |
| `504 — Tempo limite excedido` | O fluxo (ou o Gemini) demorou mais de 30 s | Tente novamente; verifique a credencial e a conexão |
| `resultado_n8n` com `"erro": "Falha ao parsear JSON do modelo"` | O Gemini devolveu um texto que não é JSON | Veja o campo `raw`; reforce as instruções do prompt |
| Erro de credencial no node do Gemini | Chave de API inválida ou não configurada | Recrie a credencial com uma chave válida do Google AI Studio |
| Alterei o `.env` e nada mudou | A API carrega o `.env` somente ao iniciar | Reinicie o `uvicorn` |

---

## 12. Melhorias Futuras

- 🐳 **Docker:** criar `Dockerfile` da API e `docker-compose.yml` para subir API + n8n com um único comando.
- 🔀 **Roteamento real:** adicionar um node **Switch** após a IA para encaminhar cada categoria ao setor correspondente (e-mail, Slack, Google Sheets, CRM).
- 🚨 **Alertas:** notificar automaticamente quando a prioridade for `alta`.
- 🔐 **Autenticação:** proteger o webhook (Header Auth) e a API (API Key).
- ✅ **Validação:** validar no n8n se `categoria` e `prioridade` pertencem às listas permitidas.
- 🧪 **Testes automatizados** com `pytest` para a API.

---

## 13. Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">
  Desenvolvido por <strong>Luan Missel</strong> • KODIE — Desafio Técnico de IA e Automação
</p>
