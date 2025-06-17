import graphene
from graphene.types.generic import GenericScalar
from flask_graphql import GraphQLView

from .db import JobSpaceContractsMapping
from .db import JobSpaceContractsMappingDB

# Mongo-backed DB instance
mapping_db = JobSpaceContractsMappingDB()


# --- GraphQL Type ---
class JobSpaceContractsMappingType(graphene.ObjectType):
    task_id = graphene.String()
    sub_task_id = graphene.String()
    key = graphene.String()
    contract_ids = graphene.List(graphene.String)
    metadata = GenericScalar()

    def resolve_key(parent, info):
        return f"{parent.task_id}::{parent.sub_task_id}" if parent.sub_task_id else parent.task_id


class Query(graphene.ObjectType):
    all_mappings = graphene.List(JobSpaceContractsMappingType)
    mapping_by_key = graphene.Field(JobSpaceContractsMappingType, key=graphene.String(required=True))
    mappings_by_task_id = graphene.List(JobSpaceContractsMappingType, task_id=graphene.String(required=True))
    query_mappings = graphene.List(JobSpaceContractsMappingType, where=GenericScalar())

    def resolve_all_mappings(self, info):
        return mapping_db.list_all()

    def resolve_mapping_by_key(self, info, key):
        return mapping_db.get(key)

    def resolve_mappings_by_task_id(self, info, task_id):
        return [m for m in mapping_db.list_all() if m.task_id == task_id]

    def resolve_query_mappings(self, info, where=None):
        where = where or {}
        cursor = mapping_db.collection.find(where)
        return [JobSpaceContractsMapping.from_dict(doc) for doc in cursor]


schema = graphene.Schema(query=Query)


def mount_graphql(app):
    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view(
            "graphql",
            schema=schema,
            graphiql=True
        )
    )
