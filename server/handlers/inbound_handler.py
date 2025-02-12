class InboundHandler:
    @staticmethod
    async def handle_client_message(server, websocket, message_data):
        workflow_id = message_data.get('workflow_id')
        
        if not workflow_id or workflow_id not in server.workflows:
            return
            
        workflow = server.workflows[workflow_id]
        
        match message_data['type']:
            case 'node_created':
                await InboundHandler._handle_node_created(server, workflow, workflow_id, message_data)
            case 'node_deleted':
                await InboundHandler._handle_node_deleted(server, workflow, workflow_id, message_data)
            case 'edge_created':
                await InboundHandler._handle_edge_created(server, workflow, workflow_id, message_data)
            case 'edge_deleted':
                await InboundHandler._handle_edge_deleted(server, workflow, workflow_id, message_data)

    @staticmethod
    async def _handle_node_created(server, workflow, workflow_id, data):
        if any(n['id'] == data['nodeId'] for n in workflow['nodes']):
            return
            
        workflow['nodes'].append({
            'id': data['nodeId'],
            'class': data['nodeType'],
            'config': {}
        })
        await server.save_workflow(workflow_id)

    @staticmethod
    async def _handle_node_deleted(server, workflow, workflow_id, data):
        node_id = data['nodeId']
        workflow['nodes'] = [n for n in workflow['nodes'] if n['id'] != node_id]
        workflow['edges'] = [e for e in workflow['edges'] 
                            if e['from'] != node_id and e['to'] != node_id]
        await server.save_workflow(workflow_id)

    @staticmethod
    async def _handle_edge_created(server, workflow, workflow_id, data):
        from_node = data['from']
        to_node = data['to']
        existing = any(e['from'] == from_node and e['to'] == to_node 
                      for e in workflow['edges'])
        nodes_exist = (any(n['id'] == from_node for n in workflow['nodes']) and
                      any(n['id'] == to_node for n in workflow['nodes']))
        
        if not existing and nodes_exist:
            workflow['edges'].append({
                'from': from_node,
                'to': to_node,
                'condition': 'True'
            })
            await server.save_workflow(workflow_id)

    @staticmethod
    async def _handle_edge_deleted(server, workflow, workflow_id, data):
        workflow['edges'] = [
            e for e in workflow['edges']
            if not (e['from'] == data['from'] and e['to'] == data['to'])
        ]
        await server.save_workflow(workflow_id)