from aiohttp import web, WSMsgType, ClientSession
from aiohttp.web import WebSocketResponse
import numpy as np
import cv2, asyncio, uuid
from threading import Thread
from flask import Flask, request, render_template, Response, jsonify


frame = None
close = False

##############################################Flask########################
app = Flask(__name__)

def main():
    global frame
    while True:
        if frame is not None:
            ret, buffer = cv2.imencode('.jpg', frame)
            image = buffer.tobytes()
            yield (b'--frame\r\n'
            
                            b'Content-Type: image/jpeg\r\n\r\n' + image + b'\r\n')
    
@app.route("/")

def index():

    return render_template('index.html')


@app.route('/video')

def video():

    return Response(main(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/gamepad_data', methods=['POST'])
def gamepad_data():
    data = request.get_json()
    for client_id in websocket_connections:
        asyncio.run(send_data_via_ws(client_id, data))
    return jsonify({'message': 'Data gets'})

def start_flask():

    app.run(host='0.0.0.0', debug=True, use_reloader=False)



#####################################Server video#################################

websocket_connections = {}

def generate_unique_client_id():
    return str(uuid.uuid4())

async def send_data_via_ws(client_id, data):
    ws = websocket_connections.get(client_id)
    
    await ws.send_json(data)

async def handle(request):
    global frame
    ws = WebSocketResponse()
    await ws.prepare(request)
    client_id = generate_unique_client_id()  # Генерувати унікальний ідентифікатор для кожного клієнта
    websocket_connections[client_id] = ws  # Зберігати посилання на WebSocket з'єднання
    print('Client connected: ' + client_id)


    while True:
        msg = await ws.receive()
        if msg.type == WSMsgType.binary:
            frame_data = msg.data
            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            # Отримані кадри можна відображати, наприклад, за допомогою OpenCV
##            cv2.imshow('Server Video', frame)
##            cv2.waitKey(1)
        elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
            del websocket_connections[client_id]  # При завершенні з'єднання видаляємо його зі словника
            print('Client disconnected: ' + client_id)
            break

    return ws


if __name__ == '__main__':
    t1 = Thread(target = start_flask)
    t1.start()
    WebApp = web.Application()
    WebApp.router.add_get('/ws', handle)
    web.run_app(WebApp)
