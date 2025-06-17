# Org APIs gateway

## Introduction

The **ORG Role Access Control System** is a pluggable authorization and constraint validation framework designed to operate as a middleware layer in distributed API or message-based infrastructures.

This system enforces **fine-grained access control** and **dynamic policy constraints** based on role associations and DSL-based logic. It is ideal for environments where routes must be restricted based on organizational roles, group memberships, and runtime-validated conditions.

The architecture is modular, caching-aware, and designed for extensibility — integrating with REST APIs, message brokers, and policy execution systems.

### Key Features

* **Route-Level Access Control**: Every API or message route can be associated with role/group mappings to restrict access.
* **Constraint Execution Engine**: Dynamically evaluates constraint logic using a DSL workflow for each request.
* **Hybrid Cache + DB**: High-performance Redis cache with MongoDB fallback ensures both speed and persistence.
* **Reverse Proxy Enforcement**: Middleware intercepts all incoming requests and enforces validation before forwarding to backend services.
* **Admin APIs**: Internal APIs to manage cache, role associations, and constraints in real-time.
* **Service-Aware Routing**: Reverse proxy dynamically resolves destination services based on route prefix mapping.

---

## Architecture

The ORG Role Access Control System is designed as a modular middleware layer that intercepts and validates all incoming REST or message-based requests before they reach backend services. It combines a role-based access mechanism with a dynamic constraint evaluation engine and forwards only valid requests to their respective destinations.

![org-gateway](../images/org-gateway.png)

The system is composed of the following key layers:

### 1. API Gateway

Acts as the main entry point for all HTTP traffic. Requests are routed to this component, which applies access rules and constraint validation before forwarding.

* Supports all HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`)
* Compatible with both internal systems and external clients
* Mounted on a reverse proxy that maps incoming routes to backend services

---

### 2. Reverse Proxy Input Module

This component handles:

* Extraction of metadata like `api_route` and `subject_id`
* Validation of the request using constraint maps and role associations
* Delegation to the output module if the request is authorized

---

### 3. Constraint Evaluation Layer

The core logic engine that:

* Loads constraints based on the `message_type` and `dsl_workflow_id`
* Executes the corresponding DSL logic using `ConstraintsManager`
* Allows or blocks requests based on runtime evaluation

Constraints are reusable and loaded once per `message_type` to optimize performance.

---

### 4. Redis Access Cache

Provides fast in-memory lookups for:

* Route-to-role and group mappings
* Constraint execution metadata

Cache entries are initialized from MongoDB and can be managed dynamically through internal APIs. This drastically reduces the need to access the database for every request.

---

### 5. MongoDB Data Store

Persistent storage for:

* Role association tables (`api_route ➝ role_id, group_id`)
* Constraint mappings (`api_route ➝ DSL metadata`)

The database is used to initialize the cache and for any cache miss fallback. All CRUD operations are exposed via secure internal APIs.

---

### 6. Reverse Proxy Output Module

Responsible for forwarding validated requests to the appropriate backend service. The mapping of route prefixes to service URLs is managed via a runtime environment variable (`SERVICE_MAP_JSON`).

* Mimics the original request in terms of headers, method, body, and query string
* Supports flexible multi-service routing based on prefix matching

---

### 7. Cache Manager

Provides a control interface to:

* Initialize the Redis cache from DB
* Flush or refresh cache entries
* Delete or reload route-specific cache data

This is typically used by internal systems or admin users.

---

### 8. Management APIs

All management functions (for both DB and cache) are exposed via `/internal/db/` and `/internal/cache/` routes, supporting:

* Create, update, and delete role associations and constraints
* Flush and refresh the cache
* Per-route cache control

---

### 9. DSL Executor Integration

The constraint system is extensible and integrates with a custom DSL execution engine that allows for complex logic evaluation during runtime. This makes the system ideal for rule-governed environments like organizational workflows, multi-tenant systems, and AI policy enforcement.

---

### Service Communication

| Component           | Communicates With             | Purpose                             |
| ------------------- | ----------------------------- | ----------------------------------- |
| API Gateway         | Reverse Proxy Input Module    | Handles request routing and parsing |
| Input Module        | Redis, Constraints Checker    | Validates route and subject         |
| Constraints Checker | ConstraintsManager, Redis, DB | Loads/evaluates logic               |
| Output Module       | Backend Services              | Forwards validated request          |
| Cache Manager       | Redis, MongoDB                | Admin operations                    |


---

## Schema

The ORG Role Access Control System uses two primary data models stored in MongoDB and cached in Redis for fast access:


### `APIRoleAssociation`

#### Data Class

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class APIRoleAssociation:
    api_route: str
    role_id: str
    group_id: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "APIRoleAssociation":
        return APIRoleAssociation(
            api_route=data.get("api_route", ""),
            role_id=data.get("role_id", ""),
            group_id=data.get("group_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_route": self.api_route,
            "role_id": self.role_id,
            "group_id": self.group_id
        }
```

#### Field Descriptions

| Field       | Type  | Description                                               |
| ----------- | ----- | --------------------------------------------------------- |
| `api_route` | `str` | The API or message route path (e.g., `/service-a/task`)   |
| `role_id`   | `str` | The ID of the role required to access the route           |
| `group_id`  | `str` | The ID of the group this route or role is associated with |

---

### `APIConstraintMap`

#### Data Class

```python
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class APIConstraintMap:
    api_route: str
    constraints_map: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "APIConstraintMap":
        return APIConstraintMap(
            api_route=data.get("api_route", ""),
            constraints_map=data.get("constraints_map", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_route": self.api_route,
            "constraints_map": self.constraints_map
        }
```

#### Field Descriptions

| Field             | Type             | Description                                                        |
| ----------------- | ---------------- | ------------------------------------------------------------------ |
| `api_route`       | `str`            | The route this constraint applies to (same as in role association) |
| `constraints_map` | `Dict[str, Any]` | DSL metadata used to evaluate constraints dynamically              |

---

### Example `constraints_map` Structure

```json
{
  "message_type": "task.submit",
  "dsl_workflow_id": "validate-submission-logic"
}
```

| Key               | Description                                                 |
| ----------------- | ----------------------------------------------------------- |
| `message_type`    | A unique name representing what type of constraint to load  |
| `dsl_workflow_id` | Identifier used to locate the associated DSL logic workflow |

---

## Create, Update, and Delete APIs

These internal REST APIs allow administrators to manage database records for:

* Role-to-route associations (`APIRoleAssociation`)
* Constraint logic bindings for routes (`APIConstraintMap`)

All routes are prefixed under `/internal/db/`.

---

### 1. Create Role Association

**Endpoint:** `POST /internal/db/role-association`
**Description:** Create a new API route-to-role mapping.

#### Request Body

```json
{
  "api_route": "/service-a/task",
  "role_id": "admin",
  "group_id": "org-1"
}
```

#### Response

```json
{
  "status": "created",
  "api_route": "/service-a/task"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/internal/db/role-association \
  -H "Content-Type: application/json" \
  -d '{
        "api_route": "/service-a/task",
        "role_id": "admin",
        "group_id": "org-1"
      }'
```

---

### 2. Update Role Association

**Endpoint:** `PUT /internal/db/role-association/<api_route>`
**Description:** Update role or group for a given route.

#### Request Body

```json
{
  "role_id": "superadmin"
}
```

#### Response

```json
{
  "status": "updated"
}
```

---

### 3. Delete Role Association

**Endpoint:** `DELETE /internal/db/role-association/<api_route>`
**Description:** Delete a route-to-role mapping.

#### Response

```json
{
  "status": "deleted"
}
```

---

### 4. Create Constraint Map

**Endpoint:** `POST /internal/db/constraint`
**Description:** Create a constraint logic binding for a route.

#### Request Body

```json
{
  "api_route": "/service-a/task",
  "constraints_map": {
    "message_type": "task.submit",
    "dsl_workflow_id": "submission-check"
  }
}
```

#### Response

```json
{
  "status": "created",
  "api_route": "/service-a/task"
}
```

---

### 5. Update Constraint Map

**Endpoint:** `PUT /internal/db/constraint/<api_route>`
**Description:** Update the constraint logic for an existing route.

#### Request Body

```json
{
  "constraints_map": {
    "message_type": "task.submit",
    "dsl_workflow_id": "submission-check-v2"
  }
}
```

#### Response

```json
{
  "status": "updated"
}
```

---

### 6. Delete Constraint Map

**Endpoint:** `DELETE /internal/db/constraint/<api_route>`
**Description:** Remove the constraint logic for a given route.

#### Response

```json
{
  "status": "deleted"
}
```

---

## Cache Management APIs

These endpoints are available under the `/internal/cache/` prefix and provide control over Redis caching behavior. They support initialization, flushing, and per-route cache control.

---

### 1. Initialize Cache

**Endpoint:** `POST /internal/cache/init`
**Description:** Load all route-role associations and constraints from the database into Redis cache.

#### Response

```json
{
  "status": "Cache initialized from DB"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/internal/cache/init
```

---

### 2. Flush Entire Cache

**Endpoint:** `POST /internal/cache/flush`
**Description:** Clears all cache entries related to role associations and constraints.

#### Response

```json
{
  "status": "Cache flushed"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/internal/cache/flush
```

---

### 3. Refresh Cache for Specific Route

**Endpoint:** `POST /internal/cache/refresh/<api_route>`
**Description:** Refresh the role association and constraint entries in cache for a specific route. Uses data from the database.

#### Response

```json
{
  "status": "Cache refreshed for /service-a/task"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/internal/cache/refresh/service-a/task
```

---

### 4. Delete Cache for Specific Route

**Endpoint:** `POST /internal/cache/delete/<api_route>`
**Description:** Remove only the cache entries for the given route (both role and constraint mappings).

#### Response

```json
{
  "status": "Cache deleted for /service-a/task"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:5000/internal/cache/delete/service-a/task
```

---

## Proxy Usage Guide

This section explains how the Reverse Proxy mechanism works in conjunction with the constraint engine and access control cache. The proxy acts as a secure middleware layer that forwards only validated requests to backend services, such as the `roles-system`.

---

### How It Works

1. A request arrives at the **API Gateway** (e.g., `/roles-system/apply-role`)
2. The proxy:

   * Extracts the route and subject ID
   * Validates access using the role association and constraint map
3. If the request passes validation, it is **forwarded to the actual service** (e.g., `http://roles-service:5001/apply-role`)
4. If validation fails, the request is blocked with a `403 Forbidden` error.

---

### Environment Variable: `SERVICE_MAP_JSON`

To route requests correctly, the system relies on a service mapping configured via an environment variable.

#### Example

```bash
export SERVICE_MAP_JSON='{
  "/roles-system": "http://roles-service:5001"
}'
```

This maps all requests beginning with `/roles-system` to the internal service `roles-service`.

---

### Request Format

* `subject_id` must be included either:

  * As a header: `X-Subject-ID`
  * Or in the JSON body: `{ "subject_id": "..." }`

The proxy extracts this value and applies access rules and constraints.

---

### Example Request

Assume the route `/roles-system/apply-role` is protected and validated by the proxy.

#### Request

```bash
curl -X POST http://gateway-host:5000/roles-system/apply-role \
  -H "Content-Type: application/json" \
  -H "X-Subject-ID: user-123" \
  -d '{
        
      }'
```

* The proxy will:

  * Match `/roles-system` to `http://roles-service:5001`
  * Validate access and constraints for the route `/roles-system/apply-role`
  * Forward the request if allowed

---

### Error Responses

If a constraint fails or the user is unauthorized:

#### Response

```json
{
  "error": "Request blocked by constraint",
  "details": "Role 'viewer' not permitted to apply-role"
}
```

If `subject_id` is missing:

```json
{
  "error": "Missing subject_id"
}
```

---

### Notes

* The proxy performs longest-prefix matching to resolve destination services
* All HTTP methods (`GET`, `POST`, `PUT`, `DELETE`) are supported
* Headers, query parameters, and body are preserved in forwarding

---
