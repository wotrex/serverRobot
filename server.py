import aiohttp
from aiohttp import web, WSMsgType, ClientSession
from aiohttp.web import WebSocketResponse
import numpy as np
import cv2, socket, pickle
from threading import Thread
from flask import Flask, request, render_template, Response, jsonify


data = None
frame = None

################################################socket###############

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 9999))
server.listen(1)


def socket_server():
    client_socket = 0
    client_address = 0
    global data
    while True:
        if client_socket == 0:
            client_socket, client_address = server.accept()
            print(client_address, ' connected')
        else:
            if data is not None:
                data_to_send_serialized = pickle.dumps(data)
                client_socket.send(data_to_send_serialized)
                data = None

            try:
                client_socket.setblocking(0)
                data_recv = client_socket.recv(1024)
                if not data_recv:
                    print(client_address, " disconnected")
                    client_socket.close()
                    client_socket = 0
                    continue
            except socket.error as e:
                pass
            client_socket.setblocking(1)

            


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
    global data
    data = request.get_json()
    return jsonify({'message': 'Data gets'})

def start_flask():

    app.run(host='0.0.0.0', debug=True, use_reloader=False)



#####################################Server video#################################
    
async def handle(request):
    global frame
    global data
    ws = WebSocketResponse()
    await ws.prepare(request)

    while True:
        msg = await ws.receive()
        if msg.type == WSMsgType.binary:
            frame_data = msg.data
            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            # Отримані кадри можна відображати, наприклад, за допомогою OpenCV
##            cv2.imshow('Server Video', frame)
##            cv2.waitKey(1)
        elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
            break

    return ws


if __name__ == '__main__':
    t1 = Thread(target = start_flask)
    t1.start()
    t2 = Thread(target = socket_server)
    t2.daemon = True
    t2.start()
    WebApp = web.Application()
    WebApp.router.add_get('/ws', handle)
    web.run_app(WebApp)
