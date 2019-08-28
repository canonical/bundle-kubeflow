"""Trains a CNN on the MNIST dataset

See https://github.com/kubeflow/pipelines/issues/1907 for the why of the `-> str` annotations
"""

from functools import partial
from typing import NamedTuple

from kfp import dsl, components

from .common import attach_output_volume


func_to_container_op = partial(
    components.func_to_container_op,
    base_image='rocks.canonical.com:5000/kubeflow/examples/mnist-test:latest',
)


@func_to_container_op
def ensure_bucket_task(endpoint: str, bucket: str) -> str:
    """Ensures that the data bucket has been created."""

    from pathlib import Path
    from minio import Minio
    from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists

    mclient = Minio(
        endpoint,
        access_key=Path('/secrets/accesskey').read_text(),
        secret_key=Path('/secrets/secretkey').read_text(),
        secure=False,
    )

    try:
        mclient.make_bucket(bucket)
    except (BucketAlreadyExists, BucketAlreadyOwnedByYou):
        pass


@func_to_container_op
def load_task(
    endpoint: str,
    bucket: str,
    train_images: str,
    train_labels: str,
    test_images: str,
    test_labels: str,
) -> NamedTuple('Data', [('filename', str)]):
    """Transforms MNIST data from upstream format into numpy array."""

    from gzip import GzipFile
    from pathlib import Path
    from tensorflow.python.keras.utils import get_file
    import numpy as np
    import struct
    from minio import Minio

    mclient = Minio(
        endpoint,
        access_key=Path('/secrets/accesskey').read_text(),
        secret_key=Path('/secrets/secretkey').read_text(),
        secure=False,
    )

    filename = 'mnist.npz'

    def load(path):
        """Ensures that a file is downloaded locally, then unzips and reads it."""
        return GzipFile(get_file(Path(path).name, path)).read()

    def parse_labels(b: bytes) -> np.array:
        """Parses numeric labels from input data."""
        assert struct.unpack('>i', b[:4])[0] == 0x801
        return np.frombuffer(b[8:], dtype=np.uint8)

    def parse_images(b: bytes) -> np.array:
        """Parses images from input data."""
        assert struct.unpack('>i', b[:4])[0] == 0x803
        count = struct.unpack('>i', b[4:8])[0]
        rows = struct.unpack('>i', b[8:12])[0]
        cols = struct.unpack('>i', b[12:16])[0]

        return np.frombuffer(b[16:], dtype=np.uint8).reshape((count, rows, cols))

    np.savez_compressed(
        f'/output/{filename}',
        **{
            'train_x': parse_images(load(train_images)),
            'train_y': parse_labels(load(train_labels)),
            'test_x': parse_images(load(test_images)),
            'test_y': parse_labels(load(test_labels)),
        },
    )

    mclient.fput_object(bucket, filename, f'/output/{filename}')

    return filename,


@func_to_container_op
def train_task(
    endpoint: str, bucket: str, data: str, epochs: int, batch_size: int
) -> NamedTuple('Model', [('filename', str), ('examples', str)]):
    """Train CNN model on MNIST dataset."""

    from pathlib import Path
    from tempfile import TemporaryFile
    from tensorflow.python import keras
    from tensorflow.python.keras import backend as K
    from tensorflow.python.keras import Sequential
    from tensorflow.python.keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense
    from tensorflow.python.keras.utils import to_categorical
    import numpy as np
    from minio import Minio

    mclient = Minio(
        endpoint,
        access_key=Path('/secrets/accesskey').read_text(),
        secret_key=Path('/secrets/secretkey').read_text(),
        secure=False,
    )

    with TemporaryFile('w+b') as outp:
        with mclient.get_object(bucket, data) as inp:
            outp.write(inp.read())
        outp.seek(0)
        mnistdata = np.load(outp)

        train_x = mnistdata['train_x']
        train_y = to_categorical(mnistdata['train_y'])
        test_x = mnistdata['test_x']
        test_y = to_categorical(mnistdata['test_y'])

    # For example purposes, we don't need the entire training set, just enough
    # to get reasonable accuracy
    train_x = train_x[:10000, :, :]
    train_y = train_y[:10000]

    num_classes = 10
    img_w = 28
    img_h = 28

    if K.image_data_format() == 'channels_first':
        train_x.shape = (-1, 1, img_h, img_w)
        test_x.shape = (-1, 1, img_h, img_w)
        input_shape = (1, img_h, img_w)
    else:
        train_x.shape = (-1, img_h, img_w, 1)
        test_x.shape = (-1, img_h, img_w, 1)
        input_shape = (img_h, img_w, 1)

    train_x = train_x.astype('float32')
    test_x = test_x.astype('float32')
    train_x /= 255
    test_x /= 255

    model = Sequential(
        [
            Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=input_shape),
            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D(pool_size=(2, 2)),
            Dropout(0.25),
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(num_classes, activation='softmax'),
        ]
    )

    model.compile(
        loss=keras.losses.categorical_crossentropy,
        optimizer=keras.optimizers.Adadelta(),
        metrics=['accuracy'],
    )

    model.fit(
        train_x,
        train_y,
        batch_size=batch_size,
        epochs=epochs,
        verbose=1,
        validation_data=(test_x, test_y),
    )

    score = model.evaluate(test_x, test_y)
    print('Test loss & accuracy: %s, %s' % score)

    model_name = 'model.h5'

    model.save(f'/output/{model_name}')

    mclient.fput_object(bucket, model_name, f'/output/{model_name}')

    examples = 'examples.npz'

    np.savez_compressed(
        f'/output/{examples}',
        **{
            'X': test_x[:10, :, :, :],
            'y': test_y[:10],
        },
    )

    mclient.fput_object(bucket, examples, f'/output/{examples}')

    return model_name, examples


def serve_sidecar():
    """Serves tensorflow model as sidecar to testing container."""

    # See https://github.com/argoproj/argo/issues/1570 for why we
    # need the wrapper script
    code = """\
import os
import signal
import subprocess
import time

p = subprocess.Popen([
    '/usr/bin/tensorflow_model_server',
    '--model_name=mnist',
    '--model_base_path=/output/mnist',
    '--port=9000',
    '--rest_api_port=9001',
])

start = time.time()

while p.poll() is None:
    # Kill process after 30 seconds due to https://github.com/argoproj/argo/issues/1570
    if time.time() - start >= 30:
        print('Waited long enough for tests to complete.')
        os.kill(p.pid, signal.SIGKILL)
        break
    time.sleep(0.1)
    """

    return dsl.Sidecar(
        name='tensorflow-serve',
        image='tensorflow/serving:1.14.0',
        command='sh',
        args=['-c', f'apt update && apt install -y python3 && python3 -c "{code}"'],
        mirror_volume_mounts=True,
    )


@func_to_container_op
def test_task(endpoint: str, bucket: str, model_file: str, examples_file: str) -> str:
    """Connects to served model and tests example MNIST images."""

    from minio import Minio
    from pathlib import Path
    from retrying import retry
    from tensorflow.python.keras.backend import get_session
    from tensorflow.python.keras.saving import load_model
    from tensorflow.python.saved_model.simple_save import simple_save
    import numpy as np
    import requests

    mclient = Minio(
        endpoint,
        access_key=Path('/secrets/accesskey').read_text(),
        secret_key=Path('/secrets/secretkey').read_text(),
        secure=False,
    )

    print('Downloading model')

    mclient.fget_object(bucket, model_file, '/models/model.h5')
    mclient.fget_object(bucket, examples_file, '/models/examples.npz')

    print('Downloaded model, converting it to serving format')

    with get_session() as sess:
        model = load_model('/models/model.h5')
        simple_save(
            sess,
            '/output/mnist/1/',
            inputs={'input_image': model.input},
            outputs={t.name: t for t in model.outputs},
        )

    model_url = 'http://localhost:9001/v1/models/mnist'

    @retry(stop_max_delay=30 * 1000)
    def wait_for_model():
        requests.get(f'{model_url}/versions/1').raise_for_status()

    wait_for_model()

    response = requests.get(f'{model_url}/metadata')
    response.raise_for_status()
    assert response.json() == {
        'model_spec': {'name': 'mnist', 'signature_name': '', 'version': '1'},
        'metadata': {
            'signature_def': {
                'signature_def': {
                    'serving_default': {
                        'inputs': {
                            'input_image': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [
                                        {'size': '-1', 'name': ''},
                                        {'size': '28', 'name': ''},
                                        {'size': '28', 'name': ''},
                                        {'size': '1', 'name': ''},
                                    ],
                                    'unknown_rank': False,
                                },
                                'name': 'conv2d_input:0',
                            }
                        },
                        'outputs': {
                            'dense_1/Softmax:0': {
                                'dtype': 'DT_FLOAT',
                                'tensor_shape': {
                                    'dim': [{'size': '-1', 'name': ''}, {'size': '10', 'name': ''}],
                                    'unknown_rank': False,
                                },
                                'name': 'dense_1/Softmax:0',
                            }
                        },
                        'method_name': 'tensorflow/serving/predict',
                    }
                }
            }
        },
    }

    examples = np.load('/models/examples.npz')
    assert examples['X'].shape == (10, 28, 28, 1)
    assert examples['y'].shape == (10, 10)

    response = requests.post(
        f'{model_url}:predict', json={'instances': examples['X'].tolist()}
    )
    response.raise_for_status()

    predicted = np.argmax(response.json()['predictions'], axis=1).tolist()
    actual = np.argmax(examples['y'], axis=1).tolist()
    accuracy = sum(1 for (p, a) in zip(predicted, actual) if p == a) / len(predicted)

    if accuracy >= 0.8:
        print(f'Got accuracy of {accuracy:0.2f} in mnist model')
    else:
        raise Exception(f'Low accuracy in mnist model: {accuracy}')


@dsl.pipeline(
    name='MNIST CNN Example',
    description='Trains an example Convolutional Neural Network on MNIST dataset.',
)
def mnist_pipeline(
    train_images='https://people.canonical.com/~knkski/train-images-idx3-ubyte.gz',
    train_labels='https://people.canonical.com/~knkski/train-labels-idx1-ubyte.gz',
    test_images='https://people.canonical.com/~knkski/t10k-images-idx3-ubyte.gz',
    test_labels='https://people.canonical.com/~knkski/t10k-labels-idx1-ubyte.gz',
    storage_endpoint='minio:9000',
    bucket='mnist',
    train_epochs=2,
    train_batch_size=128,
):
    # Ensure minio bucket is created
    ensure_bucket = ensure_bucket_task(storage_endpoint, bucket)

    # Load mnist data and transform it into numpy array
    load = load_task(
        storage_endpoint, bucket, train_images, train_labels, test_images, test_labels
    ).after(ensure_bucket)
    load.output_artifact_paths['mnist.npz'] = '/output/mnist.npz'

    # Train model on transformed mnist dataset
    train = train_task(
        storage_endpoint, bucket, load.outputs['filename'], train_epochs, train_batch_size
    ).after(load)
    train.output_artifact_paths['model'] = '/output/model.hdf5'

    serve = serve_sidecar()
    test = (
        test_task(storage_endpoint, bucket, train.outputs['filename'], train.outputs['examples'])
        .after(train)
        .add_sidecar(serve)
    )

    # Ensure that each step has volumes attached to where ever data gets written to
    dsl.get_pipeline_conf().add_op_transformer(attach_output_volume)
