
class RoutingData:

    address = ''
    origin_node = ''
    nodes = {}

    def __init__(self, _address, _origin_node_name, _origin_node_address):
        self.address = _address
        self.origin_node = _origin_node_name
        self.nodes[_origin_node_name] = _origin_node_address


    def update(self, address, existing_node, update):
        self.nodes[existing_node] = update

    def getNodes(self):
        return self.nodes