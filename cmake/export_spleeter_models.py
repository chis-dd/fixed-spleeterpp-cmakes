import os
import json
import argparse
import tempfile
import shutil

import tensorflow as tf

import spleeter
from spleeter.model import model_fn


SPLEETER_ROOT = os.path.dirname(spleeter.__file__)


def export_model(pretrained_path: str, frequency_bin_count: int, model_name: str, export_directory: str):
    # read the json parameters
    param_path = os.path.join(SPLEETER_ROOT, "resources", model_name + ".json")
    with open(param_path) as parameter_file:
        parameters = json.load(parameter_file)
    parameters['F'] = frequency_bin_count
    parameters['MWF'] = False  # default parameter

    # create the estimator
    configuration = tf.estimator.RunConfig(session_config=tf.compat.v1.ConfigProto())
    estimator = tf.estimator.Estimator(
        model_fn=model_fn,
        model_dir=os.path.join(pretrained_path, model_name),
        params=parameters,
        config=configuration
    )

    # convert it to predictor
    def receiver():
        shape = (None, parameters['n_channels'])
        features = {
            'waveform': tf.compat.v1.placeholder(tf.float32, shape=shape),
            'audio_id': tf.compat.v1.placeholder(tf.string)
        }
        return tf.estimator.export.ServingInputReceiver(features, features)
    # export the estimator into a temp directory
    estimator.export_saved_model(export_directory, receiver)


def main():
    parser = argparse.ArgumentParser(description='Export spleeter models')
    parser.add_argument("pretrained_path")
    parser.add_argument("export_path")
    parser.add_argument("frequency_bin_count")
    args = parser.parse_args()

    os.makedirs(args.export_path, exist_ok=True)

    for model in os.listdir(args.pretrained_path):
        # the model is exported under a timestamp. We export in a temp dir,
        # then we move the created folder to the right export path
        destination = os.path.join(args.export_path, model)
        temp_dir = tempfile.mkdtemp()
        export_model(args.pretrained_path, int(args.frequency_bin_count), model, temp_dir)
        created_dir = os.path.join(temp_dir, os.listdir(temp_dir)[0])
        shutil.move(created_dir, destination)
        shutil.rmtree(temp_dir)  # cleanup


if __name__ == '__main__':
    main()
