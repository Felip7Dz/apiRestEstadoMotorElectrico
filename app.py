#!/usr/bin/env python
# encoding: utf-8
import os
import shutil
import warnings
import keras
import csv

import pandas as pd
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
import enter_utils

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost:3306/PreLoadedDatasets'
app.config['SQLALCHEMY_BINDS'] = {'users': 'mysql+mysqlconnector://root:password@localhost:3306/RegisteredUsers'}
db = SQLAlchemy(app)


class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), unique=True, nullable=False)
    shaft_frequency = db.Column(db.Double, nullable=False)
    sampling_frequency = db.Column(db.Integer, nullable=False)
    carga = db.Column(db.Double, nullable=False)
    bearing_type = db.Column(db.String(255), nullable=False)
    bpfo = db.Column(db.Double, nullable=False)
    bpfi = db.Column(db.Double, nullable=False)
    bsf = db.Column(db.Double, nullable=False)
    ftf = db.Column(db.Double, nullable=False)
    min_to_check = db.Column(db.Integer, nullable=False)
    max_to_check = db.Column(db.Integer, nullable=False)
    files_added = db.Column(db.Integer, nullable=False)


class Usuarios(db.Model):
    __tablename__ = 'Usuarios'
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(255), unique=True, nullable=False)
    apellido = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    passw = db.Column(db.String(255), unique=True, nullable=False)
    roles = db.Column(db.String(255), unique=True, nullable=False)
    maxdataset = db.Column(db.Integer, nullable=False)


@app.route('/checkUser/<string:username>', methods=['GET'])
def checkUser(username):
    user_preloaded = Usuarios.query.filter_by(usuario=username).first()

    if user_preloaded:
        return '0', 200

    return '1', 200


@app.route('/registerUser', methods=['POST'])
def registerUser():
    try:
        data = request.json

        new_user = Usuarios(
            usuario=data['usuario'],
            nombre=data['nombre'],
            apellido=data['apellido'],
            email=data['email'],
            passw=data['passw'],
            roles=data['role'],
            maxdataset=data['maxdataset']
        )

        db.session.add(new_user)
        db.session.commit()

        return '0', 201

    except Exception as e:
        print(f"IntegrityError: {str(e)}")
        return '1', 500


@app.route('/getUser/<string:username>', methods=['GET'])
def getUserByName(username):
    try:
        user = Usuarios.query.filter_by(usuario=username).first()
        if user:
            return jsonify({
                'usuario': user.usuario,
                'nombre': user.nombre,
                'apellido': user.apellido,
                'email': user.email,
                'maxdataset': user.maxdataset
            })
        else:
            return jsonify({'nombre': 'Dataset not found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getAllUsers', methods=['GET'])
def getAllUsers():
    try:
        users = Usuarios.query.all()
        if users:
            users_list = []
            for user in users:
                user_data = {
                    'usuario': user.usuario,
                    'nombre': user.nombre,
                    'apellido': user.apellido,
                    'email': user.email,
                    'role': user.roles,
                    'maxdataset': user.maxdataset
                }
                users_list.append(user_data)
            return jsonify(users_list)
        else:
            return jsonify({'message': 'No users found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/updateUser/<string:username>', methods=['PUT'])
def updateUser(username):
    try:
        data = request.json
        user = Usuarios.query.filter_by(usuario=username).first()

        user.usuario = data.get('usuario', user.usuario)
        user.nombre = data.get('nombre', user.nombre)
        user.apellido = data.get('apellido', user.apellido)
        user.email = data.get('email', user.email)
        user.passw = data.get('passw', user.passw)
        user.maxdataset = data.get('maxdataset', user.maxdataset)
        db.session.commit()

        return jsonify({'message': 'Dataset actualizado correctamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/deleteUser/<string:username>', methods=['DELETE'])
def deleteUser(username):
    try:
        user = Usuarios.query.filter_by(usuario=username).first()

        db.session.delete(user)
        db.session.commit()

        folder_path1 = 'prog_analizador/saved_models/' + username
        folder_path2 = 'prog_analizador/saved_data/' + username
        if os.path.exists(folder_path1) and os.path.isdir(folder_path1):
            os.rmdir(folder_path1)
        if os.path.exists(folder_path2) and os.path.isdir(folder_path2):
            os.rmdir(folder_path2)

        return jsonify({'message': f'Usuario {username} eliminado correctamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getDatasetByName/<string:dataset_name>', methods=['GET'])
def getDatasetByName(dataset_name):
    try:
        dataset = Dataset.query.filter_by(nombre=dataset_name).first()

        if dataset:
            return jsonify({
                'id': dataset.id,
                'nombre': dataset.nombre,
                'shaft_frequency': dataset.shaft_frequency,
                'sampling_frequency': dataset.sampling_frequency,
                'carga': dataset.carga,
                'bearing_type': dataset.bearing_type,
                'bpfo': dataset.bpfo,
                'bpfi': dataset.bpfi,
                'bsf': dataset.bsf,
                'ftf': dataset.ftf,
                'min_to_check': dataset.min_to_check,
                'max_to_check': dataset.max_to_check,
                'files_added': dataset.files_added
            })
        else:
            return jsonify({'nombre': 'Dataset not found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/createDataset/<string:username>', methods=['POST'])
def insertDataset(username):
    try:
        data = request.json

        new_dataset = Dataset(
            nombre=data['nombre'],
            shaft_frequency=data['shaft_frequency'],
            sampling_frequency=data['sampling_frequency'],
            carga=data['carga'],
            bearing_type=data['bearing_type'],
            bpfo=data['bpfo'],
            bpfi=data['bpfi'],
            bsf=data['bsf'],
            ftf=data['ftf'],
            min_to_check=data['min_to_check'],
            max_to_check=data['max_to_check'],
            files_added=data['files_added']
        )

        db.session.add(new_dataset)
        db.session.commit()

        with open('prog_analizador/saved_models/' + username + '/' + data['nombre'] + '.csv', 'w', newline='') as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            escritor_csv.writerow(
                ['Nombre', 'Shaft Frequency', 'Sampling Frequency', 'Carga', 'Bearing Type', 'BPFO', 'BPFI', 'BSF',
                 'FTF', 'Min to Check', 'Max to Check', 'Files Added'])

        return '0', 201

    except Exception as e:
        print(f"IntegrityError: {str(e)}")
        return '1', 500


@app.route('/updateDataset/<int:dataset_id>/<string:user>', methods=['PUT'])
def updateDataset(dataset_id, user):
    try:
        data = request.json

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset no encontrado'}), 404

        if dataset.nombre != data['nombre']:
            if os.path.exists('prog_analizador/saved_models/'+ user + '/' + dataset.nombre + '.csv'):
                os.rename('prog_analizador/saved_models/'+ user + '/' + dataset.nombre + '.csv', 'prog_analizador/saved_models/'+ user + '/' + data['nombre'] + '.csv')
            if os.path.exists('prog_analizador/saved_models/'+ user + '/' + dataset.nombre + '.h5'):
                os.rename('prog_analizador/saved_models/'+ user + '/' + dataset.nombre + '.h5', 'prog_analizador/saved_models/'+ user + '/' + data['nombre'] + '.h5')

        dataset.nombre = data.get('nombre', dataset.nombre)
        dataset.shaft_frequency = data.get('shaft_frequency', dataset.shaft_frequency)
        dataset.sampling_frequency = data.get('sampling_frequency', dataset.sampling_frequency)
        dataset.carga = data.get('carga', dataset.carga)
        dataset.bearing_type = data.get('bearing_type', dataset.bearing_type)
        dataset.bpfo = data.get('bpfo', dataset.bpfo)
        dataset.bpfi = data.get('bpfi', dataset.bpfi)
        dataset.bsf = data.get('bsf', dataset.bsf)
        dataset.ftf = data.get('ftf', dataset.ftf)

        db.session.commit()

        return jsonify({'message': 'Dataset actualizado correctamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getModelsList', methods=['GET'])
def getModelsList():

    ruta_data = os.path.join(os.path.dirname(__file__), 'prog_analizador/models')

    nombres_elementos = os.listdir(ruta_data)
    nombres_elementos_ordenados = sorted(nombres_elementos)

    return jsonify({'modelsList': nombres_elementos_ordenados})


@app.route('/getSavedModelsList/<string:user>', methods=['GET'])
def getSavedModelsList(user):

    ruta_data = os.path.join(os.path.dirname(__file__), 'prog_analizador/saved_models/' + user)

    if not os.path.exists(ruta_data):
        os.makedirs(ruta_data)

    nombres_elementos = os.listdir(ruta_data)
    nombres_elementos_ordenados = sorted(nombres_elementos)

    return jsonify({'modelsList': nombres_elementos_ordenados})


@app.route('/getAllSavedModelsList', methods=['GET'])
def getAllSavedModelsList():
    archivos = []
    ruta_base = 'prog_analizador/saved_models'

    for carpeta in os.listdir(ruta_base):
        ruta_carpeta = os.path.join(ruta_base, carpeta)
        for archivo in os.listdir(ruta_carpeta):
            ruta_archivo = os.path.join(ruta_carpeta, archivo)
            if os.path.isfile(ruta_archivo):

                nombre_archivo = os.path.splitext(archivo)[0]
                nombre_carpeta = carpeta

                archivos.append(f"{nombre_archivo} ({nombre_carpeta})")

    return jsonify({'modelsList': archivos})


@app.route('/deleteDataset/<string:user>', methods=['POST'])
def deleteDataset(user):
    try:
        folder_path = 'prog_analizador/saved_models/' + user

        filename_with_extension = request.json.get('nombre')

        filename_without_extension, _ = os.path.splitext(filename_with_extension)

        if (user == 'admin'):
            tmp = filename_with_extension.split("(")
            filename_without_extension = tmp[0].strip()
            folder_path = 'prog_analizador/saved_models/' + tmp[1].replace(")", "").strip()
            filename_with_extension = tmp[0].strip() + '.csv'
            if not os.path.exists(os.path.join(folder_path, filename_with_extension)):
                filename_with_extension = tmp[0].strip() + '.h5'

        file_path = os.path.join(folder_path, filename_with_extension)

        if os.path.exists(file_path):
            os.remove(file_path)
            if os.path.exists(os.path.join('prog_analizador/saved_data/' + user, filename_without_extension + '.csv')):
                os.remove(os.path.join('prog_analizador/saved_data/' + user, 'healthy' + filename_without_extension + '.csv'))
                os.remove(os.path.join('prog_analizador/saved_data/' + user, filename_without_extension + '.csv'))

            dataset = Dataset.query.filter_by(nombre=filename_without_extension).first()

            if dataset:
                db.session.delete(dataset)
                db.session.commit()

            return jsonify({'message': f'Archivo {filename_with_extension} eliminado correctamente'}), 200
        else:
            return jsonify({'error': f'Archivo {filename_with_extension} no encontrado'}), 404

    except Exception as e:
        return jsonify({'error': f'Error al eliminar el archivo: {str(e)}'}), 500


@app.route('/deleteSample/<int:dataset_id>/<string:user>', methods=['POST'])
def deleteSample(dataset_id, user):
    folder_path = 'prog_analizador/saved_data/' + user

    data = request.json
    os.remove(os.path.join(folder_path, data.get('healthy')))
    if os.path.exists(os.path.join(folder_path, data.get('regular'))):
        os.remove(os.path.join(folder_path, data.get('regular')))

    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        return jsonify({'error': 'Dataset no encontrado'}), 404

    dataset.files_added = 0
    db.session.commit()
    return 'Archivo guardado con exito', 200


def saveFile(archivo, flag, user):
    carpeta_guardado: str = ''
    try:

        if flag==0:
            carpeta_guardado = 'prog_analizador/saved_models/' + user
        if flag==1:
            carpeta_guardado = 'prog_analizador/saved_data/' + user
        if flag==3:
            carpeta_guardado = 'prog_analizador/tmp/'

        ruta_guardado = os.path.join(os.path.dirname(__file__), carpeta_guardado)

        os.makedirs(ruta_guardado, exist_ok=True)

        if archivo:
            ruta_guardar = os.path.join(ruta_guardado, archivo.filename)

            archivo.save(ruta_guardar)

            return ruta_guardar
        else:
            raise ValueError('No se proporciono ningun archivo en la solicitud')
    except Exception as e:
        raise e


@app.route('/saveData/<int:dataset_id>/<string:user>', methods=['POST'])
def saveData(dataset_id, user):
    try:
        flag = 1
        name = request.form['fileName']
        ogName = request.form['ogName']

        if name.startswith('tmp'):
            saveFile(request.files.get('archivo'), 3, user)
            os.rename('prog_analizador/tmp/' + ogName, 'prog_analizador/tmp/' + name)
            tmp2 = enter_utils.getNMaxTmp(name)
            if tmp2 < 5:
                os.remove('prog_analizador/tmp/' + name)
                return 'El archivo debe tener al menos 30 muestras.', 202
            return 'Archivo guardado con exito', 200

        saveFile(request.files.get('archivo'), flag, user)
        os.rename('prog_analizador/saved_data/' + user + '/' + ogName, 'prog_analizador/saved_data/' + user + '/' + name)

        #Metodo para crear csv healthy con primera fila de csv subido
        primeraFilaCSV('prog_analizador/saved_data/' + user + '/' + name, 'prog_analizador/saved_data/' + user + '/' + 'healthy' + name)

        tmp = enter_utils.getNMax(name, user)
        tmp2 = enter_utils.getNMax('healthy'+name, user)

        if tmp < 30:
            os.remove('prog_analizador/saved_data/' + user + '/' + name)
            os.remove('prog_analizador/saved_data/' + user + '/healthy' + name)
            return 'El archivo "healthy" debe tener al menos 30 muestras.', 202

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset no encontrado'}), 404

        dataset.files_added = 1
        dataset.min_to_check = 0
        dataset.max_to_check = tmp
        db.session.commit()
        return 'Archivo guardado con exito', 200
    except Exception as e:
        return str(e), 500


def primeraFilaCSV(archivo_csv, ruta_destino):
    data = pd.read_csv(archivo_csv, header=None, index_col=False)
    tmp = data.iloc[0]
    pd.DataFrame(tmp).to_csv(ruta_destino, header=None, index=False)

@app.route('/analyzeData/<string:session_id>/<int:flag>', methods=['POST'])
def analyzeData(session_id, flag):
    try:
        warnings.filterwarnings("ignore")

        ruta_carpeta = os.path.join(app.root_path, 'img/' + session_id)

        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)

        for archivo in os.listdir(ruta_carpeta):
            ruta_archivo = os.path.join(ruta_carpeta, archivo)
            try:
                if os.path.isfile(ruta_archivo):
                    os.unlink(ruta_archivo)
                elif os.path.isdir(ruta_archivo):
                    shutil.rmtree(ruta_archivo)
            except Exception as e:
                print(f"No se pudo eliminar {ruta_archivo}. Error: {e}")

        data = request.json
        dataset = data.get('nombre_req')
        sampling_frequency = data.get('sampling_frequency_req')
        BPFO = data.get('bpfo_req')
        BPFI = data.get('bpfi_req')
        BSF = data.get('bsf_req')
        FTF = data.get('ftf_req')
        shaft_frequency = data.get('shaft_frequency_req')

        healthy_number = data.get('healthy_number_req')
        if flag == 0:
            healthy_samples, denoised_healthy = enter_utils.getDataset(dataset, healthy_number, 0)

        if flag == 1 or flag == 3:
            healthy_samples, denoised_healthy = enter_utils.getDatasetNew(dataset, healthy_number, 0, session_id)

        analyzed_number = data.get('analyzed_number_req')
        first_sample = data.get('first_sample_req')
        if flag == 0:
            analyzed_samples = enter_utils.getDataset(dataset, analyzed_number, first_sample)[0]

        if flag == 1:
            analyzed_samples = enter_utils.getDatasetNew(dataset, analyzed_number, first_sample, session_id)[0]

        if flag == 3:
            analyzed_number = enter_utils.getNMaxTmp('tmp'+dataset+'.csv')
            if (analyzed_number < healthy_number):
                result = {
                    'fault_detected': False,
                    'fault_info': 'healthy',
                    'fault_type': [],
                    'fault_details': [],
                    'analysis_result': None
                }
                os.remove('prog_analizador/tmp/tmp' + str(dataset) + '.csv')
                return jsonify(result), 200
            first_sample = 0
            analyzed_samples = enter_utils.getDatasetTmp(dataset, analyzed_number, first_sample, session_id)[0]

        model_name = str(dataset) + '.h5'

        if flag == 0:
            if os.path.isfile('prog_analizador/models/' + model_name):
                custom_objects = {'MonotonicityLayer2': enter_utils.MonotonicityLayer2,
                                  'SmoothingLayer': enter_utils.SmoothingLayer,
                                  'from_config': enter_utils.from_config}
                ms2ae_model = keras.models.load_model('prog_analizador/models/' + str(model_name), custom_objects=custom_objects,
                                                      compile=False)
            else:
                input_data = healthy_samples[0].reshape(-1, 1)
                ms2ae_model = enter_utils.createModel('prog_analizador/models/' + str(model_name), input_data)
                epochs = 5
                batch_size = 64
                ms2ae_model.fit(healthy_samples, healthy_samples, epochs=epochs, batch_size=batch_size, verbose=0)

        if flag == 1 or flag == 3:
            if os.path.isfile('prog_analizador/saved_models/' + session_id + '/' + model_name):
                custom_objects = {'MonotonicityLayer2': enter_utils.MonotonicityLayer2,
                                  'SmoothingLayer': enter_utils.SmoothingLayer,
                                  'from_config': enter_utils.from_config}
                ms2ae_model = keras.models.load_model('prog_analizador/saved_models/' + session_id + '/' + str(model_name), custom_objects=custom_objects,
                                                      compile=False)
            else:
                input_data = healthy_samples[0].reshape(-1, 1)
                ms2ae_model = enter_utils.createModel('prog_analizador/saved_models/' + session_id + '/' + str(model_name), input_data)
                epochs = 5
                batch_size = 64
                ms2ae_model.fit(healthy_samples, healthy_samples, epochs=epochs, batch_size=batch_size, verbose=0)
                os.remove('prog_analizador/saved_models/' + session_id + '/' + str(dataset) + '.csv')

        HI_healthy_samples = ms2ae_model.predict(healthy_samples, verbose=0)
        HI_analyzed_samples = ms2ae_model.predict(analyzed_samples, verbose=0)
        threshold = enter_utils.getThreshold(HI_healthy_samples)

        isFaulty, faultySample = enter_utils.checkStage(HI_analyzed_samples, threshold)

        if not isFaulty:
            if flag == 3:
                os.remove('prog_analizador/tmp/tmp' + str(dataset) + '.csv')
            return jsonify({'fault_detected': False}), 200

        diff_harmonics = enter_utils.differenceSignals(denoised_healthy.flatten(), analyzed_samples[faultySample])
        kurtogram = enter_utils.computeKurtogram(diff_harmonics, float(sampling_frequency), 3.0)
        fstart, fend = enter_utils.getFilterBands(kurtogram, float(sampling_frequency), 3)
        freq_interest = [float(BPFO), float(BPFI), float(BSF), float(FTF)]
        result = enter_utils.determineFailure(ruta_carpeta, diff_harmonics, HI_healthy_samples, HI_analyzed_samples[faultySample], float(sampling_frequency), fstart, fend, freq_interest, 5)

        if isFaulty:
            if flag == 1:
                tmp_samples = enter_utils.getDatasetNew(dataset, first_sample + analyzed_number, 0, session_id)[0]
            if flag == 0:
                tmp_samples = enter_utils.getDataset(dataset, first_sample + analyzed_number, 0)[0]
            if flag == 3:
                tmp_samples = enter_utils.getDatasetTmp(dataset, first_sample + analyzed_number, 0, session_id)[0]
            enter_utils.matriz_full(tmp_samples, ms2ae_model.predict(tmp_samples, verbose=0), ruta_carpeta, 5, int(sampling_frequency), int(shaft_frequency), int(BPFO), int(BPFI), int(BSF), int(FTF))
            enter_utils.matriz_full2(tmp_samples, ms2ae_model.predict(tmp_samples, verbose=0), ruta_carpeta, 6)
            resultTimeReport = enter_utils.matriz_simple(tmp_samples, ms2ae_model.predict(tmp_samples, verbose=0), ruta_carpeta, 7)
            resultFreqReport = enter_utils.matriz_simple2(tmp_samples, ms2ae_model.predict(tmp_samples, verbose=0), ruta_carpeta, 8, int(sampling_frequency), int(shaft_frequency), int(BPFO), int(BPFI), int(BSF), int(FTF))
            result['resultTimeReport'] = resultTimeReport
            result['resultFreqReport'] = resultFreqReport

        if flag == 3:
            os.remove('prog_analizador/tmp/tmp' + str(dataset) + '.csv')

        return jsonify(result), 200

    except Exception as e:
        os.remove('prog_analizador/tmp/tmp' + str(dataset) + '.csv')
        return jsonify({'error': str(e)}), 500


@app.route('/getImage/<string:session_id>/<int:flag>', methods=['GET'])
def getImage(session_id, flag):
    try:
        image_path = os.path.join('img/' + session_id, f'plot{flag}.png')

        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return 'Image not found', 200

    except Exception as e:
        return f'Error: {str(e)}', 500


if __name__ == '__main__':
    app.run()
