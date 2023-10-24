import cv2
import imagezmq

from flask import Flask, request, render_template, Response, jsonify
import ffmpeg
import socket, pickle
import threading
import time


app = Flask(__name__)


image_hub = imagezmq.ImageHub(open_port='tcp://*:5556')
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('0.0.0.0', 8989))
serversocket.listen(2)

data = None

def main():

    while True:
        try:

            rpi_name, frame = image_hub.recv_image()

            image_hub.send_reply(b'OK')  #<<-- do NOT use this with PUB / SUB mode]

            process = (
                ffmpeg.input('pipe:0', format='rawvideo', pix_fmt='yuv420p', s='{}x{}'.format(300, 300))
                .output('pipe:1', format='rawvideo', pix_fmt='bgr24')
                .run(input=frame)
            )
            uncompressed_frame = process.communicate()[0]
    
    
            ret, buffer = cv2.imencode('.jpg', uncompressed_frame)
    
            frame = buffer.tobytes()
    
            yield (b'--frame\r\n'
    
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except:
            print('imageZmq error')


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

c = 0
addr = 0


def gamepad_send():

    global data
    global c
    global addr

    while True:

        if c == 0:

           c, addr = serversocket.accept()

           print(str(addr) + " connected.")

           t2 = threading.Thread(target = time_con)

           t2.start()

        else:

           try:
               if data is not None:

                  data_arr = pickle.dumps(data)

                  c.sendall(data_arr)

                  data = None
           except:
                  c.close()

                  c = 0

                  print(str(addr) + " disconnected")

                  continue
           if serversocket is None:
              break

def time_con():
    global c
    global addr
    print('con')
    while True:	     
        time.sleep(2)
        try:
           data = c.recv(64)
           print(data)
           if not data:
              c.close()
              c = 0
              print(str(addr) + " disconnected")
              break
        except:
           c.close()
           c = 0
           print(str(addr) + " disconnected")
           break	

t1 = threading.Thread(target=gamepad_send)
t1.start()

app.run(host='0.0.0.0', debug=True, use_reloader=False)
