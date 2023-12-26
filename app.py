#!/usr/bin/env python
# encoding: utf-8
import os
import warnings
import keras
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy

import enter_utils

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:12345678@localhost:3306/PreLoadedDatasets'
db = SQLAlchemy(app)
UPLOAD_FOLDER = 'prog_analizador/saved'
ALLOWED_EXTENSIONS = {'csv', 'h5'}


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


@app.route('/getDatasetByName/<string:dataset_name>', methods=['GET'])
def get_dataset_by_name(dataset_name):
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
                'max_to_check': dataset.max_to_check
            })
        else:
            return jsonify({'nombre': 'Dataset not found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/createDataset', methods=['POST'])
def insert_dataset():
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
            max_to_check=data['max_to_check']
        )

        db.session.add(new_dataset)
        db.session.commit()

        return '0', 201

    except Exception as e:
        print(f"IntegrityError: {str(e)}")
        return '1', 500


@app.route('/updateDataset/<int:dataset_id>', methods=['PUT'])
def update_dataset(dataset_id):
    try:
        data = request.json

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset no encontrado'}), 404

        os.rename('prog_analizador/saved/' + dataset.nombre + '.csv', 'prog_analizador/saved/' + data['nombre'] + '.csv')

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
        return jsonify({'error': 'Error interno del servidor'}), 500


@app.route('/getModelsList', methods=['GET'])
def obtener_nombres_elementos_route():
    carpeta_data = 'prog_analizador/models'

    ruta_data = os.path.join(os.path.dirname(__file__), carpeta_data)

    nombres_elementos = os.listdir(ruta_data)

    return jsonify({'modelsList': nombres_elementos})


@app.route('/getSavedModelsList', methods=['GET'])
def obtener_nombres_saved_route():
    carpeta_data = 'prog_analizador/saved'

    ruta_data = os.path.join(os.path.dirname(__file__), carpeta_data)

    nombres_elementos = os.listdir(ruta_data)

    return jsonify({'modelsList': nombres_elementos})


@app.route('/deleteDataset', methods=['POST'])
def delete_dataset():
    try:
        folder_path = 'prog_analizador/saved'

        filename_with_extension = request.json.get('nombre')

        filename_without_extension, _ = os.path.splitext(filename_with_extension)

        file_path = os.path.join(folder_path, filename_with_extension)

        if os.path.exists(file_path):
            os.remove(file_path)

            dataset = Dataset.query.filter_by(nombre=filename_without_extension).first()

            if dataset:
                db.session.delete(dataset)
                db.session.commit()

            return jsonify({'message': f'Archivo {filename_with_extension} eliminado correctamente'}), 200
        else:
            return jsonify({'error': f'Archivo {filename_with_extension} no encontrado'}), 404

    except Exception as e:
        return jsonify({'error': f'Error al eliminar el archivo: {str(e)}'}), 500


@app.route('/getData', methods=['GET'])
def obtener_data_route():
    carpeta_data = 'prog_analizador/data'

    ruta_data = os.path.join(os.path.dirname(__file__), carpeta_data)

    nombres_elementos = os.listdir(ruta_data)

    return jsonify({'modelsList': nombres_elementos})


def guardar_archivo(archivo):
    try:
        carpeta_guardado = 'prog_analizador/saved'
        ruta_guardado = os.path.join(os.path.dirname(__file__), carpeta_guardado)

        os.makedirs(ruta_guardado, exist_ok=True)

        archivo = request.files.get('archivo')

        if archivo:
            ruta_guardar = os.path.join(ruta_guardado, archivo.filename)

            archivo.save(ruta_guardar)

            return ruta_guardar
        else:
            raise ValueError('No se proporcionó ningún archivo en la solicitud')
    except Exception as e:
        raise e


@app.route('/guardar_archivo', methods=['POST'])
def guardar_archivo_route():
    try:
        guardar_archivo(request.files.get('archivo'))

        return 'Archivo guardado con éxito', 200
    except Exception as e:
        return str(e), 500


@app.route('/analyze_data/<string:session_id>', methods=['POST'])
def analyze_data(session_id):
    try:
        warnings.filterwarnings("ignore")

        ruta_carpeta = os.path.join(app.root_path, 'img/' + session_id)

        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)

        data = request.json
        dataset = data.get('nombre_req')
        sampling_frequency = data.get('sampling_frequency_req')
        BPFO = data.get('bpfo_req')
        BPFI = data.get('bpfi_req')
        BSF = data.get('bsf_req')
        FTF = data.get('ftf_req')

        healthy_number = data.get('healthy_number_req')
        healthy_samples, denoised_healthy = enter_utils.getDataset(dataset, healthy_number, 0)

        analyzed_number = data.get('analyzed_number_req')
        first_sample = data.get('first_sample_req')
        analyzed_samples = enter_utils.getDataset(dataset, analyzed_number, first_sample)[0]

        model_name = str(dataset) + '.h5'

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

        HI_healthy_samples = ms2ae_model.predict(healthy_samples, verbose=0)
        HI_analyzed_samples = ms2ae_model.predict(analyzed_samples, verbose=0)
        threshold = enter_utils.getThreshold(HI_healthy_samples)

        isFaulty, faultySample = enter_utils.checkStage(HI_analyzed_samples, threshold)

        if not isFaulty:
            return jsonify({'fault_detected': False}), 200

        diff_harmonics = enter_utils.differenceSignals(denoised_healthy.flatten(), analyzed_samples[faultySample])
        kurtogram = enter_utils.computeKurtogram(diff_harmonics, float(sampling_frequency), 3.0)
        fstart, fend = enter_utils.getFilterBands(kurtogram, float(sampling_frequency), 3)
        freq_interest = [float(BPFO), float(BPFI), float(BSF), float(FTF)]
        result = enter_utils.determineFailure(ruta_carpeta, diff_harmonics, HI_healthy_samples, HI_analyzed_samples[faultySample], float(sampling_frequency), fstart, fend, freq_interest, 5)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_image1/<string:session_id>', methods=['GET'])
def get_image1(session_id):
    try:
        image_directory = 'img/' + session_id
        image_name = 'ploot1.png'
        image_path = os.path.join(image_directory, image_name)

        return send_file(image_path, mimetype='image/png')

    except Exception as e:
        return f'Error: {str(e)}', 500


@app.route('/get_image2/<string:session_id>', methods=['GET'])
def get_image2(session_id):
    try:
        image_directory = 'img/' + session_id
        image_name = 'ploot2.png'
        image_path = os.path.join(image_directory, image_name)

        return send_file(image_path, mimetype='image/png')

    except Exception as e:
        return f'Error: {str(e)}', 500


if __name__ == '__main__':
    app.run()
