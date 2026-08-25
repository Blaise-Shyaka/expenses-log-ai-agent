import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";
import { NextRequest } from "next/server";

const serviceAdapter = new ExperimentalEmptyAdapter();
const deploymentUrl = process.env.AGENT_URL ?? "http://localhost:8123";

const runtime = new CopilotRuntime({
  agents: {
    chat: new LangGraphHttpAgent({
      url: deploymentUrl,
    }),
  },
});

export const POST = async (req: NextRequest) => {
  // The client attaches its own current access token (see app/page.tsx's
  // <CopilotKit headers={...}>, kept fresh by useSession() + SessionRefresh).
  // CopilotKit's runtime forwards the inbound Authorization header to the
  // agent automatically (see @copilotkit/runtime's mergeForwardableHeaders),
  // so there's nothing to inject here — this route doesn't need to resolve
  // the session at all, which sidesteps the whole "auth() won't persist a
  // refreshed cookie from a Route Handler" problem by not calling it.
  if (!req.headers.get("Authorization")) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
