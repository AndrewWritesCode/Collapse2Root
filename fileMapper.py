import os
import tempfile
import zipfile
import json
import csv
from os_fileMapper import substitute_path, generate_permutations, abs2local_path_convert
from copy import deepcopy


def FileMapper(root_dir, extensions2omit=None, extensions2include=None):
    if extensions2omit is None:
        extensions2omit = []
    if extensions2include is None:
        extensions2include = []
    file_map = {}
    if not os.path.exists(root_dir):
        raise IsADirectoryError(f'Target path: {root_dir} can\'t be accessed')

    l_root = len(root_dir)
    for directory, sub_directories, files in os.walk(root_dir):
        for file in files:
            omit_file = False
            path_number = 1
            filename = str(file)
            path = directory[l_root:]

            # checks if file has extension that is omitted
            def ext_check(ext):
                if not ext.startswith('.'):
                    ext = f'.{ext}'
                return ext

            # include filter pass
            for extension in extensions2include:
                omit_file = True
                extension = ext_check(extension)
                if os.path.splitext(file)[1] == extension:
                    omit_file = False
                    break

            # exclude filter pass
            for extension in extensions2omit:
                extension = ext_check(extension)
                if os.path.splitext(file)[1] == extension:
                    omit_file = True
                    break
            if omit_file:
                continue

            # checks to see if file_map is empty and initializes if it is
            if not file_map:
                file_info = {
                    "number of paths": path_number,
                    "filepaths": [abs2local_path_convert(str(os.path.join(path, filename)))]
                }
                file_map[filename] = file_info
            else:
                # either updates file_map for each file of creates new file_map entry
                if filename in file_map:
                    path_number = file_map[filename]["number of paths"]
                    path_number += 1
                    file_map[filename]["number of paths"] = path_number
                    file_map[filename]["filepaths"].append(abs2local_path_convert(str(os.path.join(path, filename))))
                else:
                    file_info = {
                        "number of paths": path_number,
                        "filepaths": [abs2local_path_convert(str(os.path.join(path, filename)))]
                    }
                    file_map[filename] = file_info
    return file_map


def ZipMapper(zip_file, extensions2omit=None, extensions2include=None):
    if os.path.exists(zip_file):
        with zipfile.ZipFile(zip_file) as zf:
            with tempfile.TemporaryDirectory() as temp_dir:
                zf.extractall(temp_dir)
                return FileMapper(temp_dir, extensions2omit=extensions2omit, extensions2include=extensions2include)
    else:
        return


def SmartMapper(path, extensions2omit=None, extensions2include=None):
    if os.path.splitext(path)[1] == ".zip":
        return ZipMapper(path, extensions2omit=extensions2omit, extensions2include=extensions2include)
    else:
        return FileMapper(path, extensions2omit=extensions2omit, extensions2include=extensions2include)


def FileMap2json(file_map, json_path):
    if file_map:
        if os.path.exists(os.path.split(json_path)[0]):
            json_object = json.dumps(file_map, indent=4)
            with open(json_path, "w") as j:
                j.write(json_object)


def GetMapSize(file_map):
    size = 0
    for file in file_map:
        size += file_map[file]["number of paths"]
    return size


def GetDirsInMap(file_map):
    dirs_in_map = []
    for filename in file_map:
        for filepath in file_map[filename]["filepaths"]:
            filepath = os.path.split(filepath)[0]
            if filepath not in dirs_in_map:
                dirs_in_map.append(filepath)
    return dirs_in_map


# Can create a dummy FileMap by passing a tuple in the form (root, file_map dict)
class FileMap:
    def __init__(self, target_path, extensions2omit=None, extensions2include=None, dummy=None):
        if not dummy:
            self.__root = target_path
            self.__map = SmartMapper(target_path, extensions2omit=extensions2omit,
                                     extensions2include=extensions2include)
            self.__size = GetMapSize(self.map)
            self.__dirs_list = GetDirsInMap(self.map)
            self.__is_dummy = False
        elif isinstance(dummy, dict):
            self.__root = target_path
            self.__map = dummy
            self.__size = None
            self.__is_dummy = True

    @property
    def is_dummy(self):
        return self.__is_dummy

    @property
    def root(self):
        return self.__root

    @property
    def map(self):
        return self.__map

    @property  # returns the number of filepaths in the file_map
    def size(self):
        if not self.is_dummy:
            return GetMapSize(self.map)
        else:
            try:
                return GetMapSize(self.map)
            except KeyError:
                try:
                    size = 0
                    for file in self.map:
                        self.__map[file]["number of paths"] = 0
                        for path in self.map[file]["filepaths"]:
                            size += 1
                            self.__map[file]["number of paths"] += 1
                    return size
                except KeyError:
                    print(f'Dummy FileMap {self.__name__} improperly configured')

    @property
    def dirs_list(self):
        return GetDirsInMap(self.map)

    def exists(self):
        return bool(self.map)

    def __iter__(self):
        return iter(self.map)

    def __str__(self):
        return f'FileMap Object {self.__name__} maps {self.root}'

    def __sub__(self, other):
        for file in other.map:
            for path in other.map[file]["filepaths"]:
                if path in self.map[file]["filepaths"]:
                    self.__map[file]["number of paths"] -= 1
                    self.__map[file]["filepaths"].remove(path)
                if self.map[file]["number of paths"] == 0:
                    del self.__map[file]
                    continue
        self.__is_dummy = True
        return self.map

    def modify_filepath_root(self, filepath, new_root):
        filename = os.path.split(filepath)[1]
        new_path = os.path.join(new_root, filename)
        if filename in self.map:
            self.__is_dummy = True
            self.__map[filename]["filepaths"].remove(filepath)
            self.__map[filename]["filepaths"].append(new_path)
            return True
        else:
            return False

    def export_map_to_json(self, json_path):
        if self.map:
            if os.path.exists(os.path.split(json_path)[0]):
                json_object = json.dumps(self.map, indent=4)
                with open(json_path, "w") as j:
                    j.write(json_object)
            else:
                print(f'Exporting FileMap Object {self.__name__} to JSON failed: JSON has an invalid output path:\n'
                      f'Invalid path: {json_path}')
        else:
            print(f'Exporting FileMap Object {self.__name__} to JSON failed: has an empty map')

    # Counts the number of filepaths mapped in the file_map
    def number_of_filepath_matches(self, other):
        if not isinstance(other, FileMap):
            return
        if self.map and other.map:
            match_count = 0
            for file in self.map:
                if file not in other.map:
                    continue
                else:
                    for path in self.map[file]["filepaths"]:
                        if path in other.map[file]["filepaths"]:
                            match_count += 1
            return match_count

    # This returns a tuple of how many filepaths in self are also in other, and vice versa
    def get_similarity_proportions(self, other):
        if not isinstance(other, FileMap):
            return
        if self.map and other.map:
            return (self.number_of_filepath_matches(other) / self.size,
                    other.number_of_filepath_matches(self) / other.size)

    # generates a map of all missing filepaths from other FileMap Object
    def generate_dif_map(self, other):
        if not isinstance(other, FileMap):
            return
        if self.map and other.map:
            dif_map = FileMap(self.root, dummy=self.__map.copy())
            dif_map = dif_map - other
            return dif_map


# This class is used to reform a start FileMap to the structure of an end FileMap
# The proj_map holds the end FileMap filepaths as keys, and the corresponding start FileMaps as the value of the keys
# This structure represents the keys being desired file locations, and values of keys as the filepath to locate the file
class FileMapProjection:
    def __init__(self, start_FileMap, end_FileMap):
        self.start_map = deepcopy(start_FileMap.map)
        self.end_map = deepcopy(end_FileMap.map)
        self.proj_map = {}
        for file in self.end_map:
            for path in self.end_map[file]["filepaths"]:
                self.proj_map[path] = None

    def find_exact_matches(self):
        for path in self.proj_map:
            if os.path.split(path)[1] not in self.start_map:
                continue
            else:
                for filepath in self.start_map.copy()[os.path.split(path)[1]]["filepaths"]:
                    if (filepath == path) and (self.proj_map[path] is None):
                        self.proj_map[path] = filepath
                        self.start_map[os.path.split(path)[1]]["filepaths"].remove(filepath)
                        self.start_map[os.path.split(path)[1]]["number of paths"] -= 1
                        if self.start_map[os.path.split(path)[1]]["number of paths"] == 0:
                            self.start_map.pop(os.path.split(path)[1])

    def find_root_swaps(self, start_root, end_root):
        start_root = os.path.normpath(start_root)
        end_root = os.path.normpath(end_root)
        for path in self.proj_map:
            if os.path.split(path)[1] not in self.start_map:
                continue
            else:
                for filepath in self.start_map[os.path.split(path)[1]]["filepaths"]:
                    new_filepath = substitute_path(start_root, end_root, filepath) 
                    new_filepath = abs2local_path_convert(new_filepath)
                    if (new_filepath == path) and (self.proj_map[path] is None):
                        self.proj_map[path] = filepath
                        self.start_map[os.path.split(path)[1]]["filepaths"].remove(filepath)
                        self.start_map[os.path.split(path)[1]]["number of paths"] -= 1
                        if self.start_map[os.path.split(path)[1]]["number of paths"] == 0:
                            self.start_map.pop(os.path.split(path)[1])
                        break

    def find_permutation_matches(self, separator='_', start_root=None, end_root=None, use_drops=False, seg_limit=2,
                                 manual_adds=None, manual_removes=None):
        # for path in self.proj_map:
        for filename in self.start_map.copy():
            for path in self.start_map[filename]["filepaths"]:
                possible_filepaths = generate_permutations(path, separator=separator, use_drops=use_drops,
                                                           seg_limit=seg_limit, manual_adds=manual_adds,
                                                           manual_removes=manual_removes)
                if start_root and end_root:
                    for i in range(len(possible_filepaths)):
                        start_root = os.path.normpath(start_root)
                        end_root = os.path.normpath(end_root)
                        possible_filepaths[i] = substitute_path(start_root, end_root, possible_filepaths[i])

                for i in range(len(possible_filepaths)):
                    # 1st check to see if filename exists
                    possible_filename = os.path.split(possible_filepaths[i])[1]
                    if possible_filename not in self.end_map:
                        continue
                    # 2nd check if path matches in end_map
                    if possible_filepaths[i] in self.end_map[possible_filename]["filepaths"]:
                        if self.proj_map[possible_filepaths[i]] is None:
                            self.proj_map[possible_filepaths[i]] = path
                            self.start_map[filename]["filepaths"].remove(path)
                            self.start_map[filename]["number of paths"] -= 1
                            if self.start_map[filename]["number of paths"] == 0:
                                self.start_map.pop(filename)
                            break

    def manual_match(self, start_path, end_path):
        if end_path not in self.proj_map:
            return False
        else:
            if self.proj_map[end_path] is None:
                self.proj_map[end_path] = os.path.normpath(start_path)
                return True

    def manual_match_from_csv(self):
        pass

    def permutation_modifications_from_csv(self, csv_path, separator='_', start_root=None, end_root=None,
                                           use_drops=False, seg_limit=2):
        """
        This function adds or removes segments from the permutation (Very Expensive!)
        """
        if os.path.exists(csv_path):
            with open(csv_path, newline='') as csv_file:
                manual_matches = csv.reader(csv_file, delimiter=',')
                next(manual_matches)
                for row in manual_matches:
                    additions = row[0].split(' ')
                    removals = row[1].split(' ')
                    for removal in removals:
                        if removal == '':
                            removals.remove(removal)
                    self.find_permutation_matches(separator=separator, start_root=start_root, end_root=end_root,
                                                  use_drops=use_drops, seg_limit=seg_limit,
                                                  manual_adds=additions, manual_removes=removals)

    def projection_completion(self):
        match_count = self.number_of_matches()
        return match_count / len(self.proj_map)

    def number_of_matches(self):
        match_count = 0
        for path in self.proj_map:
            if self.proj_map[path]:  # counts a match so long as path isn't None
                match_count += 1
        return match_count

    def export_projection_to_json(self, json_path):
        if self.proj_map:
            if os.path.exists(os.path.split(json_path)[0]):
                json_object = json.dumps(self.proj_map, indent=4)
                with open(json_path, "w") as j:
                    j.write(json_object)
            else:
                print(f'Exporting FileMap Projection to JSON failed: JSON has an invalid output path:\n'
                      f'Invalid path: {json_path}')
        else:
            print(f'Exporting FileMap Projection to JSON failed: has an empty map')

    def export_maps_to_json(self, start_map_json_path=None, end_map_json_path=None):
        if self.start_map:
            if start_map_json_path:
                FileMap2json(self.start_map, start_map_json_path)
        if self.end_map:
            if end_map_json_path:
                FileMap2json(self.end_map, end_map_json_path)
