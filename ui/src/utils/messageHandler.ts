import useStore from "../stores/useStore";

export function createMessageHandlers() {
  const messageHandlers = {
    available_workflows: (message: any) => {
      useStore.getState().setWorkflows(message.workflows);
      useStore.getState().updateFlow();
    },
    available_nodes: (message: any) => {
      useStore.getState().setAvailableNodes(message.nodes);
    },
    execution_state_update: (message: any) => {
      const timestamp = message.data.metadata.save_time;
      const shared_store = message.data.shared;
      const node_statuses = message.data.node_statuses;
      const current_node_ids = message.data.current_node_ids;
      useStore.getState().addDebugState({
        timestamp: timestamp,
        stateVariables: shared_store,
        node_statuses: node_statuses,
        current_node_ids: current_node_ids
      });
    },
  } as Record<string, (message: any) => void>;

  return function handleMessage(message: Record<string, any>) {
    const handler = messageHandlers[message.type as keyof typeof messageHandlers];
    if (handler) {
      handler(message);
    }
  };
}