from machine import WorkflowEngine

class InboundHandler:
    @staticmethod
    async def handle_client_message(manager, websocket, message_data):
        message_type = message_data.get('type', '')
        
        # Handle log-related messages
        if message_type.startswith('log_'):
            await InboundHandler._handle_log_message(manager, websocket, message_data)
            
        # Handle workflow editing messages
        workflow_id = message_data.get('workflow_id')
        if not workflow_id or workflow_id not in manager.workflows:
            return
        
        if message_type == 'step':
            print(f"Stepping workflow {workflow_id} with run {message_data.get('run_id')} at timestamp {message_data.get('current_timestamp')}")
            workflow_path = manager.workflow_paths[workflow_id]
            workflow = WorkflowEngine(json_path=workflow_path, run_id=message_data.get('run_id'), resume_timestamp=message_data.get('current_timestamp'))
            await workflow.step()
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

    @staticmethod
    async def _handle_node_created(manager, workflow, workflow_id, data):
        if any(n['id'] == data['nodeId'] for n in workflow['nodes']):
            return
            
        workflow['nodes'].append({
            'id': data['nodeId'],
            'class': data['nodeType'],
            'config': {}
        })
        await manager.save_workflow(workflow_id)

    @staticmethod
    async def _handle_node_deleted(manager, workflow, workflow_id, data):
        node_id = data['nodeId']
        workflow['nodes'] = [n for n in workflow['nodes'] if n['id'] != node_id]
        workflow['edges'] = [e for e in workflow['edges'] 
                            if e['from'] != node_id and e['to'] != node_id]
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
                'to': to_node,
                'condition': 'True'
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
    async def _handle_log_message(manager, websocket, data):
        """Handle all log-related messages"""
        from server.utils.scanner import SystemScanner
        from server.handlers.outbound_handler import OutboundHandler
        
        match data['type']:
            case 'log_start_debug_session':
                print(f"Starting debug session for workflow {data.get('workflow_id')} with run {data.get('run_id')}")
                print(f"Debug sessions: {manager.debug_sessions}")
                # Store which run this client is debugging
                workflow_id = data.get('workflow_id')
                run_id = data.get('run_id')
                
                if not workflow_id or not run_id or workflow_id not in manager.workflows:
                    return
                    
                manager.debug_sessions[websocket] = {
                    'workflow_id': workflow_id,
                    'run_id': run_id
                }
            
            case 'log_end_debug_session':
                print(f"Ending debug session for workflow {data.get('workflow_id')} with run {data.get('run_id')}")
                print(f"Debug sessions: {manager.debug_sessions}")
                if websocket in manager.debug_sessions:
                    del manager.debug_sessions[websocket]
            
            case 'log_get_workflow_runs':
                workflow_id = data.get('workflow_id')
                if not workflow_id:
                    return
                    
                runs = await SystemScanner.get_workflow_runs(workflow_id)
                await OutboundHandler.send_workflow_runs(websocket, workflow_id, runs)
            
            case 'log_get_run_states':
                workflow_id = data.get('workflow_id')
                run_id = data.get('run_id')
                
                if not workflow_id or not run_id:
                    return
                    
                states = await SystemScanner.get_run_states(workflow_id, run_id)
                await OutboundHandler.send_run_states(websocket, workflow_id, run_id, states)
