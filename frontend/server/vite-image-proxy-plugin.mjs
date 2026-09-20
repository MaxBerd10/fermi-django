import { handleImageProxyRequest } from "./image-proxy.mjs";

export function fjstiImageProxyPlugin() {
  // Same env var production-server.mjs reads for the same reason — see
  // image-proxy.mjs's SELF_ORIGINS comment for why self-referential media
  // URLs need to be fetched from here rather than from their own public origin.
  const fermiApiBaseUrl = String(process.env.FERMI_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
  const mount = (middlewares) => {
    middlewares.use(async (req, res, next) => {
      if (!req.url?.startsWith("/img-cache")) return next();
      const handled = await handleImageProxyRequest(req, res, fermiApiBaseUrl);
      if (!handled) next();
    });
  };

  return {
    name: "fjsti-image-proxy",
    configureServer(server) {
      mount(server.middlewares);
    },
    configurePreviewServer(server) {
      mount(server.middlewares);
    },
  };
}
