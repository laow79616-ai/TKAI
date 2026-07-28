"""Node type registry."""

from workflow_platform.models import Node, NodeType

NODE_TYPES = tuple(NodeType)

__all__ = ["NODE_TYPES", "Node", "NodeType"]
