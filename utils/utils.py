import math
import os


def get_testing_file_paths():
    project_root = os.path.dirname(os.path.dirname(__file__))
    testing_folder = os.path.join(project_root, "fixtures", "for_testing")
    if not os.path.exists(testing_folder):
        raise FileNotFoundError(f"The folder {testing_folder} doesn't exist!")

    files = [os.path.join(testing_folder, f) for f in os.listdir(testing_folder) if
             os.path.isfile(os.path.join(testing_folder, f))]
    return files


def center(bbox):
    x0, y0, x1, y1 = bbox
    return (x0 + x1) / 2, y0  # top center
    # return ((x0 + x1) / 2, (y0 + y1) / 2) # center


def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
