import tensorflow as tf
import yaml
import os
import sys
sys.path.insert(0, '/~/Documents/models/research/object_detection/utils')
from object_detection.utils import dataset_util

flags = tf.app.flags
flags.DEFINE_string('output_path', '', 'Path to output TFRecord')
FLAGS = flags.FLAGS

LABEL_DICT = {
    "Green": 1,
    "Red": 2,
    "GreenLeft": 3,
    "GreenRight": 4,
    "RedLeft": 5,
    "RedRight": 6,
    "Yellow": 7,
    "off": 8,
    "RedStraight": 9,
    "GreenStraight": 10,
    "GreenStraightLeft": 11,
    "GreenStraightRight": 12,
    "RedStraightLeft": 13,
    "RedStraightRight": 14
    }


def create_tf_example(example, example_source):
    MIN_DELTA = 5
    if example_source == "LISA":
        image_height = 960
        image_width = 1280
        image_format = 'jpg'.encode()

    else:
        # Bosch
        image_height = 720
        image_width = 1280
        image_format = 'png'.encode()
    
    filename = example['path']    
    valid_example = False
    xmins = []  # List of normalized left x coordinates in bounding box (1 per box)
    xmaxs = []  # List of normalized right x coordinates in bounding box (1 per box)
    ymins = []  # List of normalized top y coordinates in bounding box (1 per box)
    ymaxs = []  # List of normalized bottom y coordinates in bounding box (1 per box)
    classes_text = []  # List of string class name of bounding box (1 per box)
    classes = []  # List of integer class id of bounding box (1 per box)
    tf_example = []
    
    for box in example['boxes']:
        # Check that the box is within range
        x_max = min(box['x_max'], image_width-1)
        y_max = min(box['y_max'], image_height-1)
        if (x_max - box['x_min']) >= MIN_DELTA and (y_max - box['y_min']) >= MIN_DELTA:
            xmins.append(float(box['x_min'] / image_width))
            xmaxs.append(float(x_max / image_width))
            ymins.append(float(box['y_min'] / image_height))
            ymaxs.append(float(y_max / image_height))
            classes_text.append(box['label'].encode())
            classes.append(int(LABEL_DICT[box['label']]))
            valid_example = True
            
    
    if valid_example:
        with tf.gfile.GFile(filename, 'rb') as fid:
            encoded_image = fid.read()
            
        tf_example = tf.train.Example(features=tf.train.Features(feature={
            'image/height': dataset_util.int64_feature(image_height),
            'image/width': dataset_util.int64_feature(image_width),
            'image/filename': dataset_util.bytes_feature(filename),
            'image/source_id': dataset_util.bytes_feature(filename),
            'image/encoded': dataset_util.bytes_feature(encoded_image),
            'image/format': dataset_util.bytes_feature(image_format),
            'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
            'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
            'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
            'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
            'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
            'image/object/class/label': dataset_util.int64_list_feature(classes),
            }))
        
    return valid_example, tf_example

def write_tf_examples(writer, yaml_file, image_data, example_source):
    
    # Load the YAML
    examples = yaml.load(open(yaml_file, 'rb').read())
    n_examples = len(examples)
    print("Loaded {:d} Examples...".format(len(examples)))
    
    # Set the path
    for i in range(n_examples):
        examples[i]['path'] = os.path.abspath(os.path.join(os.path.dirname(image_data), examples[i]['path']))
    
    # Write the examples
    n_valid = 0
    for counter, example in enumerate(examples):
        valid_example, tf_example = create_tf_example(example, example_source)
        if valid_example:
            writer.write(tf_example.SerializeToString())
            n_valid += 1
        
        if counter % 200 == 0:
            print("Percent Done: {:.2f}%".format((float(counter)/float(n_examples))*100))
    
    return n_valid, writer

def main(_):
    writer = tf.python_io.TFRecordWriter(FLAGS.output_path)

    # BOSCH
    n_bosch = 0
    yaml_file = "BOSCH.yaml"
    image_data = "/media/merberg/Centre/Bosch_Small_traffic_lights_dataset/"
    example_source = "BOSCH"
    n_bosch, writer = write_tf_examples(writer, yaml_file, image_data, example_source)
       
    # LISA
    n_lisa = 0
    yaml_file = "LISA_dayTrain.yaml"
    image_data = "/media/merberg/Centre/LISA_traffic_light_dataset/"
    example_source = "LISA"
    #n_lisa, writer = write_tf_examples(writer, yaml_file, image_data, example_source)
    
    writer.close()
    print("TFRecord created from {:d} examples".format(n_bosch+n_lisa))
    # Now run:  python tf_record.py --output_path ../../ros/src/tl_detector/light_classification/training/data/training.record


if __name__ == '__main__':
  tf.app.run()
