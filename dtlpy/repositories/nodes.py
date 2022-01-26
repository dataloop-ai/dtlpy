from .. import entities, repositories, exceptions, miscellaneous, services


class Nodes(list):

    def __init__(self, client_api: services.ApiClient, pipeline: entities.Pipeline = None, nodes=None):
        if nodes is None:
            nodes = []
        self._client_api = client_api
        self._pipeline = pipeline
        for node in nodes:
            self.add(node)

    def add(self, node: entities.PipelineNode) -> entities.PipelineNode:
        """
        Add a node to the nodes list

        :param PipelineNode node: node to add
        :return: node that add
        """
        if node not in self:
            self.append(node)
            node._pipeline = self._pipeline
            if not self._pipeline.start_nodes:
                self._pipeline.set_start_node(node=node)
        return node

    def get(self, node_name: str) -> entities.PipelineNode:
        """
        Get a node from the nodes list by name

        :param str node_name: the node name
        :return: the result node
        """
        for node in self:
            if node_name == node.name:
                return node
        return None

    def remove(self, node_name) -> bool:
        """
        Remove a node from the nodes list by name

        :param str node_name: the node name
        :return: True if success
        """
        node = self.get(node_name=node_name)
        if node:
            copy_conn = self._pipeline.connections.copy()
            for conn in copy_conn:
                if node.node_id == conn.source.node_id or node.node_id == conn.target.node_id:
                    self._pipeline.connections.remove(conn)
            for node_index in range(len(self)):
                if self[node_index] == node:
                    self.pop(node_index)
                    if self._pipeline.start_nodes[0]['nodeId'] == node.node_id:
                        if self:
                            self._pipeline.set_start_node(self[0])
                    return True
        return False
