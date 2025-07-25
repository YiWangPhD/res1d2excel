#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this is an utility module for res1d


import utilities
import os

newLine = '\r\n'

def read_mus_file(musfilepath):
    """
    read mike urban selection file and turn into a dictionary
    """
    with open(musfilepath, 'r') as file:
        groups = file.read().strip().split('\n\n')
    return {group.split('\n')[0]: group.split('\n')[1:] for group in groups}


def clean_IDs(originalIDs, idType):
    if len(originalIDs) == 1 and list(originalIDs.keys())[0] == 'musFile':
        # add all MUIDs from the mus file into a list
        originalIDs = utilities.list_cleanup([read_mus_file(list(originalIDs.values())[0])])
    else:
        # convert string into list or tuple
        for k, v in enumerate(originalIDs):
            try:
                originalIDs[v] = utilities.string_to_list(originalIDs[v])
            except SyntaxError as err:
                raise RuntimeError(f"Cannot convert string {originalIDs[v]} to a list. {newLine} {err}")
            except:
                raise RuntimeError(f"Cannot convert string {originalIDs[v]} to a list")
        #originalIDs = {v: utilities.string_to_list(originalIDs[v]) for k, v in enumerate(originalIDs)}
        if len(originalIDs) == 1 and list(originalIDs.keys())[0] == idType:
            # convert to list if there's only one element named idType, backwards compatible
            originalIDs = originalIDs[idType]
        else:
            # clean list, keep a simple list, no tuples
            originalIDs = {v: utilities.list_cleanup([originalIDs[v]]) for k, v in enumerate(originalIDs)}

    #change list into dictionary
    if isinstance(originalIDs, list):
        originalIDs = {f'{"_".join(ids) if isinstance(ids, tuple) else ids}': utilities.list_cleanup([ids]) for ids in originalIDs}
    
    return originalIDs


def main():
    print("in utilities_res1d.py!")
    
    mus_path = os.path.join(os.path.dirname(os.path.realpath('__file__')), 'test_data', 'DiversionStructureSelection.mus')
    originalIDs = {'musFile': mus_path}
    # print(clean_IDs(originalIDs, None))
    
    originalIDs = {'levelIDs': '"a1", "b2", "c3", ("d4", "e5"), ["f6", "g7"], ("h8", "i9", "j10")'}
    print(clean_IDs(originalIDs, 'levelIDs'))
    
    originalIDs = {'levelIDs': '"a1", "b2", "c3", ("d4", "e5"), ["f6", "g7"], ("h8", "i9", "j10")', 
                  'flowIDs': '"a1", "b2", "c3", ("d4", "e5"), ["f6", "g7"], ("h8", "i9", "j10")'}
    print(clean_IDs(originalIDs, 'flowIDs'))


if __name__ == '__main__' and '__file__' not in globals():
    main()

