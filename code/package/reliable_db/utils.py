"""
Utility functions for the reliable news database are saved here.
"""
import inspect
import os
import random
import time


def random_wait(min=1, max=5):
    """
    Sleeps for a random amount of time between min+1 and max+1 seconds.
    """
    if not all(isinstance(item, int) for item in (min, max)):
        raise ValueError("min and max must be integers.")

    wait_time = 1 + random.uniform(min, max)
    print(f"\t- Sleeping for {wait_time:.2f} seconds.")
    time.sleep(wait_time)


def collect_last_x_files(path, num_files):
    """
    Collect the full paths to the most recent `num_files` files in `path`.
    Files in `path` are assumed to be prefixed with a date in the format YYYY_MM_DD.

    Parameters
    ----------
    - path (str): the path to the directory containing the files
    - num_files (int): the number of files to collect

    Returns
    -------
    list: a list of full paths to the most recent `num_files` files in `path`
    """
    # Sorted in ascending order, meaning recent dates are last
    files = sorted(os.listdir(path))
    if num_files > len(files):
        return [os.path.join(path, file) for file in files]
    return [os.path.join(path, file) for file in files[-num_files:]]


def get_class_property_dict(obj):
    """
    Return a dictionary of a class's @properties.
    """
    properties = {}
    for name, attribute in inspect.getmembers(type(obj)):
        if isinstance(attribute, property):
            properties[name] = getattr(obj, name)
    return properties


def get_dict_val(dictionary: dict, key_list: list = []):
    """
    Return `dictionary` value at the end of the key path provided
    in `key_list`.
    Indicate what value to return based on the key_list provided.
    For example, from left to right, each string in the key_list
    indicates another nested level further down in the dictionary.
    If no value is present, a `None` is returned.
    Parameters:
    ----------
    - dictionary (dict) : the dictionary object to traverse
    - key_list (list) : list of strings indicating what dict_obj
        item to retrieve
    Returns:
    ----------
    - key value (if present) or None (if not present)
    Raises:
    ----------
    - TypeError
    Examples:
    ---------
    # Create dictionary
    dictionary = {
        "a" : 1,
        "b" : {
            "c" : 2,
            "d" : 5
        },
        "e" : {
            "f" : 4,
            "g" : 3
        },
        "h" : 3
    }
    ### 1. Finding an existing value
    # Create key_list
    key_list = ['b', 'c']
    # Execute function
    get_dict_val(dictionary, key_list)
    # Returns
    2
    ~~~
    ### 2. When input key_path doesn't exist
    # Create key_list
    key_list = ['b', 'k']
    # Execute function
    value = get_dict_val(dictionary, key_list)
    # Returns NoneType because the provided path doesn't exist
    type(value)
    NoneType
    """
    if not isinstance(dictionary, dict):
        raise TypeError("`dictionary` must be of type `dict`")

    if not isinstance(key_list, list):
        raise TypeError("`key_list` must be of type `list`")

    retval = dictionary
    for k in key_list:
        # If retval is not a dictionary, we're going too deep
        if not isinstance(retval, dict):
            return None

        if k in retval:
            retval = retval[k]

        else:
            return None
    return retval
