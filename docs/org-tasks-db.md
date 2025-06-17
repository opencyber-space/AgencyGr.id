# Org Tasks DB – Introduction

**Org Tasks DB** is a MongoDB-backed system that stores and manages the lifecycle of complex organizational tasks and their associated entities. It provides a structured, scalable, and extensible API interface for interacting with various task-related data models.

This system is designed to support modular, multi-stage, and verifiable task execution in distributed environments. It is particularly suitable for platforms where:

* Tasks must be broken down into sub-tasks
* Task inputs, outputs, and behaviors need to be defined or templated
* Verification, access control, and audit logging are essential
* Subjects (agents, users, services) are involved in task assignment and review

---

#### Core Functionalities

The system supports:

* **Task creation and intent registration**
* **Sub-task decomposition and tracking**
* **Output management for tasks and sub-tasks**
* **Status updates and verification logs**
* **Access control enforcement via ACL maps**
* **Review workflows involving designated reviewers**
* **Structured query APIs for filtered retrieval**

---

## Architecture

The **Org Tasks System** is designed to manage the lifecycle of tasks and sub-tasks within a distributed organizational framework. It handles task definition, execution tracking, access control, output management, and live log streaming. The architecture integrates a structured data schema with event-driven updates and real-time logging to support complex, multi-actor task flows.

![org-tasks-db](../images/org-tasks-db.png)


### System Overview

At its core, the system consists of a **Tasks DB** backed by multiple structured tables capturing every aspect of task processing — from submission to execution and review. Supporting this persistence layer is a service orchestration module that manages querying, status tracking, and WebSocket-based log streaming. The system exposes public APIs for status queries and publishes status-change events for downstream consumers.

---

### Core Components

| Component                     | Description                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **task\_entry\_table**        | Stores metadata about each task, including intent, priority, DSLs, contracts, and the submitting subject.          |
| **sub\_task\_entry\_table**   | Represents finer-grained sub-tasks, linked to parent tasks, with independent execution and behavior configuration. |
| **task\_status\_table**       | Tracks the real-time status and update timestamp of each task. Supports log streaming via WebSocket pointers.      |
| **sub\_task\_status\_table**  | Mirrors `task_status_table` for sub-tasks, enabling isolated tracking.                                             |
| **task\_outputs\_table**      | Defines output streams and data pointers for completed tasks.                                                      |
| **sub\_task\_outputs\_table** | Stores output-related metadata and subject-level output references for sub-tasks.                                  |
| **task\_acl\_mapping**        | Encodes access control by specifying allowed functions, tools, actions, and credentials tied to task execution.    |
| **task\_review\_data**        | Captures review information from designated subjects for post-execution evaluation of a task.                      |
| **sub\_task\_review\_data**   | Review metadata for sub-tasks, supporting granular feedback collection.                                            |

---

### Runtime Service Modules

| Module                       | Description                                                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **DB Query Module**          | Interfaces with the Tasks DB to handle read operations for task status, ACLs, outputs, and review data.            |
| **Query Controller**         | Entry point for task status query API; accepts textual queries and invokes the appropriate database routines.      |
| **Status Change Listener**   | Monitors database updates to detect changes in task or sub-task status, and forwards events to downstream systems. |
| **Task Status Event Pusher** | Pushes detected task status updates to external systems or dashboards in real-time.                                |
| **Logging Connector**        | Establishes WebSocket connections for log streaming by retrieving the corresponding logging channel for a task.    |
| **Logs Streaming Server**    | Facilitates real-time streaming of task execution logs to clients via WebSocket.                                   |

---


## Schema

### 1. `TaskEntry`

```python
@dataclass
class TaskEntry:
    task_id: str
    task_goal: str
    task_intent: str
    task_priority_value: int
    task_streeability_data: Dict[str, Any]
    task_knowledgebase_ptr: Optional[str]
    submitter_subject_id: str
    task_op_convertor_dsl_id: Optional[str]
    task_execution_dsl: Optional[str]
    task_submission_ts: str
    task_completion_timeline: Dict[str, Any]
    task_execution_mode: str
    task_behavior_dsl_map: Dict[str, Any]
    task_contracts_map: Dict[str, Any]
    task_verification_subject_id: str
    task_job_submission_data: Dict[str, Any]
```

| Field                          | Type            | Description                                                  |
| ------------------------------ | --------------- | ------------------------------------------------------------ |
| `task_id`                      | `str`           | Unique ID of the task                                        |
| `task_goal`                    | `str`           | Describes the primary purpose or goal of the task            |
| `task_intent`                  | `str`           | Expresses the reasoning or intent behind initiating the task |
| `task_priority_value`          | `int`           | Numerical value indicating task priority                     |
| `task_streeability_data`       | `Dict`          | Tree or graph-like control flow data for the task            |
| `task_knowledgebase_ptr`       | `Optional[str]` | Pointer to a knowledgebase resource                          |
| `submitter_subject_id`         | `str`           | Identifier of the subject that submitted the task            |
| `task_op_convertor_dsl_id`     | `Optional[str]` | DSL ID to transform intent to operation                      |
| `task_execution_dsl`           | `Optional[str]` | DSL definition for task execution                            |
| `task_submission_ts`           | `str`           | ISO timestamp when the task was submitted                    |
| `task_completion_timeline`     | `Dict`          | Timeline metadata for completion targets or deadlines        |
| `task_execution_mode`          | `str`           | Mode of execution (manual, auto, hybrid)                     |
| `task_behavior_dsl_map`        | `Dict`          | Behavior logic encoded as DSL                                |
| `task_contracts_map`           | `Dict`          | Mapping of contracts governing task behavior                 |
| `task_verification_subject_id` | `str`           | Subject responsible for verifying task outcome               |
| `task_job_submission_data`     | `Dict`          | Raw data used to submit the job to a backend system          |

---

### 2. `SubTaskEntry`

```python
@dataclass
class SubTaskEntry:
    sub_task_id: str
    task_id: str
    sub_task_goal: str
    sub_task_intent: str
    sub_task_priority_value: int
    sub_task_streeability_data: Dict[str, Any]
    sub_task_knowledgebase_ptr: Optional[str]
    parent_subject_ids: List[str]
    parent_input_data_ptr: Optional[str]
    assigned_subject_ids: List[str]
    sub_task_submission_ts: str
    sub_task_completion_timeline: Dict[str, Any]
    sub_task_behavior_dsl_map: Dict[str, Any]
    sub_task_contracts_map: Dict[str, Any]
```

| Field                          | Type            | Description                                      |
| ------------------------------ | --------------- | ------------------------------------------------ |
| `sub_task_id`                  | `str`           | Unique identifier for the sub-task               |
| `task_id`                      | `str`           | Parent task ID                                   |
| `sub_task_goal`                | `str`           | Purpose of the sub-task                          |
| `sub_task_intent`              | `str`           | Intent behind this sub-task                      |
| `sub_task_priority_value`      | `int`           | Priority for execution                           |
| `sub_task_streeability_data`   | `Dict`          | Graph/tree structure metadata                    |
| `sub_task_knowledgebase_ptr`   | `Optional[str]` | Pointer to related knowledgebase                 |
| `parent_subject_ids`           | `List[str]`     | Subjects contributing inputs to this sub-task    |
| `parent_input_data_ptr`        | `Optional[str]` | Reference to parent data                         |
| `assigned_subject_ids`         | `List[str]`     | Subjects responsible for performing the sub-task |
| `sub_task_submission_ts`       | `str`           | Timestamp of sub-task submission                 |
| `sub_task_completion_timeline` | `Dict`          | Expected execution timeline                      |
| `sub_task_behavior_dsl_map`    | `Dict`          | Behavior DSL mapped per context                  |
| `sub_task_contracts_map`       | `Dict`          | Applied contracts for sub-task execution         |

---

### 3. `TaskOutputs`

```python
@dataclass
class TaskOutputs:
    task_id: str
    task_output_ptr: Optional[str]
    task_output_template_id: Optional[str]
    task_output_streaming_channel: Optional[str]
    task_assets_data_map: Dict[str, Any]
    ts: str
```

| Field                           | Type            | Description                            |
| ------------------------------- | --------------- | -------------------------------------- |
| `task_id`                       | `str`           | Corresponding task ID                  |
| `task_output_ptr`               | `Optional[str]` | Pointer to stored output               |
| `task_output_template_id`       | `Optional[str]` | Template used to format the output     |
| `task_output_streaming_channel` | `Optional[str]` | Channel used for live output streaming |
| `task_assets_data_map`          | `Dict`          | Data related to output assets          |
| `ts`                            | `str`           | Timestamp for this record              |

---

### 4. `SubTaskOutputs`

```python
@dataclass
class SubTaskOutputs:
    sub_task_id: str
    sub_task_output_ptrs: List[str]
    sub_task_output_template_ids: List[str]
    sub_task_assets_data_map: Dict[str, Any]
    ts: str
    subject_ids: List[str]
```

| Field                          | Type        | Description                    |
| ------------------------------ | ----------- | ------------------------------ |
| `sub_task_id`                  | `str`       | Sub-task ID                    |
| `sub_task_output_ptrs`         | `List[str]` | Output file or blob pointers   |
| `sub_task_output_template_ids` | `List[str]` | Templates used per output      |
| `sub_task_assets_data_map`     | `Dict`      | Asset metadata                 |
| `ts`                           | `str`       | Timestamp of output generation |
| `subject_ids`                  | `List[str]` | Review or receiver subjects    |

---

### 5. `TaskStatus`

```python
@dataclass
class TaskStatus:
    task_id: str
    current_status: str
    latest_update_ts: str
    logging_stream_ws: Optional[str]
```

| Field               | Type            | Description                                                       |
| ------------------- | --------------- | ----------------------------------------------------------------- |
| `task_id`           | `str`           | Unique identifier of the task                                     |
| `current_status`    | `str`           | Current lifecycle state (`pending`, `running`, `completed`, etc.) |
| `latest_update_ts`  | `str`           | Timestamp when the status was last updated                        |
| `logging_stream_ws` | `Optional[str]` | WebSocket stream for live logging (if enabled)                    |

---

### 6. `SubTaskStatus`

```python
@dataclass
class SubTaskStatus:
    sub_task_id: str
    current_status: str
    latest_update_ts: str
    logging_stream_ws: Optional[str]
```

| Field               | Type            | Description                            |
| ------------------- | --------------- | -------------------------------------- |
| `sub_task_id`       | `str`           | Unique identifier of the sub-task      |
| `current_status`    | `str`           | Lifecycle status of the sub-task       |
| `latest_update_ts`  | `str`           | Last updated timestamp for the status  |
| `logging_stream_ws` | `Optional[str]` | WebSocket URL for logging/debug stream |

---

### 7. `TaskACLMapping`

```python
@dataclass
class TaskACLMapping:
    task_id: str
    task_allowed_functions_list: List[str]
    task_allowed_actions_list: List[str]
    task_allowed_tools_list: List[str]
    task_allowed_lims_list: List[str]
    tasks_credentials_map: Dict[str, Any]
```

| Field                         | Type        | Description                                              |
| ----------------------------- | ----------- | -------------------------------------------------------- |
| `task_id`                     | `str`       | Associated task ID                                       |
| `task_allowed_functions_list` | `List[str]` | Whitelisted function IDs permitted for execution         |
| `task_allowed_actions_list`   | `List[str]` | Permitted high-level actions (e.g., `analyze`, `report`) |
| `task_allowed_tools_list`     | `List[str]` | List of allowed tools by ID                              |
| `task_allowed_lims_list`      | `List[str]` | Linked LIMS (Lab Information Management Systems) IDs     |
| `tasks_credentials_map`       | `Dict`      | Credential references for task execution contexts        |

---

### 8. `TaskReviewData`

```python
@dataclass
class TaskReviewData:
    task_id: str
    review_subject_ids: List[str]
    review_data: Dict[str, Any]
    ts: str
```

| Field                | Type        | Description                                            |
| -------------------- | ----------- | ------------------------------------------------------ |
| `task_id`            | `str`       | Task under review                                      |
| `review_subject_ids` | `List[str]` | IDs of reviewers assigned to this task                 |
| `review_data`        | `Dict`      | Reviewer feedback, forms, approval decisions, comments |
| `ts`                 | `str`       | Timestamp of review submission                         |

---

### 9. `SubTaskReviewData`

```python
@dataclass
class SubTaskReviewData:
    sub_task_id: str
    review_subject_ids: List[str]
    review_data: Dict[str, Any]
```

| Field                | Type        | Description                                                |
| -------------------- | ----------- | ---------------------------------------------------------- |
| `sub_task_id`        | `str`       | Sub-task being reviewed                                    |
| `review_subject_ids` | `List[str]` | Assigned reviewers for the sub-task                        |
| `review_data`        | `Dict`      | Reviewer inputs, approvals, rejections, and other feedback |

---

## Org Tasks DB API

### Common Response Format

Success responses:

```json
{
  "success": true,
  "data": {
    "message": "Task created",
    "id": "task_123"
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": "No document found to update"
}
```

---

## Task APIs

### `POST /task`

**Description**: Create a new task entry.

#### Request Body (JSON)

```json
{
  "task_id": "task_123",
  "task_goal": "Analyze data trends",
  "task_intent": "Automate analytics",
  "task_priority_value": 5,
  "task_streeability_data": {},
  "task_knowledgebase_ptr": "kb_001",
  "submitter_subject_id": "user_789",
  "task_op_convertor_dsl_id": "dsl_001",
  "task_execution_dsl": "exec_dsl_001",
  "task_submission_ts": "2024-06-01T12:00:00Z",
  "task_completion_timeline": {"due": "2024-06-10"},
  "task_execution_mode": "automatic",
  "task_behavior_dsl_map": {},
  "task_contracts_map": {},
  "task_verification_subject_id": "verifier_321",
  "task_job_submission_data": {}
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task \
     -H "Content-Type: application/json" \
     -d @task.json
```

---

### `GET /task/<task_id>`

**Description**: Retrieve a task entry by ID.

#### Example

```bash
curl http://localhost:8000/task/task_123
```

---

### `PUT /task/<task_id>`

**Description**: Update an existing task.

#### Request Body (JSON)

```json
{
  "task_priority_value": 10,
  "task_execution_mode": "manual"
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/task/task_123 \
     -H "Content-Type: application/json" \
     -d '{"task_priority_value": 10, "task_execution_mode": "manual"}'
```

---

### `DELETE /task/<task_id>`

**Description**: Delete a task by ID.

#### Example

```bash
curl -X DELETE http://localhost:8000/task/task_123
```

---

### `POST /tasks`

**Description**: Query tasks using filter criteria.

#### Request Body (JSON)

```json
{
  "submitter_subject_id": "user_789",
  "task_execution_mode": "automatic"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/tasks \
     -H "Content-Type: application/json" \
     -d '{"submitter_subject_id": "user_789", "task_execution_mode": "automatic"}'
```

---

## Sub-Task APIs

### `POST /sub_task`

**Description**: Create a new sub-task entry.

#### Request Body (JSON)

```json
{
  "sub_task_id": "sub_456",
  "task_id": "task_123",
  "sub_task_goal": "Extract recent metrics",
  "sub_task_intent": "Support analytics",
  "sub_task_priority_value": 3,
  "sub_task_streeability_data": {},
  "sub_task_knowledgebase_ptr": "kb_002",
  "parent_subject_ids": ["user_789"],
  "parent_input_data_ptr": "input_blob_1",
  "assigned_subject_ids": ["agent_001"],
  "sub_task_submission_ts": "2024-06-02T10:00:00Z",
  "sub_task_completion_timeline": {"expected_by": "2024-06-04"},
  "sub_task_behavior_dsl_map": {},
  "sub_task_contracts_map": {}
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/sub_task \
     -H "Content-Type: application/json" \
     -d @subtask.json
```

---

### `GET /sub_task/<sub_task_id>`

**Description**: Retrieve a sub-task by ID.

#### Example

```bash
curl http://localhost:8000/sub_task/sub_456
```

---

### `PUT /sub_task/<sub_task_id>`

**Description**: Update fields of a sub-task.

#### Request Body (JSON)

```json
{
  "sub_task_priority_value": 2,
  "assigned_subject_ids": ["agent_002", "agent_003"]
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/sub_task/sub_456 \
     -H "Content-Type: application/json" \
     -d '{"sub_task_priority_value": 2, "assigned_subject_ids": ["agent_002", "agent_003"]}'
```

---

### `DELETE /sub_task/<sub_task_id>`

**Description**: Delete a sub-task by ID.

#### Example

```bash
curl -X DELETE http://localhost:8000/sub_task/sub_456
```

---

### `POST /sub_tasks`

**Description**: Query sub-tasks using filters.

#### Request Body (JSON)

```json
{
  "task_id": "task_123",
  "assigned_subject_ids": { "$in": ["agent_001"] }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/sub_tasks \
     -H "Content-Type: application/json" \
     -d '{"task_id": "task_123", "assigned_subject_ids": {"$in": ["agent_001"]}}'
```

---

## Task Output APIs

### `POST /task_output`

**Description**: Create a new task output entry.

#### Request Body (JSON)

```json
{
  "task_id": "task_123",
  "task_output_ptr": "s3://outputs/task_123/output.json",
  "task_output_template_id": "template_01",
  "task_output_streaming_channel": "ws://stream/task_123",
  "task_assets_data_map": {
    "report": "s3://assets/report_123.pdf"
  },
  "ts": "2024-06-03T08:30:00Z"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task_output \
     -H "Content-Type: application/json" \
     -d @task_output.json
```

---

### `GET /task_output/<task_id>`

**Description**: Retrieve task output by `task_id`.

#### Example

```bash
curl http://localhost:8000/task_output/task_123
```

---

### `PUT /task_output/<task_id>`

**Description**: Update a task output entry.

#### Request Body (JSON)

```json
{
  "task_output_ptr": "s3://outputs/task_123/v2_output.json"
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/task_output/task_123 \
     -H "Content-Type: application/json" \
     -d '{"task_output_ptr": "s3://outputs/task_123/v2_output.json"}'
```

---

### `DELETE /task_output/<task_id>`

**Description**: Delete a task output record.

#### Example

```bash
curl -X DELETE http://localhost:8000/task_output/task_123
```

---

### `POST /task_outputs`

**Description**: Query task output records using filters.

#### Request Body (JSON)

```json
{
  "task_output_template_id": "template_01"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task_outputs \
     -H "Content-Type: application/json" \
     -d '{"task_output_template_id": "template_01"}'
```

---

## Sub-Task Output APIs

### `POST /sub_task_output`

**Description**: Create a new sub-task output entry.

#### Request Body (JSON)

```json
{
  "sub_task_id": "sub_456",
  "sub_task_output_ptrs": [
    "s3://outputs/sub_456/output_1.json",
    "s3://outputs/sub_456/output_2.json"
  ],
  "sub_task_output_template_ids": ["template_a", "template_b"],
  "sub_task_assets_data_map": {
    "chart": "s3://assets/chart_sub456.png"
  },
  "ts": "2024-06-03T09:00:00Z",
  "subject_ids": ["agent_002", "agent_003"]
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/sub_task_output \
     -H "Content-Type: application/json" \
     -d @sub_task_output.json
```

---

### `GET /sub_task_output/<sub_task_id>`

**Description**: Retrieve sub-task output using `sub_task_id`.

#### Example

```bash
curl http://localhost:8000/sub_task_output/sub_456
```

---

### `PUT /sub_task_output/<sub_task_id>`

**Description**: Update a sub-task output record.

#### Request Body (JSON)

```json
{
  "sub_task_output_ptrs": [
    "s3://outputs/sub_456/new_output.json"
  ]
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/sub_task_output/sub_456 \
     -H "Content-Type: application/json" \
     -d '{"sub_task_output_ptrs": ["s3://outputs/sub_456/new_output.json"]}'
```

---

### `DELETE /sub_task_output/<sub_task_id>`

**Description**: Delete a sub-task output record.

#### Example

```bash
curl -X DELETE http://localhost:8000/sub_task_output/sub_456
```

---

### `POST /sub_task_outputs`

**Description**: Query sub-task outputs using filters.

#### Request Body (JSON)

```json
{
  "subject_ids": { "$in": ["agent_003"] }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/sub_task_outputs \
     -H "Content-Type: application/json" \
     -d '{"subject_ids": {"$in": ["agent_003"]}}'
```

---

## Task Status APIs

### `POST /task_status`

**Description**: Create or register a task's initial status.

#### Request Body (JSON)

```json
{
  "task_id": "task_123",
  "current_status": "pending",
  "latest_update_ts": "2024-06-01T12:00:00Z",
  "logging_stream_ws": "ws://logs/task_123"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task_status \
     -H "Content-Type: application/json" \
     -d @task_status.json
```

---

### `GET /task_status/<task_id>`

**Description**: Retrieve current status of a task.

#### Example

```bash
curl http://localhost:8000/task_status/task_123
```

---

### `PUT /task_status/<task_id>`

**Description**: Update the status of a task.

#### Request Body (JSON)

```json
{
  "current_status": "completed",
  "latest_update_ts": "2024-06-10T17:30:00Z"
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/task_status/task_123 \
     -H "Content-Type: application/json" \
     -d '{"current_status": "completed", "latest_update_ts": "2024-06-10T17:30:00Z"}'
```

---

### `DELETE /task_status/<task_id>`

**Description**: Delete a task's status entry.

#### Example

```bash
curl -X DELETE http://localhost:8000/task_status/task_123
```

---

### `POST /task_statuss`

**Description**: Query task status records.

#### Request Body (JSON)

```json
{
  "current_status": "completed"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task_statuss \
     -H "Content-Type: application/json" \
     -d '{"current_status": "completed"}'
```

---

## Sub-Task Status APIs

### `POST /sub_task_status`

**Description**: Create a status record for a sub-task.

#### Request Body (JSON)

```json
{
  "sub_task_id": "sub_456",
  "current_status": "in_progress",
  "latest_update_ts": "2024-06-04T09:00:00Z",
  "logging_stream_ws": "ws://logs/sub_456"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/sub_task_status \
     -H "Content-Type: application/json" \
     -d @sub_task_status.json
```

---

### `GET /sub_task_status/<sub_task_id>`

**Description**: Retrieve status for a sub-task.

#### Example

```bash
curl http://localhost:8000/sub_task_status/sub_456
```

---

### `PUT /sub_task_status/<sub_task_id>`

**Description**: Update sub-task status.

#### Request Body (JSON)

```json
{
  "current_status": "completed",
  "latest_update_ts": "2024-06-05T13:00:00Z"
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/sub_task_status/sub_456 \
     -H "Content-Type: application/json" \
     -d '{"current_status": "completed", "latest_update_ts": "2024-06-05T13:00:00Z"}'
```

---

### `DELETE /sub_task_status/<sub_task_id>`

**Description**: Delete status of a sub-task.

#### Example

```bash
curl -X DELETE http://localhost:8000/sub_task_status/sub_456
```

---

### `POST /sub_task_statuss`

**Description**: Query sub-task statuses.

#### Request Body (JSON)

```json
{
  "current_status": "in_progress"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/sub_task_statuss \
     -H "Content-Type: application/json" \
     -d '{"current_status": "in_progress"}'
```

---

## Task ACL Mapping APIs

### `POST /task_acl`

**Description**: Create a new ACL mapping for a task.

#### Request Body (JSON)

```json
{
  "task_id": "task_123",
  "task_allowed_functions_list": ["func_analyze", "func_predict"],
  "task_allowed_actions_list": ["submit", "verify"],
  "task_allowed_tools_list": ["tool_x", "tool_y"],
  "task_allowed_lims_list": ["lims_01"],
  "tasks_credentials_map": {
    "aws": "arn:aws:iam::account:role"
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task_acl \
     -H "Content-Type: application/json" \
     -d @task_acl.json
```

---

### `GET /task_acl/<task_id>`

**Description**: Retrieve ACL mapping for a task.

#### Example

```bash
curl http://localhost:8000/task_acl/task_123
```

---

### `PUT /task_acl/<task_id>`

**Description**: Update ACL fields for a task.

#### Request Body (JSON)

```json
{
  "task_allowed_actions_list": ["submit", "approve"]
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/task_acl/task_123 \
     -H "Content-Type: application/json" \
     -d '{"task_allowed_actions_list": ["submit", "approve"]}'
```

---

### `DELETE /task_acl/<task_id>`

**Description**: Delete ACL mapping for a task.

#### Example

```bash
curl -X DELETE http://localhost:8000/task_acl/task_123
```

---

### `POST /task_acls`

**Description**: Query ACL mappings using filters.

#### Request Body (JSON)

```json
{
  "task_allowed_tools_list": { "$in": ["tool_x"] }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task_acls \
     -H "Content-Type: application/json" \
     -d '{"task_allowed_tools_list": {"$in": ["tool_x"]}}'
```

---

## Task Review APIs

### `POST /task_review`

**Description**: Submit a task-level review record.

#### Request Body (JSON)

```json
{
  "task_id": "task_123",
  "review_subject_ids": ["reviewer_1", "reviewer_2"],
  "review_data": {
    "reviewer_1": { "status": "approved", "comment": "Looks good" },
    "reviewer_2": { "status": "approved" }
  },
  "ts": "2024-06-06T11:45:00Z"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task_review \
     -H "Content-Type: application/json" \
     -d @task_review.json
```

---

### `GET /task_review/<task_id>`

**Description**: Retrieve review record for a task.

#### Example

```bash
curl http://localhost:8000/task_review/task_123
```

---

### `PUT /task_review/<task_id>`

**Description**: Update a task review.

#### Request Body (JSON)

```json
{
  "review_data": {
    "reviewer_1": { "status": "rejected", "comment": "Data incomplete" }
  }
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/task_review/task_123 \
     -H "Content-Type: application/json" \
     -d '{"review_data": {"reviewer_1": {"status": "rejected", "comment": "Data incomplete"}}}'
```

---

### `DELETE /task_review/<task_id>`

**Description**: Delete a task review record.

#### Example

```bash
curl -X DELETE http://localhost:8000/task_review/task_123
```

---

### `POST /task_reviews`

**Description**: Query task reviews by reviewer or status.

#### Request Body (JSON)

```json
{
  "review_subject_ids": { "$in": ["reviewer_1"] }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/task_reviews \
     -H "Content-Type: application/json" \
     -d '{"review_subject_ids": {"$in": ["reviewer_1"]}}'
```

---

## Sub-Task Review APIs

### `POST /sub_task_review`

**Description**: Create a sub-task review entry.

#### Request Body (JSON)

```json
{
  "sub_task_id": "sub_456",
  "review_subject_ids": ["verifier_007"],
  "review_data": {
    "verifier_007": { "comment": "Passes QA", "status": "approved" }
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/sub_task_review \
     -H "Content-Type: application/json" \
     -d @sub_task_review.json
```

---

### `GET /sub_task_review/<sub_task_id>`

**Description**: Get sub-task review data.

#### Example

```bash
curl http://localhost:8000/sub_task_review/sub_456
```

---

### `PUT /sub_task_review/<sub_task_id>`

**Description**: Update a sub-task review.

#### Request Body (JSON)

```json
{
  "review_data": {
    "verifier_007": { "status": "rejected", "comment": "Data missing section" }
  }
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8000/sub_task_review/sub_456 \
     -H "Content-Type: application/json" \
     -d '{"review_data": {"verifier_007": {"status": "rejected", "comment": "Data missing section"}}}'
```

---

### `DELETE /sub_task_review/<sub_task_id>`

**Description**: Delete sub-task review entry.

#### Example

```bash
curl -X DELETE http://localhost:8000/sub_task_review/sub_456
```

---

### `POST /sub_task_reviews`

**Description**: Query sub-task reviews.

#### Request Body (JSON)

```json
{
  "review_subject_ids": { "$in": ["verifier_007"] }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/sub_task_reviews \
     -H "Content-Type: application/json" \
     -d '{"review_subject_ids": {"$in": ["verifier_007"]}}'
```

---

## Org job assignment

### Introduction

The Job Automation System facilitates dynamic job handling using multiple decision flows. It supports both manual and competitive workflows for assigning tasks within an organizational environment.

This system integrates:

* Real-time event listening via NATS
* Decision logic through DSL workflows
* Task creation and submission via APIs
* Asynchronous processing using queues and threads

Three primary components are:

* **JobBiddingClient**: Listens for job invitations and submits bids
* **JobWinningHandler**: Listens for winning bid events and creates tasks
* **Direct Task Assignment API**: Enables synchronous job-to-task conversion through a DSL validation step

---

### Flows – Direct Task Assignment

The **Direct Task Assignment** flow enables a job to be converted into a task without competition or bidding. The system validates the job using a DSL workflow and directly assigns it as a task if allowed.

This is ideal for:

* Urgent jobs requiring no evaluation
* Pre-authorized job types
* Controlled workflows where automation bypasses bidding

---

#### 3. Direct Task Assignment API

**Endpoint**: `POST /jobs/direct-assign`
**Description**: Validates and creates a task directly from a job, using a manual assignment DSL workflow.

**Request Body (JSON)**

```json
{
  "jobId": "job-001",
  "jobGoal": { "type": "summarization" },
  "jobObjectives": ["analyze", "summarize"],
  "jobPriorityValue": 5,
  "jobCompletionMode": "single_window",
  "submittedBy": "org-123",
  "jobOutputTemplateId": "template-xyz",
  "jobVerificationSubjectIds": ["agent-456"]
}
```

**Response – Success**

```json
{
  "success": true,
  "task_id": "task-9a24aefa-3ac4-4be1-8910-96d6b014fcb7",
  "message": "Task created and inserted successfully"
}
```

**Response – Failure (Example: Missing Fields)**

```json
{
  "success": false,
  "message": "Missing required job fields: jobGoal, jobVerificationSubjectIds"
}
```

**CURL Example**

```bash
curl -X POST http://localhost:8000/jobs/direct-assign \
     -H "Content-Type: application/json" \
     -d @job.json
```

---

### Assignment Flow

The **direct assignment flow** works as follows:

1. **Job Validation**:

   * The API receives the job payload.
   * It checks all required fields (`jobId`, `jobGoal`, `jobObjectives`, etc.).

2. **DSL Evaluation**:

   * Executes a DSL workflow (ID provided via `ORG_MANUAL_JOB_ASSIGNMENT_DSL_WORKFLOW_ID`) to determine whether the job is permitted.
   * The DSL should return a JSON object with a key `"allowed": true` or `"allowed": false`.

3. **Task Construction**:

   * If allowed, a `task_id` is generated.
   * Job fields are mapped to the task structure.
   * DSL results can be embedded into the task behavior, constraints, or logic if needed.

4. **Task Insertion**:

   * The task is submitted to the task database using `TaskCreationClient`.
   * On success, the `task_id` is returned in the response.

This approach ensures controlled, secure, and auditable job-to-task transformations without human intervention, governed by programmable DSL logic.

---

### 5. DSL Workflows Used

| DSL Environment Variable                      | Description                                                        | Used In               |
| --------------------------------------------- | ------------------------------------------------------------------ | --------------------- |
| `ORG_MANUAL_JOB_ASSIGNMENT_DSL_WORKFLOW_ID`   | DSL that validates whether a job is eligible for direct assignment | Direct assignment API |
| `ORG_JOB_BID_CREATOR_DSL_WORKFLOW_ID`         | DSL that generates bid data from job information                   | JobBiddingClient      |
| `bid_task_eval_dsl_id` (from bid task object) | DSL used to evaluate submitted bids for winner selection           | BidsEvaluator         |
| `bid_task_post_evaluation_id` (optional)      | Additional DSL executed after initial bid evaluation               | BidsEvaluator         |

Each DSL is managed independently and can be authored using a domain-specific language framework that supports conditional logic, scoring, filtering, and transformation of structured input.

---
