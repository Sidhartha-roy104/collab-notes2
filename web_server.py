from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

clients = set()
shared_text = ""

@app.get("/")
async def home():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
  <title>Realtime Collaborative Notes</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    textarea { width: 100%; height: 400px; font-size: 16px; }
  </style>
</head>
<body>
  <h2>Realtime Collaborative Notes</h2>
  <textarea id="editor" placeholder="Start typing..."></textarea>

  <script>
    const protocol = location.protocol === "https:" ? "wss://" : "ws://";
    const ws = new WebSocket(protocol + location.host + "/ws");

    const editor = document.getElementById("editor");
    let isRemoteUpdate = false;

    ws.onopen = () => {
      console.log("WebSocket connected!");
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };

    ws.onmessage = (event) => {
      // Save cursor position before update
      const start = editor.selectionStart;
      const end = editor.selectionEnd;
      
      isRemoteUpdate = true;
      editor.value = event.data;
      
      // Restore cursor position after update
      editor.setSelectionRange(start, end);
      isRemoteUpdate = false;
    };

    editor.addEventListener("input", () => {
      if (!isRemoteUpdate) {
        ws.send(editor.value);
      }
    });
  </script>
</body>
</html>
""")

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global shared_text
    await ws.accept()
    clients.add(ws)
    
    print(f"Client connected. Total clients: {len(clients)}")

    # Send current content to new client
    await ws.send_text(shared_text)

    try:
        while True:
            data = await ws.receive_text()
            shared_text = data

            # Broadcast to ALL clients (including sender for consistency)
            for client in list(clients):  # Use list() to avoid modification during iteration
                try:
                    await client.send_text(shared_text)
                except:
                    # Remove dead connections
                    clients.discard(client)
    except Exception as e:
        print(f"Client disconnected: {e}")
    finally:
        clients.discard(ws)
        print(f"Client removed. Total clients: {len(clients)}")


# Run the server directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)