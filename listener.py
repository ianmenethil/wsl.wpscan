import websocket

websocket.enableTrace(True)
ws = websocket.WebSocketApp('ws://127.0.0.1:53623/devtools/browser/aa117b69-6e31-48d0-960e-2743dc314ead')


def on_open(ws):

    pass


ws.on_open = on_open
