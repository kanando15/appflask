from flask import Flask, render_template, request, url_for, redirect, jsonify, send_file #para el servidor
import sqlite3 #para la base de datos
import openai #para usar chargpt
from flask_socketio import SocketIO, send, emit, join_room #para el chat
import pyttsx3 #para la voz
import os #permite el manejo de archivos
import json #para leer archivo con constantes
import re #para obtener datos del mapa
from mido import Message, MidiFile, MidiTrack #para la musica
import io #para la musica
import ast #para la musica
import speech_recognition as sr
import glob #para obtener nombre de archivos


#from flask_session import Session

app=Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)
app.config['UPLOAD_FOLDER'] = 'static'
# establece un directorio para almacenar las imágenes cargadas
IMAGES_UPLOAD_FOLDER = '/static/imagenes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['IMAGES_UPLOAD_FOLDER'] = IMAGES_UPLOAD_FOLDER

#variable global para el historial de chatGPT
with open('static/constantes.json', 'r') as f:
    constantes = json.load(f)

usuarios = constantes['usuarios']

context = {"role": "system",
               "content": "Eres un Dungeon Mater (DM) para Dungeon and Dragons (D&D) y "+usuarios}
messages = [[context]]
for i in range(20):
    messages.append([context])


@app.route('/', methods=['GET', 'POST'])
def index():
    #me aseguro que el usuario este completando el formulario
    data = {
        'titulo': 'INICIAR SESION'
    }
    if request.method == 'POST'and 'formulario' in request.form:
        mi_conexion = sqlite3.connect('database/dndbd')
        cursor = mi_conexion.cursor()
        hidden = request.form['formulario']
        if hidden == 'crear':
            newname = request.form['newname']
            newpassword = request.form['newpassword']
            try:
                query1 = "INSERT INTO jugador (nombre, contrasenia) \
                VALUES ('" + newname + "','" + newpassword + "')"
                cursor.execute(query1)
                query4 = "SELECT id_jugador, nombre FROM jugador where nombre='" + newname + "' and contrasenia='" + newpassword + "'"
                cursor.execute(query4)
                dinamico1 = cursor.fetchall()
                #esto no es seguro, se esta mostrando el usuario y contraseña
                mi_conexion.commit()
                mi_conexion.close()
                return redirect(url_for('sesion', id=dinamico1))
            except sqlite3.IntegrityError:
                query3 = "SELECT id_jugador, nombre FROM jugador where nombre='" + newname + "' and contrasenia='" + newpassword + "'"
                query2 = ""
                cursor.execute(query3)
                dinamico2 = cursor.fetchall()
                mi_conexion.close()
                return redirect(url_for('sesion', id=dinamico2))

        elif hidden == 'login':
            name = request.form['name']
            password = request.form['password']
            query2 = "SELECT nombre, contrasenia FROM jugador where nombre='"+name+"' and contrasenia='"+password+"'"
            cursor.execute(query2)
            results = cursor.fetchall()
            if len(results) == 0:
                confirmacion= "Usuario no encontrado, intente denuevo"
                return render_template('index.html', data=data, confirmacion=confirmacion)
            else:
                query3= "SELECT id_jugador, nombre FROM jugador where nombre='"+name+"' and contrasenia='"+password+"'"
                query2 = ""
                cursor.execute(query3)
                dinamico2 = cursor.fetchall()
                mi_conexion.close()
                return redirect(url_for('sesion', id=dinamico2))
        else:
            pass
        return render_template('index.html', data=data)
    else:
        print("Actualizando página")
        return render_template('index.html', data=data)


@app.route('/sesion/<id>', methods=['GET', 'POST'])
def sesion(id):

    mi_conexion = sqlite3.connect('database/dndbd')
    mi_conexion.close()
    id_tupla = eval(id)
    nombre = id_tupla[0][1]
    id_jugador =id_tupla[0][0]
    query1= "SELECT sesiones.* FROM sesiones \
            INNER JOIN conexion ON sesiones.id_sesion = conexion.id_sesion \
            WHERE conexion.id_jugador = '"+id[2]+"'"
    mi_conexion = sqlite3.connect('database/dndbd')
    cursor = mi_conexion.cursor()
    cursor.execute(query1)
    resultados = cursor.fetchall()
    datos = []
    encabezados = []
    for encabezado in cursor.description:
        encabezados.append(encabezado[0])
    for fila in resultados:
        datos.append(list(fila))
    encabezados.append("")
    encabezados.append("link")
    datas = {
        'titulo': 'SESIONES',
        'nombre': nombre,
        'id_user': id_jugador
    }

    if request.method == 'POST' and 'formulario' in request.form:
        hidden = request.form['formulario']
        if hidden == 'crear':
            newname = request.form['newname']
            newpassword = request.form['newpassword']
            try:
                query1 = "INSERT INTO sesiones (nombre, contrasenia, enlace, administrador, cantidad) \
                          VALUES ('" + newname + "','" + newpassword + "','asd','" + nombre + "', 1)"
                cursor.execute(query1)
                query2 = "SELECT id_sesion FROM sesiones WHERE nombre='" + newname + "'AND contrasenia='" + newpassword + "'"
                cursor.execute(query2)
                result1 = cursor.fetchall()
                idsesion = str(result1[0][0])
                id_jugador = str(id_jugador)
                query3 = "INSERT INTO conexion (id_sesion, id_jugador) VALUES ('" + idsesion + "','" + id_jugador + "')"
                cursor.execute(query3)
                mi_conexion.commit()
                mi_conexion.close()
                return render_template('sesion.html', encabezados=encabezados, datos=datos, datas=datas)
            except sqlite3.IntegrityError:
                confirmacion="esa sesion ya existe, intente con otra"
                mi_conexion.close()
                return render_template('sesion.html', encabezados=encabezados, datos=datos, datas=datas, confirmacion=confirmacion)

        elif hidden == 'login':
            name = request.form['name']
            password = request.form['password']
            query2 = "SELECT id_sesion, nombre, contrasenia FROM sesiones where nombre='" + name + "' and contrasenia='" + password + "'"
            cursor.execute(query2)
            results = cursor.fetchall()
            if len(results) == 0:
                confirmacion="Sesion no encontrada, intente denuevo"
                mi_conexion.close()
                return render_template('sesion.html', encabezados=encabezados, datos=datos, datas=datas, confirmacion=confirmacion)
            else:
                print(results)
                idsesion2 = str(results[0][0])

            #se corrobora la cantidad maxima de usuarios por sesion
                max_users_per_session = 4  # Establece tu propio límite
                query_check = "SELECT COUNT(*) FROM conexion WHERE id_sesion='" + idsesion2 + "'"
                cursor.execute(query_check)
                current_users = cursor.fetchone()[0]
                if current_users >= max_users_per_session:
                    confirmacion = "La sesión ha alcanzado su límite máximo de usuarios (4)."
                    mi_conexion.close()
                    return render_template('sesion.html', encabezados=encabezados, datos=datos, datas=datas, confirmacion=confirmacion)

                query3 = "INSERT INTO conexion (id_sesion, id_jugador) VALUES ('" + str(idsesion2) + "','" + str(id_jugador) + "')"
                query2 = ""
                cursor.execute(query3)
                dinamico2 = cursor.fetchall()
                confirmacion = "Sesion agregada a su listado"
                mi_conexion.commit()
                mi_conexion.close()
                return render_template('sesion.html', encabezados=encabezados, datos=datos, datas=datas, confirmacion=confirmacion)
        else:
            pass
        return render_template('sesion.html', encabezados=encabezados, datos=datos, datas=datas)
    else:
        print("Actualizando página")
        return render_template('sesion.html', encabezados=encabezados, datos=datos, datas=datas)


@app.route('/juego/<id>/<user>', methods=['GET', 'POST'])
def juego(id, user):
    #mi_conexion = sqlite3.connect('database/dndbd')
    #cursor = mi_conexion.cursor()
    #obtener las voces

    #se le entrega el listado de voces del sistema a la pagina
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    voice_name = []
    for i, voice in enumerate(voices):
        voice_name.append(voice.name)


    # Obtener la lista de jugadores en la sesión desde la base de datos
    mi_conexion = sqlite3.connect('database/dndbd')
    cursor = mi_conexion.cursor()
    query = "SELECT id_jugador FROM conexion WHERE id_sesion = '"+id+"'"
    cursor.execute(query)
    jugadores = cursor.fetchall()
    jugadores = [jugador[0] for jugador in jugadores]  # Convertir la lista de tuplas a una lista de strings
    print(jugadores)
    # Crear la lista de rutas de imágenes
    rutas_imagenes = []
    for jugador in jugadores:
        query2 = "SELECT nombre FROM jugador WHERE id_jugador = '" + str(jugador) + "'"
        cursor.execute(query2)
        nombre = cursor.fetchall()[0][0]
        for extension in ALLOWED_EXTENSIONS:
            ruta_imagen = f"{IMAGES_UPLOAD_FOLDER[1:]}/{id}_{jugador}.{extension}"  # Cambia la ruta según corresponda
            # Verificar si el archivo existe en la ruta
            if os.path.exists(ruta_imagen):
                diccionario_imagen = {'nombre': nombre, 'ruta': ruta_imagen}
                rutas_imagenes.append(diccionario_imagen)
                break  # Si encuentra el archivo, no verifica más extensiones

    query = "SELECT nombre FROM sesiones INNER JOIN conexion ON sesiones.id_sesion = conexion.id_sesion WHERE sesiones.id_sesion = '"+id+"' AND conexion.id_jugador = '"+user+"'"
    cursor.execute(query)
    aventura = cursor.fetchall()[0][0]
    mi_conexion.close()
    datas = {
        'titulo': 'Juego de Rol',
        'id':  id,
        'id_user': user,
        'aventura': aventura,
    }
    print(rutas_imagenes)
    return render_template('juego.html', datas=datas, voice_name=voice_name, rutas_imagenes=rutas_imagenes)

@app.route('/juego/<id>/<user>/mapa', methods=['POST'])
def recibir_coordenadas(id, user):
    if request.method == 'POST' and not request.is_json:
        # Aquí es donde obtendrías las nuevas coordenadas del mapa.
        # En este ejemplo, simplemente estoy devolviendo las mismas coordenadas cada vez.
        room = int(request.form['room'])
        user = request.form['user']
        with open('static/constantes.json', 'r') as f:
            constantes = json.load(f)
        mapRequest = constantes['mapRequest']
        coordenadas = chatgpt("user " + user + ": " + mapRequest, room)
        print(coordenadas)

        # Expresión regular para buscar el patrón
        patron = r"^\s*'?(.*?)'?\s*:\s*\[\s*([0-9]+),\s*([0-9]+)\s*\]"

        # Buscar todas las coincidencias en el texto
        coincidencias = re.findall(patron, coordenadas, re.MULTILINE)

        # Crear el diccionario de coordenadas
        coordinates = {}
        for nombre, x, y in coincidencias:
            coordinates[nombre] = [int(x), int(y)]

        print(coordinates)

        return jsonify({'coordinates': coordinates})



@app.route('/juego/<id>/<user>/imagen', methods=['POST'])
def recibir_imagen(id, user):
    file = request.files['file']
    # nombre con extension
    filename_CE = id + "_" + user + os.path.splitext(file.filename)[1]
    #nombre sin extension
    filename_SE = id + "_" + user

    # Busca todos los archivos que comienzan con el nombre base
    archivos = glob.glob(os.path.join(IMAGES_UPLOAD_FOLDER[1:] + "/" + filename_SE + ".*"))    # Elimina cada archivo
    for archivo in archivos:
        os.remove(archivo)

    file.save(IMAGES_UPLOAD_FOLDER[1:] + "/"+filename_CE)
    return 'Archivo cargado exitosamente'


@app.route('/juego/<id>/<user>/microfono', methods=['POST'])
def recibir_microfono(id, user):
    if request.method == 'POST':
        if 'audio_data' in request.files:
            audio_file = request.files['audio_data']
        # Aquí puedes realizar las acciones que desees con el archivo de audio
        # Por ejemplo, guardar el archivo en el sistema de archivos
            audio_file.save('static/microfono.wav')
            filename = "static/microfono.wav"
            message = transcribe_audio_to_test(filename)
            print(message)
            return jsonify(message)
        else:
            return 'No se proporcionó ningún archivo de audio'


def transcribe_audio_to_test(filename):
    recogizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recogizer.record(source)
    try:
        return recogizer.recognize_google(audio)
    except:
        print("skipping unkown error")


@app.route('/juego/<id>/<user>/music', methods=['POST'])
def music(id, user):
    if request.method == 'POST':
        data = request.get_json()  # obtienes los datos JSON como un diccionario de Python
        room = data.get('room')  # esto te da los datos como un objeto MultiDict
        music_request = constantes['music_request']
        solicitud = chatgpt(music_request, room)
        print(solicitud)
        response_content=chatgpt_sin_room(solicitud)

        melody_pitch_duration_data = extract_melody(response_content)
        # Constants
        TICKS_PER_BEAT = 480  # Standard for most DAWs
        BEATS_PER_MINUTE = 120  # Tempo
        SECONDS_PER_MINUTE = 60
        TICKS_PER_SECOND = TICKS_PER_BEAT * BEATS_PER_MINUTE / SECONDS_PER_MINUTE

        # Create a new MIDI file
        mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)

        # Create a new track
        track = MidiTrack()

        # Append the track to the MIDI file
        mid.tracks.append(track)

        # Convert your data into MIDI events
        for note, duration in melody_pitch_duration_data:
            # If there's a silence, don't make a note event
            if note != 0:
                # Add a note on event
                track.append(Message('note_on', note=note, velocity=64, time=0))

            # Wait for the duration of the note/silence
            # We multiply by TICKS_PER_SECOND because duration is in seconds
            track.append(Message('note_off', note=note, velocity=64, time=int(duration * TICKS_PER_SECOND)))

        # Save the MIDI file
        filename = f"melody_{id}_{user}.mid"
        filepath = os.path.join('static', filename)
        mid.save(filepath)

        # return the URL of the file
        return jsonify({"url": "/" + filepath})


@socketio.on('map-updated')
def handleMessage(data):
    room = data['room']
    coordinates = data['coordinates']
    emit('map-updated', coordinates, room=room)

@socketio.on('message')
def handleMessage(data):
    room = data['room']
    message = data['message']
    user = str(data['user'])
    print(f'Mensaje recibido en la sala {room}: {message}')
    emit('message', message, room=room)
    print(user +": "+message, room)
    response = chatgpt("user "+user +": "+message, room)
    emit('message', response, room=room)
    
    #dar mensaje de audio
    voice = data['voice']
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('rate', 150)  # Velocidad de habla (palabras por minuto)
    engine.setProperty('voice', voices[0].name)  # Idioma seleccionado por default

    if voices[0].name != voice:
        for i in range(len(voices)):
            if voice == voices[i].name:
                engine.setProperty('voice', voices[i].id)
                print("voz cambiada a: ", voices[i].name)

    # eliminar archivo previo si existe
    archivo_output = "static/output.mp3"
    if os.path.exists(archivo_output):
        os.remove(archivo_output)
    engine.save_to_file(response, 'static/output.mp3')
    engine.runAndWait()
    # Enviar el archivo de audio al cliente a través del socket
    #emit('audio', {'filename': 'output.mp3'})
    emit('audio', {'filename': 'static/output.mp3'}, room=room)


@socketio.on('join')
def on_join(room):
    join_room(room)
    print(f'Cliente unido a la sala: {room}')

#queda pendiente terminar la funcionalidad
def dalle(request):
    content = request
    response = openai.Image.create(
        prompt=content,
        n=1,
        size="256x256"
    )
    image_url = response['data'][0]['url']
    return image_url
#dalle("a player sprite for a tiled dungeon and dragons map");

def chatgpt_sin_room(request):

    openai.api_key = "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"
    contexto = {"role": "system", "content": constantes['music_rules']}
    mensaje = [contexto]
    response1 = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=mensaje)
    mensaje.append({"role": "assistant", "content": response1['choices'][0]['message']['content']})
    user_message = {"role": "user", "content": constantes['request_start']+"'"+request+"'"}
    mensaje.append(user_message)
    response2 = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=mensaje)

    #en algunos casos, GPT entrega mas de una respuesta, por lo que definimos obtener siempre la primera
    response_content = response2.choices[0].message.content

    #print(response_content)
    return response_content



def extract_melody(text):
    start_keyword = "melody_pitch_duration_data = ["
    end_keyword = "]"

    start_index = text.find(start_keyword)
    end_index = text.find(end_keyword, start_index) + len(end_keyword)

    # Verify if keywords were found in the text
    if start_index == -1 or end_index == -1:
        return None

    raw_melody = text[start_index:end_index].strip()

    # Remove the assignment part to get only the list
    melody_list = raw_melody.replace(start_keyword, "").strip()

    # Extract the tuple values using regex
    tuples_str = re.findall(r'\(\d+,\s*\d+(?:\.\d+)?\)', melody_list)

    # Convert the tuples from string to actual tuples
    tuples = [ast.literal_eval(t) for t in tuples_str]
    print(tuples)
    return tuples



def chatgpt(request, room):

    openai.api_key = "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"
    global messages

    content = request
    messages[room].append({"role": "user", "content": content})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages[room])

    #en algunos casos, GPT entrega mas de una respuesta, por lo que definimos obtener siempre la primera
    response_content = response.choices[0].message.content

    messages[room].append({"role": "assistant", "content": response_content})

    return response_content


#redirige  el error 404
def pagina_no_encontrada(error):
    return render_template('404.html'), 404
    #return redirect(url_for('index'))


if __name__=='__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    #app.run(debug=True, port=5000)
    socketio.run(app, debug=True, port=5000)
    #socketio.run(app)
    #socketio = SocketIO(app, async_mode='threading')

