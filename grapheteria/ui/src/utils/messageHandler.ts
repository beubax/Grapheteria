import useStore from "../stores/useStore";

export function createMessageHandlers() {
  const messageHandlers = {
    init: (message: any) => {
      console.log("workflows", message.workflows);
      useStore.getState().setWorkflows(message.workflows);
      useStore.getState().setAvailableNodes(message.nodes);
      useStore.getState().setTools(message.tools);
      useStore.getState().setAuthenticatedTools(message.authenticated_tools);
    },

    updated_state: (message: any) => {
      console.log("workflows", message.workflows);
      useStore.getState().setNotificationFlag(true);
      useStore.getState().setWorkflows(message.workflows);
      useStore.getState().setAvailableNodes(message.nodes);
      useStore.getState().updateFlowStructure();
      useStore.getState().updateFlowStatus();
    },
  } as Record<string, (message: any) => void>;

  return function handleMessage(message: Record<string, any>) {
    const handler = messageHandlers[message.type as keyof typeof messageHandlers];
    if (handler) {
      handler(message);
    }
  };
}