#!/usr/bin/env python3
"""Clear Weaviate database"""
import weaviate
import weaviate.classes as wvc

print("Connecting to Weaviate...")
client = weaviate.connect_to_custom(
    http_host="weaviate.cyber-pi-intel.svc.cluster.local",
    http_port=8080,
    http_secure=False,
    grpc_host="weaviate.cyber-pi-intel.svc.cluster.local",
    grpc_port=50051,
    grpc_secure=False
)

collection = client.collections.get("CyberThreatIntelligence")

print("Clearing all threats...")
collection.data.delete_many(where=wvc.query.Filter.by_property("threatId").like("*"))

print("✅ Weaviate cleared")
client.close()
