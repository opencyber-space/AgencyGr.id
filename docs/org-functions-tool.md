# Org Tools Executor – Introduction

**Org Tools Executor** is a service framework built to register, manage, and execute modular **tool components** within the org. These tools can be binary executables, scripts, or containerized components that perform specific functions.

This system provides:

* A structured format to **register and store tools** in a backend data store.
* A **WebSocket-based interface** for submitting tool execution requests and receiving results asynchronously.
* A **RESTful API** for tool lifecycle management: create, update, delete, query, and register tools from external sources.
* A **queue-based task executor** that decouples tool execution from client interaction, supporting scalable asynchronous processing.

---

## Tool Schema

### `OrgTools` Data Class

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class OrgTools:
    tool_id: str = ''
    tool_search_tags: List[str] = field(default_factory=list)
    tool_metadata: Dict[str, Any] = field(default_factory=dict)
    tool_description: str = ''
    tool_default_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgTools":
        return cls(
            tool_id=data.get("tool_id", ""),
            tool_search_tags=data.get("tool_tags", []),
            tool_metadata=data.get("tool_metadata", {}),
            tool_description=data.get("tool_description", ""),
            tool_default_params=data.get("tool_default_params", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "tool_search_tags": self.tool_search_tags,
            "tool_metadata": self.tool_metadata,
            "tool_description": self.tool_description,
            "tool_default_params": self.tool_default_params
        }
```

| Field Name            | Type             | Description                                                |
| --------------------- | ---------------- | ---------------------------------------------------------- |
| `tool_id`             | `str`            | Unique identifier for the tool.                            |
| `tool_search_tags`    | `List[str]`      | Tags for categorizing the tool.                            |
| `tool_metadata`       | `Dict[str, Any]` | Metadata such as input/output schema, source URL, runtime. |
| `tool_description`    | `str`            | A description of the tool’s purpose.                       |
| `tool_default_params` | `Dict[str, Any]` | Default configuration or parameters for the tool.          |

---

## REST APIs

### API: Create Tool

**Endpoint**: `POST /tool`
**Description**: Registers a new tool.

#### cURL Example

```bash
curl -X POST http://localhost:8000/tool \
     -H "Content-Type: application/json" \
     -d @tool.json
```

---

### API: Get Tool by ID

**Endpoint**: `GET /tool/<tool_id>`
**Description**: Retrieves a tool’s details by its ID.

#### cURL Example

```bash
curl http://localhost:8000/tool/binary-increment-tool
```

---

### API: Update Tool

**Endpoint**: `PUT /tool/<tool_id>`
**Description**: Updates metadata for an existing tool.

#### cURL Example

```bash
curl -X PUT http://localhost:8000/tool/binary-increment-tool \
     -H "Content-Type: application/json" \
     -d '{"tool_description": "Updated description"}'
```

---

### API: Delete Tool

**Endpoint**: `DELETE /tool/<tool_id>`
**Description**: Deletes a tool by its ID.

#### cURL Example

```bash
curl -X DELETE http://localhost:8000/tool/binary-increment-tool
```

---

### API: Query Tools

**Endpoint**: `POST /tools`
**Description**: Query tools using filters.

#### Request Example

```json
{
  "tool_search_tags": { "$in": ["math", "utils"] }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/tools \
     -H "Content-Type: application/json" \
     -d '{"tool_search_tags": {"$in": ["math", "utils"]}}'
```

---

### API: Register Tool from External Source

**Endpoint**: `POST /tool/register/<tool_id>`
**Description**: Fetches tool metadata from an external registry and stores it.

#### cURL Example

```bash
curl -X POST http://localhost:8000/tool/register/binary-increment-tool
```

---

## WebSocket Server

Org Tools Executor includes a WebSocket interface to support real-time execution of tool components.

---

### WebSocket Endpoint

**URL**: `ws://<host>:8765/tool`
**Protocol**: WebSocket

---

### Request Format (JSON)

```json
{
  "tool_id": "binary-increment-tool",
  "input_data": {
    "value": 5
  }
}
```

| Field        | Type     | Description                             |
| ------------ | -------- | --------------------------------------- |
| `tool_id`    | `string` | ID of the tool to execute               |
| `input_data` | `object` | Parameters to provide to the tool input |

---

### Response Format (on Acceptance)

```json
{
  "success": true,
  "uuid": "0f97f33c-5ea4-451e-98cd-4b746cb38c21"
}
```

---

### Response Format (on Completion)

```json
{
  "success": true,
  "output": {
    "result": 6
  }
}
```

---

### Response Format (on Error)

```json
{
  "success": false,
  "error": "Tool not registered"
}
```

---

### Python WebSocket Client Example

```python
import asyncio
import websockets
import json

async def run_tool():
    uri = "ws://localhost:8765/tool"
    async with websockets.connect(uri) as websocket:
        request_payload = {
            "tool_id": "binary-increment-tool",
            "input_data": { "value": 5 }
        }

        await websocket.send(json.dumps(request_payload))

        while True:
            response = await websocket.recv()
            response_data = json.loads(response)
            print("Response:", response_data)

            if "output" in response_data or "error" in response_data:
                break

asyncio.run(run_tool())
```

---

### Execution Lifecycle

1. Client submits a WebSocket request with `tool_id` and input.
2. Server validates the tool and enqueues the task.
3. A UUID is returned immediately.
4. The result is pushed back to the client on the same WebSocket connection.
5. The connection closes after delivering the result or error.

---

# Org Functions Executor – Introduction

**Org Functions Executor** is a microservice framework designed to register, manage, and execute function-based modules that encapsulate reusable business or computational logic. These functions are versioned, typed, and can be executed either locally or via APIs.

This system provides:

* A structured format to **register and persist functions** in a backend datastore.
* A **WebSocket interface** for asynchronous function execution with real-time response delivery.
* A **RESTful API suite** for full lifecycle management: create, update, delete, query, and register external functions.
* A **queue-based task processor** to decouple client requests from backend execution, enabling horizontal scalability.

---

## Function Schema

### `OrgFunctions` Data Class

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class OrgFunctions:
    function_id: str = ''
    function_search_tags: List[str] = field(default_factory=list)
    function_metadata: Dict[str, Any] = field(default_factory=dict)
    function_description: str = ''
    function_default_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgFunctions":
        return cls(
            function_id=data.get("function_id", ""),
            function_search_tags=data.get("function_tags", []),
            function_metadata=data.get("function_metadata", {}),
            function_description=data.get("function_description", ""),
            function_default_params=data.get("function_default_params", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_id": self.function_id,
            "function_search_tags": self.function_search_tags,
            "function_metadata": self.function_metadata,
            "function_description": self.function_description,
            "function_default_params": self.function_default_params
        }
```

| Field Name                | Type             | Description                                              |
| ------------------------- | ---------------- | -------------------------------------------------------- |
| `function_id`             | `str`            | Unique identifier (e.g., `weather_lookup:v1.0.0-stable`) |
| `function_search_tags`    | `List[str]`      | Keywords to classify and search functions                |
| `function_metadata`       | `Dict[str, Any]` | Version, protocol, API spec, type, subtype, URL, etc.    |
| `function_description`    | `str`            | Describes what the function does                         |
| `function_default_params` | `Dict[str, Any]` | Optional defaults passed on invocation                   |

---

## REST APIs

### API: Create Function

**Endpoint**: `POST /function`
**Description**: Registers a new function in the local registry.

#### cURL Example

```bash
curl -X POST http://localhost:8000/function \
     -H "Content-Type: application/json" \
     -d @function.json
```

---

### API: Get Function by ID

**Endpoint**: `GET /function/<function_id>`
**Description**: Retrieves the function definition for a given ID.

#### cURL Example

```bash
curl http://localhost:8000/function/weather_lookup:v1.0.0-stable
```

---

### API: Update Function

**Endpoint**: `PUT /function/<function_id>`
**Description**: Updates the stored metadata or parameters for a function.

#### cURL Example

```bash
curl -X PUT http://localhost:8000/function/weather_lookup:v1.0.0-stable \
     -H "Content-Type: application/json" \
     -d '{"function_description": "Updated version with better accuracy"}'
```

---

### API: Delete Function

**Endpoint**: `DELETE /function/<function_id>`
**Description**: Removes a function definition from the local store.

#### cURL Example

```bash
curl -X DELETE http://localhost:8000/function/weather_lookup:v1.0.0-stable
```

---

### API: Query Functions

**Endpoint**: `POST /functions`
**Description**: Query functions based on filters.

#### Request Body Example

```json
{
  "function_search_tags": { "$in": ["weather", "location"] }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/functions \
     -H "Content-Type: application/json" \
     -d '{"function_search_tags": {"$in": ["weather"]}}'
```

---

### API: Register Function from External Source

**Endpoint**: `POST /function/register/<function_id>`
**Description**: Imports a function’s metadata from an external service (e.g., function registry).

#### cURL Example

```bash
curl -X POST http://localhost:8000/function/register/weather_lookup:v1.0.0-stable
```

---

## WebSocket Server

The WebSocket interface supports real-time execution of registered functions. Clients submit a request and receive output on the same connection.

---

### WebSocket Endpoint

**URL**: `ws://<host>:8765/function`
**Protocol**: WebSocket

---

### Request Format (JSON)

```json
{
  "function_id": "weather_lookup:v1.0.0-stable",
  "input_data": {
    "city": "Delhi"
  }
}
```

| Field         | Type     | Description                               |
| ------------- | -------- | ----------------------------------------- |
| `function_id` | `string` | ID of the function to invoke              |
| `input_data`  | `object` | JSON payload passed to the function logic |

---

### Response Format (on Acceptance)

```json
{
  "success": true,
  "uuid": "c6b4b8e5-7fd2-49f3-bf3b-91c82e5e0de5"
}
```

---

### Response Format (on Completion)

```json
{
  "success": true,
  "output": {
    "temperature": 28,
    "unit": "C"
  }
}
```

---

### Response Format (on Error)

```json
{
  "success": false,
  "error": "Function not registered"
}
```

---

### Python WebSocket Client Example

```python
import asyncio
import websockets
import json

async def run_function():
    uri = "ws://localhost:8765/function"
    async with websockets.connect(uri) as websocket:
        request_payload = {
            "function_id": "weather_lookup:v1.0.0-stable",
            "input_data": { "city": "Delhi" }
        }

        await websocket.send(json.dumps(request_payload))

        while True:
            response = await websocket.recv()
            response_data = json.loads(response)
            print("Response:", response_data)

            if "output" in response_data or "error" in response_data:
                break

asyncio.run(run_function())
```

---

### Execution Lifecycle

1. Client sends a function execution request over WebSocket.
2. The server:

   * Validates the `function_id`.
   * Assigns a UUID.
   * Enqueues the task for background execution.
3. The result is pushed back over the same WebSocket connection.
4. The socket closes once the response is sent.

---
