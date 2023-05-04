import os
from itertools import permutations


def path2list(filepath):
    """
    converts a filepath to an ordered list containing the directories and filename of the path [root, :, filename]
    """
    path_list = []
    split = os.path.split(filepath)
    path_list.append(split[1])
    while True:
        split = os.path.split(split[0])
        if split[1] == '':
            break
        path_list.append(split[1])
    path_list.append(split[0])
    path_list.reverse()
    if (len(path_list) > 1) and (path_list[0] == ''):
        return path_list[1:]
    else:
        return path_list


def list2path(filepath_list):
    """
    converts an ordered list containing the directories and filename of the path [root, :, filename] to a filepath
    """
    if len(filepath_list) == 1:
        return os.path.normpath(filepath_list[0])
    else:
        filepath = os.path.join(filepath_list[0], filepath_list[1])
        if len(filepath_list) == 2:
            return filepath
    for i in range(2, len(filepath_list)):
        filepath = os.path.join(filepath, filepath_list[i])
    return filepath


def substitute_path(orig_path, sub_path, filepath):
    """
    Substitutes part of a filepath.

    orig_path: matching criteria for substitution
    sub_path: what to replace orig_path with
    filepath: the filepath to be modified
    """
    orig_list = path2list(orig_path)
    sub_list = path2list(sub_path)
    filepath_list = path2list(filepath)

    for i in range(len(filepath_list)):
        if filepath_list[i] == orig_list[0]:
            j = i + 1
            for k in range(1, len(orig_list)+1):
                if k == len(orig_list):
                    out_path = filepath_list[:i] + sub_list + filepath_list[(i+len(orig_list)):]
                    return list2path(out_path)
                if filepath_list[j] != orig_list[k]:
                    break
                j += 1
    return filepath


def find_path_similarity(filepath1, filepath2):
    """
    This method returns the amount of overlap between filepath1 and the max length of another filepath
    """
    list1 = path2list(filepath1)
    list2 = path2list(filepath2)
    match_count = 0
    if len(list1) < len(list2):
        iter_list = list1
        check_list = list2
    else:
        iter_list = list2
        check_list = list1
    for i in range(len(iter_list)):
        count_candidate = 0
        if iter_list[i] in check_list:
            for j in range(len(iter_list[i:])):
                if len(check_list) < (i+j):
                    break
                elif iter_list[i+j] == check_list[i+j]:
                    count_candidate += 1
            if count_candidate > match_count:
                match_count = count_candidate
        else:
            continue
    return match_count / len(check_list)
    # TODO: add spelling similarity to final addition


def substitute_filename_in_path(orig_filename, sub_filename, filepath, keep_ext=True):
    name = os.path.split(filepath)
    if name[1] != orig_filename:
        return filepath
    else:
        if not keep_ext:
            return os.path.join(name[0], sub_filename)
        else:
            ext = os.path.splitext(name[1])[1]
            name_only = os.path.splitext(sub_filename)[0]
            return os.path.join(name[0], f'{name_only}{ext}')


def abs2local_path_convert(filepath):
    """
    converts a filepath to a local path (removes / at start of path). Allows path to be used in os.path.join statements
    if filepath is not absolute, then filepath is returned unaltered
    """
    if filepath[0] == '\\':
        return filepath[1:]
    elif filepath[0:1] == '\\\\':
        return filepath[2:]
    else:
        return filepath


def join_paths_as_local(**paths):
    """
    takes any number of paths and joins them into a new local path

    unlike os.path.join(), this functions guarantees the joining of paths (treats abspath as local)
    """
    last_filepath = ""
    for filepath in paths:
        last_filepath = os.path.join(abs2local_path_convert(last_filepath), abs2local_path_convert(filepath))
    return abs2local_path_convert(last_filepath)


def generate_permutations(filepath, separator='_', use_drops=False, seg_limit=2, manual_adds=None, manual_removes=None):
    """
    Generates permutations of a filename given a separator. For example: r_g_b.png -> r_b_g.png, g_r_b.png, etc

    use_drops defines if segments of filename can be dropped. For example: r_g_b.png -> r_b.png, g_b.png, etc
    seg_limit defines the minimum number of segments to allow

    manual_adds/removes define a list of segments to be added or removed. If a segment cannot be removed, then
    permutations are not generated. By removing and then adding the same segment, you can only add segments to filenames
    with the removed segment (which was be added back in, so it acts like a filter)
    """
    # Manual adds/removes is a list of segments to be added or removed from the permutations
    def assemble_permutation(str_tuple):
        out_string = ''
        for string in str_tuple:
            out_string += string
            out_string += separator
        return out_string[:-1]

    path_only, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)
    segments = list(name.split(separator))
    if manual_adds:
        for manual_add in manual_adds:
            segments.append(manual_add)
    if manual_removes:
        for manual_remove in manual_removes:
            if manual_remove in segments:
                segments.remove(manual_remove)
            elif manual_remove != '':
                return []
    possible_filenames = list(permutations(segments))
    possible_filepaths = []

    for i in range(len(possible_filenames)):
        possible_filepaths.append(os.path.join(path_only, f'{assemble_permutation(possible_filenames[i])}{ext}'))
        if use_drops:
            j = len(possible_filenames) - 1
            if seg_limit < 1:
                seg_limit = 1
            while j >= seg_limit:
                possible_filepaths.append(os.path.join(path_only,
                                                       f'{assemble_permutation(possible_filenames[i][:j])}{ext}'))
                j -= 1
    return possible_filepaths
