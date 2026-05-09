from flask import Flask, render_template, Response, jsonify
import os
import cv2
import numpy as np

base_dir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.join(base_dir, '../frontend')

app = Flask(__name__, 
            template_folder=frontend_dir, 
            static_folder=os.path.join(frontend_dir, 'static'))

camera = cv2.VideoCapture(0)

# Variabel global untuk menyimpan apa yang sedang dilihat AI saat ini
deteksi_sekarang = ""

def generate_frames():
    global deteksi_sekarang
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            lower_blue = np.array([90, 130, 50])
            upper_blue = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv_frame, lower_blue, upper_blue)
            
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            objek_ditemukan = "" # Kosongkan status setiap kali melihat frame baru
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:
                    keliling = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.04 * keliling, True)
                    
                    nama_bentuk = "Benda"
                    jumlah_sudut = len(approx)
                    
                    if jumlah_sudut == 3:
                        nama_bentuk = "Segitiga"
                    elif jumlah_sudut == 4:
                        nama_bentuk = "Kotak"
                    elif jumlah_sudut > 5:
                        nama_bentuk = "Lingkaran"

                    x, y, w, h = cv2.boundingRect(contour)
                    teks_tampil = f"{nama_bentuk} Biru"
                    
                    # Simpan hasil untuk dikirim ke Web
                    objek_ditemukan = teks_tampil
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 3)
                    cv2.putText(frame, teks_tampil, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            
            # Update variabel global dengan apa yang ditemukan di frame ini
            deteksi_sekarang = objek_ditemukan

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- INI JALUR KOMUNIKASI BARU UNTUK BROWSER ---
@app.route('/data_deteksi')
def data_deteksi():
    return jsonify({"hasil": deteksi_sekarang})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)