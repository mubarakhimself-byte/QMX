// POST acknowledges a request; its JSON-RPC reply arrives on the SSE stream.
import http from "node:http";

export class ReticleMcp {
  constructor(base, timeoutMs) {
    this.base = new URL(base);
    this.timeoutMs = timeoutMs;
    this.nextId = 1;
    this.pending = new Map();
  }
  async connect() {
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.close();
        reject(new Error("MCP endpoint announcement timeout"));
      }, this.timeoutMs);
      const fail = (error) => {
        clearTimeout(timer);
        reject(error);
        for (const item of this.pending.values()) item.reject(error);
        this.pending.clear();
      };
      this.stream = http.get(new URL("/mcp/sse", this.base), (response) => {
        if (response.statusCode !== 200) {
          response.resume();
          fail(new Error(`MCP stream HTTP ${response.statusCode}`));
          return;
        }
        this.response = response;
        let buffer = "";
        response.setEncoding("utf8");
        response.on("error", fail);
        response.on("end", () => fail(new Error("MCP stream closed")));
        response.on("data", (chunk) => {
          try {
            buffer += chunk.replace(/\r\n/g, "\n");
            if (buffer.length > 2 * 1024 * 1024)
              throw new Error("MCP frame too large");
            let end;
            while ((end = buffer.indexOf("\n\n")) !== -1) {
              const frame = buffer.slice(0, end);
              buffer = buffer.slice(end + 2);
              const event = /^event: ?(.*)$/m.exec(frame)?.[1] || "message";
              const data = [...frame.matchAll(/^data: ?(.*)$/gm)]
                .map((m) => m[1])
                .join("\n");
              if (event === "endpoint") {
                const endpoint = new URL(data, this.base);
                if (
                  endpoint.origin !== this.base.origin ||
                  endpoint.pathname !== "/mcp/message"
                ) {
                  throw new Error("MCP announced an unexpected endpoint");
                }
                this.endpoint = endpoint;
                clearTimeout(timer);
                resolve();
              } else if (data && event === "message") {
                const message = JSON.parse(data);
                const item = this.pending.get(message.id);
                if (!item) continue;
                this.pending.delete(message.id);
                if (message.error)
                  item.reject(new Error(message.error.message || "MCP error"));
                else item.resolve(message.result);
              }
            }
          } catch (error) {
            fail(error);
            this.close();
          }
        });
      });
      this.stream.on("error", fail);
    });
    await this.call("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "qmx-unattended-reticle", version: "1" },
    });
    await this.post({ jsonrpc: "2.0", method: "notifications/initialized" });
  }
  async post(message) {
    const response = await fetch(this.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message),
      signal: AbortSignal.timeout(this.timeoutMs),
    });
    if (!response.ok) throw new Error(`MCP POST HTTP ${response.status}`);
    await response.body?.cancel();
  }
  async call(method, params) {
    const id = this.nextId++;
    let timer;
    const reply = new Promise((resolve, reject) => {
      timer = setTimeout(
        () => reject(new Error(`MCP ${method} response timeout`)),
        this.timeoutMs,
      );
      this.pending.set(id, { resolve, reject });
    });
    try {
      const [, result] = await Promise.all([
        this.post({ jsonrpc: "2.0", id, method, params }),
        reply,
      ]);
      return result;
    } finally {
      clearTimeout(timer);
      this.pending.delete(id);
    }
  }
  close() {
    this.response?.destroy();
    this.stream?.destroy();
    for (const item of this.pending.values())
      item.reject(new Error("MCP connection closed"));
    this.pending.clear();
  }
}

export function payload(result) {
  if (result?.isError) {
    const detail = (result.content || [])
      .filter((c) => c.type === "text")
      .map((c) => c.text)
      .join(" ");
    throw new Error(`Reticle tool error: ${detail.slice(0, 1200)}`);
  }
  if (result?.structuredContent) return result.structuredContent;
  for (const item of result?.content || []) {
    if (item.type === "text") {
      try {
        return JSON.parse(item.text);
      } catch {
        /* try the next text block */
      }
    }
  }
  throw new Error("Reticle returned no structured result");
}
