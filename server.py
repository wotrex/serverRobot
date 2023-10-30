from aiohttp import web, WSMsgType, ClientSession
from aiohttp.web import WebSocketResponse
import numpy as np
import cv2, asyncio, uuid
from threading import Thread
from flask import Flask, request, render_template, Response, jsonify


frame = None
frame2 = None

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
            
def main2():
    global frame2
    while True:
        if frame2 is not None:
            ret, buffer = cv2.imencode('.jpg', frame2)
            image = buffer.tobytes()
            yield (b'--frame\r\n'
            
                            b'Content-Type: image/jpeg\r\n\r\n' + image + b'\r\n')
    
@app.route("/")

def index():

    return render_template('index.html')


@app.route('/video')

def video():

    return Response(main(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video2')

def video2():

    return Response(main2(), mimetype='multipart/x-mixed-replace; boundary=frame')

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
    try:
        ws = websocket_connections.get(client_id)
        await ws.send_json(data)
    except:
        pass

async def handleVideo(request):
    global frame
    ws = WebSocketResponse()
    await ws.prepare(request)
    print('Client connected: ' + request.remote)

    while True:
        msg = await ws.receive()
        if msg.type == WSMsgType.binary:
            frame_data = msg.data
            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            # Отримані кадри можна відображати, наприклад, за допомогою OpenCV
##            cv2.imshow('Server Video', frame)
##            cv2.waitKey(1)
        elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
            print('Client disconnected: ' + request.remote)
            break

    return ws

async def handleVideo2(request):
    global frame2
    ws = WebSocketResponse()
    await ws.prepare(request)
    print('Client connected: ' + request.remote)

    while True:
        msg = await ws.receive()
        if msg.type == WSMsgType.binary:
            frame_data = msg.data
            frame2 = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            # Отримані кадри можна відображати, наприклад, за допомогою OpenCV
##            cv2.imshow('Server Video', frame)
##            cv2.waitKey(1)
        elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
            print('Client disconnected: ' + request.remote)
            break

    return ws

async def send_handler(request):
    ws = WebSocketResponse()
    await ws.prepare(request)
    client_id = generate_unique_client_id()  # Генерувати унікальний ідентифікатор для кожного клієнта
    websocket_connections[client_id] = ws  # Зберігати посилання на WebSocket з'єднання
    print('Client connected: ' + request.remote)
    while True:
        try:
            msg = await ws.receive()
            if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
                del websocket_connections[client_id]
                print('Client disconnected: ' + request.remote)
                break
        except:
            print('Error')
    return ws

if __name__ == '__main__':
    t1 = Thread(target = start_flask)
    t1.start()
    WebApp = web.Application()
    WebApp.add_routes([web.get('/ws', handleVideo),
                web.get('/send', send_handler),
                web.get('/ws2', handleVideo2)])
    web.run_app(WebApp)
