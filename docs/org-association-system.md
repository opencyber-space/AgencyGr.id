# Org Association System

## Introduction

This module provides REST APIs to manage and query various subject-related associations and configurations in a distributed organizational system. These associations are essential for defining how subjects (such as users, agents, or entities) interact with roles, groups, contracts, messaging systems, and job spaces.

The system is composed of the following key components, each backed by a dedicated MongoDB collection:

1. **Subject Association**
   Defines a subject's relationship to a role, group, job space, and selection/DSL-based configuration. Also supports parent-child hierarchies and lifecycle workflows.

2. **Subject Contract Association**
   Associates a subject with a specific contract type and contract instance within a job space.

3. **Subject Message Communication**
   Specifies how a subject interacts with external communication channels using message types, sub-types, and conversion pipelines.

4. **Subject Association Configuration**
   Manages custom configuration values per subject within specific job spaces.

Each component exposes a minimal set of REST APIs for querying and retrieving entities by ID. These APIs are useful for internal coordination, role-task assignments, and distributed function execution where subject metadata must be consistently managed across subsystems.

## Schema

This section defines the data models used in the subject association system. Each model corresponds to a collection in MongoDB and is represented using a Python data class. These classes ensure structured serialization, validation, and compatibility with REST and database operations.

---

### SubjectAssociation

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class SubjectAssociation:
    subject_id: str = ''
    subject_type: str = ''
    subject_role_id: str = ''
    subject_group_id: str = ''
    subject_role_type: str = ''
    subject_job_space_id: str = ''
    subject_selection_dsl_id: str = ''
    parent_subject_ids: List[str] = field(default_factory=list)
    post_joining_dsl_id: str = ''
    post_leaving_dsl_id: str = ''
    association_payload_data: Dict[str, Any] = field(default_factory=dict)
    association_status: str = ''
    association_time: str = ''
```

#### Fields

| Field Name                 | Type             | Description                                                    |
| -------------------------- | ---------------- | -------------------------------------------------------------- |
| `subject_id`               | `str`            | Unique identifier of the subject                               |
| `subject_type`             | `str`            | Type/category of the subject (e.g., user, agent)               |
| `subject_role_id`          | `str`            | Role assigned to the subject                                   |
| `subject_group_id`         | `str`            | Group in which the subject is included                         |
| `subject_role_type`        | `str`            | Role type or classification (e.g., admin, evaluator)           |
| `subject_job_space_id`     | `str`            | Job space to which the subject belongs                         |
| `subject_selection_dsl_id` | `str`            | DSL used to determine if a subject is selected                 |
| `parent_subject_ids`       | `List[str]`      | List of parent subjects this subject inherits properties from  |
| `post_joining_dsl_id`      | `str`            | DSL to execute immediately after the subject is associated     |
| `post_leaving_dsl_id`      | `str`            | DSL to execute when the subject leaves the association         |
| `association_payload_data` | `Dict[str, Any]` | Custom metadata or contextual data relevant to the association |
| `association_status`       | `str`            | Current status (e.g., active, inactive)                        |
| `association_time`         | `str`            | Timestamp of when the association was created or last updated  |

---

### SubjectContractAssociation

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SubjectContractAssociation:
    subject_id: str = ''
    subject_contract_type: str = ''
    subject_contract_id: str = ''
    job_space_id: str = ''
```

#### Fields

| Field Name              | Type  | Description                                                 |
| ----------------------- | ----- | ----------------------------------------------------------- |
| `subject_id`            | `str` | Unique identifier of the subject                            |
| `subject_contract_type` | `str` | Type of contract assigned (e.g., SLA, MOU)                  |
| `subject_contract_id`   | `str` | Unique identifier of the specific contract document         |
| `job_space_id`          | `str` | Job space or operational context where the contract applies |

This model binds a subject to a contractual agreement. It enables dynamic enforcement of contract-bound logic or resource limits based on job context.

---

### SubjectMessageCommunication

```python
from dataclasses import dataclass

@dataclass
class SubjectMessageCommunication:
    messaging_id: str = ''
    subject_id: str = ''
    message_type: str = ''
    message_sub_type: str = ''
    channel_id: str = ''
    input_message_convertor_id: str = ''
    output_message_convertor_id: str = ''
```

#### Fields

| Field Name                    | Type  | Description                                                        |
| ----------------------------- | ----- | ------------------------------------------------------------------ |
| `messaging_id`                | `str` | Unique identifier for the messaging config                         |
| `subject_id`                  | `str` | Identifier of the subject using the messaging config               |
| `message_type`                | `str` | Type of the message (e.g., notification, response)                 |
| `message_sub_type`            | `str` | Further categorization of the message type (e.g., alert, approval) |
| `channel_id`                  | `str` | ID of the external channel (e.g., Slack, Teams, Email)             |
| `input_message_convertor_id`  | `str` | Identifier for logic used to process inbound messages              |
| `output_message_convertor_id` | `str` | Identifier for logic used to process outbound messages             |

This model defines how a subject communicates externally, including routing logic and transformation handlers for input/output messages.

---

### SubjectAssociationConfig

```python
from dataclasses import dataclass

@dataclass
class SubjectAssociationConfig:
    config_id: str = ''
    subject_id: str = ''
    job_space_id: str = ''
    config_name: str = ''
    config_value: str = ''
```

#### Fields

| Field Name     | Type  | Description                                      |
| -------------- | ----- | ------------------------------------------------ |
| `config_id`    | `str` | Unique configuration identifier                  |
| `subject_id`   | `str` | Identifier of the subject this config applies to |
| `job_space_id` | `str` | Job space context for the configuration          |
| `config_name`  | `str` | Name/key of the configuration parameter          |
| `config_value` | `str` | Value assigned to the configuration parameter    |

This model is used to store key-value configuration overrides or settings per subject per job space, useful for fine-grained runtime behavior.

---

## APIs

This section documents the REST API endpoints exposed by the subject association system. Each resource supports:

* **GET by ID** – to fetch a single entry by its unique identifier
* **POST query** – to filter entries based on specific fields

All endpoints return JSON responses with a consistent structure.

---

### Subject Association APIs

#### Get Subject Association by ID

**Endpoint**: `GET /subject-association/<subject_id>`

**Description**: Retrieve a single subject association using the subject's unique ID.

##### cURL Example

```bash
curl -X GET http://localhost:8000/subject-association/subject_123
```

---

#### Query Subject Associations

**Endpoint**: `POST /subject-association/query`

**Description**: Query multiple subject associations using filter conditions.

##### Request Body Example

```json
{
  "subject_role_type": "evaluator"
}
```

##### cURL Example

```bash
curl -X POST http://localhost:8000/subject-association/query \
     -H "Content-Type: application/json" \
     -d '{"subject_role_type": "evaluator"}'
```

---

### Subject Contract Association APIs

####  Get Subject Contract Association by ID

**Endpoint**: `GET /subject-contract/<subject_id>`

**Description**: Fetch contract association information for a subject using its ID.

##### cURL Example

```bash
curl -X GET http://localhost:8000/subject-contract/subject_123
```

---

#### Query Subject Contract Associations

**Endpoint**: `POST /subject-contract/query`

**Description**: Filter subject-contract mappings using fields like `contract_type` or `job_space_id`.

##### Request Body Example

```json
{
  "subject_contract_type": "SLA"
}
```

##### cURL Example

```bash
curl -X POST http://localhost:8000/subject-contract/query \
     -H "Content-Type: application/json" \
     -d '{"subject_contract_type": "SLA"}'
```

---

### Subject Message Communication APIs

####  Get Subject Message Config by ID

**Endpoint**: `GET /subject-message/<messaging_id>`

**Description**: Retrieve a subject's external messaging configuration by its messaging ID.

##### cURL Example

```bash
curl -X GET http://localhost:8000/subject-message/msg_456
```

---

#### Query Subject Message Communications

**Endpoint**: `POST /subject-message/query`

**Description**: Query messaging configurations using fields like `subject_id`, `message_type`, etc.

##### Request Body Example

```json
{
  "channel_id": "slack_main"
}
```

##### cURL Example

```bash
curl -X POST http://localhost:8000/subject-message/query \
     -H "Content-Type: application/json" \
     -d '{"channel_id": "slack_main"}'
```

---

### Subject Association Config APIs

#### Get Subject Config by ID

**Endpoint**: `GET /subject-config/<config_id>`

**Description**: Retrieve a single subject association config entry by its unique ID.

##### cURL Example

```bash
curl -X GET http://localhost:8000/subject-config/config_xyz
```

---

#### Query Subject Association Configs

**Endpoint**: `POST /subject-config/query`

**Description**: Filter subject configuration entries using fields such as `subject_id`, `config_name`, etc.

##### Request Body Example

```json
{
  "subject_id": "subject_123"
}
```

##### cURL Example

```bash
curl -X POST http://localhost:8000/subject-config/query \
     -H "Content-Type: application/json" \
     -d '{"subject_id": "subject_123"}'
```

---

