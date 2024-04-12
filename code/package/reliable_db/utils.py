"""
Utility functions for the reliable news database are saved here.
"""

import inspect
import os
import random
import tiktoken
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


def collect_last_x_files(path, num_paths=None, all=None):
    """
    Collect the full paths to the most recent `num_paths` files in `path`.
    Files in `path` are assumed to be prefixed with a date in the format YYYY_MM_DD.

    Parameters
    ----------
    - path (str): the path to the directory containing the files.
    - all (bool): if True, collect all files in `path`. If False, rely on `num_paths`.
        Default = True.
    - num_paths (int): return *up to* this many paths. Must be > 0. If the number
        of files in `path` < `num_paths` all paths are returned. Cannot be utilized
        when `all == True`. Default = None.

    Returns
    -------
    list: a sorted list of full paths to the most recent `num_paths` files in `path`
    """
    if not isinstance(path, str):
        raise TypeError("`path` must be string.")
    if not isinstance(all, bool):
        raise TypeError("`all` must be boolean.")
    if all and num_paths is not None:
        raise TypeError("`num_paths` cannot be passed when `all == True`")
    if not all and not isinstance(num_paths, int):
        raise TypeError("`num_paths` must be an integer")
    if num_paths is not None and num_paths <= 0:
        raise ValueError("`num_paths` must be > 0")

    # Sorted in ascending order, meaning recent dates are last
    files = sorted(os.listdir(path), reverse=True)
    if all or num_paths > len(files):
        return [os.path.join(path, file) for file in files]
    return [os.path.join(path, file) for file in files[:num_paths]]


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


def get_nested_attr(obj, attr_path, default=None):
    """
    Retrieve a nested attribute from an object. Works like get_dict_val but for
    classes with nested attributes.

    Parameters:
    ------------
    - obj: The object from which to get the nested attribute.
    - attr_path (list): The nested attribute path, as a list e.g., ["attr1", "attr2"].
    - default: The default value to return if any attribute in the path doesn't exist.

    Returns:
    -----------
    - The value of the nested attribute if it exists, otherwise 'default'.
    """
    current = obj
    for attr in attr_path:
        if hasattr(current, attr):
            current = getattr(current, attr)
        else:
            return default
    return current


def num_tokens_from_string(string, encoding_name="gpt-3.5-turbo"):
    """
    Return the number of tokens in a text string.

    Parameters:
    ------------
    - string (str): text for which we count tokens.
    - encoding_name (str): An OpenAI chat completions model (default = gpt-3.5-turbo)

    Returns
    ------------
    - num_tokens (int): the number of tokens in `string` based on `model`
    """
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def trim_text_to_token_limit(text, encoding_name="gpt-3.5-turbo", max_tokens=3500):
    """
    Trim the input text to ensure it does not exceed a specified token limit based on the model's encoding.

    Parameters:
    ------------
    - text (str): The input text to trim.
    - encoding_name (str): The encoding model name, default is "gpt-3.5-turbo".
    - max_tokens (int): the maximum tokens to allow for for a provided string.
        - Note: The maximum tokens for gpt-3.5 is 4097, however, chat completions insert additional tokens
            which drives the functional limit down. For simplicity, we use 3500
        - Ref: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken#6-counting-tokens-for-chat-completions-api-calls

    Returns:
    ------------
    - trimmed_text (str): Trimmed text that meets the token limit.
    """

    # Calculate the number of tokens in the input text
    encoding = tiktoken.encoding_for_model(encoding_name)
    tokens = encoding.encode(text)

    # If the number of tokens exceeds the limit return the truncated text
    if len(tokens) > max_tokens:
        return encoding.decode(tokens[:max_tokens])
    return text
