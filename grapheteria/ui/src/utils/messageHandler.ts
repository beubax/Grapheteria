import useStore from "../stores/useStore";

export function createMessageHandlers() {
  const messageHandlers = {
    init: (message: any) => {
      useStore.getState().setWorkflows(message.workflows);
      useStore.getState().setAvailableNodes(message.nodes);
      console.log(message.nodes);
    },

    available_workflows: (message: any) => {
      console.log(message.workflows);
      useStore.getState().setWorkflows(message.workflows);
      useStore.getState().updateFlowStructure();
      useStore.getState().updateFlowStatus();
    },
    available_nodes: (message: any) => {
      console.log("Received available nodes");
      useStore.getState().setAvailableNodes(message.nodes);
      useStore.getState().updateFlowStructure();
      useStore.getState().updateFlowStatus();
      console.log(message.nodes);
    },
  } as Record<string, (message: any) => void>;

  return function handleMessage(message: Record<string, any>) {
    const handler = messageHandlers[message.type as keyof typeof messageHandlers];
    if (handler) {
      handler(message);
    }
  };
}