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
  } as Record<string, (message: any) => void>;

  return function handleMessage(message: Record<string, any>) {
    const handler = messageHandlers[message.type as keyof typeof messageHandlers];
    if (handler) {
      handler(message);
    }
  };
}