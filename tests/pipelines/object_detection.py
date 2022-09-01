from functools import partial

from kfp import dsl, components
from kfp.components import InputBinaryFile, OutputBinaryFile

from .common import attach_output_volume

func_to_container_op = partial(
    components.func_to_container_op,
    base_image='rocks.canonical.com:5000/kubeflow/examples/object_detection:latest',
)


@func_to_container_op
def load_task(
    images: str,
    annotations: str,
    records: OutputBinaryFile(str),
    validation_images: OutputBinaryFile(str),
):
    """Transforms pet data from images to TensorFlow records."""

    from glob import glob
    from pathlib import Path
    from tensorflow.python.keras.utils import get_file
    import subprocess
    import tarfile

    def load(path):
        return get_file(Path(path).name, path, extract=True)

    load(images)
    load(annotations)

    with tarfile.open(mode='w:gz', fileobj=validation_images) as tar:
        for image in glob('/root/.keras/datasets/images/*.jpg')[:10]:
            tar.add(image, arcname=Path(image).name)

    subprocess.run(
        [
            'python',
            'object_detection/dataset_tools/create_pet_tf_record.py',
            '--label_map_path=object_detection/data/pet_label_map.pbtxt',
            '--data_dir',
            '/root/.keras/datasets/',
            '--output_dir=/models/research',
        ],
        check=True,
        cwd='/models/research',
    )

    with tarfile.open(mode='w:gz', fileobj=records) as tar:
        for record in glob('/models/research/*.record-*'):
            tar.add(record, arcname=Path(record).name)


@func_to_container_op
def train_task(records: InputBinaryFile(str), pretrained: str, exported: OutputBinaryFile(str)):
    from pathlib import Path
    from tensorflow.python.keras.utils import get_file
    import subprocess
    import shutil
    import re
    import tarfile
    import sys

    def load(path):
        return get_file(Path(path).name, path, extract=True)

    model_path = Path(load(pretrained))
    model_path = str(model_path.with_name(model_path.name.split('.')[0]))
    shutil.move(model_path, '/model')

    with tarfile.open(mode='r:gz', fileobj=records) as tar:
        tar.extractall('/records')

    with open('/pipeline.config', 'w') as f:
        config = Path('samples/configs/faster_rcnn_resnet101_pets.config').read_text()
        config = re.sub(r'PATH_TO_BE_CONFIGURED\/model\.ckpt', '/model/model.ckpt', config)
        config = re.sub('PATH_TO_BE_CONFIGURED', '/records', config)
        f.write(config)

    shutil.copy('data/pet_label_map.pbtxt', '/records/pet_label_map.pbtxt')

    print("Training model")
    subprocess.check_call(
        [
            sys.executable,
            'model_main.py',
            '--model_dir',
            '/model',
            '--num_train_steps',
            '1',
            '--pipeline_config_path',
            '/pipeline.config',
        ],
    )

    subprocess.check_call(
        [
            sys.executable,
            'export_inference_graph.py',
            '--input_type',
            'image_tensor',
            '--pipeline_config_path',
            '/pipeline.config',
            '--trained_checkpoint_prefix',
            '/model/model.ckpt-1',
            '--output_directory',
            '/exported',
        ],
    )

    with tarfile.open(mode='w:gz', fileobj=exported) as tar:
        tar.add('/exported', recursive=True)


def serve_sidecar():
    """Serves tensorflow model as sidecar to testing container."""

    return dsl.Sidecar(
        name='tensorflow-serve',
        image='tensorflow/serving:1.15.0-gpu',
        command='/usr/bin/tensorflow_model_server',
        args=[
            '--model_name=object_detection',
            '--model_base_path=/output/object_detection',
            '--port=9000',
            '--rest_api_port=9001',
        ],
        mirror_volume_mounts=True,
    )


@func_to_container_op
def test_task(model: InputBinaryFile(str), validation_images: InputBinaryFile(str)):
    """Connects to served model and tests example pet images."""

    import numpy as np
    import requests
    import shutil
    import tarfile
    import time
    from matplotlib.pyplot import imread

    with tarfile.open(model.name) as tar:
        tar.extractall(path="/")
    shutil.move('/exported', '/output/object_detection')
    # https://stackoverflow.com/a/45552938
    shutil.copytree('/output/object_detection/saved_model', '/output/object_detection/1')

    with tarfile.open(validation_images.name) as tar:
        tar.extractall(path="/images")

    model_url = 'http://localhost:9001/v1/models/object_detection'
    for _ in range(60):
        try:
            requests.get(f'{model_url}/versions/1').raise_for_status()
            break
        except requests.RequestException as err:
            print(err)
            time.sleep(5)
    else:
        raise Exception("Waited too long for sidecar to come up!")

    response = requests.get(f'{model_url}/metadata')
    response.raise_for_status()
    assert response.json() == {
        'model_spec': {'name': 'object_detection', 'signature_name': '', 'version': '1'},
        'metadata': {
            'signature_def': {
                'signature_def': {
                    'serving_default': {
                        'inputs': {
                            'inputs': {
                                'dtype': 'DT_UINT8',
                                'tensor_shape': {
                                    'dim': [
                                        {'size': '-1', 'name': ''},
                                        {'size': '-1', 'name': ''},
                                        {'size': '-1', 'name': ''},
                                        {'size': '3', 'name': ''},
                                    ],
                                    'unknown_rank': False,
                                },
                                'name': 'image_tensor:0',
                            }
                        },
                        'outputs': {
                            'raw_detection_scores': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [
                                        {'size': '-1', 'name': ''},
                                        {'size': '300', 'name': ''},
                                        {'size': '38', 'name': ''},
                                    ],
                                    'unknown_rank': False,
                                },
                                'name': 'raw_detection_scores:0',
                            },
                            'detection_multiclass_scores': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [
                                        {'size': '-1', 'name': ''},
                                        {'size': '300', 'name': ''},
                                        {'size': '38', 'name': ''},
                                    ],
                                    'unknown_rank': False,
                                },
                                'name': 'detection_multiclass_scores:0',
                            },
                            'detection_classes': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [
                                        {'size': '-1', 'name': ''},
                                        {'size': '300', 'name': ''},
                                    ],
                                    'unknown_rank': False,
                                },
                                'name': 'detection_classes:0',
                            },
                            'num_detections': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [{'size': '-1', 'name': ''}],
                                    'unknown_rank': False,
                                },
                                'name': 'num_detections:0',
                            },
                            'detection_boxes': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [
                                        {'size': '-1', 'name': ''},
                                        {'size': '300', 'name': ''},
                                        {'size': '4', 'name': ''},
                                    ],
                                    'unknown_rank': False,
                                },
                                'name': 'detection_boxes:0',
                            },
                            'raw_detection_boxes': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [
                                        {'size': '-1', 'name': ''},
                                        {'size': '300', 'name': ''},
                                        {'size': '4', 'name': ''},
                                    ],
                                    'unknown_rank': False,
                                },
                                'name': 'raw_detection_boxes:0',
                            },
                            'detection_scores': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [
                                        {'size': '-1', 'name': ''},
                                        {'size': '300', 'name': ''},
                                    ],
                                    'unknown_rank': False,
                                },
                                'name': 'detection_scores:0',
                            },
                        },
                        'method_name': 'tensorflow/serving/predict',
                    }
                }
            }
        },
    }

    test_images = np.zeros((5, 100, 100, 3), dtype=np.uint8).tolist()
    response = requests.post(f'{model_url}:predict', json={'instances': test_images})
    response.raise_for_status()
    shapes = {
        'detection_boxes': (300, 4),
        'raw_detection_boxes': (300, 4),
        'detection_scores': (300,),
        'raw_detection_scores': (300, 38),
        'detection_multiclass_scores': (300, 38),
        'detection_classes': (300,),
    }
    for i, prediction in enumerate(response.json()['predictions']):
        print("Checking prediction #%s" % i)
        for name, shape in shapes.items():
            assert np.array(prediction[name]).shape == shape, name

    with open('pet.jpg', 'wb') as f:
        f.write(
            requests.get(
                'https://github.com/canonical/bundle-kubeflow/raw/main/tests/pipelines/artifacts/pet.jpg'
            ).content
        )
    test_image = imread('pet.jpg').reshape((1, 500, 357, 3)).tolist()
    response = requests.post(f'{model_url}:predict', json={'instances': test_image})
    response.raise_for_status()
    shapes = {
        'detection_boxes': (300, 4),
        'raw_detection_boxes': (300, 4),
        'detection_scores': (300,),
        'raw_detection_scores': (300, 38),
        'detection_multiclass_scores': (300, 38),
        'detection_classes': (300,),
    }
    for i, prediction in enumerate(response.json()['predictions']):
        print("Checking prediction #%s" % i)
        for name, shape in shapes.items():
            assert np.array(prediction[name]).shape == shape, name


@dsl.pipeline(
    name='Object Detection Example',
    description='Continues training a pretrained pet detection model, then tests serving it.',
)
def object_detection_pipeline(
    images='http://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz',
    annotations='http://www.robots.ox.ac.uk/~vgg/data/pets/data/annotations.tar.gz',
    pretrained='http://storage.googleapis.com/download.tensorflow.org/models/object_detection/faster_rcnn_resnet101_coco_11_06_2017.tar.gz',  # noqa
):
    loaded = load_task(images, annotations)
    loaded.container.set_gpu_limit(1)
    train = train_task(loaded.outputs['records'], pretrained)
    train.container.set_gpu_limit(1)

    test = test_task(train.outputs['exported'], loaded.outputs['validation_images'])
    test.add_sidecar(serve_sidecar().set_gpu_limit(1))

    dsl.get_pipeline_conf().add_op_transformer(attach_output_volume)
