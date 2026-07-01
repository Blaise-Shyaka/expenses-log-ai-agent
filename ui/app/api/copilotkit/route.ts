import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from '@copilotkit/runtime';
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";
import { NextRequest } from 'next/server';

const serviceAdapter = new ExperimentalEmptyAdapter();
const deploymentUrl = process.env.AGENT_URL || "http://localhost:8123"

const runtime = new CopilotRuntime({
  agents: {
    chat: new LangGraphHttpAgent({
      url: deploymentUrl,
    }),
  }
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: '/api/copilotkit',
  });
  return handleRequest(req);
};
