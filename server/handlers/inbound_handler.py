import json
import uuid

class InboundHandler:
    @staticmethod
    async def handle_client_message(manager, websocket, message_data):
        message_type = message_data.get('type', '')
            
        # Handle workflow editing messages
        workflow_id = message_data.get('workflow_id')
        if not workflow_id or workflow_id not in manager.workflows:
            return
        
        workflow = manager.workflows[workflow_id]
        
        match message_data['type']:
            case 'node_created':
                await InboundHandler._handle_node_created(manager, workflow, workflow_id, message_data)
            case 'node_deleted':
                await InboundHandler._handle_node_deleted(manager, workflow, workflow_id, message_data)
            case 'edge_created':
                await InboundHandler._handle_edge_created(manager, workflow, workflow_id, message_data)
            case 'edge_deleted':
                await InboundHandler._handle_edge_deleted(manager, workflow, workflow_id, message_data)
            case 'mark_as_start_node':
                await InboundHandler._handle_mark_as_start_node(manager, workflow, workflow_id, message_data)
            case 'set_edge_condition':
                await InboundHandler._handle_set_edge_condition(manager, workflow, workflow_id, message_data)
            case 'set_initial_state':
                await InboundHandler._handle_set_initial_state(manager, workflow, workflow_id, message_data)
            case 'save_node_config':
                await InboundHandler._handle_save_node_config(manager, workflow, workflow_id, message_data)
            case 'save_node_code':
                await InboundHandler._handle_save_node_code(manager, workflow, workflow_id, message_data)

    @staticmethod
    async def _handle_node_created(manager, workflow, workflow_id, data):
        # Get node class name
        node_class = data['class']
        
        # Generate a unique ID with class name + underscore + short UUID
        def generate_class_prefixed_id():
            return f"{node_class}_{str(uuid.uuid4())[:2]}"
        
        # Generate initial ID
        node_id = generate_class_prefixed_id()
        
        # Keep generating new IDs until we find a unique one
        while any(n['id'] == node_id for n in workflow['nodes']):
            node_id = generate_class_prefixed_id()
        
        workflow['nodes'].append({
            'id': node_id,
            'class': node_class,
            'config': {}
        })

        if not workflow['start']:
            workflow['start'] = node_id
            
        await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_node_deleted(manager, workflow, workflow_id, data):
        node_id = data['nodeId']
        is_start_node = workflow.get('start') == node_id

        workflow['nodes'] = [n for n in workflow['nodes'] if n['id'] != node_id]
        
        # Remove any edges connected to this node
        workflow['edges'] = [e for e in workflow['edges'] 
                            if e['from'] != node_id and e['to'] != node_id]
        
        if is_start_node and workflow['nodes']:
            import random
            new_start_node = random.choice(workflow['nodes'])
            workflow['start'] = new_start_node['id']

        if not workflow['nodes']:
            workflow['start'] = None

            
        await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_edge_created(manager, workflow, workflow_id, data):
        from_node = data['from']
        to_node = data['to']
        existing = any(e['from'] == from_node and e['to'] == to_node 
                      for e in workflow['edges'])
        nodes_exist = (any(n['id'] == from_node for n in workflow['nodes']) and
                      any(n['id'] == to_node for n in workflow['nodes']))
        
        if not existing and nodes_exist:
            workflow['edges'].append({
                'from': from_node,
                'to': to_node
            })
            await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_edge_deleted(manager, workflow, workflow_id, data):
        workflow['edges'] = [
            e for e in workflow['edges']
            if not (e['from'] == data['from'] and e['to'] == data['to'])
        ]
        await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_mark_as_start_node(manager, workflow, workflow_id, data):
        node_id = data['nodeId']
        workflow['start'] = node_id
        await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_set_edge_condition(manager, workflow, workflow_id, data):
        from_node = data['from']
        to_node = data['to']
        condition = data['condition']
        for edge in workflow['edges']:
            if edge['from'] == from_node and edge['to'] == to_node:
                edge['condition'] = condition
                break
        await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_set_initial_state(manager, workflow, workflow_id, data):
        workflow['initial_state'] = json.loads(data['initialState'])
        await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_save_node_config(manager, workflow, workflow_id, data):
        node_id = data['nodeId']
        config = json.loads(data['config'])
        for node in workflow['nodes']:
            if node['id'] == node_id:
                node['config'] = config
                break
        await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_save_node_code(manager, workflow, workflow_id, data):
        await manager.update_node_source(data['module'], data['class'], data['code'])