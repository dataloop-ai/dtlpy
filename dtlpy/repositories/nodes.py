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

    def get(self, node_name: str = None, node_id: str = None) -> entities.PipelineNode:
        """
        Get a node from the nodes list by name

        :param str node_name: the node name
        :param str node_id: the node id
        :return: the result node
        """
        if node_id is None and node_name is None:
            raise exceptions.PlatformException('400',
                                               'Must provide node_id or node_name')
        for node in self:
            if node_name == node.name or node_id == node.node_id:
                return node
        return None

    def remove(self, node_name) -> bool:
        """
        Remove a node from the nodes list by name

        :param str node_name: the node name
        :return: True if success
        """
        if not isinstance(node_name, str):
            raise ValueError('node name must be string')

        # get the wanted node
        node = self.get(node_name=node_name)
        if node:
            copy_conn = self._pipeline.connections.copy()
            # remove all node connections
            for conn in copy_conn:
                if node.node_id == conn.source.node_id or node.node_id == conn.target.node_id:
                    self._pipeline.connections.remove(conn)
            # remove the node
            for node_index in range(len(self)):
                if self[node_index].node_id == node.node_id:
                    self.pop(node_index)
                    # remove the node from the start_nodes if it exists
                    # if the node is the root node set the first node as the start node
                    for n in self._pipeline.start_nodes:
                        if n['nodeId'] == node.node_id:
                            # check if still have nodes in the pipeline nodes list
                            if self:
                                if n['type'] == 'root':
                                    self._pipeline.set_start_node(self[0])
                                else:
                                    self._pipeline.start_nodes.remove(n)
                            else:
                                self._pipeline.start_nodes = []
                    return True
        return False
