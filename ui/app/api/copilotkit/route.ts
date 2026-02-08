import {
  CopilotRuntime,
  GoogleGenerativeAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from '@copilotkit/runtime';
import { LangGraphAgent } from '@copilotkit/runtime/langgraph';
import { NextRequest } from 'next/server';

const serviceAdapter = new GoogleGenerativeAIAdapter({ model: 'gemini-2.0-flash' });
const deploymentUrl = process.env.AGENT_URL || ""

const runtime = new CopilotRuntime({
  agents: { 
    'chat': new LangGraphAgent({
      deploymentUrl,
      graphId: 'chat',
    }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: '/api/copilotkit',
  });
  return handleRequest(req);
};
