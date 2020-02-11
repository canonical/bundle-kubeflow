"""Trains a Convolutional Neural Network on the MNIST dataset."""

from functools import partial

from kfp import components, dsl
from kfp.components import InputBinaryFile, OutputBinaryFile, OutputTextFile

from .common import attach_output_volume

func_to_container_op = partial(
    components.func_to_container_op,
    base_image='rocks.canonical.com:5000/kubeflow/examples/mnist-test:latest',
)


@func_to_container_op
def load_task(
    train_images: str,
    train_labels: str,
    test_images: str,
    test_labels: str,
    traintest_output: OutputBinaryFile(str),
    validation_output: OutputBinaryFile(str),
):
    """Transforms MNIST data from upstream format into numpy array."""

    from gzip import GzipFile
    from pathlib import Path
    from tensorflow.python.keras.utils import get_file
    import numpy as np
    import struct
    from tensorflow.python.keras.utils import to_categorical

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

        data = np.frombuffer(b[16:], dtype=np.uint8)
        return data.reshape((count, rows, cols)).astype('float32') / 255

    train_x = parse_images(load(train_images))
    train_y = to_categorical(parse_labels(load(train_labels)))
    test_x = parse_images(load(test_images))
    test_y = to_categorical(parse_labels(load(test_labels)))

    # For example purposes, we don't need the entire training set, just enough
    # to get reasonable accuracy
    train_x = train_x[:1000, :, :]
    train_y = train_y[:1000]

    np.savez_compressed(
        traintest_output,
        **{
            'train_x': train_x,
            'train_y': train_y,
            'test_x': test_x[100:, :, :],
            'test_y': test_y[100:],
        },
    )

    np.savez_compressed(
        validation_output,
        **{'val_x': test_x[:100, :, :].reshape(100, 28, 28, 1), 'val_y': test_y[:100]},
    )


@func_to_container_op
def train_task(
    data: InputBinaryFile(str), epochs: int, batch_size: int, model_path: OutputBinaryFile(str)
):
    """Train CNN model on MNIST dataset."""

    from tensorflow.python import keras
    from tensorflow.python.keras import Sequential, backend as K
    from tensorflow.python.keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense
    import numpy as np

    mnistdata = np.load(data)

    train_x = mnistdata['train_x']
    train_y = mnistdata['train_y']
    test_x = mnistdata['test_x']
    test_y = mnistdata['test_y']

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
    print('Test loss & accuracy: %s' % (score,))

    model.save(model_path)




def serve_sidecar():
    """Serves tensorflow model as sidecar to testing container."""

    return dsl.Sidecar(
        name='tensorflow-serve',
        image='tensorflow/serving:1.14.0',
        command='/usr/bin/tensorflow_model_server',
        args=[
            '--model_name=mnist',
            '--model_base_path=/output/mnist',
            '--port=9000',
            '--rest_api_port=9001',
        ],
        mirror_volume_mounts=True,
    )


@func_to_container_op
def test_task(
    model_file: InputBinaryFile(str),
    examples_file: InputBinaryFile(str),
    confusion_matrix: OutputTextFile(str),
    results: OutputTextFile(str),
):
    """Connects to served model and tests example MNIST images."""

    import time
    import json

    import numpy as np
    import requests
    from tensorflow.python.keras.backend import get_session
    from tensorflow.python.keras.saving import load_model
    from tensorflow.python.saved_model.simple_save import simple_save

    with get_session() as sess:
        model = load_model(model_file)
        simple_save(
            sess,
            '/output/mnist/1/',
            inputs={'input_image': model.input},
            outputs={t.name: t for t in model.outputs},
        )

    model_url = 'http://localhost:9001/v1/models/mnist'

    for _ in range(60):
        try:
            requests.get(f'{model_url}/versions/1').raise_for_status()
            break
        except requests.RequestException:
            time.sleep(5)
    else:
        raise Exception("Waited too long for sidecar to come up!")

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

    examples = np.load(examples_file)
    assert examples['val_x'].shape == (100, 28, 28, 1)
    assert examples['val_y'].shape == (100, 10)

    response = requests.post(f'{model_url}:predict', json={'instances': examples['val_x'].tolist()})
    response.raise_for_status()

    predicted = np.argmax(response.json()['predictions'], axis=1).tolist()
    actual = np.argmax(examples['val_y'], axis=1).tolist()
    zipped = list(zip(predicted, actual))
    accuracy = sum(1 for (p, a) in zipped if p == a) / len(predicted)

    print(f"Accuracy: {accuracy:0.2f}")
    # TODO: Figure out how to access artifacts via pipelines UI
    #  print("Generating confusion matrix")
    #  labels = list(range(10))
    #  cm = [[0] * 10 for _ in range(10)]
    #  for pred, target in zipped:
    #      cm[target][pred] += 1
    #  for target in range(10):
    #      for predicted in range(10):
    #          count = cm[target][predicted]
    #          confusion_matrix.write(f'{target},{predicted},{count}\n')
    #
    #  with open('/output/mlpipeline-ui-metadata.json', 'w') as f:
    #      json.dump(
    #          {
    #              "version": 1,
    #              "outputs": [
    #                  {
    #                      "type": "confusion_matrix",
    #                      "format": "csv",
    #                      "source": "minio://mlpipeline/cm.tgz",
    #                      "schema": [
    #                          {"name": "target", "type": "CATEGORY"},
    #                          {"name": "predicted", "type": "CATEGORY"},
    #                          {"name": "count", "type": "NUMBER"},
    #                      ],
    #                      "labels": list(map(str, labels)),
    #                  }
    #              ],
    #          },
    #          f,
    #      )

@dsl.pipeline(
    name='MNIST CNN Example',
    description='Trains an example Convolutional Neural Network on MNIST dataset.',
)
def mnist_pipeline(
    train_images='https://people.canonical.com/~knkski/train-images-idx3-ubyte.gz',
    train_labels='https://people.canonical.com/~knkski/train-labels-idx1-ubyte.gz',
    test_images='https://people.canonical.com/~knkski/t10k-images-idx3-ubyte.gz',
    test_labels='https://people.canonical.com/~knkski/t10k-labels-idx1-ubyte.gz',
    train_epochs: int = 2,
    train_batch_size: int = 128,
):
    # Load mnist data and transform it into numpy array
    load = load_task(train_images, train_labels, test_images, test_labels)

    # Train model on transformed mnist dataset
    train = train_task(load.outputs['traintest_output'], train_epochs, train_batch_size)

    serve = serve_sidecar()
    test_task(train.outputs['model_path'], load.outputs['validation_output']).add_sidecar(serve)

    # Ensure that each step has volumes attached to where ever data gets written to
    dsl.get_pipeline_conf().add_op_transformer(attach_output_volume)
